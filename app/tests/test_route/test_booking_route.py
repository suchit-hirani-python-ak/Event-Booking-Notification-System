from httpx import patch
import pytest
from datetime import datetime
from unittest.mock import patch, AsyncMock

# Define a ISO-formatted string or ensure your model handles objects
date_str = datetime.now().isoformat()

@pytest.mark.asyncio
@patch("app.services.booking_service.BookingService.register_booking", new_callable=AsyncMock)
async def test_all_bookings(mock_get_all, client):
    headers = {"Authorization": "Bearer fake-token-string"}
    id = "69c6460dde3abb1df795fd75"
    # FIX: Use strings for dates to avoid serialisation issues in the mock return
    mock_get_all.return_value = {
  "_id": "69cfb035fba805883788a3cf",
  "user_id": "69ca62bb3ce84fae84ef20bb",
  "event_id": "69c6460dde3abb1df795fd75",
  "status": "completed",
  "created_at": "2026-04-03T12:19:01.404262"
}

    # FIX: Ensure the URL matches your router (is it /events or /bookings?)
    # If the service is 'all_user_event', the route is likely "/events"
    response = await client.post(f"/booking/{id}", headers=headers)

    assert response.status_code == 200
    mock_get_all.assert_called_once()

@pytest.mark.asyncio
# 1. FIX: Ensure the path to BookingService.all_booking is correct
@patch("app.services.booking_service.BookingService.all_booking", new_callable=AsyncMock)
async def test_all_bookings_me(mock_get_all, client):
    headers = {"Authorization": "Bearer fake-token-string"}
    
    # 2. Return a list of bookings
    mock_get_all.return_value = [{
        "_id": "69cfb035fba805883788a3cf",
        "user_id": "69ca62bb3ce84fae84ef20bb",
        "event_id": "69c6460dde3abb1df795fd75",
        "status": "completed",
        "created_at": "2026-04-03T12:19:01.404262"
    }]

    # 3. FIX: Use 'get' instead of 'post' for fetching data
    # 4. FIX: Check if your prefix is "/booking" or "/bookings"

    # If it 404s, try the plural form:
    response = await client.get("/booking/me", headers=headers)

    assert response.status_code == 200
    mock_get_all.assert_called_once()
