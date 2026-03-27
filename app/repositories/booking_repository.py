from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase

from app.schemas.tokens import TokenResponse

class BookingRepository:
    def __init__(self, db: AsyncDatabase):
        self.bookings = db.get_collection("Bookings")
        self.events = db.get_collection("Events")

    async def find_and_decrement_slot(self, event_id: str):
        # Atomic check: Decrement only if available_slots > 0
        return await self.events.find_one_and_update(
            {"_id": ObjectId(event_id), "available_slots": {"$gt": 0}},
            {"$inc": {"available_slots": -1}},
            return_document=True
        )

    async def insert_booking(self, booking_data: dict):
        result = await self.bookings.insert_one(booking_data)
        booking_data["_id"] = result.inserted_id
        return booking_data

    async def check_existing_booking(self, event_id: str, user_id: str):
        # Prevents duplicate bookings by the same user
        return await self.bookings.find_one({
            "event_id": ObjectId(event_id), 
            "user_id": ObjectId(user_id)
        })
    
    async def show_bookings(self, id: str):
        return await self.bookings.find({"user_id":ObjectId(id)}).to_list(length=None)
