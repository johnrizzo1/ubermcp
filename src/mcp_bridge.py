"""MCP Bridge for Claude Desktop integration.

This bridge translates between MCP stdio protocol and our HTTP FastAPI server.
"""

import asyncio
import sys
from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel

try:
    from mcp import Server, Tool
    from mcp.server import stdio
except ImportError:
    print(
        "MCP library not installed. This module requires 'mcp' package.",
        file=sys.stderr,
    )
    sys.exit(1)


class ToolRequest(BaseModel):
    """Model for tool request parameters."""

    params: Optional[Dict[str, Any]] = None


class MCPBridge:
    """Bridge between MCP stdio and HTTP FastAPI server."""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.server = Server("uber-mcp-server")
        self.client = httpx.AsyncClient()

    async def initialize(self):
        """Initialize the MCP server with available tools."""
        try:
            # Fetch available tools from FastAPI server
            response = await self.client.get(f"{self.base_url}/tools")
            response.raise_for_status()
            tools_data = response.json()

            # Register each tool with MCP
            for tool_info in tools_data["tools"]:
                tool_name = tool_info["name"]

                # Create a tool handler for each tool
                async def create_handler(name):
                    async def handler(**kwargs):
                        # Call the FastAPI endpoint
                        response = await self.client.post(
                            f"{self.base_url}/tools/{name}", json=kwargs
                        )
                        response.raise_for_status()
                        return response.json()

                    return handler

                # Register the tool
                tool = Tool(
                    name=tool_name,
                    description=f"Kubernetes tool: {tool_name}",
                    input_schema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": True,
                    },
                )

                handler = await create_handler(tool_name)
                self.server.add_tool(tool, handler)

        except httpx.HTTPStatusError as exc:
            print(f"HTTP error initializing MCP bridge: {exc}", file=sys.stderr)
            raise
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            print(f"Network error initializing MCP bridge: {exc}", file=sys.stderr)
            raise
        except Exception as exc:
            print(f"Unexpected error initializing MCP bridge: {exc}", file=sys.stderr)
            raise

    async def run(self):
        """Run the MCP server using stdio transport."""
        async with stdio.stdio_server() as transport:
            await self.server.run(transport)

    async def cleanup(self):
        """Clean up resources."""
        await self.client.aclose()


async def main():
    """Main entry point for the MCP bridge."""
    # Check if FastAPI server is running
    bridge = MCPBridge()

    try:
        # Test connection to FastAPI server
        response = await bridge.client.get(f"{bridge.base_url}/")
        response.raise_for_status()
        print("Connected to FastAPI server", file=sys.stderr)
    except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
        print(
            f"Error: FastAPI server not running at {bridge.base_url} - {e}",
            file=sys.stderr,
        )
        print("Please start the server with 'nix run' first", file=sys.stderr)
        await bridge.cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error connecting to server: {e}", file=sys.stderr)
        await bridge.cleanup()
        sys.exit(1)

    try:
        await bridge.initialize()
        await bridge.run()
    finally:
        await bridge.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
