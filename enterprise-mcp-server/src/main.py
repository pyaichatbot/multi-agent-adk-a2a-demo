"""
Enterprise MCP Server - Pure FastMCP Implementation
Production-ready MCP server with enterprise features following SOLID principles
"""

import asyncio
import os
import signal
import sys
import time
from datetime import datetime
from typing import Any, Dict

from fastmcp import FastMCP
import uvicorn

from src.config.settings import settings
from src.core.observability import observability
from src.core.authentication import sageai_auth, permission_manager
from src.core.rate_limiter import rate_limiter
from src.core.policy_engine import policy_engine
from src.core.policy_enforcement import policy_enforcement
from src.tools import DatabaseTools, AnalyticsTools, DocumentTools, SystemTools


# FastMCP server instance
mcp = FastMCP("Enterprise MCP Server")


# MCP Tools Implementation - Following SOLID Principles
# Each tool category is handled by its respective class

# Database Tools
@mcp.tool()
async def search_database(query: str, database: str = "default", limit: int = 100) -> str:
    """Search enterprise database with SQL queries"""
    return await DatabaseTools.search_database(query, database, limit)

@mcp.tool()
async def execute_sql(sql: str, database: str = "default", timeout: int = 30) -> str:
    """Execute SQL query with timeout protection"""
    return await DatabaseTools.execute_sql(sql, database, timeout)

@mcp.tool()
async def get_table_schema(table_name: str, database: str = "default") -> str:
    """Get table schema information"""
    return await DatabaseTools.get_table_schema(table_name, database)

# Analytics Tools
@mcp.tool()
async def generate_report(report_type: str, parameters: Dict[str, Any], format: str = "pdf") -> str:
    """Generate business reports and analytics"""
    return await AnalyticsTools.generate_report(report_type, parameters, format)

@mcp.tool()
async def run_analytics(analysis_type: str, data_source: str, parameters: Dict[str, Any]) -> str:
    """Run advanced analytics and machine learning models"""
    return await AnalyticsTools.run_analytics(analysis_type, data_source, parameters)

@mcp.tool()
async def create_dashboard(dashboard_name: str, widgets: list, layout: str = "grid") -> str:
    """Create analytics dashboard"""
    return await AnalyticsTools.create_dashboard(dashboard_name, widgets, layout)

@mcp.tool()
async def export_data(data_source: str, format: str = "csv", filters: Dict[str, Any] = None) -> str:
    """Export data for analysis"""
    return await AnalyticsTools.export_data(data_source, format, filters)

# Document Tools
@mcp.tool()
async def search_documents(query: str, repository: str = "enterprise_docs", limit: int = 10) -> str:
    """Search through enterprise document repositories"""
    return await DocumentTools.search_documents(query, repository, limit)

@mcp.tool()
async def index_document(document_path: str, repository: str = "enterprise_docs", metadata: Dict[str, Any] = None) -> str:
    """Index document for search"""
    return await DocumentTools.index_document(document_path, repository, metadata)

@mcp.tool()
async def extract_text(document_path: str, format: str = "auto") -> str:
    """Extract text from document"""
    return await DocumentTools.extract_text(document_path, format)

@mcp.tool()
async def summarize_document(document_path: str, summary_length: str = "medium") -> str:
    """Generate document summary"""
    return await DocumentTools.summarize_document(document_path, summary_length)

# System Tools
@mcp.tool()
async def check_system_health() -> str:
    """Check system health and agent status"""
    return await SystemTools.check_system_health()

@mcp.tool()
async def list_tools() -> str:
    """List all available MCP tools with their descriptions and parameters"""
    return await SystemTools.list_tools()

@mcp.tool()
async def get_system_info() -> str:
    """Get system information and status"""
    return await SystemTools.get_system_info()


# Policy and Compliance Endpoints
@mcp.tool()
async def get_compliance_metrics() -> str:
    """Get comprehensive compliance and governance metrics"""
    try:
        metrics = await policy_engine.get_compliance_metrics()
        return f"Compliance Metrics:\n{metrics}"
    except Exception as e:
        return f"Failed to get compliance metrics: {str(e)}"


