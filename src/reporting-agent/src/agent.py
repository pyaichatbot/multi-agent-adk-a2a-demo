"""
Reporting Agent - Specialized agent for generating business reports
Uses MCP tools for analytics and data processing
Enhanced with auto-registration capabilities
"""

import uuid
import os
import time
from datetime import datetime
from typing import Any, Dict, Optional
import logging

from google.adk import Agent
from google.adk.agents import LlmAgent
from google.adk.tools import MCPToolset
from adk_shared.observability import get_tracer
from adk_shared.security import get_auth_token
from adk_shared.litellm_integration import create_agent_llm_config, get_litellm_wrapper
from adk_shared.agent_registry import SelfRegisteringAgent, AgentCapability
import yaml


class ReportingAgent(SelfRegisteringAgent, LlmAgent):
    """Specialized agent for report generation and analytics"""
    
    def __init__(self, config_path: str = "config/root_agent.yaml"):
        # Load agent configuration
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Initialize with MCP toolset
        mcp_toolset = MCPToolset(
            server_url=config['mcp_server']['url'],
            auth_token=get_auth_token(),
            tools=['run_analytics', 'query_database', 'search_documents']
        )
        
        # Create LiteLLM-compatible configuration
        llm_config = create_agent_llm_config('reporting')
        
        # Initialize LlmAgent first
        LlmAgent.__init__(
            self,
            name="ReportingAgent",
            description="Specialized agent for business reporting and analytics",
            tools=[mcp_toolset],
            llm_config=llm_config
        )
        
        # Initialize SelfRegisteringAgent with auto-registration
        SelfRegisteringAgent.__init__(
            self,
            registry_url=config.get('registry_url'),
            auto_register=config.get('auto_register', True),
            heartbeat_interval=config.get('heartbeat_interval', 30)
        )
        
        # Define agent-specific capabilities
        self.agent_capabilities = [
            AgentCapability(
                name="reporting",
                description="Generate reports and analytics from enterprise data",
                input_schema={
                    "type": "object",
                    "properties": {
                        "report_type": {"type": "string", "description": "Type of report to generate"},
                        "data_source": {"type": "string", "description": "Data source for the report"},
                        "parameters": {"type": "object", "description": "Report parameters"}
                    },
                    "required": ["report_type"]
                },
                output_schema={
                    "type": "object", 
                    "properties": {
                        "report": {"type": "object", "description": "Generated report"},
                        "metadata": {"type": "object", "description": "Report metadata"}
                    }
                },
                complexity_score=2.5,  # High complexity
                estimated_duration=10.0  # 10 seconds average
            ),
            AgentCapability(
                name="analytics",
                description="Perform data analytics and insights generation",
                input_schema={
                    "type": "object",
                    "properties": {
                        "analysis_type": {"type": "string"},
                        "data_scope": {"type": "string"}
                    }
                },
                output_schema={"type": "object"},
                complexity_score=3.0,  # Very high complexity
                estimated_duration=15.0
            )
        ]
        
        # Set additional attributes for auto-registration
        self.version = "2.0.0"
        self.max_concurrent_requests = config.get('max_concurrent_requests', 8)
        self.tags = set(config.get('tags', ['reporting', 'analytics', 'business']))
        self.priority = config.get('priority', 3)  # High priority for reporting agent
        
        # Initialize LiteLLM wrapper for enhanced functionality
        self.litellm_wrapper = get_litellm_wrapper('reporting')
        self.tracer = get_tracer("reporting-agent")
    
    async def process_request(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process reporting requests with enhanced telemetry and auto-registration"""
        # Use the enhanced telemetry from SelfRegisteringAgent
        return await self.process_request_with_telemetry(query, context)
