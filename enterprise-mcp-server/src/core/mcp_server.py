"""
Enterprise MCP Server with FastMCP
Production-grade MCP server implementation
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Union
from contextlib import asynccontextmanager

from fastmcp import FastMCP
from fastmcp.server import MCPServer
from fastmcp.types import Tool, TextContent, ImageContent, EmbeddedResource
import httpx
import redis.asyncio as redis

from config.settings import settings
from core.observability import observability, trace_function, log_operation
from core.authentication import entra_auth, permission_manager


class InhouseAgentConnector:
    """Connector for inhouse agents"""
    
    def __init__(self):
        self.agent_endpoints = {
            "data-search-agent": "http://localhost:8002",
            "reporting-agent": "http://localhost:8003", 
            "analytics-agent": "http://localhost:8004"
        }
        self.redis_client = None
    
    async def connect_redis(self):
        """Connect to Redis for caching"""
        try:
            self.redis_client = redis.from_url(settings.redis.url)
            await self.redis_client.ping()
            observability.log_structured("info", "Redis connected for agent caching")
        except Exception as e:
            observability.log_structured("error", "Redis connection failed", error=str(e))
            self.redis_client = None
    
    async def call_agent(self, agent_name: str, method: str, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Call inhouse agent with caching and error handling"""
        try:
            with observability.trace_operation("agent_call", agent=agent_name, method=method):
                # Check cache first
                cache_key = f"agent:{agent_name}:{method}:{hash(str(params))}"
                if self.redis_client:
                    cached_result = await self.redis_client.get(cache_key)
                    if cached_result:
                        observability.log_structured("info", "Cache hit", agent=agent_name, method=method)
                        return json.loads(cached_result)
                
                # Call agent
                endpoint = self.agent_endpoints.get(agent_name)
                if not endpoint:
                    raise ValueError(f"Unknown agent: {agent_name}")
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{endpoint}/{method}",
                        json=params,
                        headers={"X-User-ID": user_id}
                    )
                    response.raise_for_status()
                    result = response.json()
                
                # Cache result
                if self.redis_client:
                    await self.redis_client.setex(
                        cache_key,
                        300,  # 5 minutes cache
                        json.dumps(result)
                    )
                
                observability.log_structured(
                    "info",
                    "Agent call successful",
                    agent=agent_name,
                    method=method,
                    user_id=user_id
                )
                
                return result
                
        except httpx.TimeoutException:
            observability.log_structured(
                "error",
                "Agent call timeout",
                agent=agent_name,
                method=method,
                user_id=user_id
            )
            raise Exception(f"Agent {agent_name} timeout")
        except httpx.HTTPStatusError as e:
            observability.log_structured(
                "error",
                "Agent call failed",
                agent=agent_name,
                method=method,
                status_code=e.response.status_code,
                user_id=user_id
            )
            raise Exception(f"Agent {agent_name} returned error: {e.response.status_code}")
        except Exception as e:
            observability.log_structured(
                "error",
                "Agent call error",
                agent=agent_name,
                method=method,
                error=str(e),
                user_id=user_id
            )
            raise


