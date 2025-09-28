"""
ADK Dev UI Integration for Enterprise System
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

from adk_shared.agent_registry import RedisAgentRegistry, AgentMetadata
from adk_shared.enterprise_evals import EnterpriseEvaluator, ContinuousEvalManager
from adk_shared.observability import get_tracer, get_meter


class EnterpriseDevUIPlugin:
    """Plugin to extend ADK Dev UI with enterprise features"""
    
    def __init__(self, registry: RedisAgentRegistry, eval_manager: ContinuousEvalManager):
        self.registry = registry
        self.eval_manager = eval_manager
        self.tracer = get_tracer("enterprise-dev-ui")
        self.meter = get_meter("enterprise-dev-ui")
        
        # Metrics
        self.ui_requests_counter = self.meter.create_counter(
            name="dev_ui_requests_total",
            description="Total Dev UI requests"
        )
    
    def register_routes(self, app: FastAPI):
        """Register enterprise-specific routes with Dev UI"""
        
        @app.get("/enterprise/agents")
        async def get_enterprise_agents():
            """Get all registered agents with enterprise metadata"""
            try:
                agents = await self.registry.list_agents()
                
                agent_data = []
                for agent in agents:
                    agent_data.append({
                        "id": agent.agent_id,
                        "name": agent.name,
                        "version": agent.version,
                        "status": agent.status.value,
                        "capabilities": [
                            {
                                "name": cap.name,
                                "description": cap.description,
                                "complexity_score": cap.complexity_score,
                                "estimated_duration": cap.estimated_duration
                            }
                            for cap in agent.capabilities
                        ],
                        "endpoint_url": agent.endpoint_url,
                        "health_check_url": agent.health_check_url,
                        "current_load": agent.current_load,
                        "max_concurrent_requests": agent.max_concurrent_requests,
                        "tags": list(agent.tags),
                        "registered_at": agent.registered_at.isoformat(),
                        "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else None
                    })
                
                self.ui_requests_counter.add(1, {"endpoint": "enterprise_agents"})
                return {"agents": agent_data}
                
            except Exception as e:
                logging.error(f"Failed to get enterprise agents: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/enterprise/agents/{agent_id}")
        async def get_agent_details(agent_id: str):
            """Get detailed information about a specific agent"""
            try:
                agent = await self.registry.get_agent(agent_id)
                if not agent:
                    raise HTTPException(status_code=404, detail="Agent not found")
                
                return {
                    "id": agent.agent_id,
                    "name": agent.name,
                    "version": agent.version,
                    "description": agent.description,
                    "status": agent.status.value,
                    "capabilities": [
                        {
                            "name": cap.name,
                            "description": cap.description,
                            "input_schema": cap.input_schema,
                            "output_schema": cap.output_schema,
                            "complexity_score": cap.complexity_score,
                            "estimated_duration": cap.estimated_duration
                        }
                        for cap in agent.capabilities
                    ],
                    "endpoint_url": agent.endpoint_url,
                    "health_check_url": agent.health_check_url,
                    "current_load": agent.current_load,
                    "max_concurrent_requests": agent.max_concurrent_requests,
                    "cpu_cores": agent.cpu_cores,
                    "memory_gb": agent.memory_gb,
                    "service_name": agent.service_name,
                    "namespace": agent.namespace,
                    "cluster": agent.cluster,
                    "tags": list(agent.tags),
                    "priority": agent.priority,
                    "registered_at": agent.registered_at.isoformat(),
                    "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else None
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logging.error(f"Failed to get agent details: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/enterprise/evaluations")
        async def get_evaluations():
            """Get all scheduled evaluations"""
            try:
                evaluations = []
                for eval_id, eval_info in self.eval_manager.scheduled_evals.items():
                    evaluations.append({
                        "eval_id": eval_id,
                        "name": eval_info["config"].name,
                        "description": eval_info["config"].description,
                        "status": eval_info["status"].value,
                        "next_run": eval_info["next_run"].isoformat(),
                        "agent_targets": eval_info["config"].agent_targets,
                        "eval_frequency": eval_info["config"].eval_frequency,
                        "success_criteria": eval_info["config"].success_criteria,
                        "alerts_enabled": eval_info["config"].alerts_enabled
                    })
                
                self.ui_requests_counter.add(1, {"endpoint": "evaluations"})
                return {"evaluations": evaluations}
                
            except Exception as e:
                logging.error(f"Failed to get evaluations: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/enterprise/metrics")
        async def get_enterprise_metrics():
            """Get enterprise system metrics"""
            try:
                # Get agent metrics
                agents = await self.registry.list_agents()
                healthy_agents = len([a for a in agents if a.status.value == "healthy"])
                degraded_agents = len([a for a in agents if a.status.value == "degraded"])
                unhealthy_agents = len([a for a in agents if a.status.value == "unhealthy"])
                
                # Calculate system utilization
                total_capacity = sum(a.max_concurrent_requests for a in agents)
                current_load = sum(a.current_load for a in agents)
                utilization_percent = (current_load / total_capacity * 100) if total_capacity > 0 else 0
                
                # Get evaluation metrics
                total_evals = len(self.eval_manager.scheduled_evals)
                running_evals = len([e for e in self.eval_manager.scheduled_evals.values() 
                                   if e["status"].value == "running"])
                
                metrics = {
                    "system_health": {
                        "total_agents": len(agents),
                        "healthy_agents": healthy_agents,
                        "degraded_agents": degraded_agents,
                        "unhealthy_agents": unhealthy_agents,
                        "utilization_percent": round(utilization_percent, 2)
                    },
                    "evaluations": {
                        "total_scheduled": total_evals,
                        "currently_running": running_evals
                    },
                    "performance": {
                        "avg_response_time_ms": 150,  # Mock data
                        "requests_per_second": 25,    # Mock data
                        "error_rate_percent": 2.1     # Mock data
                    }
                }
                
                self.ui_requests_counter.add(1, {"endpoint": "metrics"})
                return metrics
                
            except Exception as e:
                logging.error(f"Failed to get enterprise metrics: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/enterprise/dashboard")
        async def get_dashboard_data():
            """Get comprehensive dashboard data"""
            try:
                # Get all data in parallel
                agents_task = self.registry.list_agents()
                evaluations_task = asyncio.create_task(self._get_evaluations_data())
                metrics_task = asyncio.create_task(self._get_metrics_data())
                
                agents = await agents_task
                evaluations = await evaluations_task
                metrics = await metrics_task
                
                dashboard_data = {
                    "agents": [
                        {
                            "id": agent.agent_id,
                            "name": agent.name,
                            "status": agent.status.value,
                            "capabilities_count": len(agent.capabilities),
                            "current_load": agent.current_load,
                            "max_capacity": agent.max_concurrent_requests
                        }
                        for agent in agents
                    ],
                    "evaluations": evaluations,
                    "metrics": metrics,
                    "timestamp": asyncio.get_event_loop().time()
                }
                
                self.ui_requests_counter.add(1, {"endpoint": "dashboard"})
                return dashboard_data
                
            except Exception as e:
                logging.error(f"Failed to get dashboard data: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _get_evaluations_data(self) -> List[Dict[str, Any]]:
        """Get evaluations data"""
        evaluations = []
        for eval_id, eval_info in self.eval_manager.scheduled_evals.items():
            evaluations.append({
                "eval_id": eval_id,
                "name": eval_info["config"].name,
                "status": eval_info["status"].value,
                "next_run": eval_info["next_run"].isoformat()
            })
        return evaluations
    
    async def _get_metrics_data(self) -> Dict[str, Any]:
        """Get metrics data"""
        return {
            "system_utilization": 75.5,
            "active_evaluations": 3,
            "total_requests_today": 1250,
            "error_rate": 1.2
        }


class EnterpriseDevUIManager:
    """Manages the enterprise Dev UI integration"""
    
    def __init__(self, registry: RedisAgentRegistry, eval_manager: ContinuousEvalManager):
        self.registry = registry
        self.eval_manager = eval_manager
        self.plugin = EnterpriseDevUIPlugin(registry, eval_manager)
        self.tracer = get_tracer("enterprise-dev-ui-manager")
    
    def setup_enterprise_dev_ui(self, app: FastAPI):
        """Setup enterprise features for Dev UI"""
        with self.tracer.start_as_current_span("setup_enterprise_dev_ui"):
            # Register enterprise routes
            self.plugin.register_routes(app)
            
            # Add enterprise dashboard widget
            self._add_dashboard_widget(app)
            
            # Setup background tasks
            self._setup_background_tasks(app)
            
            logging.info("Enterprise Dev UI features registered")
    
    def _add_dashboard_widget(self, app: FastAPI):
        """Add enterprise dashboard widget"""
        
        @app.get("/enterprise/widgets/agent-registry", response_class=HTMLResponse)
        async def agent_registry_widget():
            """Agent registry status widget"""
            try:
                agents = await self.registry.list_agents()
                
                widget_html = f"""
                <div class="enterprise-widget">
                    <h3>Agent Registry Status</h3>
                    <div class="agent-stats">
                        <div class="stat">
                            <span class="label">Total Agents:</span>
                            <span class="value">{len(agents)}</span>
                        </div>
                        <div class="stat">
                            <span class="label">Healthy:</span>
                            <span class="value healthy">{len([a for a in agents if a.status.value == 'healthy'])}</span>
                        </div>
                        <div class="stat">
                            <span class="label">Degraded:</span>
                            <span class="value degraded">{len([a for a in agents if a.status.value == 'degraded'])}</span>
                        </div>
                    </div>
                </div>
                """
                
                return widget_html
                
            except Exception as e:
                return f"<div class='error'>Failed to load agent registry: {str(e)}</div>"
        
        @app.get("/enterprise/widgets/evaluation-status", response_class=HTMLResponse)
        async def evaluation_status_widget():
            """Evaluation status widget"""
            try:
                total_evals = len(self.eval_manager.scheduled_evals)
                running_evals = len([e for e in self.eval_manager.scheduled_evals.values() 
                                   if e["status"].value == "running"])
                
                widget_html = f"""
                <div class="enterprise-widget">
                    <h3>Evaluation Status</h3>
                    <div class="eval-stats">
                        <div class="stat">
                            <span class="label">Scheduled:</span>
                            <span class="value">{total_evals}</span>
                        </div>
                        <div class="stat">
                            <span class="label">Running:</span>
                            <span class="value running">{running_evals}</span>
                        </div>
                    </div>
                </div>
                """
                
                return widget_html
                
            except Exception as e:
                return f"<div class='error'>Failed to load evaluation status: {str(e)}</div>"
    
    def _setup_background_tasks(self, app: FastAPI):
        """Setup background tasks for enterprise features"""
        
        @app.on_event("startup")
        async def start_enterprise_background_tasks():
            """Start enterprise background tasks"""
            asyncio.create_task(self._run_continuous_evaluations())
            asyncio.create_task(self._monitor_agent_health())
        
        @app.on_event("shutdown")
        async def stop_enterprise_background_tasks():
            """Stop enterprise background tasks"""
            # Cancel background tasks
            pass
    
    async def _run_continuous_evaluations(self):
        """Run continuous evaluations in background"""
        while True:
            try:
                await self.eval_manager.run_scheduled_evals()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logging.error(f"Continuous evaluation error: {str(e)}")
                await asyncio.sleep(60)
    
    async def _monitor_agent_health(self):
        """Monitor agent health in background"""
        while True:
            try:
                # Update agent health status
                agents = await self.registry.list_agents()
                for agent in agents:
                    # Check agent health (mock implementation)
                    health_status = await self._check_agent_health(agent)
                    await self.registry.update_agent_status(
                        agent.agent_id, 
                        health_status["status"], 
                        health_status["load"]
                    )
                
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logging.error(f"Agent health monitoring error: {str(e)}")
                await asyncio.sleep(30)
    
    async def _check_agent_health(self, agent: AgentMetadata) -> Dict[str, Any]:
        """Check agent health status"""
        # Mock health check implementation
        import random
        
        # Simulate health check
        is_healthy = random.random() > 0.1  # 90% chance of being healthy
        load = random.randint(0, agent.max_concurrent_requests)
        
        if is_healthy:
            status = "healthy" if load < agent.max_concurrent_requests * 0.8 else "degraded"
        else:
            status = "unhealthy"
        
        return {
            "status": status,
            "load": load
        }
