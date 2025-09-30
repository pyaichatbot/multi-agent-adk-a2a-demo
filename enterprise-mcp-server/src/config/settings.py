"""
Enterprise MCP Server Configuration
Clean, simple configuration following SOLID principles
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class RedisSettings(BaseSettings):
    """Redis configuration"""
    url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    max_connections: int = Field(default=20, env="REDIS_MAX_CONNECTIONS")
    socket_timeout: int = Field(default=5, env="REDIS_SOCKET_TIMEOUT")


class MCPSettings(BaseSettings):
    """MCP server configuration"""
    host: str = Field(default="0.0.0.0", env="MCP_HOST")
    port: int = Field(default=8000, env="MCP_PORT")
    max_connections: int = Field(default=1000, env="MCP_MAX_CONNECTIONS")
    timeout: int = Field(default=30, env="MCP_TIMEOUT")
    rate_limit: int = Field(default=100, env="MCP_RATE_LIMIT")


class SecuritySettings(BaseSettings):
    """Security configuration"""
    # Rate limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")  # requests per minute
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # seconds
    rate_limit_burst: int = Field(default=20, env="RATE_LIMIT_BURST")  # burst allowance
    
    # User-specific rate limiting
    user_rate_limit_requests: int = Field(default=50, env="USER_RATE_LIMIT_REQUESTS")
    user_rate_limit_window: int = Field(default=60, env="USER_RATE_LIMIT_WINDOW")
    
    # Tool execution rate limiting
    tool_rate_limit_requests: int = Field(default=10, env="TOOL_RATE_LIMIT_REQUESTS")
    tool_rate_limit_window: int = Field(default=60, env="TOOL_RATE_LIMIT_WINDOW")


class SageAISettings(BaseSettings):
    """SageAI platform configuration"""
    base_url: str = Field(default="https://sageai.platform.com/api/v1", env="SAGEAI_BASE_URL")
    auth_proxy_url: str = Field(default="https://auth.sageai.platform.com", env="SAGEAI_AUTH_PROXY_URL")
    timeout: int = Field(default=30, env="SAGEAI_TIMEOUT")
    token_cache_ttl: int = Field(default=300, env="SAGEAI_TOKEN_CACHE_TTL")  # 5 minutes
    max_retries: int = Field(default=3, env="SAGEAI_MAX_RETRIES")


class EnterpriseMCPSettings(BaseSettings):
    """Main application settings - Clean and Simple"""
    
    # Core services
    redis: RedisSettings = RedisSettings()
    mcp: MCPSettings = MCPSettings()
    security: SecuritySettings = SecuritySettings()
    sageai: SageAISettings = SageAISettings()
    
    # Simple observability - single flag
    enable_telemetry: bool = Field(default=False, env="ENABLE_TELEMETRY")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Application settings
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="production", env="ENVIRONMENT")
    
    # Tool registry
    tool_registry_url: str = Field(
        default="http://localhost:8001/tools",
        env="TOOL_REGISTRY_URL"
    )
    
    # Inhouse agents
    inhouse_agents: List[str] = Field(
        default=["data-search-agent", "reporting-agent", "analytics-agent"],
        env="INHOUSE_AGENTS"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = EnterpriseMCPSettings()
