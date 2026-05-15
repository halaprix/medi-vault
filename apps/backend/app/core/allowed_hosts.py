"""ALLOWED_HOSTS middleware for FastAPI."""
import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

ALLOWED_HOSTS = set(os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,frontend").split(","))

class AllowedHostsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        host = request.headers.get("host", "").split(":")[0]
        if host and host not in ALLOWED_HOSTS and "*" not in ALLOWED_HOSTS:
            return JSONResponse({"detail": "Host not allowed"}, status_code=403)
        return await call_next(request)
