"""
Policy Enforcement Middleware for SageAI MCP Server
Integrates policy engine with MCP tool execution
"""

import time
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.core.policy_engine import policy_engine, PolicyDecision
from src.core.observability import observability
from src.core.sageai_auth import sageai_auth

class PolicyEnforcement:
    """Policy enforcement middleware for MCP tool execution"""
    
    def __init__(self):
        self.enforcement_enabled = True
        self.execution_times: Dict[str, float] = {}
        
    async def enforce_policy(self, 
                           tool_name: str,
                           user_token: str,
                           parameters: Optional[Dict[str, Any]] = None) -> PolicyDecision:
        """Enforce policy for MCP tool execution"""
        try:
            if not self.enforcement_enabled:
                return PolicyDecision(allowed=True, reason="Policy enforcement disabled", restrictions={})
            
            # Extract user information from token
            user_info = await sageai_auth.validate_token(user_token)
            if not user_info:
                return PolicyDecision(
                    allowed=False, 
                    reason="Invalid or expired token",
                    restrictions={}
                )
            
            user_id = user_info.get('user_id', 'unknown')
            user_role = user_info.get('role', 'user')
            
            # Determine resource type and ID
            resource_type, resource_id = self._parse_tool_name(tool_name)
            
            # Evaluate policy
            policy_decision = await policy_engine.evaluate_policy(
                user_id=user_id,
                user_role=user_role,
                resource_type=resource_type,
                resource_id=resource_id,
                action='execute',
                parameters=parameters
            )
            
            # Record policy decision
            await self._record_policy_decision(tool_name, user_id, policy_decision)
            
            return policy_decision
            
        except Exception as e:
            observability.log("error", "Policy enforcement failed", 
                           error=str(e), tool_name=tool_name)
            return PolicyDecision(
                allowed=False,
                reason=f"Policy enforcement error: {str(e)}",
                restrictions={}
            )
    
    def _parse_tool_name(self, tool_name: str) -> tuple[str, str]:
        """Parse tool name to extract resource type and ID"""
        try:
            if tool_name.startswith('list_sageai_agents') or tool_name.startswith('get_sageai_agent') or tool_name.startswith('invoke_sageai_agent'):
                return 'agent', tool_name.replace('sageai_', '').replace('_', '-')
            elif tool_name.startswith('list_sageai_tools') or tool_name.startswith('get_sageai_tool') or tool_name.startswith('execute_sageai_tool'):
                return 'tool', tool_name.replace('sageai_', '').replace('_', '-')
            else:
                # For system tools, use generic resource
                return 'system', tool_name
                
        except Exception as e:
            observability.log("error", "Failed to parse tool name", 
                           error=str(e), tool_name=tool_name)
            return 'unknown', tool_name
    
    async def _record_policy_decision(self, tool_name: str, user_id: str, decision: PolicyDecision):
        """Record policy decision for audit trail"""
        try:
            observability.log("info", "Policy decision recorded", 
                           tool_name=tool_name, user_id=user_id, 
                           allowed=decision.allowed, reason=decision.reason)
                           
        except Exception as e:
            observability.log("error", "Failed to record policy decision", 
                           error=str(e), tool_name=tool_name, user_id=user_id)
    
    async def enforce_execution_limits(self, tool_name: str, execution_time: float, 
                                     max_time: Optional[float] = None) -> bool:
        """Enforce execution time limits"""
        try:
            if max_time is None:
                max_time = 300  # Default 5 minutes
            
            if execution_time > max_time:
                await policy_engine.record_violation(
                    user_id="system",
                    resource_type="execution",
                    resource_id=tool_name,
                    action="execute",
                    violation_type="execution_time_violation",
                    details={"execution_time": execution_time, "max_time": max_time}
                )
                return False
            
            return True
            
        except Exception as e:
            observability.log("error", "Failed to enforce execution limits", 
                           error=str(e), tool_name=tool_name, execution_time=execution_time)
            return True
    
    async def get_user_accessible_tools(self, user_token: str) -> List[str]:
        """Get list of tools accessible to user based on policies"""
        try:
            user_info = await sageai_auth.validate_token(user_token)
            if not user_info:
                return []
            
            user_id = user_info.get('user_id', 'unknown')
            user_role = user_info.get('role', 'user')
            
            # Get user permissions
            user_permissions = await policy_engine.get_user_permissions(user_id, user_role)
            
            accessible_tools = []
            
            # Add SageAI agent tools if user has access
            if user_permissions.get('agents'):
                accessible_tools.extend([
                    'list_sageai_agents',
                    'get_sageai_agent_details',
                    'invoke_sageai_agent'
                ])
            
            # Add SageAI tool tools if user has access
            if user_permissions.get('tools'):
                accessible_tools.extend([
                    'list_sageai_tools',
                    'get_sageai_tool_details',
                    'execute_sageai_tool'
                ])
            
            # Always add system tools
            accessible_tools.extend([
                'get_system_info',
                'check_health',
                'list_tools',
                'get_tool_info'
            ])
            
            return accessible_tools
            
        except Exception as e:
            observability.log("error", "Failed to get user accessible tools", 
                           error=str(e))
            return []
    
    async def get_compliance_report(self) -> Dict[str, Any]:
        """Get comprehensive compliance report"""
        try:
            # Get policy engine metrics
            policy_metrics = await policy_engine.get_compliance_metrics()
            
            # Get audit trail
            audit_trail = await policy_engine.get_audit_trail(limit=50)
            
            # Get enforcement statistics
            enforcement_stats = {
                'enforcement_enabled': self.enforcement_enabled,
                'total_enforcements': len(self.execution_times),
                'average_execution_time': sum(self.execution_times.values()) / len(self.execution_times) if self.execution_times else 0
            }
            
            return {
                'policy_metrics': policy_metrics,
                'audit_trail': audit_trail,
                'enforcement_stats': enforcement_stats,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            observability.log("error", "Failed to get compliance report", error=str(e))
            return {}
    
    async def reload_policies(self):
        """Reload policies from all sources"""
        try:
            await policy_engine.reload_policies()
            observability.log("info", "Policies reloaded successfully")
            
        except Exception as e:
            observability.log("error", "Failed to reload policies", error=str(e))
            raise
    
    def enable_enforcement(self):
        """Enable policy enforcement"""
        self.enforcement_enabled = True
        observability.log("info", "Policy enforcement enabled")
    
    def disable_enforcement(self):
        """Disable policy enforcement"""
        self.enforcement_enabled = False
        observability.log("info", "Policy enforcement disabled")

# Global policy enforcement instance
policy_enforcement = PolicyEnforcement()
