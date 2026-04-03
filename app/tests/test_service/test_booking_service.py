import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
from app.exception.error import BadRequest
from app.services.booking_service import BookingService

@pytest.mark.asyncio
async def test_register_booking_success():
    mock_repo = AsyncMock()
    mock_cache = AsyncMock()
    service = BookingService(mock_repo,mock_cache)
    service.repo = mock_repo
    service.cache = mock_cache

    event_id = "660adb23f51bb4362e0020ee"
    user_id = "660adb23f51bb4362e0020ff"
    
    # 1. Setup Mock User & Inputs
    current_user = MagicMock(id=user_id, email="test@gmail.com")
    
    # 2. Mock Logic Path: No existing booking + Slot available
    mock_repo.check_existing_booking.return_value = None
    mock_repo.find_and_decrement_slot.return_value = {"_id": event_id}
    
    mock_booking = {
        "_id": ObjectId(), 
        "event_id": ObjectId(event_id), 
        "user_id": ObjectId(user_id)
    }
    mock_repo.insert_booking.return_value = mock_booking

    # 3. Patch Celery Task
    with patch("app.services.booking_service.send_booking_notification_task.delay") as mock_email:
        
        result = await service.register_booking(event_id, current_user)

        # 4. Assertions
        assert result["event_id"] == event_id
        assert result["user_id"] == user_id
        
        # Verify Background Task received STRINGS, not ObjectIds
        mock_email.assert_called_once_with("test@gmail.com", str(mock_booking["_id"]))
        
        # Verify Cache Invalidation for the specific event
        mock_cache.delete_cache.assert_called_once_with(f"event:{event_id}")

@pytest.mark.asyncio
async def test_register_booking_double_booking():
    mock_repo = AsyncMock()
    mock_cache = AsyncMock()
    service = BookingService(mock_repo,mock_cache)
    service.repo = mock_repo

    # 5. Simulate existing booking
    mock_repo.check_existing_booking.return_value = {"_id": "exists"}

    with pytest.raises(BadRequest) as exc:
        await service.register_booking("event_id", MagicMock())
    
    assert "already registered" in str(exc.value)
    mock_repo.insert_booking.assert_not_called()

@pytest.mark.asyncio
async def test_register_booking_event_full():
    mock_repo = AsyncMock()
    mock_cache = AsyncMock()
    service = BookingService(mock_repo,mock_cache)
    service.repo = mock_repo

    # 6. No double booking, but EVENT IS FULL (returns None)
    mock_repo.check_existing_booking.return_value = None
    mock_repo.find_and_decrement_slot.return_value = None

    with pytest.raises(BadRequest) as exc:
        await service.register_booking("event_id", MagicMock())
    
    assert "full or does not exist" in str(exc.value)

@pytest.mark.asyncio
async def test_all_booking_success():
    # 1. Setup Mocks
    mock_repo = AsyncMock()
    mock_cache = AsyncMock()
    service = BookingService(mock_repo,mock_cache)
    service.repo = mock_repo

    user_id = "660adb23f51bb4362e0020ee"
    current_user = MagicMock()
    current_user.id = user_id

    # 2. Mock Repository Return (List of bookings)
    mock_bookings = [
        {
            "_id": "69cfb035fba805883788a3cf",
            "user_id": user_id,
            "event_id": "event_1",
            "status": "completed"
        },
        {
            "_id": "69cfb035fba805883788a3d0",
            "user_id": user_id,
            "event_id": "event_2",
            "status": "completed"
        }
    ]
    mock_repo.show_bookings.return_value = mock_bookings

    # 3. Execute Service Method
    result = await service.all_booking(current_user)

    # 4. Assertions
    assert len(result) == 2
    assert result[0]["user_id"] == user_id
    # Verify the service called the repo with the CORRECT user ID
    mock_repo.show_bookings.assert_called_once_with(user_id)

@pytest.mark.asyncio
async def test_all_booking_empty():
    mock_repo = AsyncMock()
    mock_cache = AsyncMock()
    service = BookingService(mock_repo,mock_cache)
    service.repo = mock_repo

    current_user = MagicMock(id="new_user_id")
    
    # Simulate a user with no bookings
    mock_repo.show_bookings.return_value = []

    result = await service.all_booking(current_user)

    assert result == []
    mock_repo.show_bookings.assert_called_once_with("new_user_id")