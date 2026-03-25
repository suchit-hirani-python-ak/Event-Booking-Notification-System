from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from app.db.session import db_manager,get_db
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB
    await db_manager.connect_to_mongo()
    yield
    # Shutdown: Close connection
    await db_manager.close_mongo_connection()

# 2. Pass the lifespan to the FastAPI app
app = FastAPI(lifespan=lifespan)

@app.get("/")
def server():
    return "server is running"


if __name__ == "__main__":
    uvicorn.run("main:app",port=8001,host="0.0.0.0",reload=True)