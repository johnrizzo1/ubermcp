"""MCP Server implementation with Streamable HTTP transport."""

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, Response

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPServer:
    """MCP Server with Streamable HTTP transport."""

    def __init__(self, app: FastAPI, tools: List[Any]):
        self.app = app
        self.tools = tools
        self.protocol_version = "2024-11-05"
        self.server_info = {"name": "uber-mcp-server", "version": "0.1.0"}

        # Register MCP endpoints
        self._register_endpoints()

    def _register_endpoints(self):
        """Register MCP endpoints on the FastAPI app."""

        @self.app.post("/mcp/v1/message")
        async def handle_message(request: Request) -> Response:
            """Handle MCP messages via Streamable HTTP transport."""
            try:
                # Parse incoming JSON-RPC message
                body = await request.body()
                message = json.loads(body)

                logger.info("Received MCP message: %s", message)

                # Handle the message based on method
                method = message.get("method")
                params = message.get("params", {})
                request_id = message.get("id")

                # Process the request and generate response
                response = await self._handle_method(method, params, request_id)

                # For streamable transport, we return the response directly
                return Response(
                    content=json.dumps(response),
                    media_type="application/json",
                    headers={
                        "Content-Type": "application/json",
                    },
                )

            except json.JSONDecodeError:
                return Response(
                    content=json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "error": {"code": -32700, "message": "Parse error"},
                        }
                    ),
                    media_type="application/json",
                    status_code=400,
                )
            except Exception as e:
                logger.error("Error handling message: %s", e)
                return Response(
                    content=json.dumps(
                        {"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}}
                    ),
                    media_type="application/json",
                    status_code=500,
                )

    async def _handle_method(
        self, method: str, params: Dict[str, Any], request_id: Optional[Any]
    ) -> Dict[str, Any]:
        """Handle specific MCP methods."""

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": self.protocol_version,
                    "capabilities": {
                        "tools": {},
                        "resources": {"subscribe": False, "listChanged": False},
                    },
                    "serverInfo": self.server_info,
                },
            }

        if method == "initialized":
            # Client confirms initialization
            return {"jsonrpc": "2.0", "id": request_id, "result": {}}

        if method == "tools/list":
            # Return list of available tools
            tools_list = []
            for tool in self.tools:
                # Build tool schema based on the tool's execute method
                tool_schema = {
                    "name": tool.name,
                    "description": f"Kubernetes tool: {tool.name}",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": True,
                    },
                }

                # Add specific schemas for known tools
                if tool.name == "kubernetesportforwarding":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["start", "stop", "list"],
                                "default": "start",
                            },
                            "pod_name": {"type": "string"},
                            "namespace": {"type": "string"},
                            "local_port": {"type": "integer"},
                            "remote_port": {"type": "integer"},
                            "forward_id": {"type": "string"},
                        },
                    }
                elif tool.name in [
                    "kubernetespods",
                    "kubernetesdeployments",
                    "kubernetesservices",
                ]:
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "namespace": {
                                "type": "string",
                                "description": "Kubernetes namespace to filter by (optional)",
                            }
                        },
                    }

                tools_list.append(tool_schema)

            return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": tools_list}}

        if method == "tools/call":
            # Execute a tool
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            # Find the tool
            tool = None
            for tool_instance in self.tools:
                if tool_instance.name == tool_name:
                    tool = tool_instance
                    break

            if not tool:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32602,
                        "message": f"Tool not found: {tool_name}",
                    },
                }

            try:
                # Execute the tool
                result = tool.execute(**arguments)

                # Format the result as MCP expects
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {"type": "text", "text": json.dumps(result, indent=2)}
                        ],
                        "isError": "error" in result,
                    },
                }

            except Exception as e:
                logger.error("Error executing tool %s: %s", tool_name, e)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": f"Tool execution error: {str(e)}",
                    },
                }

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }


def setup_mcp_server(app: FastAPI, tools: List[Any]):
    """Set up MCP server on the FastAPI app."""
    mcp_server = MCPServer(app, tools)
    return mcp_server
