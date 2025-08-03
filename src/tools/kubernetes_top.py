"""Kubernetes top tool for viewing resource usage."""

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from src.base_tool import BaseTool


class KubernetesTopTool(BaseTool):
    """Tool for displaying resource usage metrics for nodes and pods."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()

            resource_type = kwargs.get("resource_type", "pods")
            namespace = kwargs.get("namespace", None)
            sort_by = kwargs.get("sort_by", "cpu")  # cpu or memory

            # Create custom objects API client for metrics
            custom_api = client.CustomObjectsApi()
            v1 = client.CoreV1Api()

            if resource_type.lower() in ["pod", "pods", "po"]:
                return self._get_pod_metrics(custom_api, namespace, sort_by)
            if resource_type.lower() in ["node", "nodes", "no"]:
                return self._get_node_metrics(custom_api, v1, sort_by)
            return {
                "error": f"Unsupported resource type: {resource_type}. Use 'pods' or 'nodes'"
            }

        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    def _get_pod_metrics(self, api, namespace, sort_by):
        try:
            # Get pod metrics from metrics-server
            if namespace:
                metrics = api.list_namespaced_custom_object(
                    group="metrics.k8s.io",
                    version="v1beta1",
                    namespace=namespace,
                    plural="pods",
                )
            else:
                metrics = api.list_cluster_custom_object(
                    group="metrics.k8s.io", version="v1beta1", plural="pods"
                )

            pod_metrics = []

            for item in metrics.get("items", []):
                pod_name = item["metadata"]["name"]
                pod_namespace = item["metadata"]["namespace"]

                # Aggregate metrics for all containers
                total_cpu = 0
                total_memory = 0

                for container in item.get("containers", []):
                    # Parse CPU (in nanocores)
                    cpu_str = container["usage"]["cpu"]
                    cpu_nanocores = self._parse_cpu(cpu_str)
                    total_cpu += cpu_nanocores

                    # Parse memory
                    memory_str = container["usage"]["memory"]
                    memory_bytes = self._parse_memory(memory_str)
                    total_memory += memory_bytes

                pod_metrics.append(
                    {
                        "name": pod_name,
                        "namespace": pod_namespace,
                        "cpu": self._format_cpu(total_cpu),
                        "cpu_raw": total_cpu,  # For sorting
                        "memory": self._format_memory(memory_bytes),
                        "memory_raw": total_memory,  # For sorting
                        "containers": len(item.get("containers", [])),
                    }
                )

            # Sort by requested field
            if sort_by == "memory":
                pod_metrics.sort(key=lambda x: x["memory_raw"], reverse=True)
            else:  # Default to CPU
                pod_metrics.sort(key=lambda x: x["cpu_raw"], reverse=True)

            # Remove raw values used for sorting
            for pod in pod_metrics:
                pod.pop("cpu_raw", None)
                pod.pop("memory_raw", None)

            return {
                "resource_type": "pods",
                "namespace": namespace or "all",
                "sorted_by": sort_by,
                "count": len(pod_metrics),
                "metrics": pod_metrics,
            }

        except ApiException as e:
            if e.status == 404:
                return {
                    "error": "Metrics API not available. Please ensure metrics-server is installed in your cluster.",
                    "install_command": "kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml",
                }
            return {"error": f"Failed to get pod metrics: {str(e)}"}

    def _get_node_metrics(self, api, v1, sort_by):
        try:
            # Get node metrics from metrics-server
            metrics = api.list_cluster_custom_object(
                group="metrics.k8s.io", version="v1beta1", plural="nodes"
            )

            # Get node information for capacity
            nodes = v1.list_node()
            node_capacity = {}
            for node in nodes.items:
                node_capacity[node.metadata.name] = {
                    "cpu": node.status.capacity.get("cpu", "0"),
                    "memory": node.status.capacity.get("memory", "0"),
                }

            node_metrics = []

            for item in metrics.get("items", []):
                node_name = item["metadata"]["name"]

                # Parse usage
                cpu_str = item["usage"]["cpu"]
                cpu_nanocores = self._parse_cpu(cpu_str)

                memory_str = item["usage"]["memory"]
                memory_bytes = self._parse_memory(memory_str)

                # Calculate percentages if capacity is known
                cpu_percent = None
                memory_percent = None

                if node_name in node_capacity:
                    # CPU percentage
                    cpu_capacity = (
                        int(node_capacity[node_name]["cpu"]) * 1000000000
                    )  # Convert to nanocores
                    if cpu_capacity > 0:
                        cpu_percent = (cpu_nanocores / cpu_capacity) * 100

                    # Memory percentage
                    memory_capacity = self._parse_memory(
                        node_capacity[node_name]["memory"]
                    )
                    if memory_capacity > 0:
                        memory_percent = (memory_bytes / memory_capacity) * 100

                node_metric = {
                    "name": node_name,
                    "cpu": self._format_cpu(cpu_nanocores),
                    "cpu_raw": cpu_nanocores,
                    "memory": self._format_memory(memory_bytes),
                    "memory_raw": memory_bytes,
                }

                if cpu_percent is not None:
                    node_metric["cpu_percent"] = f"{cpu_percent:.1f}%"
                if memory_percent is not None:
                    node_metric["memory_percent"] = f"{memory_percent:.1f}%"

                node_metrics.append(node_metric)

            # Sort by requested field
            if sort_by == "memory":
                node_metrics.sort(key=lambda x: x["memory_raw"], reverse=True)
            else:  # Default to CPU
                node_metrics.sort(key=lambda x: x["cpu_raw"], reverse=True)

            # Remove raw values used for sorting
            for node in node_metrics:
                node.pop("cpu_raw", None)
                node.pop("memory_raw", None)

            return {
                "resource_type": "nodes",
                "sorted_by": sort_by,
                "count": len(node_metrics),
                "metrics": node_metrics,
            }

        except ApiException as e:
            if e.status == 404:
                return {
                    "error": "Metrics API not available. Please ensure metrics-server is installed in your cluster.",
                    "install_command": "kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml",
                }
            return {"error": f"Failed to get node metrics: {str(e)}"}

    def _parse_cpu(self, cpu_str):
        """Parse CPU string to nanocores"""
        if cpu_str.endswith("n"):
            return int(cpu_str[:-1])
        if cpu_str.endswith("u"):
            return int(cpu_str[:-1]) * 1000
        if cpu_str.endswith("m"):
            return int(cpu_str[:-1]) * 1000000
        return int(cpu_str) * 1000000000

    def _format_cpu(self, nanocores):
        """Format nanocores to human readable format"""
        if nanocores >= 1000000000:
            return f"{nanocores / 1000000000:.2f}"
        if nanocores >= 1000000:
            return f"{nanocores / 1000000}m"
        if nanocores >= 1000:
            return f"{nanocores / 1000}u"
        return f"{nanocores}n"

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
        if memory_str.endswith("Ti"):
            return int(memory_str[:-2]) * 1024 * 1024 * 1024 * 1024
        if memory_str.endswith("K"):
            return int(memory_str[:-1]) * 1000
        if memory_str.endswith("M"):
            return int(memory_str[:-1]) * 1000 * 1000
        if memory_str.endswith("G"):
            return int(memory_str[:-1]) * 1000 * 1000 * 1000
        if memory_str.endswith("T"):
            return int(memory_str[:-1]) * 1000 * 1000 * 1000 * 1000
        try:
            return int(memory_str)
        except ValueError:
            return 0

    def _format_memory(self, bytes_value):
        """Format bytes to human readable format"""
        if bytes_value >= 1024 * 1024 * 1024 * 1024:
            return f"{bytes_value / (1024 * 1024 * 1024 * 1024):.1f}Ti"
        if bytes_value >= 1024 * 1024 * 1024:
            return f"{bytes_value / (1024 * 1024 * 1024):.1f}Gi"
        if bytes_value >= 1024 * 1024:
            return f"{bytes_value / (1024 * 1024):.1f}Mi"
        if bytes_value >= 1024:
            return f"{bytes_value / 1024:.1f}Ki"
        return f"{bytes_value}B"
