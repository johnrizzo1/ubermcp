"""Kubernetes delete tool for removing resources."""

from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesDeleteTool(BaseTool):
    """Tool for deleting Kubernetes resources by type and name."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()

            resource_type = kwargs.get("resource_type", "")
            name = kwargs.get("name", None)
            namespace = kwargs.get("namespace", "default")
            label_selector = kwargs.get("label_selector", None)
            force = kwargs.get("force", False)
            grace_period = kwargs.get("grace_period", None)

            if not resource_type:
                return {"error": "resource_type is required"}

            # Initialize API clients
            v1 = client.CoreV1Api()
            apps_v1 = client.AppsV1Api()
            batch_v1 = client.BatchV1Api()
            networking_v1 = client.NetworkingV1Api()

            # Delete options
            delete_options = client.V1DeleteOptions()
            if grace_period is not None:
                delete_options.grace_period_seconds = grace_period
            if force:
                delete_options.grace_period_seconds = 0

            deleted_resources = []

            # Helper function to delete resource
            def delete_resource(api_func, name, namespace, kind):
                try:
                    if namespace:
                        api_func(name, namespace, body=delete_options)
                    else:
                        api_func(name, body=delete_options)
                    deleted_resources.append(
                        {
                            "kind": kind,
                            "name": name,
                            "namespace": namespace if namespace else "cluster-wide",
                        }
                    )
                except Exception as e:
                    return {"error": f"Failed to delete {kind} {name}: {str(e)}"}
                return None

            # Handle different resource types
            if resource_type.lower() in ["pod", "pods", "po"]:
                if name:
                    error = delete_resource(
                        v1.delete_namespaced_pod, name, namespace, "Pod"
                    )
                    if error:
                        return error
                elif label_selector:
                    pods = v1.list_namespaced_pod(
                        namespace, label_selector=label_selector
                    )
                    for pod in pods.items:
                        error = delete_resource(
                            v1.delete_namespaced_pod,
                            pod.metadata.name,
                            namespace,
                            "Pod",
                        )
                        if error:
                            return error
                else:
                    return {"error": "Either 'name' or 'label_selector' is required"}

            elif resource_type.lower() in ["deployment", "deployments", "deploy"]:
                if name:
                    error = delete_resource(
                        apps_v1.delete_namespaced_deployment,
                        name,
                        namespace,
                        "Deployment",
                    )
                    if error:
                        return error
                elif label_selector:
                    deployments = apps_v1.list_namespaced_deployment(
                        namespace, label_selector=label_selector
                    )
                    for deployment in deployments.items:
                        error = delete_resource(
                            apps_v1.delete_namespaced_deployment,
                            deployment.metadata.name,
                            namespace,
                            "Deployment",
                        )
                        if error:
                            return error
                else:
                    return {"error": "Either 'name' or 'label_selector' is required"}

            elif resource_type.lower() in ["service", "services", "svc"]:
                if name:
                    error = delete_resource(
                        v1.delete_namespaced_service, name, namespace, "Service"
                    )
                    if error:
                        return error
                elif label_selector:
                    services = v1.list_namespaced_service(
                        namespace, label_selector=label_selector
                    )
                    for service in services.items:
                        error = delete_resource(
                            v1.delete_namespaced_service,
                            service.metadata.name,
                            namespace,
                            "Service",
                        )
                        if error:
                            return error
                else:
                    return {"error": "Either 'name' or 'label_selector' is required"}

            elif resource_type.lower() in ["namespace", "namespaces", "ns"]:
                if name:
                    error = delete_resource(
                        v1.delete_namespace, name, None, "Namespace"
                    )
                    if error:
                        return error
                else:
                    return {"error": "'name' is required for namespace deletion"}

            elif resource_type.lower() in ["replicaset", "replicasets", "rs"]:
                if name:
                    error = delete_resource(
                        apps_v1.delete_namespaced_replica_set,
                        name,
                        namespace,
                        "ReplicaSet",
                    )
                    if error:
                        return error
                elif label_selector:
                    replicasets = apps_v1.list_namespaced_replica_set(
                        namespace, label_selector=label_selector
                    )
                    for replica_set in replicasets.items:
                        error = delete_resource(
                            apps_v1.delete_namespaced_replica_set,
                            replica_set.metadata.name,
                            namespace,
                            "ReplicaSet",
                        )
                        if error:
                            return error
                else:
                    return {"error": "Either 'name' or 'label_selector' is required"}

            elif resource_type.lower() in ["statefulset", "statefulsets", "sts"]:
                if name:
                    error = delete_resource(
                        apps_v1.delete_namespaced_stateful_set,
                        name,
                        namespace,
                        "StatefulSet",
                    )
                    if error:
                        return error
                elif label_selector:
                    statefulsets = apps_v1.list_namespaced_stateful_set(
                        namespace, label_selector=label_selector
                    )
                    for sts in statefulsets.items:
                        error = delete_resource(
                            apps_v1.delete_namespaced_stateful_set,
                            sts.metadata.name,
                            namespace,
                            "StatefulSet",
                        )
                        if error:
                            return error
                else:
                    return {"error": "Either 'name' or 'label_selector' is required"}

            elif resource_type.lower() in ["daemonset", "daemonsets", "ds"]:
                if name:
                    error = delete_resource(
                        apps_v1.delete_namespaced_daemon_set,
                        name,
                        namespace,
                        "DaemonSet",
                    )
                    if error:
                        return error
                elif label_selector:
                    daemonsets = apps_v1.list_namespaced_daemon_set(
                        namespace, label_selector=label_selector
                    )
                    for daemon_set in daemonsets.items:
                        error = delete_resource(
                            apps_v1.delete_namespaced_daemon_set,
                            daemon_set.metadata.name,
                            namespace,
                            "DaemonSet",
                        )
                        if error:
                            return error
                else:
                    return {"error": "Either 'name' or 'label_selector' is required"}

            elif resource_type.lower() in ["job", "jobs"]:
                if name:
                    error = delete_resource(
                        batch_v1.delete_namespaced_job, name, namespace, "Job"
                    )
                    if error:
                        return error
                elif label_selector:
                    jobs = batch_v1.list_namespaced_job(
                        namespace, label_selector=label_selector
                    )
                    for job in jobs.items:
                        error = delete_resource(
                            batch_v1.delete_namespaced_job,
                            job.metadata.name,
                            namespace,
                            "Job",
                        )
                        if error:
                            return error
                else:
                    return {"error": "Either 'name' or 'label_selector' is required"}

            elif resource_type.lower() in ["cronjob", "cronjobs", "cj"]:
                if name:
                    error = delete_resource(
                        batch_v1.delete_namespaced_cron_job, name, namespace, "CronJob"
                    )
                    if error:
                        return error
                elif label_selector:
                    cronjobs = batch_v1.list_namespaced_cron_job(
                        namespace, label_selector=label_selector
                    )
                    for cron_job in cronjobs.items:
                        error = delete_resource(
                            batch_v1.delete_namespaced_cron_job,
                            cron_job.metadata.name,
                            namespace,
                            "CronJob",
                        )
                        if error:
                            return error
                else:
                    return {"error": "Either 'name' or 'label_selector' is required"}

            elif resource_type.lower() in ["ingress", "ingresses", "ing"]:
                if name:
                    error = delete_resource(
                        networking_v1.delete_namespaced_ingress,
                        name,
                        namespace,
                        "Ingress",
                    )
                    if error:
                        return error
                elif label_selector:
                    ingresses = networking_v1.list_namespaced_ingress(
                        namespace, label_selector=label_selector
                    )
                    for ing in ingresses.items:
                        error = delete_resource(
                            networking_v1.delete_namespaced_ingress,
                            ing.metadata.name,
                            namespace,
                            "Ingress",
                        )
                        if error:
                            return error
                else:
                    return {"error": "Either 'name' or 'label_selector' is required"}

            elif resource_type.lower() in ["configmap", "configmaps", "cm"]:
                if name:
                    error = delete_resource(
                        v1.delete_namespaced_config_map, name, namespace, "ConfigMap"
                    )
                    if error:
                        return error
                elif label_selector:
                    configmaps = v1.list_namespaced_config_map(
                        namespace, label_selector=label_selector
                    )
                    for config_map in configmaps.items:
                        error = delete_resource(
                            v1.delete_namespaced_config_map,
                            config_map.metadata.name,
                            namespace,
                            "ConfigMap",
                        )
                        if error:
                            return error
                else:
                    return {"error": "Either 'name' or 'label_selector' is required"}

            elif resource_type.lower() in ["secret", "secrets"]:
                if name:
                    error = delete_resource(
                        v1.delete_namespaced_secret, name, namespace, "Secret"
                    )
                    if error:
                        return error
                elif label_selector:
                    secrets = v1.list_namespaced_secret(
                        namespace, label_selector=label_selector
                    )
                    for secret in secrets.items:
                        error = delete_resource(
                            v1.delete_namespaced_secret,
                            secret.metadata.name,
                            namespace,
                            "Secret",
                        )
                        if error:
                            return error
                else:
                    return {"error": "Either 'name' or 'label_selector' is required"}

            else:
                return {"error": f"Unsupported resource type: {resource_type}"}

            return {
                "status": "success",
                "deleted": deleted_resources,
                "message": f"Deleted {len(deleted_resources)} resource(s)",
            }

        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