class EnterpriseMCPServer:
    """Enterprise MCP Server with FastMCP"""
    
    def __init__(self):
        self.mcp = FastMCP("Enterprise MCP Server")
        self.agent_connector = InhouseAgentConnector()
        self.tools_registry = {}
        self._setup_tools()
    
    def _setup_tools(self):
        """Setup MCP tools from inhouse agents"""
        
        # Data Search Agent Tools
        @self.mcp.tool()
        async def search_database(
            query: str,
            database: str = "default",
            limit: int = 100
        ) -> str:
            """Search enterprise database with SQL queries"""
            try:
                with observability.trace_operation("tool_execution", tool="search_database"):
                    result = await self.agent_connector.call_agent(
                        "data-search-agent",
                        "process_request",
                        {
                            "query": query,
                            "context": {
                                "database": database,
                                "limit": limit
                            }
                        },
                        "system"  # System user for internal calls
                    )
                    
                    observability.record_tool_execution("search_database", "success", "system")
                    return f"Database search completed: {result.get('result', 'No results')}"
                    
            except Exception as e:
                observability.record_tool_execution("search_database", "error", "system")
                return f"Database search failed: {str(e)}"
        
        # Reporting Agent Tools
        @self.mcp.tool()
        async def generate_report(
            report_type: str,
            parameters: Dict[str, Any],
            format: str = "pdf"
        ) -> str:
            """Generate business reports and analytics"""
            try:
                with observability.trace_operation("tool_execution", tool="generate_report"):
                    result = await self.agent_connector.call_agent(
                        "reporting-agent",
                        "process_request",
                        {
                            "query": f"Generate {report_type} report",
                            "context": {
                                "report_type": report_type,
                                "parameters": parameters,
                                "format": format
                            }
                        },
                        "system"
                    )
                    
                    observability.record_tool_execution("generate_report", "success", "system")
                    return f"Report generated successfully: {result.get('result', 'Report created')}"
                    
            except Exception as e:
                observability.record_tool_execution("generate_report", "error", "system")
                return f"Report generation failed: {str(e)}"
        
        # Analytics Agent Tools
        @self.mcp.tool()
        async def run_analytics(
            analysis_type: str,
            data_source: str,
            parameters: Dict[str, Any]
        ) -> str:
            """Run advanced analytics and machine learning models"""
            try:
                with observability.trace_operation("tool_execution", tool="run_analytics"):
                    result = await self.agent_connector.call_agent(
                        "analytics-agent",
                        "process_request",
                        {
                            "query": f"Run {analysis_type} analysis",
                            "context": {
                                "analysis_type": analysis_type,
                                "data_source": data_source,
                                "parameters": parameters
                            }
                        },
                        "system"
                    )
                    
                    observability.record_tool_execution("run_analytics", "success", "system")
                    return f"Analytics completed: {result.get('result', 'Analysis finished')}"
                    
            except Exception as e:
                observability.record_tool_execution("run_analytics", "error", "system")
                return f"Analytics failed: {str(e)}"
        
        # Document Search Tool
        @self.mcp.tool()
        async def search_documents(
            query: str,
            repository: str = "enterprise_docs",
            limit: int = 10
        ) -> str:
            """Search through enterprise document repositories"""
            try:
                with observability.trace_operation("tool_execution", tool="search_documents"):
                    result = await self.agent_connector.call_agent(
                        "data-search-agent",
                        "process_request",
                        {
                            "query": f"Search documents: {query}",
                            "context": {
                                "repository": repository,
                                "limit": limit,
                                "search_type": "document"
                            }
                        },
                        "system"
                    )
                    
                    observability.record_tool_execution("search_documents", "success", "system")
                    return f"Document search completed: {result.get('result', 'No documents found')}"
                    
            except Exception as e:
                observability.record_tool_execution("search_documents", "error", "system")
                return f"Document search failed: {str(e)}"
        
        # System Health Tool
        @self.mcp.tool()
        async def check_system_health() -> str:
            """Check system health and agent status"""
            try:
                with observability.trace_operation("tool_execution", tool="check_system_health"):
                    health_status = {}
                    
                    for agent_name, endpoint in self.agent_connector.agent_endpoints.items():
                        try:
                            async with httpx.AsyncClient(timeout=5.0) as client:
                                response = await client.get(f"{endpoint}/health")
                                health_status[agent_name] = {
                                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                                    "response_time": response.elapsed.total_seconds()
                                }
                        except Exception as e:
                            health_status[agent_name] = {
                                "status": "unreachable",
                                "error": str(e)
                            }
                    
                    observability.record_tool_execution("check_system_health", "success", "system")
                    return f"System health check completed: {json.dumps(health_status, indent=2)}"
                    
            except Exception as e:
                observability.record_tool_execution("check_system_health", "error", "system")
                return f"Health check failed: {str(e)}"
    
    async def start(self):
        """Start the MCP server"""
        try:
            # Connect to Redis
            await self.agent_connector.connect_redis()
            
            # Start MCP server
            observability.log_structured(
                "info",
                "Starting Enterprise MCP Server",
                host=settings.mcp.host,
                port=settings.mcp.port
            )
            
            # Start metrics server
            observability.start_metrics_server()
            
            # Run the server
            await self.mcp.run(
                host=settings.mcp.host,
                port=settings.mcp.port
            )
            
        except Exception as e:
            observability.log_structured(
                "error",
                "Failed to start MCP server",
                error=str(e)
            )
            raise
    
    async def stop(self):
        """Stop the MCP server"""
        try:
            if self.agent_connector.redis_client:
                await self.agent_connector.redis_client.close()
            
            observability.log_structured("info", "Enterprise MCP Server stopped")
            
        except Exception as e:
            observability.log_structured(
                "error",
                "Error stopping MCP server",
                error=str(e)
            )


# Global server instance
mcp_server = EnterpriseMCPServer()
