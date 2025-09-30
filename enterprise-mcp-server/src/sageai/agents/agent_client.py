"""
SageAI Agent Client
SOLID Principle: Single Responsibility - Handles SageAI agent API communication
Enterprise Standard: Clean, maintainable client with proper error handling
"""

import httpx
import time
import asyncio
from typing import Dict, Any, Optional, List

from src.config.settings import settings
from src.core.sageai_auth import sageai_auth
from src.core.sageai_observability import sageai_observability


class SageAIAgentClient:
    """Enterprise SageAI agent client with authentication and observability"""
    
    def __init__(self):
        self.base_url = settings.sageai.base_url
        self.timeout = settings.sageai.timeout
        self.max_retries = settings.sageai.max_retries
        
    async def list_agents(self, token: str) -> List[Dict[str, Any]]:
        """List all available SageAI agents from the platform"""
        try:
            start_time = time.time()
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Call SageAI platform to get available agents
                response = await client.get(
                    f"{self.base_url}/agents",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    }
                )
                
                latency = time.time() - start_time
                sageai_observability.record_sageai_api_call(
                    "/agents", "GET", response.status_code, latency
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Handle different possible response formats from SageAI
                    agents = data.get('agents', data.get('data', data.get('results', [])))
                    
                    # Normalize agent data structure
                    normalized_agents = []
                    for agent in agents:
                        normalized_agent = {
                            'id': agent.get('id', agent.get('agent_id', 'unknown')),
                            'name': agent.get('name', agent.get('agent_name', 'Unknown Agent')),
                            'description': agent.get('description', agent.get('summary', 'No description available')),
                            'status': agent.get('status', agent.get('state', 'active')),
                            'capabilities': agent.get('capabilities', agent.get('skills', [])),
                            'version': agent.get('version', '1.0.0'),
                            'created_at': agent.get('created_at', agent.get('created', None)),
                            'updated_at': agent.get('updated_at', agent.get('modified', None))
                        }
                        normalized_agents.append(normalized_agent)
                    
                    sageai_observability.log("info", "SageAI agents listed from platform", 
                                           count=len(normalized_agents))
                    return normalized_agents
                else:
                    sageai_observability.log("error", "Failed to list SageAI agents from platform", 
                                           status_code=response.status_code, 
                                           response_text=response.text[:200])
                    return []
                    
        except Exception as e:
            sageai_observability.log("error", "SageAI agent listing failed", error=str(e))
            return []
    
    async def get_agent_details(self, agent_id: str, token: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific SageAI agent"""
        try:
            start_time = time.time()
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/agents/{agent_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                latency = time.time() - start_time
                sageai_observability.record_sageai_api_call(
                    f"/agents/{agent_id}", "GET", response.status_code, latency
                )
                
                if response.status_code == 200:
                    agent_details = response.json()
                    sageai_observability.log("info", "SageAI agent details retrieved", 
                                           agent_id=agent_id)
                    return agent_details
                else:
                    sageai_observability.log("error", "Failed to get SageAI agent details", 
                                           agent_id=agent_id, status_code=response.status_code)
                    return None
                    
        except Exception as e:
            sageai_observability.log("error", "SageAI agent details retrieval failed", 
                                   agent_id=agent_id, error=str(e))
            return None
    
    async def invoke_agent(self, agent_id: str, input_data: Dict[str, Any], 
                          parameters: Optional[Dict[str, Any]], token: str) -> Optional[Dict[str, Any]]:
        """Invoke a SageAI agent with input data and parameters and retry logic"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                
                # Prepare payload for SageAI agent invocation
                payload = {
                    "agent_id": agent_id,
                    "input": input_data,
                    "parameters": parameters or {},
                    "metadata": {
                        "source": "enterprise-mcp-server",
                        "timestamp": time.time(),
                        "version": "1.0.0",
                        "attempt": attempt + 1
                    }
                }
                
                client = httpx.AsyncClient(timeout=self.timeout)
                try:
                    response = await client.post(
                        f"{self.base_url}/agents/{agent_id}/invoke",
                        json=payload,
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json"
                        }
                    )
                    
                    latency = time.time() - start_time
                    sageai_observability.record_sageai_api_call(
                        f"/agents/{agent_id}/invoke", "POST", response.status_code, latency
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        # Normalize response from SageAI
                        result = {
                            'success': True,
                            'agent_id': agent_id,
                            'output': data.get('output', data.get('result', data.get('response', 'No output'))),
                            'metadata': data.get('metadata', {}),
                            'execution_time': data.get('execution_time', latency),
                            'status': data.get('status', 'completed'),
                            'attempt': attempt + 1,
                            'raw_response': data
                        }
                        
                        sageai_observability.record_agent_invocation(
                            agent_id, "user", True, latency
                        )
                        sageai_observability.log("info", "SageAI agent invoked successfully", 
                                               agent_id=agent_id, execution_time=latency, attempt=attempt + 1)
                        return result
                    else:
                        last_error = f"SageAI agent invocation failed: {response.status_code}"
                        sageai_observability.log("warning", "SageAI agent invocation failed, retrying", 
                                               agent_id=agent_id, status_code=response.status_code, 
                                               attempt=attempt + 1, max_retries=self.max_retries)
                        
                        # Don't retry on client errors (4xx)
                        if 400 <= response.status_code < 500:
                            break
                            
                        # Wait before retry (exponential backoff)
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s
                finally:
                    await client.aclose()
                            
            except Exception as e:
                last_error = f"SageAI agent invocation error: {str(e)}"
                sageai_observability.log("warning", "SageAI agent invocation error, retrying", 
                                       agent_id=agent_id, error=str(e), attempt=attempt + 1, max_retries=self.max_retries)
                
                # Wait before retry (exponential backoff)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s
        
        # All retries failed
        sageai_observability.record_agent_invocation(agent_id, "user", False, 0)
        sageai_observability.log("error", "SageAI agent invocation failed after all retries", 
                               agent_id=agent_id, error=last_error, max_retries=self.max_retries)
        
        return {
            'success': False,
            'agent_id': agent_id,
            'error': f"SageAI agent invocation failed after {self.max_retries} attempts: {last_error}",
            'max_retries': self.max_retries
        }


# Global agent client instance
sageai_agent_client = SageAIAgentClient()
