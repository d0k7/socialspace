"""
SocialSpace Agent - Retry Logic
================================

Exponential backoff retry decorator for resilient API calls.

Handles:
--------
- Transient network failures
- API rate limiting
- Service unavailability
- Timeout errors

Strategy:
---------
Exponential Backoff with Jitter (industry best practice)

Formula: wait = min(max_wait, base * (2 ** attempt) + random_jitter)

Author: Dheeraj Mishra
Created: February 7, 2026
Session: 2
"""

import asyncio
import time
import random
import logging
from typing import TypeVar, Callable, Optional, Type, Tuple
from functools import wraps

logger = logging.getLogger(__name__)

# Type variables for generic functions
T = TypeVar('T')


# ============================================
# RETRY DECORATOR (SYNC)
# ============================================

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Retry decorator with exponential backoff (synchronous).
    
    Automatically retries failed function calls with increasing delays.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay cap (default: 60.0)
        exponential_base: Exponential growth factor (default: 2.0)
        jitter: Add random jitter to prevent thundering herd (default: True)
        exceptions: Tuple of exceptions to catch (default: all exceptions)
        on_retry: Callback function(attempt, exception, delay)
        
    Returns:
        Decorated function with retry logic
        
    Example:
        >>> @retry_with_backoff(max_retries=3, base_delay=1.0)
        ... def fetch_data():
        ...     response = requests.get("https://api.example.com/data")
        ...     return response.json()
        >>> 
        >>> data = fetch_data()  # Retries up to 3 times on failure
        
    Retry Schedule (without jitter):
        Attempt 1: Immediate
        Attempt 2: Wait 1.0s  (1 * 2^0)
        Attempt 3: Wait 2.0s  (1 * 2^1)
        Attempt 4: Wait 4.0s  (1 * 2^2)
        
    Why Jitter?
        - Prevents all clients retrying simultaneously
        - Reduces load spikes on recovering services
        - Industry best practice (AWS, Google recommend it)
    """
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    # Try executing the function
                    result = func(*args, **kwargs)
                    
                    # Success! Log if we retried
                    if attempt > 0:
                        logger.info(
                            f"{func.__name__} succeeded on attempt {attempt + 1}"
                        )
                    
                    return result
                    
                except exceptions as e:
                    last_exception = e
                    
                    # Check if we should retry
                    if attempt >= max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise
                    
                    # Calculate backoff delay
                    delay = calculate_backoff_delay(
                        attempt=attempt,
                        base_delay=base_delay,
                        max_delay=max_delay,
                        exponential_base=exponential_base,
                        jitter=jitter
                    )
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        on_retry(attempt + 1, e, delay)
                    
                    # Wait before retrying
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            raise last_exception
        
        return wrapper
    return decorator


# ============================================
# RETRY DECORATOR (ASYNC)
# ============================================

def async_retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Retry decorator with exponential backoff (asynchronous).
    
    Same as retry_with_backoff but for async functions.
    
    Args:
        max_retries: Maximum retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap
        exponential_base: Exponential growth factor
        jitter: Add random jitter
        exceptions: Tuple of exceptions to catch
        on_retry: Callback function(attempt, exception, delay)
        
    Returns:
        Decorated async function with retry logic
        
    Example:
        >>> @async_retry_with_backoff(max_retries=5, base_delay=2.0)
        ... async def fetch_data_async():
        ...     async with httpx.AsyncClient() as client:
        ...         response = await client.get("https://api.example.com/data")
        ...         return response.json()
        >>> 
        >>> data = await fetch_data_async()  # Retries up to 5 times
    """
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    # Try executing the async function
                    result = await func(*args, **kwargs)
                    
                    # Success! Log if we retried
                    if attempt > 0:
                        logger.info(
                            f"{func.__name__} succeeded on attempt {attempt + 1}"
                        )
                    
                    return result
                    
                except exceptions as e:
                    last_exception = e
                    
                    # Check if we should retry
                    if attempt >= max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise
                    
                    # Calculate backoff delay
                    delay = calculate_backoff_delay(
                        attempt=attempt,
                        base_delay=base_delay,
                        max_delay=max_delay,
                        exponential_base=exponential_base,
                        jitter=jitter
                    )
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        on_retry(attempt + 1, e, delay)
                    
                    # Wait before retrying (async sleep)
                    await asyncio.sleep(delay)
            
            # Should never reach here, but just in case
            raise last_exception
        
        return wrapper
    return decorator


