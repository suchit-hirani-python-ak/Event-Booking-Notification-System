import time
import math
from fastapi import Request
from fastapi.responses import JSONResponse
from app.dependencies.depandency import redis_client

async def sliding_window_rate_limiter(request: Request, next_call):
    # 1. Configuration
    LIMIT = 10
    WINDOW_SECONDS = 6
    
    # 2. Safety check for Client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # 3. Define window keys
    now = time.time()
    current_window_idx = int(now // WINDOW_SECONDS)
    prev_window_idx = current_window_idx - 1
    
    curr_key = f"rate_limit:{client_ip}:{current_window_idx}"
    prev_key = f"rate_limit:{client_ip}:{prev_window_idx}"

    try:
        # 4. Atomic check & increment using a Pipeline
        async with redis_client.pipeline(transaction=True) as pipe:
            pipe.get(prev_key)
            pipe.incr(curr_key)
            pipe.expire(curr_key, WINDOW_SECONDS * 2) # Keep long enough for next window
            results = await pipe.execute()
        
        prev_count = int(results[0] or 0)
        curr_count = int(results[1])

        # 5. Weighted Calculation: how far into the window are we?
        elapsed_in_window = now % WINDOW_SECONDS
        prev_weight = 1 - (elapsed_in_window / WINDOW_SECONDS)
        
        # Total estimated requests in the last 60s
        estimated_count = math.floor(prev_count * prev_weight) + curr_count

        if estimated_count > LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."},
                headers={"Retry-After": str(WINDOW_SECONDS - int(elapsed_in_window))}
            )

        return await next_call(request)

    except Exception as e:
        # Fail-open: don't block users if Redis is down
        print(f"Rate limiter error: {e}")
        return await next_call(request)
