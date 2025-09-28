"""
Enterprise evaluation framework integrating ADK Evals with telemetry
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

from adk.evals import EvalSuite, EvalResult, EvalMetric, Evaluator
from adk.evals.metrics import AccuracyMetric, LatencyMetric, ThroughputMetric
from adk_shared.observability import get_tracer, get_meter
from adk_shared.agent_registry import RedisAgentRegistry, AgentMetadata


class EvalStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed" 
    FAILED = "failed"
    SCHEDULED = "scheduled"


@dataclass
class EnterpriseEvalConfig:
    """Configuration for enterprise evaluations"""
    eval_id: str
    name: str
    description: str
    agent_targets: List[str]  # Agent IDs or "all"
    eval_frequency: str  # "continuous", "daily", "weekly", "on_demand"
    test_cases: List[Dict[str, Any]]
    success_criteria: Dict[str, float]  # metric_name: threshold
    alerts_enabled: bool = True
    store_results: bool = True
    max_concurrent_evals: int = 5


@dataclass 
class EnterpriseEvalResult:
    """Enhanced eval result with enterprise context"""
    eval_id: str
    agent_id: str
    agent_name: str
    test_case_id: str
    timestamp: datetime
    
    # Core metrics
    accuracy_score: float
    latency_ms: float
    throughput_rps: float
    success: bool
    
    # Enterprise metrics
    cost_estimate: float
    compliance_score: float
    security_score: float
    business_impact_score: float
    
    # Detailed results
    raw_response: str
    expected_response: str
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


class EnterpriseEvaluator(Evaluator):
    """Enhanced evaluator with enterprise metrics and telemetry"""
    
    def __init__(self, registry: RedisAgentRegistry):
        super().__init__()
        self.registry = registry
        self.tracer = get_tracer("enterprise-evaluator")
        self.meter = get_meter("enterprise-evaluator")
        
        # Metrics
        self.eval_counter = self.meter.create_counter(
            name="enterprise_evals_total",
            description="Total enterprise evaluations run"
        )
        self.eval_success_rate = self.meter.create_gauge(
            name="enterprise_eval_success_rate",
            description="Success rate of evaluations"
        )
        self.agent_performance_score = self.meter.create_gauge(
            name="agent_performance_score",
            description="Overall performance score per agent"
        )
    
    async def run_enterprise_eval(self, config: EnterpriseEvalConfig) -> List[EnterpriseEvalResult]:
        """Run enterprise evaluation with enhanced metrics"""
        with self.tracer.start_as_current_span("enterprise_eval") as span:
            span.set_attribute("eval_id", config.eval_id)
            span.set_attribute("agent_targets", str(config.agent_targets))
            
            try:
                # Get target agents
                if "all" in config.agent_targets:
                    agents = await self.registry.list_agents()
                else:
                    agents = []
                    for agent_id in config.agent_targets:
                        agent = await self.registry.get_agent(agent_id)
                        if agent:
                            agents.append(agent)
                
                if not agents:
                    raise ValueError("No agents found for evaluation")
                
                # Run evaluations
                results = []
                for agent in agents:
                    agent_results = await self._evaluate_agent(agent, config)
                    results.extend(agent_results)
                
                # Update metrics
                self.eval_counter.add(len(results), {"eval_id": config.eval_id})
                
                # Calculate success rate
                successful_evals = sum(1 for r in results if r.success)
                success_rate = successful_evals / len(results) if results else 0
                self.eval_success_rate.set(success_rate, {"eval_id": config.eval_id})
                
                logging.info(f"Enterprise eval {config.eval_id} completed: {len(results)} results")
                return results
                
            except Exception as e:
                span.record_exception(e)
                logging.error(f"Enterprise eval {config.eval_id} failed: {str(e)}")
                raise
    
    async def _evaluate_agent(self, agent: AgentMetadata, config: EnterpriseEvalConfig) -> List[EnterpriseEvalResult]:
        """Evaluate a specific agent"""
        results = []
        
        for test_case in config.test_cases:
            try:
                # Run the test case
                start_time = time.time()
                
                # Mock agent call (replace with actual agent communication)
                response = await self._call_agent(agent, test_case)
                
                latency_ms = (time.time() - start_time) * 1000
                
                # Calculate metrics
                accuracy_score = self._calculate_accuracy(response, test_case.get("expected_output"))
                throughput_rps = 1.0 / (latency_ms / 1000) if latency_ms > 0 else 0
                
                # Enterprise metrics
                cost_estimate = self._calculate_cost(agent, latency_ms)
                compliance_score = self._calculate_compliance_score(response, test_case)
                security_score = self._calculate_security_score(response, test_case)
                business_impact_score = self._calculate_business_impact(response, test_case)
                
                result = EnterpriseEvalResult(
                    eval_id=config.eval_id,
                    agent_id=agent.agent_id,
                    agent_name=agent.name,
                    test_case_id=test_case.get("id", "unknown"),
                    timestamp=datetime.now(),
                    accuracy_score=accuracy_score,
                    latency_ms=latency_ms,
                    throughput_rps=throughput_rps,
                    success=accuracy_score >= config.success_criteria.get("accuracy", 0.8),
                    cost_estimate=cost_estimate,
                    compliance_score=compliance_score,
                    security_score=security_score,
                    business_impact_score=business_impact_score,
                    raw_response=response,
                    expected_response=test_case.get("expected_output", ""),
                    metadata=test_case.get("metadata", {})
                )
                
                results.append(result)
                
            except Exception as e:
                logging.error(f"Test case {test_case.get('id')} failed for agent {agent.name}: {str(e)}")
                
                # Create failed result
                failed_result = EnterpriseEvalResult(
                    eval_id=config.eval_id,
                    agent_id=agent.agent_id,
                    agent_name=agent.name,
                    test_case_id=test_case.get("id", "unknown"),
                    timestamp=datetime.now(),
                    accuracy_score=0.0,
                    latency_ms=0.0,
                    throughput_rps=0.0,
                    success=False,
                    cost_estimate=0.0,
                    compliance_score=0.0,
                    security_score=0.0,
                    business_impact_score=0.0,
                    raw_response="",
                    expected_response=test_case.get("expected_output", ""),
                    error_message=str(e),
                    metadata=test_case.get("metadata", {})
                )
                
                results.append(failed_result)
        
        return results
    
    async def _call_agent(self, agent: AgentMetadata, test_case: Dict[str, Any]) -> str:
        """Call agent with test case (mock implementation)"""
        # This would be replaced with actual agent communication
        await asyncio.sleep(0.1)  # Simulate processing time
        return f"Mock response for {test_case.get('input', 'test')}"
    
    def _calculate_accuracy(self, response: str, expected: str) -> float:
        """Calculate accuracy score"""
        if not expected:
            return 1.0
        
        # Simple string similarity (replace with more sophisticated matching)
        if response.lower() == expected.lower():
            return 1.0
        elif expected.lower() in response.lower():
            return 0.8
        else:
            return 0.3
    
    def _calculate_cost(self, agent: AgentMetadata, latency_ms: float) -> float:
        """Calculate cost estimate"""
        # Mock cost calculation based on agent resources and latency
        base_cost = agent.cpu_cores * 0.1 + agent.memory_gb * 0.05
        latency_cost = latency_ms * 0.001
        return base_cost + latency_cost
    
    def _calculate_compliance_score(self, response: str, test_case: Dict[str, Any]) -> float:
        """Calculate compliance score"""
        # Mock compliance scoring
        compliance_checks = test_case.get("compliance_checks", [])
        if not compliance_checks:
            return 1.0
        
        passed_checks = 0
        for check in compliance_checks:
            if self._check_compliance(response, check):
                passed_checks += 1
        
        return passed_checks / len(compliance_checks) if compliance_checks else 1.0
    
    def _check_compliance(self, response: str, check: Dict[str, Any]) -> bool:
        """Check specific compliance requirement"""
        check_type = check.get("type")
        
        if check_type == "no_pii":
            # Check for PII patterns
            pii_patterns = [r'\b\d{3}-\d{2}-\d{4}\b', r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b']
            for pattern in pii_patterns:
                if re.search(pattern, response):
                    return False
            return True
        
        elif check_type == "data_retention":
            # Check data retention compliance
            return "retention_policy" in response.lower()
        
        return True
    
    def _calculate_security_score(self, response: str, test_case: Dict[str, Any]) -> float:
        """Calculate security score"""
        # Mock security scoring
        security_checks = test_case.get("security_checks", [])
        if not security_checks:
            return 1.0
        
        passed_checks = 0
        for check in security_checks:
            if self._check_security(response, check):
                passed_checks += 1
        
        return passed_checks / len(security_checks) if security_checks else 1.0
    
    def _check_security(self, response: str, check: Dict[str, Any]) -> bool:
        """Check specific security requirement"""
        check_type = check.get("type")
        
        if check_type == "no_secrets":
            # Check for potential secrets
            secret_patterns = [r'password\s*=\s*\w+', r'api_key\s*=\s*\w+', r'token\s*=\s*\w+']
            for pattern in secret_patterns:
                if re.search(pattern, response, re.IGNORECASE):
                    return False
            return True
        
        elif check_type == "encryption_mentioned":
            return "encrypt" in response.lower() or "secure" in response.lower()
        
        return True
    
    def _calculate_business_impact(self, response: str, test_case: Dict[str, Any]) -> float:
        """Calculate business impact score"""
        # Mock business impact calculation
        impact_factors = test_case.get("business_impact_factors", [])
        if not impact_factors:
            return 0.5
        
        total_score = 0
        for factor in impact_factors:
            factor_type = factor.get("type")
            if factor_type == "revenue_impact":
                if "revenue" in response.lower() or "profit" in response.lower():
                    total_score += 0.8
                else:
                    total_score += 0.3
            elif factor_type == "customer_satisfaction":
                if "customer" in response.lower() or "satisfaction" in response.lower():
                    total_score += 0.7
                else:
                    total_score += 0.4
        
        return min(total_score / len(impact_factors), 1.0)


class ContinuousEvalManager:
    """Manages continuous evaluation scheduling and execution"""
    
    def __init__(self, evaluator: EnterpriseEvaluator):
        self.evaluator = evaluator
        self.scheduled_evals = {}
        self.tracer = get_tracer("continuous-eval-manager")
        self.meter = get_meter("continuous-eval-manager")
        
        # Metrics
        self.scheduled_evals_counter = self.meter.create_counter(
            name="scheduled_evals_total",
            description="Total scheduled evaluations"
        )
        self.completed_evals_counter = self.meter.create_counter(
            name="completed_evals_total",
            description="Total completed evaluations"
        )
    
    async def schedule_eval(self, config: EnterpriseEvalConfig) -> str:
        """Schedule an evaluation"""
        eval_id = f"eval_{int(time.time())}"
        config.eval_id = eval_id
        
        self.scheduled_evals[eval_id] = {
            "config": config,
            "status": EvalStatus.SCHEDULED,
            "next_run": self._calculate_next_run(config.eval_frequency)
        }
        
        self.scheduled_evals_counter.add(1, {"eval_id": eval_id})
        logging.info(f"Scheduled evaluation {eval_id}")
        
        return eval_id
    
    def _calculate_next_run(self, frequency: str) -> datetime:
        """Calculate next run time based on frequency"""
        now = datetime.now()
        
        if frequency == "continuous":
            return now + timedelta(minutes=5)
        elif frequency == "daily":
            return now + timedelta(days=1)
        elif frequency == "weekly":
            return now + timedelta(weeks=1)
        else:
            return now + timedelta(hours=1)
    
    async def run_scheduled_evals(self):
        """Run all scheduled evaluations"""
        current_time = datetime.now()
        
        for eval_id, eval_info in self.scheduled_evals.items():
            if (eval_info["status"] == EvalStatus.SCHEDULED and 
                current_time >= eval_info["next_run"]):
                
                try:
                    eval_info["status"] = EvalStatus.RUNNING
                    
                    # Run the evaluation
                    results = await self.evaluator.run_enterprise_eval(eval_info["config"])
                    
                    # Update status and schedule next run
                    eval_info["status"] = EvalStatus.COMPLETED
                    eval_info["next_run"] = self._calculate_next_run(
                        eval_info["config"].eval_frequency
                    )
                    
                    self.completed_evals_counter.add(1, {"eval_id": eval_id})
                    
                    logging.info(f"Completed scheduled evaluation {eval_id}: {len(results)} results")
                    
                except Exception as e:
                    eval_info["status"] = EvalStatus.FAILED
                    logging.error(f"Scheduled evaluation {eval_id} failed: {str(e)}")
    
    async def get_eval_status(self, eval_id: str) -> Dict[str, Any]:
        """Get evaluation status"""
        if eval_id not in self.scheduled_evals:
            return {"error": "Evaluation not found"}
        
        eval_info = self.scheduled_evals[eval_id]
        return {
            "eval_id": eval_id,
            "status": eval_info["status"],
            "next_run": eval_info["next_run"].isoformat(),
            "config": {
                "name": eval_info["config"].name,
                "description": eval_info["config"].description,
                "agent_targets": eval_info["config"].agent_targets,
                "eval_frequency": eval_info["config"].eval_frequency
            }
        }
