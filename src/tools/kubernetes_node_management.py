"""Kubernetes node management tool for managing cluster nodes."""

from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesNodeManagementTool(BaseTool):
    """Tool for managing Kubernetes cluster nodes and their states."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()
            v1 = client.CoreV1Api()

            action = kwargs.get("action", "")
            node_name = kwargs.get("node_name", "")

            if not action:
                return {"error": "action is required (cordon, uncordon, drain, taint)"}
            if not node_name:
                return {"error": "node_name is required"}

            if action == "cordon":
                return self._cordon_node(v1, node_name)
            if action == "uncordon":
                return self._uncordon_node(v1, node_name)
            if action == "drain":
                ignore_daemonsets = kwargs.get("ignore_daemonsets", True)
                delete_emptydir_data = kwargs.get("delete_emptydir_data", True)
                force = kwargs.get("force", False)
                grace_period = kwargs.get("grace_period", 30)
                return self._drain_node(
                    v1,
                    node_name,
                    ignore_daemonsets,
                    delete_emptydir_data,
                    force,
                    grace_period,
                )
            if action == "taint":
                taint_action = kwargs.get("taint_action", "add")  # add or remove
                key = kwargs.get("key", "")
                value = kwargs.get("value", "")
                effect = kwargs.get(
                    "effect", "NoSchedule"
                )  # NoSchedule, PreferNoSchedule, NoExecute
                return self._manage_taint(
                    v1, node_name, taint_action, key, value, effect
                )
            return {
                "error": f"Unknown action: {action}. Supported: cordon, uncordon, drain, taint"
            }

        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    def _cordon_node(self, api, node_name):
        """Mark node as unschedulable"""
        try:
            # Get the node
            node = api.read_node(node_name)

            # Set unschedulable
            node.spec.unschedulable = True

            # Update the node
            updated_node = api.patch_node(node_name, node)

            return {
                "status": "success",
                "message": f"Node {node_name} cordoned (marked unschedulable)",
                "node": {
                    "name": updated_node.metadata.name,
                    "unschedulable": updated_node.spec.unschedulable,
                },
            }

        except Exception as e:
            return {"error": f"Failed to cordon node: {str(e)}"}

    def _uncordon_node(self, api, node_name):
        """Mark node as schedulable"""
        try:
            # Get the node
            node = api.read_node(node_name)

            # Set schedulable
            node.spec.unschedulable = False

            # Update the node
            updated_node = api.patch_node(node_name, node)

            return {
                "status": "success",
                "message": f"Node {node_name} uncordoned (marked schedulable)",
                "node": {
                    "name": updated_node.metadata.name,
                    "unschedulable": updated_node.spec.unschedulable,
                },
            }

        except Exception as e:
            return {"error": f"Failed to uncordon node: {str(e)}"}

    def _drain_node(
        self,
        api,
        node_name,
        ignore_daemonsets,
        delete_emptydir_data,
        force,
        grace_period,
    ):
        """Drain node by evicting pods"""
        try:
            # First, cordon the node
            cordon_result = self._cordon_node(api, node_name)
            if "error" in cordon_result:
                return cordon_result

            # Get all pods on the node
            field_selector = f"spec.nodeName={node_name}"
            pods = api.list_pod_for_all_namespaces(field_selector=field_selector)

            evicted_pods = []
            failed_pods = []
            skipped_pods = []

            for pod in pods.items:
                pod_name = pod.metadata.name
                namespace = pod.metadata.namespace

                # Skip mirror pods (static pods)
                if (
                    pod.metadata.annotations
                    and "kubernetes.io/config.mirror" in pod.metadata.annotations
                ):
                    skipped_pods.append(
                        {
                            "name": pod_name,
                            "namespace": namespace,
                            "reason": "mirror pod",
                        }
                    )
                    continue

                # Check if it's a DaemonSet pod
                if pod.metadata.owner_references:
                    for owner in pod.metadata.owner_references:
                        if owner.kind == "DaemonSet":
                            if ignore_daemonsets:
                                skipped_pods.append(
                                    {
                                        "name": pod_name,
                                        "namespace": namespace,
                                        "reason": "daemonset pod",
                                    }
                                )
                                continue
                            if not force:
                                failed_pods.append(
                                    {
                                        "name": pod_name,
                                        "namespace": namespace,
                                        "reason": "daemonset pod (use force=True to evict)",
                                    }
                                )
                                continue

                # Check for emptyDir volumes
                has_emptydir = False
                if pod.spec.volumes:
                    for volume in pod.spec.volumes:
                        if volume.empty_dir is not None:
                            has_emptydir = True
                            break

                if has_emptydir and not delete_emptydir_data and not force:
                    failed_pods.append(
                        {
                            "name": pod_name,
                            "namespace": namespace,
                            "reason": "has emptyDir volume (use delete_emptydir_data=True or force=True)",
                        }
                    )
                    continue

                # Try to evict the pod
                try:
                    eviction = client.V1Eviction(
                        metadata=client.V1ObjectMeta(
                            name=pod_name, namespace=namespace
                        ),
                        delete_options=client.V1DeleteOptions(
                            grace_period_seconds=grace_period
                        ),
                    )

                    api.create_namespaced_pod_eviction(
                        name=pod_name, namespace=namespace, body=eviction
                    )

                    evicted_pods.append({"name": pod_name, "namespace": namespace})

                except Exception as e:
                    failed_pods.append(
                        {"name": pod_name, "namespace": namespace, "reason": str(e)}
                    )

            return {
                "status": "success" if not failed_pods else "partial",
                "message": f"Node {node_name} drain {'completed' if not failed_pods else 'completed with errors'}",
                "node": node_name,
                "evicted_pods": evicted_pods,
                "skipped_pods": skipped_pods,
                "failed_pods": failed_pods,
                "summary": {
                    "total_pods": len(pods.items),
                    "evicted": len(evicted_pods),
                    "skipped": len(skipped_pods),
                    "failed": len(failed_pods),
                },
            }

        except Exception as e:
            return {"error": f"Failed to drain node: {str(e)}"}

    def _manage_taint(self, api, node_name, taint_action, key, value, effect):
        """Add or remove taints from a node"""
        try:
            if not key:
                return {"error": "key is required for taint operations"}

            # Validate effect
            valid_effects = ["NoSchedule", "PreferNoSchedule", "NoExecute"]
            if effect not in valid_effects:
                return {
                    "error": f"Invalid effect: {effect}. Must be one of: {', '.join(valid_effects)}"
                }

            # Get the node
            node = api.read_node(node_name)

            if taint_action == "add":
                # Create new taint
                new_taint = client.V1Taint(key=key, value=value, effect=effect)

                # Initialize taints list if needed
                if not node.spec.taints:
                    node.spec.taints = []

                # Check if taint already exists
                taint_exists = False
                for i, taint in enumerate(node.spec.taints):
                    if taint.key == key and taint.effect == effect:
                        # Update existing taint
                        node.spec.taints[i] = new_taint
                        taint_exists = True
                        break

                if not taint_exists:
                    # Add new taint
                    node.spec.taints.append(new_taint)

                # Update the node
                updated_node = api.patch_node(node_name, node)

                return {
                    "status": "success",
                    "message": f"Taint {'updated' if taint_exists else 'added'} on node {node_name}",
                    "taint": {"key": key, "value": value, "effect": effect},
                    "node_taints": [
                        {"key": t.key, "value": t.value, "effect": t.effect}
                        for t in (updated_node.spec.taints or [])
                    ],
                }

            if taint_action == "remove":
                # Remove taint
                if not node.spec.taints:
                    return {
                        "status": "success",
                        "message": f"Node {node_name} has no taints",
                        "node_taints": [],
                    }

                # Filter out the taint to remove
                original_count = len(node.spec.taints)
                node.spec.taints = [
                    t
                    for t in node.spec.taints
                    if not (t.key == key and (effect == "" or t.effect == effect))
                ]

                if len(node.spec.taints) == original_count:
                    return {
                        "status": "not_found",
                        "message": f"Taint with key '{key}' not found on node {node_name}",
                        "node_taints": [
                            {"key": t.key, "value": t.value, "effect": t.effect}
                            for t in node.spec.taints
                        ],
                    }

                # Update the node
                updated_node = api.patch_node(node_name, node)

                return {
                    "status": "success",
                    "message": f"Taint removed from node {node_name}",
                    "removed_taint": {
                        "key": key,
                        "effect": effect if effect else "any",
                    },
                    "node_taints": [
                        {"key": t.key, "value": t.value, "effect": t.effect}
                        for t in (updated_node.spec.taints or [])
                    ],
                }

            return {
                "error": f"Invalid taint_action: {taint_action}. Use 'add' or 'remove'"
            }

        except Exception as e:
            return {"error": f"Failed to manage taint: {str(e)}"}
