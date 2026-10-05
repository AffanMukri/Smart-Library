from typing import Literal
from pydantic import BaseModel, Field

class SensorUpdate(BaseModel):
    distance: float = Field(ge=0, le=400)
    light: int = Field(ge=0, le=1023)
    books: int = Field(ge=0)
    door: Literal["OPEN", "CLOSED"]
    lights: Literal["ON", "OFF"]
    occupancy: int | None = Field(default=None, ge=0)
    shelf_present: bool | None = None
    shelf_book_code: str | None = None
    security_alert: bool | None = None
    buzzer: Literal["ON", "OFF"] | None = None
    security_led: Literal["ON", "OFF"] | None = None
    lcd_line_1: str | None = Field(default=None, max_length=16)
    lcd_line_2: str | None = Field(default=None, max_length=16)
    last_student_id: str | None = None
    last_book_id: str | None = None
