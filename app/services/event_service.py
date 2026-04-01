from datetime import datetime, timedelta
from bson import ObjectId
import json
from redis.asyncio import Redis
from pymongo.asynchronous.database import AsyncDatabase
from app.dependencies.depandency import get_current_user
from app.exception.error import BadRequest, Forbidden, NotFound
from app.repositories.event_repository import EventRepository
from app.schemas.event import EventRequest
from app.schemas.tokens import TokenResponse
from app.utils.redishelper import RedisHelper


class EventService:
    def __init__(self, db: AsyncDatabase, redis: Redis):
        self.repo = EventRepository(db)
        self.cache = RedisHelper(redis) # Use the helper
        
    async def create_event_for_user(self, payload: EventRequest, current_user: TokenResponse):
        if payload.available_slots > payload.total_slots:
            raise BadRequest("available slots cannot exceed total slots")
        
        event_data = payload.model_dump()
        event_data.update({
            "created_by": ObjectId(current_user.id), 
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        })
        
        new_event = await self.repo.create_event(event_data)
        await self.cache.delete_cache("events:list")
        return new_event
    
    async def all_user_event(self):
        # 1. Check Cache
        cached = await self.cache.get_cache("events:list")
        if cached: return cached
        
        # 2. Get from DB & Set Cache
        events = await self.repo.get_all()
        await self.cache.set_cache("events:list", events, ttl=60)
        return events
    
    async def event_by_id(self, id: str):
        cache_key = f"event:{id}"
        
        # 1. Check Cache
        cached = await self.cache.get_cache(cache_key)
        if cached: return cached
            
        # 2. Get from DB
        event = await self.repo.get_by_id(id)
        if not event: raise NotFound("event not found")
            
        # 3. Set Cache
        await self.cache.set_cache(cache_key, event, ttl=120)
        return event
    
    async def update_id(self, id: str, payload: EventRequest, user: TokenResponse):
        existing_event = await self.repo.get_by_id(id)
        if not existing_event: 
            raise NotFound("event not found")
        if user.role != "admin": 
            raise Forbidden()
        if str(existing_event.get("created_by")) != user.id:
             raise Forbidden("You can only edit your own events")

        update_dict = payload.model_dump()
        update_dict["updated_at"] = datetime.now() + timedelta(hours=5,minutes=30)

        updated_event = await self.repo.update_by_id(id, update_dict)
        
        # Invalidate multiple keys at once
        await self.cache.delete_cache("events:list", f"event:{id}")
        return updated_event

    async def delete_id(self, id: str, user: TokenResponse):
        # 1. Check existence and permissions
        existing_event = await self.repo.get_by_id(id)
        if not existing_event: 
            raise NotFound("event not found")
        if user.role != "admin": 
            raise Forbidden()
        if str(existing_event.get("created_by")) != user.id:
             raise Forbidden("You can only delete your own events")

        # 2. Perform deletion
        result = await self.repo.delete_by_id(id)
        
        # 3. Invalidate relevant cache keys
        await self.cache.delete_cache("events:list", f"event:{id}")
        return result
