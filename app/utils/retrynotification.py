import asyncio
import functools

def retry(max_attempts=3, delay=2, backoff=2):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies for logging
            repo = kwargs.get('repo')
            booking_id = kwargs.get('booking_id')
            email = kwargs.get('email')
            
            current_delay = delay
            for attempt in range(1, max_attempts + 1):
                try:
                    # Try the actual notification
                    result = await func(*args, **kwargs)
                    
                    # LOG SUCCESS: If we reach here, it worked
                    if repo:
                        await repo.log_notification(booking_id, email, "sent", attempt)
                    return result
                
                except Exception as e:
                    # LOG FAILURE: Log this specific attempt
                    if repo:
                        await repo.log_notification(booking_id, email, "failed", attempt, message=str(e))
                    
                    # If it was the last attempt, re-raise the error
                    if attempt == max_attempts:
                        raise e
                    
                    # Wait before next attempt (2s -> 4s -> 8s)
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
                    
        return wrapper
    return decorator
