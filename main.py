from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from app.db.session import db_manager,get_db
from app.api import event_all_route, event_route, user_route
from app.exception.error import BaseException
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
app.include_router(user_route.router,prefix="/auth",tags=["Authentication"])
app.include_router(event_route.router,prefix="/events",tags=["event"])
app.include_router(event_all_route.router,prefix="/booking",tags=["Bookings"])

@app.get("/")
def server():
    return "server is running"

@app.exception_handler(BaseException)
async def global_app_exception_handler(request: Request, exc: BaseException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.message,
            "path": request.url.path,
            "timestamp": datetime.now().isoformat(),
        },headers={"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    )

if __name__ == "__main__":
    uvicorn.run("main:app",port=8001,host="0.0.0.0",reload=True)