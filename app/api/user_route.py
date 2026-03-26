from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from app.db.session import get_db
from app.schemas.users import UserCreate, UserResponse
from app.repositories.user_repo import UserRepository
from app.schemas.tokens import Token
from app.services.user_service import UserService

router = APIRouter(prefix="/users")

@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate, db = Depends(get_db)):
    
    
    try:
        return await UserService(db).register_user(user_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login",response_model=Token)
async def login(response:Response,
    payload: Annotated[OAuth2PasswordRequestForm, Depends()],
    db = Depends(get_db)):
    return await UserService(db).login_user(payload,response)

@router.post("/refresh",response_model=Token)
async def refresh(refresh_token:str,db = Depends(get_db)):
    return await UserService(db).refresh_token(refresh_token)