import time
import uuid
from datetime import datetime
from fastapi import Request, BackgroundTasks

class Middleware:
    async def log_requests_middleware(self, request: Request, call_next):
        start_time = time.perf_counter()
        response = None
        
        try:
            # 1. Process the request (Dependencies run here)
            response = await call_next(request)
        except Exception as e:
            # If the route crashes, we still want to log the failure
            # Your global_app_exception_handler will eventually catch this
            raise e
        finally:
            # 2. Get DB from app state (Set in your lifespan)
            db = getattr(request.app.state, "db", None)
            
            if db is not None:
                execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
                

                # 4. Prepare the log payload
                log_data = {
                    "method": request.method,
                    "endpoint": request.url.path,
                    "status_code": response.status_code if response else 500, 
                    "response_time_ms": execution_time_ms,
                    "timestamp": datetime.now().isoformat()
                }

                # 5. Offload to BackgroundTasks
                from app.repositories.log_repository import LogRepository
                repo = LogRepository(db)
                
                # Ensure background tasks are initialized on the response
                if response:
                    if response.background is None:
                        response.background = BackgroundTasks()
                    response.background.add_task(repo.create_log, log_data)
                    
                    # Add Traceability ID
                    response.headers["X-Request-ID"] = str(uuid.uuid4())

        return response
