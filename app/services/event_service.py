from datetime import datetime
from bson import ObjectId
import json
from redis.asyncio import Redis
from pymongo.asynchronous.database import AsyncDatabase
from app.dependencies.depandency import get_current_user
from app.exception.error import BadRequest, Forbidden, NotFound
from app.repositories.event_repository import EventRepository
from app.schemas.event import EventRequest
from app.schemas.tokens import TokenResponse


class EventService:
    def __init__(self, db: AsyncDatabase, redis: Redis):
        self.repo = EventRepository(db)
        self.redis = redis
        
    async def create_event_for_user(self, payload: EventRequest, current_user: TokenResponse):
        if payload.available_slots > payload.total_slots:
            raise BadRequest("available slots cannot exceed form total slots")
        
        event_data = payload.model_dump()
        event_data.update({
            "created_by": ObjectId(current_user.id), 
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        })
        
        new_event = await self.repo.create_event(event_data)
        
        # Invalidate List
        await self.redis.delete("events:list")
        return new_event
    
    async def all_user_event(self):
        # 1. Check Cache
        cached = await self.redis.get("events:list")
        if cached:
            return json.loads(cached)
        # 2. Get from DB
        events = await self.repo.get_all()
        
        # 3. Set Cache (60s TTL)
        await self.redis.set("events:list", json.dumps(events, default=str), ex=60)
        return events
    
    async def event_by_id(self, id: str):
        cache_key = f"event:{id}"
        
        # 1. Check Cache
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
            
        # 2. Get from DB
        event = await self.repo.get_by_id(id)
        if not event:
            raise NotFound("event not found")
            
        # 3. Set Cache (120s TTL)
        await self.redis.set(cache_key, json.dumps(event, default=str), ex=120)
        return event
    
    async def update_id(self, id: str, payload: EventRequest, user: TokenResponse):
        existing_event = await self.repo.get_by_id(id)
        if not existing_event: raise NotFound("event not found")
        if payload.available_slots > payload.total_slots: raise BadRequest("available slots cannot exceed form total slots")
        if user.role != "admin": raise Forbidden()
        
        # Logic fix: Allow edit if admin AND owner
        if str(existing_event.get("created_by")) != user.id:
             raise Forbidden("You can only edit your own events")

        update_dict = payload.model_dump()
        update_dict["updated_at"] = datetime.now().isoformat()

        updated_event = await self.repo.update_by_id(id, update_dict)
        
        # Invalidate List AND Detail
        await self.redis.delete("events:list", f"event:{id}")
        return updated_event
    
    async def delete_id(self, id: str, user: TokenResponse):
        existing_event = await self.repo.get_by_id(id)
        if not existing_event: raise NotFound("event not found")
        if user.role != "admin": raise Forbidden()
        if str(existing_event.get("created_by")) != user.id:
             raise Forbidden("You can only delete your own events")

        result = await self.repo.delete_by_id(id)
        
        # Invalidate List AND Detail
        await self.redis.delete("events:list", f"event:{id}")
        return result
