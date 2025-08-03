"""Helm show tool for displaying chart information."""

import yaml

from src.tools.helm_base import HelmBaseTool


class HelmShowTool(HelmBaseTool):
    """Tool for showing information about a Helm chart."""

    def execute(self, **kwargs):
        try:
            show_type = kwargs.get(
                "show_type", "all"
            )  # all, chart, readme, values, crds
            chart = kwargs.get("chart", "")
            version = kwargs.get("version", None)
            devel = kwargs.get("devel", False)
            verify = kwargs.get("verify", False)
            keyring = kwargs.get("keyring", None)
            repo = kwargs.get("repo", None)
            username = kwargs.get("username", None)
            password = kwargs.get("password", None)
            kubeconfig = kwargs.get("kubeconfig", None)
            context = kwargs.get("context", None)

            if not chart:
                return {"error": "chart is required"}

            # Build helm show command
            cmd = ["helm", "show", show_type, chart]

            # Add version if specified
            if version:
                cmd.extend(["--version", version])

            # Add flags
            if devel:
                cmd.append("--devel")

            if verify:
                cmd.append("--verify")
                if keyring:
                    cmd.extend(["--keyring", keyring])

            # Add repo if specified
            if repo:
                cmd.extend(["--repo", repo])

            # Add authentication if provided
            if username:
                cmd.extend(["--username", username])
            if password:
                cmd.extend(["--password", password])

            # Add kubeconfig args
            cmd.extend(self._get_kubeconfig_args(kubeconfig, context))

            # Run the command
            result = self._run_helm_command(cmd)

            if "error" in result:
                return result

            # Parse output based on show type
            if show_type == "values":
                try:
                    values = (
                        yaml.safe_load(result["stdout"]) if result["stdout"] else {}
                    )
                    return {
                        "status": "success",
                        "chart": chart,
                        "show_type": show_type,
                        "values": values,
                    }
                except (yaml.YAMLError, ValueError):
                    # Return raw values if parsing fails
                    return {
                        "status": "success",
                        "chart": chart,
                        "show_type": show_type,
                        "raw_values": result["stdout"],
                    }

            elif show_type == "chart":
                try:
                    chart_info = (
                        yaml.safe_load(result["stdout"]) if result["stdout"] else {}
                    )
                    return {
                        "status": "success",
                        "chart": chart,
                        "show_type": show_type,
                        "chart_info": chart_info,
                    }
                except (yaml.YAMLError, ValueError):
                    return {
                        "status": "success",
                        "chart": chart,
                        "show_type": show_type,
                        "raw_chart": result["stdout"],
                    }

            elif show_type == "readme":
                return {
                    "status": "success",
                    "chart": chart,
                    "show_type": show_type,
                    "readme": result["stdout"],
                }

            elif show_type == "crds":
                # Parse CRDs from YAML
                crds = []
                if result["stdout"]:
                    try:
                        docs = result["stdout"].split("\n---\n")
                        for doc in docs:
                            if doc.strip():
                                crd = yaml.safe_load(doc)
                                if (
                                    crd
                                    and crd.get("kind") == "CustomResourceDefinition"
                                ):
                                    crds.append(
                                        {
                                            "name": crd.get("metadata", {}).get("name"),
                                            "group": crd.get("spec", {}).get("group"),
                                            "versions": [
                                                v.get("name")
                                                for v in crd.get("spec", {}).get(
                                                    "versions", []
                                                )
                                            ],
                                            "scope": crd.get("spec", {}).get("scope"),
                                        }
                                    )
                    except (yaml.YAMLError, ValueError):
                        return {
                            "status": "success",
                            "chart": chart,
                            "show_type": show_type,
                            "raw_crds": result["stdout"],
                        }

                return {
                    "status": "success",
                    "chart": chart,
                    "show_type": show_type,
                    "crds": crds,
                    "crd_count": len(crds),
                }

            elif show_type == "all":
                # Parse all sections
                sections = {}
                current_section = None
                current_content = []

                for line in result["stdout"].split("\n"):
                    if line.startswith("---") and line.endswith("---"):
                        # Save previous section
                        if current_section:
                            content = "\n".join(current_content).strip()
                            if current_section == "values":
                                try:
                                    sections[current_section] = (
                                        yaml.safe_load(content) if content else {}
                                    )
                                except (yaml.YAMLError, ValueError):
                                    sections[current_section] = content
                            else:
                                sections[current_section] = content

                        # Extract section name
                        section_name = line.strip("- ").lower()
                        if "chart.yaml" in section_name:
                            current_section = "chart"
                        elif "values.yaml" in section_name:
                            current_section = "values"
                        elif "readme" in section_name.lower():
                            current_section = "readme"
                        else:
                            current_section = section_name
                        current_content = []
                    else:
                        current_content.append(line)

                # Save last section
                if current_section:
                    content = "\n".join(current_content).strip()
                    if current_section == "values":
                        try:
                            sections[current_section] = (
                                yaml.safe_load(content) if content else {}
                            )
                        except (yaml.YAMLError, ValueError):
                            sections[current_section] = content
                    else:
                        sections[current_section] = content

                return {
                    "status": "success",
                    "chart": chart,
                    "show_type": show_type,
                    "sections": sections,
                }

            else:
                # Unknown type, return raw output
                return {
                    "status": "success",
                    "chart": chart,
                    "show_type": show_type,
                    "output": result["stdout"],
                }

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
