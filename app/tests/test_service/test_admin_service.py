import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
from app.exception.error import BadRequest, Forbidden, NotFound
from app.services.event_service import EventService

@pytest.mark.asyncio
async def test_create_event_success():
    mock_repo = AsyncMock()
    mock_cache = AsyncMock()
    service = EventService(mock_cache,mock_repo)
    service.repo = mock_repo
    service.cache = mock_cache

    # 1. Setup Input Payload and User
    payload = MagicMock()
    payload.available_slots = 10
    payload.total_slots = 20
    payload.model_dump.return_value = {"title": "Test Event"}
    
    current_user = MagicMock()
    current_user.id = "660adb23f51bb4362e0020ee"

    # 2. Mock Repo Return
    mock_repo.create_event.return_value = {"_id": "event_123", "title": "Test Event"}

    # 3. Run Service
    result = await service.create_event_for_user(payload, current_user)

    # 4. Assertions
    assert result["_id"] == "event_123"
    mock_repo.create_event.assert_called_once()
    mock_cache.delete_cache.assert_called_once_with("events:list")
    
    # Verify ObjectId conversion and timestamps
    args, _ = mock_repo.create_event.call_args
    assert isinstance(args[0]["created_by"], ObjectId)
    assert "created_at" in args[0]

@pytest.mark.asyncio
async def test_create_event_invalid_slots():
    service = EventService(db=AsyncMock(),redis=AsyncMock())
    
    # 5. Case: Available slots > Total slots
    payload = MagicMock()
    payload.available_slots = 50
    payload.total_slots = 10
    
    with pytest.raises(BadRequest) as exc:
        await service.create_event_for_user(payload, MagicMock())
    
    assert "available slots cannot exceed total slots" in str(exc.value)

@pytest.mark.asyncio
async def test_create_event_negative_slots():
    service = EventService(db=AsyncMock(),redis=AsyncMock())
    
    # 6. Case: Negative values
    payload = MagicMock()
    payload.available_slots = -1
    payload.total_slots = 10
    
    with pytest.raises(BadRequest) as exc:
        await service.create_event_for_user(payload, MagicMock())
    
    assert "value cannot be negative" in str(exc.value)


@pytest.mark.asyncio
async def test_update_id_success():
    mock_repo = AsyncMock()
    mock_cache = AsyncMock()
    service = EventService(mock_repo,mock_cache)
    service.repo = mock_repo
    service.cache = mock_cache

    event_id = "660adb23f51bb4362e0020ee"
    user_id = "user_123"

    # 1. Setup Mock User (Admin & Owner)
    current_user = MagicMock()
    current_user.id = user_id
    current_user.role = "admin"

    # 2. Setup Mock Database State
    existing_event = {"_id": event_id, "created_by": user_id}
    mock_repo.get_by_id.return_value = existing_event
    
    updated_data = {"_id": event_id, "title": "New Title"}
    mock_repo.update_by_id.return_value = updated_data

    # 3. Payload
    payload = MagicMock()
    payload.model_dump.return_value = {"title": "New Title"}

    # 4. Execute
    result = await service.update_id(event_id, payload, current_user)

    # 5. Assertions
    assert result["title"]== "New Title" # type: ignore
    # Ensure cache for BOTH the list and the specific ID is cleared
    mock_cache.delete_cache.assert_called_once_with("events:list", f"event:{event_id}")
    mock_repo.update_by_id.assert_called_once()

@pytest.mark.asyncio
async def test_update_id_not_owner():
    mock_repo = AsyncMock()
    mock_cache = AsyncMock()
    service = EventService(mock_repo,mock_cache)
    service.repo = mock_repo

    event_id = "event_123"
    # User is admin but NOT the one who created the event
    current_user = MagicMock(id="hacker_id", role="admin")
    existing_event = {"_id": event_id, "created_by": "original_owner_id"}
    
    mock_repo.get_by_id.return_value = existing_event

    # 6. Verify Forbidden Error
    with pytest.raises(Forbidden) as exc:
        await service.update_id(event_id, MagicMock(), current_user)
    
    assert "You can only edit your own events" in str(exc.value)
    mock_repo.update_by_id.assert_not_called()

@pytest.mark.asyncio
async def test_update_id_not_admin():
    mock_repo = AsyncMock()
    mock_cache= AsyncMock()
    service = EventService(mock_repo,mock_cache)
    service.repo = mock_repo

    # 7. User is owner but NOT an admin
    current_user = MagicMock(id="user_123", role="user")
    mock_repo.get_by_id.return_value = {"created_by": "user_123"}

    with pytest.raises(Forbidden):
        await service.update_id("id", MagicMock(), current_user)
        
@pytest.mark.asyncio
async def test_delete_id_success():
    mock_repo = AsyncMock()
    mock_cache = AsyncMock()
    service = EventService(mock_repo,mock_cache)
    service.repo = mock_repo
    service.cache = mock_cache

    event_id = "660adb23f51bb4362e0020ee"
    user_id = "admin_123"

    # 1. Mock Admin & Owner User
    current_user = MagicMock()
    current_user.id = user_id
    current_user.role = "admin"

    # 2. Mock Database State
    mock_repo.get_by_id.return_value = {"_id": event_id, "created_by": user_id}
    mock_repo.delete_by_id.return_value = {"message": "Event deleted"}

    # 3. Execute
    result = await service.delete_id(event_id, current_user)

    # 4. Assertions
    assert result["message"] == "Event deleted" # type: ignore
    # Ensure cache is invalidated for BOTH the list and the specific ID
    mock_cache.delete_cache.assert_called_once_with("events:list", f"event:{event_id}")
    mock_repo.delete_by_id.assert_called_once_with(event_id)

@pytest.mark.asyncio
async def test_delete_id_forbidden_not_owner():
    mock_repo = AsyncMock()
    mock_cache = AsyncMock()
    service = EventService(mock_repo,mock_cache)
    service.repo = mock_repo

    event_id = "event_123"
    # User is admin but NOT the owner
    current_user = MagicMock(id="stranger_id", role="admin")
    mock_repo.get_by_id.return_value = {"_id": event_id, "created_by": "owner_id"}

    # 5. Verify Ownership Protection
    with pytest.raises(Forbidden) as exc:
        await service.delete_id(event_id, current_user)
    
    assert "You can only delete your own events" in str(exc.value)
    mock_repo.delete_by_id.assert_not_called()

@pytest.mark.asyncio
async def test_delete_id_not_found():
    mock_repo = AsyncMock()
    mock_cache = AsyncMock()
    service = EventService(mock_repo,mock_cache)
    service.repo = mock_repo

    # 6. Simulate Event doesn't exist
    mock_repo.get_by_id.return_value = None

    with pytest.raises(NotFound) as exc:
        await service.delete_id("any_id", MagicMock())
    
    assert "event not found" in str(exc.value)