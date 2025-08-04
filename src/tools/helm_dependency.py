"""Helm dependency management tool for building and updating chart dependencies."""

import os

from src.tools.helm_base import HelmBaseTool


class HelmDependencyTool(HelmBaseTool):
    """Tool for managing Helm chart dependencies."""

    def execute(self, **kwargs):
        try:
            action = kwargs.get("action", "build")
            chart_path = kwargs.get("chart_path", ".")
            verify = kwargs.get("verify", False)
            skip_refresh = kwargs.get("skip_refresh", False)
            keyring = kwargs.get("keyring", None)
            kubeconfig = kwargs.get("kubeconfig", None)
            context = kwargs.get("context", None)

            # Validate chart path
            if not os.path.exists(chart_path):
                return {"error": f"Chart path does not exist: {chart_path}"}

            # Check if it's a valid chart directory
            chart_yaml = os.path.join(chart_path, "Chart.yaml")
            if not os.path.exists(chart_yaml):
                return {"error": f"No Chart.yaml found in {chart_path}"}

            # Build helm dependency command
            cmd = ["helm", "dependency", action]

            # Add chart path
            cmd.append(chart_path)

            # Add kubeconfig args
            cmd.extend(self._get_kubeconfig_args(kubeconfig, context))

            # Add optional flags based on action
            if action == "build":
                if verify:
                    cmd.append("--verify")
                if skip_refresh:
                    cmd.append("--skip-refresh")
                if keyring:
                    cmd.extend(["--keyring", keyring])
            elif action == "update":
                if verify:
                    cmd.append("--verify")
                if skip_refresh:
                    cmd.append("--skip-refresh")
                if keyring:
                    cmd.extend(["--keyring", keyring])
            elif action == "list":
                # List has different output format
                pass
            else:
                return {
                    "error": f"Invalid action: {action}. Must be 'build', 'update', or 'list'"
                }

            # Run the command
            result = self._run_helm_command(cmd)

            if "error" in result:
                return result

            # Parse output based on action
            stdout = result.get("stdout", "")
            stderr = result.get("stderr", "")

            if action == "list":
                # Parse dependency list
                dependencies = []
                lines = stdout.strip().split("\n")
                if len(lines) > 1:  # Skip header
                    for line in lines[1:]:
                        parts = line.split()
                        if len(parts) >= 3:
                            dependencies.append(
                                {
                                    "name": parts[0],
                                    "version": parts[1],
                                    "repository": parts[2],
                                    "status": parts[3] if len(parts) > 3 else "unknown",
                                }
                            )

                return {
                    "status": "success",
                    "action": action,
                    "chart_path": chart_path,
                    "dependencies": dependencies,
                }
            # For build and update actions
            # Check if there were no dependencies
            if (
                "no dependencies" in stderr.lower()
                or "no requirements found" in stderr.lower()
            ):
                return {
                    "status": "success",
                    "action": action,
                    "chart_path": chart_path,
                    "message": "No dependencies found in Chart.yaml",
                }

            # Check if dependencies were successfully processed
            if "Saving" in stdout and "charts/" in stdout:
                # Extract saved dependencies from output
                saved_deps = []
                for line in stdout.split("\n"):
                    if "Saving" in line and "charts/" in line:
                        # Extract dependency info from lines like:
                        # "Saving 3 charts"
                        # "Saving kafka-1.2.3 to charts/"
                        parts = line.split()
                        if len(parts) > 1 and parts[1] != "charts":
                            saved_deps.append(parts[1])

                return {
                    "status": "success",
                    "action": action,
                    "chart_path": chart_path,
                    "message": f"Successfully {action}ed dependencies",
                    "saved_dependencies": saved_deps,
                    "output": stdout,
                }
            # Generic success
            return {
                "status": "success",
                "action": action,
                "chart_path": chart_path,
                "message": f"Successfully completed dependency {action}",
                "output": stdout,
            }

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
