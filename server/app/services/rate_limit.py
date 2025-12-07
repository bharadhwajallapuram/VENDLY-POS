"""
Vendly POS - Rate Limiting
Prevents brute force attacks and API abuse
"""

from typing import Callable, Optional
import time
from collections import defaultdict
from threading import Lock

from fastapi import Request, HTTPException, status


class RateLimiter:
    """
    Simple in-memory rate limiter using sliding window.
    For production, use Redis-based rate limiting.
    """

    def __init__(self):
        self.requests: dict[str, list[float]] = defaultdict(list)
        self.lock = Lock()

    def _parse_rate(self, rate: str) -> tuple[int, int]:
        """Parse rate string like '5/minute' to (count, seconds)"""
        count, period = rate.split("/")
        count = int(count)

        period_seconds = {
            "second": 1,
            "minute": 60,
            "hour": 3600,
            "day": 86400,
        }

        seconds = period_seconds.get(period, 60)
        return count, seconds

    def is_allowed(self, key: str, rate: str) -> tuple[bool, dict]:
        """
        Check if request is allowed under rate limit.
        Returns (allowed, info) where info contains rate limit headers.
        """
        max_requests, window_seconds = self._parse_rate(rate)
        now = time.time()
        window_start = now - window_seconds

        with self.lock:
            # Clean old requests
            self.requests[key] = [ts for ts in self.requests[key] if ts > window_start]

            current_count = len(self.requests[key])
            remaining = max(0, max_requests - current_count)

            # Calculate reset time
            if self.requests[key]:
                reset_time = int(self.requests[key][0] + window_seconds)
            else:
                reset_time = int(now + window_seconds)

            info = {
                "X-RateLimit-Limit": str(max_requests),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset_time),
            }

            if current_count >= max_requests:
                retry_after = int(self.requests[key][0] + window_seconds - now)
                info["Retry-After"] = str(max(1, retry_after))
                return False, info

            # Record this request
            self.requests[key].append(now)
            info["X-RateLimit-Remaining"] = str(remaining - 1)

            return True, info

    def reset(self, key: str):
        """Reset rate limit for a key (e.g., after successful login)"""
        with self.lock:
            self.requests.pop(key, None)


# Global rate limiter instance
rate_limiter = RateLimiter()


def get_client_ip(request: Request) -> str:
    """Get client IP from request, handling proxies"""
    # Check for forwarded headers (from load balancer/proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Direct connection
    if request.client:
        return request.client.host

    return "unknown"


def rate_limit(
    rate: str = "60/minute", key_func: Optional[Callable[[Request], str]] = None
):
    """
    Rate limiting dependency for FastAPI endpoints.

    Usage:
        @router.post("/login")
        async def login(request: Request, _: None = Depends(rate_limit("5/minute"))):
            ...
    """

    async def dependency(request: Request):
        from app.core.config import settings

        if not settings.RATE_LIMIT_ENABLED:
            return

        # Get key for rate limiting (default: IP address)
        if key_func:
            key = key_func(request)
        else:
            key = f"ip:{get_client_ip(request)}:{request.url.path}"

        allowed, info = rate_limiter.is_allowed(key, rate)

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {info.get('Retry-After', '60')} seconds.",
                headers=info,
            )

        # Store info for response headers
        request.state.rate_limit_info = info

    return dependency


def rate_limit_login():
    """Pre-configured rate limit for login endpoint"""
    from app.core.config import settings

    return rate_limit(settings.RATE_LIMIT_LOGIN)
