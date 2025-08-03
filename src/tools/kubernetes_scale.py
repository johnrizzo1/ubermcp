"""Kubernetes scale tool for scaling deployments and replicasets."""

from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesScaleTool(BaseTool):
    """Tool for scaling Kubernetes deployments and replicasets."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()
            apps_v1 = client.AppsV1Api()

            resource_type = kwargs.get("resource_type", "deployment")
            name = kwargs.get("name", "")
            namespace = kwargs.get("namespace", "default")
            replicas = kwargs.get("replicas", None)

            if not name:
                return {"error": "name is required"}
            if replicas is None:
                return {"error": "replicas is required"}
            if not isinstance(replicas, int) or replicas < 0:
                return {"error": "replicas must be a non-negative integer"}

            try:
                if resource_type.lower() in ["deployment", "deploy"]:
                    # Get current deployment
                    deployment = apps_v1.read_namespaced_deployment(name, namespace)
                    old_replicas = deployment.spec.replicas

                    # Update replicas
                    deployment.spec.replicas = replicas

                    # Apply the update
                    apps_v1.patch_namespaced_deployment(
                        name=name, namespace=namespace, body=deployment
                    )

                    return {
                        "status": "success",
                        "resource": {
                            "kind": "Deployment",
                            "name": name,
                            "namespace": namespace,
                            "old_replicas": old_replicas,
                            "new_replicas": replicas,
                        },
                        "message": f"Scaled deployment {name} from {old_replicas} to {replicas} replicas",
                    }

                if resource_type.lower() in ["replicaset", "rs"]:
                    # Get current replicaset
                    replicaset = apps_v1.read_namespaced_replica_set(name, namespace)
                    old_replicas = replicaset.spec.replicas

                    # Update replicas
                    replicaset.spec.replicas = replicas

                    # Apply the update
                    apps_v1.patch_namespaced_replica_set(
                        name=name, namespace=namespace, body=replicaset
                    )

                    return {
                        "status": "success",
                        "resource": {
                            "kind": "ReplicaSet",
                            "name": name,
                            "namespace": namespace,
                            "old_replicas": old_replicas,
                            "new_replicas": replicas,
                        },
                        "message": f"Scaled replicaset {name} from {old_replicas} to {replicas} replicas",
                    }

                if resource_type.lower() in ["statefulset", "sts"]:
                    # Get current statefulset
                    statefulset = apps_v1.read_namespaced_stateful_set(name, namespace)
                    old_replicas = statefulset.spec.replicas

                    # Update replicas
                    statefulset.spec.replicas = replicas

                    # Apply the update
                    apps_v1.patch_namespaced_stateful_set(
                        name=name, namespace=namespace, body=statefulset
                    )

                    return {
                        "status": "success",
                        "resource": {
                            "kind": "StatefulSet",
                            "name": name,
                            "namespace": namespace,
                            "old_replicas": old_replicas,
                            "new_replicas": replicas,
                        },
                        "message": f"Scaled statefulset {name} from {old_replicas} to {replicas} replicas",
                    }

                if resource_type.lower() in ["replicationcontroller", "rc"]:
                    v1 = client.CoreV1Api()

                    # Get current replication controller
                    replication_controller = v1.read_namespaced_replication_controller(
                        name, namespace
                    )
                    old_replicas = replication_controller.spec.replicas

                    # Update replicas
                    replication_controller.spec.replicas = replicas

                    # Apply the update
                    v1.patch_namespaced_replication_controller(
                        name=name, namespace=namespace, body=replication_controller
                    )

                    return {
                        "status": "success",
                        "resource": {
                            "kind": "ReplicationController",
                            "name": name,
                            "namespace": namespace,
                            "old_replicas": old_replicas,
                            "new_replicas": replicas,
                        },
                        "message": f"Scaled replication controller {name} from {old_replicas} to {replicas} replicas",
                    }

                return {
                    "error": f"Unsupported resource type for scaling: {resource_type}"
                }

            except Exception as e:
                return {"error": f"Failed to scale {resource_type} {name}: {str(e)}"}

        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
