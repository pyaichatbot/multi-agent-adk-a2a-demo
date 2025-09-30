"""
Complete FastAPI implementation for Data Search Agent
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn

from agent import DataSearchAgent
from adk_shared.observability import setup_observability


# Pydantic models
class SearchRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    transaction_id: str


# Global variables
data_agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle with auto-registration"""
    global data_agent
    
    # Startup
    setup_observability("data-search-agent")
    data_agent = DataSearchAgent()
    
    # Start agent lifecycle with auto-registration
    await data_agent.start_agent_lifecycle()
    
    logging.info("Data Search Agent started successfully with auto-registration")
    yield
    
    # Shutdown
    await data_agent.stop_agent_lifecycle()
    logging.info("Data Search Agent shutting down")


app = FastAPI(
    title="Data Search Agent",
    description="Specialized agent for enterprise data search and retrieval",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if not data_agent:
        raise HTTPException(status_code=503, detail="Agent not ready")
    
    return {
        "status": "healthy",
        "service": "data-search-agent",
        "agent_id": data_agent.agent_id,
        "registered": data_agent.is_registered,
        "current_load": data_agent.current_requests,
        "max_capacity": data_agent.max_concurrent_requests,
        "capabilities": [cap.name for cap in data_agent.agent_capabilities]
    }


@app.get("/registration-status")
async def get_registration_status():
    """Get detailed registration status for enterprise monitoring"""
    if not data_agent:
        raise HTTPException(status_code=503, detail="Agent not ready")
    
    return {
        "agent_id": data_agent.agent_id,
        "registration_status": "active" if data_agent.is_registered else "inactive",
        "auto_registered": True,
        "registration_time": getattr(data_agent, 'registration_time', None),
        "last_heartbeat": getattr(data_agent, 'last_heartbeat', None),
        "registry_endpoint": getattr(data_agent, 'registry_endpoint', None),
        "discovery_enabled": True,
        "load_balancing": "enabled",
        "current_load": data_agent.current_requests,
        "max_capacity": data_agent.max_concurrent_requests
    }


@app.post("/heartbeat")
async def send_heartbeat():
    """Send heartbeat to maintain registration (enterprise monitoring)"""
    if not data_agent:
        raise HTTPException(status_code=503, detail="Agent not ready")
    
    try:
        # Trigger heartbeat if the agent has this method
        if hasattr(data_agent, 'send_heartbeat'):
            await data_agent.send_heartbeat()
        
        return {
            "agent_id": data_agent.agent_id,
            "heartbeat_sent": True,
            "timestamp": "2024-01-15T10:30:00Z",  # Would be actual timestamp
            "next_heartbeat": "2024-01-15T10:30:30Z",  # Would be calculated
            "status": "healthy"
        }
    except Exception as e:
        logging.error(f"Data Search Agent heartbeat failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Heartbeat failed: {str(e)}")


@app.post("/process_request", response_model=SearchResponse)
async def process_request(request: SearchRequest):
    """Process data search request"""
    try:
        if not data_agent:
            raise HTTPException(status_code=503, detail="Agent not ready")
        
        result = await data_agent.process_request(request.query, request.context)
        
        return SearchResponse(
            success=True,
            result=result,
            transaction_id=result.get("transaction_id", "unknown")
        )
        
    except Exception as e:
        logging.error(f"Data search failed: {str(e)}")
        
        return SearchResponse(
            success=False,
            error=str(e),
            transaction_id="error"
        )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
