"""Helm search tool for finding charts in repositories."""

import json

import yaml

from src.tools.helm_base import HelmBaseTool


class HelmSearchTool(HelmBaseTool):
    """Tool for searching Helm charts in repositories."""

    def execute(self, **kwargs):
        try:
            search_type = kwargs.get("search_type", "repo")  # repo or hub
            keyword = kwargs.get("keyword", "")
            version = kwargs.get("version", None)
            versions = kwargs.get("versions", False)  # Show all versions
            output_format = kwargs.get("output", "table")
            devel = kwargs.get("devel", False)  # Include development versions
            max_col_width = kwargs.get("max_col_width", 50)
            kubeconfig = kwargs.get("kubeconfig", None)
            context = kwargs.get("context", None)

            # Build helm search command
            cmd = ["helm", "search", search_type]

            # Add keyword if provided
            if keyword:
                cmd.append(keyword)

            # Add version constraint if specified
            if version:
                cmd.extend(["--version", version])

            # Add flags
            if versions:
                cmd.append("--versions")

            if devel:
                cmd.append("--devel")

            # Add output format
            if output_format in ["json", "yaml"]:
                cmd.extend(["--output", output_format])

            # Add max column width for table output
            if output_format == "table":
                cmd.extend(["--max-col-width", str(max_col_width)])

            # Add kubeconfig args
            cmd.extend(self._get_kubeconfig_args(kubeconfig, context))

            # Run the command
            result = self._run_helm_command(cmd)

            if "error" in result:
                return result

            # Parse output based on format
            if output_format == "json":
                try:
                    charts = json.loads(result["stdout"]) if result["stdout"] else []

                    return {
                        "status": "success",
                        "search_type": search_type,
                        "keyword": keyword,
                        "charts": charts,
                        "count": len(charts),
                    }
                except (json.JSONDecodeError, ValueError):
                    return {
                        "error": "Failed to parse JSON output",
                        "raw_output": result["stdout"],
                    }

            elif output_format == "yaml":
                try:
                    charts = (
                        yaml.safe_load(result["stdout"]) if result["stdout"] else []
                    )

                    return {
                        "status": "success",
                        "search_type": search_type,
                        "keyword": keyword,
                        "charts": charts,
                        "count": len(charts),
                    }
                except (yaml.YAMLError, ValueError):
                    return {
                        "error": "Failed to parse YAML output",
                        "raw_output": result["stdout"],
                    }

            else:
                # Parse table output
                lines = result["stdout"].strip().split("\n")
                if not lines or len(lines) < 2:
                    return {
                        "status": "success",
                        "search_type": search_type,
                        "keyword": keyword,
                        "charts": [],
                        "count": 0,
                    }

                charts = []
                for line in lines[1:]:  # Skip header
                    parts = line.split("\t")
                    if search_type == "repo" and len(parts) >= 3:
                        charts.append(
                            {
                                "name": parts[0].strip(),
                                "chart_version": parts[1].strip(),
                                "app_version": (
                                    parts[2].strip() if len(parts) > 2 else ""
                                ),
                                "description": (
                                    parts[3].strip() if len(parts) > 3 else ""
                                ),
                            }
                        )
                    elif search_type == "hub" and len(parts) >= 4:
                        charts.append(
                            {
                                "url": parts[0].strip(),
                                "chart_version": parts[1].strip(),
                                "app_version": parts[2].strip(),
                                "description": (
                                    parts[3].strip() if len(parts) > 3 else ""
                                ),
                            }
                        )

                return {
                    "status": "success",
                    "search_type": search_type,
                    "keyword": keyword,
                    "charts": charts,
                    "count": len(charts),
                }

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
