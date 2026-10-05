from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.book import EventCreate, EventOut
from app.services.event_service import EventConflictError, list_events, record_event


router = APIRouter(prefix="/api", tags=["Events"])


@router.post("/event", response_model=EventOut, status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: EventCreate,
    db: AsyncSession = Depends(get_db),
) -> EventOut:
    try:
        return await record_event(db, payload)
    except EventConflictError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/events", response_model=list[EventOut])
async def get_events(
    limit: int = Query(default=50, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> list[EventOut]:
    return await list_events(db, limit)
