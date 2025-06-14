#!/usr/bin/env python3
"""
Minimal test server to isolate the issue
"""

from mcp.server.fastmcp import FastMCP

# Create minimal server
app = FastMCP("test-server")

@app.tool()
async def hello() -> str:
    """Test tool"""
    return "Hello from test server"

if __name__ == "__main__":
    app.run()