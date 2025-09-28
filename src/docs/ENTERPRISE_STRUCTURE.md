# Enterprise Multi-Agent System - Folder Structure

## Overview

This enterprise structure organizes the multi-agent system into proper microservices with clear separation of concerns, following enterprise best practices.

## Directory Structure

```
src/
├── adk-shared/                          # Shared libraries and utilities
│   ├── __init__.py
│   ├── agent_registry/                  # Dynamic agent registry and service discovery
│   │   └── __init__.py
│   ├── observability/                   # OpenTelemetry tracing and metrics
│   │   └── __init__.py
│   └── security/                        # Authentication and authorization
│       └── __init__.py
│
├── mcp-server/                          # Centralized MCP Tool Server
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── config/
│   │   └── tools.yaml                   # Tool configurations
│   └── src/
│       ├── __init__.py
│       ├── main.py                      # FastAPI application
│       └── server.py                    # MCP server implementation
│
├── orchestrator-agent/                  # Central orchestration service
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── config/
│   │   ├── root_agent.yaml             # Agent configuration
│   │   └── policy.yaml                 # Governance policies
│   └── src/
│       ├── __init__.py
│       ├── main.py                      # FastAPI application
│       └── agent.py                     # Orchestrator implementation
│
├── data-search-agent/                   # Specialized data retrieval agent
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── config/
│   │   └── root_agent.yaml             # Agent configuration
│   └── src/
│       ├── __init__.py
│       ├── main.py                      # FastAPI application
│       └── agent.py                     # Data search implementation
│
├── reporting-agent/                     # Specialized reporting agent
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── config/
│   │   └── root_agent.yaml             # Agent configuration
│   └── src/
│       ├── __init__.py
│       ├── main.py                      # FastAPI application
│       └── agent.py                     # Reporting implementation
│
├── infrastructure/                      # Deployment and infrastructure
│   ├── docker-compose.yml              # Local development setup
│   └── deploy.sh                       # Production deployment script
│
└── docs/                               # Documentation
    └── README.md                        # System documentation
```

## Key Features

### 🏗️ **Microservices Architecture**
- **Independent Services**: Each service can be deployed independently
- **Clear Boundaries**: Well-defined service interfaces and responsibilities
- **Scalable**: Services can be scaled independently based on load

### 🔧 **Enterprise-Grade Features**
- **Observability**: OpenTelemetry integration for tracing, metrics, and logging
- **Security**: JWT authentication and policy-based authorization
- **Configuration**: YAML-driven configuration management
- **Health Checks**: Comprehensive health monitoring for all services

### 🚀 **Production Ready**
- **Docker Support**: Each service has its own Dockerfile
- **Cloud Deployment**: Google Cloud Run deployment scripts
- **Local Development**: Docker Compose for local development
- **Infrastructure as Code**: Terraform and deployment automation

### 📊 **Monitoring & Observability**
- **Distributed Tracing**: End-to-end request tracing across services
- **Metrics Collection**: Custom metrics for agent performance
- **Structured Logging**: JSON logging with correlation IDs
- **Health Monitoring**: Service health checks and status reporting

## Service Responsibilities

### MCP Server (Port 8000)
- **Purpose**: Centralized tool registry for enterprise tools
- **Tools**: Database queries, document search, analytics
- **Features**: Authentication, observability, tool execution

### Orchestrator Agent (Port 8001)
- **Purpose**: Central coordination and request routing
- **Features**: Agent selection, policy enforcement, load balancing
- **Capabilities**: Dynamic routing, governance, audit trails

### Data Search Agent (Port 8002)
- **Purpose**: Specialized data retrieval and search
- **Tools**: Database queries, document search
- **Features**: SQL execution, document indexing, result formatting

### Reporting Agent (Port 8003)
- **Purpose**: Business reporting and analytics
- **Tools**: Analytics, data processing, visualization
- **Features**: Report generation, business insights, data visualization

## Shared Libraries (adk-shared)

### Agent Registry
- **Dynamic Service Discovery**: Redis-based agent registration
- **Load Balancing**: Intelligent agent selection
- **Health Monitoring**: Agent status tracking
- **Capability Matching**: Skill-based routing

### Observability
- **OpenTelemetry Integration**: Distributed tracing
- **Metrics Collection**: Performance monitoring
- **Structured Logging**: JSON logging with context
- **Health Checks**: Service monitoring

### Security
- **JWT Authentication**: Service-to-service authentication
- **Policy Enforcement**: Role-based access control
- **Audit Trails**: Security event logging
- **Data Protection**: Encryption and compliance

## Configuration Management

### Service-Specific Configurations
- **MCP Server**: Tool definitions and parameters
- **Orchestrator**: Agent routing and policy rules
- **Data Agent**: Search capabilities and data access
- **Reporting Agent**: Analytics and visualization settings

### Environment Support
- **Development**: Local development configurations
- **Production**: Cloud deployment settings
- **Security**: Environment-specific security policies
- **Monitoring**: Observability configurations

## Deployment Options

### Local Development
```bash
cd src/infrastructure
docker-compose up -d
```

### Production Deployment
```bash
cd src/infrastructure
./deploy.sh
```

### Individual Service Deployment
```bash
# Deploy specific service
gcloud run deploy service-name --source ./service-directory
```

## Benefits of This Structure

### ✅ **Enterprise Readiness**
- **Scalability**: Independent service scaling
- **Maintainability**: Clear separation of concerns
- **Security**: Comprehensive security framework
- **Observability**: Full system monitoring

### ✅ **Developer Experience**
- **Clear Structure**: Easy to navigate and understand
- **Independent Development**: Services can be developed separately
- **Local Testing**: Complete local development environment
- **Documentation**: Comprehensive guides and examples

### ✅ **Operational Excellence**
- **Health Monitoring**: Service health checks
- **Deployment Automation**: Automated deployment scripts
- **Configuration Management**: Environment-specific configurations
- **Troubleshooting**: Clear debugging and monitoring tools

This enterprise structure provides a solid foundation for a production-ready multi-agent system with enterprise-grade features, security, and observability.
