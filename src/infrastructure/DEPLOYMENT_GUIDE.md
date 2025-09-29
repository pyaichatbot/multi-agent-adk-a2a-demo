# Enterprise Multi-Agent System - Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the enterprise multi-agent system with LiteLLM Azure OpenAI integration using Docker Compose.

## Prerequisites

### Required Software
- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Azure OpenAI Account**: With deployed GPT-4o models
- **Google Cloud Account**: For observability (optional)

### Required Credentials
- Azure OpenAI API Key
- Azure OpenAI Endpoint URL
- Google Cloud Project ID (optional)

## Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd multi-agent-adk/src/infrastructure
```

### 2. Configure Environment
```bash
# Copy environment template
cp env.example .env

# Edit environment variables
nano .env
```

### 3. Configure Azure OpenAI
Edit `.env` file with your Azure OpenAI credentials:
```bash
AZURE_API_KEY=your_actual_azure_openai_api_key
AZURE_API_BASE=https://your-resource-name.openai.azure.com/
AZURE_API_VERSION=2024-02-15-preview
```

### 4. Deploy Services
```bash
# Build and start all services
docker-compose up --build -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

## Service Architecture

### Service Ports
- **MCP Server**: http://localhost:8000
- **Orchestrator Agent**: http://localhost:8001
- **Data Search Agent**: http://localhost:8002
- **Reporting Agent**: http://localhost:8003
- **Example Agent**: http://localhost:8004
- **Redis**: localhost:6379

### Service Dependencies
```
Redis → Example Agent
MCP Server → All Agents
Orchestrator → All Agents (via A2A)
```

## Configuration Details

### Environment Variables

#### Azure OpenAI Configuration
```bash
# Required
AZURE_API_KEY=your_azure_openai_api_key
AZURE_API_BASE=https://your-resource.openai.azure.com/
AZURE_API_VERSION=2024-02-15-preview

# Optional: Agent-specific models
ORCHESTRATOR_AZURE_MODEL=gpt-4o
DATA_SEARCH_AZURE_MODEL=gpt-4o
REPORTING_AZURE_MODEL=gpt-4o
EXAMPLE_AGENT_AZURE_MODEL=gpt-4o
```

#### Service Configuration
```bash
# Google Cloud (optional)
GOOGLE_CLOUD_PROJECT=your-gcp-project-id

# Registry Configuration
REGISTRY_URL=redis://redis:6379
AUTO_REGISTER=true

# Fallback Configuration (optional)
ENABLE_FALLBACK=false
OPENAI_API_KEY=your_openai_api_key
```

### Volume Mounts
- **Configuration Files**: Mounted from `./<service>/config`
- **Redis Data**: Persistent volume for registry data

## Service Management

### Starting Services
```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d orchestrator-agent

# Start with logs
docker-compose up
```

### Stopping Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Stop specific service
docker-compose stop orchestrator-agent
```

### Service Health Checks
```bash
# Check service health
curl http://localhost:8000/health  # MCP Server
curl http://localhost:8001/health  # Orchestrator
curl http://localhost:8002/health  # Data Search
curl http://localhost:8003/health  # Reporting
curl http://localhost:8004/health  # Example Agent
```

### Viewing Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f orchestrator-agent

# Last 100 lines
docker-compose logs --tail=100 orchestrator-agent
```

## Testing the Deployment

### 1. Health Check
```bash
# Check all services are healthy
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
```

### 2. Test Orchestrator
```bash
curl -X POST http://localhost:8001/process \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello, can you help me with data analysis?"}'
```

### 3. Test Data Search Agent
```bash
curl -X POST http://localhost:8002/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Find customer data for account 12345"}'
```

### 4. Test Reporting Agent
```bash
curl -X POST http://localhost:8003/report \
  -H "Content-Type: application/json" \
  -d '{"query": "Generate a sales report for Q1 2024"}'
```

### 5. Test Example Agent
```bash
curl -X POST http://localhost:8004/analytics \
  -H "Content-Type: application/json" \
  -d '{"query": "Analyze customer trends and provide insights"}'
```

## Monitoring and Observability

### Service Status
```bash
# Check running containers
docker-compose ps

# Check resource usage
docker stats

# Check service health
docker-compose exec orchestrator-agent curl localhost:8000/health
```

### Logs and Debugging
```bash
# Enable debug logging
export LITELLM_DEBUG=true
export LITELLM_LOG_LEVEL=DEBUG

# Restart services with debug
docker-compose down
docker-compose up --build
```

### Azure OpenAI Integration
```bash
# Test Azure OpenAI connection
docker-compose exec orchestrator-agent python -c "
from adk_shared.litellm_integration import validate_azure_config
print(validate_azure_config())
"
```

## Troubleshooting

### Common Issues

#### 1. Azure OpenAI Connection Issues
```bash
# Check environment variables
docker-compose exec orchestrator-agent env | grep AZURE

# Test Azure OpenAI connection
docker-compose exec orchestrator-agent python -c "
import os
print('Azure API Key:', 'SET' if os.getenv('AZURE_API_KEY') else 'NOT SET')
print('Azure API Base:', os.getenv('AZURE_API_BASE'))
"
```

#### 2. Service Communication Issues
```bash
# Check service connectivity
docker-compose exec orchestrator-agent curl http://mcp-server:8000/health

# Check Redis connectivity
docker-compose exec example-agent redis-cli -h redis ping
```

#### 3. Build Issues
```bash
# Clean build
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### 4. Port Conflicts
```bash
# Check port usage
netstat -tulpn | grep :8000
netstat -tulpn | grep :8001

# Change ports in docker-compose.yml if needed
```

### Debug Commands
```bash
# Enter service container
docker-compose exec orchestrator-agent bash

# Check service logs
docker-compose logs orchestrator-agent

# Check service configuration
docker-compose exec orchestrator-agent cat config/root_agent.yaml
```

## Production Deployment

### Environment Configuration
```bash
# Production environment variables
export ENVIRONMENT=production
export GOOGLE_CLOUD_PROJECT=your-production-project
export AZURE_API_KEY=your-production-key
export AZURE_API_BASE=https://your-production-resource.openai.azure.com/
```

### Security Considerations
- Use secrets management for API keys
- Enable TLS/SSL for production
- Configure firewall rules
- Set up monitoring and alerting

### Scaling
```bash
# Scale specific service
docker-compose up -d --scale orchestrator-agent=3

# Use load balancer for multiple instances
```

## Maintenance

### Updates
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

### Backup
```bash
# Backup Redis data
docker-compose exec redis redis-cli BGSAVE

# Backup configuration files
tar -czf config-backup.tar.gz */config/
```

### Cleanup
```bash
# Remove unused containers and images
docker-compose down
docker system prune -a

# Remove volumes (WARNING: This will delete data)
docker-compose down -v
```

## Support

### Logs Location
- **Application Logs**: `docker-compose logs <service>`
- **System Logs**: `/var/log/docker/`
- **Configuration**: `./<service>/config/`

### Health Monitoring
- **Health Endpoints**: `http://localhost:<port>/health`
- **Metrics**: Available via OpenTelemetry
- **Tracing**: Google Cloud Trace integration

This deployment guide provides comprehensive instructions for deploying and managing the enterprise multi-agent system with LiteLLM Azure OpenAI integration.
