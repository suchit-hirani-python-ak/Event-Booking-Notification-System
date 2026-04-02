import pytest
from app.db.session import get_db
from main import app
from app.dependencies.depandency import  get_redis, allow_admin
from unittest.mock import AsyncMock

# 1. Mock Object so current_user.id works in your Service
class MockAdmin:
    id = "660abb4f2e3f4a1234567890" # Valid 24-char hex
    email = "admin@test.com"
    role = "admin"

@pytest.mark.asyncio
async def test_add_event_success(async_client, fake_db):
    # --- 2. SETUP DEPENDENCIES ---
    # Mock Redis to avoid connection errors
    mock_redis = AsyncMock()
    
    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_redis] = lambda: mock_redis
    app.dependency_overrides[allow_admin] = lambda: MockAdmin()

    # --- 3. THE PAYLOAD ---
    event_payload = {
        "title": "string",
        "date": "2026-04-02T12:11:54.544Z",
        "location": "string",
        "total_slots": 1,
        "available_slots": 0,
        "created_by": MockAdmin.id # Required by your EventRequest model
    }

    # --- 4. ACTION ---
    # Headers must exist to satisfy OAuth2Scheme, content is ignored due to override
    headers = {"Authorization": "Bearer fake-token"}
    response = await async_client.post("/events", json=event_payload, headers=headers)

    # --- 5. VERIFICATION ---
    if response.status_code == 422:
        print(f"Validation Error: {response.json()}")

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "string"
    assert data["total_slots"] == 1

    # Cleanup
    app.dependency_overrides.clear()
