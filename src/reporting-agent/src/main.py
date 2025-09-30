"""
Complete FastAPI implementation for Reporting Agent
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn

from agent import ReportingAgent
from adk_shared.observability import setup_observability


# Pydantic models
class ReportRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None


class ReportResponse(BaseModel):
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    transaction_id: str


# Global variables
reporting_agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle with auto-registration"""
    global reporting_agent
    
    # Startup
    setup_observability("reporting-agent")
    reporting_agent = ReportingAgent()
    
    # Start agent lifecycle with auto-registration
    await reporting_agent.start_agent_lifecycle()
    
    logging.info("Reporting Agent started successfully with auto-registration")
    yield
    
    # Shutdown
    await reporting_agent.stop_agent_lifecycle()
    logging.info("Reporting Agent shutting down")


app = FastAPI(
    title="Reporting Agent",
    description="Specialized agent for business reporting and analytics",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "reporting-agent",
        "capabilities": ["report generation", "analytics", "business insights"]
    }


@app.post("/process_request", response_model=ReportResponse)
async def process_request(request: ReportRequest):
    """Process reporting request"""
    try:
        if not reporting_agent:
            raise HTTPException(status_code=503, detail="Agent not ready")
        
        result = await reporting_agent.process_request(request.query, request.context)
        
        return ReportResponse(
            success=True,
            result=result,
            transaction_id=result.get("transaction_id", "unknown")
        )
        
    except Exception as e:
        logging.error(f"Reporting failed: {str(e)}")
        
        return ReportResponse(
            success=False,
            error=str(e),
            transaction_id="error"
        )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
