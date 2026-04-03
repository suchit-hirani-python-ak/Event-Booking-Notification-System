import pytest
from datetime import datetime
from unittest.mock import patch, AsyncMock


date = datetime.now()
@pytest.mark.asyncio
@patch("app.services.event_service.EventService.all_user_event", new_callable=AsyncMock)
async def test_all_event(mock_get_all, client):
    
    # FIX: Add 'created_at' and 'updated_at' to match your response model
    mock_get_all.return_value = [{
        "_id": "69c6460dde3abb1df795fd75",
        "title": "karan ajula",
        "date": "2026-04-28T07:00:00Z",
        "location": "IIM, Ahmedabad",
        "total_slots": 500,
        "available_slots": 485,
        "created_by": "660adb23f51bb4362e0020ee",
        "created_at": date, # Added
        "updated_at": date # Added
    }]

    response = await client.get("/events")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["title"] == "karan ajula"
    mock_get_all.assert_called_once()

@pytest.mark.asyncio
@patch("app.services.event_service.EventService.event_by_id", new_callable=AsyncMock)
async def test_event_id(mock_get_all, client):
    id = "69c6460dde3abb1df795fd75"
    # FIX: Add 'created_at' and 'updated_at' to match your response model
    mock_get_all.return_value = {
        "_id": "69c6460dde3abb1df795fd75",
        "title": "karan ajula",
        "date": "2026-04-28T07:00:00Z",
        "location": "IIM, Ahmedabad",
        "total_slots": 500,
        "available_slots": 485,
        "created_by": "660adb23f51bb4362e0020ee",
        "created_at": "2026-03-27T14:25:41.406582", # Added
        "updated_at": "2026-03-27T14:25:41.406582"  # Added
    }

    response = await client.get(f"/events/{id}")
    assert response.status_code == 200
    assert response.json()["_id"] == "69c6460dde3abb1df795fd75"
    mock_get_all.assert_called_once()