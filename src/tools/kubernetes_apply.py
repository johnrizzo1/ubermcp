"""Kubernetes apply tool for applying configuration changes."""

import yaml
from kubernetes import client, config, utils

from src.base_tool import BaseTool


class KubernetesApplyTool(BaseTool):
    """Tool for applying Kubernetes resource configurations from YAML."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()

            yaml_content = kwargs.get("yaml_content", "")
            namespace = kwargs.get("namespace", "default")

            if not yaml_content:
                return {"error": "yaml_content is required"}

            # Parse YAML content
            try:
                k8s_objects = yaml.safe_load_all(yaml_content)
            except yaml.YAMLError as e:
                return {"error": f"Invalid YAML: {str(e)}"}

            applied_resources = []

            # Create Kubernetes API client
            k8s_client = client.ApiClient()

            for obj in k8s_objects:
                if obj is None:
                    continue

                # Set namespace if not specified in object
                if "metadata" not in obj:
                    obj["metadata"] = {}
                if "namespace" not in obj["metadata"] and obj.get("kind") not in [
                    "Namespace",
                    "ClusterRole",
                    "ClusterRoleBinding",
                ]:
                    obj["metadata"]["namespace"] = namespace

                try:
                    # Try to create or update the resource
                    # First, try to get the resource to see if it exists
                    kind = obj.get("kind", "Unknown")
                    name = obj.get("metadata", {}).get("name", "Unknown")
                    resource_namespace = obj.get("metadata", {}).get(
                        "namespace", namespace
                    )

                    # Apply the resource (create or update)
                    try:
                        # Try to create first
                        utils.create_from_dict(k8s_client, obj)
                        action = "created"
                    except client.exceptions.ApiException as e:
                        if e.status == 409:  # Conflict - resource already exists
                            # Try to update/replace
                            try:
                                # Get the appropriate API client and method based on resource kind
                                api_version = obj.get("apiVersion", "v1")

                                if kind == "Deployment" and "apps/" in api_version:
                                    apps_v1 = client.AppsV1Api()
                                    apps_v1.patch_namespaced_deployment(
                                        name=name,
                                        namespace=resource_namespace,
                                        body=obj,
                                    )
                                elif kind == "Service":
                                    v1 = client.CoreV1Api()
                                    v1.patch_namespaced_service(
                                        name=name,
                                        namespace=resource_namespace,
                                        body=obj,
                                    )
                                elif kind == "ConfigMap":
                                    v1 = client.CoreV1Api()
                                    v1.patch_namespaced_config_map(
                                        name=name,
                                        namespace=resource_namespace,
                                        body=obj,
                                    )
                                elif kind == "Secret":
                                    v1 = client.CoreV1Api()
                                    v1.patch_namespaced_secret(
                                        name=name,
                                        namespace=resource_namespace,
                                        body=obj,
                                    )
                                elif kind == "StatefulSet" and "apps/" in api_version:
                                    apps_v1 = client.AppsV1Api()
                                    apps_v1.patch_namespaced_stateful_set(
                                        name=name,
                                        namespace=resource_namespace,
                                        body=obj,
                                    )
                                elif kind == "DaemonSet" and "apps/" in api_version:
                                    apps_v1 = client.AppsV1Api()
                                    apps_v1.patch_namespaced_daemon_set(
                                        name=name,
                                        namespace=resource_namespace,
                                        body=obj,
                                    )
                                elif kind == "Job" and "batch/" in api_version:
                                    batch_v1 = client.BatchV1Api()
                                    batch_v1.patch_namespaced_job(
                                        name=name,
                                        namespace=resource_namespace,
                                        body=obj,
                                    )
                                elif kind == "CronJob" and "batch/" in api_version:
                                    batch_v1 = client.BatchV1Api()
                                    batch_v1.patch_namespaced_cron_job(
                                        name=name,
                                        namespace=resource_namespace,
                                        body=obj,
                                    )
                                elif (
                                    kind == "Ingress"
                                    and "networking.k8s.io/" in api_version
                                ):
                                    networking_v1 = client.NetworkingV1Api()
                                    networking_v1.patch_namespaced_ingress(
                                        name=name,
                                        namespace=resource_namespace,
                                        body=obj,
                                    )
                                else:
                                    # For other resources, try generic patch
                                    # This might not work for all resource types
                                    raise NotImplementedError(
                                        f"Update not implemented for {kind}"
                                    ) from e

                                action = "configured"
                            except Exception as update_error:
                                return {
                                    "error": f"Failed to update {kind} {name}: {str(update_error)}",
                                    "applied": applied_resources,
                                }
                        else:
                            raise e

                    resource_info = {
                        "kind": kind,
                        "name": name,
                        "namespace": (
                            resource_namespace
                            if resource_namespace != namespace
                            else resource_namespace
                        ),
                        "action": action,
                    }
                    applied_resources.append(resource_info)

                except Exception as e:
                    return {
                        "error": f"Failed to apply {obj.get('kind', 'Unknown')} {obj.get('metadata', {}).get('name', 'Unknown')}: {str(e)}",
                        "applied": applied_resources,
                    }

            return {
                "status": "success",
                "applied": applied_resources,
                "message": f"Applied {len(applied_resources)} resource(s)",
            }

        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
