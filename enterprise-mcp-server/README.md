# 🎯 SageAI-Focused Enterprise MCP Server

## **Enterprise-Grade Model Context Protocol Server with Policy Engine**

A production-ready MCP server focused on SageAI platform integration with comprehensive governance, policy enforcement, and compliance monitoring.

---

## **🏗️ Architecture Overview**

### **Core Components**
- **Policy Engine**: YAML + Database policy management
- **Policy Enforcement**: Real-time governance and access control
- **SageAI Integration**: Platform agents and tools as MCP tools
- **Compliance Monitoring**: Audit trails and metrics
- **Rate Limiting**: Multi-level rate limiting with Redis
- **Observability**: Enterprise logging, metrics, and tracing

### **Tool Categories**
```
SageAI Tools (6):     System Tools (4):     Policy Tools (5):
├── list_sageai_agents    ├── get_system_info        ├── get_compliance_metrics
├── get_sageai_agent_     ├── check_system_health    ├── get_audit_trail
├── invoke_sageai_agent   ├── list_tools            ├── get_user_accessible_tools
├── list_sageai_tools     └── get_tool_info         ├── reload_policies
├── get_sageai_tool_      └── get_policy_status
└── execute_sageai_tool
```

---

## **🔐 Policy Engine & Governance**

### **Policy Configuration (YAML)**
```yaml
# sageai_policies.yaml
sageai_governance:
  enabled: true
  policy_engine: "yaml_based"
  default_policy: "deny"
  
  agents:
    allow_list: ["agent_001", "agent_003", "agent_005"]
    deny_list: ["agent_002", "agent_004"]
    restrictions:
      agent_001:
        max_execution_time: 300
        allowed_parameters: ["format", "output_type"]
        rate_limit: 5  # per hour
        
  tools:
    allow_list: ["tool_analytics", "tool_database"]
    restrictions:
      tool_analytics:
        max_execution_time: 180
        allowed_parameters: ["data_source", "analysis_type"]
        
  users:
    role_based_access:
      admin: { agents: ["*"], tools: ["*"] }
      agent_user: { agents: ["agent_001", "agent_003"] }
      tool_user: { tools: ["tool_analytics", "tool_database"] }
```

### **Policy Sources (Priority Order)**
1. **Database** (SageAI SQL Server/CosmosDB) - *Highest Priority*
2. **YAML Configuration** - *Fallback*
3. **Default Policies** - *Lowest Priority*

### **Governance Features**
- ✅ **Access Control**: Role-based permissions
- ✅ **Resource Restrictions**: Per-agent/tool limits
- ✅ **Rate Limiting**: Global, per-user, per-resource
- ✅ **Parameter Validation**: Allowed/forbidden parameters
- ✅ **Execution Limits**: Time, memory, CPU constraints
- ✅ **Audit Trail**: Complete activity logging
- ✅ **Compliance Metrics**: Real-time monitoring

---

## **🚀 Quick Start**

### **1. Installation**
```bash
cd enterprise-mcp-server
pip install -r requirements.txt
```

### **2. Configuration**
```bash
# Copy environment template
cp env.example .env

# Edit configuration
nano .env
```

### **3. Policy Setup**
```bash
# Default policies will be created automatically
# Edit sageai_policies.yaml for custom policies
nano sageai_policies.yaml
```

### **4. Start Server**

#### **Local Development (STDIO Transport)**
```bash
# For local development with STDIO transport
python run_local.py
```

#### **Remote/Kubernetes Deployment (SSE Transport)**
```bash
# For remote deployment with SSE transport
python run_remote.py
```

#### **Docker Deployment**
```bash
# Build and run with Docker (SSE mode)
docker build -t enterprise-mcp-server .
docker run -p 8000:8000 enterprise-mcp-server
```

---

## **📡 Dual Transport Architecture**

The Enterprise MCP Server supports **two transport modes** to accommodate different deployment scenarios:

### **STDIO Transport (Local Development)**
- **Purpose**: Direct process communication for local development
- **Communication**: stdin/stdout pipes
- **Use Cases**: 
  - Local development and testing
  - Direct MCP client integration
  - Development environments
- **Configuration**: `MCP_TRANSPORT=stdio`
- **Script**: `python run_local.py`

### **SSE Transport (Remote/Kubernetes)**
- **Purpose**: HTTP-based communication for remote deployment
- **Communication**: Server-Sent Events over HTTP
- **Use Cases**:
  - Kubernetes cluster deployment
  - Remote server access
  - Production environments
  - Load-balanced deployments
