# =============================================================================
# Complete Usage Examples - Agent Creation with Auto-Registration
# =============================================================================

# example-agent/my_custom_agent.py
"""
Example showing how to create a custom agent with auto-registration and telemetry
"""

import asyncio
import yaml
from typing import Dict, Any, List

from adk import Agent, FunctionTool
from adk_shared.agent_registration import SelfRegisteringAgent, AgentCapability
from adk_shared.observability import setup_observability


class CustomAnalyticsTool(FunctionTool):
    """Custom tool for the agent"""
    
    name = "run_custom_analytics"
    description = "Run custom analytics on business data"
    
    async def execute(self, data_source: str, analysis_type: str, **kwargs) -> Dict[str, Any]:
        """Execute custom analytics"""
        # Mock implementation
        return {
            "analysis_type": analysis_type,
            "data_source": data_source,
            "results": {"trend": "positive", "confidence": 0.87},
            "processing_time_ms": 1500
        }


class MyCustomAgent(SelfRegisteringAgent, Agent):
    """Example custom agent with auto-registration"""
    
    def __init__(self, config_path: str = "config/agent_config.yaml"):
        
        # Load configuration
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Initialize custom tools
        custom_tools = [CustomAnalyticsTool()]
        
        # Define specific capabilities (these will be auto-registered)
        agent_capabilities = [
            AgentCapability(
                name="custom_analytics",
                description="Advanced business analytics and trend analysis",
                input_schema={
                    "type": "object",
                    "properties": {
                        "data_source": {"type": "string"},
                        "analysis_type": {"type": "string"},
                        "parameters": {"type": "object"}
                    },
                    "required": ["data_source", "analysis_type"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "results": {"type": "object"},
                        "confidence": {"type": "number"},
                        "recommendations": {"type": "array"}
                    }
                },
                complexity_score=2.5,  # High complexity
                estimated_duration=6.0  # 6 seconds average
            ),
            AgentCapability(
                name=                "trend_forecasting",
                description="Predict future trends based on historical data",
                input_schema={
                    "type": "object",
                    "properties": {
                        "historical_data": {"type": "array"},
                        "forecast_period": {"type": "string"},
                        "confidence_level": {"type": "number"}
                    },
                    "required": ["historical_data", "forecast_period"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "forecast": {"type": "array"},
                        "accuracy": {"type": "number"},
                        "trend_direction": {"type": "string"}
                    }
                },
                complexity_score=3.0,  # Very high complexity
                estimated_duration=10.0  # 10 seconds average
            )
        ]
        
        # Initialize Agent
        Agent.__init__(
            self,
            name="CustomAnalyticsAgent",
            description="Advanced analytics agent with trend forecasting capabilities",
            tools=custom_tools,
            llm_config=config['llm']
        )
        
        # Initialize SelfRegisteringAgent with configuration
        SelfRegisteringAgent.__init__(
            self,
            registry_url=config.get('registry_url', 'redis://localhost:6379'),
            auto_register=config.get('auto_register', True),
            heartbeat_interval=config.get('heartbeat_interval', 30)
        )
        
        # Set agent-specific attributes for registration
        self.version = "1.0.0"
        self.agent_capabilities = agent_capabilities
        self.max_concurrent_requests = config.get('max_concurrent_requests', 8)
        self.tags = set(config.get('tags', ['analytics', 'forecasting', 'business']))
        self.priority = config.get('priority', 3)  # High priority
        
    async def process_request(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process analytics requests with enhanced capabilities"""
        
        # Use the inherited telemetry from SelfRegisteringAgent
        with self.tracer.start_as_current_span("custom_analytics_processing") as span:
            span.set_attribute("query_type", "custom_analytics")
            
            try:
                # Enhanced prompt for analytics
                analytics_prompt = f"""
                You are an advanced analytics agent. Process this request:
                
                Query: {query}
                Context: {context or {}}
                
                Available capabilities:
                1. Custom analytics on business data
                2. Trend forecasting with confidence intervals
                3. Data visualization recommendations
                
                Use the appropriate tools and provide detailed insights.
                """
                
                response = await self.chat(analytics_prompt)
                
                return {
                    "agent": "CustomAnalyticsAgent",
                    "capability_used": "custom_analytics",
                    "query": query,
                    "response": response,
                    "metadata": {
                        "analysis_depth": "comprehensive",
                        "confidence_level": 0.92,
                        "visualization_available": True
                    }
                }
                
            except Exception as e:
                span.record_exception(e)
                logging.error(f"Custom analytics processing failed: {str(e)}")
                raise


# =============================================================================
# Agent Configuration Files
# =============================================================================

# config/agent_config.yaml
AGENT_CONFIG_YAML = """
# Custom Agent Configuration
agent_name: "CustomAnalyticsAgent"
version: "1.0.0"

# LLM Configuration
llm:
  provider: "openai"
  model: "gpt-4"
  temperature: 0.1
  max_tokens: 2000

# Registry Configuration
registry_url: "redis://localhost:6379"
auto_register: true
heartbeat_interval: 30

# Agent Settings
max_concurrent_requests: 8
priority: 3
tags:
  - "analytics"
  - "forecasting" 
  - "business"
  - "custom"

# Observability
telemetry:
  tracing: true
  metrics: true
  log_level: "INFO"

# Service Configuration
service:
  host: "0.0.0.0"
  port: 8000
  workers: 1
"""

# =============================================================================
# FastAPI Integration for Custom Agent
# =============================================================================

# example-agent/main.py
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
        await custom_agent.stop_agent_lifecycle()
    logging.info("Custom Analytics Agent stopped")


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


# =============================================================================
# Docker Configuration for Custom Agent
# =============================================================================

# example-agent/Dockerfile
DOCKERFILE_CUSTOM_AGENT = '''
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared libraries
COPY ../adk-shared ./adk-shared

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD curl -f http://localhost:$PORT/health || exit 1

EXPOSE $PORT

CMD ["python", "main.py"]
'''

# =============================================================================
# Complete Deployment Script
# =============================================================================

# deploy-enhanced-system.sh
DEPLOY_SCRIPT = '''
#!/bin/bash
# Enhanced deployment script with dynamic agent registration

set -e

PROJECT_ID="your-gcp-project-id"
REGION="us-central1"
REDIS_URL="redis://redis-instance:6379"

echo "🚀 Deploying Enhanced Enterprise Multi-Agent System..."

# Deploy Redis instance for agent registry
echo "📦 Deploying Redis for Agent Registry..."
gcloud redis instances create agent-registry \\
  --size=1 \\
  --region=$REGION \\
  --redis-version=redis_6_x \\
  --project=$PROJECT_ID

# Get Redis connection details
REDIS_IP=$(gcloud redis instances describe agent-registry --region=$REGION --format="value(host)")
REDIS_URL="redis://$REDIS_IP:6379"

# Deploy MCP Server
echo "🔧 Deploying MCP Server..."
gcloud run deploy mcp-server \\
  --source ./mcp-server \\
  --region $REGION \\
  --project $PROJECT_ID \\
  --platform managed \\
  --allow-unauthenticated \\
  --memory 1Gi \\
  --cpu 1 \\
  --set-env-vars ENVIRONMENT=production \\
  --set-env-vars REDIS_URL=$REDIS_URL

MCP_URL=$(gcloud run services describe mcp-server --region=$REGION --format='value(status.url)')

# Deploy Enhanced Orchestrator
echo "🎯 Deploying Enhanced Orchestrator..."
gcloud run deploy enhanced-orchestrator \\
  --source ./orchestrator-agent \\
  --region $REGION \\
  --project $PROJECT_ID \\
  --platform managed \\
  --allow-unauthenticated \\
  --memory 2Gi \\
  --cpu 1 \\
  --concurrency 50 \\
  --max-instances 10 \\
  --set-env-vars ENVIRONMENT=production \\
  --set-env-vars AGENT_REGISTRY_URL=$REDIS_URL \\
  --set-env-vars MCP_SERVER_URL=$MCP_URL

ORCHESTRATOR_URL=$(gcloud run services describe enhanced-orchestrator --region=$REGION --format='value(status.url)')

# Deploy Enhanced Data Search Agent (auto-registers)
echo "🔍 Deploying Enhanced Data Search Agent..."
DATA_AGENT_URL="https://enhanced-data-search-agent-${PROJECT_ID//_/-}-${REGION}.a.run.app"

gcloud run deploy enhanced-data-search-agent \\
  --source ./data-search-agent \\
  --region $REGION \\
  --project $PROJECT_ID \\
  --platform managed \\
  --allow-unauthenticated \\
  --memory 1Gi \\
  --cpu 1 \\
  --set-env-vars ENVIRONMENT=production \\
  --set-env-vars AGENT_REGISTRY_URL=$REDIS_URL \\
  --set-env-vars MCP_SERVER_URL=$MCP_URL \\
  --set-env-vars SERVICE_URL=$DATA_AGENT_URL \\
  --set-env-vars AUTO_REGISTER=true

# Deploy Enhanced Reporting Agent (auto-registers)  
echo "📊 Deploying Enhanced Reporting Agent..."
REPORTING_AGENT_URL="https://enhanced-reporting-agent-${PROJECT_ID//_/-}-${REGION}.a.run.app"

gcloud run deploy enhanced-reporting-agent \\
  --source ./reporting-agent \\
  --region $REGION \\
  --project $PROJECT_ID \\
  --platform managed \\
  --allow-unauthenticated \\
  --memory 1Gi \\
  --cpu 1 \\
  --set-env-vars ENVIRONMENT=production \\
  --set-env-vars AGENT_REGISTRY_URL=$REDIS_URL \\
  --set-env-vars MCP_SERVER_URL=$MCP_URL \\
  --set-env-vars SERVICE_URL=$REPORTING_AGENT_URL \\
  --set-env-vars AUTO_REGISTER=true

# Deploy Custom Analytics Agent (auto-registers)
echo "📈 Deploying Custom Analytics Agent..."
CUSTOM_AGENT_URL="https://custom-analytics-agent-${PROJECT_ID//_/-}-${REGION}.a.run.app"

gcloud run deploy custom-analytics-agent \\
  --source ./example-agent \\
  --region $REGION \\
  --project $PROJECT_ID \\
  --platform managed \\
  --allow-unauthenticated \\
  --memory 1Gi \\
  --cpu 1 \\
  --set-env-vars ENVIRONMENT=production \\
  --set-env-vars AGENT_REGISTRY_URL=$REDIS_URL \\
  --set-env-vars SERVICE_URL=$CUSTOM_AGENT_URL \\
  --set-env-vars AUTO_REGISTER=true

echo "✅ Deployment Complete!"
echo ""
echo "🔗 Service URLs:"
echo "   MCP Server:           $MCP_URL"
echo "   Enhanced Orchestrator: $ORCHESTRATOR_URL"
echo "   Data Search Agent:    $DATA_AGENT_URL"
echo "   Reporting Agent:      $REPORTING_AGENT_URL"
echo "   Custom Analytics:     $CUSTOM_AGENT_URL"
echo ""
echo "🧪 Test the system:"
echo "curl -X POST '$ORCHESTRATOR_URL/process' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"query\": \"Analyze sales trends for Q1\"}'"
echo ""
echo "📊 View agents:"
echo "curl '$ORCHESTRATOR_URL/agents'"
echo ""
echo "📈 View metrics:"
echo "curl '$ORCHESTRATOR_URL/metrics'"
'''

# =============================================================================
# Testing and Validation Script
# =============================================================================

# test-system.py
"""
Comprehensive testing script for the enhanced system
"""

import asyncio
import aiohttp
import json
import time
from typing import List, Dict, Any


class SystemTester:
    """Test the complete enhanced system"""
    
    def __init__(self, orchestrator_url: str):
        self.orchestrator_url = orchestrator_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_health_checks(self) -> Dict[str, Any]:
        """Test health endpoints"""
        print("🏥 Testing health checks...")
        
        try:
            async with self.session.get(f"{self.orchestrator_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ Orchestrator healthy: {health_data['agents_healthy']} agents available")
                    return health_data
                else:
                    print(f"❌ Orchestrator health check failed: {response.status}")
                    return None
        except Exception as e:
            print(f"❌ Health check error: {str(e)}")
            return None
    
    async def test_agent_discovery(self) -> List[Dict[str, Any]]:
        """Test agent discovery"""
        print("🔍 Testing agent discovery...")
        
        try:
            async with self.session.get(f"{self.orchestrator_url}/agents") as response:
                if response.status == 200:
                    agents_data = await response.json()
                    agents = agents_data['agents']
                    
                    print(f"✅ Found {len(agents)} registered agents:")
                    for agent in agents:
                        print(f"   • {agent['name']} ({agent['status']}) - {len(agent['capabilities'])} capabilities")
                    
                    return agents
                else:
                    print(f"❌ Agent discovery failed: {response.status}")
                    return []
        except Exception as e:
            print(f"❌ Agent discovery error: {str(e)}")
            return []
    
    async def test_capability_routing(self) -> Dict[str, Any]:
        """Test capability-based routing"""
        print("🎯 Testing capability-based routing...")
        
        test_queries = [
            {
                "query": "Search for customer data in the database",
                "expected_capability": "data_search"
            },
            {
                "query": "Generate a quarterly sales report",
                "expected_capability": "reporting"
            },
            {
                "query": "Analyze market trends and forecast revenue",
                "expected_capability": "custom_analytics"
            }
        ]
        
        results = []
        
        for test_case in test_queries:
            try:
                print(f"   Testing: {test_case['query']}")
                
                request_data = {
                    "query": test_case["query"],
                    "context": {"test_mode": True}
                }
                
                start_time = time.time()
                async with self.session.post(
                    f"{self.orchestrator_url}/process",
                    json=request_data
                ) as response:
                    
                    processing_time = int((time.time() - start_time) * 1000)
                    
                    if response.status == 200:
                        result = await response.json()
                        selected_agent = result['selected_agent']['name']
                        
                        print(f"   ✅ Routed to: {selected_agent} (in {processing_time}ms)")
                        
                        results.append({
                            "query": test_case["query"],
                            "selected_agent": selected_agent,
                            "processing_time_ms": processing_time,
                            "success": True
                        })
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Routing failed: {response.status} - {error_text}")
                        
                        results.append({
                            "query": test_case["query"],
                            "error": error_text,
                            "success": False
                        })
                        
            except Exception as e:
                print(f"   ❌ Routing error: {str(e)}")
                results.append({
                    "query": test_case["query"],
                    "error": str(e),
                    "success": False
                })
        
        return results
    
    async def test_load_balancing(self) -> Dict[str, Any]:
        """Test load balancing across agents"""
        print("⚖️  Testing load balancing...")
        
        # Send multiple concurrent requests
        tasks = []
        for i in range(10):
            task = self.session.post(
                f"{self.orchestrator_url}/process",
                json={"query": f"Search for data item {i}", "context": {"batch_test": True}}
            )
            tasks.append(task)
        
        try:
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful_requests = 0
            agent_usage = {}
            
            for response in responses:
                if isinstance(response, Exception):
                    continue
                    
                if response.status == 200:
                    result = await response.json()
                    successful_requests += 1
                    
                    agent_name = result['selected_agent']['name']
                    agent_usage[agent_name] = agent_usage.get(agent_name, 0) + 1
            
            print(f"   ✅ {successful_requests}/10 requests successful")
            print(f"   Load distribution: {agent_usage}")
            
            return {
                "total_requests": 10,
                "successful_requests": successful_requests,
                "agent_distribution": agent_usage
            }
            
        except Exception as e:
            print(f"   ❌ Load balancing test error: {str(e)}")
            return {"error": str(e)}
    
    async def test_metrics_endpoint(self) -> Dict[str, Any]:
        """Test metrics collection"""
        print("📊 Testing metrics collection...")
        
        try:
            async with self.session.get(f"{self.orchestrator_url}/metrics") as response:
                if response.status == 200:
                    metrics = await response.json()
                    
                    print(f"   ✅ System utilization: {metrics['utilization_percent']}%")
                    print(f"   Agent status: {metrics['healthy_agents']} healthy, {metrics['degraded_agents']} degraded")
                    
                    return metrics
                else:
                    print(f"   ❌ Metrics collection failed: {response.status}")
                    return None
        except Exception as e:
            print(f"   ❌ Metrics error: {str(e)}")
            return None
    
    async def run_complete_test(self) -> Dict[str, Any]:
        """Run complete system test"""
        print("🧪 Running Complete System Test")
        print("=" * 50)
        
        test_results = {
            "timestamp": time.time(),
            "tests": {}
        }
        
        # Health checks
        health_result = await self.test_health_checks()
        test_results["tests"]["health_check"] = health_result
        
        # Agent discovery
        agents_result = await self.test_agent_discovery()
        test_results["tests"]["agent_discovery"] = {
            "agents_found": len(agents_result),
            "agents": agents_result
        }
        
        # Capability routing
        routing_result = await self.test_capability_routing()
        test_results["tests"]["capability_routing"] = routing_result
        
        # Load balancing
        load_balancing_result = await self.test_load_balancing()
        test_results["tests"]["load_balancing"] = load_balancing_result
        
        # Metrics
        metrics_result = await self.test_metrics_endpoint()
        test_results["tests"]["metrics"] = metrics_result
        
        print("\n" + "=" * 50)
        print("🏁 Test Complete!")
        
        # Summary
        total_tests = len([t for t in test_results["tests"].values() if t is not None])
        successful_tests = len([
            t for t in test_results["tests"].values() 
            if t is not None and not isinstance(t, dict) or not t.get("error")
        ])
        
        print(f"📋 Summary: {successful_tests}/{total_tests} test categories passed")
        
        return test_results


async def main():
    """Main testing function"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python test-system.py <orchestrator-url>")
        sys.exit(1)
    
    orchestrator_url = sys.argv[1]
    
    async with SystemTester(orchestrator_url) as tester:
        results = await tester.run_complete_test()
        
        # Save results
        with open("test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to test_results.json")


