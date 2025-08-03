"""Kubernetes describe tool for showing detailed resource information."""

from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesDescribeTool(BaseTool):
    """Tool for describing Kubernetes resources with detailed information."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()

            resource_type = kwargs.get("resource_type", "")
            name = kwargs.get("name", "")
            namespace = kwargs.get("namespace", "default")

            if not resource_type:
                return {"error": "resource_type is required"}
            if not name:
                return {"error": "name is required"}

            # Initialize API clients
            v1 = client.CoreV1Api()
            apps_v1 = client.AppsV1Api()

            # Helper function to format events
            def get_events(name, namespace, kind):
                try:
                    field_selector = (
                        f"involvedObject.name={name},involvedObject.kind={kind}"
                    )
                    if namespace:
                        events = v1.list_namespaced_event(
                            namespace, field_selector=field_selector
                        )
                    else:
                        events = v1.list_event_for_all_namespaces(
                            field_selector=field_selector
                        )

                    event_list = []
                    for event in events.items:
                        event_list.append(
                            {
                                "type": event.type,
                                "reason": event.reason,
                                "message": event.message,
                                "first_seen": str(event.first_timestamp),
                                "last_seen": str(event.last_timestamp),
                                "count": event.count,
                            }
                        )
                    return event_list
                except Exception:
                    return []

            # Handle different resource types
            if resource_type.lower() in ["pod", "pods", "po"]:
                try:
                    pod = v1.read_namespaced_pod(name, namespace)

                    # Extract container details
                    containers = []
                    for container in pod.spec.containers:
                        container_info = {
                            "name": container.name,
                            "image": container.image,
                            "ports": [
                                {
                                    "containerPort": p.container_port,
                                    "protocol": p.protocol,
                                }
                                for p in (container.ports or [])
                            ],
                            "env": [
                                {"name": e.name, "value": e.value}
                                for e in (container.env or [])
                                if e.value
                            ],
                            "resources": (
                                container.resources.to_dict()
                                if container.resources
                                else {}
                            ),
                        }
                        containers.append(container_info)

                    # Extract container statuses
                    container_statuses = []
                    for status in pod.status.container_statuses or []:
                        status_info = {
                            "name": status.name,
                            "ready": status.ready,
                            "restart_count": status.restart_count,
                            "state": {},
                        }
                        if status.state:
                            if status.state.running:
                                status_info["state"]["running"] = {
                                    "started_at": str(status.state.running.started_at)
                                }
                            elif status.state.waiting:
                                status_info["state"]["waiting"] = {
                                    "reason": status.state.waiting.reason,
                                    "message": status.state.waiting.message,
                                }
                            elif status.state.terminated:
                                status_info["state"]["terminated"] = {
                                    "exit_code": status.state.terminated.exit_code,
                                    "reason": status.state.terminated.reason,
                                }
                        container_statuses.append(status_info)

                    # Get conditions
                    conditions = []
                    for condition in pod.status.conditions or []:
                        conditions.append(
                            {
                                "type": condition.type,
                                "status": condition.status,
                                "reason": condition.reason,
                                "message": condition.message,
                                "last_transition": str(condition.last_transition_time),
                            }
                        )

                    result = {
                        "kind": "Pod",
                        "metadata": {
                            "name": pod.metadata.name,
                            "namespace": pod.metadata.namespace,
                            "labels": pod.metadata.labels or {},
                            "annotations": pod.metadata.annotations or {},
                            "created": str(pod.metadata.creation_timestamp),
                            "uid": pod.metadata.uid,
                        },
                        "spec": {
                            "node_name": pod.spec.node_name,
                            "service_account": pod.spec.service_account_name,
                            "restart_policy": pod.spec.restart_policy,
                            "containers": containers,
                        },
                        "status": {
                            "phase": pod.status.phase,
                            "pod_ip": pod.status.pod_ip,
                            "host_ip": pod.status.host_ip,
                            "conditions": conditions,
                            "container_statuses": container_statuses,
                        },
                        "events": get_events(name, namespace, "Pod"),
                    }

                    return result

                except Exception as e:
                    return {"error": f"Failed to describe pod {name}: {str(e)}"}

            elif resource_type.lower() in ["deployment", "deployments", "deploy"]:
                try:
                    deployment = apps_v1.read_namespaced_deployment(name, namespace)

                    # Get conditions
                    conditions = []
                    for condition in deployment.status.conditions or []:
                        conditions.append(
                            {
                                "type": condition.type,
                                "status": condition.status,
                                "reason": condition.reason,
                                "message": condition.message,
                                "last_update": str(condition.last_update_time),
                            }
                        )

                    result = {
                        "kind": "Deployment",
                        "metadata": {
                            "name": deployment.metadata.name,
                            "namespace": deployment.metadata.namespace,
                            "labels": deployment.metadata.labels or {},
                            "annotations": deployment.metadata.annotations or {},
                            "created": str(deployment.metadata.creation_timestamp),
                            "uid": deployment.metadata.uid,
                        },
                        "spec": {
                            "replicas": deployment.spec.replicas,
                            "selector": deployment.spec.selector.match_labels,
                            "strategy": {
                                "type": deployment.spec.strategy.type,
                                "rolling_update": (
                                    deployment.spec.strategy.rolling_update.to_dict()
                                    if deployment.spec.strategy.rolling_update
                                    else None
                                ),
                            },
                            "template": {
                                "containers": [
                                    {
                                        "name": c.name,
                                        "image": c.image,
                                        "ports": [
                                            {"containerPort": p.container_port}
                                            for p in (c.ports or [])
                                        ],
                                    }
                                    for c in deployment.spec.template.spec.containers
                                ]
                            },
                        },
                        "status": {
                            "replicas": deployment.status.replicas,
                            "updated_replicas": deployment.status.updated_replicas,
                            "ready_replicas": deployment.status.ready_replicas,
                            "available_replicas": deployment.status.available_replicas,
                            "conditions": conditions,
                        },
                        "events": get_events(name, namespace, "Deployment"),
                    }

                    return result

                except Exception as e:
                    return {"error": f"Failed to describe deployment {name}: {str(e)}"}

            elif resource_type.lower() in ["service", "services", "svc"]:
                try:
                    service = v1.read_namespaced_service(name, namespace)

                    # Get endpoints
                    endpoints = []
                    try:
                        endpoint = v1.read_namespaced_endpoints(name, namespace)
                        for subset in endpoint.subsets or []:
                            for address in subset.addresses or []:
                                for port in subset.ports or []:
                                    endpoints.append(f"{address.ip}:{port.port}")
                    except Exception:
                        pass

                    result = {
                        "kind": "Service",
                        "metadata": {
                            "name": service.metadata.name,
                            "namespace": service.metadata.namespace,
                            "labels": service.metadata.labels or {},
                            "annotations": service.metadata.annotations or {},
                            "created": str(service.metadata.creation_timestamp),
                            "uid": service.metadata.uid,
                        },
                        "spec": {
                            "type": service.spec.type,
                            "cluster_ip": service.spec.cluster_ip,
                            "ports": [
                                {
                                    "name": p.name,
                                    "port": p.port,
                                    "target_port": str(p.target_port),
                                    "protocol": p.protocol,
                                }
                                for p in service.spec.ports
                            ],
                            "selector": service.spec.selector or {},
                        },
                        "endpoints": endpoints,
                        "events": get_events(name, namespace, "Service"),
                    }

                    # Add external IPs for LoadBalancer
                    if (
                        service.spec.type == "LoadBalancer"
                        and service.status.load_balancer.ingress
                    ):
                        result["status"] = {
                            "load_balancer": {
                                "ingress": [
                                    {"ip": ing.ip, "hostname": ing.hostname}
                                    for ing in service.status.load_balancer.ingress
                                ]
                            }
                        }

                    return result

                except Exception as e:
                    return {"error": f"Failed to describe service {name}: {str(e)}"}

            elif resource_type.lower() in ["node", "nodes", "no"]:
                try:
                    node = v1.read_node(name)

                    # Get conditions
                    conditions = []
                    for condition in node.status.conditions or []:
                        conditions.append(
                            {
                                "type": condition.type,
                                "status": condition.status,
                                "reason": condition.reason,
                                "message": condition.message,
                                "last_heartbeat": str(condition.last_heartbeat_time),
                            }
                        )

                    result = {
                        "kind": "Node",
                        "metadata": {
                            "name": node.metadata.name,
                            "labels": node.metadata.labels or {},
                            "annotations": node.metadata.annotations or {},
                            "created": str(node.metadata.creation_timestamp),
                            "uid": node.metadata.uid,
                        },
                        "spec": {
                            "taints": [
                                {"key": t.key, "value": t.value, "effect": t.effect}
                                for t in (node.spec.taints or [])
                            ],
                            "unschedulable": node.spec.unschedulable,
                        },
                        "status": {
                            "conditions": conditions,
                            "capacity": node.status.capacity,
                            "allocatable": node.status.allocatable,
                            "node_info": {
                                "os": node.status.node_info.operating_system,
                                "architecture": node.status.node_info.architecture,
                                "kernel_version": node.status.node_info.kernel_version,
                                "container_runtime": node.status.node_info.container_runtime_version,
                                "kubelet_version": node.status.node_info.kubelet_version,
                            },
                        },
                        "events": get_events(name, None, "Node"),
                    }

                    return result

                except Exception as e:
                    return {"error": f"Failed to describe node {name}: {str(e)}"}

            else:
                return {"error": f"Unsupported resource type: {resource_type}"}

        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
