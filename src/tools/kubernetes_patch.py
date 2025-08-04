"""Kubernetes patch tool for applying partial updates to resources."""

import json

from kubernetes import client, config
from kubernetes.dynamic import DynamicClient

from src.base_tool import BaseTool


class KubernetesPatchTool(BaseTool):
    """Tool for patching Kubernetes resources with partial updates."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()

            resource_type = kwargs.get("resource_type", "")
            name = kwargs.get("name", "")
            namespace = kwargs.get("namespace", "default")
            patch = kwargs.get("patch", {})
            patch_type = kwargs.get("patch_type", "strategic")  # strategic, merge, json
            api_version = kwargs.get("api_version", None)  # For CRDs

            if not resource_type:
                return {"error": "resource_type is required"}
            if not name:
                return {"error": "name is required"}
            if not patch:
                return {"error": "patch is required"}

            # Initialize API clients
            v1 = client.CoreV1Api()
            apps_v1 = client.AppsV1Api()
            batch_v1 = client.BatchV1Api()
            networking_v1 = client.NetworkingV1Api()
            api_extensions_v1 = client.ApiextensionsV1Api()
            dynamic_client = DynamicClient(client.ApiClient())

            # Map patch type to content type
            content_type_map = {
                "strategic": "application/strategic-merge-patch+json",
                "merge": "application/merge-patch+json",
                "json": "application/json-patch+json",
            }

            if patch_type not in content_type_map:
                return {
                    "error": f"Invalid patch_type: {patch_type}. Use 'strategic', 'merge', or 'json'"
                }

            # For JSON patch, ensure it's a list
            if patch_type == "json" and not isinstance(patch, list):
                return {
                    "error": "For patch_type='json', patch must be a list of operations"
                }

            try:
                result = None

                if resource_type.lower() in ["pod", "pods", "po"]:
                    result = v1.patch_namespaced_pod(
                        name=name,
                        namespace=namespace,
                        body=patch,
                        _content_type=content_type_map[patch_type],
                    )
                    kind = "Pod"

                elif resource_type.lower() in ["deployment", "deployments", "deploy"]:
                    result = apps_v1.patch_namespaced_deployment(
                        name=name,
                        namespace=namespace,
                        body=patch,
                        _content_type=content_type_map[patch_type],
                    )
                    kind = "Deployment"

                elif resource_type.lower() in ["service", "services", "svc"]:
                    result = v1.patch_namespaced_service(
                        name=name,
                        namespace=namespace,
                        body=patch,
                        _content_type=content_type_map[patch_type],
                    )
                    kind = "Service"

                elif resource_type.lower() in ["configmap", "configmaps", "cm"]:
                    result = v1.patch_namespaced_config_map(
                        name=name,
                        namespace=namespace,
                        body=patch,
                        _content_type=content_type_map[patch_type],
                    )
                    kind = "ConfigMap"

                elif resource_type.lower() in ["secret", "secrets"]:
                    result = v1.patch_namespaced_secret(
                        name=name,
                        namespace=namespace,
                        body=patch,
                        _content_type=content_type_map[patch_type],
                    )
                    kind = "Secret"

                elif resource_type.lower() in ["replicaset", "replicasets", "rs"]:
                    result = apps_v1.patch_namespaced_replica_set(
                        name=name,
                        namespace=namespace,
                        body=patch,
                        _content_type=content_type_map[patch_type],
                    )
                    kind = "ReplicaSet"

                elif resource_type.lower() in ["statefulset", "statefulsets", "sts"]:
                    result = apps_v1.patch_namespaced_stateful_set(
                        name=name,
                        namespace=namespace,
                        body=patch,
                        _content_type=content_type_map[patch_type],
                    )
                    kind = "StatefulSet"

                elif resource_type.lower() in ["daemonset", "daemonsets", "ds"]:
                    result = apps_v1.patch_namespaced_daemon_set(
                        name=name,
                        namespace=namespace,
                        body=patch,
                        _content_type=content_type_map[patch_type],
                    )
                    kind = "DaemonSet"

                elif resource_type.lower() in ["job", "jobs"]:
                    result = batch_v1.patch_namespaced_job(
                        name=name,
                        namespace=namespace,
                        body=patch,
                        _content_type=content_type_map[patch_type],
                    )
                    kind = "Job"

                elif resource_type.lower() in ["cronjob", "cronjobs", "cj"]:
                    result = batch_v1.patch_namespaced_cron_job(
                        name=name,
                        namespace=namespace,
                        body=patch,
                        _content_type=content_type_map[patch_type],
                    )
                    kind = "CronJob"

                elif resource_type.lower() in ["ingress", "ingresses", "ing"]:
                    result = networking_v1.patch_namespaced_ingress(
                        name=name,
                        namespace=namespace,
                        body=patch,
                        _content_type=content_type_map[patch_type],
                    )
                    kind = "Ingress"

                elif resource_type.lower() in ["namespace", "namespaces", "ns"]:
                    result = v1.patch_namespace(
                        name=name,
                        body=patch,
                        _content_type=content_type_map[patch_type],
                    )
                    kind = "Namespace"

                elif resource_type.lower() in ["node", "nodes", "no"]:
                    result = v1.patch_node(
                        name=name,
                        body=patch,
                        _content_type=content_type_map[patch_type],
                    )
                    kind = "Node"

                elif resource_type.lower() in [
                    "customresourcedefinition",
                    "customresourcedefinitions",
                    "crd",
                    "crds",
                ]:
                    # Handle CRDs
                    result = api_extensions_v1.patch_custom_resource_definition(
                        name=name,
                        body=patch,
                        _content_type=content_type_map[patch_type],
                    )
                    kind = "CustomResourceDefinition"

                else:
                    # Try to handle as a custom resource using dynamic client
                    if api_version:
                        try:
                            # Get the API resource
                            api_resource = None
                            for api in dynamic_client.resources:
                                if api.api_version == api_version and (
                                    api.kind.lower() == resource_type.lower()
                                    or api.name == resource_type.lower()
                                    or api.name == resource_type.lower() + "s"
                                ):
                                    api_resource = api
                                    break

                            if not api_resource:
                                return {
                                    "error": f"Resource type {resource_type} with API version {api_version} not found"
                                }

                            # Patch the resource
                            if api_resource.namespaced and namespace:
                                result = api_resource.patch(
                                    name=name,
                                    namespace=namespace,
                                    body=patch,
                                    content_type=content_type_map[patch_type],
                                )
                            else:
                                result = api_resource.patch(
                                    name=name,
                                    body=patch,
                                    content_type=content_type_map[patch_type],
                                )

                            kind = api_resource.kind

                        except Exception as e:
                            return {
                                "error": f"Failed to patch custom resource: {str(e)}"
                            }
                    else:
                        return {
                            "error": f"Unsupported resource type: {resource_type}. For custom resources, please provide api_version parameter."
                        }

                # Handle both regular and dynamic client results
                if hasattr(result, "metadata"):
                    # Standard API result
                    resource_info = {
                        "kind": kind,
                        "name": result.metadata.name,
                        "namespace": getattr(
                            result.metadata, "namespace", "cluster-wide"
                        ),
                        "resource_version": result.metadata.resource_version,
                    }
                else:
                    # Dynamic client result (dict-like)
                    resource_info = {
                        "kind": kind,
                        "name": result.get("metadata", {}).get("name", name),
                        "namespace": result.get("metadata", {}).get(
                            "namespace", "cluster-wide"
                        ),
                        "resource_version": result.get("metadata", {}).get(
                            "resourceVersion", ""
                        ),
                    }

                return {
                    "status": "success",
                    "message": f"Successfully patched {kind} {name}",
                    "resource": resource_info,
                    "patch_type": patch_type,
                    "patch_applied": patch,
                }

            except client.exceptions.ApiException as e:
                error_body = json.loads(e.body) if e.body else {"message": str(e)}
                return {
                    "error": f"Failed to patch {resource_type} {name}",
                    "details": error_body.get("message", str(e)),
                    "status_code": e.status,
                }

        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}
        except (json.JSONDecodeError, ValueError) as e:
            return {"error": f"Invalid patch data: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
