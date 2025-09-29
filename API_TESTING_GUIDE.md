# Enterprise Multi-Agent System - API Testing Guide

This guide provides comprehensive curl commands for testing all services in the enterprise multi-agent system. All commands are formatted for Windows Command Prompt.

## Service Overview

| Service | Port | Description |
|---------|------|-------------|
| MCP Server | 8000 | Centralized tool registry |
| Orchestrator Agent | 8001 | Central orchestration |
| Data Search Agent | 8002 | Data search and retrieval |
| Reporting Agent | 8003 | Business reporting and analytics |
| Example Agent | 8004 | Custom analytics with auto-registration |
| Redis | 6379 | Agent registry backend |

## Prerequisites

1. **Start all services:**
   ```cmd
   cd src\infrastructure
   docker-compose up -d
   ```

2. **Verify services are running:**
   ```cmd
   docker-compose ps
   ```

3. **Get authentication token** (if required):
   ```cmd
   curl -X POST http://localhost:8000/auth/token -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"password\"}"
   ```

---

## 1. MCP Server (Port 8000)

### Health Check
```cmd
curl -X GET http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "mcp-server",
  "tools_available": 5
}
```

### List Available Tools
```cmd
curl -X GET http://localhost:8000/tools -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Expected Response:**
```json
{
  "tools": [
    {
      "name": "query_database",
      "description": "Execute SQL queries on enterprise databases"
    },
    {
      "name": "search_documents",
      "description": "Search through enterprise document repositories"
    },
    {
      "name": "run_analytics",
      "description": "Execute business analytics and reporting"
    },
    {
      "name": "generate_report",
      "description": "Generate formatted business reports"
    },
    {
      "name": "data_visualization",
      "description": "Create data visualizations and charts"
    }
  ]
}
```

### Execute Tool - Database Query
```cmd
curl -X POST http://localhost:8000/execute -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_TOKEN_HERE" -d "{\"tool_name\":\"query_database\",\"parameters\":{\"query\":\"SELECT COUNT(*) FROM users\",\"database\":\"enterprise_db\"}}"
```

### Execute Tool - Document Search
```cmd
curl -X POST http://localhost:8000/execute -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_TOKEN_HERE" -d "{\"tool_name\":\"search_documents\",\"parameters\":{\"query\":\"quarterly sales report\",\"repository\":\"enterprise_docs\"}}"
```

### Execute Tool - Analytics
```cmd
curl -X POST http://localhost:8000/execute -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_TOKEN_HERE" -d "{\"tool_name\":\"run_analytics\",\"parameters\":{\"analysis_type\":\"sales_trends\",\"date_range\":\"2024-01-01 to 2024-12-31\"}}"
```

---

## 2. Orchestrator Agent (Port 8001)

### Health Check
```cmd
curl -X GET http://localhost:8001/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "orchestrator-agent",
  "agents_available": 3
}
```

### List Available Agents (Service Discovery)
```cmd
curl -X GET http://localhost:8001/agents
```

**Expected Response:**
```json
{
  "agents": [
    {
      "name": "DataSearchAgent",
      "capabilities": ["database queries", "document search", "data retrieval"]
    },
    {
      "name": "ReportingAgent", 
      "capabilities": ["report generation", "analytics", "business insights"]
    },
    {
      "name": "ExampleAgent",
      "capabilities": ["custom analytics", "data processing", "insights generation"]
    }
  ]
}
```

### List Orchestration Patterns
```cmd
curl -X GET http://localhost:8001/patterns
```

**Expected Response:**
```json
{
  "patterns": [
    {
      "name": "sequential",
      "description": "Step-by-step execution",
      "use_case": "When tasks must be completed in order"
    },
    {
      "name": "parallel", 
      "description": "Concurrent execution",
      "use_case": "When tasks can be executed simultaneously"
    },
    {
      "name": "loop",
      "description": "Iterative execution",
      "use_case": "When tasks need to be repeated until condition is met"
    },
    {
      "name": "simple",
      "description": "Single agent execution",
      "use_case": "When only one agent is needed"
    }
  ]
}
```

### List User Override Options
```cmd
curl -X GET http://localhost:8001/override-options
```

**Expected Response:**
```json
{
  "override_options": {
    "orchestration_pattern": {
      "description": "Override automatic pattern selection",
      "options": ["sequential", "parallel", "loop", "simple"],
      "example": "{\"orchestration_pattern\": \"parallel\"}"
    },
    "agents": {
      "description": "Specify which agents to use",
      "options": "List of agent names from /agents endpoint",
      "example": "{\"agents\": [\"DataSearchAgent\", \"ReportingAgent\"]}"
    },
    "agent_sequence": {
      "description": "Specify order of agents for sequential execution",
      "options": "Ordered list of agent names",
      "example": "{\"agent_sequence\": [\"DataSearchAgent\", \"ReportingAgent\"]}"
    },
    "parallel_config": {
      "description": "Configuration for parallel execution",
      "options": {
        "timeout": "Maximum execution time in seconds",
        "fail_fast": "Stop on first failure (boolean)"
      },
      "example": "{\"parallel_config\": {\"timeout\": 30, \"fail_fast\": false}}"
    },
    "loop_config": {
      "description": "Configuration for loop execution",
      "options": {
        "max_iterations": "Maximum number of iterations",
        "condition": "Condition to check for completion"
      },
      "example": "{\"loop_config\": {\"max_iterations\": 5, \"condition\": \"accuracy > 0.9\"}}"
    }
  },
  "usage_examples": {
    "sequential_override": {
      "query": "Get data and generate report",
      "context": {
        "orchestration_pattern": "sequential",
        "agent_sequence": ["DataSearchAgent", "ReportingAgent"]
      }
    },
    "parallel_override": {
      "query": "Analyze data from multiple sources",
      "context": {
        "orchestration_pattern": "parallel",
        "agents": ["DataSearchAgent", "ReportingAgent", "ExampleAgent"],
        "parallel_config": {"timeout": 30, "fail_fast": false}
      }
    },
    "loop_override": {
      "query": "Refine analysis iteratively",
      "context": {
        "orchestration_pattern": "loop",
        "agents": ["DataSearchAgent", "ReportingAgent"],
        "loop_config": {"max_iterations": 5, "condition": "accuracy > 0.9"}
      }
    }
  }
}
```

### Process Request - Data Search Query
```cmd
curl -X POST http://localhost:8001/process -H "Content-Type: application/json" -d "{\"query\":\"Find all sales data for Q4 2024\",\"context\":{\"department\":\"sales\",\"priority\":\"high\"}}"
```

### Process Request - Reporting Query
```cmd
curl -X POST http://localhost:8001/process -H "Content-Type: application/json" -d "{\"query\":\"Generate a comprehensive sales report for the last quarter\",\"context\":{\"format\":\"pdf\",\"include_charts\":true}}"
```

### Process Request - Analytics Query
```cmd
curl -X POST http://localhost:8001/process -H "Content-Type: application/json" -d "{\"query\":\"Analyze customer behavior patterns and provide insights\",\"context\":{\"analysis_type\":\"behavioral\",\"timeframe\":\"6_months\"}}"
```

### Process Request - Sequential Orchestration
```cmd
curl -X POST http://localhost:8001/process -H "Content-Type: application/json" -d "{\"query\":\"First get sales data, then analyze trends, then generate a comprehensive report\",\"context\":{\"orchestration_pattern\":\"sequential\",\"steps\":[\"data_retrieval\",\"analysis\",\"reporting\"]}}"
```

### Process Request - Parallel Orchestration
```cmd
curl -X POST http://localhost:8001/process -H "Content-Type: application/json" -d "{\"query\":\"Get data from multiple sources simultaneously and aggregate the results\",\"context\":{\"orchestration_pattern\":\"parallel\",\"sources\":[\"database\",\"documents\",\"apis\"]}}"
```

### Process Request - Loop Orchestration
```cmd
curl -X POST http://localhost:8001/process -H "Content-Type: application/json" -d "{\"query\":\"Keep refining the analysis until we achieve 95% confidence in the results\",\"context\":{\"orchestration_pattern\":\"loop\",\"target_confidence\":0.95,\"max_iterations\":10}}"
```

## User Override Examples

### Override Orchestration Pattern
```cmd
curl -X POST http://localhost:8001/process -H "Content-Type: application/json" -d "{\"query\":\"Analyze sales data\",\"context\":{\"orchestration_pattern\":\"parallel\"}}"
```

### Override Agent Selection - Sequential
```cmd
curl -X POST http://localhost:8001/process -H "Content-Type: application/json" -d "{\"query\":\"Get data and generate report\",\"context\":{\"orchestration_pattern\":\"sequential\",\"agent_sequence\":[\"DataSearchAgent\",\"ReportingAgent\"]}}"
```

### Override Agent Selection - Parallel
```cmd
curl -X POST http://localhost:8001/process -H "Content-Type: application/json" -d "{\"query\":\"Analyze data from multiple sources\",\"context\":{\"orchestration_pattern\":\"parallel\",\"agents\":[\"DataSearchAgent\",\"ReportingAgent\",\"ExampleAgent\"],\"parallel_config\":{\"timeout\":30,\"fail_fast\":false}}}"
```

### Override Agent Selection - Loop
```cmd
curl -X POST http://localhost:8001/process -H "Content-Type: application/json" -d "{\"query\":\"Refine analysis iteratively\",\"context\":{\"orchestration_pattern\":\"loop\",\"agents\":[\"DataSearchAgent\",\"ReportingAgent\"],\"loop_config\":{\"max_iterations\":5,\"condition\":\"accuracy > 0.9\"}}}"
```

### Override Agent Selection - Simple
```cmd
curl -X POST http://localhost:8001/process -H "Content-Type: application/json" -d "{\"query\":\"Search for specific data\",\"context\":{\"orchestration_pattern\":\"simple\",\"agents\":[\"DataSearchAgent\"]}}"
```

## Comprehensive Override Testing

### Test 1: Override Agents Only (Auto Pattern Selection)
```cmd
curl -X POST http://localhost:8001/process -H "Content-Type: application/json" -d "{\"query\":\"Analyze customer data and generate insights\",\"context\":{\"agents\":[\"DataSearchAgent\",\"ReportingAgent\"],\"business_context\":\"customer_analysis\"}}"
```

**Expected Response:**
```json
{
  "pattern": "sequential",
  "user_override": true,
  "agents": ["DataSearchAgent", "ReportingAgent"],
  "results": [
    {
      "agent": "DataSearchAgent",
      "result": {
        "status": "success",
        "data": "Customer data retrieved successfully"
      }
    },
    {
      "agent": "ReportingAgent", 
      "result": {
        "status": "success",
        "insights": "Customer insights generated"
      }
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Test 2: Override Pattern Only (Auto Agent Selection)
```cmd
curl -X POST http://localhost:8001/process -H "Content-Type: application/json" -d "{\"query\":\"Process multiple data sources simultaneously\",\"context\":{\"orchestration_pattern\":\"parallel\",\"data_sources\":[\"database\",\"documents\",\"apis\"],\"timeout\":60}}"
```

**Expected Response:**
```json
{
  "pattern": "parallel",
  "user_override": true,
  "agents": ["DataSearchAgent", "ReportingAgent", "ExampleAgent"],
  "parallel_config": {"timeout": 60},
  "results": [
    {
      "agent": "DataSearchAgent",
      "result": {"status": "success", "data": "Database data processed"},
      "status": "success"
    },
    {
      "agent": "ReportingAgent",
      "result": {"status": "success", "data": "Document data processed"},
      "status": "success"
    },
    {
      "agent": "ExampleAgent",
      "result": {"status": "success", "data": "API data processed"},
      "status": "success"
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Test 3: Override Both Pattern and Agents
```cmd
curl -X POST http://localhost:8001/process -H "Content-Type: application/json" -d "{\"query\":\"Execute iterative analysis with specific agents\",\"context\":{\"orchestration_pattern\":\"loop\",\"agents\":[\"DataSearchAgent\",\"ReportingAgent\"],\"loop_config\":{\"max_iterations\":3,\"condition\":\"accuracy > 0.85\"},\"analysis_type\":\"iterative_refinement\"}}"
```

**Expected Response:**
```json
{
  "pattern": "loop",
  "user_override": true,
  "agents": ["DataSearchAgent", "ReportingAgent"],
  "loop_config": {
    "max_iterations": 3,
    "condition": "accuracy > 0.85"
  },
  "iterations_completed": 2,
  "results": [
    {
      "iteration": 1,
      "results": [
        {
          "agent": "DataSearchAgent",
          "result": {"accuracy": 0.78, "status": "needs_refinement"}
        },
        {
          "agent": "ReportingAgent",
          "result": {"accuracy": 0.82, "status": "needs_refinement"}
        }
      ]
    },
    {
      "iteration": 2,
      "results": [
        {
          "agent": "DataSearchAgent",
          "result": {"accuracy": 0.89, "status": "target_achieved"}
        },
        {
          "agent": "ReportingAgent",
          "result": {"accuracy": 0.91, "status": "target_achieved"}
        }
      ]
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Test 4: Complex Sequential Override with Custom Order
```cmd
curl -X POST http://localhost:8001/process -H "Content-Type: application/json" -d "{\"query\":\"Execute complex business intelligence workflow\",\"context\":{\"orchestration_pattern\":\"sequential\",\"agent_sequence\":[\"DataSearchAgent\",\"ExampleAgent\",\"ReportingAgent\"],\"workflow_type\":\"comprehensive_bi\",\"stakeholders\":[\"executives\",\"analysts\"]}}"
```

**Expected Response:**
```json
{
  "pattern": "sequential",
  "user_override": true,
  "agent_sequence": ["DataSearchAgent", "ExampleAgent", "ReportingAgent"],
  "results": [
    {
      "agent": "DataSearchAgent",
      "result": {
        "status": "success",
        "data_retrieved": "Q4 sales data, customer demographics, product performance",
        "data_quality": "high"
      }
    },
    {
      "agent": "ExampleAgent",
      "result": {
        "status": "success",
        "analytics": "Advanced ML analysis completed",
        "insights": "Customer segmentation and trend analysis"
      }
    },
    {
      "agent": "ReportingAgent",
      "result": {
        "status": "success",
        "report": "Executive summary report generated",
        "format": "PDF",
        "sections": ["executive_summary", "financial_performance", "strategic_recommendations"]
      }
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Test 5: Parallel Override with Failure Handling
```cmd
curl -X POST http://localhost:8001/process -H "Content-Type: application/json" -d "{\"query\":\"Process data from multiple sources with error handling\",\"context\":{\"orchestration_pattern\":\"parallel\",\"agents\":[\"DataSearchAgent\",\"ReportingAgent\",\"ExampleAgent\"],\"parallel_config\":{\"timeout\":30,\"fail_fast\":false},\"data_sources\":[\"primary_db\",\"backup_db\",\"external_api\"]}}"
```

**Expected Response:**
```json
{
  "pattern": "parallel",
  "user_override": true,
  "agents": ["DataSearchAgent", "ReportingAgent", "ExampleAgent"],
  "parallel_config": {
    "timeout": 30,
    "fail_fast": false
  },
  "results": [
    {
      "agent": "DataSearchAgent",
      "result": {"status": "success", "data": "Primary database processed successfully"},
      "status": "success"
    },
    {
      "agent": "ReportingAgent",
      "result": {"status": "success", "data": "Backup database processed successfully"},
      "status": "success"
    },
    {
      "agent": "ExampleAgent",
      "result": {"error": "External API timeout", "status": "failed"},
      "status": "failed"
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Test 6: Loop Override with Custom Iteration Logic
```cmd
curl -X POST http://localhost:8001/process -H "Content-Type: application/json" -d "{\"query\":\"Refine model until convergence criteria is met\",\"context\":{\"orchestration_pattern\":\"loop\",\"agents\":[\"DataSearchAgent\",\"ExampleAgent\"],\"loop_config\":{\"max_iterations\":5,\"condition\":\"convergence_threshold < 0.01\",\"convergence_metric\":\"rmse\"},\"model_type\":\"predictive_analytics\"}}"
```

**Expected Response:**
```json
{
  "pattern": "loop",
  "user_override": true,
  "agents": ["DataSearchAgent", "ExampleAgent"],
  "loop_config": {
    "max_iterations": 5,
    "condition": "convergence_threshold < 0.01",
    "convergence_metric": "rmse"
  },
  "iterations_completed": 3,
  "results": [
    {
      "iteration": 1,
      "results": [
        {
          "agent": "DataSearchAgent",
          "result": {"rmse": 0.15, "convergence": false}
        },
        {
          "agent": "ExampleAgent",
          "result": {"rmse": 0.12, "convergence": false}
        }
      ]
    },
    {
      "iteration": 2,
      "results": [
        {
          "agent": "DataSearchAgent",
          "result": {"rmse": 0.08, "convergence": false}
        },
        {
          "agent": "ExampleAgent",
          "result": {"rmse": 0.06, "convergence": false}
        }
      ]
    },
    {
      "iteration": 3,
      "results": [
        {
          "agent": "DataSearchAgent",
          "result": {"rmse": 0.005, "convergence": true}
        },
        {
          "agent": "ExampleAgent",
          "result": {"rmse": 0.003, "convergence": true}
        }
      ]
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 3. Data Search Agent (Port 8002)

### Health Check
```cmd
curl -X GET http://localhost:8002/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "data-search-agent",
  "capabilities": ["database queries", "document search", "data retrieval"]
}
```

### Process Data Search Request
```cmd
curl -X POST http://localhost:8002/process_request -H "Content-Type: application/json" -d "{\"query\":\"Search for all customer records with purchase amount greater than $1000\",\"context\":{\"database\":\"customer_db\",\"filters\":{\"amount\":\">1000\"}}}"
```

### Process Document Search Request
```cmd
curl -X POST http://localhost:8002/process_request -H "Content-Type: application/json" -d "{\"query\":\"Find all contracts expiring in the next 30 days\",\"context\":{\"document_type\":\"contracts\",\"date_range\":\"next_30_days\"}}"
```

### Process Complex Data Query
```cmd
curl -X POST http://localhost:8002/process_request -H "Content-Type: application/json" -d "{\"query\":\"Retrieve sales performance data by region and product category for the last 6 months\",\"context\":{\"group_by\":[\"region\",\"product_category\"],\"time_period\":\"6_months\",\"include_metrics\":[\"revenue\",\"units_sold\",\"growth_rate\"]}}"
```

---

## 4. Reporting Agent (Port 8003)

### Health Check
```cmd
curl -X GET http://localhost:8003/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "reporting-agent",
  "capabilities": ["report generation", "analytics", "business insights"]
}
```

### Process Report Generation Request
```cmd
curl -X POST http://localhost:8003/process_request -H "Content-Type: application/json" -d "{\"query\":\"Generate a comprehensive quarterly business review report\",\"context\":{\"report_type\":\"quarterly_review\",\"format\":\"pdf\",\"sections\":[\"executive_summary\",\"financial_performance\",\"operational_metrics\",\"strategic_initiatives\"]}}"
```

### Process Analytics Request
```cmd
curl -X POST http://localhost:8003/process_request -H "Content-Type: application/json" -d "{\"query\":\"Create a detailed analysis of customer acquisition costs and lifetime value\",\"context\":{\"analysis_type\":\"customer_metrics\",\"timeframe\":\"12_months\",\"include_visualizations\":true}}"
```

### Process Business Insights Request
```cmd
curl -X POST http://localhost:8003/process_request -H "Content-Type: application/json" -d "{\"query\":\"Analyze market trends and provide strategic recommendations for Q1 2025\",\"context\":{\"insight_type\":\"strategic_planning\",\"focus_areas\":[\"market_expansion\",\"product_development\",\"competitive_analysis\"]}}"
```

---

## 5. Example Agent (Port 8004)

### Health Check
```cmd
curl -X GET http://localhost:8004/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "custom-analytics-agent",
  "agent_id": "agent_12345",
  "registered": true,
  "current_load": 2,
  "max_capacity": 10,
  "capabilities": ["custom_analytics", "data_processing", "insights_generation"]
}
```

### Get Agent Capabilities
```cmd
curl -X GET http://localhost:8004/capabilities
```

**Expected Response:**
```json
{
  "agent_name": "MyCustomAgent",
  "agent_id": "agent_12345",
  "version": "1.0.0",
  "capabilities": [
    {
      "name": "custom_analytics",
      "description": "Advanced custom analytics processing",
      "complexity_score": 8,
      "estimated_duration": 300
    },
    {
      "name": "data_processing",
      "description": "High-performance data processing",
      "complexity_score": 6,
      "estimated_duration": 180
    },
    {
      "name": "insights_generation",
      "description": "AI-powered insights generation",
      "complexity_score": 9,
      "estimated_duration": 450
    }
  ],
  "tags": ["analytics", "ai", "enterprise"]
}
```

### Process Analytics Request
```cmd
curl -X POST http://localhost:8004/process_request -H "Content-Type: application/json" -d "{\"query\":\"Perform advanced customer segmentation analysis using machine learning\",\"context\":{\"analysis_type\":\"customer_segmentation\",\"ml_algorithm\":\"kmeans\",\"features\":[\"purchase_history\",\"demographics\",\"behavioral_data\"]},\"analysis_type\":\"advanced_analytics\"}"
```

### Process Data Processing Request
```cmd
curl -X POST http://localhost:8004/process_request -H "Content-Type: application/json" -d "{\"query\":\"Process and clean large dataset for predictive modeling\",\"context\":{\"dataset_size\":\"1M_records\",\"data_quality_checks\":true,\"feature_engineering\":true},\"analysis_type\":\"data_preparation\"}"
```

### Process Insights Generation Request
```cmd
curl -X POST http://localhost:8004/process_request -H "Content-Type: application/json" -d "{\"query\":\"Generate actionable business insights from sales performance data\",\"context\":{\"data_source\":\"sales_system\",\"insight_depth\":\"strategic\",\"recommendations\":true},\"analysis_type\":\"insights_generation\"}"
```

---

## 6. End-to-End Workflow Testing

### Complete Business Intelligence Workflow
```cmd
# Step 1: Get data from Data Search Agent
curl -X POST http://localhost:8002/process_request -H "Content-Type: application/json" -d "{\"query\":\"Retrieve all sales transactions for Q4 2024\",\"context\":{\"timeframe\":\"Q4_2024\",\"include_details\":true}}"

# Step 2: Generate report using Reporting Agent
curl -X POST http://localhost:8003/process_request -H "Content-Type: application/json" -d "{\"query\":\"Create executive summary report from Q4 sales data\",\"context\":{\"report_type\":\"executive_summary\",\"data_source\":\"Q4_sales\",\"format\":\"presentation\"}}"

# Step 3: Advanced analytics using Example Agent
curl -X POST http://localhost:8004/process_request -H "Content-Type: application/json" -d "{\"query\":\"Perform predictive analysis on Q4 sales trends\",\"context\":{\"analysis_type\":\"predictive\",\"forecast_period\":\"Q1_2025\"},\"analysis_type\":\"predictive_analytics\"}"

# Step 4: Orchestrate complete workflow
curl -X POST http://localhost:8001/process -H "Content-Type: application/json" -d "{\"query\":\"Complete end-to-end business intelligence analysis: retrieve Q4 data, generate executive report, and provide predictive insights\",\"context\":{\"workflow_type\":\"complete_bi_analysis\",\"stakeholders\":[\"executives\",\"analysts\"]}}"
```

---

## 7. Error Handling Tests

### Test Invalid Tool Name
```cmd
curl -X POST http://localhost:8000/execute -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_TOKEN_HERE" -d "{\"tool_name\":\"invalid_tool\",\"parameters\":{}}"
```

### Test Missing Authentication
```cmd
curl -X GET http://localhost:8000/tools
```

### Test Invalid Agent Request
```cmd
curl -X POST http://localhost:8001/process -H "Content-Type: application/json" -d "{\"query\":\"\",\"context\":{}}"
```

### Test Service Unavailable
```cmd
curl -X GET http://localhost:8005/health
```

---

## 8. Performance Testing

### Load Test - Multiple Concurrent Requests
```cmd
# Run these commands simultaneously in multiple command prompt windows
curl -X POST http://localhost:8001/process -H "Content-Type: application/json" -d "{\"query\":\"Test request 1\",\"context\":{}}"
curl -X POST http://localhost:8001/process -H "Content-Type: application/json" -d "{\"query\":\"Test request 2\",\"context\":{}}"
curl -X POST http://localhost:8001/process -H "Content-Type: application/json" -d "{\"query\":\"Test request 3\",\"context\":{}}"
```

### Stress Test - Rapid Fire Requests
```cmd
for /L %i in (1,1,10) do curl -X GET http://localhost:8001/health
```

---

## 9. Monitoring and Observability

### Check All Service Health
```cmd
curl -X GET http://localhost:8000/health
curl -X GET http://localhost:8001/health
curl -X GET http://localhost:8002/health
curl -X GET http://localhost:8003/health
curl -X GET http://localhost:8004/health
```

### Check Docker Container Status
```cmd
docker-compose ps
```

### View Service Logs
```cmd
docker-compose logs mcp-server
docker-compose logs orchestrator-agent
docker-compose logs data-search-agent
docker-compose logs reporting-agent
docker-compose logs example-agent
```

---

## 10. Troubleshooting

### Common Issues and Solutions

1. **Service Not Responding:**
   ```cmd
   docker-compose restart SERVICE_NAME
   ```

2. **Authentication Errors:**
   - Verify token is valid and not expired
   - Check Authorization header format

3. **Port Conflicts:**
   ```cmd
   netstat -an | findstr :8000
   ```

4. **Docker Issues:**
   ```cmd
   docker-compose down
   docker-compose up -d --build
   ```

### Debug Mode
```cmd
# Enable debug logging
set LOG_LEVEL=DEBUG
docker-compose up
```

---

## Notes

- All curl commands are formatted for Windows Command Prompt
- Replace `YOUR_TOKEN_HERE` with actual authentication token
- JSON payloads are properly escaped for Windows
- Use `-v` flag with curl for verbose output: `curl -v -X GET http://localhost:8000/health`
- For PowerShell, use `Invoke-RestMethod` instead of curl
- All services support CORS for web-based testing
- Health checks return 200 status for healthy services
- All endpoints return JSON responses
- Error responses include detailed error messages and transaction IDs
