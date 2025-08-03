"""Helm install tool for deploying charts to Kubernetes."""

import os
import tempfile

import yaml

from src.tools.helm_base import HelmBaseTool


class HelmInstallTool(HelmBaseTool):
    """Tool for installing Helm charts to create new releases."""

    def execute(self, **kwargs):
        try:
            release_name = kwargs.get("release_name", "")
            chart = kwargs.get("chart", "")
            namespace = kwargs.get("namespace", "default")
            values = kwargs.get("values", {})
            values_file = kwargs.get("values_file", None)
            version = kwargs.get("version", None)
            create_namespace = kwargs.get("create_namespace", True)
            wait = kwargs.get("wait", False)
            timeout = kwargs.get("timeout", "5m")
            atomic = kwargs.get("atomic", False)
            dry_run = kwargs.get("dry_run", False)
            kubeconfig = kwargs.get("kubeconfig", None)
            context = kwargs.get("context", None)

            if not release_name:
                return {"error": "release_name is required"}
            if not chart:
                return {"error": "chart is required"}

            # Build helm install command
            cmd = ["helm", "install", release_name, chart]

            # Add namespace
            cmd.extend(["--namespace", namespace])

            # Add create-namespace flag if requested
            if create_namespace:
                cmd.append("--create-namespace")

            # Add version if specified
            if version:
                cmd.extend(["--version", version])

            # Add kubeconfig args
            cmd.extend(self._get_kubeconfig_args(kubeconfig, context))

            # Handle values
            temp_values_file = None
            if values:
                # Create temporary values file
                temp_values_file = tempfile.NamedTemporaryFile(
                    mode="w", suffix=".yaml", delete=False
                )
                yaml.dump(values, temp_values_file)
                temp_values_file.close()
                cmd.extend(["--values", temp_values_file.name])

            # Add external values file if provided
            if values_file:
                cmd.extend(["--values", values_file])

            # Add optional flags
            if wait:
                cmd.append("--wait")
                cmd.extend(["--timeout", timeout])

            if atomic:
                cmd.append("--atomic")

            if dry_run:
                cmd.append("--dry-run")

            # Add output format
            cmd.extend(["--output", "json"])

            # Run the command
            result = self._run_helm_command(cmd)

            # Clean up temporary file
            if temp_values_file:
                os.unlink(temp_values_file.name)

            if "error" in result:
                return result

            # Parse JSON output
            try:
                import json

                release_info = json.loads(result["stdout"])

                return {
                    "status": "success",
                    "message": f"Successfully installed release {release_name}",
                    "release": {
                        "name": release_info.get("name"),
                        "namespace": release_info.get("namespace"),
                        "revision": release_info.get("version", 1),
                        "status": release_info.get("info", {}).get("status"),
                        "chart": f"{release_info.get('chart', {}).get('metadata', {}).get('name')}-{release_info.get('chart', {}).get('metadata', {}).get('version')}",
                        "app_version": release_info.get("chart", {})
                        .get("metadata", {})
                        .get("appVersion"),
                        "notes": release_info.get("info", {}).get("notes", ""),
                    },
                }
            except (json.JSONDecodeError, ValueError, KeyError):
                # Fallback for non-JSON output
                return {
                    "status": "success",
                    "message": f"Successfully installed release {release_name}",
                    "output": result["stdout"],
                }

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
