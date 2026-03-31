from datetime import datetime
from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase

class NotificationRepository:
    def __init__(self, db:AsyncDatabase):
        self.collection = db.get_collection("Notification")

    async def log_notification(self, booking_id: str, email: str, status: str, attempt: int, message: str = "Booking confirmed"):
        """
        Updates the notification log for a specific booking.
        If no log exists (first attempt), it creates one.
        """
        query = {"booking_id": ObjectId(booking_id)}
        
        update_data = {
            "$set": {
                "status": status,      # "sent" or "failed"
                "attempts": attempt,   # 1, 2, or 3
            },
            # setOnInsert only runs the very first time the record is created
            "$setOnInsert": {
                "created_at": datetime.now().isoformat()
            }
        }

        # upsert=True is the key to preventing duplicate records
        await self.collection.update_one(query, update_data, upsert=True)
