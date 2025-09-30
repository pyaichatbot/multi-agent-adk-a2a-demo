"""
Orchestrator Agent - Central coordination agent using A2A protocol
Dynamically routes requests to specialized agents based on capabilities
"""

import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
import logging

from google.adk import Agent
from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent, LoopAgent
from a2a.client import A2AClient
# Optional imports - handle missing dependencies gracefully
try:
    from adk_shared.observability import get_tracer, trace_agent_call_simple as trace_agent_call
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    print("Warning: Observability module not available, using mock implementations")
    OBSERVABILITY_AVAILABLE = False
    def get_tracer(name): return None
    def trace_agent_call(agent, target, transaction_id): return None

try:
    from adk_shared.security import validate_policy
    SECURITY_AVAILABLE = True
except ImportError:
    print("Warning: Security module not available, using mock implementations")
    SECURITY_AVAILABLE = False
    def validate_policy(policy, source, target): return True

try:
    from adk_shared.agent_registry import RedisAgentRegistry, AgentMetadata, AgentCapability, AgentStatus
    REGISTRY_AVAILABLE = True
except ImportError:
    print("Warning: Agent registry not available, using mock implementations")
    REGISTRY_AVAILABLE = False
    def RedisAgentRegistry(): return None
    def AgentMetadata(): return None
    def AgentCapability(): return None
    def AgentStatus(): return None

from adk_shared.litellm_integration import create_agent_llm_config, get_litellm_wrapper
import yaml


