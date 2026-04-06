import pytest
from bson import ObjectId
from app.repositories.booking_repository import BookingRepository

@pytest.mark.asyncio
async def test_find_and_decrement_slot_success(db):
    repo = BookingRepository(db)
    
    # 1. Use a valid 24-char hex string
    event_id_str = "660adb23f51bb4362e0020ee"
    
    # 2. SEED: Must use "Events" (Capital E) to match Repo
    await db["Events"].insert_one({
        "_id": ObjectId(event_id_str), 
        "available_slots": 10
    })

    # 3. Execute
    result = await repo.find_and_decrement_slot(event_id_str)

    # 4. Assert
    assert result is not None
    assert result["available_slots"] == 9
    
    # Verify DB actually updated
    updated = await db["Events"].find_one({"_id": ObjectId(event_id_str)})
    assert updated["available_slots"] == 9

@pytest.mark.asyncio
async def test_check_existing_booking(db):
    repo = BookingRepository(db)

    e_id, u_id = "660adb23f51bb4362e0020ee", "660adb23f51bb4362e0020ff"
    
    # 2. SEED: Must use "Bookings" (Capital B)
    await db["Bookings"].insert_one({
        "event_id": ObjectId(e_id),
        "user_id": ObjectId(u_id)
    })

    # 3. Execute
    result = await repo.check_existing_booking(e_id, u_id)

    assert result is not None
    assert str(result["event_id"]) == e_id
    assert str(result["user_id"]) == u_id

@pytest.mark.asyncio
async def test_show_bookings_real_db(db):
    repo = BookingRepository(db)
    user_id = "660adb23f51bb4362e0020ee"
    
    # 2. SEED: Use "Bookings"
    await db["Bookings"].insert_many([
        {"user_id": ObjectId(user_id), "event_name": "Concert"},
        {"user_id": ObjectId(user_id), "event_name": "Game"},
        {"user_id": ObjectId("660adb23f51bb4362e0020aa"), "event_name": "Other"}
    ])

    # 3. Execute
    result = await repo.show_bookings(user_id)

    # 4. Assert
    assert len(result) == 2
    assert all(str(b["user_id"]) == user_id for b in result)

@pytest.mark.asyncio
async def test_insert_booking_real_db(db):
    repo = BookingRepository(db)
    
    booking_data = {
        "event_id": ObjectId("660adb23f51bb4362e0020ee"),
        "user_id": ObjectId("660adb23f51bb4362e0020ff"),
        "status": "confirmed"
    }

    # Execute
    result = await repo.insert_booking(booking_data)

    # Assert
    assert "_id" in result
    assert isinstance(result["_id"], ObjectId)
    
    # Verify in DB
    in_db = await db["Bookings"].find_one({"_id": result["_id"]})
    assert in_db is not None
    assert in_db["status"] == "confirmed"
