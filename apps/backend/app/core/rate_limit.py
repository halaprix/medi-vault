"""Rate limiting for FastAPI endpoints."""
import time
from collections import defaultdict
from fastapi import Request, HTTPException, status

class RateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def __call__(self, request: Request):
        now = time.time()
        client = request.client.host if request.client else "unknown"
        # Clean old entries
        self._requests[client] = [t for t in self._requests[client] if now - t < self.window]
        if len(self._requests[client]) >= self.max_requests:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
        self._requests[client].append(now)
