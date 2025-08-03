"""Kubernetes ingresses tool for managing ingress resources."""

from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesIngressesTool(BaseTool):
    """Tool for listing and managing Kubernetes ingress resources."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()
            networking_v1 = client.NetworkingV1Api()
            ingresses = networking_v1.list_ingress_for_all_namespaces(watch=False)
            ingress_list = []
            for i in ingresses.items:
                ingress_list.append(
                    {
                        "name": i.metadata.name,
                        "namespace": i.metadata.namespace,
                        "rules": (
                            [
                                {
                                    "host": r.host,
                                    "paths": [
                                        {
                                            "path": p.path,
                                            "path_type": p.path_type,
                                            "backend_service_name": p.backend.service.name,
                                            "backend_service_port": p.backend.service.port.number,
                                        }
                                        for p in r.http.paths
                                    ],
                                }
                                for r in i.spec.rules
                            ]
                            if i.spec.rules
                            else []
                        ),
                    }
                )
            return {"ingresses": ingress_list}
        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
