import time
import random
import logging
from functools import wraps
from typing import Callable, Type, Union, Tuple, Optional

class RetryError(Exception):
    """Raised when all retry attempts fail"""
    pass

def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception
) -> Callable:
    """
    Retry decorator with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delay
        exceptions: Exception types to catch and retry
    """
    def decorator(func: Callable) -> Callable:
        logger = logging.getLogger('RootBot.retry')
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(
                            f"All retry attempts failed for {func.__name__}",
                            extra={
                                'function': func.__name__,
                                'attempts': attempt + 1,
                                'error': str(e)
                            }
                        )
                        raise RetryError(f"Failed after {max_retries} retries") from e
                    
                    # Calculate next delay
                    delay = min(delay * exponential_base, max_delay)
                    if jitter:
                        delay *= (0.5 + random.random())
                    
                    logger.warning(
                        f"Retry attempt {attempt + 1}/{max_retries} for {func.__name__}",
                        extra={
                            'function': func.__name__,
                            'attempt': attempt + 1,
                            'delay': delay,
                            'error': str(e)
                        }
                    )
                    
                    time.sleep(delay)
            
            return None  # Should never reach here
        
        return wrapper
    
    return decorator
