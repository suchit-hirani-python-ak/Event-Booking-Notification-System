import pytest
from bson import ObjectId
from app.repositories.event_repository import EventRepository

@pytest.mark.asyncio
async def test_get_all_events_repo(db):
    repo = EventRepository(db)
    
    # 1. Seed data into "Events" collection
    await db["Events"].insert_many([
        {"title": "Event 1", "location": "London"},
        {"title": "Event 2", "location": "Paris"}
    ])

    # 2. Execute
    result = await repo.get_all()

    # 3. Assertions
    assert len(result) == 2
    titles = [event["title"] for event in result]
    assert "Event 1" in titles
    assert "Event 2" in titles

@pytest.mark.asyncio
async def test_update_by_id_repo(db):
    repo = EventRepository(db)

    # 1. Seed an event
    fake_id = "660adb23f51bb4362e0020ee"
    await db["Events"].insert_one({
        "_id": ObjectId(fake_id),
        "title": "Original Title",
        "location": "Old York"
    })

    update_data = {"location": "New York"}

    # 2. Execute
    result = await repo.update_by_id(fake_id, update_data)

    # 3. Assertions
    assert result is not None
    assert result["location"] == "New York"
    assert result["title"] == "Original Title"  # Ensure other fields remain
    
    # 4. Verify in DB
    db_entry = await db["Events"].find_one({"_id": ObjectId(fake_id)})
    assert db_entry["location"] == "New York"

@pytest.mark.asyncio
async def test_delete_by_id_repo(db):
    repo = EventRepository(db)

    # 1. Seed an event
    fake_id = "660adb23f51bb4362e0020ee"
    await db["Events"].insert_one({"_id": ObjectId(fake_id), "title": "To be deleted"})

    # 2. Execute
    result = await repo.delete_by_id(fake_id)

    # 3. Assertions
    assert result is not None
    assert str(result["_id"]) == fake_id
    
    # 4. Verify it's actually gone from the DB
    remaining = await db["Events"].find_one({"_id": ObjectId(fake_id)})
    assert remaining is None

@pytest.mark.asyncio
async def test_delete_by_id_not_found(db):
    repo = EventRepository(db)
    
    # Attempt to delete non-existent ID
    result = await repo.delete_by_id(str(ObjectId()))
    
    assert result is None
