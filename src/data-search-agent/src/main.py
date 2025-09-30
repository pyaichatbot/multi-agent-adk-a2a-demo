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
    return {
        "status": "healthy",
        "service": "data-search-agent",
        "capabilities": ["database queries", "document search", "data retrieval"]
    }


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
