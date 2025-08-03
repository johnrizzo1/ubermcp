"""Kubernetes secrets tool for managing secrets."""

from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesSecretsTool(BaseTool):
    """Tool for listing and managing Kubernetes secrets."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()
            v1 = client.CoreV1Api()
            secrets = v1.list_secret_for_all_namespaces(watch=False)
            secret_list = []
            for i in secrets.items:
                secret_list.append(
                    {
                        "name": i.metadata.name,
                        "namespace": i.metadata.namespace,
                        "type": i.type,
                        "data_keys": list(i.data.keys()) if i.data else [],
                    }
                )
            return {"secrets": secret_list}
        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
