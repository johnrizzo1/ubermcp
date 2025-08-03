"""Kubernetes rollout tool for managing deployment rollouts."""

import time

from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesRolloutTool(BaseTool):
    """Tool for managing rollouts of Kubernetes deployments."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()
            apps_v1 = client.AppsV1Api()

            action = kwargs.get("action", "status")
            resource_type = kwargs.get("resource_type", "deployment")
            name = kwargs.get("name", "")
            namespace = kwargs.get("namespace", "default")
            revision = kwargs.get("revision", None)

            if not name:
                return {"error": "name is required"}

            if resource_type.lower() not in [
                "deployment",
                "deploy",
                "daemonset",
                "ds",
                "statefulset",
                "sts",
            ]:
                return {
                    "error": f"Rollout operations not supported for resource type: {resource_type}"
                }

            if action == "status":
                return self._get_rollout_status(apps_v1, resource_type, name, namespace)
            if action == "history":
                return self._get_rollout_history(
                    apps_v1, resource_type, name, namespace
                )
            if action == "undo":
                return self._rollout_undo(
                    apps_v1, resource_type, name, namespace, revision
                )
            if action == "pause":
                return self._rollout_pause(apps_v1, resource_type, name, namespace)
            if action == "resume":
                return self._rollout_resume(apps_v1, resource_type, name, namespace)
            if action == "restart":
                return self._rollout_restart(apps_v1, resource_type, name, namespace)
            return {
                "error": f"Unknown action: {action}. Supported: status, history, undo, pause, resume, restart"
            }

        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    def _get_rollout_status(self, api, resource_type, name, namespace):
        try:
            if resource_type.lower() in ["deployment", "deploy"]:
                deployment = api.read_namespaced_deployment(name, namespace)

                # Get replica sets for this deployment
                label_selector = ""
                if deployment.spec.selector.match_labels:
                    label_selector = ",".join(
                        [
                            f"{k}={v}"
                            for k, v in deployment.spec.selector.match_labels.items()
                        ]
                    )

                replica_sets = api.list_namespaced_replica_set(
                    namespace, label_selector=label_selector
                )

                # Find the new and old replica sets
                new_replica_set = None
                old_replica_set_list = []

                for replica_set in replica_sets.items:
                    if (
                        replica_set.metadata.annotations
                        and replica_set.metadata.annotations.get(
                            "deployment.kubernetes.io/revision"
                        )
                        == str(deployment.metadata.generation)
                    ):
                        new_replica_set = replica_set
                    else:
                        old_replica_set_list.append(replica_set)

                conditions = []
                for condition in deployment.status.conditions or []:
                    conditions.append(
                        {
                            "type": condition.type,
                            "status": condition.status,
                            "reason": condition.reason,
                            "message": condition.message,
                        }
                    )

                status = {
                    "deployment": name,
                    "namespace": namespace,
                    "replicas": {
                        "desired": deployment.spec.replicas,
                        "updated": deployment.status.updated_replicas or 0,
                        "ready": deployment.status.ready_replicas or 0,
                        "available": deployment.status.available_replicas or 0,
                    },
                    "conditions": conditions,
                    "rollout_status": (
                        "Complete"
                        if deployment.status.ready_replicas == deployment.spec.replicas
                        else "In Progress"
                    ),
                }

                if new_replica_set:
                    status["current_revision"] = (
                        new_replica_set.metadata.annotations.get(
                            "deployment.kubernetes.io/revision", "Unknown"
                        )
                    )

                return status

            if resource_type.lower() in ["statefulset", "sts"]:
                statefulset = api.read_namespaced_stateful_set(name, namespace)

                status = {
                    "statefulset": name,
                    "namespace": namespace,
                    "replicas": {
                        "desired": statefulset.spec.replicas,
                        "ready": statefulset.status.ready_replicas or 0,
                        "current": statefulset.status.current_replicas or 0,
                        "updated": statefulset.status.updated_replicas or 0,
                    },
                    "current_revision": statefulset.status.current_revision,
                    "update_revision": statefulset.status.update_revision,
                    "rollout_status": (
                        "Complete"
                        if statefulset.status.ready_replicas
                        == statefulset.spec.replicas
                        else "In Progress"
                    ),
                }

                return status

            if resource_type.lower() in ["daemonset", "ds"]:
                daemonset = api.read_namespaced_daemon_set(name, namespace)

                status = {
                    "daemonset": name,
                    "namespace": namespace,
                    "desired": daemonset.status.desired_number_scheduled,
                    "current": daemonset.status.current_number_scheduled,
                    "ready": daemonset.status.number_ready,
                    "updated": daemonset.status.updated_number_scheduled,
                    "rollout_status": (
                        "Complete"
                        if daemonset.status.number_ready
                        == daemonset.status.desired_number_scheduled
                        else "In Progress"
                    ),
                }

                return status

        except Exception as e:
            return {"error": f"Failed to get rollout status: {str(e)}"}

    def _get_rollout_history(self, api, resource_type, name, namespace):
        try:
            if resource_type.lower() in ["deployment", "deploy"]:
                deployment = api.read_namespaced_deployment(name, namespace)

                # Get all replica sets for this deployment
                label_selector = ""
                if deployment.spec.selector.match_labels:
                    label_selector = ",".join(
                        [
                            f"{k}={v}"
                            for k, v in deployment.spec.selector.match_labels.items()
                        ]
                    )

                replica_sets = api.list_namespaced_replica_set(
                    namespace, label_selector=label_selector
                )

                history = []
                for replica_set in sorted(
                    replica_sets.items,
                    key=lambda x: int(
                        x.metadata.annotations.get(
                            "deployment.kubernetes.io/revision", "0"
                        )
                    ),
                ):
                    revision = replica_set.metadata.annotations.get(
                        "deployment.kubernetes.io/revision", "Unknown"
                    )
                    change_cause = replica_set.metadata.annotations.get(
                        "kubernetes.io/change-cause", "None"
                    )

                    history.append(
                        {
                            "revision": revision,
                            "change_cause": change_cause,
                            "replica_set": replica_set.metadata.name,
                            "created": str(replica_set.metadata.creation_timestamp),
                        }
                    )

                return {"deployment": name, "namespace": namespace, "history": history}

            return {
                "error": f"History not implemented for resource type: {resource_type}"
            }

        except Exception as e:
            return {"error": f"Failed to get rollout history: {str(e)}"}

    def _rollout_undo(self, api, resource_type, name, namespace, revision):
        try:
            if resource_type.lower() in ["deployment", "deploy"]:
                # Get deployment
                deployment = api.read_namespaced_deployment(name, namespace)

                if revision:
                    # TODO: Implement rollback to specific revision
                    # This would require finding the replica set with the specified revision
                    # and updating the deployment's pod template spec to match
                    return {
                        "error": "Rollback to specific revision not yet implemented"
                    }
                # Rollback to previous revision
                # Add annotation to trigger rollback
                if not deployment.spec.template.metadata.annotations:
                    deployment.spec.template.metadata.annotations = {}

                # Update a timestamp annotation to trigger a new rollout
                deployment.spec.template.metadata.annotations[
                    "kubectl.kubernetes.io/restartedAt"
                ] = str(time.time())

                # Apply the update
                api.patch_namespaced_deployment(name, namespace, deployment)

                return {
                    "status": "success",
                    "message": f"Rolled back deployment {name}",
                    "deployment": name,
                    "namespace": namespace,
                }

            return {"error": f"Undo not implemented for resource type: {resource_type}"}

        except Exception as e:
            return {"error": f"Failed to rollback: {str(e)}"}

    def _rollout_pause(self, api, resource_type, name, namespace):
        try:
            if resource_type.lower() in ["deployment", "deploy"]:
                # Pause deployment rollout
                body = {"spec": {"paused": True}}
                api.patch_namespaced_deployment(name, namespace, body)

                return {
                    "status": "success",
                    "message": f"Paused rollout for deployment {name}",
                    "deployment": name,
                    "namespace": namespace,
                }

            return {"error": f"Pause not supported for resource type: {resource_type}"}

        except Exception as e:
            return {"error": f"Failed to pause rollout: {str(e)}"}

    def _rollout_resume(self, api, resource_type, name, namespace):
        try:
            if resource_type.lower() in ["deployment", "deploy"]:
                # Resume deployment rollout
                body = {"spec": {"paused": False}}
                api.patch_namespaced_deployment(name, namespace, body)

                return {
                    "status": "success",
                    "message": f"Resumed rollout for deployment {name}",
                    "deployment": name,
                    "namespace": namespace,
                }

            return {"error": f"Resume not supported for resource type: {resource_type}"}

        except Exception as e:
            return {"error": f"Failed to resume rollout: {str(e)}"}

    def _rollout_restart(self, api, resource_type, name, namespace):
        try:
            if resource_type.lower() in ["deployment", "deploy"]:
                deployment = api.read_namespaced_deployment(name, namespace)

                # Add/update annotation to trigger restart
                if not deployment.spec.template.metadata.annotations:
                    deployment.spec.template.metadata.annotations = {}

                deployment.spec.template.metadata.annotations[
                    "kubectl.kubernetes.io/restartedAt"
                ] = str(time.time())

                # Apply the update
                api.patch_namespaced_deployment(name, namespace, deployment)

                return {
                    "status": "success",
                    "message": f"Restarted deployment {name}",
                    "deployment": name,
                    "namespace": namespace,
                }

            if resource_type.lower() in ["statefulset", "sts"]:
                statefulset = api.read_namespaced_stateful_set(name, namespace)

                if not statefulset.spec.template.metadata.annotations:
                    statefulset.spec.template.metadata.annotations = {}

                statefulset.spec.template.metadata.annotations[
                    "kubectl.kubernetes.io/restartedAt"
                ] = str(time.time())

                api.patch_namespaced_stateful_set(name, namespace, statefulset)

                return {
                    "status": "success",
                    "message": f"Restarted statefulset {name}",
                    "statefulset": name,
                    "namespace": namespace,
                }

            if resource_type.lower() in ["daemonset", "ds"]:
                daemonset = api.read_namespaced_daemon_set(name, namespace)

                if not daemonset.spec.template.metadata.annotations:
                    daemonset.spec.template.metadata.annotations = {}

                daemonset.spec.template.metadata.annotations[
                    "kubectl.kubernetes.io/restartedAt"
                ] = str(time.time())

                api.patch_namespaced_daemon_set(name, namespace, daemonset)

                return {
                    "status": "success",
                    "message": f"Restarted daemonset {name}",
                    "daemonset": name,
                    "namespace": namespace,
                }

            return {
                "error": f"Restart not supported for resource type: {resource_type}"
            }

        except Exception as e:
            return {"error": f"Failed to restart: {str(e)}"}
