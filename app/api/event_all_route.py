from typing import Annotated, List
from redis.asyncio import Redis
from pymongo.asynchronous.database import AsyncDatabase
from app.db.session import get_db
from app.schemas.books import BookingResponse
from app.schemas.event import EventAllResponse, EventResponse
from app.schemas.tokens import TokenResponse
from app.services.booking_service import BookingService
from app.services.event_service import EventService
from fastapi import APIRouter, Depends
from app.dependencies.depandency import get_current_user,get_redis


router = APIRouter()

@router.get("",response_model=List[EventResponse])
async def all(db:Annotated[AsyncDatabase,Depends(get_db)],redis: Annotated[Redis, Depends(get_redis)],):
    return await EventService(db,redis).all_user_event()

@router.get("/me",response_model=List[BookingResponse])
async def get_my_bookings(db:Annotated[AsyncDatabase,Depends(get_db)], user: Annotated[TokenResponse,Depends(get_current_user)],redis: Annotated[Redis, Depends(get_redis)],):
    return await BookingService(db,redis).all_booking(user)
    
@router.get("/{id}",response_model=EventAllResponse)
async def by_id(db:Annotated[AsyncDatabase,Depends(get_db)],redis: Annotated[Redis, Depends(get_redis)],id: str):
    return await EventService(db,redis).event_by_id(id)

@router.post("/{id}",response_model=BookingResponse)
async def register_booking(db:Annotated[AsyncDatabase,Depends(get_db)],
                     id: str,
                     token:Annotated[TokenResponse,Depends(get_current_user)],
                     redis: Annotated[Redis, Depends(get_redis)],):
    return await BookingService(db,redis).register_booking(id,token)

