import pytest
from bson import ObjectId
from app.repositories.user_repository import UserRepository

@pytest.mark.asyncio
async def test_create_user_repo(db):
    repo = UserRepository(db)
    user_data = {"email": "test@gmail.com", "password": "hashed_password"}

    # 1. Execute
    result = await repo.create_user(user_data)

    # 2. Assertions
    assert "_id" in result
    # assert isinstance(result["_id"], str)
    
    # 3. Verify in Real DB
    found = await db.users.find_one({"email": "test@gmail.com"})
    assert found is not None
    assert str(found["_id"]) == result["_id"]

@pytest.mark.asyncio
async def test_find_by_id_repo(db):
    repo = UserRepository(db)
    
    # Seed data directly into the test DB
    inserted = await db.users.insert_one({"email": "find_me@test.com"})
    test_id = str(inserted.inserted_id)

    # Execute
    result = await repo.find_by_id(test_id)

    assert result is not None
    assert result["email"] == "find_me@test.com"
    # Ensure the repo returns a dict or object as expected
    assert str(result["_id"]) == test_id

@pytest.mark.asyncio
async def test_find_by_email_repo(db):
    repo = UserRepository(db)
    
    email = "kimber@gmail.com"
    await db.users.insert_one({"email": email})

    # Execute
    result = await repo.find_by_email(email)

    assert result is not None
    assert result["email"] == email

@pytest.mark.asyncio
async def test_remove_user_repo_success(db):
    repo = UserRepository(db)
    
    # Seed data
    inserted = await db.users.insert_one({"email": "delete_me@test.com"})
    test_id = str(inserted.inserted_id)

    # Execute
    success = await repo.remove_user(test_id)

    # Assertions
    assert success is True
    # Verify deletion from actual DB
    remaining = await db.users.find_one({"_id": ObjectId(test_id)})
    assert remaining is None

@pytest.mark.asyncio
async def test_remove_user_repo_fail(db):
    repo = UserRepository(db)
    
    # Attempt to delete a non-existent ID
    fake_id = str(ObjectId())
    success = await repo.remove_user(fake_id)

    assert success is False
