"""Helm uninstall tool for removing releases from Kubernetes."""

from src.tools.helm_base import HelmBaseTool


class HelmUninstallTool(HelmBaseTool):
    """Tool for uninstalling Helm releases from the cluster."""

    def execute(self, **kwargs):
        try:
            release_name = kwargs.get("release_name", "")
            namespace = kwargs.get("namespace", "default")
            keep_history = kwargs.get("keep_history", False)
            dry_run = kwargs.get("dry_run", False)
            no_hooks = kwargs.get("no_hooks", False)
            timeout = kwargs.get("timeout", "5m")
            wait = kwargs.get("wait", False)
            kubeconfig = kwargs.get("kubeconfig", None)
            context = kwargs.get("context", None)

            if not release_name:
                return {"error": "release_name is required"}

            # Build helm uninstall command
            cmd = ["helm", "uninstall", release_name]

            # Add namespace
            cmd.extend(["--namespace", namespace])

            # Add optional flags
            if keep_history:
                cmd.append("--keep-history")

            if dry_run:
                cmd.append("--dry-run")

            if no_hooks:
                cmd.append("--no-hooks")

            if wait:
                cmd.append("--wait")

            # Add timeout
            cmd.extend(["--timeout", timeout])

            # Add kubeconfig args
            cmd.extend(self._get_kubeconfig_args(kubeconfig, context))

            # Run the command
            result = self._run_helm_command(cmd)

            if "error" in result:
                return result

            # Parse output
            output = result["stdout"].strip()

            if dry_run:
                return {
                    "status": "dry_run",
                    "message": f"Dry run: would uninstall release {release_name}",
                    "output": output,
                }
            return {
                "status": "success",
                "message": f"Successfully uninstalled release {release_name}",
                "release_name": release_name,
                "namespace": namespace,
                "kept_history": keep_history,
                "output": output,
            }

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
