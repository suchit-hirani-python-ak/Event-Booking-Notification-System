import pytest
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
from datetime import datetime, timedelta
from app.repositories.notification_repository import NotificationRepository

@pytest.mark.asyncio
async def test_log_notification_upsert():
    # 1. Setup Mocks
    mock_collection = AsyncMock()
    mock_db = MagicMock()
    mock_db.get_collection.return_value = mock_collection
    repo = NotificationRepository(mock_db)

    booking_id = "660adb23f51bb4362e0020ee"
    email = "test@gmail.com"
    status = "sent"
    attempt = 1

    # 2. Execute
    await repo.log_notification(booking_id, email, status, attempt)

    # 3. Assertions: Verify the ATOMIC operators ($set and $setOnInsert)
    # Verify the filter uses ObjectId
    expected_query = {"booking_id": ObjectId(booking_id)}
    
    # Verify the update document structure
    args, kwargs = mock_collection.update_one.call_args
    
    assert args[0] == expected_query
    assert "$set" in args[1]
    assert args[1]["$set"]["status"] == "sent"
    assert args[1]["$set"]["attempts"] == 1
    
    # Verify $setOnInsert exists and upsert is True
    assert "$setOnInsert" in args[1]
    assert "created_at" in args[1]["$setOnInsert"]
    assert kwargs["upsert"] is True

@pytest.mark.asyncio
async def test_log_notification_retry_update():
    mock_collection = AsyncMock()
    mock_db = MagicMock()
    mock_db.get_collection.return_value = mock_collection
    repo = NotificationRepository(mock_db)

    booking_id = "660adb23f51bb4362e0020ee"
    
    # Simulate a RETRY (attempt 2, status failed)
    await repo.log_notification(booking_id, "test@gmail.com", "failed", 2)

    args, _ = mock_collection.update_one.call_args
    assert args[1]["$set"]["attempts"] == 2
    assert args[1]["$set"]["status"] == "failed"
