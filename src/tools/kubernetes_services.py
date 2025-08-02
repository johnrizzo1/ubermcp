from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesServicesTool(BaseTool):
    def execute(self, **kwargs):
        try:
            config.load_kube_config()
            v1 = client.CoreV1Api()
            services = v1.list_service_for_all_namespaces(watch=False)
            service_list = []
            for i in services.items:
                service_list.append(
                    {
                        "name": i.metadata.name,
                        "namespace": i.metadata.namespace,
                        "cluster_ip": i.spec.cluster_ip,
                        "type": i.spec.type,
                        "ports": [
                            {"name": p.name, "port": p.port, "protocol": p.protocol}
                            for p in i.spec.ports
                        ],
                    }
                )
            return {"services": service_list}
        except Exception as e:
            return {"error": str(e)}
