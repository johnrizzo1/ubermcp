"""Kubernetes label tool for managing resource labels."""

from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesLabelTool(BaseTool):
    """Tool for adding, updating, and removing labels on Kubernetes resources."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()

            resource_type = kwargs.get("resource_type", "")
            name = kwargs.get("name", "")
            namespace = kwargs.get("namespace", "default")
            labels = kwargs.get("labels", {})
            remove_labels = kwargs.get("remove_labels", [])
            overwrite = kwargs.get("overwrite", False)

            if not resource_type:
                return {"error": "resource_type is required"}
            if not name:
                return {"error": "name is required"}
            if not labels and not remove_labels:
                return {"error": "Either labels or remove_labels is required"}

            # Initialize API clients
            v1 = client.CoreV1Api()
            apps_v1 = client.AppsV1Api()
            batch_v1 = client.BatchV1Api()
            networking_v1 = client.NetworkingV1Api()

            try:
                # Get current resource to retrieve existing labels
                current_resource = None

                if resource_type.lower() in ["pod", "pods", "po"]:
                    current_resource = v1.read_namespaced_pod(name, namespace)
                elif resource_type.lower() in ["deployment", "deployments", "deploy"]:
                    current_resource = apps_v1.read_namespaced_deployment(
                        name, namespace
                    )
                elif resource_type.lower() in ["service", "services", "svc"]:
                    current_resource = v1.read_namespaced_service(name, namespace)
                elif resource_type.lower() in ["configmap", "configmaps", "cm"]:
                    current_resource = v1.read_namespaced_config_map(name, namespace)
                elif resource_type.lower() in ["secret", "secrets"]:
                    current_resource = v1.read_namespaced_secret(name, namespace)
                elif resource_type.lower() in ["namespace", "namespaces", "ns"]:
                    current_resource = v1.read_namespace(name)
                elif resource_type.lower() in ["node", "nodes", "no"]:
                    current_resource = v1.read_node(name)
                elif resource_type.lower() in ["replicaset", "replicasets", "rs"]:
                    current_resource = apps_v1.read_namespaced_replica_set(
                        name, namespace
                    )
                elif resource_type.lower() in ["statefulset", "statefulsets", "sts"]:
                    current_resource = apps_v1.read_namespaced_stateful_set(
                        name, namespace
                    )
                elif resource_type.lower() in ["daemonset", "daemonsets", "ds"]:
                    current_resource = apps_v1.read_namespaced_daemon_set(
                        name, namespace
                    )
                elif resource_type.lower() in ["job", "jobs"]:
                    current_resource = batch_v1.read_namespaced_job(name, namespace)
                elif resource_type.lower() in ["cronjob", "cronjobs", "cj"]:
                    current_resource = batch_v1.read_namespaced_cron_job(
                        name, namespace
                    )
                elif resource_type.lower() in ["ingress", "ingresses", "ing"]:
                    current_resource = networking_v1.read_namespaced_ingress(
                        name, namespace
                    )
                else:
                    return {
                        "error": f"Label operations not implemented for resource type: {resource_type}"
                    }

                # Get current labels
                current_labels = current_resource.metadata.labels or {}
                original_labels = current_labels.copy()

                # Apply label changes
                if overwrite and labels:
                    # Replace all labels
                    new_labels = labels.copy()
                else:
                    # Merge labels
                    new_labels = current_labels.copy()
                    new_labels.update(labels)

                # Remove specified labels
                for label_key in remove_labels:
                    new_labels.pop(label_key, None)

                # Prepare patch
                patch = {"metadata": {"labels": new_labels}}

                # Initialize variables
                result = None
                kind = None

                # Apply patch based on resource type
                if resource_type.lower() in ["pod", "pods", "po"]:
                    result = v1.patch_namespaced_pod(name, namespace, patch)
                    kind = "Pod"
                elif resource_type.lower() in ["deployment", "deployments", "deploy"]:
                    result = apps_v1.patch_namespaced_deployment(name, namespace, patch)
                    kind = "Deployment"
                elif resource_type.lower() in ["service", "services", "svc"]:
                    result = v1.patch_namespaced_service(name, namespace, patch)
                    kind = "Service"
                elif resource_type.lower() in ["configmap", "configmaps", "cm"]:
                    result = v1.patch_namespaced_config_map(name, namespace, patch)
                    kind = "ConfigMap"
                elif resource_type.lower() in ["secret", "secrets"]:
                    result = v1.patch_namespaced_secret(name, namespace, patch)
                    kind = "Secret"
                elif resource_type.lower() in ["namespace", "namespaces", "ns"]:
                    result = v1.patch_namespace(name, patch)
                    kind = "Namespace"
                elif resource_type.lower() in ["node", "nodes", "no"]:
                    result = v1.patch_node(name, patch)
                    kind = "Node"
                elif resource_type.lower() in ["replicaset", "replicasets", "rs"]:
                    result = apps_v1.patch_namespaced_replica_set(
                        name, namespace, patch
                    )
                    kind = "ReplicaSet"
                elif resource_type.lower() in ["statefulset", "statefulsets", "sts"]:
                    result = apps_v1.patch_namespaced_stateful_set(
                        name, namespace, patch
                    )
                    kind = "StatefulSet"
                elif resource_type.lower() in ["daemonset", "daemonsets", "ds"]:
                    result = apps_v1.patch_namespaced_daemon_set(name, namespace, patch)
                    kind = "DaemonSet"
                elif resource_type.lower() in ["job", "jobs"]:
                    result = batch_v1.patch_namespaced_job(name, namespace, patch)
                    kind = "Job"
                elif resource_type.lower() in ["cronjob", "cronjobs", "cj"]:
                    result = batch_v1.patch_namespaced_cron_job(name, namespace, patch)
                    kind = "CronJob"
                elif resource_type.lower() in ["ingress", "ingresses", "ing"]:
                    result = networking_v1.patch_namespaced_ingress(
                        name, namespace, patch
                    )
                    kind = "Ingress"

                # Calculate changes
                added_labels = {
                    k: v for k, v in new_labels.items() if k not in original_labels
                }
                updated_labels = {
                    k: v
                    for k, v in new_labels.items()
                    if k in original_labels and original_labels[k] != v
                }
                removed_labels = {
                    k: original_labels[k]
                    for k in original_labels
                    if k not in new_labels
                }

                return {
                    "status": "success",
                    "message": f"Successfully updated labels for {kind} {name}",
                    "resource": {
                        "kind": kind,
                        "name": result.metadata.name,
                        "namespace": getattr(
                            result.metadata, "namespace", "cluster-wide"
                        ),
                    },
                    "labels": {
                        "current": result.metadata.labels or {},
                        "added": added_labels,
                        "updated": updated_labels,
                        "removed": removed_labels,
                    },
                }

            except client.exceptions.ApiException as e:
                return {"error": f"Failed to update labels: {str(e)}"}

        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
