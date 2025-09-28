"""
Complete FastAPI implementation for MCP Server
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uvicorn

from server import EnterpriseToolServer
from adk_shared.observability import get_tracer, setup_observability
from adk_shared.security import authenticate_request


# Pydantic models
class ToolRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    auth_token: Optional[str] = None


class ToolResponse(BaseModel):
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    transaction_id: str


# Global variables
tool_server = None
security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global tool_server
    
    # Startup
    setup_observability("mcp-server")
    tool_server = EnterpriseToolServer()
    
    logging.info("MCP Server started successfully")
    yield
    
    # Shutdown
    logging.info("MCP Server shutting down")


app = FastAPI(
    title="Enterprise MCP Tool Server",
    description="Centralized tool registry for enterprise multi-agent system",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    if not authenticate_request(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return credentials.credentials


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "mcp-server",
        "tools_available": len(tool_server.tools) if tool_server else 0
    }


@app.get("/tools")
async def list_tools(token: str = Depends(verify_token)):
    """List available tools"""
    if not tool_server:
        raise HTTPException(status_code=503, detail="Server not ready")
    
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in tool_server.tools.values()
        ]
    }


@app.post("/execute", response_model=ToolResponse)
async def execute_tool(
    request: ToolRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """Execute a tool"""
    tracer = get_tracer("mcp-server")
    
    with tracer.start_as_current_span("tool_execution") as span:
        span.set_attribute("tool_name", request.tool_name)
        
        try:
            if not tool_server:
                raise HTTPException(status_code=503, detail="Server not ready")
            
            if request.tool_name not in tool_server.tools:
                raise HTTPException(status_code=404, detail=f"Tool '{request.tool_name}' not found")
            
            tool = tool_server.tools[request.tool_name]
            result = await tool.execute(**request.parameters, auth_token=token)
            
            return ToolResponse(
                success=True,
                result=result,
                transaction_id=result.get("transaction_id", "unknown")
            )
            
        except Exception as e:
            span.record_exception(e)
            logging.error(f"Tool execution failed: {str(e)}")
            
            return ToolResponse(
                success=False,
                error=str(e),
                transaction_id="error"
            )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
