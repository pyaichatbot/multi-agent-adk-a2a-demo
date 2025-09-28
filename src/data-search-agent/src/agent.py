"""
Data Search Agent - Specialized agent for data retrieval operations
Uses MCP tools for database queries and document searches
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional
import logging

from adk import Agent, MCPToolset
from adk_shared.observability import get_tracer
from adk_shared.security import get_auth_token
import yaml


class DataSearchAgent(Agent):
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
        
        super().__init__(
            name="DataSearchAgent",
            description="Specialized agent for enterprise data search and retrieval",
            tools=[mcp_toolset],
            llm_config=config['llm']
        )
        
        self.tracer = get_tracer("data-search-agent")
    
    async def process_request(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process data search requests with full observability"""
        transaction_id = str(uuid.uuid4())
        
        with self.tracer.start_as_current_span("data_search_request") as span:
            span.set_attribute("transaction_id", transaction_id)
            span.set_attribute("query", query)
            
            try:
                # Use LLM to determine best approach
                response = await self.chat(
                    f"Search for data based on this query: {query}. "
                    f"Context: {context or {}}"
                )
                
                return {
                    "transaction_id": transaction_id,
                    "agent": "DataSearchAgent",
                    "query": query,
                    "response": response,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                span.record_exception(e)
                logging.error(f"Data search failed: {transaction_id} - {str(e)}")
                raise
