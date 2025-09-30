"""
Data Search Agent - Specialized agent for data retrieval operations
Uses MCP tools for database queries and document searches
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


class DataSearchAgent(SelfRegisteringAgent, LlmAgent):
    """Specialized agent for data search and retrieval"""
    
    def __init__(self, config_path: str = "config/root_agent.yaml"):
        # Load agent configuration
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Initialize with MCP toolset
        mcp_toolset = MCPToolset(
            server_url=config['mcp_server']['url'],
            auth_token=get_auth_token(),
            tools=['query_database', 'search_documents']
        )
        
        # Create LiteLLM-compatible configuration
        llm_config = create_agent_llm_config('data_search')
        
        # Initialize LlmAgent first
        LlmAgent.__init__(
            self,
            name="DataSearchAgent",
            description="Specialized agent for enterprise data search and retrieval",
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
                name="data_search",
                description="Search and retrieve data from enterprise databases and documents",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "context": {"type": "object", "description": "Additional context"}
                    },
                    "required": ["query"]
                },
                output_schema={
                    "type": "object", 
                    "properties": {
                        "results": {"type": "array", "description": "Search results"},
                        "metadata": {"type": "object", "description": "Result metadata"}
                    }
                },
                complexity_score=1.5,  # Medium complexity
                estimated_duration=3.0  # 3 seconds average
            ),
            AgentCapability(
                name="database_query",
                description="Execute SQL queries against enterprise databases",
                input_schema={
                    "type": "object",
                    "properties": {
                        "sql_query": {"type": "string"},
                        "database": {"type": "string"}
                    }
                },
                output_schema={"type": "object"},
                complexity_score=2.0,  # Higher complexity
                estimated_duration=5.0
            )
        ]
        
        # Set additional attributes for auto-registration
        self.version = "2.0.0"
        self.max_concurrent_requests = config.get('max_concurrent_requests', 15)
        self.tags = set(config.get('tags', ['data', 'search', 'database']))
        self.priority = config.get('priority', 2)  # Higher priority for data agent
        
        # Initialize LiteLLM wrapper for enhanced functionality
        self.litellm_wrapper = get_litellm_wrapper('data_search')
        self.tracer = get_tracer("data-search-agent")
    
    async def process_request(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process data search requests with enhanced telemetry and auto-registration"""
        # Use the enhanced telemetry from SelfRegisteringAgent
        return await self.process_request_with_telemetry(query, context)
