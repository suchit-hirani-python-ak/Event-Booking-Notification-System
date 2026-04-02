from unittest.mock import patch
import pytest
from app.exception.error import Forbidden
from app.services.user_service import UserService
from app.schemas.users import UserCreate
from app.core.config import settings

@pytest.mark.asyncio
async def test_service_registration_logic(fake_db):
    service = UserService(fake_db)
    user_in = UserCreate(email="service@test.com", password="plain_password")
    
    # The service should hash the password before calling the repo
    created_user = await service.register_user(user_in)
    
    assert created_user["email"] == "service@test.com"
    # Logic check: It must NOT be the plain text password
    assert created_user["password"] != "plain_password"
    assert len(created_user["password"]) > 20 # Standard for hashes


@pytest.mark.asyncio
async def test_admin(fake_db):
    service = UserService(fake_db)
    admin_data = UserCreate(email="admin@gmail.com", password="hash_pass")
    
    with patch("app.services.user_service.send_welcome_email_task.delay") as mock_email:
        # Action: Pass the correct secrets from settings
        admin = await service.register_admin(
            admin_data, 
            secret_name=settings.admin_name, 
            secret_pass=settings.admin_pass
        )
        
        # Verify Celery was called
        mock_email.assert_called_once()
        mock_email.assert_called_once_with("admin@gmail.com")
    
    assert admin["email"] == "admin@gmail.com"
    assert admin["password"] != "hash_pass"
    assert len(admin["password"]) > 20
    
@pytest.mark.asyncio
async def test_register_admin_forbidden_secrets(fake_db):
    service = UserService(fake_db)
    user_in = UserCreate(email="hacker@test.com", password="123")
    
    # Action & Verification: Should raise Forbidden
    with pytest.raises(Forbidden) as exc: # Replace Exception with your Forbidden class
        await service.register_admin(user_in, "wrong_name", "wrong_pass")
    