- **Configuration**: `MCP_TRANSPORT=sse`
- **Endpoint**: `http://host:port/sse`
- **Script**: `python run_remote.py`

### **Transport Selection Logic**
```python
# Automatic transport selection based on environment
transport = os.getenv("MCP_TRANSPORT", "stdio")

if transport == "sse":
    # Remote deployment with HTTP endpoints
    mcp.run(transport="sse", host=host, port=port)
else:
    # Local development with STDIO
    mcp.run()
```

### **Deployment Scenarios**

| Scenario | Transport | Configuration | Access Method |
|----------|-----------|---------------|---------------|
| **Local Development** | STDIO | `MCP_TRANSPORT=stdio` | Direct process communication |
| **Docker Local** | SSE | `MCP_TRANSPORT=sse` | `http://localhost:8000/sse` |
| **Kubernetes** | SSE | `MCP_TRANSPORT=sse` | `http://service:port/sse` |
| **Production** | SSE | `MCP_TRANSPORT=sse` | `https://domain.com/sse` |

---

## **🔧 Configuration**

### **Environment Variables**
```bash
# MCP Server Transport
MCP_TRANSPORT=stdio          # stdio for local, sse for remote
MCP_HOST=localhost           # For SSE transport
MCP_PORT=8000               # For SSE transport

# SageAI Integration
SAGEAI_BASE_URL=https://sageai.platform.com/api/v1
SAGEAI_AUTH_PROXY_URL=https://auth.sageai.platform.com
SAGEAI_TIMEOUT=30
SAGEAI_MAX_RETRIES=3

# Policy Engine
POLICY_ENGINE_ENABLED=true
POLICY_SOURCE_PRIORITY=database,yaml

# Rate Limiting
REDIS_URL=redis://localhost:6379
RATE_LIMIT_ENABLED=true

# Observability
LOG_LEVEL=INFO
METRICS_ENABLED=true
```

### **Transport Modes**

#### **STDIO Transport (Local Development)**
- **Use Case**: Local development, direct process communication
- **Configuration**: `MCP_TRANSPORT=stdio`
- **Access**: Direct process communication via stdin/stdout
- **Script**: `python run_local.py`

#### **SSE Transport (Remote/Kubernetes)**
- **Use Case**: Remote deployment, Kubernetes clusters, HTTP-based communication
- **Configuration**: `MCP_TRANSPORT=sse`
- **Access**: HTTP endpoint at `http://host:port/sse`
- **Script**: `python run_remote.py`

### **Policy Configuration**
```yaml
# sageai_policies.yaml
sageai_governance:
  enabled: true
  policy_engine: "yaml_based"
  
  # Agent policies
  agents:
    default_policy: "deny"
    allow_list: ["agent_001", "agent_003"]
    restrictions:
      agent_001:
        max_execution_time: 300
        allowed_parameters: ["format", "output_type"]
        rate_limit: 5
        
  # Tool policies  
  tools:
    default_policy: "deny"
    allow_list: ["tool_analytics", "tool_database"]
    restrictions:
      tool_analytics:
        max_execution_time: 180
        allowed_parameters: ["data_source", "analysis_type"]
        
  # User roles
  users:
    role_based_access:
      admin: { agents: ["*"], tools: ["*"] }
      agent_user: { agents: ["agent_001"] }
      tool_user: { tools: ["tool_analytics"] }
```

---

## **🛠️ MCP Tools**

### **SageAI Agent Tools**
```python
# List available SageAI agents
list_sageai_agents(token: str) -> str

# Get agent details
get_sageai_agent_details(agent_id: str, token: str) -> str

# Invoke SageAI agent
invoke_sageai_agent(agent_id: str, input_data: dict, token: str, parameters: dict = None) -> str
```

### **SageAI Tool Tools**
```python
# List available SageAI tools
list_sageai_tools(token: str) -> str

# Get tool details
get_sageai_tool_details(tool_id: str, token: str) -> str

# Execute SageAI tool
execute_sageai_tool(tool_id: str, parameters: dict, token: str) -> str
```

### **System Tools**
```python
# System information
get_system_info() -> str
check_system_health() -> str
list_tools() -> str
get_tool_info(tool_name: str) -> str
```

### **Policy & Compliance Tools**
```python
# Compliance monitoring
get_compliance_metrics() -> str
get_audit_trail(limit: int = 50) -> str
get_user_accessible_tools(token: str) -> str
reload_policies() -> str
get_policy_status() -> str
```

