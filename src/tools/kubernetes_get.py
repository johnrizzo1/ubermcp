"""Kubernetes get tool for retrieving resource information."""

from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesGetTool(BaseTool):
    """Tool for getting and listing Kubernetes resources."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()

            resource_type = kwargs.get("resource_type", "pods")
            namespace = kwargs.get("namespace", None)
            name = kwargs.get("name", None)
            label_selector = kwargs.get("label_selector", None)
            field_selector = kwargs.get("field_selector", None)

            # Initialize API clients
            v1 = client.CoreV1Api()
            apps_v1 = client.AppsV1Api()
            batch_v1 = client.BatchV1Api()
            networking_v1 = client.NetworkingV1Api()

            result = {"resources": []}

            # Helper function to format resource
            def format_resource(item, kind):
                resource = {
                    "kind": kind,
                    "name": item.metadata.name,
                    "namespace": getattr(item.metadata, "namespace", "cluster-wide"),
                    "created": str(item.metadata.creation_timestamp),
                    "labels": item.metadata.labels or {},
                }

                # Add resource-specific fields
                if kind == "Pod":
                    resource["status"] = item.status.phase
                    resource["ready"] = (
                        f"{sum(1 for c in item.status.container_statuses if c.ready)}/{len(item.spec.containers)}"
                    )
                    resource["restarts"] = sum(
                        c.restart_count for c in item.status.container_statuses
                    )
                    resource["node"] = item.spec.node_name
                elif kind == "Deployment":
                    resource["ready"] = (
                        f"{item.status.ready_replicas or 0}/{item.spec.replicas}"
                    )
                    resource["up_to_date"] = item.status.updated_replicas or 0
                    resource["available"] = item.status.available_replicas or 0
                elif kind == "Service":
                    resource["type"] = item.spec.type
                    resource["cluster_ip"] = item.spec.cluster_ip
                    resource["ports"] = [
                        f"{p.port}/{p.protocol}" for p in item.spec.ports
                    ]
                elif kind == "Node":
                    conditions = {c.type: c.status for c in item.status.conditions}
                    resource["status"] = (
                        "Ready" if conditions.get("Ready") == "True" else "NotReady"
                    )
                    resource["version"] = item.status.node_info.kubelet_version
                elif kind == "Namespace":
                    resource["status"] = item.status.phase

                return resource

            # Handle different resource types
            if resource_type.lower() in ["pod", "pods", "po"]:
                if name and namespace:
                    pod = v1.read_namespaced_pod(name, namespace)
                    result["resources"].append(format_resource(pod, "Pod"))
                elif namespace:
                    pods = v1.list_namespaced_pod(
                        namespace,
                        label_selector=label_selector,
                        field_selector=field_selector,
                    )
                    result["resources"] = [
                        format_resource(pod, "Pod") for pod in pods.items
                    ]
                else:
                    pods = v1.list_pod_for_all_namespaces(
                        label_selector=label_selector, field_selector=field_selector
                    )
                    result["resources"] = [
                        format_resource(pod, "Pod") for pod in pods.items
                    ]

            elif resource_type.lower() in ["deployment", "deployments", "deploy"]:
                if name and namespace:
                    deployment = apps_v1.read_namespaced_deployment(name, namespace)
                    result["resources"].append(
                        format_resource(deployment, "Deployment")
                    )
                elif namespace:
                    deployments = apps_v1.list_namespaced_deployment(
                        namespace, label_selector=label_selector
                    )
                    result["resources"] = [
                        format_resource(dep, "Deployment") for dep in deployments.items
                    ]
                else:
                    deployments = apps_v1.list_deployment_for_all_namespaces(
                        label_selector=label_selector
                    )
                    result["resources"] = [
                        format_resource(dep, "Deployment") for dep in deployments.items
                    ]

            elif resource_type.lower() in ["service", "services", "svc"]:
                if name and namespace:
                    service = v1.read_namespaced_service(name, namespace)
                    result["resources"].append(format_resource(service, "Service"))
                elif namespace:
                    services = v1.list_namespaced_service(
                        namespace, label_selector=label_selector
                    )
                    result["resources"] = [
                        format_resource(svc, "Service") for svc in services.items
                    ]
                else:
                    services = v1.list_service_for_all_namespaces(
                        label_selector=label_selector
                    )
                    result["resources"] = [
                        format_resource(svc, "Service") for svc in services.items
                    ]

            elif resource_type.lower() in ["node", "nodes", "no"]:
                if name:
                    node = v1.read_node(name)
                    result["resources"].append(format_resource(node, "Node"))
                else:
                    nodes = v1.list_node(
                        label_selector=label_selector, field_selector=field_selector
                    )
                    result["resources"] = [
                        format_resource(node, "Node") for node in nodes.items
                    ]

            elif resource_type.lower() in ["namespace", "namespaces", "ns"]:
                if name:
                    namespace_obj = v1.read_namespace(name)
                    result["resources"].append(
                        format_resource(namespace_obj, "Namespace")
                    )
                else:
                    namespaces = v1.list_namespace(label_selector=label_selector)
                    result["resources"] = [
                        format_resource(ns, "Namespace") for ns in namespaces.items
                    ]

            elif resource_type.lower() in ["replicaset", "replicasets", "rs"]:
                if name and namespace:
                    replica_set = apps_v1.read_namespaced_replica_set(name, namespace)
                    result["resources"].append(
                        format_resource(replica_set, "ReplicaSet")
                    )
                elif namespace:
                    replicasets = apps_v1.list_namespaced_replica_set(
                        namespace, label_selector=label_selector
                    )
                    result["resources"] = [
                        format_resource(replica_set, "ReplicaSet")
                        for replica_set in replicasets.items
                    ]
                else:
                    replicasets = apps_v1.list_replica_set_for_all_namespaces(
                        label_selector=label_selector
                    )
                    result["resources"] = [
                        format_resource(replica_set, "ReplicaSet")
                        for replica_set in replicasets.items
                    ]

            elif resource_type.lower() in ["statefulset", "statefulsets", "sts"]:
                if name and namespace:
                    sts = apps_v1.read_namespaced_stateful_set(name, namespace)
                    result["resources"].append(format_resource(sts, "StatefulSet"))
                elif namespace:
                    statefulsets = apps_v1.list_namespaced_stateful_set(
                        namespace, label_selector=label_selector
                    )
                    result["resources"] = [
                        format_resource(sts, "StatefulSet")
                        for sts in statefulsets.items
                    ]
                else:
                    statefulsets = apps_v1.list_stateful_set_for_all_namespaces(
                        label_selector=label_selector
                    )
                    result["resources"] = [
                        format_resource(sts, "StatefulSet")
                        for sts in statefulsets.items
                    ]

            elif resource_type.lower() in ["daemonset", "daemonsets", "ds"]:
                if name and namespace:
                    daemon_set = apps_v1.read_namespaced_daemon_set(name, namespace)
                    result["resources"].append(format_resource(daemon_set, "DaemonSet"))
                elif namespace:
                    daemonsets = apps_v1.list_namespaced_daemon_set(
                        namespace, label_selector=label_selector
                    )
                    result["resources"] = [
                        format_resource(daemon_set, "DaemonSet")
                        for daemon_set in daemonsets.items
                    ]
                else:
                    daemonsets = apps_v1.list_daemon_set_for_all_namespaces(
                        label_selector=label_selector
                    )
                    result["resources"] = [
                        format_resource(daemon_set, "DaemonSet")
                        for daemon_set in daemonsets.items
                    ]

            elif resource_type.lower() in ["job", "jobs"]:
                if name and namespace:
                    job = batch_v1.read_namespaced_job(name, namespace)
                    result["resources"].append(format_resource(job, "Job"))
                elif namespace:
                    jobs = batch_v1.list_namespaced_job(
                        namespace, label_selector=label_selector
                    )
                    result["resources"] = [
                        format_resource(job, "Job") for job in jobs.items
                    ]
                else:
                    jobs = batch_v1.list_job_for_all_namespaces(
                        label_selector=label_selector
                    )
                    result["resources"] = [
                        format_resource(job, "Job") for job in jobs.items
                    ]

            elif resource_type.lower() in ["cronjob", "cronjobs", "cj"]:
                if name and namespace:
                    cron_job = batch_v1.read_namespaced_cron_job(name, namespace)
                    result["resources"].append(format_resource(cron_job, "CronJob"))
                elif namespace:
                    cronjobs = batch_v1.list_namespaced_cron_job(
                        namespace, label_selector=label_selector
                    )
                    result["resources"] = [
                        format_resource(cron_job, "CronJob")
                        for cron_job in cronjobs.items
                    ]
                else:
                    cronjobs = batch_v1.list_cron_job_for_all_namespaces(
                        label_selector=label_selector
                    )
                    result["resources"] = [
                        format_resource(cron_job, "CronJob")
                        for cron_job in cronjobs.items
                    ]

            elif resource_type.lower() in ["ingress", "ingresses", "ing"]:
                if name and namespace:
                    ing = networking_v1.read_namespaced_ingress(name, namespace)
                    result["resources"].append(format_resource(ing, "Ingress"))
                elif namespace:
                    ingresses = networking_v1.list_namespaced_ingress(
                        namespace, label_selector=label_selector
                    )
                    result["resources"] = [
                        format_resource(ing, "Ingress") for ing in ingresses.items
                    ]
                else:
                    ingresses = networking_v1.list_ingress_for_all_namespaces(
                        label_selector=label_selector
                    )
                    result["resources"] = [
                        format_resource(ing, "Ingress") for ing in ingresses.items
                    ]

            elif resource_type.lower() in ["configmap", "configmaps", "cm"]:
                if name and namespace:
                    config_map = v1.read_namespaced_config_map(name, namespace)
                    result["resources"].append(format_resource(config_map, "ConfigMap"))
                elif namespace:
                    configmaps = v1.list_namespaced_config_map(
                        namespace, label_selector=label_selector
                    )
                    result["resources"] = [
                        format_resource(config_map, "ConfigMap")
                        for config_map in configmaps.items
                    ]
                else:
                    configmaps = v1.list_config_map_for_all_namespaces(
                        label_selector=label_selector
                    )
                    result["resources"] = [
                        format_resource(config_map, "ConfigMap")
                        for config_map in configmaps.items
                    ]

            elif resource_type.lower() in ["secret", "secrets"]:
                if name and namespace:
                    secret = v1.read_namespaced_secret(name, namespace)
                    result["resources"].append(format_resource(secret, "Secret"))
                elif namespace:
                    secrets = v1.list_namespaced_secret(
                        namespace, label_selector=label_selector
                    )
                    result["resources"] = [
                        format_resource(secret, "Secret") for secret in secrets.items
                    ]
                else:
                    secrets = v1.list_secret_for_all_namespaces(
                        label_selector=label_selector
                    )
                    result["resources"] = [
                        format_resource(secret, "Secret") for secret in secrets.items
                    ]

            else:
                return {"error": f"Unsupported resource type: {resource_type}"}

            result["count"] = len(result["resources"])
            return result

        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
