#!/usr/bin/env python3
"""
Local development script for Enterprise MCP Server
Runs with STDIO transport for local development
"""

import os
import sys

# Set environment for local development
os.environ["MCP_TRANSPORT"] = "stdio"
os.environ["ENVIRONMENT"] = "development"
os.environ["ENABLE_TELEMETRY"] = "false"
os.environ["LOG_LEVEL"] = "DEBUG"

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import and run the main module
if __name__ == "__main__":
    from src.main import mcp
    
    print("🚀 Starting Enterprise MCP Server (STDIO mode)")
    print("📡 Transport: STDIO")
    print("🔧 Environment: Development")
    print("=" * 50)
    
    mcp.run()
