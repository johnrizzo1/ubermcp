from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.mcp_server import setup_mcp_server

# Explicitly import all tools
from src.tools import (
    example_tool,
    kubernetes_cron_jobs,
    kubernetes_deployments,
    kubernetes_events,
    kubernetes_ingresses,
    kubernetes_jobs,
    kubernetes_persistent_volumes,
    kubernetes_pods,
    kubernetes_port_forwarding,
    kubernetes_routes,
    kubernetes_secrets,
    kubernetes_services,
)


def create_app():
    fastapi_app = FastAPI(
        title="Uber MCP Server",
        description="FastAPI-based MCP Server providing Kubernetes management tools",
        version="0.1.0",
    )

    # Add CORS middleware for Claude Desktop access
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, restrict this to Claude's origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register tools
    tools = [
        example_tool.ExampleTool("example"),
        kubernetes_pods.KubernetesPodsTool("kubernetespods"),
        kubernetes_events.KubernetesEventsTool("kubernetesevents"),
        kubernetes_deployments.KubernetesDeploymentsTool("kubernetesdeployments"),
        kubernetes_services.KubernetesServicesTool("kubernetesservices"),
        kubernetes_ingresses.KubernetesIngressesTool("kubernetesingresses"),
        kubernetes_secrets.KubernetesSecretsTool("kubernetessecrets"),
        kubernetes_persistent_volumes.KubernetesPersistentVolumesTool(
            "kubernetespersistentvolumes"
        ),
        kubernetes_jobs.KubernetesJobsTool("kubernetesjobs"),
        kubernetes_cron_jobs.KubernetesCronJobsTool("kubernetescronjobs"),
        kubernetes_routes.KubernetesRoutesTool("kubernetesroutes"),
        kubernetes_port_forwarding.KubernetesPortForwardingTool(
            "kubernetesportforwarding"
        ),
    ]

    @fastapi_app.get("/")
    async def root():
        """Root endpoint - returns server info and available tools."""
        return {
            "name": "Uber MCP Server",
            "version": "0.1.0",
            "description": "FastAPI-based MCP Server providing Kubernetes management tools",
            "tools_endpoint": "/tools/{tool_name}",
            "docs": "/docs",
            "openapi": "/openapi.json",
        }

    @fastapi_app.get("/tools")
    async def list_tools():
        """List all available tools."""
        return {
            "tools": [
                {"name": tool.name, "endpoint": f"/tools/{tool.name}", "method": "POST"}
                for tool in tools
            ]
        }

    for tool_instance in tools:
        # Create a closure to capture the tool instance
        def create_endpoint(tool):
            async def endpoint(params: Optional[Dict[str, Any]] = None):
                # Handle both empty body and params
                if params is None:
                    params = {}
                return tool.execute(**params)

            return endpoint

        fastapi_app.add_api_route(
            f"/tools/{tool_instance.name}",
            create_endpoint(tool_instance),
            methods=["POST"],
        )

    # Set up MCP server
    setup_mcp_server(fastapi_app, tools)

    return fastapi_app


# Create an app instance for direct usage
app = create_app()
