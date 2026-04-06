from typing import Annotated, List
from redis.asyncio import Redis
from fastapi import APIRouter, Depends
from pymongo.asynchronous.database import AsyncDatabase
from app.db.session import get_db
from app.schemas.event import EventRequest, EventResponse
from app.schemas.tokens import TokenResponse
from app.services.event_service import EventService
from app.dependencies.depandency import allow_admin,get_redis

router = APIRouter()


@router.get("",response_model=List[EventResponse])
async def all(db:Annotated[AsyncDatabase,Depends(get_db)],
              redis: Annotated[Redis, Depends(get_redis)])-> List[dict]:
    """By connecting with redis and db show list of events as response

    Args:
        db (Annotated[AsyncDatabase,Depends): connection with db with get_db
        redis (Annotated[Redis, Depends): connection with redis with get_redis

    Returns:
        List[dict]: list of all events
    """
    return await EventService(db,redis).all_user_event()

@router.post("", response_model=EventResponse)
async def add_event(
    payload: EventRequest, 
    db: Annotated[AsyncDatabase, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[TokenResponse, Depends(allow_admin)]
)-> dict:  
    """Only works if admin try to create event no other roles have access

    Args:
        payload (EventRequest): take data from pydantic
        db (Annotated[AsyncDatabase, Depends): connection with db with get_db
        redis (Annotated[Redis, Depends):connection with redis with get_redis
        current_user (Annotated[TokenResponse, Depends): check admin by token

    Returns:
        dict: add event as response
    """
    return await EventService(db,redis).create_event_for_user(payload, current_user)

@router.put("/{id}",response_model=EventResponse)
async def update_event(
    id: str,
    payload: EventRequest,
    db: Annotated[AsyncDatabase,Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[TokenResponse, Depends(allow_admin)]
)->None:
    """Only works if admin try to update event no other roles have access

    Args:
        id: provide event id to update event data
        payload (EventRequest): take data from pydantic
        db (Annotated[AsyncDatabase, Depends): connection with db with get_db
        redis (Annotated[Redis, Depends):connection with redis with get_redis
        current_user (Annotated[TokenResponse, Depends): check admin by token

    Returns:
        dict: add event as response
    """
    return await EventService(db,redis).update_id(id, payload, current_user)

@router.delete("/{id}")
async def delete_event(
    event_id: str,
    db: Annotated[AsyncDatabase,Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[TokenResponse, Depends(allow_admin)]
)->str:
    """Only works if admin try to delete event no other roles have access

    Args:
        id: provide event id to delete event data
        payload (EventRequest): take data from pydantic
        db (Annotated[AsyncDatabase, Depends): connection with db with get_db
        redis (Annotated[Redis, Depends): connection with redis with get_redis
        current_user (Annotated[TokenResponse, Depends): check admin by token

    Returns:
        dict: add event as response
    """
    delete = await EventService(db,redis).delete_id(event_id, current_user)
    return f"deleted successfully"

@router.get("/{id}",response_model=EventResponse)
async def by_id(db:Annotated[AsyncDatabase,Depends(get_db)],
                redis: Annotated[Redis, Depends(get_redis)],
                id: str
)->dict:
    """By providing id gets data as output of event

    Args:
        db (Annotated[AsyncDatabase,Depends): connection with db with get_db
        redis (Annotated[Redis, Depends): connection with redis with get_redis
        id (str): get event id 

    Returns:
        dict: give data of serched event
    """
    return await EventService(db,redis).event_by_id(id)