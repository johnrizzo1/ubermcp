"""Kubernetes edit tool for modifying resources."""

from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesEditTool(BaseTool):
    """Tool for editing Kubernetes resources by applying patches."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()

            resource_type = kwargs.get("resource_type", "")
            name = kwargs.get("name", "")
            namespace = kwargs.get("namespace", "default")
            edit_type = kwargs.get("edit_type", "merge")  # merge or replace
            changes = kwargs.get("changes", {})

            if not resource_type:
                return {"error": "resource_type is required"}
            if not name:
                return {"error": "name is required"}
            if not changes:
                return {"error": "changes is required"}

            # Initialize API clients
            v1 = client.CoreV1Api()
            apps_v1 = client.AppsV1Api()

            try:
                # Get the current resource
                current_resource = None

                if resource_type.lower() in ["pod", "pods", "po"]:
                    current_resource = v1.read_namespaced_pod(name, namespace)

                    # Apply changes
                    if edit_type == "merge":
                        # Deep merge changes into current resource
                        self._deep_merge(current_resource.to_dict(), changes)
                    else:
                        # Replace specific fields
                        for key, value in changes.items():
                            if hasattr(current_resource, key):
                                setattr(current_resource, key, value)

                    # Update the resource
                    updated = v1.patch_namespaced_pod(name, namespace, current_resource)
                    return {
                        "status": "success",
                        "resource": {
                            "kind": "Pod",
                            "name": updated.metadata.name,
                            "namespace": updated.metadata.namespace,
                        },
                        "message": f"Successfully edited pod {name}",
                    }

                if resource_type.lower() in ["deployment", "deployments", "deploy"]:
                    current_resource = apps_v1.read_namespaced_deployment(
                        name, namespace
                    )

                    if edit_type == "merge":
                        # For deployments, commonly edited fields
                        if "replicas" in changes:
                            current_resource.spec.replicas = changes["replicas"]
                        if "image" in changes:
                            # Update all containers with the new image
                            for (
                                container
                            ) in current_resource.spec.template.spec.containers:
                                container.image = changes["image"]
                        if "spec" in changes:
                            # Deep merge spec changes
                            self._merge_spec(current_resource.spec, changes["spec"])
                        if "metadata" in changes:
                            # Merge metadata changes
                            if "labels" in changes["metadata"]:
                                if not current_resource.metadata.labels:
                                    current_resource.metadata.labels = {}
                                current_resource.metadata.labels.update(
                                    changes["metadata"]["labels"]
                                )
                            if "annotations" in changes["metadata"]:
                                if not current_resource.metadata.annotations:
                                    current_resource.metadata.annotations = {}
                                current_resource.metadata.annotations.update(
                                    changes["metadata"]["annotations"]
                                )

                    # Update the resource
                    updated = apps_v1.patch_namespaced_deployment(
                        name, namespace, current_resource
                    )
                    return {
                        "status": "success",
                        "resource": {
                            "kind": "Deployment",
                            "name": updated.metadata.name,
                            "namespace": updated.metadata.namespace,
                        },
                        "message": f"Successfully edited deployment {name}",
                    }

                if resource_type.lower() in ["service", "services", "svc"]:
                    current_resource = v1.read_namespaced_service(name, namespace)

                    if edit_type == "merge":
                        if "spec" in changes:
                            if "type" in changes["spec"]:
                                current_resource.spec.type = changes["spec"]["type"]
                            if "ports" in changes["spec"]:
                                # Update ports
                                new_ports = []
                                for port_data in changes["spec"]["ports"]:
                                    port = client.V1ServicePort(
                                        port=port_data.get("port"),
                                        target_port=port_data.get(
                                            "targetPort", port_data.get("port")
                                        ),
                                        protocol=port_data.get("protocol", "TCP"),
                                        name=port_data.get("name"),
                                    )
                                    new_ports.append(port)
                                current_resource.spec.ports = new_ports
                            if "selector" in changes["spec"]:
                                current_resource.spec.selector = changes["spec"][
                                    "selector"
                                ]

                    # Update the resource
                    updated = v1.patch_namespaced_service(
                        name, namespace, current_resource
                    )
                    return {
                        "status": "success",
                        "resource": {
                            "kind": "Service",
                            "name": updated.metadata.name,
                            "namespace": updated.metadata.namespace,
                        },
                        "message": f"Successfully edited service {name}",
                    }

                if resource_type.lower() in ["configmap", "configmaps", "cm"]:
                    current_resource = v1.read_namespaced_config_map(name, namespace)

                    if edit_type == "merge":
                        if "data" in changes:
                            if not current_resource.data:
                                current_resource.data = {}
                            current_resource.data.update(changes["data"])
                        if "binaryData" in changes:
                            if not current_resource.binary_data:
                                current_resource.binary_data = {}
                            current_resource.binary_data.update(changes["binaryData"])

                    # Update the resource
                    updated = v1.patch_namespaced_config_map(
                        name, namespace, current_resource
                    )
                    return {
                        "status": "success",
                        "resource": {
                            "kind": "ConfigMap",
                            "name": updated.metadata.name,
                            "namespace": updated.metadata.namespace,
                        },
                        "message": f"Successfully edited configmap {name}",
                    }

                if resource_type.lower() in ["secret", "secrets"]:
                    current_resource = v1.read_namespaced_secret(name, namespace)

                    if edit_type == "merge":
                        if "data" in changes:
                            if not current_resource.data:
                                current_resource.data = {}
                            current_resource.data.update(changes["data"])
                        if "stringData" in changes:
                            if not current_resource.string_data:
                                current_resource.string_data = {}
                            current_resource.string_data.update(changes["stringData"])

                    # Update the resource
                    updated = v1.patch_namespaced_secret(
                        name, namespace, current_resource
                    )
                    return {
                        "status": "success",
                        "resource": {
                            "kind": "Secret",
                            "name": updated.metadata.name,
                            "namespace": updated.metadata.namespace,
                        },
                        "message": f"Successfully edited secret {name}",
                    }

                return {
                    "error": f"Edit not implemented for resource type: {resource_type}"
                }

            except client.exceptions.ApiException as e:
                return {"error": f"Failed to edit {resource_type} {name}: {e.body}"}

        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    def _deep_merge(self, base, updates):
        """Deep merge updates into base dictionary"""
        for key, value in updates.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _merge_spec(self, spec, spec_changes):
        """Merge changes into a spec object"""
        for key, value in spec_changes.items():
            if hasattr(spec, key):
                if isinstance(value, dict) and hasattr(getattr(spec, key), "__dict__"):
                    # Recursively merge nested objects
                    self._merge_spec(getattr(spec, key), value)
                else:
                    setattr(spec, key, value)
