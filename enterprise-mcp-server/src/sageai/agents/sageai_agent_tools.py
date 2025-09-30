"""
SageAI Agent Tools
SOLID Principle: Single Responsibility - Exposes SageAI agents as MCP tools
Enterprise Standard: Zero-configuration auto-discovery with enterprise-grade features
"""

from typing import Any, Dict
from src.core.observability import observability
from src.core.rate_limiter import rate_limiter
from src.core.sageai_auth import sageai_auth
from src.core.sageai_observability import sageai_observability
from src.core.policy_enforcement import policy_enforcement
from src.tools.base_tool import EnterpriseToolRegistry, enterprise_tool
from .agent_client import sageai_agent_client


class SageAIAgentTools:
    """Enterprise SageAI agent tools with zero-configuration auto-discovery"""
    
    @staticmethod
    def get_tools_metadata() -> list:
        """Return metadata for all SageAI agent tools - Enterprise auto-discovery!"""
        return EnterpriseToolRegistry.get_tools_metadata("sageai_agents")
    
    @enterprise_tool(category="sageai_agents")
    @staticmethod
    async def list_sageai_agents(
        token: str
    ) -> str:
        """List all available SageAI agents"""
        try:
            with observability.trace_operation("tool_execution", tool="list_sageai_agents"):
                # Policy enforcement
                policy_decision = await policy_enforcement.enforce_policy("list_sageai_agents", token)
                if not policy_decision.allowed:
                    return f"Policy violation: {policy_decision.reason}"
                
                # Validate token and get user info
                user_info = await sageai_auth.validate_token(token)
                if not user_info:
                    return "Authentication failed: Invalid or expired token"
                
                # Check permissions
                permissions = await sageai_auth.get_user_permissions(user_info)
                if not permissions.get('can_invoke_agents', False):
                    return "Permission denied: User cannot access SageAI agents"
                
                # Check rate limit
                is_allowed, rate_info = await rate_limiter.check_rate_limit(
                    "list_sageai_agents", "tool"
                )
                
                if not is_allowed:
                    return f"Rate limit exceeded for list_sageai_agents. Retry after {rate_info.get('window', 60)} seconds"
                
                # List agents from SageAI platform
                agents = await sageai_agent_client.list_agents(token)
                
                if agents:
                    agent_list = []
                    for agent in agents:
                        agent_info = f"{agent.get('name', 'Unknown')} (ID: {agent.get('id', 'unknown')})"
                        if agent.get('status') == 'active':
                            agent_info += " [ACTIVE]"
                        agent_list.append(agent_info)
                    
                    result = f"Found {len(agents)} SageAI agents from platform:\n" + "\n".join(agent_list)
                else:
                    result = "No SageAI agents found or unable to retrieve agent list from platform"
                
                observability.record_tool_execution("list_sageai_agents", "success")
                observability.log("info", "SageAI agents listed", 
                               user_id=user_info.get('user_id'), agent_count=len(agents))
                
                return result
                
        except Exception as e:
            observability.record_tool_execution("list_sageai_agents", "error")
            observability.log("error", "SageAI agent listing failed", error=str(e))
            return f"SageAI agent listing failed: {str(e)}"
    
    @enterprise_tool(category="sageai_agents")
    @staticmethod
    async def get_sageai_agent_details(
        agent_id: str,
        token: str
    ) -> str:
        """Get details for a specific SageAI agent"""
        try:
            with observability.trace_operation("tool_execution", tool="get_sageai_agent_details"):
                # Policy enforcement
                policy_decision = await policy_enforcement.enforce_policy("get_sageai_agent_details", token)
                if not policy_decision.allowed:
                    return f"Policy violation: {policy_decision.reason}"
                
                # Validate token and get user info
                user_info = await sageai_auth.validate_token(token)
                if not user_info:
                    return "Authentication failed: Invalid or expired token"
                
                # Check permissions
                permissions = await sageai_auth.get_user_permissions(user_info)
                if not permissions.get('can_invoke_agents', False):
                    return "Permission denied: User cannot access SageAI agents"
                
                # Check rate limit
                is_allowed, rate_info = await rate_limiter.check_rate_limit(
                    "get_sageai_agent_details", "tool"
                )
                
                if not is_allowed:
                    return f"Rate limit exceeded for get_sageai_agent_details. Retry after {rate_info.get('window', 60)} seconds"
                
                # Get agent details
                agent_details = await sageai_agent_client.get_agent_details(agent_id, token)
                
                if agent_details:
                    result = f"Agent '{agent_id}' details: {agent_details.get('description', 'No description available')}"
                else:
                    result = f"Agent '{agent_id}' not found or unable to retrieve details"
                
                observability.record_tool_execution("get_sageai_agent_details", "success")
                observability.log("info", "SageAI agent details retrieved", 
                               user_id=user_info.get('user_id'), agent_id=agent_id)
                
                return result
                
        except Exception as e:
            observability.record_tool_execution("get_sageai_agent_details", "error")
            observability.log("error", "SageAI agent details retrieval failed", error=str(e))
            return f"SageAI agent details retrieval failed: {str(e)}"
    
    @enterprise_tool(category="sageai_agents")
    @staticmethod
    async def invoke_sageai_agent(
        agent_id: str,
        input_data: dict,
        token: str,
        parameters: dict = None
    ) -> str:
        """Invoke a SageAI agent with input data and parameters"""
        try:
            with observability.trace_operation("tool_execution", tool="invoke_sageai_agent"):
                # Policy enforcement
                policy_decision = await policy_enforcement.enforce_policy("invoke_sageai_agent", token, parameters)
                if not policy_decision.allowed:
                    return f"Policy violation: {policy_decision.reason}"
                
                # Validate token and get user info
                user_info = await sageai_auth.validate_token(token)
                if not user_info:
                    return "Authentication failed: Invalid or expired token"
                
                # Check permissions
                permissions = await sageai_auth.get_user_permissions(user_info)
                if not permissions.get('can_invoke_agents', False):
                    return "Permission denied: User cannot invoke SageAI agents"
                
                # Check rate limit
                is_allowed, rate_info = await rate_limiter.check_rate_limit(
                    "invoke_sageai_agent", "tool"
                )
                
                if not is_allowed:
                    return f"Rate limit exceeded for invoke_sageai_agent. Retry after {rate_info.get('window', 60)} seconds"
                
                # Invoke agent from SageAI platform
                result = await sageai_agent_client.invoke_agent(agent_id, input_data, parameters, token)
                
                if result and result.get('success', False):
                    output = result.get('output', 'No output available')
                    execution_time = result.get('execution_time', 0)
                    status = result.get('status', 'completed')
                    
                    response_text = f"✅ Agent '{agent_id}' executed successfully!\n"
                    response_text += f"Status: {status}\n"
                    response_text += f"Execution Time: {execution_time:.2f}s\n"
                    response_text += f"Result: {output}"
                else:
                    error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
                    response_text = f"❌ Agent '{agent_id}' execution failed: {error_msg}"
                
                observability.record_tool_execution("invoke_sageai_agent", "success")
                observability.log("info", "SageAI agent invoked", 
                               user_id=user_info.get('user_id'), agent_id=agent_id)
                
                return response_text
                
        except Exception as e:
            observability.record_tool_execution("invoke_sageai_agent", "error")
            observability.log("error", "SageAI agent invocation failed", error=str(e))
            return f"SageAI agent invocation failed: {str(e)}"
