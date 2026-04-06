import pytest
from bson import ObjectId
from datetime import datetime
from app.repositories.notification_repository import NotificationRepository

@pytest.mark.asyncio
async def test_log_notification_upsert_real_db(db):
    # 1. Setup Repo with real DB (Assuming collection name is "Notifications")
    repo = NotificationRepository(db)
    
    booking_id = "660adb23f51bb4362e0020ee"
    email = "test@gmail.com"
    
    # 2. First execution: This should trigger an INSERT (upsert)
    await repo.log_notification(booking_id, email, "sent", 1)

    # 3. Verify it exists in the real DB
    # Note: Use the exact case "Notifications" or "notifications" from your repo
    record = await db["Notification"].find_one({"booking_id": ObjectId(booking_id)})
    
    assert record is not None
    assert record["status"] == "sent"
    assert record["attempts"] == 1
    assert "created_at" in record
    
    first_created_at = record["created_at"]

    # 4. Second execution: Simulate a RETRY (update)
    # This should update status/attempts but NOT overwrite created_at
    await repo.log_notification(booking_id, email, "failed", 2)
    
    updated_record = await db["Notification"].find_one({"booking_id": ObjectId(booking_id)})
    
    assert updated_record["status"] == "failed"
    assert updated_record["attempts"] == 2
    # CRITICAL: created_at must remain the same because of $setOnInsert
    assert updated_record["created_at"] == first_created_at

@pytest.mark.asyncio
async def test_log_notification_retry_update_real_db(db):
    repo = NotificationRepository(db)
    booking_id = "660adb23f51bb4362e0020ee"
    
    # Seed an existing record
    await db["Notification"].insert_one({
        "booking_id": ObjectId(booking_id),
        "status": "pending",
        "attempts": 0
    })

    # Execute retry update via repo
    await repo.log_notification(booking_id, "test@gmail.com", "failed", 2)

    # Verify atomic update
    result = await db["Notification"].find_one({"booking_id": ObjectId(booking_id)})
    assert result["status"] == "failed"
    assert result["attempts"] == 2
