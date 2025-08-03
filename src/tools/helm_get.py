"""Helm get tool for retrieving release information."""

import json

import yaml

from src.tools.helm_base import HelmBaseTool


class HelmGetTool(HelmBaseTool):
    """Tool for getting information about a Helm release."""

    def execute(self, **kwargs):
        try:
            action = kwargs.get(
                "action", "values"
            )  # values, manifest, notes, hooks, all
            release_name = kwargs.get("release_name", "")
            namespace = kwargs.get("namespace", "default")
            revision = kwargs.get("revision", None)
            output_format = kwargs.get(
                "output", None
            )  # json, yaml, or None for default
            kubeconfig = kwargs.get("kubeconfig", None)
            context = kwargs.get("context", None)

            if not release_name:
                return {"error": "release_name is required"}

            # Build helm get command
            cmd = ["helm", "get", action, release_name]

            # Add namespace
            cmd.extend(["--namespace", namespace])

            # Add revision if specified
            if revision is not None:
                cmd.extend(["--revision", str(revision)])

            # Add output format for values
            if action == "values" and output_format in ["json", "yaml"]:
                cmd.extend(["--output", output_format])

            # Add kubeconfig args
            cmd.extend(self._get_kubeconfig_args(kubeconfig, context))

            # Run the command
            result = self._run_helm_command(cmd)

            if "error" in result:
                return result

            # Parse output based on action and format
            if action == "values":
                if output_format == "json":
                    try:
                        values = (
                            json.loads(result["stdout"]) if result["stdout"] else {}
                        )
                        return {
                            "status": "success",
                            "release_name": release_name,
                            "namespace": namespace,
                            "action": action,
                            "values": values,
                        }
                    except (json.JSONDecodeError, ValueError):
                        return {
                            "error": "Failed to parse JSON output",
                            "raw_output": result["stdout"],
                        }

                elif output_format == "yaml" or not output_format:
                    try:
                        values = (
                            yaml.safe_load(result["stdout"]) if result["stdout"] else {}
                        )
                        return {
                            "status": "success",
                            "release_name": release_name,
                            "namespace": namespace,
                            "action": action,
                            "values": values,
                        }
                    except (yaml.YAMLError, ValueError):
                        # Return raw YAML if parsing fails
                        return {
                            "status": "success",
                            "release_name": release_name,
                            "namespace": namespace,
                            "action": action,
                            "raw_values": result["stdout"],
                        }

            elif action == "manifest":
                # Parse Kubernetes manifests from YAML
                manifests = []
                if result["stdout"]:
                    try:
                        # Split by document separator
                        docs = result["stdout"].split("\n---\n")
                        for doc in docs:
                            if doc.strip():
                                manifest = yaml.safe_load(doc)
                                if manifest:
                                    manifests.append(manifest)
                    except (yaml.YAMLError, ValueError):
                        # If parsing fails, return raw output
                        return {
                            "status": "success",
                            "release_name": release_name,
                            "namespace": namespace,
                            "action": action,
                            "raw_manifest": result["stdout"],
                        }

                return {
                    "status": "success",
                    "release_name": release_name,
                    "namespace": namespace,
                    "action": action,
                    "manifests": manifests,
                    "manifest_count": len(manifests),
                }

            elif action == "notes":
                return {
                    "status": "success",
                    "release_name": release_name,
                    "namespace": namespace,
                    "action": action,
                    "notes": result["stdout"],
                }

            elif action == "hooks":
                # Parse hooks from YAML
                hooks = []
                if result["stdout"]:
                    try:
                        docs = result["stdout"].split("\n---\n")
                        for doc in docs:
                            if doc.strip():
                                hook = yaml.safe_load(doc)
                                if hook and hook.get("metadata", {}).get(
                                    "annotations", {}
                                ).get("helm.sh/hook"):
                                    hooks.append(
                                        {
                                            "name": hook.get("metadata", {}).get(
                                                "name"
                                            ),
                                            "kind": hook.get("kind"),
                                            "hook": hook.get("metadata", {})
                                            .get("annotations", {})
                                            .get("helm.sh/hook"),
                                            "weight": hook.get("metadata", {})
                                            .get("annotations", {})
                                            .get("helm.sh/hook-weight"),
                                            "delete_policy": hook.get("metadata", {})
                                            .get("annotations", {})
                                            .get("helm.sh/hook-delete-policy"),
                                        }
                                    )
                    except (yaml.YAMLError, ValueError, KeyError):
                        return {
                            "status": "success",
                            "release_name": release_name,
                            "namespace": namespace,
                            "action": action,
                            "raw_hooks": result["stdout"],
                        }

                return {
                    "status": "success",
                    "release_name": release_name,
                    "namespace": namespace,
                    "action": action,
                    "hooks": hooks,
                    "hook_count": len(hooks),
                }

            elif action == "all":
                # Return all information as structured sections
                sections = {}
                current_section = None
                current_content = []

                for line in result["stdout"].split("\n"):
                    if line.startswith("---") and line.endswith("---") and ":" in line:
                        # Save previous section
                        if current_section:
                            sections[current_section] = "\n".join(current_content)
                        # Start new section
                        current_section = line.strip("- ").replace(":", "").lower()
                        current_content = []
                    else:
                        current_content.append(line)

                # Save last section
                if current_section:
                    sections[current_section] = "\n".join(current_content)

                return {
                    "status": "success",
                    "release_name": release_name,
                    "namespace": namespace,
                    "action": action,
                    "sections": sections,
                }

            else:
                # Unknown action, return raw output
                return {
                    "status": "success",
                    "release_name": release_name,
                    "namespace": namespace,
                    "action": action,
                    "output": result["stdout"],
                }

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
