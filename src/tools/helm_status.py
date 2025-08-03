"""Helm status tool for checking release status."""

import json

import yaml

from src.tools.helm_base import HelmBaseTool


class HelmStatusTool(HelmBaseTool):
    """Tool for displaying the status of a Helm release."""

    def execute(self, **kwargs):
        try:
            release_name = kwargs.get("release_name", "")
            namespace = kwargs.get("namespace", "default")
            revision = kwargs.get("revision", None)
            output_format = kwargs.get("output", "json")
            show_desc = kwargs.get("show_desc", False)
            kubeconfig = kwargs.get("kubeconfig", None)
            context = kwargs.get("context", None)

            if not release_name:
                return {"error": "release_name is required"}

            # Build helm status command
            cmd = ["helm", "status", release_name]

            # Add namespace
            cmd.extend(["--namespace", namespace])

            # Add revision if specified
            if revision is not None:
                cmd.extend(["--revision", str(revision)])

            # Add output format
            if output_format in ["json", "yaml"]:
                cmd.extend(["--output", output_format])

            # Add show-desc flag
            if show_desc:
                cmd.append("--show-desc")

            # Add kubeconfig args
            cmd.extend(self._get_kubeconfig_args(kubeconfig, context))

            # Run the command
            result = self._run_helm_command(cmd)

            if "error" in result:
                return result

            # Parse output based on format
            if output_format == "json":
                try:
                    status_info = json.loads(result["stdout"])

                    return {
                        "status": "success",
                        "release": {
                            "name": status_info.get("name"),
                            "namespace": status_info.get("namespace"),
                            "revision": status_info.get("version"),
                            "status": status_info.get("info", {}).get("status"),
                            "last_deployed": status_info.get("info", {}).get(
                                "last_deployed"
                            ),
                            "description": status_info.get("info", {}).get(
                                "description", ""
                            ),
                            "chart": {
                                "name": status_info.get("chart", {})
                                .get("metadata", {})
                                .get("name"),
                                "version": status_info.get("chart", {})
                                .get("metadata", {})
                                .get("version"),
                                "app_version": status_info.get("chart", {})
                                .get("metadata", {})
                                .get("appVersion"),
                            },
                            "notes": status_info.get("info", {}).get("notes", ""),
                            "resources": status_info.get("info", {}).get(
                                "resources", {}
                            ),
                        },
                    }
                except Exception as e:
                    return {
                        "error": f"Failed to parse JSON output: {str(e)}",
                        "raw_output": result["stdout"],
                    }

            elif output_format == "yaml":
                try:
                    status_info = yaml.safe_load(result["stdout"])

                    return {
                        "status": "success",
                        "release": {
                            "name": status_info.get("name"),
                            "namespace": status_info.get("namespace"),
                            "revision": status_info.get("version"),
                            "status": status_info.get("info", {}).get("status"),
                            "last_deployed": status_info.get("info", {}).get(
                                "last_deployed"
                            ),
                            "description": status_info.get("info", {}).get(
                                "description", ""
                            ),
                            "chart": {
                                "name": status_info.get("chart", {})
                                .get("metadata", {})
                                .get("name"),
                                "version": status_info.get("chart", {})
                                .get("metadata", {})
                                .get("version"),
                                "app_version": status_info.get("chart", {})
                                .get("metadata", {})
                                .get("appVersion"),
                            },
                            "notes": status_info.get("info", {}).get("notes", ""),
                            "resources": status_info.get("info", {}).get(
                                "resources", {}
                            ),
                        },
                    }
                except Exception as e:
                    return {
                        "error": f"Failed to parse YAML output: {str(e)}",
                        "raw_output": result["stdout"],
                    }

            else:
                # Parse text output
                output_lines = result["stdout"].strip().split("\n")

                # Extract basic information from text output
                status_dict = {}
                current_section = None

                for line in output_lines:
                    if line.startswith("NAME:"):
                        status_dict["name"] = line.split(":", 1)[1].strip()
                    elif line.startswith("LAST DEPLOYED:"):
                        status_dict["last_deployed"] = line.split(":", 1)[1].strip()
                    elif line.startswith("NAMESPACE:"):
                        status_dict["namespace"] = line.split(":", 1)[1].strip()
                    elif line.startswith("STATUS:"):
                        status_dict["status"] = line.split(":", 1)[1].strip()
                    elif line.startswith("REVISION:"):
                        status_dict["revision"] = line.split(":", 1)[1].strip()

                return {
                    "status": "success",
                    "release": status_dict,
                    "raw_output": result["stdout"],
                }

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
