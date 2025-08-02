from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesJobsTool(BaseTool):
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
        except Exception as e:
            return {"error": str(e)}
