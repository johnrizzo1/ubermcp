"""Helm history tool for retrieving release revision history."""

import json

import yaml

from src.tools.helm_base import HelmBaseTool


class HelmHistoryTool(HelmBaseTool):
    """Tool for displaying the release history of a Helm chart."""

    def execute(self, **kwargs):
        try:
            release_name = kwargs.get("release_name", "")
            namespace = kwargs.get("namespace", "default")
            max_revisions = kwargs.get("max", None)
            output_format = kwargs.get("output", "table")
            kubeconfig = kwargs.get("kubeconfig", None)
            context = kwargs.get("context", None)

            if not release_name:
                return {"error": "release_name is required"}

            # Build helm history command
            cmd = ["helm", "history", release_name]

            # Add namespace
            cmd.extend(["--namespace", namespace])

            # Add max revisions if specified
            if max_revisions is not None:
                cmd.extend(["--max", str(max_revisions)])

            # Add output format
            if output_format in ["json", "yaml"]:
                cmd.extend(["--output", output_format])

            # Add kubeconfig args
            cmd.extend(self._get_kubeconfig_args(kubeconfig, context))

            # Run the command
            result = self._run_helm_command(cmd)

            if "error" in result:
                return result

            # Parse output based on format
            if output_format == "json":
                try:
                    history = json.loads(result["stdout"]) if result["stdout"] else []

                    return {
                        "status": "success",
                        "release_name": release_name,
                        "namespace": namespace,
                        "history": history,
                        "revision_count": len(history),
                    }
                except Exception as e:
                    return {
                        "error": f"Failed to parse JSON output: {str(e)}",
                        "raw_output": result["stdout"],
                    }

            elif output_format == "yaml":
                try:
                    history = (
                        yaml.safe_load(result["stdout"]) if result["stdout"] else []
                    )

                    return {
                        "status": "success",
                        "release_name": release_name,
                        "namespace": namespace,
                        "history": history,
                        "revision_count": len(history),
                    }
                except Exception as e:
                    return {
                        "error": f"Failed to parse YAML output: {str(e)}",
                        "raw_output": result["stdout"],
                    }

            else:
                # Parse table output
                lines = result["stdout"].strip().split("\n")
                if not lines or len(lines) < 2:
                    return {
                        "status": "success",
                        "release_name": release_name,
                        "namespace": namespace,
                        "history": [],
                        "revision_count": 0,
                    }

                # Skip header
                history = []
                for line in lines[1:]:
                    parts = line.split("\t")
                    if len(parts) >= 7:  # Expected format
                        history.append(
                            {
                                "revision": (
                                    int(parts[0].strip())
                                    if parts[0].strip().isdigit()
                                    else parts[0].strip()
                                ),
                                "updated": parts[1].strip(),
                                "status": parts[2].strip(),
                                "chart": parts[3].strip(),
                                "app_version": parts[4].strip(),
                                "description": (
                                    parts[5].strip() if len(parts) > 5 else ""
                                ),
                            }
                        )

                return {
                    "status": "success",
                    "release_name": release_name,
                    "namespace": namespace,
                    "history": history,
                    "revision_count": len(history),
                }

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
