"""Students, circulation, capabilities, occupancy and smart-shelf APIs."""
from datetime import datetime, timedelta
import re
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models import Book, Event, Loan, Student
from app.services.sensor_service import get_system_state

router = APIRouter(prefix="/api", tags=["Smart Operations"])
DEFAULT_LOAN_DAYS, FINE_PER_DAY, MAXIMUM_FINE = 14, 5.0, None

def now() -> datetime: return datetime.utcnow()
def student_dict(s: Student) -> dict:
    return {"id": s.id, "student_code": s.student_code, "name": s.name, "department": s.department, "email": s.email, "status": s.status, "blocked": s.blocked, "borrowing_limit": s.borrowing_limit, "created_at": s.created_at}
def book_dict(b: Book) -> dict:
    return {"id": b.id, "book_code": b.book_code, "isbn": b.isbn, "title": b.title, "author": b.author, "category": b.category, "shelf_code": b.shelf_code, "status": b.status, "cover_url": b.cover_url}
def fine_for(loan: Loan, end: datetime | None = None) -> tuple[int, float]:
    end = end or loan.returned_at or now()
    days = max(0, (end.date() - loan.due_at.date()).days)
    amount = days * FINE_PER_DAY
    return days, min(amount, MAXIMUM_FINE) if MAXIMUM_FINE else amount
def effective_status(loan: Loan) -> str:
    if loan.returned_at: return "RETURNED"
    days = (loan.due_at.date() - now().date()).days
    return "OVERDUE" if days < 0 else "DUE_SOON" if days <= 2 else "ACTIVE"
def loan_dict(loan: Loan, student: Student, book: Book) -> dict:
    days, fine = fine_for(loan)
    return {"id": loan.id, "student_id": student.id, "student_code": student.student_code, "student_name": student.name, "book_id": book.id, "book_code": book.book_code, "book_title": book.title, "issued_at": loan.issued_at, "due_at": loan.due_at, "returned_at": loan.returned_at, "status": effective_status(loan), "days_overdue": days, "fine_amount": fine}

async def joined_loans(db: AsyncSession, where=None):
    statement = select(Loan, Student, Book).join(Student, Loan.student_id == Student.id).join(Book, Loan.book_id == Book.id).order_by(Loan.created_at.desc())
    if where is not None: statement = statement.where(where)
    return [loan_dict(*row) for row in (await db.execute(statement)).all()]

@router.get("/students")
async def students(db: AsyncSession = Depends(get_db)):
    rows = list((await db.execute(select(Student).order_by(Student.student_code))).scalars())
    return [student_dict(row) for row in rows]

@router.get("/students/{student_code}")
async def student(student_code: str, db: AsyncSession = Depends(get_db)):
    row = await db.scalar(select(Student).where(func.upper(Student.student_code) == student_code.upper()))
    if not row: raise HTTPException(404, "Student not found")
    active = await db.scalar(select(func.count(Loan.id)).where(Loan.student_id == row.id, Loan.returned_at.is_(None)))
    loans = await joined_loans(db, Loan.student_id == row.id)
    return {**student_dict(row), "active_loans": active or 0, "outstanding_fine": sum(x["fine_amount"] for x in loans if x["status"] != "RETURNED")}

class IdentifyStudent(BaseModel):
    text: str
    confidence: float | None = None

@router.post("/students/identify")
async def identify_student(payload: IdentifyStudent, db: AsyncSession = Depends(get_db)):
    candidates = re.findall(r"[A-Za-z0-9-]{5,20}", payload.text.upper())
    row = None
    for candidate in candidates:
        row = await db.scalar(select(Student).where(func.upper(Student.student_code) == candidate))
        if row: break
    if not row: raise HTTPException(404, "Student ID was not recognized. Enter it manually.")
    state = await get_system_state(db); state.last_student_id = row.student_code; state.lcd_line_1 = "Student Verified"[:16]; state.lcd_line_2 = row.student_code[:16]
    db.add(Event(event_type="STUDENT_IDENTIFIED", source="WEB_CAMERA", student_id=row.id, value=row.student_code))
    await db.commit()
    return await student(row.student_code, db)

class IssueRequest(BaseModel):
    student_code: str
    book_code: str
    loan_days: int = DEFAULT_LOAN_DAYS

