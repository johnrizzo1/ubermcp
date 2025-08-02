from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesPodsTool(BaseTool):
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
        except Exception as e:
            return {"error": str(e)}
