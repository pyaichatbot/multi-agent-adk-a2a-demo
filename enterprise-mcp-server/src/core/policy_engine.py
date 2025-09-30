"""
Enterprise Policy Engine for SageAI MCP Server
Provides governance, access control, and compliance monitoring
"""

import yaml
import json
import time
import asyncio
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import logging

from src.core.observability import observability
from src.config.settings import settings

@dataclass
class PolicyDecision:
    """Policy decision result"""
    allowed: bool
    reason: str
    restrictions: Dict[str, Any]
    expires_at: Optional[datetime] = None

@dataclass
class PolicyViolation:
    """Policy violation record"""
    timestamp: datetime
    user_id: str
    resource_type: str  # 'agent' or 'tool'
    resource_id: str
    action: str
    violation_type: str
    details: Dict[str, Any]

@dataclass
class ComplianceMetrics:
    """Compliance monitoring metrics"""
    total_requests: int = 0
    allowed_requests: int = 0
    denied_requests: int = 0
    policy_violations: int = 0
    rate_limit_hits: int = 0
    execution_time_violations: int = 0
    parameter_violations: int = 0

class PolicyEngine:
    """Enterprise policy engine with YAML and database support"""
    
    def __init__(self):
        self.enabled: bool = True
        self.policies: Dict[str, Any] = {}
        self.violations: List[PolicyViolation] = []
        self.metrics = ComplianceMetrics()
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger("policy_engine")
        self.logger.setLevel(logging.INFO)
        
        # Initialize policy sources
        self.yaml_config_path = Path("sageai_policies.yaml")
        self.db_config = None  # Will be set when database is available
        
    async def initialize(self):
        """Initialize policy engine with all sources"""
        try:
            # Load from database first (if available)
            await self.load_policies_from_database()
            
            # Fallback to YAML if database not available
            if not self.policies:
                await self.load_policies_from_yaml()
                
            # Initialize rate limiting
            await self.initialize_rate_limits()
            
            observability.log("info", "Policy engine initialized", 
                           policy_count=len(self.policies),
                           sources=["database", "yaml"])
                           
        except Exception as e:
            observability.log("error", "Failed to initialize policy engine", 
                           error=str(e))
            raise

    async def load_policies_from_database(self) -> bool:
        """Load policies from database (SageAI SQL Server/CosmosDB)"""
        try:
            # TODO: Implement database connection when available
            # For now, return False to indicate database not available
            observability.log("info", "Database policy source not available", 
                           source="database")
            return False
            
        except Exception as e:
            observability.log("error", "Failed to load policies from database", 
                           error=str(e))
            return False

    async def load_policies_from_yaml(self) -> Dict[str, Any]:
        """Load policies from YAML configuration file"""
        try:
            if not self.yaml_config_path.exists():
                # Create default YAML configuration
                await self.create_default_yaml_config()
                
            with open(self.yaml_config_path, 'r') as file:
                config = yaml.safe_load(file)
                
            self.policies = config.get('sageai_governance', {})
            observability.log("info", "Policies loaded from YAML", 
                           file_path=str(self.yaml_config_path),
                           source="yaml")
            return self.policies
            
        except Exception as e:
            observability.log("error", "Failed to load policies from YAML", 
                           error=str(e))
            # Create default policies
            self.policies = self.get_default_policies()
            return self.policies

    async def create_default_yaml_config(self):
        """Create default YAML configuration file"""
        default_config = {
            'sageai_governance': {
                'enabled': True,
                'policy_engine': 'yaml_based',
                'default_policy': 'deny',
                
                'agents': {
                    'default_policy': 'deny',
                    'allow_list': [],
                    'deny_list': [],
                    'restrictions': {}
                },
                
                'tools': {
                    'default_policy': 'deny',
                    'allow_list': [],
                    'deny_list': [],
                    'restrictions': {}
                },
                
                'users': {
                    'role_based_access': {
                        'admin': {
                            'agents': ['*'],
                            'tools': ['*']
                        },
                        'agent_user': {
                            'agents': [],
                            'tools': []
                        },
                        'tool_user': {
                            'agents': [],
                            'tools': []
                        }
                    }
                },
                
                'rate_limits': {
                    'global': {
                        'requests_per_hour': 1000,
                        'requests_per_minute': 100
                    },
                    'per_user': {
                        'requests_per_hour': 100,
                        'requests_per_minute': 10
                    },
                    'per_agent': {
                        'requests_per_hour': 50,
                        'requests_per_minute': 5
                    },
                    'per_tool': {
                        'requests_per_hour': 50,
                        'requests_per_minute': 5
                    }
                },
                
                'execution_limits': {
                    'max_execution_time': 300,  # 5 minutes
                    'max_memory_usage': '1GB',
                    'max_cpu_usage': '80%'
                }
            }
        }
        
        with open(self.yaml_config_path, 'w') as file:
            yaml.dump(default_config, file, default_flow_style=False, indent=2)
            
        observability.log("info", "Default YAML configuration created", 
                       file_path=str(self.yaml_config_path))

    def get_default_policies(self) -> Dict[str, Any]:
        """Get default policy configuration"""
        return {
            'enabled': True,
            'policy_engine': 'yaml_based',
            'default_policy': 'deny',
            'agents': {'default_policy': 'deny', 'allow_list': [], 'deny_list': []},
            'tools': {'default_policy': 'deny', 'allow_list': [], 'deny_list': []},
            'users': {'role_based_access': {}},
            'rate_limits': {'global': {'requests_per_hour': 1000}},
            'execution_limits': {'max_execution_time': 300}
        }

    async def initialize_rate_limits(self):
        """Initialize rate limiting tracking"""
        self.rate_limits = {
            'global': {'requests': [], 'limit': 1000, 'window': 3600},
            'per_user': {},
            'per_agent': {},
            'per_tool': {}
        }

    async def evaluate_policy(self, 
                            user_id: str, 
                            user_role: str,
                            resource_type: str,  # 'agent' or 'tool'
                            resource_id: str,
                            action: str = 'execute',
                            parameters: Optional[Dict[str, Any]] = None) -> PolicyDecision:
        """Evaluate policy for user access to resource"""
        try:
            # Check if policy engine is enabled
            if not self.policies.get('enabled', True):
                return PolicyDecision(allowed=True, reason="Policy engine disabled", restrictions={})
            
            # Get user permissions
            user_permissions = await self.get_user_permissions(user_id, user_role)
            
            # Check resource access
            access_allowed = await self.check_resource_access(
                user_permissions, resource_type, resource_id
            )
            
            if not access_allowed:
                await self.record_violation(user_id, resource_type, resource_id, action, "access_denied")
                return PolicyDecision(
                    allowed=False, 
                    reason="Access denied by policy",
                    restrictions={}
                )
            
            # Check rate limits
            rate_limit_ok = await self.check_rate_limits(user_id, resource_type, resource_id)
            if not rate_limit_ok:
                await self.record_violation(user_id, resource_type, resource_id, action, "rate_limit_exceeded")
                return PolicyDecision(
                    allowed=False,
                    reason="Rate limit exceeded",
                    restrictions={}
                )
            
            # Get execution restrictions
            restrictions = await self.get_execution_restrictions(resource_type, resource_id)
            
            # Validate parameters
            if parameters:
                param_validation = await self.validate_parameters(resource_type, resource_id, parameters)
                if not param_validation['valid']:
                    await self.record_violation(user_id, resource_type, resource_id, action, "parameter_violation", param_validation)
                    return PolicyDecision(
                        allowed=False,
                        reason=f"Parameter violation: {param_validation['reason']}",
                        restrictions=restrictions
                    )
            
            # Update metrics
            self.metrics.total_requests += 1
            self.metrics.allowed_requests += 1
            
            return PolicyDecision(
                allowed=True,
                reason="Access granted",
                restrictions=restrictions
            )
            
        except Exception as e:
            observability.log("error", "Policy evaluation failed", 
                           error=str(e), user_id=user_id, resource_type=resource_type, resource_id=resource_id)
            return PolicyDecision(
                allowed=False,
                reason=f"Policy evaluation error: {str(e)}",
                restrictions={}
            )

    async def get_user_permissions(self, user_id: str, user_role: str) -> Dict[str, Any]:
        """Get user permissions based on role"""
        try:
            role_access = self.policies.get('users', {}).get('role_based_access', {}).get(user_role, {})
            
            return {
                'agents': role_access.get('agents', []),
                'tools': role_access.get('tools', []),
                'role': user_role
            }
            
        except Exception as e:
            observability.log("error", "Failed to get user permissions", 
                           error=str(e), user_id=user_id, user_role=user_role)
            return {'agents': [], 'tools': [], 'role': user_role}

    async def check_resource_access(self, user_permissions: Dict[str, Any], 
                                 resource_type: str, resource_id: str) -> bool:
        """Check if user has access to specific resource"""
        try:
            if resource_type == 'agent':
                allowed_resources = user_permissions.get('agents', [])
            elif resource_type == 'tool':
                allowed_resources = user_permissions.get('tools', [])
            else:
                return False
            
            # Check for wildcard access
            if '*' in allowed_resources:
                return True
            
            # Check specific resource access
            return resource_id in allowed_resources
            
        except Exception as e:
            observability.log("error", "Failed to check resource access", 
                           error=str(e), resource_type=resource_type, resource_id=resource_id)
            return False

    async def check_rate_limits(self, user_id: str, resource_type: str, resource_id: str) -> bool:
        """Check rate limits for user and resource"""
        try:
            current_time = time.time()
            
            # Check global rate limit
            global_requests = self.rate_limits['global']['requests']
            global_requests = [req_time for req_time in global_requests if current_time - req_time < 3600]
            if len(global_requests) >= self.rate_limits['global']['limit']:
                return False
            
            # Check per-user rate limit
            if user_id not in self.rate_limits['per_user']:
                self.rate_limits['per_user'][user_id] = {'requests': [], 'limit': 100, 'window': 3600}
            
            user_requests = self.rate_limits['per_user'][user_id]['requests']
            user_requests = [req_time for req_time in user_requests if current_time - req_time < 3600]
            if len(user_requests) >= self.rate_limits['per_user'][user_id]['limit']:
                return False
            
            # Check per-resource rate limit
            resource_key = f"{resource_type}_{resource_id}"
            if resource_key not in self.rate_limits['per_agent']:
                self.rate_limits['per_agent'][resource_key] = {'requests': [], 'limit': 50, 'window': 3600}
            
            resource_requests = self.rate_limits['per_agent'][resource_key]['requests']
            resource_requests = [req_time for req_time in resource_requests if current_time - req_time < 3600]
            if len(resource_requests) >= self.rate_limits['per_agent'][resource_key]['limit']:
                return False
            
            # Update rate limit tracking
            self.rate_limits['global']['requests'].append(current_time)
            self.rate_limits['per_user'][user_id]['requests'].append(current_time)
            self.rate_limits['per_agent'][resource_key]['requests'].append(current_time)
            
            return True
            
        except Exception as e:
            observability.log("error", "Failed to check rate limits", 
                           error=str(e), user_id=user_id, resource_type=resource_type, resource_id=resource_id)
            return False

    async def get_execution_restrictions(self, resource_type: str, resource_id: str) -> Dict[str, Any]:
        """Get execution restrictions for resource"""
        try:
            restrictions = {}
            
            if resource_type == 'agent':
                agent_restrictions = self.policies.get('agents', {}).get('restrictions', {}).get(resource_id, {})
                restrictions.update(agent_restrictions)
            elif resource_type == 'tool':
                tool_restrictions = self.policies.get('tools', {}).get('restrictions', {}).get(resource_id, {})
                restrictions.update(tool_restrictions)
            
            # Add global execution limits
            global_limits = self.policies.get('execution_limits', {})
            restrictions.update(global_limits)
            
            return restrictions
            
        except Exception as e:
            observability.log("error", "Failed to get execution restrictions", 
                           error=str(e), resource_type=resource_type, resource_id=resource_id)
            return {}

    async def validate_parameters(self, resource_type: str, resource_id: str, 
                               parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate execution parameters against policy"""
        try:
            restrictions = await self.get_execution_restrictions(resource_type, resource_id)
            
            # Check allowed parameters
            allowed_params = restrictions.get('allowed_parameters', [])
            if allowed_params and allowed_params != ['*']:
                for param_name in parameters.keys():
                    if param_name not in allowed_params:
                        return {
                            'valid': False,
                            'reason': f"Parameter '{param_name}' not allowed",
                            'allowed_parameters': allowed_params
                        }
            
            # Check forbidden parameters
            forbidden_params = restrictions.get('forbidden_parameters', [])
            for param_name in parameters.keys():
                if param_name in forbidden_params:
                    return {
                        'valid': False,
                        'reason': f"Parameter '{param_name}' is forbidden",
                        'forbidden_parameters': forbidden_params
                    }
            
            return {'valid': True, 'reason': 'Parameters valid'}
            
        except Exception as e:
            observability.log("error", "Failed to validate parameters", 
                           error=str(e), resource_type=resource_type, resource_id=resource_id)
            return {'valid': False, 'reason': f'Validation error: {str(e)}'}

    async def record_violation(self, user_id: str, resource_type: str, resource_id: str, 
                             action: str, violation_type: str, details: Optional[Dict[str, Any]] = None):
        """Record policy violation"""
        try:
            violation = PolicyViolation(
                timestamp=datetime.now(),
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                violation_type=violation_type,
                details=details or {}
            )
            
            self.violations.append(violation)
            self.metrics.policy_violations += 1
            
            # Log violation
            observability.log("warning", "Policy violation recorded", 
                           user_id=user_id, resource_type=resource_type, resource_id=resource_id,
                           violation_type=violation_type, details=details)
            
            # Update specific violation metrics
            if violation_type == "rate_limit_exceeded":
                self.metrics.rate_limit_hits += 1
            elif violation_type == "execution_time_violation":
                self.metrics.execution_time_violations += 1
            elif violation_type == "parameter_violation":
                self.metrics.parameter_violations += 1
                
        except Exception as e:
            observability.log("error", "Failed to record violation", 
                           error=str(e), user_id=user_id, resource_type=resource_type, resource_id=resource_id)

    async def get_compliance_metrics(self) -> Dict[str, Any]:
        """Get compliance monitoring metrics"""
        try:
            total_requests = self.metrics.total_requests
            allowed_requests = self.metrics.allowed_requests
            denied_requests = self.metrics.denied_requests
            
            compliance_rate = (allowed_requests / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'total_requests': total_requests,
                'allowed_requests': allowed_requests,
                'denied_requests': denied_requests,
                'compliance_rate': compliance_rate,
                'policy_violations': self.metrics.policy_violations,
                'rate_limit_hits': self.metrics.rate_limit_hits,
                'execution_time_violations': self.metrics.execution_time_violations,
                'parameter_violations': self.metrics.parameter_violations,
                'violations_by_type': self.get_violations_by_type(),
                'violations_by_user': self.get_violations_by_user(),
                'violations_by_resource': self.get_violations_by_resource()
            }
            
        except Exception as e:
            observability.log("error", "Failed to get compliance metrics", error=str(e))
            return {}

    def get_violations_by_type(self) -> Dict[str, int]:
        """Get violations grouped by type"""
        violations_by_type = {}
        for violation in self.violations:
            violations_by_type[violation.violation_type] = violations_by_type.get(violation.violation_type, 0) + 1
        return violations_by_type

    def get_violations_by_user(self) -> Dict[str, int]:
        """Get violations grouped by user"""
        violations_by_user = {}
        for violation in self.violations:
            violations_by_user[violation.user_id] = violations_by_user.get(violation.user_id, 0) + 1
        return violations_by_user

    def get_violations_by_resource(self) -> Dict[str, int]:
        """Get violations grouped by resource"""
        violations_by_resource = {}
        for violation in self.violations:
            resource_key = f"{violation.resource_type}_{violation.resource_id}"
            violations_by_resource[resource_key] = violations_by_resource.get(resource_key, 0) + 1
        return violations_by_resource

    async def get_audit_trail(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit trail of policy decisions and violations"""
        try:
            audit_entries = []
            
            # Add recent violations
            recent_violations = self.violations[-limit:]
            for violation in recent_violations:
                audit_entries.append({
                    'timestamp': violation.timestamp.isoformat(),
                    'type': 'violation',
                    'user_id': violation.user_id,
                    'resource_type': violation.resource_type,
                    'resource_id': violation.resource_id,
                    'action': violation.action,
                    'violation_type': violation.violation_type,
                    'details': violation.details
                })
            
            # Sort by timestamp (newest first)
            audit_entries.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return audit_entries[:limit]
            
        except Exception as e:
            observability.log("error", "Failed to get audit trail", error=str(e))
            return []

    async def reload_policies(self):
        """Reload policies from all sources"""
        try:
            # Clear existing policies
            self.policies = {}
            
            # Reload from database first
            await self.load_policies_from_database()
            
            # Fallback to YAML if database not available
            if not self.policies:
                await self.load_policies_from_yaml()
            
            # Reinitialize rate limits
            await self.initialize_rate_limits()
            
            observability.log("info", "Policies reloaded successfully", 
                           policy_count=len(self.policies))
            
        except Exception as e:
            observability.log("error", "Failed to reload policies", error=str(e))
            raise

# Global policy engine instance
policy_engine = PolicyEngine()