@router.post("/loans/issue")
async def issue(payload: IssueRequest, db: AsyncSession = Depends(get_db)):
    student_row = await db.scalar(select(Student).where(func.upper(Student.student_code) == payload.student_code.upper()))
    book = await db.scalar(select(Book).where(func.upper(Book.book_code) == payload.book_code.upper()))
    if not student_row: raise HTTPException(404, "Student not found")
    if student_row.status != "ACTIVE" or student_row.blocked: raise HTTPException(409, "Student is inactive or blocked")
    if not book: raise HTTPException(404, "Book not found")
    if book.status != "AVAILABLE": raise HTTPException(409, "Book is not available")
    active = await db.scalar(select(func.count(Loan.id)).where(Loan.student_id == student_row.id, Loan.returned_at.is_(None)))
    if active >= student_row.borrowing_limit: raise HTTPException(409, "Student borrowing limit exceeded")
    issued_at, due_at = now(), now() + timedelta(days=max(1, min(payload.loan_days, 90)))
    loan = Loan(student_id=student_row.id, book_id=book.id, issued_at=issued_at, due_at=due_at, status="ACTIVE")
    book.status = "ISSUED"
    state = await get_system_state(db); state.books = max(0, state.books - 1); state.last_student_id = student_row.student_code; state.last_book_id = book.book_code
    state.authorized_removal_until = now() + timedelta(seconds=10); state.shelf_book_code = book.book_code; state.lcd_line_1 = "Book Issued"; state.lcd_line_2 = f"Due: {due_at:%d/%m}"[:16]
    db.add_all([loan, Event(event_type="BOOK_ISSUED", books=state.books, source="WEB_CAMERA", student_id=student_row.id, book_id=book.id, value=book.book_code)])
    await db.commit(); await db.refresh(loan)
    return {"success": True, "loan_id": loan.id, "student": student_row.name, "book": book.title, "book_code": book.book_code, "issued_at": issued_at, "due_at": due_at, "status": "ACTIVE"}

class ReturnRequest(BaseModel):
    book_code: str
    returned_at: datetime | None = None

@router.post("/loans/return")
async def return_loan(payload: ReturnRequest, db: AsyncSession = Depends(get_db)):
    book = await db.scalar(select(Book).where(func.upper(Book.book_code) == payload.book_code.upper()))
    if not book: raise HTTPException(404, "Book not found")
    loan = await db.scalar(select(Loan).where(Loan.book_id == book.id, Loan.returned_at.is_(None)).order_by(Loan.issued_at.desc()))
    if not loan: raise HTTPException(409, "No active loan exists for this book")
    returned = payload.returned_at or now(); days, fine = fine_for(loan, returned)
    loan.returned_at, loan.fine_amount, loan.status = returned, fine, "RETURNED"; book.status = "AVAILABLE"
    state = await get_system_state(db); state.books = min(state.max_books, state.books + 1); state.last_book_id = book.book_code; state.lcd_line_1 = "Book Returned"; state.lcd_line_2 = f"Fine: Rs {fine:.0f}"[:16]
    db.add(Event(event_type="BOOK_RETURNED", books=state.books, source="WEB_CAMERA", student_id=loan.student_id, book_id=book.id, value=book.book_code))
    if fine: db.add(Event(event_type="FINE_CALCULATED", source="SOFTWARE", student_id=loan.student_id, book_id=book.id, value=f"{fine:.2f}"))
    await db.commit()
    return {"success": True, "book": book.title, "book_code": book.book_code, "returned_at": returned, "days_overdue": days, "fine_amount": fine, "status": "RETURNED"}

@router.get("/loans")
async def loans(db: AsyncSession = Depends(get_db)): return await joined_loans(db)
@router.get("/loans/active")
async def active_loans(db: AsyncSession = Depends(get_db)): return await joined_loans(db, Loan.returned_at.is_(None))
@router.get("/loans/overdue")
async def overdue_loans(db: AsyncSession = Depends(get_db)): return await joined_loans(db, Loan.returned_at.is_(None) & (Loan.due_at < now()))
@router.get("/students/{student_code}/loans")
async def student_loans(student_code: str, db: AsyncSession = Depends(get_db)):
    row = await db.scalar(select(Student).where(func.upper(Student.student_code) == student_code.upper()))
    if not row: raise HTTPException(404, "Student not found")
    return await joined_loans(db, Loan.student_id == row.id)

class OccupancyRequest(BaseModel): event: str
@router.post("/occupancy")
async def occupancy(payload: OccupancyRequest, db: AsyncSession = Depends(get_db)):
    event = payload.event.upper()
    if event not in {"PERSON_ENTERED", "PERSON_EXITED"}: raise HTTPException(422, "event must be PERSON_ENTERED or PERSON_EXITED")
    state = await get_system_state(db)
    if event == "PERSON_ENTERED": state.occupancy += 1; state.entries_today += 1
    else: state.occupancy = max(0, state.occupancy - 1); state.exits_today += 1
    state.peak_occupancy = max(state.peak_occupancy, state.occupancy); state.occupancy_source = "SOFTWARE_SIMULATION"
    state.lights = "ON" if (state.light or 1023) < state.dark_threshold and state.occupancy > 0 else "OFF"
    db.add(Event(event_type=event, books=state.books, source="SOFTWARE_SIMULATION", value=str(state.occupancy)))
    await db.commit(); return {"occupancy": state.occupancy, "entries_today": state.entries_today, "exits_today": state.exits_today, "peak_occupancy": state.peak_occupancy, "source": state.occupancy_source}

