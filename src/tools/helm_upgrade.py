"""Helm upgrade tool for updating existing releases."""

import os
import tempfile

import yaml

from src.tools.helm_base import HelmBaseTool


class HelmUpgradeTool(HelmBaseTool):
    """Tool for upgrading a Helm release with a new chart version or values."""

    def execute(self, **kwargs):
        try:
            release_name = kwargs.get("release_name", "")
            chart = kwargs.get("chart", "")
            namespace = kwargs.get("namespace", "default")
            values = kwargs.get("values", {})
            values_file = kwargs.get("values_file", None)
            version = kwargs.get("version", None)
            install = kwargs.get("install", True)  # Install if release doesn't exist
            force = kwargs.get("force", False)
            recreate_pods = kwargs.get("recreate_pods", False)
            wait = kwargs.get("wait", False)
            timeout = kwargs.get("timeout", "5m")
            atomic = kwargs.get("atomic", False)
            cleanup_on_fail = kwargs.get("cleanup_on_fail", False)
            dry_run = kwargs.get("dry_run", False)
            reset_values = kwargs.get("reset_values", False)
            reuse_values = kwargs.get("reuse_values", False)
            kubeconfig = kwargs.get("kubeconfig", None)
            context = kwargs.get("context", None)

            if not release_name:
                return {"error": "release_name is required"}
            if not chart:
                return {"error": "chart is required"}

            # Build helm upgrade command
            cmd = ["helm", "upgrade", release_name, chart]

            # Add namespace
            cmd.extend(["--namespace", namespace])

            # Add install flag if requested
            if install:
                cmd.append("--install")

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
            if force:
                cmd.append("--force")

            if recreate_pods:
                cmd.append("--recreate-pods")

            if wait:
                cmd.append("--wait")
                cmd.extend(["--timeout", timeout])

            if atomic:
                cmd.append("--atomic")

            if cleanup_on_fail:
                cmd.append("--cleanup-on-fail")

            if dry_run:
                cmd.append("--dry-run")

            if reset_values:
                cmd.append("--reset-values")
            elif reuse_values:
                cmd.append("--reuse-values")

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
                    "message": f"Successfully upgraded release {release_name}",
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
                    "message": f"Successfully upgraded release {release_name}",
                    "output": result["stdout"],
                }

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
