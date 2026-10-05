from datetime import datetime

from pydantic import BaseModel


class SensorHistoryPoint(BaseModel):
    timestamp: datetime
    light: int
    distance: float


class CountPoint(BaseModel):
    name: str
    count: int


class AnalyticsOut(BaseModel):
    sensor_history: list[SensorHistoryPoint]
    transaction_counts: list[CountPoint]
    event_distribution: list[CountPoint]
    uptime_seconds: int
    system_status: str

