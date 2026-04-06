from unittest.mock import AsyncMock

import pytest
from app.exception.error import BadRequest, NotFound
from app.services.event_service import EventService


@pytest.mark.asyncio
async def test_all_user_event_cache_hit():
    # 1. Setup Mocks
    mock_cache = AsyncMock()
    mock_repo = AsyncMock()
    service = EventService(mock_cache,mock_repo)
    service.cache = mock_cache
    service.repo = mock_repo

    # 2. Simulate CACHE HIT
    cached_data = [{"title": "Cached Event", "_id": "1"}]
    mock_cache.get_cache.return_value = cached_data

    # 3. Execute
    result = await service.all_user_event()

    # 4. Assertions
    assert result == cached_data
    mock_cache.get_cache.assert_called_once_with("events:list")
    # Repo should NOT be called if cache hits
    mock_repo.get_all.assert_not_called()
    mock_cache.set_cache.assert_not_called()

@pytest.mark.asyncio
async def test_all_user_event_cache_miss():
    mock_cache = AsyncMock()
    mock_repo = AsyncMock()
    service = EventService(mock_cache,mock_repo)
    service.cache = mock_cache
    service.repo = mock_repo

    # 1. Simulate CACHE MISS
    mock_cache.get_cache.return_value = None
    db_data = [{"title": "DB Event", "_id": "2"}]
    mock_repo.get_all.return_value = db_data

    # 2. Execute
    result = await service.all_user_event()

    # 3. Assertions
    assert result == db_data
    mock_cache.get_cache.assert_called_once_with("events:list")
    # Repo MUST be called
    mock_repo.get_all.assert_called_once()
    # Data MUST be cached for next time with TTL 60
    mock_cache.set_cache.assert_called_once_with("events:list", db_data, ttl=60)
    
@pytest.mark.asyncio
async def test_event_by_id_invalid_length():
    service = EventService(db=AsyncMock(),redis=AsyncMock())
    
    # 1. Test validation logic (ID < 24 chars)
    with pytest.raises(BadRequest) as exc:
        await service.event_by_id("short_id")
    
    assert "size is less than 24" in str(exc.value)

@pytest.mark.asyncio
async def test_event_by_id_cache_hit():
    mock_cache = AsyncMock()
    mock_repo = AsyncMock()
    service = EventService(mock_cache,mock_repo)
    service.cache = mock_cache
    service.repo = mock_repo

    valid_id = "660adb23f51bb4362e0020ee"
    cached_event = {"_id": valid_id, "title": "Cached Event"}
    
    # 2. Simulate Cache Hit
    mock_cache.get_cache.return_value = cached_event

    result = await service.event_by_id(valid_id)

    assert result == cached_event
    mock_cache.get_cache.assert_called_once_with(f"event:{valid_id}")
    mock_repo.get_by_id.assert_not_called()

@pytest.mark.asyncio
async def test_event_by_id_cache_miss_and_not_found():
    mock_cache = AsyncMock()
    mock_repo = AsyncMock()
    service = EventService(mock_cache,mock_repo)
    service.cache = mock_cache
    service.repo = mock_repo

    valid_id = "660adb23f51bb4362e0020ee"
    
    # 3. Simulate Cache Miss + Database Not Found
    mock_cache.get_cache.return_value = None
    mock_repo.get_by_id.return_value = None

    with pytest.raises(NotFound) as exc:
        await service.event_by_id(valid_id)
    
    assert "event not found" in str(exc.value)
    mock_cache.set_cache.assert_not_called()

@pytest.mark.asyncio
async def test_event_by_id_cache_miss_success():
    mock_cache = AsyncMock()
    mock_repo = AsyncMock()
    service = EventService(mock_cache,mock_repo)
    service.cache = mock_cache
    service.repo = mock_repo

    valid_id = "660adb23f51bb4362e0020ee"
    db_event = {"_id": valid_id, "title": "DB Event"}
    
    # 4. Simulate Cache Miss + Database Success
    mock_cache.get_cache.return_value = None
    mock_repo.get_by_id.return_value = db_event

    result = await service.event_by_id(valid_id)

    assert result == db_event
    # Verify it was saved to cache with TTL 120
    mock_cache.set_cache.assert_called_once_with(f"event:{valid_id}", db_event, ttl=120)