"""Helm install tool for deploying charts to Kubernetes."""

import os
import tempfile
import time

import yaml

from src.tools.helm_base import HelmBaseTool


class HelmInstallTool(HelmBaseTool):
    """Tool for installing Helm charts to create new releases."""

    def execute(self, **kwargs):
        try:
            release_name = kwargs.get("release_name", "")
            chart = kwargs.get("chart", "")
            # Convert to absolute path if it's a local directory
            if (
                chart
                and not chart.startswith(("http://", "https://"))
                and os.path.exists(chart)
            ):
                chart = os.path.abspath(chart)
            namespace = kwargs.get("namespace", "default")
            values = kwargs.get("values", {})
            values_file = kwargs.get("values_file", None)
            version = kwargs.get("version", None)
            create_namespace = kwargs.get("create_namespace", True)
            wait = kwargs.get("wait", False)
            timeout = kwargs.get("timeout", "5m")
            atomic = kwargs.get("atomic", False)
            dry_run = kwargs.get("dry_run", False)
            build_dependencies = kwargs.get("build_dependencies", True)
            kubeconfig = kwargs.get("kubeconfig", None)
            context = kwargs.get("context", None)

            if not release_name:
                return {"error": "release_name is required"}
            if not chart:
                return {"error": "chart is required"}

            # Check if chart is a local directory and build dependencies if needed
            dependency_build_output = None
            if build_dependencies and os.path.isdir(chart):
                # Debug: Check chart directory contents
                charts_dir = os.path.join(chart, "charts")
                chart_info = {
                    "chart_path": chart,
                    "charts_dir_exists": os.path.exists(charts_dir),
                    "charts_dir_contents": (
                        os.listdir(charts_dir) if os.path.exists(charts_dir) else []
                    ),
                }

                chart_yaml_path = os.path.join(chart, "Chart.yaml")
                if os.path.exists(chart_yaml_path):
                    # Add initial chart info to dependency output
                    chart_info["chart_yaml_exists"] = True

                    # Run helm dependency build for local charts
                    dep_cmd = ["helm", "dependency", "build", chart]
                    dep_cmd.extend(self._get_kubeconfig_args(kubeconfig, context))

                    dep_result = self._run_helm_command(dep_cmd)
                    dependency_build_output = {
                        "command": " ".join(dep_cmd),
                        "result": dep_result,
                        "chart_info_before": chart_info.copy(),
                    }

                    # Check if dependency build was successful
                    if dep_result.get("status") != "success":
                        stderr = dep_result.get("stderr", "")
                        stdout = dep_result.get("stdout", "")

                        # Check for common non-error conditions
                        if any(
                            msg in stderr.lower()
                            for msg in ["no dependencies", "no requirements found"]
                        ):
                            pass  # No dependencies to build, continue
                        else:
                            # Real error occurred
                            return {
                                "error": "Failed to build chart dependencies",
                                "details": dep_result.get("error", "Unknown error"),
                                "stderr": stderr,
                                "stdout": stdout,
                                "suggestion": "Try running 'helm dependency build' manually first",
                            }
                    # If we get here, dependencies were handled (built or not needed)
                    # Update chart info after dependency build
                    chart_info_after = {
                        "charts_dir_exists": os.path.exists(charts_dir),
                        "charts_dir_contents": (
                            os.listdir(charts_dir) if os.path.exists(charts_dir) else []
                        ),
                    }
                    if dependency_build_output:
                        dependency_build_output["chart_info_after"] = chart_info_after

                    # Verify dependencies were actually downloaded
                    if dep_result.get(
                        "status"
                    ) == "success" and "Saving" in dep_result.get("stdout", ""):
                        # Check if charts directory has the expected files
                        if not os.path.exists(charts_dir) or not os.listdir(charts_dir):
                            return {
                                "error": "Dependencies were downloaded but charts directory is empty",
                                "dependency_build_info": dependency_build_output,
                                "suggestion": "There may be a permission or path issue. Try running 'helm dependency build' manually.",
                            }

                        # Add a small delay to ensure filesystem sync
                        time.sleep(0.5)

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
                # Include dependency build info in error if available
                if dependency_build_output:
                    result["dependency_build_info"] = dependency_build_output
                return result

            # Parse JSON output
            try:
                import json

                release_info = json.loads(result["stdout"])

                response = {
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
                if dependency_build_output:
                    response["dependency_build_info"] = dependency_build_output
                return response
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