class EnterpriseOrchestrator(LlmAgent):
    """Enterprise orchestrator with dynamic routing using service discovery"""
    
    def __init__(self, config_path: str = "config/root_agent.yaml", policy_path: str = "config/policy.yaml", 
                 registry_url: str = None):
        # Load configurations
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        with open(policy_path, 'r') as f:
            self._policy = yaml.safe_load(f)
        
        # Create LiteLLM-compatible configuration
        llm_config = create_agent_llm_config('orchestrator')
        
        # Initialize as LlmAgent with dynamic routing capabilities
        super().__init__(
            name="EnterpriseOrchestrator",
            description="Central orchestrator for enterprise multi-agent system with dynamic routing",
            instruction="You are an enterprise orchestrator. Analyze incoming requests and route them to the most appropriate specialized agent using service discovery.",
            model=llm_config.get('model', 'gpt-4'),
            tools=[],  # We'll add routing tools
        )
        
        # Initialize service discovery
        # Use environment variable for Redis URL if not provided
        if registry_url is None:
            registry_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        if REGISTRY_AVAILABLE:
            self._registry = RedisAgentRegistry(registry_url)
            self._agents = {}  # Will be populated dynamically
        else:
            # Fallback to hardcoded configuration
            self._agents = {}
            for agent_config in config.get('agents', []):
                client = A2AClient(
                    agent_url=agent_config['url'],
                    agent_name=agent_config['name'],
                    capabilities=agent_config['capabilities']
                )
                self._agents[agent_config['name']] = client
        
        # Initialize LiteLLM wrapper for enhanced functionality
        self._litellm_wrapper = get_litellm_wrapper('orchestrator')
        self._tracer = get_tracer("orchestrator-agent")
        
        # Orchestration patterns
        self._sequential_agent = None
        self._parallel_agent = None
        self._loop_agent = None
    
    async def start_service_discovery(self):
        """Start service discovery and populate agent pool"""
        if not REGISTRY_AVAILABLE:
            return
        
        try:
            # Discover available agents
            available_agents = await self._registry.list_agents(status=AgentStatus.HEALTHY)
            
            # Create A2A clients for discovered agents
            for agent_metadata in available_agents:
                client = A2AClient(
                    agent_url=agent_metadata.endpoint_url,
                    agent_name=agent_metadata.name,
                    capabilities=[cap.name for cap in agent_metadata.capabilities]
                )
                self._agents[agent_metadata.name] = client
                
            logging.info(f"Discovered {len(self._agents)} agents via service discovery")
            
        except Exception as e:
            logging.error(f"Service discovery failed: {e}")
            # Fallback to hardcoded configuration if discovery fails
    
    async def process_request(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process request using ADK LLM-driven delegation with user overrides"""
        # Ensure agents are discovered
        if REGISTRY_AVAILABLE and not self._agents:
            await self.start_service_discovery()
        
        # Check for user overrides in context
        user_override = self._extract_user_overrides(context)
        
        if user_override:
            return await self._execute_user_override(query, context, user_override)
        
        # Determine orchestration pattern automatically
        orchestration_pattern = await self._determine_orchestration_pattern(query, context)
        
        if orchestration_pattern == "sequential":
            return await self._execute_sequential(query, context)
        elif orchestration_pattern == "parallel":
            return await self._execute_parallel(query, context)
        elif orchestration_pattern == "loop":
            return await self._execute_loop(query, context)
        else:
            # Default to simple routing
            return await self.route_request(query, context)
    
    async def route_request(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Route request to most appropriate agent with governance checks"""
        transaction_id = str(uuid.uuid4())
        
        with self.tracer.start_as_current_span("orchestration_request") as span:
            span.set_attribute("transaction_id", transaction_id)
            span.set_attribute("query", query)
            
            try:
                # Determine best agent using LLM reasoning
                agent_selection = await self._select_agent(query, context)
                selected_agent = agent_selection['agent']
                
                # Validate policy compliance
                if not validate_policy(self.policy, "orchestrator", selected_agent):
                    raise PermissionError(f"Policy violation: orchestrator cannot call {selected_agent}")
                
                # Execute request with selected agent
                with trace_agent_call("orchestrator", selected_agent, transaction_id):
                    agent_client = self._agents[selected_agent]
                    response = await agent_client.process_request(query, context)
                
                return {
                    "transaction_id": transaction_id,
                    "orchestrator": "EnterpriseOrchestrator",
                    "selected_agent": selected_agent,
                    "selection_reasoning": agent_selection['reasoning'],
                    "query": query,
                    "response": response,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                span.record_exception(e)
                logging.error(f"Orchestration failed: {transaction_id} - {str(e)}")
                raise
    
    async def _select_agent(self, query: str, context: Dict[str, Any] = None) -> Dict[str, str]:
        """Use LLM to select the most appropriate agent"""
        capabilities_summary = "\n".join([
            f"- {name}: {client.capabilities}"
            for name, client in self._agents.items()
        ])
        
        selection_prompt = f"""
        Based on the following query and available agents, select the most appropriate agent:
        
        Query: {query}
        Context: {context or {}}
        
        Available Agents:
        {capabilities_summary}
        
        Respond with JSON containing:
        - agent: the selected agent name
        - reasoning: why this agent was selected
        """
        
        # Use LiteLLM wrapper for enhanced functionality
        messages = [
            {"role": "user", "content": selection_prompt}
        ]
        
        try:
            response = await self.litellm_wrapper.chat_completion(messages)
            response_text = response.get('content', '')
            
            # Parse JSON response
            return json.loads(response_text)
            
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse agent selection response: {e}")
            # Fallback to first available agent
            return {
                "agent": list(self._agents.keys())[0],
                "reasoning": "Fallback selection due to parsing error"
            }
        except Exception as e:
            logging.error(f"Agent selection failed: {e}")
            # Fallback to first available agent
            return {
                "agent": list(self._agents.keys())[0],
                "reasoning": f"Fallback selection due to error: {str(e)}"
            }
    
    async def _determine_orchestration_pattern(self, query: str, context: Dict[str, Any] = None) -> str:
        """Determine the best orchestration pattern for the request"""
        pattern_prompt = f"""
        Analyze the following request and determine the best orchestration pattern:
        
        Query: {query}
        Context: {context or {}}
        
        Available patterns:
        - sequential: Step-by-step execution (e.g., "First get data, then analyze, then report")
        - parallel: Concurrent execution (e.g., "Get data from multiple sources simultaneously")
        - loop: Iterative execution (e.g., "Keep refining until condition is met")
        - simple: Single agent execution (default)
        
        Respond with just the pattern name.
        """
        
        try:
            messages = [{"role": "user", "content": pattern_prompt}]
            response = await self.litellm_wrapper.chat_completion(messages)
            pattern = response.get('content', '').strip().lower()
            
            if pattern in ["sequential", "parallel", "loop", "simple"]:
                return pattern
            else:
                return "simple"
                
        except Exception as e:
            logging.error(f"Pattern determination failed: {e}")
            return "simple"
    
    def _extract_user_overrides(self, context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Extract user overrides from context"""
        if not context:
            return None
        
        overrides = {}
        
        # Check for explicit orchestration pattern
        if "orchestration_pattern" in context:
            pattern = context["orchestration_pattern"]
            if pattern in ["sequential", "parallel", "loop", "simple"]:
                overrides["pattern"] = pattern
        
        # Check for explicit agent list
        if "agents" in context:
            agents = context["agents"]
            if isinstance(agents, list) and len(agents) > 0:
                overrides["agents"] = agents
        
        # Check for explicit agent order (for sequential)
        if "agent_sequence" in context:
            sequence = context["agent_sequence"]
            if isinstance(sequence, list) and len(sequence) > 0:
                overrides["agent_sequence"] = sequence
        
        # Check for parallel execution config
        if "parallel_config" in context:
            parallel_config = context["parallel_config"]
            if isinstance(parallel_config, dict):
                overrides["parallel_config"] = parallel_config
        
        # Check for loop configuration
        if "loop_config" in context:
            loop_config = context["loop_config"]
            if isinstance(loop_config, dict):
                overrides["loop_config"] = loop_config
        
        return overrides if overrides else None
    
    async def _execute_user_override(self, query: str, context: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Execute request with user-specified overrides"""
        transaction_id = str(uuid.uuid4())
        
        with self.tracer.start_as_current_span("user_override_execution") as span:
            span.set_attribute("transaction_id", transaction_id)
            span.set_attribute("override_pattern", override.get("pattern", "unknown"))
            
            try:
                pattern = override.get("pattern", "simple")
                
                if pattern == "sequential":
                    return await self._execute_sequential_override(query, context, override)
                elif pattern == "parallel":
                    return await self._execute_parallel_override(query, context, override)
                elif pattern == "loop":
                    return await self._execute_loop_override(query, context, override)
                else:
                    return await self._execute_simple_override(query, context, override)
                    
            except Exception as e:
                span.record_exception(e)
                logging.error(f"User override execution failed: {transaction_id} - {str(e)}")
                raise
    
    async def _execute_sequential_override(self, query: str, context: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Execute sequential pattern with user-specified agents"""
        agent_sequence = override.get("agent_sequence", override.get("agents", []))
        
        if not agent_sequence:
            raise ValueError("No agents specified for sequential execution")
        
        results = []
        for agent_name in agent_sequence:
            if agent_name not in self._agents:
                raise ValueError(f"Agent '{agent_name}' not available")
            
            agent_client = self._agents[agent_name]
            result = await agent_client.process_request(query, context)
            results.append({
                "agent": agent_name,
                "result": result
            })
        
        return {
            "pattern": "sequential",
            "user_override": True,
            "agent_sequence": agent_sequence,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_parallel_override(self, query: str, context: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Execute parallel pattern with user-specified agents"""
        agents = override.get("agents", [])
        parallel_config = override.get("parallel_config", {})
        
        if not agents:
            raise ValueError("No agents specified for parallel execution")
        
        # Execute all agents concurrently
        import asyncio
        tasks = []
        for agent_name in agents:
            if agent_name not in self._agents:
                raise ValueError(f"Agent '{agent_name}' not available")
            
            agent_client = self._agents[agent_name]
            task = agent_client.process_request(query, context)
            tasks.append((agent_name, task))
        
        # Wait for all tasks to complete
        results = []
        for agent_name, task in tasks:
            try:
                result = await task
                results.append({
                    "agent": agent_name,
                    "result": result,
                    "status": "success"
                })
            except Exception as e:
                results.append({
                    "agent": agent_name,
                    "error": str(e),
                    "status": "failed"
                })
        
        return {
            "pattern": "parallel",
            "user_override": True,
            "agents": agents,
            "parallel_config": parallel_config,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_loop_override(self, query: str, context: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Execute loop pattern with user-specified configuration"""
        agents = override.get("agents", [])
        loop_config = override.get("loop_config", {})
        
        if not agents:
            raise ValueError("No agents specified for loop execution")
        
        max_iterations = loop_config.get("max_iterations", 10)
        condition = loop_config.get("condition", "Check if result meets requirements")
        iteration = 0
        results = []
        
        while iteration < max_iterations:
            iteration += 1
            
            # Execute agents in sequence for this iteration
            iteration_results = []
            for agent_name in agents:
                if agent_name not in self._agents:
                    raise ValueError(f"Agent '{agent_name}' not available")
                
                agent_client = self._agents[agent_name]
                result = await agent_client.process_request(query, context)
                iteration_results.append({
                    "agent": agent_name,
                    "result": result
                })
            
            results.append({
                "iteration": iteration,
                "results": iteration_results
            })
            
            # Check if condition is met (simplified for now)
            # In a real implementation, this would use the LLM to evaluate the condition
            if iteration >= 3:  # Simplified condition
                break
        
        return {
            "pattern": "loop",
            "user_override": True,
            "agents": agents,
            "loop_config": loop_config,
            "iterations_completed": iteration,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_simple_override(self, query: str, context: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Execute simple pattern with user-specified agent"""
        agents = override.get("agents", [])
        
        if not agents:
            raise ValueError("No agent specified for simple execution")
        
        if len(agents) > 1:
            raise ValueError("Simple execution requires exactly one agent")
        
        agent_name = agents[0]
        if agent_name not in self._agents:
            raise ValueError(f"Agent '{agent_name}' not available")
        
        agent_client = self._agents[agent_name]
        result = await agent_client.process_request(query, context)
        
        return {
            "pattern": "simple",
            "user_override": True,
            "agent": agent_name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_sequential(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute sequential orchestration pattern"""
        if not self.sequential_agent:
            # Create SequentialAgent with discovered agents
            sub_agents = []
            for name, client in self._agents.items():
                # Create LlmAgent for each discovered agent
                sub_agent = LlmAgent(
                    name=name,
                    description=f"Agent for {name}",
                    instruction=f"You are {name}. {client.capabilities}",
                    model="gpt-4",
                    tools=[]
                )
                sub_agents.append(sub_agent)
            
            self.sequential_agent = SequentialAgent(
                name="SequentialOrchestrator",
                description="Sequential execution orchestrator",
                sub_agents=sub_agents
            )
        
        # Execute sequential workflow
        result = await self.sequential_agent.process_request(query, context)
        return {
            "pattern": "sequential",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_parallel(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute parallel orchestration pattern"""
        if not self.parallel_agent:
            # Create ParallelAgent with discovered agents
            sub_agents = []
            for name, client in self._agents.items():
                sub_agent = LlmAgent(
                    name=name,
                    description=f"Agent for {name}",
                    instruction=f"You are {name}. {client.capabilities}",
                    model="gpt-4",
                    tools=[]
                )
                sub_agents.append(sub_agent)
            
            self.parallel_agent = ParallelAgent(
                name="ParallelOrchestrator",
                description="Parallel execution orchestrator",
                sub_agents=sub_agents
            )
        
        # Execute parallel workflow
        result = await self.parallel_agent.process_request(query, context)
        return {
            "pattern": "parallel",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_loop(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute loop orchestration pattern"""
        if not self.loop_agent:
            # Create LoopAgent with discovered agents
            sub_agents = []
            for name, client in self._agents.items():
                sub_agent = LlmAgent(
                    name=name,
                    description=f"Agent for {name}",
                    instruction=f"You are {name}. {client.capabilities}",
                    model="gpt-4",
                    tools=[]
                )
                sub_agents.append(sub_agent)
            
            self.loop_agent = LoopAgent(
                name="LoopOrchestrator",
                description="Loop execution orchestrator",
                sub_agents=sub_agents,
                max_iterations=10,  # Prevent infinite loops
                condition_check="Check if the result meets the requirements"
            )
        
        # Execute loop workflow
        result = await self.loop_agent.process_request(query, context)
        return {
            "pattern": "loop",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
