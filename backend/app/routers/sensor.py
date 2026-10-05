from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.sensor import SensorUpdate
from app.schemas.system import SystemStateOut
from app.services.sensor_service import update_sensor_state


router = APIRouter(prefix="/api", tags=["Sensors"])


@router.post("/sensor", response_model=SystemStateOut)
async def receive_sensor_data(
    payload: SensorUpdate,
    db: AsyncSession = Depends(get_db),
) -> SystemStateOut:
    return await update_sensor_state(db, payload)

