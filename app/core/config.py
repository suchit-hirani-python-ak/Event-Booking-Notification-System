from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
class Settings(BaseSettings):
    algorithm: str
    mongo_url: str
    redis_url: str
    access_token: SecretStr
    refresh_token: SecretStr
    access_expire_in_minutes: int 
    refresh_expire_in_days: int 
    encription: str
    mail_username: str
    mail_password: SecretStr
    mail_from: str
    mail_port: int
    admin_name: str
    admin_pass: str
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )
        
settings = Settings() # type: ignore loads from .env file