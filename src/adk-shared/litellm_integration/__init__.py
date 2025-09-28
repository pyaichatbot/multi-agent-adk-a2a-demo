"""
LiteLLM Integration Module for Azure OpenAI

This module provides utilities for integrating LiteLLM with Azure OpenAI models
across the multi-agent system. It includes configuration management, model
initialization, and consistent error handling.
"""

from .azure_config import AzureOpenAIConfig
from .litellm_wrapper import LiteLLMWrapper
from .model_factory import ModelFactory
from .utils import (
    create_agent_llm_config,
    get_litellm_wrapper,
    validate_azure_config,
    create_message,
    create_chat_messages,
    format_agent_response,
    handle_litellm_error,
    get_model_info
)

__all__ = [
    "AzureOpenAIConfig",
    "LiteLLMWrapper", 
    "ModelFactory",
    "create_agent_llm_config",
    "get_litellm_wrapper",
    "validate_azure_config",
    "create_message",
    "create_chat_messages",
    "format_agent_response",
    "handle_litellm_error",
    "get_model_info"
]
