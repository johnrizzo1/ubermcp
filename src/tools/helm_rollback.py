"""Helm rollback tool for reverting to previous release versions."""

from src.tools.helm_base import HelmBaseTool


class HelmRollbackTool(HelmBaseTool):
    """Tool for rolling back a Helm release to a previous revision."""

    def execute(self, **kwargs):
        try:
            release_name = kwargs.get("release_name", "")
            revision = kwargs.get("revision", None)
            namespace = kwargs.get("namespace", "default")
            force = kwargs.get("force", False)
            recreate_pods = kwargs.get("recreate_pods", False)
            wait = kwargs.get("wait", False)
            timeout = kwargs.get("timeout", "5m")
            cleanup_on_fail = kwargs.get("cleanup_on_fail", False)
            dry_run = kwargs.get("dry_run", False)
            kubeconfig = kwargs.get("kubeconfig", None)
            context = kwargs.get("context", None)

            if not release_name:
                return {"error": "release_name is required"}

            # Build helm rollback command
            cmd = ["helm", "rollback", release_name]

            # Add revision if specified (otherwise rolls back to previous)
            if revision is not None:
                cmd.append(str(revision))

            # Add namespace
            cmd.extend(["--namespace", namespace])

            # Add optional flags
            if force:
                cmd.append("--force")

            if recreate_pods:
                cmd.append("--recreate-pods")

            if wait:
                cmd.append("--wait")
                cmd.extend(["--timeout", timeout])

            if cleanup_on_fail:
                cmd.append("--cleanup-on-fail")

            if dry_run:
                cmd.append("--dry-run")

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
                    "message": f"Dry run: would rollback release {release_name}"
                    + (
                        f" to revision {revision}"
                        if revision
                        else " to previous revision"
                    ),
                    "output": output,
                }
            # Extract revision info from output if possible
            import re

            rollback_match = re.search(
                r"Rollback was a success! Happy Helming!", output
            )

            return {
                "status": "success",
                "message": f"Successfully rolled back release {release_name}"
                + (f" to revision {revision}" if revision else " to previous revision"),
                "release_name": release_name,
                "namespace": namespace,
                "target_revision": revision if revision else "previous",
                "output": output,
            }

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
