"""
Rate limiting middleware for the Task API.

This is a basic implementation for demonstration purposes.
In production, consider using Redis-based solutions like:
- slowapi (FastAPI rate limiting)
- fastapi-limiter
- nginx rate limiting
"""

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
from typing import Dict, Tuple
import asyncio


class InMemoryRateLimiter(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiter middleware.
    
    NOT SUITABLE FOR PRODUCTION with multiple instances.
    Use Redis-based solutions for production deployments.
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 1 minute window
        self.requests: Dict[str, list] = {}
        
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request"""
        return request.client.host if request.client else "unknown"
    
    def _cleanup_old_requests(self, client_id: str, now: float):
        """Remove requests outside the time window"""
        if client_id in self.requests:
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if now - req_time < self.window_size
            ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        client_id = self._get_client_id(request)
        now = time.time()
        
        # Clean up old requests
        self._cleanup_old_requests(client_id, now)
        
        # Check rate limit
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        if len(self.requests[client_id]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": self.requests_per_minute,
                    "window": "1 minute",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )
        
        # Record this request
        self.requests[client_id].append(now)
        
        # Process the request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_minute - len(self.requests[client_id])
        )
        response.headers["X-RateLimit-Reset"] = str(int(now + self.window_size))
        
        return response