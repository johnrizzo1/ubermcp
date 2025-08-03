"""Kubernetes create tool for creating resources from YAML."""

import yaml
from kubernetes import client, config, utils

from src.base_tool import BaseTool


class KubernetesCreateTool(BaseTool):
    """Tool for creating Kubernetes resources from YAML definitions."""

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

            created_resources = []

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
                    # Create the resource
                    utils.create_from_dict(k8s_client, obj)

                    resource_info = {
                        "kind": obj.get("kind", "Unknown"),
                        "name": obj.get("metadata", {}).get("name", "Unknown"),
                        "namespace": obj.get("metadata", {}).get(
                            "namespace", "cluster-wide"
                        ),
                    }
                    created_resources.append(resource_info)

                except Exception as e:
                    return {
                        "error": f"Failed to create {obj.get('kind', 'Unknown')} {obj.get('metadata', {}).get('name', 'Unknown')}: {str(e)}",
                        "created": created_resources,
                    }

            return {
                "status": "success",
                "created": created_resources,
                "message": f"Created {len(created_resources)} resource(s)",
            }

        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
