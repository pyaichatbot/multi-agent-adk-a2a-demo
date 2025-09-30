#!/usr/bin/env python3
"""
Remote deployment script for Enterprise MCP Server
Runs with SSE transport for remote/Kubernetes deployment
"""

import os
import sys

# Set environment for remote deployment
os.environ["MCP_TRANSPORT"] = "sse"
os.environ["ENVIRONMENT"] = "production"
os.environ["ENABLE_TELEMETRY"] = "true"
os.environ["LOG_LEVEL"] = "INFO"
os.environ["MCP_HOST"] = "0.0.0.0"
os.environ["MCP_PORT"] = "8000"

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import and run the main module
if __name__ == "__main__":
    from src.main import mcp
    
    print("🚀 Starting Enterprise MCP Server (SSE mode)")
    print("📡 Transport: SSE")
    print("🌐 Host: 0.0.0.0:8000")
    print("🔧 Environment: Production")
    print("=" * 50)
    
    mcp.run(
        transport="sse",
        host="0.0.0.0",
        port=8000
    )
