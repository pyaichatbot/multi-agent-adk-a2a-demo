# LiteLLM Integration for Azure OpenAI

This module provides comprehensive integration between LiteLLM and Azure OpenAI for the multi-agent system. It includes configuration management, model initialization, error handling, and fallback mechanisms.

## Quick Start

### 1. Basic Usage

```python
from adk_shared.litellm_integration import create_agent_llm_config, get_litellm_wrapper

# Create ADK-compatible configuration for an agent
llm_config = create_agent_llm_config('orchestrator')

# Get LiteLLM wrapper for an agent
wrapper = get_litellm_wrapper('data_search')

# Use the wrapper for chat completion
messages = [
    {'role': 'user', 'content': 'Hello, how can you help me?'}
]
response = await wrapper.chat_completion(messages)
```

### 2. Agent Configuration

```python
from adk_shared.litellm_integration import AzureOpenAIConfig, ModelFactory

# Initialize configuration
config = AzureOpenAIConfig()

# Create model factory
factory = ModelFactory(config)

# Get agent-specific configuration
agent_config = factory.create_agent_config('orchestrator')
```

## Components

### AzureOpenAIConfig

Manages Azure OpenAI configuration and environment variables:

```python
from adk_shared.litellm_integration import AzureOpenAIConfig

config = AzureOpenAIConfig()

# Access configuration
api_key = config.api_key
api_base = config.api_base
model = config.get_agent_model('orchestrator')
```

### LiteLLMWrapper

Provides consistent interface for LiteLLM with Azure OpenAI:

```python
from adk_shared.litellm_integration import LiteLLMWrapper

wrapper = LiteLLMWrapper('orchestrator')

# Async chat completion
response = await wrapper.chat_completion(messages)

# Sync chat completion
response = wrapper.chat_completion_sync(messages)
```

### ModelFactory

Factory pattern for creating and managing model instances:

```python
from adk_shared.litellm_integration import ModelFactory

factory = ModelFactory()

# Get wrapper for specific agent
wrapper = factory.get_wrapper('data_search')

# Create ADK configuration
adk_config = factory.create_agent_config('reporting')
```

## Utility Functions

### Configuration Helpers

```python
from adk_shared.litellm_integration import (
    create_agent_llm_config,
    validate_azure_config,
    get_model_info
)

# Create agent configuration
config = create_agent_llm_config('orchestrator')

# Validate configuration
validation = validate_azure_config()

# Get model information
model_info = get_model_info('data_search')
```

### Message Creation

```python
from adk_shared.litellm_integration import (
    create_message,
    create_chat_messages
)

# Create single message
message = create_message('user', 'Hello!')

# Create chat conversation
messages = create_chat_messages(
    system_prompt="You are a helpful assistant",
    user_message="What is the weather?",
    conversation_history=[
        {'role': 'user', 'content': 'Hi'},
        {'role': 'assistant', 'content': 'Hello!'}
    ]
)
```

### Response Handling

```python
from adk_shared.litellm_integration import (
    format_agent_response,
    handle_litellm_error
)

# Format successful response
formatted_response = format_agent_response(response, 'orchestrator')

# Handle errors
error_response = handle_litellm_error(exception, 'data_search')
```

## Configuration

### Environment Variables

The module uses the following environment variables:

```bash
# Required
AZURE_API_KEY=your_azure_openai_api_key
AZURE_API_BASE=https://your-resource.openai.azure.com/
AZURE_API_VERSION=2024-02-15-preview

# Optional
DEFAULT_AZURE_MODEL=gpt-4o
DEFAULT_TEMPERATURE=0.1
DEFAULT_MAX_TOKENS=2000

# Agent-specific models
ORCHESTRATOR_AZURE_MODEL=gpt-4o
DATA_SEARCH_AZURE_MODEL=gpt-4o-mini
REPORTING_AZURE_MODEL=gpt-4o
EXAMPLE_AGENT_AZURE_MODEL=gpt-4o-mini

# Fallback configuration
ENABLE_FALLBACK=false
OPENAI_API_KEY=your_openai_api_key

# Debug settings
LITELLM_DEBUG=false
LITELLM_LOG_LEVEL=INFO
```

### Agent-Specific Configuration

Each agent can have its own model configuration:

```python
# Get agent-specific model
model = config.get_agent_model('orchestrator')  # Returns ORCHESTRATOR_AZURE_MODEL or DEFAULT_AZURE_MODEL

# Get complete agent configuration
agent_config = config.get_agent_config('data_search')
```

## Error Handling

The module provides comprehensive error handling:

```python
try:
    response = await wrapper.chat_completion(messages)
except APIError as e:
    # Handle API errors
    error_response = handle_litellm_error(e, 'orchestrator')
except RateLimitError as e:
    # Handle rate limiting
    logger.warning(f"Rate limit exceeded: {e}")
except Timeout as e:
    # Handle timeouts
    logger.error(f"Request timeout: {e}")
```

## Fallback Mechanism

Enable fallback to OpenAI if Azure OpenAI fails:

```bash
ENABLE_FALLBACK=true
OPENAI_API_KEY=your_openai_api_key
```

```python
# Fallback is automatically handled in the wrapper
response = await wrapper.chat_completion(messages)
# If Azure OpenAI fails and fallback is enabled, it will try OpenAI
```

## Logging

Configure logging for debugging:

```bash
LITELLM_DEBUG=true
LITELLM_LOG_LEVEL=DEBUG
```

```python
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('adk_shared.litellm_integration')
```

## Best Practices

1. **Use the factory pattern**: Create model instances through ModelFactory
2. **Handle errors gracefully**: Always wrap API calls in try-catch blocks
3. **Use async methods**: Prefer async methods for better performance
4. **Configure per agent**: Use agent-specific model configurations
5. **Enable fallback**: Configure fallback for production reliability
6. **Monitor usage**: Track usage statistics and costs

## Examples

### Complete Agent Integration

```python
from adk_shared.litellm_integration import (
    create_agent_llm_config,
    get_litellm_wrapper,
    create_chat_messages
)

class MyAgent:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.llm_config = create_agent_llm_config(agent_name)
        self.wrapper = get_litellm_wrapper(agent_name)
    
    async def process_request(self, query: str):
        messages = create_chat_messages(
            system_prompt="You are a helpful assistant",
            user_message=query
        )
        
        try:
            response = await self.wrapper.chat_completion(messages)
            return response['content']
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return "Sorry, I encountered an error processing your request."
```

### Configuration Validation

```python
from adk_shared.litellm_integration import validate_azure_config

# Validate configuration before starting services
validation = validate_azure_config()

if not validation['valid']:
    print("Configuration errors:")
    for error in validation['errors']:
        print(f"  - {error}")
else:
    print("Configuration is valid!")
```

This module provides a complete solution for integrating LiteLLM with Azure OpenAI across the multi-agent system, with comprehensive error handling, fallback mechanisms, and easy-to-use utilities.
