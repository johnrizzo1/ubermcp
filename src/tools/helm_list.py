"""Helm list tool for listing installed releases."""

from src.tools.helm_base import HelmBaseTool


class HelmListTool(HelmBaseTool):
    """Tool for listing all Helm releases in the cluster."""

    def execute(self, **kwargs):
        try:
            namespace = kwargs.get("namespace", None)
            all_namespaces = kwargs.get("all_namespaces", False)
            filter_name = kwargs.get("filter", None)
            output_format = kwargs.get("output", "table")
            show_all = kwargs.get("all", False)
            deployed_only = kwargs.get("deployed", False)
            failed_only = kwargs.get("failed", False)
            pending_only = kwargs.get("pending", False)
            uninstalling_only = kwargs.get("uninstalling", False)
            kubeconfig = kwargs.get("kubeconfig", None)
            context = kwargs.get("context", None)

            # Build helm list command
            cmd = ["helm", "list"]

            # Add namespace or all-namespaces
            if all_namespaces:
                cmd.append("--all-namespaces")
            elif namespace:
                cmd.extend(["--namespace", namespace])

            # Add filter if specified
            if filter_name:
                cmd.extend(["--filter", filter_name])

            # Add status filters
            if show_all:
                cmd.append("--all")
            if deployed_only:
                cmd.append("--deployed")
            if failed_only:
                cmd.append("--failed")
            if pending_only:
                cmd.append("--pending")
            if uninstalling_only:
                cmd.append("--uninstalling")

            # Add kubeconfig args
            cmd.extend(self._get_kubeconfig_args(kubeconfig, context))

            # Add output format
            if output_format == "json":
                cmd.extend(["--output", "json"])
            elif output_format == "yaml":
                cmd.extend(["--output", "yaml"])

            # Run the command
            result = self._run_helm_command(cmd)

            if "error" in result:
                return result

            # Parse output based on format
            if output_format == "json":
                try:
                    import json

                    releases = json.loads(result["stdout"]) if result["stdout"] else []

                    return {
                        "status": "success",
                        "releases": releases,
                        "count": len(releases),
                    }
                except (json.JSONDecodeError, ValueError):
                    return {
                        "error": "Failed to parse JSON output",
                        "raw_output": result["stdout"],
                    }

            elif output_format == "yaml":
                try:
                    import yaml

                    releases = (
                        yaml.safe_load(result["stdout"]) if result["stdout"] else []
                    )

                    return {
                        "status": "success",
                        "releases": releases,
                        "count": len(releases),
                    }
                except (yaml.YAMLError, ValueError):
                    return {
                        "error": "Failed to parse YAML output",
                        "raw_output": result["stdout"],
                    }

            else:
                # Parse table output
                releases = self._parse_helm_list_output(result["stdout"])

                return {
                    "status": "success",
                    "releases": releases,
                    "count": len(releases),
                    "namespace": (
                        namespace
                        if namespace
                        else "all" if all_namespaces else "default"
                    ),
                }

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
