from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models import Book, Loan
from app.services.sensor_service import get_system_state

router = APIRouter(prefix="/api", tags=["Dashboard"])
@router.get("/dashboard")
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    s = await get_system_state(db)
    active = await db.scalar(select(func.count(Loan.id)).where(Loan.returned_at.is_(None))) or 0
    overdue = await db.scalar(select(func.count(Loan.id)).where(Loan.returned_at.is_(None), Loan.due_at < datetime.utcnow())) or 0
    available = await db.scalar(select(func.count(Book.id)).where(Book.status == "AVAILABLE"))
    loans = list((await db.execute(select(Loan).where(Loan.returned_at.is_(None)))).scalars())
    outstanding = sum(max(0, (datetime.utcnow().date() - loan.due_at.date()).days) * 5 for loan in loans)
    data = {column.name: getattr(s, column.name) for column in s.__table__.columns}
    data.update({"available_books": min(available, s.books) if available is not None else s.books, "active_loans": active, "overdue_books": overdue, "due_soon": sum(0 <= (l.due_at.date()-datetime.utcnow().date()).days <= 2 for l in loans), "outstanding_fines": outstanding, "lighting_reason": "Dark environment + library occupied" if s.lights == "ON" else "Energy saving - library empty" if (s.light or 1023) < s.dark_threshold and s.occupancy == 0 else "Ambient light sufficient", "lighting_decision_source": "HYBRID_AUTOMATION"})
    return data
