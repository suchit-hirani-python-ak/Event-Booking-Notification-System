from datetime import datetime
from app.core.config import settings
import jwt
from pymongo.asynchronous.database import AsyncDatabase
from app.core.security import generate_tokens, hash_password, redis_client, verify_password
from fastapi import Response
from fastapi.security import OAuth2PasswordRequestForm
from app.exception.error import BadRequest, Forbidden, NotFound, Unauthorized
from app.repositories.user_repository import UserRepository
from app.schemas.users import UserCreate, UserResponse, UserRole
from app.utils.celery import send_welcome_email_task
class UserService:
    def __init__(self, db: AsyncDatabase):
        self.repo = UserRepository(db)

    async def register_user(self, user_in: UserCreate):
        # 1. Check if user exists
        if await self.repo.find_by_email(user_in.email):
            raise BadRequest("User already exists")

        send_welcome_email_task.delay(user_in.email) # type: ignore
        # 2. Convert to dict and HASH the password
        user_dict = user_in.model_dump()
        user_dict["role"] = UserRole.USER.value
        user_dict["password"] = hash_password(user_in.password) # <--- CRITICAL STEP
        
        # 3. Add timestamps
        user_dict["created_at"] = datetime.now().isoformat()
        
        
        # 4. Save to MongoDB
        return await self.repo.create_user(user_dict)

    async def login_user(self, payload: OAuth2PasswordRequestForm, response: Response):
            email = payload.username
            lockout_key = f"lockout:{email}"
            attempts_key = f"attempts:{email}"

            # 1. Check if user is currently locked out
            if await redis_client.exists(lockout_key):
                ttl = await redis_client.ttl(lockout_key)
                raise Forbidden(f"Account locked try again in {ttl//60} minutes")

            user = await self.repo.find_by_email(email)
            
            # 2. Verify Credentials
            if not user or not verify_password(payload.password, user.get("password")):
                # --- FAILURE BLOCK ---
                failed_count = await redis_client.incr(attempts_key)
                
                if failed_count == 1:
                    await redis_client.expire(attempts_key, 600) # 10 min window

                if failed_count >= 5:
                    await redis_client.setex(lockout_key, 600, "locked")
                    await redis_client.delete(attempts_key)
                    raise Forbidden("Too many attempts. Locked for 10 min.")
                    
                raise Unauthorized(f"Invalid credentials. {5 - failed_count} attempts left.")

            
            await redis_client.delete(attempts_key)

            tokens = generate_tokens(user)
            
            return tokens
        
    async def refresh_token(self, refresh_token: str):
        try:
            payload = jwt.decode(
                refresh_token, 
                settings.refresh_token.get_secret_value(), 
                algorithms=[settings.algorithm]
            )
        except jwt.exceptions.InvalidSignatureError:
            raise Unauthorized("Invalid refresh token signature")
        except jwt.exceptions.ExpiredSignatureError:
            raise Unauthorized("Refresh token expired")

        if payload.get("type") != "refresh":
            raise Unauthorized("This is not a refresh token")

        email = payload.get("sub")
        if not email:
            raise Unauthorized("Token payload missing email")

        user = await self.repo.find_by_email(email)
        if not user:
            raise NotFound("user not found")
                
        return generate_tokens(user)
    

    # async def register_admin(self, user_in: UserCreate, secret_name: str, secret_pass: str):
    #     # 1. Verify against .env secrets
    #     if secret_name != settings.admin_name or secret_pass != settings.admin_pass:
    #         raise Forbidden()

    #     # 2. Check if exists
    #     if await self.repo.find_by_email(user_in.email):
    #         raise BadRequest("email already exists")

    #     # 3. Force Admin Role
    #     user_dict = user_in.model_dump()
    #     user_dict["role"] = UserRole.ADMIN.value
    #     user_dict["password"] = hash_password(user_in.password)
    #     user_dict["created_at"] = datetime.now().isoformat()

    #     return await self.repo.create_user(user_dict)
