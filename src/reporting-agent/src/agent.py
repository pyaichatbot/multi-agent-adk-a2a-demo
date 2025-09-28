"""
Reporting Agent - Specialized agent for generating business reports
Uses MCP tools for analytics and data processing
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional
import logging

from adk import Agent, MCPToolset
from adk_shared.observability import get_tracer
from adk_shared.security import get_auth_token
import yaml


class ReportingAgent(Agent):
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
        
        super().__init__(
            name="ReportingAgent",
            description="Specialized agent for business reporting and analytics",
            tools=[mcp_toolset],
            llm_config=config['llm']
        )
        
        self.tracer = get_tracer("reporting-agent")
    
    async def process_request(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process reporting requests with full observability"""
        transaction_id = str(uuid.uuid4())
        
        with self.tracer.start_as_current_span("reporting_request") as span:
            span.set_attribute("transaction_id", transaction_id)
            span.set_attribute("query", query)
            
            try:
                # Use LLM to generate comprehensive reports
                response = await self.chat(
                    f"Generate a comprehensive report based on: {query}. "
                    f"Use analytics tools and data sources as needed. "
                    f"Context: {context or {}}"
                )
                
                return {
                    "transaction_id": transaction_id,
                    "agent": "ReportingAgent",
                    "query": query,
                    "response": response,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                span.record_exception(e)
                logging.error(f"Reporting failed: {transaction_id} - {str(e)}")
                raise
