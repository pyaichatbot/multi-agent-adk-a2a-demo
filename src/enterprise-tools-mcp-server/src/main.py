"""
Enterprise Tools MCP Server
Provides database queries, document search, and analytics tools for enterprise agents
Following ADK MCP documentation: https://google.github.io/adk-docs/tools/mcp-tools/
"""

import logging
import os
from src.mcp_server import main


if __name__ == "__main__":
    # Get port from environment
    port = int(os.getenv("PORT", 8000))
    
    # Start MCP server following ADK documentation
    # (Observability is set up in mcp_server.py main function)
    main(port=port, json_response=False)
