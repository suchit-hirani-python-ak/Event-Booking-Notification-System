from datetime import datetime
from pymongo.asynchronous.database import AsyncDatabase
class LogRepository:
    def __init__(self, db:AsyncDatabase):
        self.collection = db.get_collection("RequestLogs")

    async def create_log(self, log_data: dict):
        log_data["timestamp"] = datetime.now().isoformat()
        await self.collection.insert_one(log_data)
