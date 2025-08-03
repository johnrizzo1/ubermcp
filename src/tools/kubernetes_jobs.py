"""Kubernetes jobs tool for managing batch jobs."""

from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesJobsTool(BaseTool):
    """Tool for listing and managing Kubernetes batch jobs."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()
            batch_v1 = client.BatchV1Api()
            jobs = batch_v1.list_job_for_all_namespaces(watch=False)
            job_list = []
            for i in jobs.items:
                job_list.append(
                    {
                        "name": i.metadata.name,
                        "namespace": i.metadata.namespace,
                        "completions": i.spec.completions,
                        "succeeded": i.status.succeeded,
                        "failed": i.status.failed,
                    }
                )
            return {"jobs": job_list}
        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