if __name__ == "__main__":
    asyncio.run(main())


print("\n" + "="*80)
print("🎉 COMPLETE ENTERPRISE SYSTEM IMPLEMENTATION!")
print("="*80)

final_summary = """
✅ FULLY INTEGRATED SYSTEM:

🔄 Agent Auto-Registration:
   • Agents inherit from SelfRegisteringAgent mixin
   • Automatic capability extraction from tools and config
   • Self-registration on startup with Redis registry
   • Continuous health monitoring and heartbeat

📊 Complete Telemetry Integration:
   • OpenTelemetry spans for all operations
   • Metrics for registration, requests, load balancing
   • Distributed tracing across entire system
   • Real-time performance monitoring

🚀 Production Ready Features:
   • Dynamic agent discovery and routing
   • Health-based load balancing with failover
   • Policy enforcement with audit trails
   • Comprehensive error handling and retries
   • Auto-scaling with Cloud Run

📝 Usage Example:
   1. Create agent: MyAgent(SelfRegisteringAgent, Agent)
   2. Deploy: gcloud run deploy --set-env-vars AUTO_REGISTER=true
   3. Agent automatically registers capabilities
   4. Orchestrator discovers and routes to agent
   5. Full telemetry and monitoring active

🧪 Testing:
   • Health check validation
   • Agent discovery verification
   • Capability-based routing tests  
   • Load balancing distribution
   • End-to-end performance metrics

🔧 Deployment:
   • Single script deploys entire system
   • Agents auto-register on startup
   • Redis registry for service discovery
   • Cloud Run with auto-scaling
   • Complete observability stack
"""

print(final_summary)
print("="*80)
                        