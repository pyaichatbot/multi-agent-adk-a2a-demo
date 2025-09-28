"""
Orchestrator Agent - Central coordination agent using A2A protocol
Dynamically routes requests to specialized agents based on capabilities
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
import logging

from adk import Agent, A2AClient, RouterAgent
from adk_shared.observability import get_tracer, trace_agent_call
from adk_shared.security import validate_policy
import yaml


class EnterpriseOrchestrator(RouterAgent):
    """Enterprise orchestrator with dynamic routing and governance"""
    
    def __init__(self, config_path: str = "config/root_agent.yaml", policy_path: str = "config/policy.yaml"):
        # Load configurations
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        with open(policy_path, 'r') as f:
            self.policy = yaml.safe_load(f)
        
        # Initialize A2A clients for each specialized agent
        self.agents = {}
        for agent_config in config['agents']:
            client = A2AClient(
                agent_url=agent_config['url'],
                agent_name=agent_config['name'],
                capabilities=agent_config['capabilities']
            )
            self.agents[agent_config['name']] = client
        
        super().__init__(
            name="EnterpriseOrchestrator",
            description="Central orchestrator for enterprise multi-agent system",
            agents=list(self.agents.values()),
            llm_config=config['llm']
        )
        
        self.tracer = get_tracer("orchestrator-agent")
    
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
        
        response = await self.chat(selection_prompt)
        # Parse LLM response (implementation depends on LLM output format)
        return json.loads(response)
