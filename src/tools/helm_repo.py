"""Helm repository tool for managing chart repositories."""

import json

from src.tools.helm_base import HelmBaseTool


class HelmRepoTool(HelmBaseTool):
    """Tool for managing Helm chart repositories."""

    def execute(self, **kwargs):
        try:
            action = kwargs.get("action", "list")
            repo_name = kwargs.get("repo_name", "")
            repo_url = kwargs.get("repo_url", "")
            username = kwargs.get("username", None)
            password = kwargs.get("password", None)
            force_update = kwargs.get("force_update", False)
            insecure_skip_tls_verify = kwargs.get("insecure_skip_tls_verify", False)
            kubeconfig = kwargs.get("kubeconfig", None)
            context = kwargs.get("context", None)

            if action == "add":
                return self._add_repo(
                    repo_name,
                    repo_url,
                    username,
                    password,
                    force_update,
                    insecure_skip_tls_verify,
                    kubeconfig,
                    context,
                )
            if action == "remove":
                return self._remove_repo(repo_name, kubeconfig, context)
            if action == "list":
                return self._list_repos(kubeconfig, context)
            if action == "update":
                return self._update_repos(repo_name, kubeconfig, context)
            if action == "index":
                directory = kwargs.get("directory", ".")
                return self._index_repo(directory, kubeconfig, context)
            return {
                "error": f"Unknown action: {action}. Supported: add, remove, list, update, index"
            }

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    def _add_repo(
        self,
        repo_name,
        repo_url,
        username,
        password,
        force_update,
        insecure_skip_tls_verify,
        kubeconfig,
        context,
    ):
        """Add a chart repository"""
        if not repo_name:
            return {"error": "repo_name is required for add action"}
        if not repo_url:
            return {"error": "repo_url is required for add action"}

        cmd = ["helm", "repo", "add", repo_name, repo_url]

        # Add authentication if provided
        if username:
            cmd.extend(["--username", username])
        if password:
            cmd.extend(["--password", password])

        # Add optional flags
        if force_update:
            cmd.append("--force-update")
        if insecure_skip_tls_verify:
            cmd.append("--insecure-skip-tls-verify")

        # Add kubeconfig args
        cmd.extend(self._get_kubeconfig_args(kubeconfig, context))

        result = self._run_helm_command(cmd)

        if "error" in result:
            return result

        return {
            "status": "success",
            "message": f"Successfully added repository {repo_name}",
            "repo": {"name": repo_name, "url": repo_url},
            "output": result["stdout"],
        }

    def _remove_repo(self, repo_name, kubeconfig, context):
        """Remove a chart repository"""
        if not repo_name:
            return {"error": "repo_name is required for remove action"}

        cmd = ["helm", "repo", "remove", repo_name]

        # Add kubeconfig args
        cmd.extend(self._get_kubeconfig_args(kubeconfig, context))

        result = self._run_helm_command(cmd)

        if "error" in result:
            return result

        return {
            "status": "success",
            "message": f"Successfully removed repository {repo_name}",
            "output": result["stdout"],
        }

    def _list_repos(self, kubeconfig, context):
        """List chart repositories"""
        cmd = ["helm", "repo", "list", "--output", "json"]

        # Add kubeconfig args
        cmd.extend(self._get_kubeconfig_args(kubeconfig, context))

        result = self._run_helm_command(cmd)

        if "error" in result:
            # Check if it's the "no repositories" error
            if "no repositories to show" in result.get("stderr", ""):
                return {"status": "success", "repositories": [], "count": 0}
            return result

        try:
            repos = json.loads(result["stdout"]) if result["stdout"] else []

            return {"status": "success", "repositories": repos, "count": len(repos)}
        except (json.JSONDecodeError, ValueError):
            # Fallback to parsing table output
            cmd = ["helm", "repo", "list"]
            result = self._run_helm_command(cmd)

            if "error" in result:
                return result

            lines = result["stdout"].strip().split("\n")
            if not lines or len(lines) < 2:
                return {"status": "success", "repositories": [], "count": 0}

            repos = []
            for line in lines[1:]:  # Skip header
                parts = line.split("\t")
                if len(parts) >= 2:
                    repos.append({"name": parts[0].strip(), "url": parts[1].strip()})

            return {"status": "success", "repositories": repos, "count": len(repos)}

    def _update_repos(self, repo_name, kubeconfig, context):
        """Update chart repositories"""
        cmd = ["helm", "repo", "update"]

        # Add specific repo if provided
        if repo_name:
            cmd.append(repo_name)

        # Add kubeconfig args
        cmd.extend(self._get_kubeconfig_args(kubeconfig, context))

        result = self._run_helm_command(cmd)

        if "error" in result:
            return result

        # Parse update results from output
        output_lines = result["stdout"].strip().split("\n")
        updated_repos = []

        for line in output_lines:
            if "Successfully got an update from" in line:
                # Extract repo name from the line
                import re

                match = re.search(r'"([^"]+)"', line)
                if match:
                    updated_repos.append(match.group(1))

        return {
            "status": "success",
            "message": f"Successfully updated {'repository ' + repo_name if repo_name else 'all repositories'}",
            "updated_repos": updated_repos,
            "output": result["stdout"],
        }

    def _index_repo(self, directory, kubeconfig, context):
        """Generate an index file for a chart repository"""
        cmd = ["helm", "repo", "index", directory]

        # Add kubeconfig args
        cmd.extend(self._get_kubeconfig_args(kubeconfig, context))

        result = self._run_helm_command(cmd)

        if "error" in result:
            return result

        return {
            "status": "success",
            "message": f"Successfully generated index for directory {directory}",
            "directory": directory,
            "output": result["stdout"],
        }
