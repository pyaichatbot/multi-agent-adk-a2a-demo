"""
LiteLLM Wrapper for Azure OpenAI Integration

Provides a consistent interface for using LiteLLM with Azure OpenAI models
across the multi-agent system. Handles initialization, error handling, and
fallback mechanisms.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

try:
    import litellm
    from litellm import completion, acompletion
    from litellm.exceptions import APIError, RateLimitError, Timeout
except ImportError:
    raise ImportError("LiteLLM is required. Install with: pip install litellm")

from .azure_config import AzureOpenAIConfig

logger = logging.getLogger(__name__)


class LiteLLMWrapper:
    """Wrapper for LiteLLM with Azure OpenAI integration"""
    
    def __init__(self, agent_name: str, config: Optional[AzureOpenAIConfig] = None):
        """
        Initialize LiteLLM wrapper for specific agent
        
        Args:
            agent_name: Name of the agent using this wrapper
            config: Azure OpenAI configuration. If None, creates new instance
        """
        self.agent_name = agent_name
        self.config = config or AzureOpenAIConfig()
        self._setup_litellm()
        
        logger.info(f"LiteLLM wrapper initialized for agent: {agent_name}")
    
    def _setup_litellm(self):
        """Setup LiteLLM configuration and logging"""
        # Configure LiteLLM logging
        if self.config.debug_mode:
            litellm.set_verbose = True
        
        # Set log level
        log_level = self.config.log_level.upper()
        if hasattr(logging, log_level):
            litellm.logging_level = getattr(logging, log_level)
        
        # Configure retry settings
        retry_config = self.config.get_retry_config()
        litellm.num_retries = retry_config['max_retries']
        litellm.retry_delay = retry_config['retry_delay']
        litellm.request_timeout = retry_config['timeout']
        
        logger.info(f"LiteLLM configured with retry settings: {retry_config}")
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration for this agent"""
        return self.config.get_litellm_config(self.agent_name)
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Async chat completion using Azure OpenAI via LiteLLM
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Override model name
            temperature: Override temperature setting
            max_tokens: Override max tokens setting
            **kwargs: Additional parameters for LiteLLM
            
        Returns:
            Dictionary with completion response
            
        Raises:
            APIError: If API call fails
            RateLimitError: If rate limit exceeded
            Timeout: If request times out
        """
        try:
            # Get base configuration
            config = self.get_model_config()
            
            # Override with provided parameters
            if model:
                config['model'] = f"azure/{model}"
            if temperature is not None:
                config['temperature'] = temperature
            if max_tokens is not None:
                config['max_tokens'] = max_tokens
            
            # Merge additional kwargs
            config.update(kwargs)
            
            logger.info(f"Making chat completion request for agent: {self.agent_name}")
            logger.debug(f"Model config: {config}")
            
            # Make async completion request
            response = await acompletion(
                messages=messages,
                **config
            )
            
            logger.info(f"Chat completion successful for agent: {self.agent_name}")
            return self._format_response(response)
            
        except (APIError, RateLimitError, Timeout) as e:
            logger.error(f"LiteLLM API error for agent {self.agent_name}: {e}")
            
            # Try fallback if enabled
            if self.config.enable_fallback and self.config.openai_api_key:
                logger.info(f"Attempting fallback for agent: {self.agent_name}")
                return await self._fallback_completion(messages, **kwargs)
            
            raise
    
    def chat_completion_sync(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Synchronous chat completion using Azure OpenAI via LiteLLM
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Override model name
            temperature: Override temperature setting
            max_tokens: Override max tokens setting
            **kwargs: Additional parameters for LiteLLM
            
        Returns:
            Dictionary with completion response
        """
        try:
            # Get base configuration
            config = self.get_model_config()
            
            # Override with provided parameters
            if model:
                config['model'] = f"azure/{model}"
            if temperature is not None:
                config['temperature'] = temperature
            if max_tokens is not None:
                config['max_tokens'] = max_tokens
            
            # Merge additional kwargs
            config.update(kwargs)
            
            logger.info(f"Making sync chat completion request for agent: {self.agent_name}")
            logger.debug(f"Model config: {config}")
            
            # Make sync completion request
            response = completion(
                messages=messages,
                **config
            )
            
            logger.info(f"Sync chat completion successful for agent: {self.agent_name}")
            return self._format_response(response)
            
        except (APIError, RateLimitError, Timeout) as e:
            logger.error(f"LiteLLM API error for agent {self.agent_name}: {e}")
            
            # Try fallback if enabled
            if self.config.enable_fallback and self.config.openai_api_key:
                logger.info(f"Attempting fallback for agent: {self.agent_name}")
                return self._fallback_completion_sync(messages, **kwargs)
            
            raise
    
    async def _fallback_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """Fallback to OpenAI if Azure OpenAI fails"""
        try:
            fallback_config = {
                'model': 'gpt-4',
                'messages': messages,
                'api_key': self.config.openai_api_key,
                **kwargs
            }
            
            logger.info(f"Using OpenAI fallback for agent: {self.agent_name}")
            response = await acompletion(**fallback_config)
            
            return self._format_response(response)
            
        except Exception as e:
            logger.error(f"Fallback completion failed for agent {self.agent_name}: {e}")
            raise
    
    def _fallback_completion_sync(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """Synchronous fallback to OpenAI if Azure OpenAI fails"""
        try:
            fallback_config = {
                'model': 'gpt-4',
                'messages': messages,
                'api_key': self.config.openai_api_key,
                **kwargs
            }
            
            logger.info(f"Using OpenAI fallback for agent: {self.agent_name}")
            response = completion(**fallback_config)
            
            return self._format_response(response)
            
        except Exception as e:
            logger.error(f"Fallback completion failed for agent {self.agent_name}: {e}")
            raise
    
    def _format_response(self, response: Any) -> Dict[str, Any]:
        """Format LiteLLM response into consistent format"""
        try:
            # Extract content from response
            if hasattr(response, 'choices') and response.choices:
                content = response.choices[0].message.content
            else:
                content = str(response)
            
            return {
                'content': content,
                'model': getattr(response, 'model', 'unknown'),
                'usage': getattr(response, 'usage', {}),
                'timestamp': datetime.now().isoformat(),
                'agent': self.agent_name
            }
            
        except Exception as e:
            logger.error(f"Error formatting response for agent {self.agent_name}: {e}")
            return {
                'content': str(response),
                'model': 'unknown',
                'usage': {},
                'timestamp': datetime.now().isoformat(),
                'agent': self.agent_name,
                'error': str(e)
            }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for this agent"""
        # This would integrate with LiteLLM's usage tracking
        # For now, return basic info
        return {
            'agent': self.agent_name,
            'model': self.get_model_config().get('model', 'unknown'),
            'timestamp': datetime.now().isoformat()
        }
