"""Kubernetes cluster info tool for displaying cluster information."""

import urllib3
from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesClusterInfoTool(BaseTool):
    """Tool for retrieving Kubernetes cluster information and endpoints."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()
            v1 = client.CoreV1Api()
            version_api = client.VersionApi()

            # Disable SSL warnings for local clusters
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            cluster_info = {}

            # Get cluster version
            try:
                version_info = version_api.get_code()
                cluster_info["version"] = {
                    "major": version_info.major,
                    "minor": version_info.minor,
                    "git_version": version_info.git_version,
                    "platform": version_info.platform,
                    "build_date": version_info.build_date,
                }
            except Exception as e:
                cluster_info["version"] = {"error": str(e)}

            # Get nodes information
            try:
                nodes = v1.list_node()
                node_list = []
                total_cpu = 0
                total_memory = 0

                for node in nodes.items:
                    # Get node conditions
                    conditions = {}
                    for condition in node.status.conditions:
                        conditions[condition.type] = condition.status

                    # Extract resource information
                    cpu_capacity = node.status.capacity.get("cpu", "0")
                    memory_capacity = node.status.capacity.get("memory", "0Ki")

                    # Convert memory to bytes for aggregation
                    memory_bytes = self._parse_memory(memory_capacity)
                    total_memory += memory_bytes

                    # Add CPU cores
                    try:
                        total_cpu += int(cpu_capacity)
                    except ValueError:
                        pass

                    node_info = {
                        "name": node.metadata.name,
                        "status": (
                            "Ready" if conditions.get("Ready") == "True" else "NotReady"
                        ),
                        "roles": self._get_node_roles(node),
                        "version": node.status.node_info.kubelet_version,
                        "os": f"{node.status.node_info.operating_system}/{node.status.node_info.architecture}",
                        "container_runtime": node.status.node_info.container_runtime_version,
                        "resources": {
                            "cpu": cpu_capacity,
                            "memory": memory_capacity,
                            "pods": node.status.capacity.get("pods", "Unknown"),
                        },
                    }
                    node_list.append(node_info)

                cluster_info["nodes"] = {
                    "count": len(node_list),
                    "total_cpu": f"{total_cpu} cores",
                    "total_memory": self._format_memory(total_memory),
                    "nodes": node_list,
                }
            except Exception as e:
                cluster_info["nodes"] = {"error": str(e)}

            # Get namespaces count
            try:
                namespaces = v1.list_namespace()
                cluster_info["namespaces"] = {
                    "count": len(namespaces.items),
                    "names": [ns.metadata.name for ns in namespaces.items],
                }
            except Exception as e:
                cluster_info["namespaces"] = {"error": str(e)}

            # Get core services (in kube-system namespace)
            try:
                services = v1.list_namespaced_service("kube-system")
                service_list = []
                for svc in services.items:
                    service_list.append(
                        {
                            "name": svc.metadata.name,
                            "type": svc.spec.type,
                            "cluster_ip": svc.spec.cluster_ip,
                        }
                    )
                cluster_info["system_services"] = service_list
            except Exception as e:
                cluster_info["system_services"] = {"error": str(e)}

            # Get API server endpoint
            try:
                # Get the current context configuration
                _, active_context = config.list_kube_config_contexts()
                if active_context:
                    cluster_info["api_server"] = {
                        "context": active_context["name"],
                        "cluster": active_context["context"]["cluster"],
                        "user": active_context["context"]["user"],
                    }
            except Exception as e:
                cluster_info["api_server"] = {"error": str(e)}

            # Get resource usage summary
            try:
                # Count pods across all namespaces
                pods = v1.list_pod_for_all_namespaces()
                running_pods = sum(
                    1 for pod in pods.items if pod.status.phase == "Running"
                )

                cluster_info["workload_summary"] = {
                    "total_pods": len(pods.items),
                    "running_pods": running_pods,
                    "pending_pods": sum(
                        1 for pod in pods.items if pod.status.phase == "Pending"
                    ),
                    "failed_pods": sum(
                        1 for pod in pods.items if pod.status.phase == "Failed"
                    ),
                }
            except Exception as e:
                cluster_info["workload_summary"] = {"error": str(e)}

            return cluster_info

        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    def _get_node_roles(self, node):
        """Extract node roles from labels"""
        roles = []
        for label, _ in (node.metadata.labels or {}).items():
            if label.startswith("node-role.kubernetes.io/"):
                role = label.split("/", 1)[1]
                roles.append(role)
        return roles if roles else ["worker"]

    def _parse_memory(self, memory_str):
        """Parse memory string to bytes"""
        if not memory_str:
            return 0

        # Remove 'i' suffix if present
        memory_str = memory_str.rstrip("i")

        # Parse different units
        if memory_str.endswith("Ki"):
            return int(memory_str[:-2]) * 1024
        if memory_str.endswith("Mi"):
            return int(memory_str[:-2]) * 1024 * 1024
        if memory_str.endswith("Gi"):
            return int(memory_str[:-2]) * 1024 * 1024 * 1024
        if memory_str.endswith("K"):
            return int(memory_str[:-1]) * 1000
        if memory_str.endswith("M"):
            return int(memory_str[:-1]) * 1000 * 1000
        if memory_str.endswith("G"):
            return int(memory_str[:-1]) * 1000 * 1000 * 1000
        try:
            return int(memory_str)
        except ValueError:
            return 0

    def _format_memory(self, bytes_value):
        """Format bytes to human readable format"""
        if bytes_value >= 1024 * 1024 * 1024:
            return f"{bytes_value / (1024 * 1024 * 1024):.1f}Gi"
        if bytes_value >= 1024 * 1024:
            return f"{bytes_value / (1024 * 1024):.1f}Mi"
        if bytes_value >= 1024:
            return f"{bytes_value / 1024:.1f}Ki"
        return f"{bytes_value}B"
