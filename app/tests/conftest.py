import pytest
import asyncio
import uuid
from pymongo import AsyncMongoClient
from httpx import AsyncClient, ASGITransport
from main import app
from app.db.session import get_db
from app.core.config import settings

@pytest.fixture(scope="function")
def event_loop():
    """Forces a fresh loop for every test to prevent cross-test contamination."""
    loop = asyncio.new_event_loop()
    yield loop
    # Drain any remaining tasks before closing
    loop.run_until_complete(asyncio.sleep(0))
    loop.close()

@pytest.fixture
async def fake_db():
    test_db_name = f"test_{uuid.uuid4().hex[:8]}"
    client = AsyncMongoClient(settings.mongo_url)
    db = client[test_db_name]
    
    try:
        yield db
    finally:
        # 1. Cleanup Data
        await client.drop_database(test_db_name)
        # 2. Close Connection (Must be awaited)
        await client.close()
        # 3. CRITICAL: Wait for the SSL 'Bad file descriptor' noise to settle 
        # before the event loop is destroyed
        await asyncio.sleep(0.2) 

@pytest.fixture
async def async_client(fake_db):
    # Override the DB dependency
    app.dependency_overrides[get_db] = lambda: fake_db
    # Use ASGITransport for HTTPX 0.28+ compatibility
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
