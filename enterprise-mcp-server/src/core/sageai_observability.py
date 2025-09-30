"""
SageAI Observability Module
SOLID Principle: Single Responsibility - Handles SageAI-specific observability
Enterprise Standard: Clean, maintainable observability with correlation tracking
"""

import time
from typing import Dict, Any, Optional
from datetime import datetime

from .observability import observability


class SageAIObservability:
    """Enterprise SageAI observability with correlation tracking"""
    
    def __init__(self):
        self.sageai_api_calls = 0
        self.sageai_success_count = 0
        self.sageai_error_count = 0
        self.sageai_latency_sum = 0.0
        self.agent_invocations = 0
        self.tool_executions = 0
        
    def record_sageai_api_call(self, endpoint: str, method: str, status_code: int, 
                              latency: float, user_id: Optional[str] = None):
        """Record SageAI API call metrics"""
        self.sageai_api_calls += 1
        self.sageai_latency_sum += latency
        
        if 200 <= status_code < 300:
            self.sageai_success_count += 1
            observability.log("info", "SageAI API call successful", 
                           endpoint=endpoint, method=method, 
                           status_code=status_code, latency=latency, user_id=user_id)
        else:
            self.sageai_error_count += 1
            observability.log("warning", "SageAI API call failed", 
                           endpoint=endpoint, method=method, 
                           status_code=status_code, latency=latency, user_id=user_id)
    
    def record_agent_invocation(self, agent_id: str, user_id: str, 
                                success: bool, latency: float):
        """Record SageAI agent invocation"""
        self.agent_invocations += 1
        
        if success:
            observability.log("info", "SageAI agent invoked successfully", 
                           agent_id=agent_id, user_id=user_id, latency=latency)
        else:
            observability.log("error", "SageAI agent invocation failed", 
                           agent_id=agent_id, user_id=user_id, latency=latency)
    
    def record_tool_execution(self, tool_id: str, user_id: str, 
                            success: bool, latency: float):
        """Record SageAI tool execution"""
        self.tool_executions += 1
        
        if success:
            observability.log("info", "SageAI tool executed successfully", 
                           tool_id=tool_id, user_id=user_id, latency=latency)
        else:
            observability.log("error", "SageAI tool execution failed", 
                           tool_id=tool_id, user_id=user_id, latency=latency)
    
    def get_sageai_metrics(self) -> Dict[str, Any]:
        """Get SageAI-specific metrics"""
        avg_latency = (self.sageai_latency_sum / self.sageai_api_calls) if self.sageai_api_calls > 0 else 0
        success_rate = (self.sageai_success_count / self.sageai_api_calls) if self.sageai_api_calls > 0 else 0
        
        return {
            "sageai_api_calls": self.sageai_api_calls,
            "sageai_success_count": self.sageai_success_count,
            "sageai_error_count": self.sageai_error_count,
            "sageai_success_rate": success_rate,
            "sageai_avg_latency": avg_latency,
            "agent_invocations": self.agent_invocations,
            "tool_executions": self.tool_executions,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get SageAI health status"""
        return {
            "sageai_connected": True,  # Would check actual connectivity
            "api_calls_today": self.sageai_api_calls,
            "success_rate": (self.sageai_success_count / self.sageai_api_calls) if self.sageai_api_calls > 0 else 0,
            "last_check": datetime.utcnow().isoformat() + "Z"
        }


# Global SageAI observability instance
sageai_observability = SageAIObservability()
