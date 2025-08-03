"""Kubernetes pods tool for managing pods."""

from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesPodsTool(BaseTool):
    """Tool for listing and managing Kubernetes pods."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()
            v1 = client.CoreV1Api()
            pods = v1.list_pod_for_all_namespaces(watch=False)
            pod_list = []
            for i in pods.items:
                pod_list.append(
                    {
                        "name": i.metadata.name,
                        "namespace": i.metadata.namespace,
                        "status": i.status.phase,
                        "ip": i.status.pod_ip,
                        "node": i.spec.node_name,
                    }
                )
            return {"pods": pod_list}
        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
