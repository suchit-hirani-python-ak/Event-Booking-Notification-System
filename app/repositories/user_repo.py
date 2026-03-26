import jwt
from pymongo.asynchronous.database import AsyncDatabase
from bson import ObjectId


class UserRepository:
    def __init__(self, db: AsyncDatabase):
        self.collection =  db.get_collection("users")

    async def create_user(self, user_data: dict) -> dict:
        result = await self.collection.insert_one(user_data)
        user_data["_id"] = result.inserted_id
        return user_data

    async def find_by_email(self, email: str):
        return await self.collection.find_one({"email": email})

    async def find_by_id(self):
        return await self.collection.find_one({"_id":str(ObjectId)})
    
    