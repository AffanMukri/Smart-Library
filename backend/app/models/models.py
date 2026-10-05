"""Database models for the Smart Library.

Legacy count-based tables remain intact while individual books and loans add a
real circulation layer. SQLite migrations in ``database.py`` add columns to
existing installations without deleting user data.
"""

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.db.database import Base


class SystemState(Base):
    __tablename__ = "system_state"
    id = Column(Integer, primary_key=True)
    books = Column(Integer, nullable=False, default=5)
    max_books = Column(Integer, nullable=False, default=5)
    distance = Column(Float, nullable=True)
    light = Column(Integer, nullable=True)
    door = Column(String(6), nullable=False, default="CLOSED")
    lights = Column(String(3), nullable=False, default="OFF")
    system_status = Column(String(10), nullable=False, default="ONLINE")
    occupancy = Column(Integer, nullable=False, default=0)
    entries_today = Column(Integer, nullable=False, default=0)
    exits_today = Column(Integer, nullable=False, default=0)
    peak_occupancy = Column(Integer, nullable=False, default=0)
    occupancy_source = Column(String(32), nullable=False, default="SOFTWARE_SIMULATION")
    dark_threshold = Column(Integer, nullable=False, default=500)
    shelf_present = Column(Boolean, nullable=False, default=True)
    shelf_book_code = Column(String(32), nullable=True)
    security_alert = Column(Boolean, nullable=False, default=False)
    buzzer = Column(String(3), nullable=False, default="OFF")
    security_led = Column(String(3), nullable=False, default="OFF")
    lcd_line_1 = Column(String(16), nullable=False, default="Smart Library")
    lcd_line_2 = Column(String(16), nullable=False, default="System Ready")
    last_student_id = Column(String(32), nullable=True)
    last_book_id = Column(String(32), nullable=True)
    authorized_removal_until = Column(DateTime(timezone=True), nullable=True)
    lights_on_since = Column(DateTime(timezone=True), nullable=True)
    lights_on_minutes = Column(Float, nullable=False, default=0)
    prevented_minutes = Column(Float, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    __table_args__ = (
        CheckConstraint("books >= 0", name="ck_system_state_books_non_negative"),
        CheckConstraint("max_books >= books", name="ck_system_state_max_ge_current"),
        CheckConstraint("door IN ('OPEN','CLOSED')", name="ck_system_state_door"),
        CheckConstraint("lights IN ('ON','OFF')", name="ck_system_state_lights"),
    )


class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_type = Column(String(48), nullable=False)
    books = Column(Integer, nullable=True)
    source = Column(String(32), nullable=False, default="SOFTWARE")
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=True)
    value = Column(String(128), nullable=True)
    event_metadata = Column("metadata", Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class BookTransaction(Base):
    __tablename__ = "book_transactions"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_type = Column(String(6), nullable=False)
    books_remaining = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class SensorReading(Base):
    __tablename__ = "sensor_readings"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    distance = Column(Float, nullable=False)
    light = Column(Integer, nullable=False)
    door = Column(String(6), nullable=False)
    lights = Column(String(3), nullable=False)
    occupancy = Column(Integer, nullable=False, default=0)
    shelf_present = Column(Boolean, nullable=False, default=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_code = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False)
    department = Column(String(120), nullable=False)
    email = Column(String(160), nullable=True)
    status = Column(String(10), nullable=False, default="ACTIVE")
    blocked = Column(Boolean, nullable=False, default=False)
    borrowing_limit = Column(Integer, nullable=False, default=3)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, autoincrement=True)
    book_code = Column(String(32), unique=True, nullable=False, index=True)
    isbn = Column(String(32), unique=True, nullable=True, index=True)
    title = Column(String(200), nullable=False)
    author = Column(String(160), nullable=False)
    category = Column(String(80), nullable=True)
    shelf_code = Column(String(32), nullable=False)
    status = Column(String(12), nullable=False, default="AVAILABLE")
    cover_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Loan(Base):
    __tablename__ = "loans"
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)
    issued_at = Column(DateTime(timezone=True), nullable=False)
    due_at = Column(DateTime(timezone=True), nullable=False, index=True)
    returned_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(12), nullable=False, default="ACTIVE")
    fine_amount = Column(Float, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
