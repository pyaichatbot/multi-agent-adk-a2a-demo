"""
SageAI Authentication Module
SOLID Principle: Single Responsibility - Handles SageAI authentication and token validation
Enterprise Standard: Clean, maintainable authentication with proper error handling
"""

import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from src.config.settings import settings
from .observability import observability


class SageAIAuthenticator:
    """Enterprise SageAI authentication with token validation and caching"""
    
    def __init__(self):
        self.base_url = settings.sageai.base_url
        self.auth_proxy_url = settings.sageai.auth_proxy_url
        self.token_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = settings.sageai.token_cache_ttl
        
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate SageAI token and return user information"""
        try:
            with observability.trace_operation("sageai_auth", operation="validate_token"):
                # Check cache first
                if token in self.token_cache:
                    cached_data = self.token_cache[token]
                    if datetime.now() < cached_data['expires_at']:
                        observability.log("info", "Token validated from cache", token=token[:8] + "...")
                        return cached_data['user_info']
                    else:
                        # Remove expired token
                        del self.token_cache[token]
                
                # Validate with SageAI auth proxy
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        f"{self.auth_proxy_url}/validate",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    
                    if response.status_code == 200:
                        user_info = response.json()
                        
                        # Cache the token
                        self.token_cache[token] = {
                            'user_info': user_info,
                            'expires_at': datetime.now() + timedelta(seconds=self.cache_ttl)
                        }
                        
                        observability.record_authentication("success", "sageai")
                        observability.log("info", "Token validated successfully", 
                                       user_id=user_info.get('user_id'), 
                                       roles=user_info.get('roles', []))
                        
                        return user_info
                    else:
                        observability.record_authentication("failed", "sageai")
                        observability.log("warning", "Token validation failed", 
                                       status_code=response.status_code)
                        return None
                        
        except Exception as e:
            observability.record_authentication("error", "sageai")
            observability.log("error", "Token validation error", error=str(e))
            return None
    
    async def get_user_permissions(self, user_info: Dict[str, Any]) -> Dict[str, bool]:
        """Extract user permissions from SageAI user info"""
        try:
            roles = user_info.get('roles', [])
            permissions = {
                'can_invoke_agents': 'agent_user' in roles or 'admin' in roles,
                'can_execute_tools': 'tool_user' in roles or 'admin' in roles,
                'can_access_analytics': 'analytics_user' in roles or 'admin' in roles,
                'can_access_database': 'database_user' in roles or 'admin' in roles,
                'is_admin': 'admin' in roles
            }
            
            observability.log("info", "User permissions extracted", 
                           user_id=user_info.get('user_id'), 
                           permissions=permissions)
            
            return permissions
            
        except Exception as e:
            observability.log("error", "Permission extraction failed", error=str(e))
            return {
                'can_invoke_agents': False,
                'can_execute_tools': False,
                'can_access_analytics': False,
                'can_access_database': False,
                'is_admin': False
            }
    
    def clear_token_cache(self, token: Optional[str] = None):
        """Clear token cache - optionally for specific token"""
        if token:
            self.token_cache.pop(token, None)
            observability.log("info", "Token cache cleared for specific token")
        else:
            self.token_cache.clear()
            observability.log("info", "Token cache cleared for all tokens")


# Global authenticator instance
sageai_auth = SageAIAuthenticator()
