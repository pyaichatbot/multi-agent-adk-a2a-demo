"""
Enterprise MCP Server - Following ADK Documentation
Exposes ADK tools via MCP protocol as per https://google.github.io/adk-docs/tools/mcp-tools/
"""

import asyncio
import logging
import uuid
import yaml
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send

from adk_shared.observability import get_tracer, trace_tool_call, setup_observability
from adk_shared.security import authenticate_request


class EnterpriseMCPServer:
    """Enterprise MCP Server exposing ADK tools via MCP protocol"""
    
    def __init__(self, config_path: str = "config/mcp_config.yaml"):
        # Setup observability first
        setup_observability("enterprise-mcp-server")
        self.tracer = get_tracer("enterprise-mcp-server")
        
        # Load configuration
        self.config = self._load_config(config_path)
        self.tools = {}
        self._register_tools()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load MCP server configuration from YAML"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logging.warning(f"MCP config file {config_path} not found, using defaults")
            return {
                "server": {"name": "enterprise-tools-mcp-server", "version": "1.0.0"},
                "tools": {},
                "security": {"authentication_required": True},
                "observability": {"tracing_enabled": True}
            }
    
    def _register_tools(self):
        """Register ADK tools as MCP tools using configuration"""
        # Register tools based on configuration
        tool_configs = self.config.get('tools', {})
        
        self.tools = {}
        if 'query_database' in tool_configs:
            self.tools["query_database"] = DatabaseQueryTool()
        if 'search_documents' in tool_configs:
            self.tools["search_documents"] = DocumentSearchTool()
        if 'run_analytics' in tool_configs:
            self.tools["run_analytics"] = AnalyticsTool()
        
        logging.info(f"Registered {len(self.tools)} enterprise tools from configuration")
    
    def create_mcp_server(self) -> Server:
        """Create MCP server with tool handlers"""
        app = Server("enterprise-tools-mcp-server")
        
        @app.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.ContentBlock]:
            """Handle MCP tool calls"""
            with self.tracer.start_as_current_span("mcp_tool_call") as span:
                span.set_attribute("tool_name", name)
                
                try:
                    if name not in self.tools:
                        raise ValueError(f"Tool '{name}' not found")
                    
                    tool = self.tools[name]
                    
                    # Extract auth token from arguments if present
                    auth_token = arguments.pop('auth_token', None)
                    
                    # Execute tool with observability
                    result = await tool.execute(auth_token=auth_token, **arguments)
                    
                    return [
                        types.TextContent(
                            type="text",
                            text=f"Tool execution successful: {result}"
                        )
                    ]
                    
                except Exception as e:
                    span.record_exception(e)
                    logging.error(f"MCP tool call failed: {name} - {str(e)}")
                    raise
        
        @app.list_tools()
        async def list_tools() -> list[types.Tool]:
            """List available MCP tools"""
            return [
                types.Tool(
                    name=tool.name,
                    description=tool.description,
                    inputSchema=tool.get_input_schema()
                )
                for tool in self.tools.values()
            ]
        
        return app


class DatabaseQueryTool:
    """ADK Tool: Database queries via MCP"""
    
    name = "query_database"
    description = "Execute SQL queries against enterprise databases"
    
    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "SQL query to execute"},
                "database": {"type": "string", "description": "Target database", "default": "default"},
                "auth_token": {"type": "string", "description": "Authentication token"}
            },
            "required": ["query"]
        }
    
    async def execute(self, query: str, database: str = "default", auth_token: str = None, **kwargs) -> Dict[str, Any]:
        """Execute database query with MCP protocol"""
        transaction_id = str(uuid.uuid4())
        
        with trace_tool_call("database_query", transaction_id, {"query": query, "database": database}):
            try:
                # Authenticate the request
                if not authenticate_request(auth_token):
                    raise PermissionError("Unauthorized database access")
                
                # Mock database query - replace with actual ADK database tool
                result = {
                    "transaction_id": transaction_id,
                    "query": query,
                    "database": database,
                    "rows": [
                        {"id": 1, "name": "Sample Record 1", "value": 100},
                        {"id": 2, "name": "Sample Record 2", "value": 200}
                    ],
                    "row_count": 2,
                    "execution_time_ms": 150,
                    "timestamp": datetime.now().isoformat()
                }
                
                logging.info(f"Database query executed via MCP: {transaction_id}")
                return result
                
            except Exception as e:
                logging.error(f"Database query failed: {transaction_id} - {str(e)}")
                raise


