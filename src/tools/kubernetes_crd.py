"""Kubernetes CRD (Custom Resource Definition) management tool."""

import json
import subprocess

import yaml

from src.base_tool import BaseTool


class KubernetesCRDTool(BaseTool):
    """Tool for managing Kubernetes Custom Resource Definitions and custom resources."""

    def execute(self, **kwargs):
        try:
            action = kwargs.get("action", "get")
            api_version = kwargs.get("api_version")
            kind = kwargs.get("kind")
            name = kwargs.get("name")
            namespace = kwargs.get("namespace")
            yaml_content = kwargs.get("yaml_content")
            resource_data = kwargs.get("resource_data")
            label_selector = kwargs.get("label_selector")
            field_selector = kwargs.get("field_selector")
            output_format = kwargs.get("output_format", "json")
            kubeconfig = kwargs.get("kubeconfig", None)
            context = kwargs.get("context", None)

            # Build base kubectl command
            cmd = ["kubectl"]

            # Add kubeconfig and context if provided
            if kubeconfig:
                cmd.extend(["--kubeconfig", kubeconfig])
            if context:
                cmd.extend(["--context", context])

            if action == "apply":
                # Apply a custom resource from YAML
                if not yaml_content:
                    return {"error": "yaml_content is required for apply action"}

                cmd.append("apply")
                cmd.extend(["-f", "-"])

                # Run command with YAML as input
                result = subprocess.run(
                    cmd, input=yaml_content, capture_output=True, text=True, check=False
                )

                if result.returncode == 0:
                    return {
                        "status": "success",
                        "message": "Resource applied successfully",
                        "output": result.stdout,
                    }
                return {
                    "error": "Failed to apply resource",
                    "stderr": result.stderr,
                    "stdout": result.stdout,
                }

            if action == "create":
                # Create a custom resource from structured data
                if not all([api_version, kind, name]):
                    return {
                        "error": "api_version, kind, and name are required for create action"
                    }

                if not resource_data:
                    resource_data = {}

                # Build the resource manifest
                manifest = {
                    "apiVersion": api_version,
                    "kind": kind,
                    "metadata": {"name": name},
                }

                if namespace:
                    manifest["metadata"]["namespace"] = namespace

                # Merge additional resource data
                if "metadata" in resource_data:
                    manifest["metadata"].update(resource_data["metadata"])
                    del resource_data["metadata"]

                # Add spec and other fields
                manifest.update(resource_data)

                yaml_str = yaml.dump(manifest, default_flow_style=False)

                cmd.append("apply")
                cmd.extend(["-f", "-"])

                result = subprocess.run(
                    cmd, input=yaml_str, capture_output=True, text=True, check=False
                )

                if result.returncode == 0:
                    return {
                        "status": "success",
                        "message": f"Created {kind} {name}",
                        "manifest": manifest,
                        "output": result.stdout,
                    }
                return {
                    "error": f"Failed to create {kind}",
                    "stderr": result.stderr,
                    "stdout": result.stdout,
                    "manifest": manifest,
                }

            if action == "get":
                # Get custom resources
                if not api_version:
                    return {"error": "api_version is required for get action"}

                # Use the resource type format for CRDs
                if kind:
                    # Convert kind to plural lowercase (simple pluralization)
                    resource_type = kind.lower()
                    if not resource_type.endswith("s"):
                        resource_type += "s"

                    cmd.extend(["get", f"{resource_type}.{api_version.split('/')[0]}"])
                else:
                    # List all CRDs
                    cmd.extend(["get", "crd"])

                if name:
                    cmd.append(name)

                if namespace:
                    cmd.extend(["-n", namespace])
                elif namespace is None and kind:
                    # For custom resources, check all namespaces by default
                    cmd.append("--all-namespaces")

                if label_selector:
                    cmd.extend(["-l", label_selector])

                if field_selector:
                    cmd.extend(["--field-selector", field_selector])

                # Output format
                if output_format == "yaml":
                    cmd.extend(["-o", "yaml"])
                else:
                    cmd.extend(["-o", "json"])

                result = subprocess.run(
                    cmd, capture_output=True, text=True, check=False
                )

                if result.returncode == 0:
                    try:
                        if output_format == "yaml":
                            data = yaml.safe_load(result.stdout)
                        else:
                            data = json.loads(result.stdout)

                        # Parse the results
                        if "items" in data:
                            # It's a list
                            resources = []
                            for item in data["items"]:
                                resources.append(
                                    {
                                        "name": item["metadata"]["name"],
                                        "namespace": item["metadata"].get(
                                            "namespace", ""
                                        ),
                                        "apiVersion": item.get("apiVersion", ""),
                                        "kind": item.get("kind", ""),
                                        "created": item["metadata"].get(
                                            "creationTimestamp", ""
                                        ),
                                        "spec": item.get("spec", {}),
                                        "status": item.get("status", {}),
                                    }
                                )

                            return {
                                "status": "success",
                                "resources": resources,
                                "count": len(resources),
                            }
                        # Single resource
                        return {
                            "status": "success",
                            "resource": {
                                "name": data["metadata"]["name"],
                                "namespace": data["metadata"].get("namespace", ""),
                                "apiVersion": data.get("apiVersion", ""),
                                "kind": data.get("kind", ""),
                                "created": data["metadata"].get(
                                    "creationTimestamp", ""
                                ),
                                "spec": data.get("spec", {}),
                                "status": data.get("status", {}),
                            },
                        }
                    except (json.JSONDecodeError, yaml.YAMLError):
                        return {"status": "success", "output": result.stdout}
                else:
                    return {"error": "Failed to get resources", "stderr": result.stderr}

            if action == "delete":
                # Delete custom resources
                if not all([api_version, kind, name]):
                    return {
                        "error": "api_version, kind, and name are required for delete action"
                    }

                # Convert kind to plural lowercase
                resource_type = kind.lower()
                if not resource_type.endswith("s"):
                    resource_type += "s"

                cmd.extend(
                    ["delete", f"{resource_type}.{api_version.split('/')[0]}", name]
                )

                if namespace:
                    cmd.extend(["-n", namespace])

                result = subprocess.run(
                    cmd, capture_output=True, text=True, check=False
                )

                if result.returncode == 0:
                    return {
                        "status": "success",
                        "message": f"Deleted {kind} {name}",
                        "output": result.stdout,
                    }
                return {
                    "error": f"Failed to delete {kind} {name}",
                    "stderr": result.stderr,
                }

            if action == "list_crds":
                # List all CRDs in the cluster
                cmd.extend(["get", "crd", "-o", "json"])

                result = subprocess.run(
                    cmd, capture_output=True, text=True, check=False
                )

                if result.returncode == 0:
                    try:
                        data = json.loads(result.stdout)
                        crds = []
                        for item in data.get("items", []):
                            crds.append(
                                {
                                    "name": item["metadata"]["name"],
                                    "group": item["spec"]["group"],
                                    "versions": [
                                        v["name"] for v in item["spec"]["versions"]
                                    ],
                                    "scope": item["spec"]["scope"],
                                    "kind": item["spec"]["names"]["kind"],
                                    "plural": item["spec"]["names"]["plural"],
                                    "created": item["metadata"].get(
                                        "creationTimestamp", ""
                                    ),
                                }
                            )

                        return {"status": "success", "crds": crds, "count": len(crds)}
                    except json.JSONDecodeError:
                        return {"status": "success", "output": result.stdout}
                else:
                    return {"error": "Failed to list CRDs", "stderr": result.stderr}

            return {
                "error": f"Invalid action: {action}. Valid actions are: apply, create, get, delete, list_crds"
            }

        except subprocess.TimeoutExpired as e:
            return {"error": f"Command timed out: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
