from datetime import datetime
from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase

from app.dependencies.depandency import get_current_user
from app.exception.error import BadRequest, Forbidden, NotFound
from app.repositories.event_repository import EventRepository
from app.schemas.event import EventRequest
from app.schemas.tokens import TokenResponse
from app.schemas.users import UserResponse

class EventService:
    def __init__(self,db:AsyncDatabase):
        self.repo = EventRepository(db)
        
    async def create_event_for_user(self, payload: EventRequest, current_user: TokenResponse):
        event = payload.model_dump()
        if payload.available_slots > payload.total_slots:
            raise BadRequest("available slots cannot exceed form total slots")
        
        event.update({
            "created_by": ObjectId(current_user.id), 
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        })
        
        return await self.repo.create_event(event)
    
    async def all_user_event(self):
        return await self.repo.get_all()
    
    async def event_by_id(self, id: str):
        return await self.repo.get_by_id(id)
    
    async def update_id(self, event_id: str, payload: EventRequest, user: TokenResponse):
        
        existing_event = await self.repo.get_by_id(event_id)
        if not existing_event:
            raise NotFound("event not found")
        if payload.available_slots > payload.total_slots:
            raise BadRequest("available slots cannot exceed form total slots")
        
        if user.role != "admin":
            raise Forbidden()
        
        if (existing_event.get("created_by")) != user.id and user.role == "admin":
             raise Forbidden("You can only edit your own events")

        update_dict = payload.model_dump()
        update_dict["updated_at"] = datetime.now().isoformat()

        return await self.repo.update_by_id(event_id, update_dict)