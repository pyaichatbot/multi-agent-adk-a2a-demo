"""
Enterprise Authentication Module
SageAI Platform Auth Proxy Integration
"""

import time
from typing import Optional, Dict, Any

import httpx

from src.config.settings import settings
from src.core.observability import observability


class SageAIAuthProxy:
    """SageAI Platform Auth Proxy integration"""
    
    def __init__(self):
        self.auth_proxy_url = settings.sageai.auth_proxy_url
        self.timeout = 10.0
    
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user via SageAI Auth Proxy"""
        try:
            with observability.trace_operation("sageai_auth_proxy", username=username):
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.auth_proxy_url}/auth/login",
                        json={"username": username, "password": password}
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    observability.record_authentication("success", "sageai_auth_proxy")
                    observability.log_structured(
                        "info",
                        "User authenticated via SageAI Auth Proxy",
                        username=username,
                        user_id=result.get("user_id")
                    )
                    
                    return result
                    
        except httpx.HTTPStatusError as e:
            observability.record_authentication("failed", "sageai_auth_proxy")
            observability.log_structured(
                "warning",
                "Authentication failed via SageAI Auth Proxy",
                username=username,
                status_code=e.response.status_code
            )
            return None
        except Exception as e:
            observability.record_authentication("error", "sageai_auth_proxy")
            observability.log_structured(
                "error",
                "SageAI Auth Proxy error",
                username=username,
                error=str(e)
            )
            return None
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate token via SageAI Auth Proxy"""
        try:
            with observability.trace_operation("token_validation"):
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.auth_proxy_url}/auth/validate",
                        json={"token": token}
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    observability.log_structured(
                        "info",
                        "Token validated via SageAI Auth Proxy",
                        user_id=result.get("user_id")
                    )
                    
                    return result
                    
        except httpx.HTTPStatusError as e:
            observability.log_structured(
                "warning",
                "Token validation failed via SageAI Auth Proxy",
                status_code=e.response.status_code
            )
            return None
        except Exception as e:
            observability.log_structured(
                "error",
                "SageAI Auth Proxy validation error",
                error=str(e)
            )
            return None


class PermissionManager:
    """Tool execution permission manager via SageAI Auth Proxy"""
    
    def __init__(self):
        self.auth_proxy_url = settings.sageai.auth_proxy_url
        self.timeout = 10.0
    
    async def check_tool_permission(self, user_id: str, tool_name: str, user_roles: list) -> bool:
        """Check tool permission via SageAI Auth Proxy"""
        try:
            with observability.trace_operation("permission_check", tool=tool_name, user=user_id):
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.auth_proxy_url}/auth/check-permission",
                        json={
                            "user_id": user_id,
                            "tool_name": tool_name,
                            "user_roles": user_roles
                        }
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    has_permission = result.get("has_permission", False)
                    
                    observability.log_structured(
                        "info" if has_permission else "warning",
                        "Permission check result",
                        user_id=user_id,
                        tool=tool_name,
                        has_permission=has_permission
                    )
                    
                    return has_permission
                    
        except Exception as e:
            observability.log_structured(
                "error",
                "Permission check error via SageAI Auth Proxy",
                user_id=user_id,
                tool=tool_name,
                error=str(e)
            )
            return False
    
    async def get_user_roles(self, user_id: str) -> list:
        """Get user roles via SageAI Auth Proxy"""
        try:
            with observability.trace_operation("get_user_roles", user=user_id):
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(
                        f"{self.auth_proxy_url}/auth/user/{user_id}/roles"
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    return result.get("roles", ["viewer"])
                    
        except Exception as e:
            observability.log_structured(
                "error",
                "Failed to get user roles via SageAI Auth Proxy",
                user_id=user_id,
                error=str(e)
            )
            return ["viewer"]


# Global instances
sageai_auth = SageAIAuthProxy()
permission_manager = PermissionManager()
