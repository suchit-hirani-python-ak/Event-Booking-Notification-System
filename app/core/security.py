from datetime import datetime,timedelta,timezone
import jwt
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
import redis.asyncio as redis
from app.core.config import settings
from app.schemas.users import UserCreate

redis_client = redis.from_url(settings.redis_url, decode_responses = True)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/login')

password_hash = CryptContext(schemes=[settings.encription], deprecated="auto")

def hash_password(password: str):
    return password_hash.hash(password)

def verify_password(pain_password: str, hash_password: str):
    return password_hash.verify(pain_password,hash_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=settings.access_expire_in_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode,settings.access_token.get_secret_value(),algorithm=settings.algorithm)

def refresh_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(days=settings.refresh_expire_in_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode,settings.refresh_token.get_secret_value(),algorithm=settings.algorithm)

def generate_tokens(user:UserCreate):
    access_token = create_access_token(
        data={"sub": user["email"]}
    )
    refresh_token = refresh_access_token(
        data={"sub":user["email"]}
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "type": "bearer"
    }