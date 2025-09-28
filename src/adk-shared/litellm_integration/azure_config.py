"""
Azure OpenAI Configuration Management

Handles loading and validation of Azure OpenAI configuration from environment variables
and provides consistent configuration across all agents.
"""

import os
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class AzureOpenAIConfig:
    """Manages Azure OpenAI configuration and environment variables"""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize Azure OpenAI configuration
        
        Args:
            env_file: Optional path to .env file. If None, uses default .env file
        """
        self._load_environment(env_file)
        self._validate_configuration()
    
    def _load_environment(self, env_file: Optional[str] = None):
        """Load environment variables from .env file"""
        try:
            if env_file:
                load_dotenv(env_file)
            else:
                load_dotenv()
            logger.info("Environment variables loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load .env file: {e}")
    
    def _validate_configuration(self):
        """Validate that required Azure OpenAI configuration is present"""
        required_vars = ['AZURE_API_KEY', 'AZURE_API_BASE', 'AZURE_API_VERSION']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
        
        logger.info("Azure OpenAI configuration validated successfully")
    
    @property
    def api_key(self) -> str:
        """Get Azure OpenAI API key"""
        return os.getenv('AZURE_API_KEY')
    
    @property
    def api_base(self) -> str:
        """Get Azure OpenAI API base URL"""
        return os.getenv('AZURE_API_BASE')
    
    @property
    def api_version(self) -> str:
        """Get Azure OpenAI API version"""
        return os.getenv('AZURE_API_VERSION')
    
    @property
    def default_model(self) -> str:
        """Get default Azure OpenAI model"""
        return os.getenv('DEFAULT_AZURE_MODEL', 'gpt-4o')
    
    @property
    def default_temperature(self) -> float:
        """Get default temperature setting"""
        return float(os.getenv('DEFAULT_TEMPERATURE', '0.1'))
    
    @property
    def default_max_tokens(self) -> int:
        """Get default max tokens setting"""
        return int(os.getenv('DEFAULT_MAX_TOKENS', '2000'))
    
    def get_agent_model(self, agent_name: str) -> str:
        """
        Get model configuration for specific agent
        
        Args:
            agent_name: Name of the agent (e.g., 'orchestrator', 'data_search')
            
        Returns:
            Model name for the agent
        """
        # Map agent names to environment variable names
        agent_mapping = {
            'orchestrator': 'ORCHESTRATOR_AZURE_MODEL',
            'data_search': 'DATA_SEARCH_AZURE_MODEL', 
            'reporting': 'REPORTING_AZURE_MODEL',
            'example_agent': 'EXAMPLE_AGENT_AZURE_MODEL'
        }
        
        env_var = agent_mapping.get(agent_name.lower())
        if env_var and os.getenv(env_var):
            return os.getenv(env_var)
        
        return self.default_model
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """
        Get complete configuration for specific agent
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dictionary with agent-specific configuration
        """
        return {
            'model': self.get_agent_model(agent_name),
            'temperature': self.default_temperature,
            'max_tokens': self.default_max_tokens,
            'api_key': self.api_key,
            'api_base': self.api_base,
            'api_version': self.api_version
        }
    
    def get_litellm_config(self, agent_name: str) -> Dict[str, Any]:
        """
        Get LiteLLM-compatible configuration for agent
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dictionary with LiteLLM configuration
        """
        config = self.get_agent_config(agent_name)
        
        # Convert to LiteLLM format
        return {
            'model': f"azure/{config['model']}",
            'temperature': config['temperature'],
            'max_tokens': config['max_tokens'],
            'api_key': config['api_key'],
            'api_base': config['api_base'],
            'api_version': config['api_version']
        }
    
    @property
    def enable_fallback(self) -> bool:
        """Check if OpenAI fallback is enabled"""
        return os.getenv('ENABLE_FALLBACK', 'false').lower() == 'true'
    
    @property
    def openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key for fallback"""
        return os.getenv('OPENAI_API_KEY') if self.enable_fallback else None
    
    @property
    def debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        return os.getenv('LITELLM_DEBUG', 'false').lower() == 'true'
    
    @property
    def log_level(self) -> str:
        """Get LiteLLM log level"""
        return os.getenv('LITELLM_LOG_LEVEL', 'INFO')
    
    def get_retry_config(self) -> Dict[str, Any]:
        """Get retry and timeout configuration"""
        return {
            'max_retries': int(os.getenv('MAX_RETRIES', '3')),
            'retry_delay': float(os.getenv('RETRY_DELAY', '1.0')),
            'timeout': float(os.getenv('TIMEOUT', '30.0'))
        }
