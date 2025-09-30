"""
Example showing how to create a custom agent with auto-registration and telemetry

This example demonstrates TWO tool patterns:
1. MCP Tools - Enterprise tools shared across all agents (via MCPToolset)
2. Custom Agent Tools - Agent-specific tools (via FunctionTool)

Use this as a reference to create new agents by:
- Copying this structure
- Modifying the custom tools for your specific needs
- Adding/removing MCP tools as needed
- Updating agent capabilities and configuration
"""

import asyncio
import yaml
import logging
from typing import Dict, Any, List

from google.adk import Agent
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool, MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams
from adk_shared.agent_registry import SelfRegisteringAgent, AgentCapability
from adk_shared.observability import setup_observability, get_tracer
from adk_shared.litellm_integration import create_agent_llm_config, get_litellm_wrapper


# Custom analytics function for the agent
async def run_custom_analytics(data_source: str, analysis_type: str, **kwargs) -> Dict[str, Any]:
    """Execute custom analytics - this is the actual function that will be called"""
    # Mock implementation
    return {
        "analysis_type": analysis_type,
        "data_source": data_source,
        "results": {"trend": "positive", "confidence": 0.87},
        "processing_time_ms": 1500
    }


class CustomAnalyticsTool(FunctionTool):
    """Custom tool for the agent - demonstrates agent-specific tools"""
    
    def __init__(self):
        super().__init__(
            func=run_custom_analytics
        )


class MyCustomAgent(SelfRegisteringAgent, LlmAgent):
    """Example custom agent with auto-registration"""
    
    def __init__(self, config_path: str = "config/agent_config.yaml"):
        
        # Load configuration
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Initialize both MCP tools (enterprise shared) and custom agent tools
        # 1. MCP Tools - Enterprise tools shared across all agents (MCP Client)
        # Following ADK documentation: https://google.github.io/adk-docs/tools/mcp-tools/
        mcp_config = config.get('mcp_server', {})
        
        # Validate MCP configuration
        if not mcp_config.get('url'):
            logging.warning("MCP server URL not configured, using default")
            mcp_config['url'] = 'http://localhost:8000/mcp'
        
        # Create MCP toolset with proper error handling
        try:
            mcp_toolset = MCPToolset(
                connection_params=SseConnectionParams(
                    url=mcp_config.get('url'),
                    headers=mcp_config.get('headers', {})
                ),
                tool_filter=mcp_config.get('tool_filter', ['run_analytics', 'query_database', 'search_documents'])
            )
            logging.info(f"MCP toolset initialized with {len(mcp_config.get('tool_filter', []))} filtered tools")
        except Exception as e:
            logging.error(f"Failed to initialize MCP toolset: {e}")
            # Fallback to empty toolset if MCP connection fails
            mcp_toolset = None
        
        # 2. Custom Agent Tools - Agent-specific functionality
        custom_tools = [CustomAnalyticsTool()]
        
        # Combine both types of tools (handle MCP connection failures gracefully)
        all_tools = custom_tools
        if mcp_toolset is not None:
            all_tools = [mcp_toolset] + custom_tools
            logging.info("Agent initialized with both MCP and custom tools")
        else:
            logging.warning("Agent initialized with custom tools only (MCP connection failed)")
        
        # Define specific capabilities (these will be auto-registered)
        agent_capabilities = [
            AgentCapability(
                name="custom_analytics",
                description="Advanced business analytics and trend analysis",
                input_schema={
                    "type": "object",
                    "properties": {
                        "data_source": {"type": "string"},
                        "analysis_type": {"type": "string"},
                        "parameters": {"type": "object"}
                    },
                    "required": ["data_source", "analysis_type"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "results": {"type": "object"},
                        "confidence": {"type": "number"},
                        "recommendations": {"type": "array"}
                    }
                },
                complexity_score=2.5,  # High complexity
                estimated_duration=6.0  # 6 seconds average
            ),
            AgentCapability(
                name="trend_forecasting",
                description="Predict future trends based on historical data",
                input_schema={
                    "type": "object",
                    "properties": {
                        "historical_data": {"type": "array"},
                        "forecast_period": {"type": "string"},
                        "confidence_level": {"type": "number"}
                    },
                    "required": ["historical_data", "forecast_period"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "forecast": {"type": "array"},
                        "accuracy": {"type": "number"},
                        "trend_direction": {"type": "string"}
                    }
                },
                complexity_score=3.0,  # Very high complexity
                estimated_duration=10.0  # 10 seconds average
            )
        ]
        
        # Create LiteLLM-compatible configuration
        llm_config = create_agent_llm_config('example_agent')
        
        # Initialize Agent with both MCP and custom tools
        Agent.__init__(
            self,
            name="CustomAnalyticsAgent",
            description="Advanced analytics agent with trend forecasting capabilities",
            tools=all_tools,
            llm_config=llm_config
        )
        
        # Initialize SelfRegisteringAgent with configuration
        SelfRegisteringAgent.__init__(
            self,
            registry_url=config.get('registry_url', 'redis://localhost:6379'),
            auto_register=config.get('auto_register', True),
            heartbeat_interval=config.get('heartbeat_interval', 30)
        )
        
        # Set agent-specific attributes for registration
        self.version = "1.0.0"
        self.agent_capabilities = agent_capabilities
        self.max_concurrent_requests = config.get('max_concurrent_requests', 8)
        self.tags = set(config.get('tags', ['analytics', 'forecasting', 'business']))
        self.priority = config.get('priority', 3)  # High priority
        
        # Initialize LiteLLM wrapper for enhanced functionality
        self.litellm_wrapper = get_litellm_wrapper('example_agent')
        self.tracer = get_tracer("custom-analytics-agent")
        
        # Store MCP toolset for proper cleanup
        self.mcp_toolset = mcp_toolset
    
    async def cleanup(self):
        """Cleanup MCP connections following ADK documentation patterns"""
        if self.mcp_toolset is not None:
            try:
                # Close MCP connections properly
                await self.mcp_toolset.close()
                logging.info("MCP toolset connections closed successfully")
            except Exception as e:
                logging.error(f"Error closing MCP toolset: {e}")
        
    async def process_request(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process analytics requests with enhanced capabilities"""
        
        # Use the inherited telemetry from SelfRegisteringAgent
        with self.tracer.start_as_current_span("custom_analytics_processing") as span:
            span.set_attribute("query_type", "custom_analytics")
            
            try:
                # Enhanced prompt for analytics
                analytics_prompt = f"""
                You are an advanced analytics agent. Process this request:
                
                Query: {query}
                Context: {context or {}}
                
                Available capabilities:
                1. Custom analytics on business data
                2. Trend forecasting with confidence intervals
                3. Data visualization recommendations
                
                Use the appropriate tools and provide detailed insights.
                """
                
                # Use LiteLLM wrapper for enhanced functionality
                messages = [
                    {"role": "user", "content": analytics_prompt}
                ]
                
                response = await self.litellm_wrapper.chat_completion(messages)
                response_content = response.get('content', '')
                
                return {
                    "agent": "CustomAnalyticsAgent",
                    "capability_used": "custom_analytics",
                    "query": query,
                    "response": response_content,
                    "model": response.get('model', 'unknown'),
                    "usage": response.get('usage', {}),
                    "metadata": {
                        "analysis_depth": "comprehensive",
                        "confidence_level": 0.92,
                        "visualization_available": True
                    }
                }
                
            except Exception as e:
                span.record_exception(e)
                logging.error(f"Custom analytics processing failed: {str(e)}")
                raise
