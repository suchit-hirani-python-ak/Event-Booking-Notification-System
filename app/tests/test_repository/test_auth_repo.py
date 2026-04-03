import pytest
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
from app.repositories.user_repository import UserRepository

@pytest.mark.asyncio
async def test_create_user_repo():
    # 1. Mock the MongoDB Collection
    mock_collection = AsyncMock()
    mock_db = MagicMock()
    mock_db.get_collection.return_value = mock_collection

    # 2. Initialize Repo
    repo = UserRepository(mock_db)
    
    # 3. Setup Mock Behavior
    mock_result = MagicMock()
    mock_result.inserted_id = ObjectId("660adb23f51bb4362e0020ee")
    mock_collection.insert_one.return_value = mock_result

    user_data = {"email": "test@gmail.com", "password": "hashed_password"}

    # 4. Execute
    result = await repo.create_user(user_data)

    # 5. Assertions
    # Check if the result contains the string version of the ID
    assert result["_id"] == "660adb23f51bb4362e0020ee"
    # Verify the EXACT MongoDB command was sent
    mock_collection.insert_one.assert_called_once_with(user_data)

@pytest.mark.asyncio
async def test_find_by_id_repo():
    mock_collection = AsyncMock()
    mock_db = MagicMock()
    mock_db.get_collection.return_value = mock_collection
    repo = UserRepository(mock_db)

    test_id = "660adb23f51bb4362e0020ee"
    mock_collection.find_one.return_value = {"_id": ObjectId(test_id), "email": "test@test.com"}

    result = await repo.find_by_id(test_id)

    # Verify that the string ID was correctly converted to an ObjectId for the query
    mock_collection.find_one.assert_called_once_with({"_id": ObjectId(test_id)})
    assert result["email"] == "test@test.com" #type: ignore
    
@pytest.mark.asyncio
async def test_find_by_email_repo():
    mock_collection = AsyncMock()
    mock_db = MagicMock()
    mock_db.get_collection.return_value = mock_collection
    repo = UserRepository(mock_db)

    test_id = "kimber@gmail.com"
    mock_collection.find_one.return_value = {"email": "kimber@gmail.com"}

    result = await repo.find_by_email(test_id)

    # Verify that the string ID was correctly converted to an ObjectId for the query
    mock_collection.find_one.assert_called_once_with({"email":"kimber@gmail.com"})
    assert result["email"] == "kimber@gmail.com" #type: ignore

@pytest.mark.asyncio
async def test_remove_user_repo_success():
    mock_collection = AsyncMock()
    mock_db = MagicMock()
    mock_db.get_collection.return_value = mock_collection
    repo = UserRepository(mock_db)

    # 6. Mock a successful deletion
    mock_result = MagicMock()
    mock_result.deleted_count = 1
    mock_collection.delete_one.return_value = mock_result

    test_id = "660adb23f51bb4362e0020ee"
    success = await repo.remove_user(test_id)

    assert success is True
    mock_collection.delete_one.assert_called_once_with({"_id": ObjectId(test_id)})
