"""Kubernetes CronJobs tool for managing scheduled jobs."""

from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesCronJobsTool(BaseTool):
    """Tool for listing and managing Kubernetes CronJobs."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()
            batch_v1 = client.BatchV1Api()
            cron_jobs = batch_v1.list_cron_job_for_all_namespaces(watch=False)
            cron_job_list = []
            for i in cron_jobs.items:
                cron_job_list.append(
                    {
                        "name": i.metadata.name,
                        "namespace": i.metadata.namespace,
                        "schedule": i.spec.schedule,
                        "suspend": i.spec.suspend,
                        "last_schedule_time": (
                            str(i.status.last_schedule_time)
                            if i.status.last_schedule_time
                            else None
                        ),
                    }
                )
            return {"cron_jobs": cron_job_list}
        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
