from datetime import datetime
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

class EventCreate(BaseModel):
    event: str
    books: int | None = Field(default=None, ge=0)
    source: str = "TINKERCAD_SIMULATOR"
    student_id: int | None = None
    book_id: int | None = None
    value: str | None = None
    metadata: dict | None = None

class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    event: str = Field(validation_alias=AliasChoices("event", "event_type"))
    books: int | None
    source: str = "SOFTWARE"
    student_id: int | None = None
    book_id: int | None = None
    value: str | None = None
    metadata: str | None = Field(default=None, validation_alias="event_metadata")
    timestamp: datetime

class InventoryOut(BaseModel):
    books: int
    max_books: int
    issued: int

class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    transaction_type: str
    books_remaining: int
    timestamp: datetime
