"""
SageAI Tool Tools
SOLID Principle: Single Responsibility - Exposes SageAI tools as MCP tools
Enterprise Standard: Zero-configuration auto-discovery with enterprise-grade features
"""

from typing import Any, Dict
from src.core.observability import observability
from src.core.rate_limiter import rate_limiter
from src.core.sageai_auth import sageai_auth
from src.core.sageai_observability import sageai_observability
from src.core.policy_enforcement import policy_enforcement
from src.tools.base_tool import EnterpriseToolRegistry, enterprise_tool
from .tool_client import sageai_tool_client


class SageAIToolTools:
    """Enterprise SageAI tool tools with zero-configuration auto-discovery"""
    
    @staticmethod
    def get_tools_metadata() -> list:
        """Return metadata for all SageAI tool tools - Enterprise auto-discovery!"""
        return EnterpriseToolRegistry.get_tools_metadata("sageai_tools")
    
    @enterprise_tool(category="sageai_tools")
    @staticmethod
    async def list_sageai_tools(
        token: str
    ) -> str:
        """List all available SageAI tools"""
        try:
            with observability.trace_operation("tool_execution", tool="list_sageai_tools"):
                # Policy enforcement
                policy_decision = await policy_enforcement.enforce_policy("list_sageai_tools", token)
                if not policy_decision.allowed:
                    return f"Policy violation: {policy_decision.reason}"
                
                # Validate token and get user info
                user_info = await sageai_auth.validate_token(token)
                if not user_info:
                    return "Authentication failed: Invalid or expired token"
                
                # Check permissions
                permissions = await sageai_auth.get_user_permissions(user_info)
                if not permissions.get('can_execute_tools', False):
                    return "Permission denied: User cannot access SageAI tools"
                
                # Check rate limit
                is_allowed, rate_info = await rate_limiter.check_rate_limit(
                    "list_sageai_tools", "tool"
                )
                
                if not is_allowed:
                    return f"Rate limit exceeded for list_sageai_tools. Retry after {rate_info.get('window', 60)} seconds"
                
                # List tools from SageAI platform
                tools = await sageai_tool_client.list_tools(token)
                
                if tools:
                    tool_list = []
                    for tool in tools:
                        tool_info = f"{tool.get('name', 'Unknown')} (ID: {tool.get('id', 'unknown')})"
                        if tool.get('status') == 'active':
                            tool_info += " [ACTIVE]"
                        if tool.get('category'):
                            tool_info += f" [{tool.get('category').upper()}]"
                        tool_list.append(tool_info)
                    
                    result = f"Found {len(tools)} SageAI tools from platform:\n" + "\n".join(tool_list)
                else:
                    result = "No SageAI tools found or unable to retrieve tool list from platform"
                
                observability.record_tool_execution("list_sageai_tools", "success")
                observability.log("info", "SageAI tools listed", 
                               user_id=user_info.get('user_id'), tool_count=len(tools))
                
                return result
                
        except Exception as e:
            observability.record_tool_execution("list_sageai_tools", "error")
            observability.log("error", "SageAI tool listing failed", error=str(e))
            return f"SageAI tool listing failed: {str(e)}"
    
    @enterprise_tool(category="sageai_tools")
    @staticmethod
    async def get_sageai_tool_details(
        tool_id: str,
        token: str
    ) -> str:
        """Get details for a specific SageAI tool"""
        try:
            with observability.trace_operation("tool_execution", tool="get_sageai_tool_details"):
                # Policy enforcement
                policy_decision = await policy_enforcement.enforce_policy("get_sageai_tool_details", token)
                if not policy_decision.allowed:
                    return f"Policy violation: {policy_decision.reason}"
                
                # Validate token and get user info
                user_info = await sageai_auth.validate_token(token)
                if not user_info:
                    return "Authentication failed: Invalid or expired token"
                
                # Check permissions
                permissions = await sageai_auth.get_user_permissions(user_info)
                if not permissions.get('can_execute_tools', False):
                    return "Permission denied: User cannot access SageAI tools"
                
                # Check rate limit
                is_allowed, rate_info = await rate_limiter.check_rate_limit(
                    "get_sageai_tool_details", "tool"
                )
                
                if not is_allowed:
                    return f"Rate limit exceeded for get_sageai_tool_details. Retry after {rate_info.get('window', 60)} seconds"
                
                # Get tool details
                tool_details = await sageai_tool_client.get_tool_details(tool_id, token)
                
                if tool_details:
                    result = f"Tool '{tool_id}' details: {tool_details.get('description', 'No description available')}"
                else:
                    result = f"Tool '{tool_id}' not found or unable to retrieve details"
                
                observability.record_tool_execution("get_sageai_tool_details", "success")
                observability.log("info", "SageAI tool details retrieved", 
                               user_id=user_info.get('user_id'), tool_id=tool_id)
                
                return result
                
        except Exception as e:
            observability.record_tool_execution("get_sageai_tool_details", "error")
            observability.log("error", "SageAI tool details retrieval failed", error=str(e))
            return f"SageAI tool details retrieval failed: {str(e)}"
    
    @enterprise_tool(category="sageai_tools")
    @staticmethod
    async def execute_sageai_tool(
        tool_id: str,
        parameters: dict,
        token: str
    ) -> str:
        """Execute a SageAI tool with parameters"""
        try:
            with observability.trace_operation("tool_execution", tool="execute_sageai_tool"):
                # Policy enforcement
                policy_decision = await policy_enforcement.enforce_policy("execute_sageai_tool", token, parameters)
                if not policy_decision.allowed:
                    return f"Policy violation: {policy_decision.reason}"
                
                # Validate token and get user info
                user_info = await sageai_auth.validate_token(token)
                if not user_info:
                    return "Authentication failed: Invalid or expired token"
                
                # Check permissions
                permissions = await sageai_auth.get_user_permissions(user_info)
                if not permissions.get('can_execute_tools', False):
                    return "Permission denied: User cannot execute SageAI tools"
                
                # Check rate limit
                is_allowed, rate_info = await rate_limiter.check_rate_limit(
                    "execute_sageai_tool", "tool"
                )
                
                if not is_allowed:
                    return f"Rate limit exceeded for execute_sageai_tool. Retry after {rate_info.get('window', 60)} seconds"
                
                # Execute tool from SageAI platform
                result = await sageai_tool_client.execute_tool(tool_id, parameters, token)
                
                if result and result.get('success', False):
                    output = result.get('output', 'No output available')
                    execution_time = result.get('execution_time', 0)
                    status = result.get('status', 'completed')
                    attempt = result.get('attempt', 1)
                    
                    response_text = f"✅ Tool '{tool_id}' executed successfully!\n"
                    response_text += f"Status: {status}\n"
                    response_text += f"Execution Time: {execution_time:.2f}s\n"
                    response_text += f"Attempt: {attempt}/{result.get('max_retries', 3)}\n"
                    response_text += f"Result: {output}"
                else:
                    error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
                    max_retries = result.get('max_retries', 3) if result else 3
                    response_text = f"❌ Tool '{tool_id}' execution failed after {max_retries} attempts: {error_msg}"
                
                observability.record_tool_execution("execute_sageai_tool", "success")
                observability.log("info", "SageAI tool executed", 
                               user_id=user_info.get('user_id'), tool_id=tool_id)
                
                return response_text
                
        except Exception as e:
            observability.record_tool_execution("execute_sageai_tool", "error")
            observability.log("error", "SageAI tool execution failed", error=str(e))
            return f"SageAI tool execution failed: {str(e)}"
