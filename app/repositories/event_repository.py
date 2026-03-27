from pymongo.asynchronous.database import AsyncDatabase

from bson import ObjectId

from app.schemas.event import EventRequest
class EventRepository:
    def __init__(self,db:AsyncDatabase) -> None:
        self.collection = db.get_collection("Events")
    
    async def create_event(self, event_dict: dict):
        result = await self.collection.insert_one(event_dict)
        event_dict["_id"] = result.inserted_id
        return event_dict
    
    async def get_all(self):
        return await self.collection.find({}).to_list(length=None)
    
    async def get_by_id(self, id: str):
        return await self.collection.find_one({"_id":ObjectId(id)})
    
    async def update_by_id(self, id: str, event_data: dict):
        update_operation = {"$set": event_data}
        
        updated_document = await self.collection.find_one_and_update(
            {"_id": ObjectId(id)},
            update_operation,
            return_document=True 
        )
        return updated_document