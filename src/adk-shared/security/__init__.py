"""
Security utilities for authentication and authorization
"""

import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


def get_auth_token() -> str:
    """Generate authentication token for service-to-service communication"""
    payload = {
        "service": "enterprise-agents",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, "your-secret-key", algorithm="HS256")


def authenticate_request(token: Optional[str]) -> bool:
    """Authenticate incoming requests"""
    if not token:
        return False
    
    try:
        jwt.decode(token, "your-secret-key", algorithms=["HS256"])
        return True
    except jwt.InvalidTokenError:
        return False


def validate_policy(policy: Dict[str, Any], from_service: str, to_service: str) -> bool:
    """Validate policy compliance for service interactions"""
    try:
        rules = policy.get("rules", {})
        allowed_calls = rules.get(from_service, {}).get("can_call", [])
        return to_service in allowed_calls or "*" in allowed_calls
    except Exception:
        return False
