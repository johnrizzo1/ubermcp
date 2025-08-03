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
                # Helm tools
                if tool.name == "helminstall":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "release_name": {
                                "type": "string",
                                "description": "Name for the release",
                            },
                            "chart": {
                                "type": "string",
                                "description": "Chart to install (repo/chart or path)",
                            },
                            "namespace": {"type": "string", "default": "default"},
                            "values": {
                                "type": "object",
                                "description": "Values to override",
                            },
                            "values_file": {
                                "type": "string",
                                "description": "Path to values file",
                            },
                            "version": {
                                "type": "string",
                                "description": "Chart version",
                            },
                            "create_namespace": {"type": "boolean", "default": True},
                            "wait": {"type": "boolean", "default": False},
                            "timeout": {"type": "string", "default": "5m"},
                            "atomic": {"type": "boolean", "default": False},
                            "dry_run": {"type": "boolean", "default": False},
                        },
                        "required": ["release_name", "chart"],
                    }
                elif tool.name == "helmlist":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "namespace": {
                                "type": "string",
                                "description": "Kubernetes namespace",
                            },
                            "all_namespaces": {"type": "boolean", "default": False},
                            "filter": {
                                "type": "string",
                                "description": "Filter releases by name",
                            },
                            "output": {
                                "type": "string",
                                "enum": ["table", "json", "yaml"],
                                "default": "table",
                            },
                            "all": {
                                "type": "boolean",
                                "default": False,
                                "description": "Show all releases",
                            },
                            "deployed": {"type": "boolean", "default": False},
                            "failed": {"type": "boolean", "default": False},
                            "pending": {"type": "boolean", "default": False},
                            "uninstalling": {"type": "boolean", "default": False},
                        },
                    }
                elif tool.name == "helmuninstall":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "release_name": {
                                "type": "string",
                                "description": "Name of the release to uninstall",
                            },
                            "namespace": {"type": "string", "default": "default"},
                            "keep_history": {"type": "boolean", "default": False},
                            "dry_run": {"type": "boolean", "default": False},
                            "no_hooks": {"type": "boolean", "default": False},
                            "timeout": {"type": "string", "default": "5m"},
                            "wait": {"type": "boolean", "default": False},
                        },
                        "required": ["release_name"],
                    }
                elif tool.name == "helmupgrade":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "release_name": {
                                "type": "string",
                                "description": "Name of the release to upgrade",
                            },
                            "chart": {
                                "type": "string",
                                "description": "Chart to upgrade to",
                            },
                            "namespace": {"type": "string", "default": "default"},
                            "values": {
                                "type": "object",
                                "description": "Values to override",
                            },
                            "values_file": {
                                "type": "string",
                                "description": "Path to values file",
                            },
                            "version": {
                                "type": "string",
                                "description": "Chart version",
                            },
                            "install": {
                                "type": "boolean",
                                "default": True,
                                "description": "Install if release doesn't exist",
                            },
                            "force": {"type": "boolean", "default": False},
                            "recreate_pods": {"type": "boolean", "default": False},
                            "wait": {"type": "boolean", "default": False},
                            "timeout": {"type": "string", "default": "5m"},
                            "atomic": {"type": "boolean", "default": False},
                            "cleanup_on_fail": {"type": "boolean", "default": False},
                            "dry_run": {"type": "boolean", "default": False},
                            "reset_values": {"type": "boolean", "default": False},
                            "reuse_values": {"type": "boolean", "default": False},
                        },
                        "required": ["release_name", "chart"],
                    }
                elif tool.name == "helmrollback":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "release_name": {
                                "type": "string",
                                "description": "Name of the release to rollback",
                            },
                            "revision": {
                                "type": "integer",
                                "description": "Revision to rollback to",
                            },
                            "namespace": {"type": "string", "default": "default"},
                            "force": {"type": "boolean", "default": False},
                            "recreate_pods": {"type": "boolean", "default": False},
                            "wait": {"type": "boolean", "default": False},
                            "timeout": {"type": "string", "default": "5m"},
                            "cleanup_on_fail": {"type": "boolean", "default": False},
                            "dry_run": {"type": "boolean", "default": False},
                        },
                        "required": ["release_name"],
                    }
                elif tool.name == "helmstatus":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "release_name": {
                                "type": "string",
                                "description": "Name of the release",
                            },
                            "namespace": {"type": "string", "default": "default"},
                            "revision": {
                                "type": "integer",
                                "description": "Specific revision",
                            },
                            "output": {
                                "type": "string",
                                "enum": ["json", "yaml", "table"],
                                "default": "json",
                            },
                            "show_desc": {"type": "boolean", "default": False},
                        },
                        "required": ["release_name"],
                    }
                elif tool.name == "helmhistory":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "release_name": {
                                "type": "string",
                                "description": "Name of the release",
                            },
                            "namespace": {"type": "string", "default": "default"},
                            "max": {
                                "type": "integer",
                                "description": "Maximum number of revisions",
                            },
                            "output": {
                                "type": "string",
                                "enum": ["table", "json", "yaml"],
                                "default": "table",
                            },
                        },
                        "required": ["release_name"],
                    }
                elif tool.name == "helmget":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["values", "manifest", "notes", "hooks", "all"],
                                "default": "values",
                            },
                            "release_name": {
                                "type": "string",
                                "description": "Name of the release",
                            },
                            "namespace": {"type": "string", "default": "default"},
                            "revision": {
                                "type": "integer",
                                "description": "Specific revision",
                            },
                            "output": {
                                "type": "string",
                                "enum": ["json", "yaml"],
                                "description": "Output format for values",
                            },
                        },
                        "required": ["release_name"],
                    }
                elif tool.name == "helmrepo":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["add", "remove", "list", "update", "index"],
                                "default": "list",
                            },
                            "repo_name": {
                                "type": "string",
                                "description": "Repository name",
                            },
                            "repo_url": {
                                "type": "string",
                                "description": "Repository URL",
                            },
                            "username": {
                                "type": "string",
                                "description": "Username for authentication",
                            },
                            "password": {
                                "type": "string",
                                "description": "Password for authentication",
                            },
                            "force_update": {"type": "boolean", "default": False},
                            "insecure_skip_tls_verify": {
                                "type": "boolean",
                                "default": False,
                            },
                            "directory": {
                                "type": "string",
                                "default": ".",
                                "description": "Directory for index action",
                            },
                        },
                    }
                elif tool.name == "helmsearch":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "search_type": {
                                "type": "string",
                                "enum": ["repo", "hub"],
                                "default": "repo",
                            },
                            "keyword": {
                                "type": "string",
                                "description": "Search keyword",
                            },
                            "version": {
                                "type": "string",
                                "description": "Version constraint",
                            },
                            "versions": {
                                "type": "boolean",
                                "default": False,
                                "description": "Show all versions",
                            },
                            "output": {
                                "type": "string",
                                "enum": ["table", "json", "yaml"],
                                "default": "table",
                            },
                            "devel": {
                                "type": "boolean",
                                "default": False,
                                "description": "Include development versions",
                            },
                            "max_col_width": {"type": "integer", "default": 50},
                        },
                    }
                elif tool.name == "helmshow":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "show_type": {
                                "type": "string",
                                "enum": ["all", "chart", "readme", "values", "crds"],
                                "default": "all",
                            },
                            "chart": {
                                "type": "string",
                                "description": "Chart to show (repo/chart or path)",
                            },
                            "version": {
                                "type": "string",
                                "description": "Chart version",
                            },
                            "devel": {"type": "boolean", "default": False},
                            "verify": {"type": "boolean", "default": False},
                            "keyring": {
                                "type": "string",
                                "description": "Path to keyring for verification",
                            },
                            "repo": {"type": "string", "description": "Repository URL"},
                            "username": {
                                "type": "string",
                                "description": "Username for authentication",
                            },
                            "password": {
                                "type": "string",
                                "description": "Password for authentication",
                            },
                        },
                        "required": ["chart"],
                    }
                # Kubernetes tools
                elif tool.name == "kubernetescreate":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "yaml_content": {
                                "type": "string",
                                "description": "YAML content of resources to create",
                            },
                            "namespace": {
                                "type": "string",
                                "default": "default",
                                "description": "Default namespace for resources",
                            },
                        },
                        "required": ["yaml_content"],
                    }
                elif tool.name == "kubernetesexpose":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "resource_type": {
                                "type": "string",
                                "default": "deployment",
                                "description": "Type of resource to expose",
                            },
                            "resource_name": {
                                "type": "string",
                                "description": "Name of resource to expose",
                            },
                            "namespace": {"type": "string", "default": "default"},
                            "service_name": {
                                "type": "string",
                                "description": "Name for the new service",
                            },
                            "port": {"type": "integer", "default": 80},
                            "target_port": {
                                "type": "integer",
                                "description": "Target port on the pod",
                            },
                            "service_type": {
                                "type": "string",
                                "default": "ClusterIP",
                                "enum": ["ClusterIP", "NodePort", "LoadBalancer"],
                            },
                        },
                        "required": ["resource_name"],
                    }
                elif tool.name == "kubernetesrun":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name for the deployment",
                            },
                            "image": {
                                "type": "string",
                                "description": "Container image to run",
                            },
                            "namespace": {"type": "string", "default": "default"},
                            "replicas": {"type": "integer", "default": 1},
                            "port": {
                                "type": "integer",
                                "description": "Container port to expose",
                            },
                            "env": {
                                "type": "object",
                                "description": "Environment variables",
                            },
                            "labels": {
                                "type": "object",
                                "description": "Labels to apply",
                            },
                            "command": {"type": "array", "items": {"type": "string"}},
                            "args": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["name", "image"],
                    }
                elif tool.name == "kubernetesset":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "resource_type": {
                                "type": "string",
                                "default": "deployment",
                            },
                            "resource_name": {"type": "string"},
                            "namespace": {"type": "string", "default": "default"},
                            "set_type": {
                                "type": "string",
                                "enum": ["image", "resources", "env"],
                                "default": "image",
                            },
                            "container_name": {
                                "type": "string",
                                "description": "Container name (optional)",
                            },
                            "image": {
                                "type": "string",
                                "description": "New image (for set_type=image)",
                            },
                            "limits": {
                                "type": "object",
                                "description": "Resource limits (for set_type=resources)",
                            },
                            "requests": {
                                "type": "object",
                                "description": "Resource requests (for set_type=resources)",
                            },
                            "env": {
                                "type": "object",
                                "description": "Environment variables (for set_type=env)",
                            },
                        },
                        "required": ["resource_name"],
                    }
                elif tool.name == "kubernetesget":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "resource_type": {
                                "type": "string",
                                "default": "pods",
                                "description": "Type of resource to get",
                            },
                            "namespace": {
                                "type": "string",
                                "description": "Namespace to filter by",
                            },
                            "name": {
                                "type": "string",
                                "description": "Specific resource name",
                            },
                            "label_selector": {
                                "type": "string",
                                "description": "Label selector",
                            },
                            "field_selector": {
                                "type": "string",
                                "description": "Field selector",
                            },
                        },
                    }
                elif tool.name == "kubernetesdelete":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "resource_type": {
                                "type": "string",
                                "description": "Type of resource to delete",
                            },
                            "name": {
                                "type": "string",
                                "description": "Resource name to delete",
                            },
                            "namespace": {"type": "string", "default": "default"},
                            "label_selector": {
                                "type": "string",
                                "description": "Delete by label selector",
                            },
                            "force": {"type": "boolean", "default": False},
                            "grace_period": {
                                "type": "integer",
                                "description": "Grace period in seconds",
                            },
                        },
                        "required": ["resource_type"],
                    }
                elif tool.name == "kubernetesscale":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "resource_type": {
                                "type": "string",
                                "default": "deployment",
                            },
                            "name": {
                                "type": "string",
                                "description": "Resource name to scale",
                            },
                            "namespace": {"type": "string", "default": "default"},
                            "replicas": {"type": "integer", "minimum": 0},
                        },
                        "required": ["name", "replicas"],
                    }
                elif tool.name == "kubernetesdescribe":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "resource_type": {
                                "type": "string",
                                "description": "Type of resource to describe",
                            },
                            "name": {"type": "string", "description": "Resource name"},
                            "namespace": {"type": "string", "default": "default"},
                        },
                        "required": ["resource_type", "name"],
                    }
                elif tool.name == "kuberneteslogs":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "pod_name": {"type": "string", "description": "Pod name"},
                            "namespace": {"type": "string", "default": "default"},
                            "container": {
                                "type": "string",
                                "description": "Container name",
                            },
                            "previous": {"type": "boolean", "default": False},
                            "tail_lines": {
                                "type": "integer",
                                "description": "Number of lines from end",
                            },
                            "since_seconds": {
                                "type": "integer",
                                "description": "Logs since N seconds ago",
                            },
                            "timestamps": {"type": "boolean", "default": False},
                        },
                        "required": ["pod_name"],
                    }
                elif tool.name == "kubernetesexec":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "pod_name": {"type": "string", "description": "Pod name"},
                            "namespace": {"type": "string", "default": "default"},
                            "container": {
                                "type": "string",
                                "description": "Container name",
                            },
                            "command": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Command to execute",
                            },
                            "stdin": {
                                "type": "string",
                                "description": "Input to send to command",
                            },
                            "tty": {"type": "boolean", "default": False},
                        },
                        "required": ["pod_name", "command"],
                    }
                elif tool.name == "kubernetesapply":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "yaml_content": {
                                "type": "string",
                                "description": "YAML content to apply",
                            },
                            "namespace": {"type": "string", "default": "default"},
                        },
                        "required": ["yaml_content"],
                    }
                elif tool.name == "kubernetesportforwarding":
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
                elif tool.name == "kubernetesexplain":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "resource": {
                                "type": "string",
                                "description": "Resource type to explain (e.g., pod, deployment)",
                            },
                            "api_version": {
                                "type": "string",
                                "description": "API version (optional)",
                            },
                        },
                        "required": ["resource"],
                    }
                elif tool.name == "kubernetesedit":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "resource_type": {
                                "type": "string",
                                "description": "Type of resource to edit",
                            },
                            "name": {"type": "string", "description": "Resource name"},
                            "namespace": {"type": "string", "default": "default"},
                            "edit_type": {
                                "type": "string",
                                "enum": ["merge", "replace"],
                                "default": "merge",
                            },
                            "changes": {
                                "type": "object",
                                "description": "Changes to apply",
                            },
                        },
                        "required": ["resource_type", "name", "changes"],
                    }
                elif tool.name == "kubernetesrollout":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": [
                                    "status",
                                    "history",
                                    "undo",
                                    "pause",
                                    "resume",
                                    "restart",
                                ],
                                "default": "status",
                            },
                            "resource_type": {
                                "type": "string",
                                "default": "deployment",
                            },
                            "name": {"type": "string", "description": "Resource name"},
                            "namespace": {"type": "string", "default": "default"},
                            "revision": {
                                "type": "integer",
                                "description": "Revision number for undo",
                            },
                        },
                        "required": ["name"],
                    }
                elif tool.name == "kubernetesautoscale":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["create", "delete", "get"],
                                "default": "create",
                            },
                            "resource_type": {
                                "type": "string",
                                "default": "deployment",
                            },
                            "resource_name": {
                                "type": "string",
                                "description": "Resource to autoscale",
                            },
                            "namespace": {"type": "string", "default": "default"},
                            "min_replicas": {
                                "type": "integer",
                                "default": 1,
                                "minimum": 1,
                            },
                            "max_replicas": {
                                "type": "integer",
                                "default": 10,
                                "minimum": 1,
                            },
                            "target_cpu_percent": {
                                "type": "integer",
                                "default": 80,
                                "minimum": 1,
                                "maximum": 100,
                            },
                            "target_memory_percent": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 100,
                            },
                            "hpa_name": {"type": "string", "description": "HPA name"},
                        },
                    }
                elif tool.name == "kubernetesclusterinfo":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {},
                    }
                elif tool.name == "kubernetestop":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "resource_type": {
                                "type": "string",
                                "default": "pods",
                                "enum": ["pods", "nodes"],
                            },
                            "namespace": {
                                "type": "string",
                                "description": "Namespace (for pods)",
                            },
                            "sort_by": {
                                "type": "string",
                                "default": "cpu",
                                "enum": ["cpu", "memory"],
                            },
                        },
                    }
                elif tool.name == "kubernetesnodemanagement":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["cordon", "uncordon", "drain", "taint"],
                            },
                            "node_name": {"type": "string", "description": "Node name"},
                            "ignore_daemonsets": {"type": "boolean", "default": True},
                            "delete_emptydir_data": {
                                "type": "boolean",
                                "default": True,
                            },
                            "force": {"type": "boolean", "default": False},
                            "grace_period": {"type": "integer", "default": 30},
                            "taint_action": {
                                "type": "string",
                                "enum": ["add", "remove"],
                                "default": "add",
                            },
                            "key": {"type": "string", "description": "Taint key"},
                            "value": {"type": "string", "description": "Taint value"},
                            "effect": {
                                "type": "string",
                                "enum": ["NoSchedule", "PreferNoSchedule", "NoExecute"],
                                "default": "NoSchedule",
                            },
                        },
                        "required": ["action", "node_name"],
                    }
                elif tool.name == "kubernetescp":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "pod_name": {"type": "string", "description": "Pod name"},
                            "namespace": {"type": "string", "default": "default"},
                            "container": {
                                "type": "string",
                                "description": "Container name",
                            },
                            "src_path": {
                                "type": "string",
                                "description": "Source path",
                            },
                            "dst_path": {
                                "type": "string",
                                "description": "Destination path",
                            },
                            "direction": {
                                "type": "string",
                                "enum": ["to", "from"],
                                "default": "to",
                                "description": "Copy direction: to (local->pod) or from (pod->local)",
                            },
                        },
                        "required": ["pod_name", "src_path", "dst_path"],
                    }
                elif tool.name == "kubernetespatch":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "resource_type": {
                                "type": "string",
                                "description": "Type of resource to patch",
                            },
                            "name": {"type": "string", "description": "Resource name"},
                            "namespace": {"type": "string", "default": "default"},
                            "patch": {
                                "type": ["object", "array"],
                                "description": "Patch to apply",
                            },
                            "patch_type": {
                                "type": "string",
                                "enum": ["strategic", "merge", "json"],
                                "default": "strategic",
                            },
                        },
                        "required": ["resource_type", "name", "patch"],
                    }
                elif tool.name == "kuberneteslabel":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "resource_type": {
                                "type": "string",
                                "description": "Type of resource to label",
                            },
                            "name": {"type": "string", "description": "Resource name"},
                            "namespace": {"type": "string", "default": "default"},
                            "labels": {
                                "type": "object",
                                "description": "Labels to add/update",
                            },
                            "remove_labels": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Label keys to remove",
                            },
                            "overwrite": {
                                "type": "boolean",
                                "default": False,
                                "description": "Replace all labels",
                            },
                        },
                        "required": ["resource_type", "name"],
                    }
                elif tool.name == "kubernetesannotate":
                    tool_schema["inputSchema"] = {
                        "type": "object",
                        "properties": {
                            "resource_type": {
                                "type": "string",
                                "description": "Type of resource to annotate",
                            },
                            "name": {"type": "string", "description": "Resource name"},
                            "namespace": {"type": "string", "default": "default"},
                            "annotations": {
                                "type": "object",
                                "description": "Annotations to add/update",
                            },
                            "remove_annotations": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Annotation keys to remove",
                            },
                            "overwrite": {
                                "type": "boolean",
                                "default": False,
                                "description": "Replace all annotations",
                            },
                        },
                        "required": ["resource_type", "name"],
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

            except AttributeError as e:
                logger.error("Tool configuration error for %s: %s", tool_name, e)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32602,
                        "message": f"Tool configuration error: {str(e)}",
                    },
                }
            except Exception as e:
                logger.error("Unexpected error executing tool %s: %s", tool_name, e)
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
