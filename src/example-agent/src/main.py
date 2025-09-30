"""
FastAPI integration for custom agent with auto-registration
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn

from my_custom_agent import MyCustomAgent
from adk_shared.observability import setup_observability


# Pydantic models
class AnalyticsRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None
    analysis_type: Optional[str] = "general"


class AnalyticsResponse(BaseModel):
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    transaction_id: str
    processing_time_ms: int


# Global agent instance
custom_agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle with agent registration"""
    global custom_agent
    
    # Startup
    setup_observability("custom-analytics-agent")
    
    try:
        custom_agent = MyCustomAgent()
        
        # This automatically registers the agent and starts telemetry!
        await custom_agent.start_agent_lifecycle()
        
        logging.info("Custom Analytics Agent started and registered")
        
    except Exception as e:
        logging.error(f"Failed to start custom agent: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    if custom_agent:
        # Cleanup MCP connections following ADK documentation
        await custom_agent.cleanup()
        await custom_agent.stop_agent_lifecycle()
        logging.info("Custom Analytics Agent stopped and MCP connections cleaned up")


app = FastAPI(
    title="Custom Analytics Agent",
    description="Advanced analytics agent with auto-registration and telemetry",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check with agent status"""
    if not custom_agent:
        raise HTTPException(status_code=503, detail="Agent not ready")
    
    return {
        "status": "healthy",
        "service": "custom-analytics-agent",
        "agent_id": custom_agent.agent_id,
        "registered": custom_agent.is_registered,
        "current_load": custom_agent.current_requests,
        "max_capacity": custom_agent.max_concurrent_requests,
        "capabilities": [cap.name for cap in custom_agent.agent_capabilities]
    }


@app.post("/process_request", response_model=AnalyticsResponse)
async def process_request(request: AnalyticsRequest):
    """Process analytics request with full telemetry"""
    if not custom_agent:
        raise HTTPException(status_code=503, detail="Agent not ready")
    
    try:
        # This uses the enhanced telemetry from SelfRegisteringAgent
        result = await custom_agent.process_request_with_telemetry(
            request.query, 
            request.context
        )
        
        return AnalyticsResponse(
            success=True,
            result=result,
            transaction_id=result.get("transaction_id", "unknown"),
            processing_time_ms=result.get("processing_time_ms", 0)
        )
        
    except Exception as e:
        logging.error(f"Request processing failed: {str(e)}")
        
        return AnalyticsResponse(
            success=False,
            error=str(e),
            transaction_id="error",
            processing_time_ms=0
        )


@app.get("/capabilities")
async def get_capabilities():
    """Get agent capabilities"""
    if not custom_agent:
        raise HTTPException(status_code=503, detail="Agent not ready")
    
    return {
        "agent_name": custom_agent.name,
        "agent_id": custom_agent.agent_id,
        "version": custom_agent.version,
        "capabilities": [
            {
                "name": cap.name,
                "description": cap.description,
                "complexity_score": cap.complexity_score,
                "estimated_duration": cap.estimated_duration
            }
            for cap in custom_agent.agent_capabilities
        ],
        "tags": list(custom_agent.tags)
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
