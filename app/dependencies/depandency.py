import jwt
from fastapi import Depends, HTTPException
from app.core.config import settings
from app.core.security import oauth2_scheme,redis_client
from app.exception.error import Forbidden,Unauthorized
from app.schemas.tokens import TokenResponse
from app.schemas.users import UserCreate, UserResponse

def get_current_user(token: str=Depends(oauth2_scheme)) -> TokenResponse:
    try:
        payload = jwt.decode(token,settings.access_token.get_secret_value(),algorithms=settings.algorithm)
        data = TokenResponse(**payload)
        return data
    except:
        raise Unauthorized()
        

class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: TokenResponse = Depends(get_current_user)):
        if user.role != self.allowed_roles:
            raise Forbidden()
        return user

allow_admin = RoleChecker(["admin"])
allow_all = RoleChecker(["admin","user"])

async def get_redis():
    yield redis_client