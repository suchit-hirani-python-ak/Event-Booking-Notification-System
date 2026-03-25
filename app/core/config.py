from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
class Settings(BaseSettings):
    mongo_url: str
    redis_url: str
    access_token: SecretStr
    refresh_token: SecretStr
    access_expire_in_minutes: str 
    refresh_expire_in_days: str 
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )
        
settings = Settings() # type: ignore loads from .env file