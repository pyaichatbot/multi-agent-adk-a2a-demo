"""
Utility functions for LiteLLM integration

Provides helper functions for easy integration of LiteLLM with Azure OpenAI
across the multi-agent system.
"""

import logging
from typing import Dict, Any, List, Optional
from .azure_config import AzureOpenAIConfig
from .model_factory import ModelFactory
from .litellm_wrapper import LiteLLMWrapper

logger = logging.getLogger(__name__)


def create_agent_llm_config(agent_name: str, config: Optional[AzureOpenAIConfig] = None) -> Dict[str, Any]:
    """
    Create ADK-compatible LLM configuration for an agent
    
    Args:
        agent_name: Name of the agent
        config: Azure OpenAI configuration. If None, creates new instance
        
    Returns:
        Dictionary with ADK-compatible LLM configuration
    """
    factory = ModelFactory(config)
    return factory.create_agent_config(agent_name)


def get_litellm_wrapper(agent_name: str, config: Optional[AzureOpenAIConfig] = None) -> LiteLLMWrapper:
    """
    Get LiteLLM wrapper for an agent
    
    Args:
        agent_name: Name of the agent
        config: Azure OpenAI configuration. If None, creates new instance
        
    Returns:
        LiteLLMWrapper instance
    """
    factory = ModelFactory(config)
    return factory.get_wrapper(agent_name)


def validate_azure_config() -> Dict[str, Any]:
    """
    Validate Azure OpenAI configuration
    
    Returns:
        Dictionary with validation results
    """
    try:
        config = AzureOpenAIConfig()
        factory = ModelFactory(config)
        return factory.validate_configuration()
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return {
            'valid': False,
            'errors': [str(e)],
            'warnings': []
        }


def create_message(role: str, content: str) -> Dict[str, str]:
    """
    Create a message dictionary for LiteLLM
    
    Args:
        role: Message role ('user', 'assistant', 'system')
        content: Message content
        
    Returns:
        Message dictionary
    """
    return {
        'role': role,
        'content': content
    }


def create_chat_messages(
    system_prompt: Optional[str] = None,
    user_message: str = "",
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> List[Dict[str, str]]:
    """
    Create chat messages list for LiteLLM
    
    Args:
        system_prompt: Optional system prompt
        user_message: Current user message
        conversation_history: Optional conversation history
        
    Returns:
        List of message dictionaries
    """
    messages = []
    
    if system_prompt:
        messages.append(create_message('system', system_prompt))
    
    if conversation_history:
        messages.extend(conversation_history)
    
    if user_message:
        messages.append(create_message('user', user_message))
    
    return messages


def format_agent_response(response: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
    """
    Format agent response with consistent structure
    
    Args:
        response: Raw response from LiteLLM
        agent_name: Name of the agent
        
    Returns:
        Formatted response dictionary
    """
    return {
        'agent': agent_name,
        'content': response.get('content', ''),
        'model': response.get('model', 'unknown'),
        'usage': response.get('usage', {}),
        'timestamp': response.get('timestamp', ''),
        'success': True
    }


def handle_litellm_error(error: Exception, agent_name: str) -> Dict[str, Any]:
    """
    Handle LiteLLM errors and return formatted error response
    
    Args:
        error: Exception that occurred
        agent_name: Name of the agent
        
    Returns:
        Formatted error response
    """
    logger.error(f"LiteLLM error for agent {agent_name}: {error}")
    
    return {
        'agent': agent_name,
        'content': f"Error: {str(error)}",
        'model': 'unknown',
        'usage': {},
        'timestamp': None,
        'success': False,
        'error': str(error)
    }


def get_model_info(agent_name: str, config: Optional[AzureOpenAIConfig] = None) -> Dict[str, Any]:
    """
    Get model information for an agent
    
    Args:
        agent_name: Name of the agent
        config: Azure OpenAI configuration. If None, creates new instance
        
    Returns:
        Dictionary with model information
    """
    try:
        wrapper = get_litellm_wrapper(agent_name, config)
        model_config = wrapper.get_model_config()
        
        return {
            'agent': agent_name,
            'model': model_config['model'],
            'temperature': model_config['temperature'],
            'max_tokens': model_config['max_tokens'],
            'api_base': model_config['api_base'],
            'api_version': model_config['api_version']
        }
    except Exception as e:
        logger.error(f"Error getting model info for {agent_name}: {e}")
        return {
            'agent': agent_name,
            'error': str(e)
        }
