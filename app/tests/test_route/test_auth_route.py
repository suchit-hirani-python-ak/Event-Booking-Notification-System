import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_register_user(client):
    payload = {
        "username": "testuser",
        "email": "testuser@gmail.com",
        "password": "test1234",
    }

    with patch("app.services.user_service.UserService.register_user", new_callable=AsyncMock) as mock_register, \
         patch("app.services.user_service.send_welcome_email_task.delay"):
        
        # REMOVE the {"user": ...} nesting. Return the fields directly.
        # Ensure _id is a valid 24-char hex string for PyObjectId
        mock_register.return_value = {
            "_id": "660adb23f51bb4362e0020ee", 
            "username": "testuser",
            "email": "testuser@gmail.com",
            "role": "user",
            "created_at": "2026-04-02T05:49:24.294Z",
        }

        response = await client.post("/auth/register", json=payload)

        # DEBUG: If it still fails, print(response.json()) to see the output
        assert response.status_code == 200
        assert response.json()["email"] == "testuser@gmail.com"
        mock_register.assert_called_once()


@pytest.mark.asyncio
async def test_login_user(client):
    payload = {"username": "testuser@gmail.com", "password": "testpassword"}

    # FIX: Patch 'login' method and wrap in a patch for Redis to prevent connection errors
    with patch("app.services.user_service.UserService.login_user", new_callable=AsyncMock) as mock_login, \
         patch("app.dependencies.depandency.redis_client", AsyncMock()): # Path to your redis instance
        
        mock_login.return_value = {
            "access_token": "mocked_token",
            "refresh_token": "mocked_refresh",
            "token_type": "bearer",
        }

        # route uses 'OAuth2PasswordRequestForm', use 'data=payload'
        # Pydantic model, use 'json=payload'
        response = await client.post("/auth/login", data=payload) 

        assert response.status_code == 200
        assert "access_token" in response.json()
        mock_login.assert_called_once()
    
@pytest.mark.asyncio
async def test_register_admin(admin_client):
    # Use the client provided by the fixture (admin_client)
    client = admin_client 
    
    payload = {
        "email": "testadmin@gmail.com", 
        "password": "testpassword"
    }

    # Headers required by your route definition
    headers = {
        "x-admin-user": "admin_name",
        "x-admin-pass": "admin_pass"  
    }

    # Patch the service method
    with patch("app.services.user_service.UserService.register_admin", new_callable=AsyncMock) as mock_register,\
         patch("app.services.user_service.send_welcome_email_task.delay"):
        
        # Mock MUST return fields matching UserResponse (flat dict), NOT tokens
        mock_register.return_value = {
            "_id": "660adb23f51bb4362e0020ee",
            "email": "testadmin@gmail.com",
            "role": "admin",
            "created_at": "2026-04-02T05:49:24.294Z"
        }

        # 1. Use 'json=' for Pydantic models
        # 2. Pass the required 'headers'
        response = await client.post("/auth/setup-root", json=payload, headers=headers) 

        assert response.status_code == 200
        assert response.json()["role"] == "admin"
        assert response.json()["email"] == "testadmin@gmail.com"
        mock_register.assert_called_once()

@pytest.mark.asyncio
async def test_refresh(client):
    # 1. Patch the service method as an AsyncMoc
        
        # 2. Mock return value matching your service's success response


    payload = {"refresh_token": "mocked_token"}

    # FIX: Patch 'login' method and wrap in a patch for Redis to prevent connection errors
    with patch("app.services.user_service.UserService.refresh_token", new_callable=AsyncMock) as mock_refresh: # Path to your redis instance
        
        mock_refresh.return_value = {
            "access_token": "mocked_token",
            "refresh_token": "mocked_refresh",
            "token_type": "bearer",
        }
        response = await client.post("/auth/refresh", params=payload)

        assert response.status_code == 200
        mock_refresh.assert_called_once_with("mocked_token")

@pytest.mark.asyncio
@patch("app.services.user_service.UserService.delete_user_account", new_callable=AsyncMock)
async def test_delete_user(mock_delete,client):
    # 1. Patch the service method as an AsyncMock
        
        # 2. Mock return value matching your service's success response
        mock_delete.return_value = {"message": "User successfully deleted"}

        # 3. Add the Authorization header. 
        # FastAPI's OAuth2PasswordBearer extracts the token from this header.
        headers = {"Authorization": "Bearer fake-token-string"}

        response = await client.delete("/auth/delete", headers=headers)

        assert response.status_code == 200
        assert response.json()["message"] == "User successfully deleted"
        mock_delete.assert_called_once()
        