class ShelfRequest(BaseModel): present: bool; book_code: str | None = None
@router.post("/shelf")
async def shelf(payload: ShelfRequest, db: AsyncSession = Depends(get_db)):
    state = await get_system_state(db); was_present = state.shelf_present; state.shelf_present = payload.present
    if payload.book_code: state.shelf_book_code = payload.book_code
    if was_present and not payload.present:
        authorized = state.authorized_removal_until is not None and state.authorized_removal_until >= now()
        db.add(Event(event_type="SHELF_BOOK_REMOVED", source="TINKERCAD_SIMULATOR", value=state.shelf_book_code))
        if not authorized:
            state.security_alert, state.buzzer, state.security_led = True, "ON", "ON"; state.lcd_line_1, state.lcd_line_2 = "SECURITY ALERT", "BOOK REMOVED"
            db.add(Event(event_type="UNAUTHORIZED_BOOK_REMOVAL", source="SHELF_PRESENCE_SIMULATOR", value=state.shelf_book_code))
    elif payload.present: db.add(Event(event_type="SHELF_BOOK_RESTORED", source="TINKERCAD_SIMULATOR", value=state.shelf_book_code))
    await db.commit(); return {"shelf_present": state.shelf_present, "shelf_book_code": state.shelf_book_code, "security_alert": state.security_alert, "buzzer": state.buzzer, "security_led": state.security_led}

@router.post("/security/clear")
async def clear_security(db: AsyncSession = Depends(get_db)):
    state = await get_system_state(db); state.security_alert, state.buzzer, state.security_led = False, "OFF", "OFF"; state.lcd_line_1, state.lcd_line_2 = "Smart Library", "System Safe"
    db.add(Event(event_type="SECURITY_ALERT_CLEARED", source="SOFTWARE")); await db.commit(); return {"success": True}

@router.get("/device-command")
async def device_command(db: AsyncSession = Depends(get_db)):
    s = await get_system_state(db); return {"bridge": "SIMULATOR_BRIDGE", "lcd_line_1": s.lcd_line_1, "lcd_line_2": s.lcd_line_2, "buzzer": s.buzzer, "security_led": s.security_led, "lights": s.lights, "door": s.door}

@router.get("/devices")
async def devices(db: AsyncSession = Depends(get_db)):
    s = await get_system_state(db); seen = s.updated_at
    def d(id, name, type, source, connected, status, value=None, unit=None, description=""):
        return {"id": id, "name": name, "type": type, "source": source, "connected": connected, "status": status, "value": value, "unit": unit, "last_seen": seen if connected else None, "description": description}
    return [
      d("ultrasonic_a", "HC-SR04 Entrance", "SENSOR", "TINKERCAD_SIMULATOR", True, "SIMULATED", s.distance, "cm", "Entrance distance and automatic door detection"),
      d("servo", "SG90 Door Servo", "ACTUATOR", "TINKERCAD_SIMULATOR", True, "SIMULATED", s.door, None, "Automatic entrance door"),
      d("ldr", "LDR", "SENSOR", "TINKERCAD_SIMULATOR", True, "SIMULATED", s.light, "ADC", "Ambient brightness"),
      d("led1", "LED #1 Library Light", "ACTUATOR", "TINKERCAD_SIMULATOR", True, "SIMULATED", s.lights, None, "Lighting representation"),
      d("lcd", "16x2 LCD", "DISPLAY", "TINKERCAD_SIMULATOR", True, "SIMULATED", f"{s.lcd_line_1} / {s.lcd_line_2}", None, "Checkout, return and alarm state via simulator bridge"),
      d("buzzer", "Piezo Alarm", "ACTUATOR", "TINKERCAD_SIMULATOR", True, "SIMULATED", s.buzzer, None, "Unauthorized removal alarm"),
      d("led2", "LED #2 Security", "ACTUATOR", "TINKERCAD_SIMULATOR", True, "SIMULATED", s.security_led, None, "Security alert indicator"),
      d("shelf_switch", "Shelf Presence Switch", "SENSOR", "TINKERCAD_SIMULATOR", True, "SIMULATED", "PRESENT" if s.shelf_present else "REMOVED", None, "Push button reused as book-presence prototype"),
      d("student_ocr", "Student OCR", "SCANNER", "WEB_CAMERA", True, "WEB CAMERA", s.last_student_id, None, "Browser camera OCR; not Arduino hardware"),
      d("book_scanner", "Book Barcode/OCR", "SCANNER", "WEB_CAMERA", True, "WEB CAMERA", s.last_book_id, None, "Browser camera barcode/OCR; not Arduino hardware"),
      d("loans", "Loans and Fines", "SERVICE", "SOFTWARE", True, "SOFTWARE", None, None, "FastAPI circulation engine"),
      d("ultrasonic_b", "Second HC-SR04", "SENSOR", "NOT_CONNECTED", False, "NOT CONNECTED", None, None, "Hardware required for true directional detection"),
    ]

@router.get("/settings")
async def library_settings(): return {"default_loan_days": DEFAULT_LOAN_DAYS, "fine_per_day": FINE_PER_DAY, "maximum_fine": MAXIMUM_FINE, "demo_defaults": True}
