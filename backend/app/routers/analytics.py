from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.analytics import AnalyticsOut
from app.services.analytics_service import get_analytics


router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("", response_model=AnalyticsOut)
async def analytics(
    history_limit: int = Query(default=60, ge=1, le=300),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsOut:
    return await get_analytics(db, history_limit)

