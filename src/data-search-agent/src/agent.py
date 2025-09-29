"""
Data Search Agent - Specialized agent for data retrieval operations
Uses MCP tools for database queries and document searches
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional
import logging

from google.adk import Agent
from google.adk.agents import LlmAgent
from google.adk.tools import MCPToolset
from adk_shared.observability import get_tracer
from adk_shared.security import get_auth_token
from adk_shared.litellm_integration import create_agent_llm_config, get_litellm_wrapper
import yaml


class DataSearchAgent(LlmAgent):
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
        
        super().__init__(
            name="DataSearchAgent",
            description="Specialized agent for enterprise data search and retrieval",
            tools=[mcp_toolset],
            llm_config=llm_config
        )
        
        # Initialize LiteLLM wrapper for enhanced functionality
        self.litellm_wrapper = get_litellm_wrapper('data_search')
        self.tracer = get_tracer("data-search-agent")
    
    async def process_request(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process data search requests with full observability"""
        transaction_id = str(uuid.uuid4())
        
        with self.tracer.start_as_current_span("data_search_request") as span:
            span.set_attribute("transaction_id", transaction_id)
            span.set_attribute("query", query)
            
            try:
                # Use LiteLLM wrapper for enhanced functionality
                messages = [
                    {"role": "user", "content": f"Search for data based on this query: {query}. Context: {context or {}}"}
                ]
                
                response = await self.litellm_wrapper.chat_completion(messages)
                
                return {
                    "transaction_id": transaction_id,
                    "agent": "DataSearchAgent",
                    "query": query,
                    "response": response.get('content', ''),
                    "model": response.get('model', 'unknown'),
                    "usage": response.get('usage', {}),
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                span.record_exception(e)
                logging.error(f"Data search failed: {transaction_id} - {str(e)}")
                raise
