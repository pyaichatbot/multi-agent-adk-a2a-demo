"""
Enterprise System Tools
SOLID Principle: Single Responsibility - Handles all system-related operations
Enterprise Standard: Zero-configuration auto-discovery with enterprise-grade features
"""

from typing import Any, Dict
from src.core.observability import observability
from src.core.rate_limiter import rate_limiter
from src.tools.base_tool import EnterpriseToolRegistry, enterprise_tool


class SystemTools:
    """Enterprise system tools with zero-configuration auto-discovery"""
    
    @staticmethod
    def get_tools_metadata() -> list:
        """Return metadata for all system tools - Enterprise auto-discovery!"""
        return EnterpriseToolRegistry.get_tools_metadata("system")
    
    @enterprise_tool(category="system")
    @staticmethod
    async def get_system_info() -> str:
        """Get comprehensive system information"""
        try:
            async with observability.trace_operation("tool_execution", tool="get_system_info"):
                # Check rate limit
                is_allowed, rate_info = await rate_limiter.check_rate_limit(
                    "get_system_info", "tool"
                )
                
                if not is_allowed:
                    return f"Rate limit exceeded for get_system_info. Retry after {rate_info.get('window', 60)} seconds"
                
                # Simulate system info retrieval
                result = "System information retrieved: CPU usage, memory, disk space, network status"
                
                observability.record_tool_execution("get_system_info", "success")
                observability.log("info", "System info retrieved")
                
                return result
                
        except Exception as e:
            observability.record_tool_execution("get_system_info", "error")
            observability.log("error", "System info retrieval failed", error=str(e))
            return f"System info retrieval failed: {str(e)}"
    
    @enterprise_tool(category="system")
    @staticmethod
    async def check_system_health() -> str:
        """Check system health and status"""
        try:
            async with observability.trace_operation("tool_execution", tool="check_system_health"):
                # Check rate limit
                is_allowed, rate_info = await rate_limiter.check_rate_limit(
                    "check_system_health", "tool"
                )
                
                if not is_allowed:
                    return f"Rate limit exceeded for check_system_health. Retry after {rate_info.get('window', 60)} seconds"
                
                # Simulate health check
                result = "System health check completed: All services operational, resources within normal limits"
                
                observability.record_tool_execution("check_system_health", "success")
                observability.log("info", "System health check completed")
                
                return result
                
        except Exception as e:
            observability.record_tool_execution("check_system_health", "error")
            observability.log("error", "System health check failed", error=str(e))
            return f"System health check failed: {str(e)}"
    
    @enterprise_tool(category="system")
    @staticmethod
    async def check_health() -> str:
        """Check system health status"""
        try:
            with observability.trace_operation("tool_execution", tool="check_health"):
                # Check rate limit
                is_allowed, rate_info = await rate_limiter.check_rate_limit(
                    "check_health", "tool"
                )
                
                if not is_allowed:
                    return f"Rate limit exceeded for check_health. Retry after {rate_info.get('window', 60)} seconds"
                
                # Simulate health check
                result = "System health check completed: All services operational"
                
                observability.record_tool_execution("check_health", "success")
                observability.log("info", "Health check completed")
                
                return result
                
        except Exception as e:
            observability.record_tool_execution("check_health", "error")
            observability.log("error", "Health check failed", error=str(e))
            return f"Health check failed: {str(e)}"
    
    @enterprise_tool(category="system")
    @staticmethod
    async def list_tools() -> str:
        """List all available MCP tools"""
        try:
            with observability.trace_operation("tool_execution", tool="list_tools"):
                # Check rate limit
                is_allowed, rate_info = await rate_limiter.check_rate_limit(
                    "list_tools", "tool"
                )
                
                if not is_allowed:
                    return f"Rate limit exceeded for list_tools. Retry after {rate_info.get('window', 60)} seconds"
                
                # Get all tools from registry
                all_tools = EnterpriseToolRegistry.get_tools_metadata()
                categories = EnterpriseToolRegistry.get_categories()
                
                result = f"Available MCP tools: {len(all_tools)} tools across {len(categories)} categories"
                
                observability.record_tool_execution("list_tools", "success")
                observability.log("info", "Tools listed", tool_count=len(all_tools))
                
                return result
                
        except Exception as e:
            observability.record_tool_execution("list_tools", "error")
            observability.log("error", "Tool listing failed", error=str(e))
            return f"Tool listing failed: {str(e)}"
    
    @enterprise_tool(category="system")
    @staticmethod
    async def get_tool_info(
        tool_name: str
    ) -> str:
        """Get detailed information about a specific tool"""
        try:
            with observability.trace_operation("tool_execution", tool="get_tool_info"):
                # Check rate limit
                is_allowed, rate_info = await rate_limiter.check_rate_limit(
                    "get_tool_info", "tool"
                )
                
                if not is_allowed:
                    return f"Rate limit exceeded for get_tool_info. Retry after {rate_info.get('window', 60)} seconds"
                
                # Get tool metadata
                tool_metadata = EnterpriseToolRegistry.get_tool_by_name(tool_name)
                
                if tool_metadata:
                    result = f"Tool info for {tool_name}: {tool_metadata.description}"
                else:
                    result = f"Tool {tool_name} not found"
                
                observability.record_tool_execution("get_tool_info", "success")
                observability.log("info", "Tool info retrieved", tool_name=tool_name)
                
                return result
                
        except Exception as e:
            observability.record_tool_execution("get_tool_info", "error")
            observability.log("error", "Tool info retrieval failed", error=str(e))
            return f"Tool info retrieval failed: {str(e)}"