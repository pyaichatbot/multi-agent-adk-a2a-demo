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
from adk_shared.litellm_integration import create_agent_llm_config, get_litellm_wrapper
import yaml


class EnterpriseOrchestrator(LlmAgent):
    """Enterprise orchestrator with dynamic routing using ADK patterns"""
    
    def __init__(self, config_path: str = "config/root_agent.yaml", policy_path: str = "config/policy.yaml"):
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
            instruction="You are an enterprise orchestrator. Analyze incoming requests and route them to the most appropriate specialized agent. You can route to: DataSearchAgent for data queries, ReportingAgent for reports and analytics, or ExampleAgent for examples and demos.",
            model=llm_config.get('model', 'gpt-4'),
            tools=[],  # We'll add routing tools
        )
        
        # Initialize A2A clients for external agent communication
        self.agents = {}
        for agent_config in config['agents']:
            client = A2AClient(
                agent_url=agent_config['url'],
                agent_name=agent_config['name'],
                capabilities=agent_config['capabilities']
            )
            self.agents[agent_config['name']] = client
        
        # Initialize LiteLLM wrapper for enhanced functionality
        self.litellm_wrapper = get_litellm_wrapper('orchestrator')
        self.tracer = get_tracer("orchestrator-agent")
    
    async def process_request(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process request using ADK LLM-driven delegation"""
        # Use the LlmAgent's built-in capabilities to analyze and route
        # The LLM will decide whether to handle directly or delegate
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
