from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Event, SensorReading, SystemState
from app.schemas.sensor import SensorUpdate

async def get_system_state(db: AsyncSession) -> SystemState:
    state = await db.get(SystemState, 1)
    if state is None:
        state = SystemState(id=1, books=5, max_books=5)
        db.add(state)
        await db.flush()
    return state

async def update_sensor_state(db: AsyncSession, payload: SensorUpdate) -> SystemState:
    state = await get_system_state(db)
    sample_time = datetime.utcnow()
    if state.updated_at:
        previous = state.updated_at.replace(tzinfo=None)
        elapsed_minutes = max(0, min(5, (sample_time - previous).total_seconds() / 60))
        if state.lights == "ON":
            state.lights_on_minutes += elapsed_minutes
        if (state.light or 1023) < state.dark_threshold and state.occupancy == 0:
            state.prevented_minutes += elapsed_minutes
    data = payload.model_dump(exclude_none=True)
    old_lights, old_shelf = state.lights, state.shelf_present
    backend_commands = {"security_alert", "buzzer", "security_led", "lcd_line_1", "lcd_line_2"}
    for field, value in data.items():
        if field in backend_commands:
            continue
        if hasattr(state, field):
            setattr(state, field, value)
    # Occupancy-aware lighting is applied for upgraded bridge payloads. Legacy
    # payloads retain their provided actuator state for backwards compatibility.
    if payload.occupancy is not None:
        state.occupancy_source = "SOFTWARE_SIMULATION"
        state.peak_occupancy = max(state.peak_occupancy, state.occupancy)
        state.lights = "ON" if state.light < state.dark_threshold and state.occupancy > 0 else "OFF"
    if old_lights != state.lights:
        db.add(Event(event_type=f"LIGHTS_{state.lights}", books=state.books, source="HYBRID_AUTOMATION"))
    if payload.shelf_present is not None and old_shelf and not state.shelf_present:
        now = datetime.utcnow()
        authorized = state.authorized_removal_until is not None and state.authorized_removal_until >= now
        db.add(Event(event_type="SHELF_BOOK_REMOVED", books=state.books, source="TINKERCAD_SIMULATOR", value=state.shelf_book_code))
        if not authorized:
            state.security_alert, state.buzzer, state.security_led = True, "ON", "ON"
            state.lcd_line_1, state.lcd_line_2 = "SECURITY ALERT", "BOOK REMOVED"
            db.add(Event(event_type="UNAUTHORIZED_BOOK_REMOVAL", books=state.books, source="SHELF_PRESENCE_SIMULATOR", value=state.shelf_book_code))
    state.system_status = "ONLINE"
    db.add(SensorReading(distance=state.distance, light=state.light, door=state.door, lights=state.lights, occupancy=state.occupancy, shelf_present=state.shelf_present))
    await db.commit()
    await db.refresh(state)
    return state
