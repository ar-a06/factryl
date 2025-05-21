"""
Rate limiting utility for API requests.
"""

import asyncio
import time
from typing import Optional

class RateLimiter:
    """
    Asynchronous rate limiter for controlling request rates to external services.
    """
    
    def __init__(self, rate: float, burst: Optional[int] = None):
        """
        Initialize the rate limiter.
        
        Args:
            rate: Maximum requests per second
            burst: Maximum burst size (optional)
        """
        self.rate = rate
        self.burst = burst or int(rate * 2)
        self.tokens = self.burst
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()
        
    async def acquire(self) -> None:
        """
        Acquire a token from the rate limiter.
        Blocks until a token is available.
        """
        async with self._lock:
            while self.tokens <= 0:
                now = time.monotonic()
                time_passed = now - self.last_update
                self.tokens = min(
                    self.burst,
                    self.tokens + time_passed * self.rate
                )
                self.last_update = now
                
                if self.tokens <= 0:
                    await asyncio.sleep(1.0 / self.rate)
                    
            self.tokens -= 1
            
    def release(self) -> None:
        """
        Release is a no-op for this implementation as tokens are
        automatically replenished based on time.
        """
        pass 