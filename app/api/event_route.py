from typing import Annotated
from fastapi import APIRouter, Depends
from pymongo.asynchronous.database import AsyncDatabase
from app.db.session import get_db
from app.schemas.event import EventRequest, EventResponse
from app.schemas.tokens import TokenResponse
from app.schemas.users import UserResponse
from app.services.event_service import EventService
from app.dependencies.depandency import allow_admin

router = APIRouter()

@router.post("", response_model=EventResponse)
async def add_event(
    payload: EventRequest, 
    db: Annotated[AsyncDatabase, Depends(get_db)],
    current_user: Annotated[TokenResponse, Depends(allow_admin)]
):  
    return await EventService(db).create_event_for_user(payload, current_user)

@router.put("/{id}",response_model=EventResponse)
async def update_event(
    id: str,
    payload: EventRequest,
    db: Annotated[AsyncDatabase,Depends(get_db)],
    current_user: Annotated[TokenResponse, Depends(allow_admin)]
):
    return await EventService(db).update_id(id, payload, current_user)

@router.delete("/{id}")
async def delete_event(
    event_id: str,
    db: Annotated[AsyncDatabase,Depends(get_db)],
    current_user: Annotated[TokenResponse, Depends(allow_admin)]
):
    delete = await EventService(db).delete_id(event_id, current_user)
    return f"deleted successfully"