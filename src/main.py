"""Main entry point for the uber-mcp-server application."""

from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.mcp_server import setup_mcp_server

# Explicitly import all tools
from src.tools import (  # Helm tools; Kubernetes tools
    helm_dependency,
    helm_get,
    helm_history,
    helm_install,
    helm_list,
    helm_repo,
    helm_rollback,
    helm_search,
    helm_show,
    helm_status,
    helm_uninstall,
    helm_upgrade,
    kubernetes_annotate,
    kubernetes_apply,
    kubernetes_autoscale,
    kubernetes_cluster_info,
    kubernetes_cp,
    kubernetes_crd,
    kubernetes_create,
    kubernetes_cron_jobs,
    kubernetes_delete,
    kubernetes_deployments,
    kubernetes_describe,
    kubernetes_edit,
    kubernetes_events,
    kubernetes_exec,
    kubernetes_explain,
    kubernetes_expose,
    kubernetes_get,
    kubernetes_ingresses,
    kubernetes_jobs,
    kubernetes_label,
    kubernetes_logs,
    kubernetes_node_management,
    kubernetes_patch,
    kubernetes_persistent_volumes,
    kubernetes_pods,
    kubernetes_port_forwarding,
    kubernetes_rollout,
    kubernetes_routes,
    kubernetes_run,
    kubernetes_scale,
    kubernetes_secrets,
    kubernetes_services,
    kubernetes_set,
    kubernetes_top,
)


def create_app():
    """Create and configure the FastAPI application."""
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
        # Helm Commands
        helm_dependency.HelmDependencyTool("helmdependency"),
        helm_install.HelmInstallTool("helminstall"),
        helm_list.HelmListTool("helmlist"),
        helm_uninstall.HelmUninstallTool("helmuninstall"),
        helm_upgrade.HelmUpgradeTool("helmupgrade"),
        helm_rollback.HelmRollbackTool("helmrollback"),
        helm_status.HelmStatusTool("helmstatus"),
        helm_history.HelmHistoryTool("helmhistory"),
        helm_get.HelmGetTool("helmget"),
        helm_repo.HelmRepoTool("helmrepo"),
        helm_search.HelmSearchTool("helmsearch"),
        helm_show.HelmShowTool("helmshow"),
        # Kubernetes Basic Commands (Beginner)
        kubernetes_create.KubernetesCreateTool("kubernetescreate"),
        kubernetes_expose.KubernetesExposeTool("kubernetesexpose"),
        kubernetes_run.KubernetesRunTool("kubernetesrun"),
        kubernetes_set.KubernetesSetTool("kubernetesset"),
        # Kubernetes Basic Commands (Intermediate)
        kubernetes_explain.KubernetesExplainTool("kubernetesexplain"),
        kubernetes_get.KubernetesGetTool("kubernetesget"),
        kubernetes_edit.KubernetesEditTool("kubernetesedit"),
        kubernetes_delete.KubernetesDeleteTool("kubernetesdelete"),
        # Kubernetes Deploy Commands
        kubernetes_rollout.KubernetesRolloutTool("kubernetesrollout"),
        kubernetes_scale.KubernetesScaleTool("kubernetesscale"),
        kubernetes_autoscale.KubernetesAutoscaleTool("kubernetesautoscale"),
        # Kubernetes Cluster Management Commands
        kubernetes_cluster_info.KubernetesClusterInfoTool("kubernetesclusterinfo"),
        kubernetes_top.KubernetesTopTool("kubernetestop"),
        kubernetes_node_management.KubernetesNodeManagementTool(
            "kubernetesnodemanagement"
        ),
        # Kubernetes Troubleshooting and Debugging Commands
        kubernetes_describe.KubernetesDescribeTool("kubernetesdescribe"),
        kubernetes_logs.KubernetesLogsTool("kuberneteslogs"),
        kubernetes_exec.KubernetesExecTool("kubernetesexec"),
        kubernetes_cp.KubernetesCopyTool("kubernetescp"),
        # Kubernetes Advanced Commands
        kubernetes_apply.KubernetesApplyTool("kubernetesapply"),
        kubernetes_patch.KubernetesPatchTool("kubernetespatch"),
        kubernetes_crd.KubernetesCRDTool("kubernetescrd"),
        # Kubernetes Settings Commands
        kubernetes_label.KubernetesLabelTool("kuberneteslabel"),
        kubernetes_annotate.KubernetesAnnotateTool("kubernetesannotate"),
        # Kubernetes Existing tools
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
