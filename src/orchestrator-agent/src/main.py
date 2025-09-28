"""
Complete FastAPI implementation for Orchestrator Agent
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn

from agent import EnterpriseOrchestrator
from adk_shared.observability import get_tracer, setup_observability
from adk_shared.security import authenticate_request


# Pydantic models
class ProcessRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None


class ProcessResponse(BaseModel):
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    transaction_id: str


# Global variables
orchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global orchestrator
    
    # Startup
    setup_observability("orchestrator-agent")
    orchestrator = EnterpriseOrchestrator()
    
    logging.info("Orchestrator Agent started successfully")
    yield
    
    # Shutdown
    logging.info("Orchestrator Agent shutting down")


app = FastAPI(
    title="Enterprise Orchestrator Agent",
    description="Central orchestration agent for enterprise multi-agent system",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "orchestrator-agent",
        "agents_available": len(orchestrator.agents) if orchestrator else 0
    }


@app.post("/process", response_model=ProcessResponse)
async def process_request(request: ProcessRequest):
    """Process user request through orchestration"""
    tracer = get_tracer("orchestrator-agent")
    
    with tracer.start_as_current_span("orchestration") as span:
        span.set_attribute("query", request.query)
        
        try:
            if not orchestrator:
                raise HTTPException(status_code=503, detail="Orchestrator not ready")
            
            result = await orchestrator.route_request(request.query, request.context)
            
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
                error=str(e),
                transaction_id="error"
            )


@app.get("/agents")
async def list_agents():
    """List available agents"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not ready")
    
    return {
        "agents": [
            {
                "name": name,
                "capabilities": client.capabilities
            }
            for name, client in orchestrator.agents.items()
        ]
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
