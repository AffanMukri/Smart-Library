from datetime import datetime
from pydantic import BaseModel, ConfigDict

class SystemStateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    books: int
    max_books: int
    distance: float | None
    light: int | None
    door: str
    lights: str
    system_status: str
    occupancy: int = 0
    entries_today: int = 0
    exits_today: int = 0
    peak_occupancy: int = 0
    occupancy_source: str = "SOFTWARE_SIMULATION"
    dark_threshold: int = 500
    shelf_present: bool = True
    shelf_book_code: str | None = None
    security_alert: bool = False
    buzzer: str = "OFF"
    security_led: str = "OFF"
    lcd_line_1: str = "Smart Library"
    lcd_line_2: str = "System Ready"
    last_student_id: str | None = None
    last_book_id: str | None = None
    updated_at: datetime
