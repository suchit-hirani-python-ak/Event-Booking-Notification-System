from typing import Annotated, List
from pymongo.asynchronous.database import AsyncDatabase
from app.db.session import get_db
from app.schemas.event import EventAllResponse, EventResponse
from app.services.event_service import EventService
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("",response_model=List[EventResponse])
async def all(db:Annotated[AsyncDatabase,Depends(get_db)]):
    return await EventService(db).all_user_event()
    
@router.get("/{id}",response_model=EventAllResponse)
async def by_id(db:Annotated[AsyncDatabase,Depends(get_db)],id: str):
    return await EventService(db).event_by_id(id)