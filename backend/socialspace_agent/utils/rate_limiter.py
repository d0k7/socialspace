"""
SocialSpace Agent - Rate Limiter
=================================

Token bucket algorithm for rate limiting API requests.

Prevents:
---------
- API abuse and quota exhaustion
- Platform bans due to rate limit violations
- Cascading failures from overload

Algorithm:
----------
Token Bucket - Industry standard rate limiting

How it works:
1. Bucket starts with N tokens
2. Each request consumes 1 token
3. Tokens refill at fixed rate
4. If no tokens available, request waits

Author: Dheeraj Mishra
Created: February 7, 2026
Session: 2
"""

import time
import asyncio
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class RateLimiter:
    """
    Token bucket rate limiter.
    
    Thread-safe, async-friendly rate limiting.
    
    Attributes:
        rate: Requests per second allowed
        burst: Maximum burst size (bucket capacity)
        tokens: Current token count
        last_update: Last time tokens were refilled
        
    Example:
        >>> # Allow 10 requests/second, burst of 20
        >>> limiter = RateLimiter(rate=10, burst=20)
        >>> 
        >>> # Synchronous usage
        >>> limiter.acquire()  # Blocks if no tokens
        >>> make_api_call()
        >>> 
        >>> # Async usage
        >>> await limiter.acquire_async()
        >>> await make_async_api_call()
    
    Math:
        - rate=10, burst=20 means:
          * 10 requests/second sustained
          * Can burst up to 20 requests instantly
          * After burst, must wait for refill
    """
    
    rate: float  # Tokens added per second
    burst: int   # Maximum token capacity
    
    # Internal state
    _tokens: float = field(init=False, repr=False)
    last_update: float = field(init=False)
    
    def __post_init__(self):
        """Initialize token bucket to full capacity."""
        self._tokens = float(self.burst)
        self.last_update = time.time()

    @property
    def tokens(self) -> float:
        """Current token count (auto-refilled on access)."""
        self._refill_tokens()
        return self._tokens

    @tokens.setter
    def tokens(self, value: float) -> None:
        """Set token count directly."""
        self._tokens = float(value)
    
    def _refill_tokens(self) -> None:
        """
        Refill tokens based on time elapsed.
        
        Tokens refill at constant rate (self.rate tokens/second).
        Maximum tokens capped at burst size.
        
        Example:
            rate=10/sec, elapsed=0.5sec → add 5 tokens
            rate=10/sec, elapsed=2sec → add 20 tokens (capped at burst)
        """
        now = time.time()
        elapsed = now - self.last_update
        
        # Calculate new tokens
        new_tokens = elapsed * self.rate
        self._tokens = min(self.burst, self._tokens + new_tokens)
        
        # Update timestamp
        self.last_update = now
        
        logger.debug(
            f"Refilled tokens: {new_tokens:.2f}, "
            f"current: {self._tokens:.2f}/{self.burst}"
        )
    
    def acquire(self, tokens: int = 1, block: bool = True) -> bool:
        """
        Acquire tokens (synchronous).
        
        Args:
            tokens: Number of tokens to acquire (default: 1)
            block: If True, wait for tokens. If False, return immediately.
            
        Returns:
            True if tokens acquired, False if no tokens and block=False
            
        Raises:
            ValueError: If tokens > burst size
            
        Example:
            >>> limiter = RateLimiter(rate=10, burst=20)
            >>> 
            >>> # Blocking (waits if needed)
            >>> limiter.acquire()
            >>> 
            >>> # Non-blocking (returns False if no tokens)
            >>> if limiter.acquire(block=False):
            ...     make_api_call()
            ... else:
            ...     print("Rate limited!")
        """
        if tokens > self.burst:
            raise ValueError(
                f"Cannot acquire {tokens} tokens (burst size: {self.burst})"
            )
        
        while True:
            self._refill_tokens()
            
            if self._tokens >= tokens:
                # Consume tokens
                self._tokens -= tokens
                logger.debug(f"Acquired {tokens} tokens, {self._tokens:.2f} remaining")
                return True
            
            if not block:
                logger.debug(f"No tokens available (need {tokens}, have {self._tokens:.2f})")
                return False
            
            # Calculate wait time
            tokens_needed = tokens - self._tokens
            wait_time = tokens_needed / self.rate
            
            logger.debug(
                f"Waiting {wait_time:.2f}s for {tokens_needed:.2f} tokens"
            )
            
            time.sleep(wait_time)
    
    async def acquire_async(
        self, 
        tokens: int = 1, 
        block: bool = True
    ) -> bool:
        """
        Acquire tokens (asynchronous).
        
        Same as acquire() but uses async sleep.
        
        Args:
            tokens: Number of tokens to acquire
            block: If True, wait for tokens
            
        Returns:
            True if tokens acquired, False otherwise
            
        Example:
            >>> limiter = RateLimiter(rate=10, burst=20)
            >>> 
            >>> async def make_request():
            ...     await limiter.acquire_async()
            ...     return await api_call()
        """
        if tokens > self.burst:
            raise ValueError(
                f"Cannot acquire {tokens} tokens (burst size: {self.burst})"
            )
        
        while True:
            self._refill_tokens()
            
            if self._tokens >= tokens:
                self._tokens -= tokens
                logger.debug(f"Acquired {tokens} tokens, {self._tokens:.2f} remaining")
                return True
            
            if not block:
                logger.debug(f"No tokens available (need {tokens}, have {self._tokens:.2f})")
                return False
            
            # Calculate wait time
            tokens_needed = tokens - self._tokens
            wait_time = tokens_needed / self.rate
            
            logger.debug(
                f"Waiting {wait_time:.2f}s for {tokens_needed:.2f} tokens"
            )
            
            await asyncio.sleep(wait_time)
    
    def reset(self) -> None:
        """
        Reset rate limiter to full capacity.
        
        Useful for testing or manual override.
        
        Example:
            >>> limiter.reset()  # Refill bucket completely
        """
        self._tokens = float(self.burst)
        self.last_update = time.time()
        logger.info("Rate limiter reset to full capacity")
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """
        Calculate wait time until tokens are available.
        
        Args:
            tokens: Number of tokens needed
            
        Returns:
            Seconds to wait (0 if tokens available now)
            
        Example:
            >>> wait = limiter.get_wait_time(5)
            >>> print(f"Must wait {wait:.2f} seconds")
        """
        self._refill_tokens()
        
        if self._tokens >= tokens:
            return 0.0
        
        tokens_needed = tokens - self._tokens
        return tokens_needed / self.rate
    
    def get_stats(self) -> dict:
        """
        Get current rate limiter statistics.
        
        Returns:
            Dictionary with current state
            
        Example:
            >>> stats = limiter.get_stats()
            >>> print(f"Tokens available: {stats['tokens_available']}")
        """
        self._refill_tokens()
        
        return {
            "rate": self.rate,
            "burst": self.burst,
            "tokens_available": round(self._tokens, 2),
            "utilization": round((self.burst - self._tokens) / self.burst * 100, 1),
            "last_update": datetime.fromtimestamp(self.last_update).isoformat(),
        }


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

def create_rate_limiter(
    requests_per_minute: int,
    burst_factor: float = 2.0
) -> RateLimiter:
    """
    Create rate limiter from requests/minute.
    
    Args:
        requests_per_minute: Target request rate
        burst_factor: Burst size as multiple of rate (default: 2x)
        
    Returns:
        Configured RateLimiter
        
    Example:
        >>> # Allow 60 requests/minute with 2x burst
        >>> limiter = create_rate_limiter(60, burst_factor=2.0)
        >>> # Same as: RateLimiter(rate=1.0, burst=2)
    """
    rate_per_second = requests_per_minute / 60.0
    burst_size = int(requests_per_minute / 60.0 * burst_factor)
    
    return RateLimiter(
        rate=rate_per_second,
        burst=max(1, burst_size)  # At least 1 token
    )
