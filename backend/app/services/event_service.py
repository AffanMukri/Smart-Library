import json
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import BookTransaction, Event
from app.schemas.book import EventCreate
from app.services.sensor_service import get_system_state

class EventConflictError(Exception):
    pass

async def record_event(db: AsyncSession, payload: EventCreate) -> Event:
    state = await get_system_state(db)
    if payload.books is not None and payload.event in {"BOOK_ISSUED", "BOOK_RETURNED"}:
        expected = state.books + (-1 if payload.event == "BOOK_ISSUED" else 1)
        if payload.books != expected:
            raise EventConflictError(f"{payload.event} requires books={expected}, received {payload.books}")
        state.books = payload.books
        db.add(BookTransaction(transaction_type="ISSUE" if payload.event == "BOOK_ISSUED" else "RETURN", books_remaining=payload.books))
    event = Event(event_type=payload.event, books=payload.books if payload.books is not None else state.books, source=payload.source, student_id=payload.student_id, book_id=payload.book_id, value=payload.value, event_metadata=json.dumps(payload.metadata) if payload.metadata else None)
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event

async def list_events(db: AsyncSession, limit: int = 50) -> list[Event]:
    result = await db.execute(select(Event).order_by(desc(Event.timestamp), desc(Event.id)).limit(limit))
    return list(result.scalars())
