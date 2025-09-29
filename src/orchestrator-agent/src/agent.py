"""
Orchestrator Agent - Central coordination agent using A2A protocol
Dynamically routes requests to specialized agents based on capabilities
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
import logging

from google.adk import Agent
from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent, LoopAgent
from a2a.client import A2AClient
# Optional imports - handle missing dependencies gracefully
try:
    from adk_shared.observability import get_tracer, trace_agent_call
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
                 registry_url: str = "redis://localhost:6379"):
        # Load configurations
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        with open(policy_path, 'r') as f:
            self.policy = yaml.safe_load(f)
        
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
        if REGISTRY_AVAILABLE:
            self.registry = RedisAgentRegistry(registry_url)
            self.agents = {}  # Will be populated dynamically
        else:
            # Fallback to hardcoded configuration
            self.agents = {}
            for agent_config in config.get('agents', []):
                client = A2AClient(
                    agent_url=agent_config['url'],
                    agent_name=agent_config['name'],
                    capabilities=agent_config['capabilities']
                )
                self.agents[agent_config['name']] = client
        
        # Initialize LiteLLM wrapper for enhanced functionality
        self.litellm_wrapper = get_litellm_wrapper('orchestrator')
        self.tracer = get_tracer("orchestrator-agent")
        
        # Orchestration patterns
        self.sequential_agent = None
        self.parallel_agent = None
        self.loop_agent = None
    
    async def start_service_discovery(self):
        """Start service discovery and populate agent pool"""
        if not REGISTRY_AVAILABLE:
            return
        
        try:
            # Discover available agents
            available_agents = await self.registry.list_agents(status=AgentStatus.HEALTHY)
            
            # Create A2A clients for discovered agents
            for agent_metadata in available_agents:
                client = A2AClient(
                    agent_url=agent_metadata.endpoint_url,
                    agent_name=agent_metadata.name,
                    capabilities=[cap.name for cap in agent_metadata.capabilities]
                )
                self.agents[agent_metadata.name] = client
                
            logging.info(f"Discovered {len(self.agents)} agents via service discovery")
            
        except Exception as e:
            logging.error(f"Service discovery failed: {e}")
            # Fallback to hardcoded configuration if discovery fails
    
    async def process_request(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process request using ADK LLM-driven delegation"""
        # Ensure agents are discovered
        if REGISTRY_AVAILABLE and not self.agents:
            await self.start_service_discovery()
        
        # Determine orchestration pattern
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
                    agent_client = self.agents[selected_agent]
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
            for name, client in self.agents.items()
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
                "agent": list(self.agents.keys())[0],
                "reasoning": "Fallback selection due to parsing error"
            }
        except Exception as e:
            logging.error(f"Agent selection failed: {e}")
            # Fallback to first available agent
            return {
                "agent": list(self.agents.keys())[0],
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
    
    async def _execute_sequential(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute sequential orchestration pattern"""
        if not self.sequential_agent:
            # Create SequentialAgent with discovered agents
            sub_agents = []
            for name, client in self.agents.items():
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
            for name, client in self.agents.items():
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
            for name, client in self.agents.items():
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