# ============================================
# HELPER FUNCTIONS
# ============================================

def calculate_backoff_delay(
    attempt: int,
    base_delay: float,
    max_delay: float,
    exponential_base: float = 2.0,
    jitter: bool = True
) -> float:
    """
    Calculate exponential backoff delay with optional jitter.
    
    Formula:
        delay = min(max_delay, base_delay * (exponential_base ** attempt))
        
        With jitter:
        delay = delay + random.uniform(0, delay * 0.1)
        
    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay cap
        exponential_base: Exponential growth factor
        jitter: Whether to add random jitter
        
    Returns:
        Calculated delay in seconds
        
    Example:
        >>> # Calculate delay for 3rd retry (attempt=2)
        >>> delay = calculate_backoff_delay(2, base_delay=1.0, max_delay=60.0)
        >>> print(delay)
        4.2  # 1.0 * (2^2) + jitter
    """
    # Exponential backoff: base * (2 ^ attempt)
    delay = base_delay * (exponential_base ** attempt)
    
    # Cap at maximum delay
    delay = min(delay, max_delay)
    
    # Add jitter (up to 10% of delay)
    if jitter:
        jitter_amount = random.uniform(0, delay * 0.1)
        delay += jitter_amount
    
    return delay


# ============================================
# RETRY CLASS (ADVANCED)
# ============================================

class RetryStrategy:
    """
    Advanced retry strategy with customizable behavior.
    
    Provides more control than decorators for complex scenarios.
    
    Example:
        >>> strategy = RetryStrategy(max_retries=5, base_delay=2.0)
        >>> 
        >>> for attempt in strategy:
        ...     try:
        ...         result = make_api_call()
        ...         break
        ...     except Exception as e:
        ...         if not strategy.should_retry(e):
        ...             raise
        ...         strategy.wait(attempt)
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions
        
        self.attempt = 0
    
    def should_retry(self, exception: Exception) -> bool:
        """
        Check if exception is retryable.
        
        Args:
            exception: Exception that was raised
            
        Returns:
            True if should retry
        """
        if self.attempt >= self.max_retries:
            return False
        
        return isinstance(exception, self.retryable_exceptions)
    
    def wait(self, attempt: Optional[int] = None) -> None:
        """
        Wait with exponential backoff.
        
        Args:
            attempt: Attempt number (uses internal counter if None)
        """
        if attempt is None:
            attempt = self.attempt
        
        delay = calculate_backoff_delay(
            attempt=attempt,
            base_delay=self.base_delay,
            max_delay=self.max_delay,
            exponential_base=self.exponential_base,
            jitter=self.jitter
        )
        
        time.sleep(delay)
    
    async def wait_async(self, attempt: Optional[int] = None) -> None:
        """Wait with exponential backoff (async version)."""
        if attempt is None:
            attempt = self.attempt
        
        delay = calculate_backoff_delay(
            attempt=attempt,
            base_delay=self.base_delay,
            max_delay=self.max_delay,
            exponential_base=self.exponential_base,
            jitter=self.jitter
        )
        
        await asyncio.sleep(delay)
    
    def __iter__(self):
        """Iterate through retry attempts."""
        self.attempt = 0
        return self
    
    def __next__(self):
        """Get next retry attempt."""
        if self.attempt > self.max_retries:
            raise StopIteration
        
        current = self.attempt
        self.attempt += 1
        return current