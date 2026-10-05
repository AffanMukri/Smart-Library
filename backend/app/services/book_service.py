from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BookTransaction, Event, SystemState
from app.services.sensor_service import get_system_state


class InventoryError(Exception):
    pass


async def change_inventory(
    db: AsyncSession, transaction_type: str
) -> tuple[SystemState, BookTransaction]:
    await get_system_state(db)

    if transaction_type == "ISSUE":
        statement = (
            update(SystemState)
            .where(SystemState.id == 1, SystemState.books > 0)
            .values(books=SystemState.books - 1)
            .returning(SystemState.books)
        )
        event_type = "BOOK_ISSUED"
        error_message = "No books are available to issue"
    else:
        statement = (
            update(SystemState)
            .where(
                SystemState.id == 1,
                SystemState.books < SystemState.max_books,
            )
            .values(books=SystemState.books + 1)
            .returning(SystemState.books)
        )
        event_type = "BOOK_RETURNED"
        error_message = "All books have already been returned"

    books_remaining = (await db.execute(statement)).scalar_one_or_none()
    if books_remaining is None:
        raise InventoryError(error_message)

    event = Event(event_type=event_type, books=books_remaining)
    transaction = BookTransaction(
        transaction_type=transaction_type,
        books_remaining=books_remaining,
    )
    db.add_all((event, transaction))
    await db.commit()
    await db.refresh(transaction)
    state = await db.get(SystemState, 1, populate_existing=True)
    return state, transaction
