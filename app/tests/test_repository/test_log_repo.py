import pytest
from datetime import datetime
from bson import ObjectId
from app.repositories.log_repository import LogRepository

@pytest.mark.asyncio
async def test_create_log_repo(db):
    # 1. Setup Repo with real DB
    repo = LogRepository(db)

    log_payload = {
        "method": "POST",
        "path": "/auth/register",
        "status_code": 200,
        "user_id": "660adb23f51bb4362e0020ee"
    }

    # 2. Execute: Repository adds 'timestamp' and inserts
    await repo.create_log(log_payload)

    # 3. Assertions on the payload object
    assert "timestamp" in log_payload
    assert isinstance(log_payload["timestamp"], str)
    
    # 4. Verify the data actually exists in the "Logs" collection
    # Note: Use "Logs" or "logs" depending on your repo's __init__
    inserted_log = await db["RequestLogs"].find_one({"user_id": "660adb23f51bb4362e0020ee"})
    
    assert inserted_log is not None
    assert inserted_log["method"] == "POST"
    assert "timestamp" in inserted_log

@pytest.mark.asyncio
async def test_create_log_timestamp_format(db):
    repo = LogRepository(db)

    # Capture a baseline time just before the call
    start_time = datetime.now().isoformat()
    
    # Execute
    await repo.create_log({"event": "testing_timestamp"})
    
    # Retrieve from real DB
    log_in_db = await db["RequestLogs"].find_one({"event": "testing_timestamp"})
    
    # The log timestamp should be a string and >= our baseline start_time
    assert log_in_db["timestamp"] >= start_time
    # Verify it can be parsed back into a datetime object
    assert datetime.fromisoformat(log_in_db["timestamp"])
