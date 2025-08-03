"""Kubernetes expose tool for creating services."""

from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesExposeTool(BaseTool):
    """Tool for exposing Kubernetes resources as services."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()
            v1 = client.CoreV1Api()
            apps_v1 = client.AppsV1Api()

            resource_type = kwargs.get("resource_type", "deployment")
            resource_name = kwargs.get("resource_name", "")
            namespace = kwargs.get("namespace", "default")
            service_name = kwargs.get("service_name", "")
            port = kwargs.get("port", 80)
            target_port = kwargs.get("target_port", None)
            service_type = kwargs.get("service_type", "ClusterIP")
            protocol = kwargs.get("protocol", "TCP")

            if not resource_name:
                return {"error": "resource_name is required"}

            if not service_name:
                service_name = resource_name

            if target_port is None:
                target_port = port

            # Get labels from the resource
            labels = {}
            selector = {}

            try:
                if resource_type.lower() == "deployment":
                    deployment = apps_v1.read_namespaced_deployment(
                        resource_name, namespace
                    )
                    labels = deployment.metadata.labels or {"app": resource_name}
                    selector = deployment.spec.selector.match_labels
                elif resource_type.lower() == "pod":
                    pod = v1.read_namespaced_pod(resource_name, namespace)
                    labels = pod.metadata.labels or {"app": resource_name}
                    selector = labels
                elif resource_type.lower() in ["replicationcontroller", "rc"]:
                    replication_controller = v1.read_namespaced_replication_controller(
                        resource_name, namespace
                    )
                    labels = replication_controller.metadata.labels or {
                        "app": resource_name
                    }
                    selector = replication_controller.spec.selector or labels
                elif resource_type.lower() in ["replicaset", "rs"]:
                    replica_set = apps_v1.read_namespaced_replica_set(
                        resource_name, namespace
                    )
                    labels = replica_set.metadata.labels or {"app": resource_name}
                    selector = replica_set.spec.selector.match_labels
                elif resource_type.lower() == "service":
                    # If exposing an existing service, read it
                    existing_service = v1.read_namespaced_service(
                        resource_name, namespace
                    )
                    labels = existing_service.metadata.labels or {"app": resource_name}
                    selector = existing_service.spec.selector
                else:
                    return {"error": f"Unsupported resource type: {resource_type}"}
            except Exception as e:
                return {
                    "error": f"Failed to read {resource_type} {resource_name}: {str(e)}"
                }

            # Create service specification
            service_spec = client.V1Service(
                api_version="v1",
                kind="Service",
                metadata=client.V1ObjectMeta(
                    name=service_name, namespace=namespace, labels=labels
                ),
                spec=client.V1ServiceSpec(
                    type=service_type,
                    selector=selector,
                    ports=[
                        client.V1ServicePort(
                            port=port,
                            target_port=target_port,
                            protocol=protocol,
                            name=f"port-{port}",
                        )
                    ],
                ),
            )

            # Create the service
            try:
                service = v1.create_namespaced_service(namespace, service_spec)

                result = {
                    "status": "success",
                    "service": {
                        "name": service.metadata.name,
                        "namespace": service.metadata.namespace,
                        "type": service.spec.type,
                        "cluster_ip": service.spec.cluster_ip,
                        "ports": [
                            {"port": p.port, "target_port": p.target_port}
                            for p in service.spec.ports
                        ],
                        "selector": service.spec.selector,
                    },
                }

                # Add external IP/hostname for LoadBalancer services
                if (
                    service_type == "LoadBalancer"
                    and service.status.load_balancer.ingress
                ):
                    ingress = service.status.load_balancer.ingress[0]
                    if ingress.ip:
                        result["service"]["external_ip"] = ingress.ip
                    if ingress.hostname:
                        result["service"]["external_hostname"] = ingress.hostname

                return result

            except Exception as e:
                return {"error": f"Failed to create service: {str(e)}"}

        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
