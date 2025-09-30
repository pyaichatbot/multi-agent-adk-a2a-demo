# Enterprise MCP Server Architecture

## **🏗️ System Architecture Diagram**

```mermaid
graph TB
    subgraph "Enterprise MCP Server"
        MCP[Main Application]
        OBS[Simple Observability]
        AUTH[SageAI Authentication]
        RATE[Rate Limiter]
        MCP_SERVER[FastMCP Server]
    end
    
    subgraph "Core Services"
        REDIS[(Redis Cache)]
        MCP_SERVER
    end
    
    subgraph "SageAI Integration"
        SAGEAI_CLIENT[SageAI Client]
        AGENT_TOOLS[Agent Tools]
        TOOL_TOOLS[Tool Tools]
        SAGEAI_API[SageAI Platform API]
    end
    
    subgraph "Optional Telemetry"
        OTEL[OpenTelemetry]
        JAEGER[Jaeger Tracing]
        PROMETHEUS[Prometheus Metrics]
    end
    
    subgraph "External Services"
        SAGEAI_AUTH[SageAI Auth Proxy]
        SAGEAI_PLATFORM[SageAI Platform]
    end
    
    MCP --> OBS
    MCP --> AUTH
    MCP --> RATE
    MCP --> MCP_SERVER
    
    AUTH --> SAGEAI_AUTH
    SAGEAI_CLIENT --> SAGEAI_API
    SAGEAI_API --> SAGEAI_PLATFORM
    
    AGENT_TOOLS --> SAGEAI_CLIENT
    TOOL_TOOLS --> SAGEAI_CLIENT
    
    RATE --> REDIS
    AUTH --> REDIS
    
    OBS --> OTEL
    OTEL --> JAEGER
    OTEL --> PROMETHEUS
    
    MCP_SERVER --> AGENT_TOOLS
    MCP_SERVER --> TOOL_TOOLS
```

## **📊 Tool Categories**

```mermaid
pie title MCP Tools Distribution
    "Database Tools" : 3
    "Analytics Tools" : 4
    "Document Tools" : 4
    "System Tools" : 4
    "SageAI Agent Tools" : 3
    "SageAI Tool Tools" : 3
```

## **🔄 SageAI Integration Flow**

```mermaid
sequenceDiagram
    participant User
    participant MCP as MCP Server
    participant Auth as SageAI Auth
    participant Client as SageAI Client
    participant Platform as SageAI Platform
    
    User->>MCP: Tool Call (with token)
    MCP->>Auth: Validate Token
    Auth-->>MCP: User Info & Permissions
    MCP->>Client: API Call (with retry logic)
    Client->>Platform: HTTP Request
    Platform-->>Client: Response
    Client-->>MCP: Normalized Result
    MCP-->>User: Tool Response
```

## **🔐 Security & Permissions**

```mermaid
graph LR
    subgraph "Authentication Flow"
        TOKEN[User Token]
        AUTH_PROXY[SageAI Auth Proxy]
        USER_INFO[User Info & Roles]
        PERMISSIONS[Permission Mapping]
    end
    
    subgraph "Permission Types"
        AGENT_PERM[can_invoke_agents]
        TOOL_PERM[can_execute_tools]
        ANALYTICS_PERM[can_access_analytics]
        DB_PERM[can_access_database]
        ADMIN_PERM[is_admin]
    end
    
    TOKEN --> AUTH_PROXY
    AUTH_PROXY --> USER_INFO
    USER_INFO --> PERMISSIONS
    PERMISSIONS --> AGENT_PERM
    PERMISSIONS --> TOOL_PERM
    PERMISSIONS --> ANALYTICS_PERM
    PERMISSIONS --> DB_PERM
    PERMISSIONS --> ADMIN_PERM
```

## **🔄 Retry Logic Flow**

```mermaid
flowchart TD
    START[Start Execution]
    ATTEMPT[Attempt N]
    SUCCESS{Success?}
    RETRY{Retry Needed?}
    WAIT[Wait: 2^N seconds]
    FAIL[Return Error]
    SUCCESS_END[Return Success]
    
    START --> ATTEMPT
    ATTEMPT --> SUCCESS
    SUCCESS -->|Yes| SUCCESS_END
    SUCCESS -->|No| RETRY
    RETRY -->|Yes| WAIT
    RETRY -->|No| FAIL
    WAIT --> ATTEMPT
```

## **📈 Observability Stack**

```mermaid
graph TB
    subgraph "Application Layer"
        APP[Enterprise MCP Server]
        LOGS[Structured Logging]
    end
    
    subgraph "Optional Telemetry"
        OTEL[OpenTelemetry]
        TRACES[Distributed Traces]
        METRICS[Custom Metrics]
    end
    
    subgraph "External Observability"
        JAEGER[Jaeger]
        PROMETHEUS[Prometheus]
        GRAFANA[Grafana]
    end
    
    APP --> LOGS
    APP --> OTEL
    OTEL --> TRACES
    OTEL --> METRICS
    TRACES --> JAEGER
    METRICS --> PROMETHEUS
    JAEGER --> GRAFANA
    PROMETHEUS --> GRAFANA
```
