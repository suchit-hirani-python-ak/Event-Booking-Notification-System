import asyncio
import functools
import logging

logger = logging.getLogger(__name__)

def retry(max_attempts=3, delay=1, backoff=2):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            for attempt in range(1, max_attempts + 1):
                try:
                    # Pass the attempt number into the logic
                    kwargs['attempt_num'] = attempt 
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        raise e # Final failure for this loop
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
        return wrapper
    return decorator
