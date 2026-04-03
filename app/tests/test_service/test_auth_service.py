from jwt import ExpiredSignatureError
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.exception.error import BadRequest, Forbidden, NotFound, Unauthorized
from app.services.user_service import UserService

@pytest.mark.asyncio
async def test_register_user_logic():
    # 1. Mock the Repository (Database layer)
    mock_repo = AsyncMock()
    
    # 2. Mock the Celery Task (so it doesn't try to send real email)
    with patch("app.services.user_service.send_welcome_email_task.delay") as mock_email:
        
        # Initialize Service with the mock repo
        # If your Service creates the repo in __init__, patch the Repository class instead
        service = UserService(db=AsyncMock())
        service.repo = mock_repo 

        # Define input (Pydantic model or dict)
        user_in = MagicMock()
        user_in.email = "test@gmail.com"
        user_in.password = "password123"
        user_in.model_dump.return_value = {"email": "test@gmail.com", "password": "password123"}

        # Set up Mock behavior
        mock_repo.find_by_email.return_value = None # Simulate user doesn't exist
        mock_repo.create_user.return_value = {"_id": "123", "email": "test@gmail.com"}

        # 3. Call the service method directly
        result = await service.register_user(user_in)

        # 4. Assertions
        assert result["email"] == "test@gmail.com"
        mock_repo.find_by_email.assert_called_once_with("test@gmail.com")
        mock_repo.create_user.assert_called_once()
        mock_email.assert_called_once_with("test@gmail.com")

@pytest.mark.asyncio
async def test_register_user_already_exists():
    mock_repo = AsyncMock()
    service = UserService(db=AsyncMock())
    service.repo = mock_repo

    user_in = MagicMock()
    user_in.email = "existing@gmail.com"
    
    # Simulate user ALREADY exists
    mock_repo.find_by_email.return_value = {"_id": "1"}

    # Assert that the service raises the correct Exception
    with pytest.raises(BadRequest) as exc:
        await service.register_user(user_in)
    
    assert str(exc.value.message) == "User already exists"

@pytest.mark.asyncio
async def test_login_success():
    # 1. Setup Mocks
    mock_repo = AsyncMock()
    mock_redis = AsyncMock()
    
    # Path to where redis_client is imported in your service
    with patch("app.services.user_service.redis_client", mock_redis), \
         patch("app.services.user_service.verify_password", return_value=True), \
         patch("app.services.user_service.generate_tokens", return_value={"access_token": "abc"}):
        
        service = UserService(db=AsyncMock())
        service.repo = mock_repo
        
        # 2. Define Input (Mocking OAuth2PasswordRequestForm)
        payload = MagicMock()
        payload.username = "test@gmail.com"
        payload.password = "password123"

        # 3. Define Mock Behaviors
        mock_redis.exists.return_value = False # Not locked out
        mock_repo.find_by_email.return_value = {"email": "test@gmail.com", "password": "hashed_password"}

        # 4. Run Service
        result = await service.login_user(payload, MagicMock())

        # 5. Assertions
        assert result["access_token"] == "abc"
        mock_redis.delete.assert_called_once_with(f"attempts:test@gmail.com")

@pytest.mark.asyncio
async def test_login_lockout_triggered():
    mock_repo = AsyncMock()
    mock_redis = AsyncMock()
    
    with patch("app.services.user_service.redis_client", mock_redis), \
         patch("app.services.user_service.verify_password", return_value=False):
        
        service = UserService(db=AsyncMock())
        service.repo = mock_repo
        
        payload = MagicMock()
        payload.username = "victim@gmail.com"
        
        # 1. Simulate 5th failed attempt
        mock_redis.exists.return_value = False
        mock_repo.find_by_email.return_value = {"password": "..."}
        mock_redis.incr.return_value = 5 # This triggers the lockout

        # 2. Run and check for Forbidden exception
        with pytest.raises(Exception) as exc: # Use Forbidden if imported
            await service.login_user(payload, MagicMock())
        
        assert "Too many attempts" in str(exc.value)
        
        # 3. Verify Redis set the lockout key for 10 mins (600s)
        mock_redis.setex.assert_called_once_with(f"lockout:victim@gmail.com", 600, "locked")
        mock_redis.delete.assert_called_once_with(f"attempts:victim@gmail.com")
        
@pytest.mark.asyncio
async def test_refresh_token_success():
    mock_repo = AsyncMock()
    service = UserService(db=AsyncMock())
    service.repo = mock_repo

    # 1. This is what the DECODER returns
    mock_payload = {"sub": "test@gmail.com", "type": "refresh"}
    
    # 2. Patch the DECODER and the GENERATOR
    with patch("jwt.decode", return_value=mock_payload), \
         patch("app.services.user_service.generate_tokens", return_value={"access": "new_at"}):
        
        mock_repo.find_by_email.return_value = {"email": "test@gmail.com"}

        result = await service.refresh_token("any_string_works_now")

        assert result["access"] == "new_at"
        mock_repo.find_by_email.assert_called_once_with("test@gmail.com")

@pytest.mark.asyncio
async def test_refresh_token_invalid_type():
    service = UserService(db=AsyncMock())
    mock_payload = {"sub": "test@gmail.com", "type": "access"} # Wrong type
    
    # FIX: Patch jwt.decode so it returns the "access" payload
    with patch("jwt.decode", return_value=mock_payload):
        with pytest.raises(Unauthorized) as exc:
            await service.refresh_token("mocked_token")
        
        assert "This is not a refresh token" in str(exc.value)

@pytest.mark.asyncio
async def test_refresh_token_expired():
    service = UserService(db=AsyncMock())
    
    # FIX: Patch jwt.decode to raise the actual Expired error
    # Use the exact exception your service catches (e.g. jwt.ExpiredSignatureError)
    with patch("jwt.decode", side_effect=ExpiredSignatureError):
        with pytest.raises(Unauthorized) as exc:
            await service.refresh_token("mocked_token")
            
        assert "Refresh token expired" in str(exc.value)
        

@pytest.mark.asyncio
async def test_register_admin_wrong_secrets():
    service = UserService(db=AsyncMock())
    
    # 3. Call with wrong secrets should raise Forbidden
    with pytest.raises(Forbidden):
        await service.register_admin(MagicMock(), "wrong_user", "wrong_pass")

@pytest.mark.asyncio
async def test_delete_account_success():
    mock_repo = AsyncMock()
    service = UserService(db=AsyncMock())
    service.repo = mock_repo
    
    # Mock TokenResponse object
    mock_token = MagicMock()
    mock_token.id = "user_123"
    
    # 4. Simulate successful deletion (repo returns True)
    mock_repo.remove_user.return_value = True
    
    result = await service.delete_user_account(mock_token)
    
    assert result["message"] == "User successfully deleted"
    mock_repo.remove_user.assert_called_once_with("user_123")

@pytest.mark.asyncio
async def test_delete_account_not_found():
    mock_repo = AsyncMock()
    service = UserService(db=AsyncMock())
    service.repo = mock_repo
    
    # 5. Simulate failed deletion (repo returns False)
    mock_repo.remove_user.return_value = False
    
    with pytest.raises(NotFound) as exc:
        await service.delete_user_account(MagicMock(id="unknown"))
    
    assert "User not found" in str(exc.value)