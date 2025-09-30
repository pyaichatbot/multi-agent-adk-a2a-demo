"""
Orchestrator Agent - Main FastAPI application
Enterprise-ready with AG-UI protocol and observability
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn

from agent import EnterpriseOrchestrator
from adk_shared.observability import get_tracer, setup_observability, trace_agent_call_simple
from adk_shared.security import authenticate_request
from agui_endpoints import create_agui_router
from adk_shared.agui_protocol import (
    AGUIProtocolServer,
    RedisAGUISessionManager,
    OrchestratorAGUIMessageHandler,
    OrchestratorAGUIStreamingHandler,
    WebSocketAGUIEventEmitter
)

# Pydantic models
class ProcessRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None

class ProcessResponse(BaseModel):
    success: bool
    result: Dict[str, Any]
    transaction_id: str

# Global variables
orchestrator = None
agui_server = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global orchestrator, agui_server
    
    # Startup
    setup_observability("orchestrator-agent")
    orchestrator = EnterpriseOrchestrator()
    
    # Start service discovery
    await orchestrator.start_service_discovery()
    
    # Initialize AG-UI components
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    session_manager = RedisAGUISessionManager(redis_url=redis_url)
    message_handler = OrchestratorAGUIMessageHandler(orchestrator)
    streaming_handler = OrchestratorAGUIStreamingHandler(orchestrator)
    event_emitter = WebSocketAGUIEventEmitter()
    
    # Create AG-UI server
    agui_server = AGUIProtocolServer(
        orchestrator,
        session_manager,
        message_handler,
        streaming_handler,
        event_emitter
    )
    
    # Create and include AG-UI router
    agui_router = create_agui_router(agui_server)
    app.include_router(agui_router)
    
    logging.info("Orchestrator Agent started successfully with service discovery and AG-UI protocol")
    yield
    
    # Shutdown
    if agui_server:
        await agui_server.session_manager.disconnect()
    logging.info("Orchestrator Agent shutting down")

# Create FastAPI app
app = FastAPI(
    title="Enterprise Orchestrator Agent",
    description="Central coordination agent with AG-UI protocol support",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "orchestrator-agent",
        "agents_available": len(orchestrator._agents) if orchestrator else 0
    }

@app.post("/process", response_model=ProcessResponse)
async def process_request_endpoint(request: ProcessRequest, token: str = Depends(authenticate_request)):
    """Process orchestration request with enterprise observability"""
    tracer = get_tracer("orchestrator-agent")
    
    with tracer.start_as_current_span("orchestration") as span:
        span.set_attribute("query", request.query)
        span.set_attribute("transaction_id", request.context.get("transaction_id", "unknown") if request.context else "unknown")
        
        try:
            if not orchestrator:
                raise HTTPException(status_code=503, detail="Orchestrator not ready")
            
            result = await orchestrator.process_request(request.query, request.context)
            
            return ProcessResponse(
                success=True,
                result=result,
                transaction_id=result.get("transaction_id", "unknown")
            )
            
        except Exception as e:
            span.record_exception(e)
            logging.error(f"Orchestration failed: {str(e)}")
            
            return ProcessResponse(
                success=False,
                result={"error": str(e)},
                transaction_id=request.context.get("transaction_id", "unknown") if request.context else "unknown"
            )

@app.get("/agents")
async def list_agents():
    """List available agents via service discovery"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not ready")
    
    return {
        "agents": list(orchestrator._agents.keys()),
        "count": len(orchestrator._agents)
    }

@app.get("/patterns")
async def list_patterns():
    """List available orchestration patterns"""
    return {
        "patterns": ["sequential", "parallel", "loop", "simple"],
        "descriptions": {
            "sequential": "Execute agents in sequence",
            "parallel": "Execute agents in parallel",
            "loop": "Execute agents in a loop",
            "simple": "Execute single agent"
        }
    }

@app.get("/override-options")
async def list_override_options():
    """List available user override options"""
    return {
        "overrides": {
            "orchestration_pattern": ["sequential", "parallel", "loop", "simple"],
            "agents": "List of agent names to use",
            "agent_sequence": "Order of agents for sequential execution",
            "parallel_config": "Configuration for parallel execution",
            "loop_config": "Configuration for loop execution"
        },
        "examples": {
            "pattern_override": {
                "orchestration_pattern": "parallel"
            },
            "agent_override": {
                "agents": ["data-search-agent", "reporting-agent"]
            },
            "combined_override": {
                "orchestration_pattern": "sequential",
                "agent_sequence": ["data-search-agent", "reporting-agent"]
            }
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
