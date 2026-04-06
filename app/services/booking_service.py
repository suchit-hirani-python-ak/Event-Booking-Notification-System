import asyncio
from bson import ObjectId
from datetime import datetime
from pymongo.asynchronous.database import AsyncDatabase
from redis.asyncio import Redis
from app.exception.error import BadRequest
from app.repositories.booking_repository import BookingRepository
from app.repositories.notification_repository import NotificationRepository
from app.schemas.tokens import TokenResponse
from app.utils.celery import send_booking_notification_task
from app.utils.redishelper import RedisHelper

class BookingService:
    def __init__(self, db: AsyncDatabase, redis: Redis):
        self.repo = BookingRepository(db)
        self.cache = RedisHelper(redis)

    async def register_booking(self, event_id: str, user: TokenResponse):
        # 1. Double-booking check
        existing = await self.repo.check_existing_booking(event_id, user.id)
        if existing:
            raise BadRequest("You have already registered for this event")
        # 2. Atomic Slot Reservation (DB Truth)
        event = await self.repo.find_and_decrement_slot(event_id)
        
        if not event:
            raise BadRequest("Event is full or does not exist")
        
        # 3. Cache Invalidation (CRITICAL)
        await self.cache.delete_cache(f"event:{event_id}")

        # 4. Create Booking Document
        booking_data = {
            "event_id": ObjectId(event_id),
            "user_id": ObjectId(user.id),
            "status": "completed",
            "created_at": datetime.now().isoformat()
        }
        
        new_booking = await self.repo.insert_booking(booking_data)
        
        # FIX: Ensure IDs and emails are STRINGS before passing to Background Tasks
        booking_id = str(new_booking["_id"])

        
        # Use asyncio.create_task to run the retry logic in the background
        send_booking_notification_task.delay(user.email, booking_id) #type: ignore


        # 6. Prepare Return Data
        # We convert ObjectIds to strings so the ResponseModel doesn't crash
        new_booking["_id"] = str(new_booking["_id"])
        new_booking["event_id"] = str(new_booking["event_id"])
        new_booking["user_id"] = str(new_booking["user_id"])
        
        return new_booking



    async def all_booking(self,user: TokenResponse):
        return await self.repo.show_bookings(user.id)