import pytest
from app.repositories.user_repository import UserRepository

@pytest.mark.asyncio
async def test_repo_create_user(fake_db):
    repo = UserRepository(fake_db)
    user_data = {"email": "repo@test.com", "password": "123", "role": "user"}
    
    created_user = await repo.create_user(user_data)
    
    # Verify directly in the test database
    assert "_id" in created_user
    
    # Test Find (Direct Query)
    found = await fake_db["users"].find_one({"email": "repo@test.com"})
    assert found is not None
    assert found["password"] == "123"
    
