"""
Middleware for AI Agent Hub V3 API.
"""

import time
import uuid
from typing import Callable, Dict, Any
from collections import defaultdict
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from loguru import logger

from src.core.config import settings
from src.observability.request_context import get_workspace_id


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add request ID to each request."""
    
    async def dispatch(self, request: Request, call_next):
        # Respect incoming request id when provided by gateway/client.
        request_id = (
            request.headers.get("x-request-id")
            or request.headers.get("X-Request-ID")
            or request.headers.get("X-Request-Id")
            or str(uuid.uuid4())
        )
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log request and response details."""
    
    async def dispatch(self, request: Request, call_next):
        # Log request
        request_id = getattr(request.state, "request_id", "unknown")
        workspace_id = get_workspace_id(request)
        logger.info(
            "http.request request_id={} workspace_id={} method={} path={}",
            request_id,
            workspace_id,
            request.method,
            request.url.path,
            extra={
                "request_id": request_id,
                "workspace_id": workspace_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
            }
        )
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        workspace_id = get_workspace_id(request)
        logger.info(
            "http.response request_id={} workspace_id={} status_code={} duration_s={}",
            request_id,
            workspace_id,
            response.status_code,
            f"{process_time:.3f}",
            extra={
                "request_id": request_id,
                "workspace_id": workspace_id,
                "status_code": response.status_code,
                "process_time": process_time,
                "content_length": response.headers.get("content-length", 0),
            }
        )
        
        # Add headers
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Add timing headers to responses."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Response-Time"] = f"{process_time:.3f}s"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app: ASGIApp, requests: int = 100, period: int = 60):
        super().__init__(app)
        self.requests = requests
        self.period = period
        self.requests_log: Dict[str, list] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        
        # Clean old entries
        current_time = time.time()
        if client_ip in self.requests_log:
            self.requests_log[client_ip] = [
                t for t in self.requests_log[client_ip]
                if current_time - t < self.period
            ]
        
        # Check rate limit
        if len(self.requests_log[client_ip]) >= self.requests:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Maximum {self.requests} requests per {self.period} seconds."
            )
        
        # Add current request
        self.requests_log[client_ip].append(current_time)
        
        # Add headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests - len(self.requests_log[client_ip])
        )
        response.headers["X-RateLimit-Reset"] = str(
            int(current_time + self.period)
        )
        
        return response