@mcp.tool()
async def get_audit_trail(limit: int = 50) -> str:
    """Get audit trail of policy decisions and violations"""
    try:
        audit_entries = await policy_engine.get_audit_trail(limit)
        if not audit_entries:
            return "No audit entries found"
        
        trail_text = "Audit Trail:\n"
        for entry in audit_entries:
            trail_text += f"- {entry['timestamp']}: {entry['type']} - {entry['user_id']} - {entry['resource_type']}/{entry['resource_id']}\n"
        
        return trail_text
    except Exception as e:
        return f"Failed to get audit trail: {str(e)}"


@mcp.tool()
async def get_user_accessible_tools(token: str) -> str:
    """Get list of tools accessible to user based on policies"""
    try:
        accessible_tools = await policy_enforcement.get_user_accessible_tools(token)
        if not accessible_tools:
            return "No tools accessible to user"
        
        return f"Accessible Tools:\n" + "\n".join(f"- {tool}" for tool in accessible_tools)
    except Exception as e:
        return f"Failed to get accessible tools: {str(e)}"


@mcp.tool()
async def reload_policies() -> str:
    """Reload policies from all sources (database first, then YAML)"""
    try:
        await policy_engine.reload_policies()
        return "Policies reloaded successfully from all sources"
    except Exception as e:
        return f"Failed to reload policies: {str(e)}"


@mcp.tool()
async def get_policy_status() -> str:
    """Get current policy engine status and configuration"""
    try:
        status = {
            "policy_engine_enabled": policy_engine.policies.get('enabled', True),
            "policy_sources": ["database", "yaml"],
            "total_policies": len(policy_engine.policies),
            "enforcement_enabled": policy_enforcement.enforcement_enabled,
            "violations_count": len(policy_engine.violations)
        }
        return f"Policy Status:\n{status}"
    except Exception as e:
        return f"Failed to get policy status: {str(e)}"


# Health check tool
@mcp.tool()
async def health_check() -> str:
    """Health check endpoint for monitoring"""
    return str(observability.get_health_status())


@mcp.tool()
async def get_metrics() -> str:
    """Get metrics for monitoring"""
    return str(observability.get_metrics())


@mcp.tool()
async def get_rate_limit_status() -> str:
    """Get rate limit status"""
    try:
        status = {
            "rate_limiting": {
                "enabled": rate_limiter.enabled,
                "global_limits": {
                    "requests_per_minute": settings.security.rate_limit_requests,
                    "window_seconds": settings.security.rate_limit_window
                },
                "tool_limits": {
                    "requests_per_minute": settings.security.tool_rate_limit_requests,
                    "window_seconds": settings.security.tool_rate_limit_window
                }
            }
        }
        return str(status)
    except Exception as e:
        observability.log("error", "Rate limit status error", error=str(e))
        return str({"error": "Failed to get rate limit status"})


# Signal handlers
def signal_handler(signum, frame):
    """Handle shutdown signals"""
    observability.log("info", "Received shutdown signal", signal=signum)
    sys.exit(0)


async def startup():
    """Application startup"""
    observability.log("info", "Starting Enterprise MCP Server")
    
    # Initialize rate limiter
    await rate_limiter.connect_redis()
    
    # Initialize policy engine
    await policy_engine.initialize()
    
    observability.log("info", "Enterprise MCP Server started successfully")


async def shutdown():
    """Application shutdown"""
    observability.log("info", "Shutting down Enterprise MCP Server")


if __name__ == "__main__":
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start FastMCP server with configurable transport
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    
    if transport == "sse":
        # SSE transport for remote/Kubernetes deployment
        mcp.run(
            transport="sse",
            host=settings.mcp.host,
            port=settings.mcp.port
        )
    else:
        # STDIO transport for local development
        mcp.run()