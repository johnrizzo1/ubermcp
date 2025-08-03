"""Kubernetes annotate tool for adding or updating annotations."""

from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesAnnotateTool(BaseTool):
    """Tool for annotating Kubernetes resources with metadata."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()

            resource_type = kwargs.get("resource_type", "")
            name = kwargs.get("name", "")
            namespace = kwargs.get("namespace", "default")
            annotations = kwargs.get("annotations", {})
            remove_annotations = kwargs.get("remove_annotations", [])
            overwrite = kwargs.get("overwrite", False)

            if not resource_type:
                return {"error": "resource_type is required"}
            if not name:
                return {"error": "name is required"}
            if not annotations and not remove_annotations:
                return {"error": "Either annotations or remove_annotations is required"}

            # Initialize API clients
            v1 = client.CoreV1Api()
            apps_v1 = client.AppsV1Api()
            batch_v1 = client.BatchV1Api()
            networking_v1 = client.NetworkingV1Api()

            try:
                # Get current resource to retrieve existing annotations
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
                        "error": f"Annotation operations not implemented for resource type: {resource_type}"
                    }

                # Get current annotations
                current_annotations = current_resource.metadata.annotations or {}
                original_annotations = current_annotations.copy()

                # Apply annotation changes
                if overwrite and annotations:
                    # Replace all annotations
                    new_annotations = annotations.copy()
                else:
                    # Merge annotations
                    new_annotations = current_annotations.copy()
                    # Convert all values to strings (annotations must be strings)
                    for key, value in annotations.items():
                        new_annotations[key] = str(value)

                # Remove specified annotations
                for annotation_key in remove_annotations:
                    new_annotations.pop(annotation_key, None)

                # Prepare patch
                patch = {"metadata": {"annotations": new_annotations}}

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
                added_annotations = {
                    k: v
                    for k, v in new_annotations.items()
                    if k not in original_annotations
                }
                updated_annotations = {
                    k: v
                    for k, v in new_annotations.items()
                    if k in original_annotations and original_annotations[k] != v
                }
                removed_annotations = {
                    k: original_annotations[k]
                    for k in original_annotations
                    if k not in new_annotations
                }

                return {
                    "status": "success",
                    "message": f"Successfully updated annotations for {kind} {name}",
                    "resource": {
                        "kind": kind,
                        "name": result.metadata.name,
                        "namespace": getattr(
                            result.metadata, "namespace", "cluster-wide"
                        ),
                    },
                    "annotations": {
                        "current": result.metadata.annotations or {},
                        "added": added_annotations,
                        "updated": updated_annotations,
                        "removed": removed_annotations,
                    },
                }

            except client.exceptions.ApiException as e:
                return {"error": f"Failed to update annotations: {str(e)}"}

        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
