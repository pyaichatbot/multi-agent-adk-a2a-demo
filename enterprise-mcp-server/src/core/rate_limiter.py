"""
Enterprise Rate Limiter
Production-grade rate limiting with Redis backend
"""

import time
import asyncio
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

import redis.asyncio as redis
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from src.config.settings import settings
from src.core.observability import observability


class EnterpriseRateLimiter:
    """Enterprise-grade rate limiter with Redis backend"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.enabled = settings.security.rate_limit_enabled
        
        # Rate limit configurations
        self.global_limits = {
            "requests": settings.security.rate_limit_requests,
            "window": settings.security.rate_limit_window,
            "burst": settings.security.rate_limit_burst
        }
        
        self.user_limits = {
            "requests": settings.security.user_rate_limit_requests,
            "window": settings.security.user_rate_limit_window
        }
        
        self.tool_limits = {
            "requests": settings.security.tool_rate_limit_requests,
            "window": settings.security.tool_rate_limit_window
        }
    
    async def connect_redis(self):
        """Connect to Redis for rate limiting"""
        if not self.enabled:
            return
        
        try:
            self.redis_client = redis.from_url(settings.redis.url)
            await self.redis_client.ping()
            observability.log("info", "Rate limiter connected to Redis")
        except Exception as e:
            observability.log("error", "Rate limiter Redis connection failed", error=str(e))
            self.redis_client = None
    
    async def check_rate_limit(
        self, 
        identifier: str, 
        limit_type: str = "global",
        user_id: Optional[str] = None
    ) -> Tuple[bool, Dict[str, int]]:
        """
        Check rate limit for identifier
        
        Args:
            identifier: IP address, user_id, or tool name
            limit_type: "global", "user", or "tool"
            user_id: User ID for user-specific limits
        
        Returns:
            (is_allowed, rate_info)
        """
        if not self.enabled or not self.redis_client:
            return True, {}
        
        try:
            # Get appropriate limits
            if limit_type == "user" and user_id:
                limits = self.user_limits
                key_prefix = f"rate_limit:user:{user_id}"
            elif limit_type == "tool":
                limits = self.tool_limits
                key_prefix = f"rate_limit:tool:{identifier}"
            else:
                limits = self.global_limits
                key_prefix = f"rate_limit:global:{identifier}"
            
            # Create Redis keys
            current_time = int(time.time())
            window_start = current_time - limits["window"]
            
            # Sliding window rate limiting
            pipe = self.redis_client.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(key_prefix, 0, window_start)
            
            # Count current requests
            pipe.zcard(key_prefix)
            
            # Add current request
            pipe.zadd(key_prefix, {str(current_time): current_time})
            
            # Set expiration
            pipe.expire(key_prefix, limits["window"])
            
            results = await pipe.execute()
            current_requests = results[1]
            
            # Check if limit exceeded
            is_allowed = current_requests < limits["requests"]
            
            # Prepare rate info
            rate_info = {
                "current_requests": current_requests,
                "limit": limits["requests"],
                "window": limits["window"],
                "remaining": max(0, limits["requests"] - current_requests),
                "reset_time": current_time + limits["window"]
            }
            
            # Log rate limiting activity
            if not is_allowed:
                observability.log("warning", "Rate limit exceeded", 
                               identifier=identifier, 
                               limit_type=limit_type,
                               current_requests=current_requests,
                               limit=limits["requests"])
            else:
                observability.log("debug", "Rate limit check passed",
                               identifier=identifier,
                               limit_type=limit_type,
                               remaining=rate_info["remaining"])
            
            return is_allowed, rate_info
            
        except Exception as e:
            observability.log("error", "Rate limiter error", 
                           identifier=identifier, 
                           error=str(e))
            # Fail open - allow request if rate limiter fails
            return True, {}
    
    async def get_rate_limit_info(self, identifier: str, limit_type: str = "global") -> Dict[str, int]:
        """Get current rate limit information without consuming a request"""
        if not self.enabled or not self.redis_client:
            return {"enabled": False}
        
        try:
            # Get appropriate limits
            if limit_type == "user":
                limits = self.user_limits
                key_prefix = f"rate_limit:user:{identifier}"
            elif limit_type == "tool":
                limits = self.tool_limits
                key_prefix = f"rate_limit:tool:{identifier}"
            else:
                limits = self.global_limits
                key_prefix = f"rate_limit:global:{identifier}"
            
            current_time = int(time.time())
            window_start = current_time - limits["window"]
            
            # Count current requests in window
            current_requests = await self.redis_client.zcount(key_prefix, window_start, current_time)
            
            return {
                "enabled": True,
                "current_requests": current_requests,
                "limit": limits["requests"],
                "window": limits["window"],
                "remaining": max(0, limits["requests"] - current_requests),
                "reset_time": current_time + limits["window"]
            }
            
        except Exception as e:
            observability.log("error", "Rate limit info error", error=str(e))
            return {"enabled": False, "error": str(e)}


class RateLimitMiddleware:
    """FastAPI middleware for rate limiting"""
    
    def __init__(self, rate_limiter: EnterpriseRateLimiter):
        self.rate_limiter = rate_limiter
    
    async def __call__(self, request: Request, call_next):
        """Rate limiting middleware"""
        if not self.rate_limiter.enabled:
            return await call_next(request)
        
        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        
        # Check global rate limit
        is_allowed, rate_info = await self.rate_limiter.check_rate_limit(
            client_ip, 
            "global"
        )
        
        if not is_allowed:
            observability.log("warning", "Global rate limit exceeded", 
                           client_ip=client_ip,
                           rate_info=rate_info)
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests",
                    "retry_after": rate_info.get("window", 60),
                    "rate_info": rate_info
                },
                headers={
                    "Retry-After": str(rate_info.get("window", 60)),
                    "X-RateLimit-Limit": str(rate_info.get("limit", 0)),
                    "X-RateLimit-Remaining": str(rate_info.get("remaining", 0)),
                    "X-RateLimit-Reset": str(rate_info.get("reset_time", 0))
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        
        response.headers["X-RateLimit-Limit"] = str(rate_info.get("limit", 0))
        response.headers["X-RateLimit-Remaining"] = str(rate_info.get("remaining", 0))
        response.headers["X-RateLimit-Reset"] = str(rate_info.get("reset_time", 0))
        
        return response


# Global rate limiter instance
rate_limiter = EnterpriseRateLimiter()
