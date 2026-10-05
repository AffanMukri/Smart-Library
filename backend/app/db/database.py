from collections.abc import AsyncGenerator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

SYSTEM_COLUMNS = {
    "occupancy": "INTEGER NOT NULL DEFAULT 0", "entries_today": "INTEGER NOT NULL DEFAULT 0",
    "exits_today": "INTEGER NOT NULL DEFAULT 0", "peak_occupancy": "INTEGER NOT NULL DEFAULT 0",
    "occupancy_source": "VARCHAR(32) NOT NULL DEFAULT 'SOFTWARE_SIMULATION'",
    "dark_threshold": "INTEGER NOT NULL DEFAULT 500", "shelf_present": "BOOLEAN NOT NULL DEFAULT 1",
    "shelf_book_code": "VARCHAR(32)", "security_alert": "BOOLEAN NOT NULL DEFAULT 0",
    "buzzer": "VARCHAR(3) NOT NULL DEFAULT 'OFF'", "security_led": "VARCHAR(3) NOT NULL DEFAULT 'OFF'",
    "lcd_line_1": "VARCHAR(16) NOT NULL DEFAULT 'Smart Library'",
    "lcd_line_2": "VARCHAR(16) NOT NULL DEFAULT 'System Ready'", "last_student_id": "VARCHAR(32)",
    "last_book_id": "VARCHAR(32)", "authorized_removal_until": "DATETIME", "lights_on_since": "DATETIME",
    "lights_on_minutes": "FLOAT NOT NULL DEFAULT 0", "prevented_minutes": "FLOAT NOT NULL DEFAULT 0",
}
EVENT_COLUMNS = {"source": "VARCHAR(32) NOT NULL DEFAULT 'SOFTWARE'", "student_id": "INTEGER", "book_id": "INTEGER", "value": "VARCHAR(128)", "metadata": "TEXT"}
READING_COLUMNS = {"occupancy": "INTEGER NOT NULL DEFAULT 0", "shelf_present": "BOOLEAN NOT NULL DEFAULT 1"}

async def _add_missing(connection, table: str, columns: dict[str, str]) -> None:
    def migrate(sync_connection):
        existing = {row[1] for row in sync_connection.exec_driver_sql(f"PRAGMA table_info({table})")}
        for name, definition in columns.items():
            if name not in existing:
                sync_connection.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")
    await connection.run_sync(migrate)

async def init_db() -> None:
    from app.models import Book, Student, SystemState
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await _add_missing(connection, "system_state", SYSTEM_COLUMNS)
        await _add_missing(connection, "events", EVENT_COLUMNS)
        await _add_missing(connection, "sensor_readings", READING_COLUMNS)
    async with AsyncSessionLocal() as session:
        if await session.get(SystemState, 1) is None:
            session.add(SystemState(id=1, books=5, max_books=5))
        if await session.scalar(select(Student.id).limit(1)) is None:
            session.add_all([
                Student(student_code="23IT101", name="Affan Mukri", department="Information Technology", email="affan@example.edu"),
                Student(student_code="23IT102", name="Sara Khan", department="Information Technology", email="sara@example.edu"),
                Student(student_code="23CS103", name="Rohan Mehta", department="Computer Science", email="rohan@example.edu"),
            ])
        if await session.scalar(select(Book.id).limit(1)) is None:
            session.add_all([
                Book(book_code="BOOK001", isbn="9780133970777", title="Database Management Systems", author="Raghu Ramakrishnan", category="Databases", shelf_code="A-01"),
                Book(book_code="BOOK002", isbn="9780132350884", title="Clean Code", author="Robert C. Martin", category="Software Engineering", shelf_code="A-02"),
                Book(book_code="BOOK003", isbn="9780262033848", title="Introduction to Algorithms", author="Cormen et al.", category="Algorithms", shelf_code="B-01"),
                Book(book_code="BOOK004", isbn="9780131103627", title="The C Programming Language", author="Kernighan and Ritchie", category="Programming", shelf_code="B-02"),
                Book(book_code="BOOK005", isbn="9780201633610", title="Design Patterns", author="Gamma et al.", category="Software Engineering", shelf_code="C-01"),
            ])
        await session.commit()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
