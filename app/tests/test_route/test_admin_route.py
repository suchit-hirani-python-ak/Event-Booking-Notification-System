import pytest
from unittest.mock import patch, AsyncMock

import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_create_event(admin_client):
    payload = {
        "title": "karan ajula",
        "date": "2026-04-28T07:00:00Z",
        "location": "IIM, Ahmedabad",
        "total_slots": 500,
        "available_slots": 485
    }

    headers = {"Authorization": "Bearer fake-token"}


    with patch("app.services.event_service.EventService.create_event_for_user", new_callable=AsyncMock) as mock_create:
        
        mock_create.return_value = {
            "_id": "69c6460dde3abb1df795fd75",
            "title": "karan ajula",
            "date": "2026-04-28T07:00:00Z",
            "location": "IIM, Ahmedabad",
            "total_slots": 500,
            "available_slots": 485,
            "created_by": "660adb23f51bb4362e0020ee",
            "created_at": "2026-03-27T14:25:41.406582",
            "updated_at": "2026-03-27T15:50:03.827577"
        }

        # Ensure plural "/events" to match your main.py prefix
        response = await admin_client.post("/events", json=payload, headers=headers)

        assert response.status_code == 200
        assert response.json()["title"] == "karan ajula"
        mock_create.assert_called_once()

@pytest.mark.asyncio
async def test_update_event(admin_client):
    payload = {
        "title": "karan ajula",
        "date": "2026-04-28T07:00:00Z",
        "location": "IIT, Bombay",
        "total_slots": 500,
        "available_slots": 500
    }
    event_id = "69c6460dde3abb1df795fd75"
    headers = {"Authorization": "Bearer fake-token"}

    # 1. FIX: Patch the update method, NOT create_event_for_user
    # Ensure the path "app.services.event_service.EventService.update_event" is correct for your app
    with patch("app.services.event_service.EventService.update_id", new_callable=AsyncMock) as mock_update:
        
        mock_update.return_value = {
            "_id": event_id,
            "title": "karan ajula",
            "date": "2026-04-28T07:00:00Z",
            "location": "IIT, Bombay",
            "total_slots": 500,
            "available_slots": 500,
            "created_by": "660adb23f51bb4362e0020ee",
            "created_at": "2026-03-27T14:25:41.406582",
            "updated_at": "2026-03-27T15:50:03.827577"
        }

        response = await admin_client.put(f"/events/{event_id}", json=payload, headers=headers)

        assert response.status_code == 200
        assert response.json()["location"] == "IIT, Bombay"
        mock_update.assert_called_once()
        
        
@pytest.mark.asyncio
async def test_delete_event(admin_client):
    event_id = "69c6460dde3abb1df795fd75"
    headers = {"Authorization": "Bearer fake-token"}

    with patch("app.services.event_service.EventService.delete_id", new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value = "deleted successfully"

        # Note the URL uses {id} but we pass event_id in params to match your current route
        response = await admin_client.delete(
            f"/events/{event_id}", 
            headers=headers, 
            params={"event_id": event_id} 
        )

        assert response.status_code == 200
        assert response.json() == "deleted successfully"

