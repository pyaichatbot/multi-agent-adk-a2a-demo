"""
SageAI Tool Client
SOLID Principle: Single Responsibility - Handles SageAI tool API communication
Enterprise Standard: Clean, maintainable client with proper error handling
"""

import httpx
import time
import asyncio
from typing import Dict, Any, Optional, List

from src.config.settings import settings
from src.core.sageai_auth import sageai_auth
from src.core.sageai_observability import sageai_observability


class SageAIToolClient:
    """Enterprise SageAI tool client with authentication and observability"""
    
    def __init__(self):
        self.base_url = settings.sageai.base_url
        self.timeout = settings.sageai.timeout
        self.max_retries = settings.sageai.max_retries
        
    async def list_tools(self, token: str) -> List[Dict[str, Any]]:
        """List all available SageAI tools from the platform"""
        try:
            start_time = time.time()
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Call SageAI platform to get available tools
                response = await client.get(
                    f"{self.base_url}/tools",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    }
                )
                
                latency = time.time() - start_time
                sageai_observability.record_sageai_api_call(
                    "/tools", "GET", response.status_code, latency
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Handle different possible response formats from SageAI
                    tools = data.get('tools', data.get('data', data.get('results', [])))
                    
                    # Normalize tool data structure
                    normalized_tools = []
                    for tool in tools:
                        normalized_tool = {
                            'id': tool.get('id', tool.get('tool_id', 'unknown')),
                            'name': tool.get('name', tool.get('tool_name', 'Unknown Tool')),
                            'description': tool.get('description', tool.get('summary', 'No description available')),
                            'status': tool.get('status', tool.get('state', 'active')),
                            'category': tool.get('category', tool.get('type', 'general')),
                            'version': tool.get('version', '1.0.0'),
                            'parameters': tool.get('parameters', tool.get('schema', {})),
                            'created_at': tool.get('created_at', tool.get('created', None)),
                            'updated_at': tool.get('updated_at', tool.get('modified', None))
                        }
                        normalized_tools.append(normalized_tool)
                    
                    sageai_observability.log("info", "SageAI tools listed from platform", 
                                           count=len(normalized_tools))
                    return normalized_tools
                else:
                    sageai_observability.log("error", "Failed to list SageAI tools from platform", 
                                           status_code=response.status_code, 
                                           response_text=response.text[:200])
                    return []
                    
        except Exception as e:
            sageai_observability.log("error", "SageAI tool listing failed", error=str(e))
            return []
    
    async def get_tool_details(self, tool_id: str, token: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific SageAI tool"""
        try:
            start_time = time.time()
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/tools/{tool_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                latency = time.time() - start_time
                sageai_observability.record_sageai_api_call(
                    f"/tools/{tool_id}", "GET", response.status_code, latency
                )
                
                if response.status_code == 200:
                    tool_details = response.json()
                    sageai_observability.log("info", "SageAI tool details retrieved", 
                                           tool_id=tool_id)
                    return tool_details
                else:
                    sageai_observability.log("error", "Failed to get SageAI tool details", 
                                           tool_id=tool_id, status_code=response.status_code)
                    return None
                    
        except Exception as e:
            sageai_observability.log("error", "SageAI tool details retrieval failed", 
                                   tool_id=tool_id, error=str(e))
            return None
    
    async def execute_tool(self, tool_id: str, parameters: Dict[str, Any], 
                          token: str) -> Optional[Dict[str, Any]]:
        """Execute a SageAI tool with parameters and retry logic"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                
                # Prepare payload for SageAI tool execution
                payload = {
                    "tool_id": tool_id,
                    "parameters": parameters,
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
                        f"{self.base_url}/tools/{tool_id}/execute",
                        json=payload,
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json"
                        }
                    )
                    
                    latency = time.time() - start_time
                    sageai_observability.record_sageai_api_call(
                        f"/tools/{tool_id}/execute", "POST", response.status_code, latency
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        # Normalize response from SageAI
                        result = {
                            'success': True,
                            'tool_id': tool_id,
                            'output': data.get('output', data.get('result', data.get('response', 'No output'))),
                            'metadata': data.get('metadata', {}),
                            'execution_time': data.get('execution_time', latency),
                            'status': data.get('status', 'completed'),
                            'attempt': attempt + 1,
                            'raw_response': data
                        }
                        
                        sageai_observability.record_tool_execution(
                            tool_id, "user", True, latency
                        )
                        sageai_observability.log("info", "SageAI tool executed successfully", 
                                               tool_id=tool_id, execution_time=latency, attempt=attempt + 1)
                        return result
                    else:
                        last_error = f"SageAI tool execution failed: {response.status_code}"
                        sageai_observability.log("warning", "SageAI tool execution failed, retrying", 
                                               tool_id=tool_id, status_code=response.status_code, 
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
                last_error = f"SageAI tool execution error: {str(e)}"
                sageai_observability.log("warning", "SageAI tool execution error, retrying", 
                                       tool_id=tool_id, error=str(e), attempt=attempt + 1, max_retries=self.max_retries)
                
                # Wait before retry (exponential backoff)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s
        
        # All retries failed
        sageai_observability.record_tool_execution(tool_id, "user", False, 0)
        sageai_observability.log("error", "SageAI tool execution failed after all retries", 
                               tool_id=tool_id, error=last_error, max_retries=self.max_retries)
        
        return {
            'success': False,
            'tool_id': tool_id,
            'error': f"SageAI tool execution failed after {self.max_retries} attempts: {last_error}",
            'max_retries': self.max_retries
        }


# Global tool client instance
sageai_tool_client = SageAIToolClient()
