from time import monotonic

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BookTransaction, Event, SensorReading
from app.services.sensor_service import get_system_state


PROCESS_STARTED_AT = monotonic()


async def get_analytics(db: AsyncSession, history_limit: int) -> dict:
    history_result = await db.execute(
        select(SensorReading)
        .order_by(desc(SensorReading.timestamp), desc(SensorReading.id))
        .limit(history_limit)
    )
    history = list(reversed(list(history_result.scalars())))

    transaction_result = await db.execute(
        select(BookTransaction.transaction_type, func.count(BookTransaction.id))
        .group_by(BookTransaction.transaction_type)
    )
    transaction_map = dict(transaction_result.all())

    event_result = await db.execute(
        select(Event.event_type, func.count(Event.id)).group_by(Event.event_type)
    )
    state = await get_system_state(db)

    return {
        "sensor_history": [
            {
                "timestamp": reading.timestamp,
                "light": reading.light,
                "distance": reading.distance,
            }
            for reading in history
        ],
        "transaction_counts": [
            {"name": "ISSUE", "count": transaction_map.get("ISSUE", 0)},
            {"name": "RETURN", "count": transaction_map.get("RETURN", 0)},
        ],
        "event_distribution": [
            {"name": event_type, "count": count}
            for event_type, count in event_result.all()
        ],
        "uptime_seconds": int(monotonic() - PROCESS_STARTED_AT),
        "system_status": state.system_status,
    }

