import pytest
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
from app.repositories.booking_repository import BookingRepository

@pytest.mark.asyncio
async def test_find_and_decrement_slot_success():
    # 1. Setup Mocks
    mock_db = MagicMock()
    mock_events = AsyncMock()
    mock_db.get_collection.return_value = mock_events
    repo = BookingRepository(mock_db)

    event_id = "660adb23f51bb4362e0020ee"
    
    # 2. Mock successful atomic update
    mock_events.find_one_and_update.return_value = {"_id": ObjectId(event_id), "available_slots": 9}

    # 3. Execute
    result = await repo.find_and_decrement_slot(event_id)

    # 4. Assertions: Verify the ATOMIC operators ($gt and $inc)
    assert result["available_slots"] == 9 # type: ignore
    mock_events.find_one_and_update.assert_called_once_with(
        {"_id": ObjectId(event_id), "available_slots": {"$gt": 0}}, # Safety check
        {"$inc": {"available_slots": -1}},                          # Atomic minus 1
        return_document=True
    )

@pytest.mark.asyncio
async def test_check_existing_booking():
    mock_db = MagicMock()
    mock_bookings = AsyncMock()
    mock_db.get_collection.return_value = mock_bookings
    repo = BookingRepository(mock_db)

    e_id, u_id = "660adb23f51bb4362e0020ee", "660adb23f51bb4362e0020ff"
    mock_bookings.find_one.return_value = {"_id": "exists"}

    # Execute
    await repo.check_existing_booking(e_id, u_id)

    # Verify query uses BOTH IDs as ObjectIds
    mock_bookings.find_one.assert_called_once_with({
        "event_id": ObjectId(e_id),
        "user_id": ObjectId(u_id)
    })

@pytest.mark.asyncio
async def test_show_bookings_cursor_fix():
    # 5. Same fix as EventRepository: Collection.find must be MagicMock
    mock_db = MagicMock()
    mock_bookings = MagicMock() # Regular Mock
    mock_db.get_collection.return_value = mock_bookings
    repo = BookingRepository(mock_db)

    user_id = "660adb23f51bb4362e0020ee"
    mock_cursor = AsyncMock() # Cursor is Async
    mock_bookings.find.return_value = mock_cursor
    mock_cursor.to_list.return_value = [{"_id": "b1"}]

    # Execute
    result = await repo.show_bookings(user_id)

    assert len(result) == 1
    mock_bookings.find.assert_called_once_with({"user_id": ObjectId(user_id)})
    mock_cursor.to_list.assert_called_once_with(length=None)
