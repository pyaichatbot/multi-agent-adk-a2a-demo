"""
Model Factory for LiteLLM Integration

Provides a factory pattern for creating and managing LiteLLM model instances
across different agents in the multi-agent system.
"""

import logging
from typing import Dict, Any, Optional
from .azure_config import AzureOpenAIConfig
from .litellm_wrapper import LiteLLMWrapper

logger = logging.getLogger(__name__)


class ModelFactory:
    """Factory for creating and managing LiteLLM model instances"""
    
    def __init__(self, config: Optional[AzureOpenAIConfig] = None):
        """
        Initialize model factory
        
        Args:
            config: Azure OpenAI configuration. If None, creates new instance
        """
        self.config = config or AzureOpenAIConfig()
        self._wrappers: Dict[str, LiteLLMWrapper] = {}
        
        logger.info("Model factory initialized")
    
    def get_wrapper(self, agent_name: str) -> LiteLLMWrapper:
        """
        Get or create LiteLLM wrapper for specific agent
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            LiteLLMWrapper instance for the agent
        """
        if agent_name not in self._wrappers:
            self._wrappers[agent_name] = LiteLLMWrapper(agent_name, self.config)
            logger.info(f"Created new LiteLLM wrapper for agent: {agent_name}")
        
        return self._wrappers[agent_name]
    
    def create_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """
        Create ADK-compatible configuration for agent
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dictionary with ADK-compatible LLM configuration
        """
        wrapper = self.get_wrapper(agent_name)
        model_config = wrapper.get_model_config()
        
        # Convert to ADK-compatible format
        adk_config = {
            'provider': 'litellm',
            'model': model_config['model'],
            'temperature': model_config['temperature'],
            'max_tokens': model_config['max_tokens'],
            'api_key': model_config['api_key'],
            'api_base': model_config['api_base'],
            'api_version': model_config['api_version']
        }
        
        logger.info(f"Created ADK config for agent {agent_name}: {adk_config}")
        return adk_config
    
    def get_available_models(self) -> Dict[str, Any]:
        """
        Get list of available models for different agents
        
        Returns:
            Dictionary mapping agent names to their configured models
        """
        models = {}
        for agent_name in ['orchestrator', 'data_search', 'reporting', 'example_agent']:
            wrapper = self.get_wrapper(agent_name)
            models[agent_name] = {
                'model': wrapper.get_model_config()['model'],
                'temperature': wrapper.get_model_config()['temperature'],
                'max_tokens': wrapper.get_model_config()['max_tokens']
            }
        
        return models
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate configuration for all agents
        
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'agents': {}
        }
        
        try:
            # Test configuration for each agent
            for agent_name in ['orchestrator', 'data_search', 'reporting', 'example_agent']:
                try:
                    wrapper = self.get_wrapper(agent_name)
                    config = wrapper.get_model_config()
                    
                    # Basic validation
                    required_fields = ['model', 'api_key', 'api_base', 'api_version']
                    missing_fields = [field for field in required_fields if not config.get(field)]
                    
                    if missing_fields:
                        validation_results['errors'].append(f"Missing fields for {agent_name}: {missing_fields}")
                        validation_results['valid'] = False
                    else:
                        validation_results['agents'][agent_name] = {
                            'status': 'valid',
                            'model': config['model'],
                            'config': config
                        }
                        
                except Exception as e:
                    validation_results['errors'].append(f"Configuration error for {agent_name}: {str(e)}")
                    validation_results['valid'] = False
                    validation_results['agents'][agent_name] = {
                        'status': 'error',
                        'error': str(e)
                    }
            
            # Check for warnings
            if self.config.enable_fallback and not self.config.openai_api_key:
                validation_results['warnings'].append("Fallback enabled but OpenAI API key not provided")
            
            logger.info(f"Configuration validation completed: {validation_results}")
            
        except Exception as e:
            validation_results['valid'] = False
            validation_results['errors'].append(f"Validation failed: {str(e)}")
            logger.error(f"Configuration validation failed: {e}")
        
        return validation_results
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """
        Get usage summary for all agents
        
        Returns:
            Dictionary with usage statistics
        """
        summary = {
            'total_agents': len(self._wrappers),
            'agents': {},
            'timestamp': None
        }
        
        for agent_name, wrapper in self._wrappers.items():
            try:
                usage_stats = wrapper.get_usage_stats()
                summary['agents'][agent_name] = usage_stats
            except Exception as e:
                logger.error(f"Error getting usage stats for {agent_name}: {e}")
                summary['agents'][agent_name] = {'error': str(e)}
        
        from datetime import datetime
        summary['timestamp'] = datetime.now().isoformat()
        
        return summary
    
    def cleanup(self):
        """Cleanup resources and close connections"""
        logger.info("Cleaning up model factory resources")
        self._wrappers.clear()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
