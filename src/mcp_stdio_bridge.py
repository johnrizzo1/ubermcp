#!/usr/bin/env python3
"""Simple MCP stdio bridge for Claude Desktop integration."""

import asyncio
import json
import logging
import sys
from typing import Any, Dict

import httpx

# Set up logging
logging.basicConfig(level=logging.DEBUG, filename="/tmp/mcp_bridge.log")
logger = logging.getLogger(__name__)


class SimpleMCPBridge:
    """Simple bridge between MCP stdio protocol and HTTP FastAPI server."""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.request_id = 0

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an incoming MCP request."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        logger.debug("Received request: %s", request)

        try:
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "uber-mcp-server", "version": "0.1.0"},
                    },
                }

            if method == "tools/list":
                # Fetch tools from FastAPI server
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.base_url}/tools")
                    tools_data = response.json()

                tools = []
                for tool_info in tools_data["tools"]:
                    # Use shorter descriptions to avoid truncation
                    tool_name = tool_info["name"]
                    desc = tool_name.replace("kubernetes", "K8s ")
                    tools.append(
                        {
                            "name": tool_name,
                            "description": desc,
                            "inputSchema": {"type": "object"},
                        }
                    )

                return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": tools}}

            if method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})

                # Call the FastAPI endpoint
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/tools/{tool_name}", json=tool_args
                    )
                    result = response.json()

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {"type": "text", "text": json.dumps(result, indent=2)}
                        ]
                    },
                }

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

        except httpx.HTTPStatusError as e:
            logger.error("HTTP error handling request: %s", e)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": f"HTTP error: {str(e)}"},
            }
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            logger.error("Network error handling request: %s", e)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": f"Network error: {str(e)}"},
            }
        except Exception as e:
            logger.error("Unexpected error handling request: %s", e)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": str(e)},
            }

    async def run(self):
        """Run the stdio bridge."""
        logger.info("Starting MCP stdio bridge")

        # Check if FastAPI server is running
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/")
                response.raise_for_status()
                logger.info("Connected to FastAPI server")
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            logger.error("Cannot connect to FastAPI server at %s: %s", self.base_url, e)
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"FastAPI server not running at {self.base_url}. Start it with 'nix run' first.",
                },
            }
            sys.stdout.write(json.dumps(error_response, separators=(",", ":")) + "\n")
            sys.stdout.flush()
            return
        except Exception as e:
            logger.error("Unexpected error connecting to FastAPI server: %s", e)
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Error connecting to server: {str(e)}",
                },
            }
            sys.stdout.write(json.dumps(error_response, separators=(",", ":")) + "\n")
            sys.stdout.flush()
            return

        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

        while True:
            try:
                line = await reader.readline()
                if not line:
                    break

                # Parse JSON-RPC request
                request = json.loads(line.decode())

                # Handle request
                response = await self.handle_request(request)

                # Send response with compact JSON and newline
                response_str = json.dumps(response, separators=(",", ":"))
                sys.stdout.write(response_str + "\n")
                sys.stdout.flush()

                logger.debug(
                    "Sent response: %s... (length: %s)",
                    response_str[:200],
                    len(response_str),
                )

            except json.JSONDecodeError as e:
                logger.error("Invalid JSON: %s", e)
            except (IOError, OSError) as e:
                logger.error("IO Error: %s", e)
            except Exception as e:
                logger.error("Unexpected error in main loop: %s", e)


async def main():
    """Main entry point."""
    bridge = SimpleMCPBridge()
    await bridge.run()


if __name__ == "__main__":
    asyncio.run(main())