---

## **🔐 Security & Governance**

### **Authentication Flow**
```
1. User provides SageAI token
2. Token validated via SageAI auth proxy
3. User permissions retrieved
4. Policy evaluation performed
5. Access granted/denied based on policies
```

### **Policy Enforcement Points**
- **Tool Discovery**: Filter available tools per user
- **Tool Execution**: Validate before execution
- **Parameter Validation**: Check allowed parameters
- **Rate Limiting**: Enforce usage limits
- **Execution Limits**: Time and resource constraints

### **Compliance Monitoring**
- **Real-time Metrics**: Success rates, violations, latency
- **Audit Trail**: Complete activity logging
- **Violation Tracking**: By type, user, resource
- **Policy Status**: Engine status and configuration

---

## **📊 Observability & Monitoring**

### **Metrics**
- **Policy Metrics**: Compliance rates, violations
- **Execution Metrics**: Success rates, latency
- **Rate Limiting**: Hit rates, throttling
- **SageAI Integration**: API calls, agent invocations

### **Logging**
- **Structured Logging**: JSON format with correlation IDs
- **Policy Decisions**: All access control decisions
- **Violations**: Security and policy violations
- **Performance**: Execution times and resource usage

### **Health Checks**
- **System Health**: Overall system status
- **Policy Engine**: Configuration and status
- **SageAI Connectivity**: Platform availability
- **Rate Limiting**: Redis connectivity

---

## **🚀 Production Deployment**

### **Docker Deployment**

#### **SSE Mode (Remote/Kubernetes)**
```bash
# Build image
docker build -t enterprise-mcp-server .

# Run with SSE transport
docker run -d \
  --name mcp-server \
  -p 8000:8000 \
  -e MCP_TRANSPORT=sse \
  -e MCP_HOST=0.0.0.0 \
  -e MCP_PORT=8000 \
  -e SAGEAI_BASE_URL=https://sageai.platform.com/api/v1 \
  -e REDIS_URL=redis://redis:6379 \
  enterprise-mcp-server
```

#### **STDIO Mode (Local Development)**
```bash
# Run locally with STDIO transport
python run_local.py
```

### **Kubernetes Deployment**
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: enterprise-mcp-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: enterprise-mcp-server
  template:
    metadata:
      labels:
        app: enterprise-mcp-server
    spec:
      containers:
      - name: mcp-server
        image: enterprise-mcp-server:latest
        ports:
        - containerPort: 8000
        env:
        - name: MCP_TRANSPORT
          value: "sse"
        - name: MCP_HOST
          value: "0.0.0.0"
        - name: MCP_PORT
          value: "8000"
        - name: SAGEAI_BASE_URL
          value: "https://sageai.platform.com/api/v1"
        - name: REDIS_URL
          value: "redis://redis-service:6379"
```

### **Transport Mode Selection**

#### **For Local Development:**
```bash
# Use STDIO transport
export MCP_TRANSPORT=stdio
python run_local.py
```

#### **For Remote/Kubernetes Deployment:**
```bash
# Use SSE transport
export MCP_TRANSPORT=sse
export MCP_HOST=0.0.0.0
export MCP_PORT=8000
python run_remote.py
```

---

## **🔧 Troubleshooting**

### **Common Issues**

#### **Transport Mode Issues**
```bash
# Check transport mode
echo $MCP_TRANSPORT

# For STDIO mode (local development)
export MCP_TRANSPORT=stdio
python run_local.py

# For SSE mode (remote deployment)
export MCP_TRANSPORT=sse
export MCP_HOST=0.0.0.0
export MCP_PORT=8000
python run_remote.py
```

#### **SSE Endpoint Not Accessible**
```bash
# Test SSE endpoint
curl -f http://localhost:8000/sse

# Check if server is running
docker ps | grep enterprise-mcp-server

# Check server logs
docker logs enterprise-mcp-server
```

#### **Policy Engine Not Loading**
```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('sageai_policies.yaml'))"

# Check file permissions
ls -la sageai_policies.yaml
```

#### **SageAI Integration Failing**
```bash
# Test SageAI connectivity
curl -H "Authorization: Bearer $SAGEAI_TOKEN" \
  $SAGEAI_BASE_URL/agents

# Check auth proxy
curl -H "Authorization: Bearer $SAGEAI_TOKEN" \
  $SAGEAI_AUTH_PROXY_URL/validate
```

#### **Rate Limiting Issues**
```bash
# Check Redis connectivity
redis-cli ping

