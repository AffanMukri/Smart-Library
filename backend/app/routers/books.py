from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models import Book, Event
from app.services.book_service import InventoryError, change_inventory
from app.services.sensor_service import get_system_state

router = APIRouter(prefix="/api/books", tags=["Books"])

def book_dict(book: Book) -> dict:
    return {"id": book.id, "book_code": book.book_code, "isbn": book.isbn, "title": book.title, "author": book.author, "category": book.category, "shelf_code": book.shelf_code, "status": book.status, "cover_url": book.cover_url, "created_at": book.created_at}

@router.get("")
async def get_books(db: AsyncSession = Depends(get_db)):
    items = list((await db.execute(select(Book).order_by(Book.book_code))).scalars())
    state = await get_system_state(db)
    available = sum(book.status == "AVAILABLE" for book in items)
    return {"books": state.books, "max_books": state.max_books, "issued": state.max_books - state.books, "available_records": available, "issued_records": sum(book.status == "ISSUED" for book in items), "items": [book_dict(book) for book in items]}

@router.get("/isbn/{isbn}")
async def by_isbn(isbn: str, db: AsyncSession = Depends(get_db)):
    book = await db.scalar(select(Book).where(Book.isbn == isbn.strip()))
    if not book: raise HTTPException(404, "Book not found")
    return book_dict(book)

@router.get("/{book_code}")
async def by_code(book_code: str, db: AsyncSession = Depends(get_db)):
    book = await db.scalar(select(Book).where(func.upper(Book.book_code) == book_code.strip().upper()))
    if not book: raise HTTPException(404, "Book not found")
    return book_dict(book)

class IdentifyBook(BaseModel):
    code: str

@router.post("/identify")
async def identify(payload: IdentifyBook, db: AsyncSession = Depends(get_db)):
    value = payload.code.strip()
    book = await db.scalar(select(Book).where((func.upper(Book.book_code) == value.upper()) | (Book.isbn == value)))
    if not book: raise HTTPException(404, "No book matches the scanned code or ISBN")
    state = await get_system_state(db)
    state.last_book_id = book.book_code
    state.shelf_book_code = book.book_code
    state.lcd_line_1, state.lcd_line_2 = "Book Scanned", book.book_code[:16]
    db.add(Event(event_type="BOOK_SCANNED", source="WEB_CAMERA", book_id=book.id, value=book.book_code))
    await db.commit()
    return book_dict(book)

@router.post("/issue")
async def legacy_issue(db: AsyncSession = Depends(get_db)):
    try:
        _, transaction = await change_inventory(db, "ISSUE")
        return transaction
    except InventoryError as exc: raise HTTPException(409, str(exc)) from exc

@router.post("/return")
async def legacy_return(db: AsyncSession = Depends(get_db)):
    try:
        _, transaction = await change_inventory(db, "RETURN")
        return transaction
    except InventoryError as exc: raise HTTPException(409, str(exc)) from exc
