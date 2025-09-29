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
    
    # Start service discovery
    await orchestrator.start_service_discovery()
    
    logging.info("Orchestrator Agent started successfully with service discovery")
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


@app.get("/patterns")
async def list_orchestration_patterns():
    """List available orchestration patterns"""
    return {
        "patterns": [
            {
                "name": "sequential",
                "description": "Step-by-step execution",
                "use_case": "When tasks must be completed in order"
            },
            {
                "name": "parallel", 
                "description": "Concurrent execution",
                "use_case": "When tasks can be executed simultaneously"
            },
            {
                "name": "loop",
                "description": "Iterative execution",
                "use_case": "When tasks need to be repeated until condition is met"
            },
            {
                "name": "simple",
                "description": "Single agent execution",
                "use_case": "When only one agent is needed"
            }
        ]
    }


@app.get("/override-options")
async def list_override_options():
    """List available user override options"""
    return {
        "override_options": {
            "orchestration_pattern": {
                "description": "Override automatic pattern selection",
                "options": ["sequential", "parallel", "loop", "simple"],
                "example": "{\"orchestration_pattern\": \"parallel\"}"
            },
            "agents": {
                "description": "Specify which agents to use",
                "options": "List of agent names from /agents endpoint",
                "example": "{\"agents\": [\"DataSearchAgent\", \"ReportingAgent\"]}"
            },
            "agent_sequence": {
                "description": "Specify order of agents for sequential execution",
                "options": "Ordered list of agent names",
                "example": "{\"agent_sequence\": [\"DataSearchAgent\", \"ReportingAgent\"]}"
            },
            "parallel_config": {
                "description": "Configuration for parallel execution",
                "options": {
                    "timeout": "Maximum execution time in seconds",
                    "fail_fast": "Stop on first failure (boolean)"
                },
                "example": "{\"parallel_config\": {\"timeout\": 30, \"fail_fast\": false}}"
            },
            "loop_config": {
                "description": "Configuration for loop execution",
                "options": {
                    "max_iterations": "Maximum number of iterations",
                    "condition": "Condition to check for completion"
                },
                "example": "{\"loop_config\": {\"max_iterations\": 5, \"condition\": \"accuracy > 0.9\"}}"
            }
        },
        "usage_examples": {
            "sequential_override": {
                "query": "Get data and generate report",
                "context": {
                    "orchestration_pattern": "sequential",
                    "agent_sequence": ["DataSearchAgent", "ReportingAgent"]
                }
            },
            "parallel_override": {
                "query": "Analyze data from multiple sources",
                "context": {
                    "orchestration_pattern": "parallel",
                    "agents": ["DataSearchAgent", "ReportingAgent", "ExampleAgent"],
                    "parallel_config": {"timeout": 30, "fail_fast": false}
                }
            },
            "loop_override": {
                "query": "Refine analysis iteratively",
                "context": {
                    "orchestration_pattern": "loop",
                    "agents": ["DataSearchAgent", "ReportingAgent"],
                    "loop_config": {"max_iterations": 5, "condition": "accuracy > 0.9"}
                }
            }
        }
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
