"""Kubernetes logs tool for retrieving container logs."""

from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesLogsTool(BaseTool):
    """Tool for retrieving logs from Kubernetes containers."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()
            v1 = client.CoreV1Api()

            pod_name = kwargs.get("pod_name", "")
            namespace = kwargs.get("namespace", "default")
            container = kwargs.get("container", None)
            previous = kwargs.get("previous", False)
            tail_lines = kwargs.get("tail_lines", None)
            since_seconds = kwargs.get("since_seconds", None)
            timestamps = kwargs.get("timestamps", False)

            if not pod_name:
                return {"error": "pod_name is required"}

            try:
                # Get pod to verify it exists and get container names
                pod = v1.read_namespaced_pod(pod_name, namespace)

                # If no container specified and pod has multiple containers, return container list
                if not container and len(pod.spec.containers) > 1:
                    container_names = [c.name for c in pod.spec.containers]
                    return {
                        "error": "Pod has multiple containers, please specify one",
                        "containers": container_names,
                    }

                # Build kwargs for read_namespaced_pod_log
                log_kwargs = {
                    "name": pod_name,
                    "namespace": namespace,
                    "previous": previous,
                    "timestamps": timestamps,
                }

                if container:
                    log_kwargs["container"] = container
                if tail_lines is not None:
                    log_kwargs["tail_lines"] = tail_lines
                if since_seconds is not None:
                    log_kwargs["since_seconds"] = since_seconds

                # Note: follow=True would stream logs, which doesn't work well with MCP
                # So we ignore the follow parameter for now

                # Get logs
                logs = v1.read_namespaced_pod_log(**log_kwargs)

                # Split logs into lines for better readability
                log_lines = logs.split("\n") if logs else []

                result = {
                    "pod": pod_name,
                    "namespace": namespace,
                    "container": container or pod.spec.containers[0].name,
                    "log_lines": log_lines,
                    "line_count": len(log_lines),
                }

                if tail_lines:
                    result["tail_lines"] = tail_lines
                if since_seconds:
                    result["since_seconds"] = since_seconds
                if previous:
                    result["previous"] = True
                if timestamps:
                    result["timestamps"] = True

                return result

            except client.exceptions.ApiException as e:
                if e.status == 400 and "previous terminated container" in str(e.body):
                    return {
                        "error": "No previous terminated container found",
                        "suggestion": "Try without 'previous=True' to see current container logs",
                    }
                return {"error": f"Failed to get logs: {str(e)}"}

        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}
        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
