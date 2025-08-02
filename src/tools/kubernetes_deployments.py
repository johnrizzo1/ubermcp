from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesDeploymentsTool(BaseTool):
    def execute(self, **kwargs):
        try:
            config.load_kube_config()
            apps_v1 = client.AppsV1Api()
            deployments = apps_v1.list_deployment_for_all_namespaces(watch=False)
            deployment_list = []
            for i in deployments.items:
                deployment_list.append(
                    {
                        "name": i.metadata.name,
                        "namespace": i.metadata.namespace,
                        "replicas": i.spec.replicas,
                        "available_replicas": i.status.available_replicas,
                        "ready_replicas": i.status.ready_replicas,
                    }
                )
            return {"deployments": deployment_list}
        except Exception as e:
            return {"error": str(e)}