class DocumentSearchTool:
    """ADK Tool: Document search via MCP"""
    
    name = "search_documents"
    description = "Search through enterprise document repositories"
    
    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "repository": {"type": "string", "description": "Document repository", "default": "default"},
                "limit": {"type": "integer", "description": "Maximum results", "default": 10},
                "auth_token": {"type": "string", "description": "Authentication token"}
            },
            "required": ["query"]
        }
    
    async def execute(self, query: str, repository: str = "default", limit: int = 10, auth_token: str = None, **kwargs) -> Dict[str, Any]:
        """Search documents with MCP protocol"""
        transaction_id = str(uuid.uuid4())
        
        with trace_tool_call("document_search", transaction_id, {"query": query, "repository": repository}):
            try:
                # Authenticate the request
                if not authenticate_request(auth_token):
                    raise PermissionError("Unauthorized document access")
                
                # Mock document search - replace with actual ADK search tool
                result = {
                    "transaction_id": transaction_id,
                    "query": query,
                    "repository": repository,
                    "documents": [
                        {
                            "id": "doc_001",
                            "title": "Enterprise Architecture Guidelines",
                            "snippet": "This document outlines best practices...",
                            "score": 0.95,
                            "last_modified": "2024-01-15T10:30:00Z"
                        }
                    ],
                    "total_results": 1,
                    "search_time_ms": 75,
                    "timestamp": datetime.now().isoformat()
                }
                
                logging.info(f"Document search executed via MCP: {transaction_id}")
                return result
                
            except Exception as e:
                logging.error(f"Document search failed: {transaction_id} - {str(e)}")
                raise


class AnalyticsTool:
    """ADK Tool: Analytics via MCP"""
    
    name = "run_analytics"
    description = "Execute analytics queries and generate business insights"
    
    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "analysis_type": {"type": "string", "description": "Type of analysis to perform"},
                "parameters": {"type": "object", "description": "Analysis parameters"},
                "auth_token": {"type": "string", "description": "Authentication token"}
            },
            "required": ["analysis_type", "parameters"]
        }
    
    async def execute(self, analysis_type: str, parameters: Dict[str, Any], auth_token: str = None, **kwargs) -> Dict[str, Any]:
        """Run analytics with MCP protocol"""
        transaction_id = str(uuid.uuid4())
        
        with trace_tool_call("analytics", transaction_id, {"type": analysis_type, "params": parameters}):
            try:
                # Authenticate the request
                if not authenticate_request(auth_token):
                    raise PermissionError("Unauthorized analytics access")
                
                # Mock analytics - replace with actual ADK analytics tool
                result = {
                    "transaction_id": transaction_id,
                    "analysis_type": analysis_type,
                    "parameters": parameters,
                    "insights": [
                        {
                            "metric": "revenue_growth",
                            "value": 15.3,
                            "trend": "increasing",
                            "confidence": 0.92
                        }
                    ],
                    "processing_time_ms": 2100,
                    "timestamp": datetime.now().isoformat()
                }
                
                logging.info(f"Analytics executed via MCP: {transaction_id}")
                return result
                
            except Exception as e:
                logging.error(f"Analytics failed: {transaction_id} - {str(e)}")
                raise


def create_mcp_server():
    """Create and configure the MCP server following ADK documentation"""
    enterprise_server = EnterpriseMCPServer()
    return enterprise_server.create_mcp_server()


def main(port: int = 8000, json_response: bool = False):
    """Main server function following ADK MCP patterns"""
    # Setup observability first (following orchestrator pattern)
    setup_observability("enterprise-mcp-server")
    logging.basicConfig(level=logging.INFO)
    
    app = create_mcp_server()
    
    # Create session manager with stateless mode for scalability
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,
        json_response=json_response,
        stateless=True,  # Important for Cloud Run scalability
    )
    
    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        await session_manager.handle_request(scope, receive, send)
    
    @asynccontextmanager
    async def lifespan(app: Starlette) -> None:
        """Manage session manager lifecycle"""
        async with session_manager.run():
            logging.info("Enterprise MCP Server started!")
            try:
                yield
            finally:
                logging.info("Enterprise MCP Server shutting down...")
    
    # Create ASGI application
    starlette_app = Starlette(
        debug=False,  # Set to False for production
        routes=[
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )
    
    import uvicorn
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
