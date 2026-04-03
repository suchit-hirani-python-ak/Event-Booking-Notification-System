import pytest
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
from app.repositories.event_repository import EventRepository

@pytest.mark.asyncio
async def test_get_all_events_repo():
    # 1. Setup Mocks
    mock_collection = MagicMock() # Use MagicMock for the collection
    mock_db = MagicMock()
    mock_db.get_collection.return_value = mock_collection
    repo = EventRepository(mock_db)

    # 2. FIX: mock_collection.find must be a regular mock returning an AsyncMock
    mock_cursor = AsyncMock()
    mock_collection.find.return_value = mock_cursor
    
    # Define the data the cursor's to_list method returns
    mock_data = [{"title": "Event 1"}, {"title": "Event 2"}]
    mock_cursor.to_list.return_value = mock_data

    # 3. Execute
    result = await repo.get_all()

    # 4. Assertions
    assert len(result) == 2
    assert result[0]["title"] == "Event 1"
    
    # Verify the find() was called (regular call) and to_list was awaited
    mock_collection.find.assert_called_once_with({})
    mock_cursor.to_list.assert_called_once_with(length=None)

@pytest.mark.asyncio
async def test_update_by_id_repo():
    mock_collection = AsyncMock()
    mock_db = MagicMock()
    mock_db.get_collection.return_value = mock_collection
    repo = EventRepository(mock_db)

    event_id = "660adb23f51bb4362e0020ee"
    update_data = {"location": "New York"}
    
    # 4. Mock find_one_and_update behavior
    mock_collection.find_one_and_update.return_value = {"_id": ObjectId(event_id), "location": "New York"}

    result = await repo.update_by_id(event_id, update_data)

    # 5. Assertions
    assert result["location"] == "New York" # type: ignore
    mock_collection.find_one_and_update.assert_called_once_with(
        {"_id": ObjectId(event_id)},
        {"$set": update_data},
        return_document=True
    )

@pytest.mark.asyncio
async def test_delete_by_id_repo():
    mock_collection = AsyncMock()
    mock_db = MagicMock()
    mock_db.get_collection.return_value = mock_collection
    repo = EventRepository(mock_db)

    event_id = "660adb23f51bb4362e0020ee"
    mock_collection.find_one_and_delete.return_value = {"_id": ObjectId(event_id)}

    result = await repo.delete_by_id(event_id)

    # 6. Assertions
    assert result["_id"] == ObjectId(event_id) # type: ignore
    mock_collection.find_one_and_delete.assert_called_once_with({"_id": ObjectId(event_id)})