# Check rate limit status (SSE mode)
curl http://localhost:8000/health
```

### **Debug Mode**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export POLICY_ENGINE_DEBUG=true

# Start server
python src/main.py
```

---

## **📈 Performance & Scaling**

### **Performance Characteristics**
- **Policy Evaluation**: < 10ms per request
- **SageAI API Calls**: 3 retries with exponential backoff
- **Rate Limiting**: Redis-backed, sub-millisecond
- **Tool Execution**: Policy-enforced with time limits

### **Scaling Considerations**
- **Horizontal Scaling**: Stateless design supports multiple instances
- **Redis Clustering**: For high-availability rate limiting
- **Database Policies**: For dynamic policy management
- **Load Balancing**: Round-robin or least-connections

---

## **🔒 Security Best Practices**

### **Token Management**
- **SageAI Tokens**: Validated via auth proxy
- **Token Caching**: 5-minute TTL for performance
- **Secure Storage**: Environment variables or secrets

### **Policy Security**
- **Default Deny**: All access denied by default
- **Principle of Least Privilege**: Minimal required permissions
- **Audit Logging**: Complete activity trail
- **Violation Alerts**: Real-time security monitoring

### **Network Security**
- **TLS/SSL**: Encrypted communication
- **CORS Configuration**: Restricted origins
- **Rate Limiting**: DDoS protection
- **Input Validation**: Parameter sanitization

---

## **📚 API Reference**

### **MCP Tool Parameters**
```python
# SageAI Agent Tools
list_sageai_agents(token: str) -> str
get_sageai_agent_details(agent_id: str, token: str) -> str
invoke_sageai_agent(agent_id: str, input_data: dict, token: str, parameters: dict = None) -> str

# SageAI Tool Tools  
list_sageai_tools(token: str) -> str
get_sageai_tool_details(tool_id: str, token: str) -> str
execute_sageai_tool(tool_id: str, parameters: dict, token: str) -> str

# Policy & Compliance
get_compliance_metrics() -> str
get_audit_trail(limit: int = 50) -> str
get_user_accessible_tools(token: str) -> str
reload_policies() -> str
get_policy_status() -> str
```

### **Response Formats**
```json
{
  "success": true,
  "data": {...},
  "timestamp": "2024-01-01T00:00:00Z",
  "execution_time": 0.123,
  "policy_decision": {
    "allowed": true,
    "reason": "Access granted",
    "restrictions": {...}
  }
}
```

---

## **🎯 Enterprise Features**

### **✅ Production Ready**
- **Zero-Configuration**: Auto-discovery of tools and policies
- **Enterprise Security**: Multi-layer access control
- **Compliance**: Complete audit trail and monitoring
- **Scalability**: Horizontal scaling with Redis clustering
- **Observability**: Comprehensive logging and metrics

### **✅ SageAI Integration**
- **Real-time Platform**: Live SageAI agent and tool access
- **Retry Logic**: 3 attempts with exponential backoff
- **Response Normalization**: Consistent API responses
- **Token Validation**: Secure authentication flow

### **✅ Policy Engine**
- **YAML Configuration**: Human-readable policy definitions
- **Database Integration**: Dynamic policy management
- **Role-Based Access**: Granular permission control
- **Real-time Enforcement**: Policy decisions in < 10ms

### **✅ Governance & Compliance**
- **Audit Trail**: Complete activity logging
- **Violation Tracking**: Security and policy violations
- **Compliance Metrics**: Real-time monitoring
- **Policy Status**: Engine health and configuration

---

## **🚀 Getting Started**

### **Quick Start Options**

#### **Option 1: Local Development (STDIO)**
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp env.example .env

# 3. Start with STDIO transport
python run_local.py
```

#### **Option 2: Remote Deployment (SSE)**
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp env.example .env

# 3. Start with SSE transport
python run_remote.py
```

#### **Option 3: Docker Deployment**
```bash
# 1. Build Docker image
docker build -t enterprise-mcp-server .

# 2. Run with SSE transport
docker run -p 8000:8000 enterprise-mcp-server
```

### **Testing Your Setup**

#### **STDIO Mode (Local)**
- Use MCP client with direct process communication
- No HTTP endpoints required

#### **SSE Mode (Remote)**
- Test SSE endpoint: `curl -f http://localhost:8000/sse`
- Use MCP client with HTTP transport
- Access via `http://host:port/sse`

**🎯 This MCP server provides enterprise-grade SageAI platform integration with comprehensive governance, policy enforcement, and compliance monitoring for production environments.**