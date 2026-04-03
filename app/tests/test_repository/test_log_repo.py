import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from app.repositories.log_repository import LogRepository

@pytest.mark.asyncio
async def test_create_log_repo():
    # 1. Setup Mocks
    mock_collection = AsyncMock()
    mock_db = MagicMock()
    mock_db.get_collection.return_value = mock_collection
    repo = LogRepository(mock_db)

    log_payload = {
        "method": "POST",
        "path": "/auth/register",
        "status_code": 200,
        "user_id": "660adb23f51bb4362e0020ee"
    }

    # 2. Execute
    await repo.create_log(log_payload)

    # 3. Assertions
    # Verify that 'timestamp' was added to the dict before inserting
    assert "timestamp" in log_payload
    # Ensure it's a valid ISO string
    assert isinstance(log_payload["timestamp"], str)
    
    # Verify the MongoDB insert call
    mock_collection.insert_one.assert_called_once_with(log_payload)

@pytest.mark.asyncio
async def test_create_log_timestamp_format():
    mock_collection = AsyncMock()
    mock_db = MagicMock()
    mock_db.get_collection.return_value = mock_collection
    repo = LogRepository(mock_db)

    # Check that the timestamp is generated right now
    start_time = datetime.now().isoformat()
    await repo.create_log({"event": "test"})
    
    # The log timestamp should be equal to or later than our start_time
    args, _ = mock_collection.insert_one.call_args
    assert args[0]["timestamp"] >= start_time
