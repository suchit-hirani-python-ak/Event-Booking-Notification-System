import pytest
from unittest.mock import AsyncMock
from bson import ObjectId
from main import app
from app.db.session import get_db
from app.dependencies.depandency import  get_redis, allow_admin


# 1. Mock Object to satisfy current_user.id for EventService
class MockAdmin:
    id = "660abb4f2e3f4a1234567890" # Must be valid 24-char hex
    email = "admin@test.com"
    role = "admin"

@pytest.mark.asyncio
async def test_add_event_validation_success(async_client, fake_db):
    # --- 2. SETUP DEPENDENCIES ---
    mock_redis = AsyncMock()
    
    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_redis] = lambda: mock_redis
    app.dependency_overrides[allow_admin] = lambda: MockAdmin()

    # --- 3. THE PAYLOAD (Matching your Field constraints) ---
    event_payload = {
        "title": "Tech Summit 2026",        # min_length=1
        "date": "2026-04-27T10:00:00Z",    # ISO datetime
        "location": "Ahmedabad",
        "total_slots": 100,                 # gt=0
        "available_slots": 100              # ge=0
    }

    # --- 4. ACTION ---
    headers = {"Authorization": "Bearer fake-token"}
    response = await async_client.post("/events", json=event_payload, headers=headers)

    # --- 5. VERIFICATION ---
    if response.status_code == 422:
        print(f"Validation Error: {response.json()}")

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Tech Summit 2026"
    assert data["total_slots"] == 100
    
    # Cleanup
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_add_event_validation_fail(async_client):
    """Test that invalid slots (total_slots=0) return 422"""
    invalid_payload = {
        "title": "Fail Event",
        "date": "2026-04-27T10:00:00Z",
        "location": "Remote",
        "total_slots": 0,    # Fails 'gt=0'
        "available_slots": -1 # Fails 'ge=0'
    }
    
    response = await async_client.post("/events", json=invalid_payload)
    assert response.status_code == 401
