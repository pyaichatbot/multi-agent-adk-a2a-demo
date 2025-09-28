# Azure OpenAI Setup Guide

## Overview
This guide explains how to configure Azure OpenAI credentials for the multi-agent system using LiteLLM integration.

## Quick Setup

### 1. Copy Environment Template
```bash
cp env.template .env
```

### 2. Configure Azure OpenAI Credentials
Edit the `.env` file with your Azure OpenAI credentials:

```bash
# Required Azure OpenAI Configuration
AZURE_API_KEY=your_actual_azure_openai_api_key
AZURE_API_BASE=https://your-resource-name.openai.azure.com/
AZURE_API_VERSION=2024-02-15-preview
```

## Detailed Configuration

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_API_KEY` | Your Azure OpenAI API key | `abc123...` |
| `AZURE_API_BASE` | Your Azure OpenAI endpoint URL | `https://my-resource.openai.azure.com/` |
| `AZURE_API_VERSION` | API version to use | `2024-02-15-preview` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEFAULT_AZURE_MODEL` | Default model for all agents | `gpt-4o` |
| `DEFAULT_TEMPERATURE` | Default temperature setting | `0.1` |
| `DEFAULT_MAX_TOKENS` | Default max tokens | `2000` |
| `ENABLE_FALLBACK` | Enable OpenAI fallback | `false` |
| `LITELLM_LOG_LEVEL` | LiteLLM logging level | `INFO` |

### Agent-Specific Model Configuration

You can configure different models for different agents:

```bash
# Agent-specific model overrides
ORCHESTRATOR_AZURE_MODEL=gpt-4o
DATA_SEARCH_AZURE_MODEL=gpt-4o-mini
REPORTING_AZURE_MODEL=gpt-4o
EXAMPLE_AGENT_AZURE_MODEL=gpt-4o-mini
```

## Azure OpenAI Resource Setup

### 1. Create Azure OpenAI Resource
1. Go to [Azure Portal](https://portal.azure.com)
2. Create a new "Azure OpenAI" resource
3. Note your resource name and endpoint URL

### 2. Deploy Models
1. Go to Azure OpenAI Studio
2. Deploy the models you want to use (e.g., GPT-4o, GPT-4o-mini)
3. Note the deployment names

### 3. Get API Key
1. In Azure OpenAI Studio, go to "Keys and Endpoint"
2. Copy your API key
3. Copy your endpoint URL

## Environment File Structure

```
multi-agent-adk/
├── .env                    # Your actual environment file (not in git)
├── env.template           # Template file (in git)
├── src/
│   ├── orchestrator-agent/
│   ├── data-search-agent/
│   ├── reporting-agent/
│   └── example-agent/
```

## Security Notes

- **Never commit `.env` files to git**
- The `.env` file is already in `.gitignore`
- Use environment variables in production
- Rotate API keys regularly

## Testing Configuration

After setting up your environment, test the configuration:

```bash
# Test Azure OpenAI connection
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('Azure API Key:', 'SET' if os.getenv('AZURE_API_KEY') else 'NOT SET')
print('Azure API Base:', os.getenv('AZURE_API_BASE'))
"
```

## Troubleshooting

### Common Issues

1. **Invalid API Key**: Verify your Azure OpenAI API key
2. **Wrong Endpoint**: Ensure your `AZURE_API_BASE` includes the full URL
3. **Model Not Deployed**: Check that your model is deployed in Azure OpenAI Studio
4. **Version Mismatch**: Use the correct `AZURE_API_VERSION`

### Debug Mode

Enable debug logging:
```bash
LITELLM_DEBUG=true
LITELLM_LOG_LEVEL=DEBUG
```

## Production Deployment

For production environments, use environment variables instead of `.env` files:

```bash
export AZURE_API_KEY="your-production-key"
export AZURE_API_BASE="https://your-production-resource.openai.azure.com/"
export AZURE_API_VERSION="2024-02-15-preview"
```

## Next Steps

After configuring your environment:
1. Run the services to test Azure OpenAI integration
2. Monitor logs for any configuration issues
3. Adjust model settings based on your requirements
