from datetime import datetime
from pymongo.asynchronous.database import AsyncDatabase
from bson import ObjectId

from app.exception.error import BadRequest
from app.repositories.booking_repository import BookingRepository
from app.schemas.tokens import TokenResponse


class BookingService:
    def __init__(self, db: AsyncDatabase):
        self.repo = BookingRepository(db)

    async def register_booking(self, event_id: str, user: TokenResponse):
        # 1. Check if user already booked this event
        existing = await self.repo.check_existing_booking(event_id, user.id)
        if existing:
            raise BadRequest("You have already registered for this event")

        # 2. Try to reserve a slot (Atomic)
        event = await self.repo.find_and_decrement_slot(event_id)
        if not event:
            raise BadRequest("Event is full or does not exist")

        # 3. Create the booking document
        booking_data = {
            "event_id": ObjectId(event_id),
            "user_id": ObjectId(user.id),
            "status":"completed",
            "created": datetime.now().isoformat()
        }

        return await self.repo.insert_booking(booking_data)

    async def all_booking(self,user: TokenResponse):
        return await self.repo.show_bookings(user.id)