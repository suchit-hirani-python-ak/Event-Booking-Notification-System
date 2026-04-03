from datetime import datetime
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from main import app
from app.dependencies.depandency import get_current_user
from app.db.session import get_db
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.fixture
def mock_db():
    db = AsyncMock()
    # Explicitly mock common DB methods as AsyncMocks
    db.find_one = AsyncMock()
    db.insert_one = AsyncMock()
    db.update_one = AsyncMock()
    db.delete_one = AsyncMock()
    return db

@pytest_asyncio.fixture
async def client(mock_db):
    with patch("app.dependencies.depandency.redis_client", AsyncMock()):
        # FIX: Use MagicMock so user.role works
        mock_user = MagicMock()
        mock_user.id = "660adb23f51bb4362e0020ee"
        mock_user.email = "suchit@gmail.com"
        mock_user.role = "user"

        app.dependency_overrides = {
            get_db: lambda: mock_db,
            get_current_user: lambda: mock_user
        }

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac
        app.dependency_overrides.clear()
        
        
@pytest_asyncio.fixture
async def admin_client(client):
    # Create a mock for an Admin user
    mock_admin = MagicMock()
    mock_admin.id = "660adb23f51bb4362e0020ee"
    mock_admin.role = "admin"  # MUST match the role in your RoleChecker(["admin"])
    mock_admin.email = "admin@suchit.com"

    # Override the dependency
    app.dependency_overrides[get_current_user] = lambda: mock_admin
    
    yield client
    
    # Optional: Clear after test
    app.dependency_overrides.pop(get_current_user, None)
