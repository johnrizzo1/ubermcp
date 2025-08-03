"""Kubernetes autoscale tool for managing horizontal pod autoscalers."""

from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesAutoscaleTool(BaseTool):
    """Tool for creating and managing horizontal pod autoscalers."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()
            autoscaling_v2 = client.AutoscalingV2Api()
            autoscaling_v1 = client.AutoscalingV1Api()

            action = kwargs.get("action", "create")
            resource_type = kwargs.get("resource_type", "deployment")
            resource_name = kwargs.get("resource_name", "")
            namespace = kwargs.get("namespace", "default")
            min_replicas = kwargs.get("min_replicas", 1)
            max_replicas = kwargs.get("max_replicas", 10)
            target_cpu_percent = kwargs.get("target_cpu_percent", 80)
            target_memory_percent = kwargs.get("target_memory_percent", None)
            hpa_name = kwargs.get("hpa_name", None)

            if action == "create":
                if not resource_name:
                    return {"error": "resource_name is required"}
                if not hpa_name:
                    hpa_name = f"{resource_name}-hpa"

                # Create HPA
                try:
                    # Create metrics list
                    metrics = []

                    # Add CPU metric
                    if target_cpu_percent:
                        cpu_metric = client.V2MetricSpec(
                            type="Resource",
                            resource=client.V2ResourceMetricSource(
                                name="cpu",
                                target=client.V2MetricTarget(
                                    type="Utilization",
                                    average_utilization=target_cpu_percent,
                                ),
                            ),
                        )
                        metrics.append(cpu_metric)

                    # Add memory metric if specified
                    if target_memory_percent:
                        memory_metric = client.V2MetricSpec(
                            type="Resource",
                            resource=client.V2ResourceMetricSource(
                                name="memory",
                                target=client.V2MetricTarget(
                                    type="Utilization",
                                    average_utilization=target_memory_percent,
                                ),
                            ),
                        )
                        metrics.append(memory_metric)

                    # Map resource type to scale target ref
                    scale_target_ref = None
                    if resource_type.lower() in ["deployment", "deploy"]:
                        scale_target_ref = client.V2CrossVersionObjectReference(
                            api_version="apps/v1", kind="Deployment", name=resource_name
                        )
                    elif resource_type.lower() in ["replicaset", "rs"]:
                        scale_target_ref = client.V2CrossVersionObjectReference(
                            api_version="apps/v1", kind="ReplicaSet", name=resource_name
                        )
                    elif resource_type.lower() in ["statefulset", "sts"]:
                        scale_target_ref = client.V2CrossVersionObjectReference(
                            api_version="apps/v1",
                            kind="StatefulSet",
                            name=resource_name,
                        )
                    else:
                        return {
                            "error": f"Unsupported resource type for autoscaling: {resource_type}"
                        }

                    # Create HPA spec
                    hpa = client.V2HorizontalPodAutoscaler(
                        api_version="autoscaling/v2",
                        kind="HorizontalPodAutoscaler",
                        metadata=client.V1ObjectMeta(
                            name=hpa_name, namespace=namespace
                        ),
                        spec=client.V2HorizontalPodAutoscalerSpec(
                            scale_target_ref=scale_target_ref,
                            min_replicas=min_replicas,
                            max_replicas=max_replicas,
                            metrics=metrics,
                        ),
                    )

                    # Create the HPA
                    created_hpa = (
                        autoscaling_v2.create_namespaced_horizontal_pod_autoscaler(
                            namespace=namespace, body=hpa
                        )
                    )

                    return {
                        "status": "success",
                        "hpa": {
                            "name": created_hpa.metadata.name,
                            "namespace": created_hpa.metadata.namespace,
                            "target": f"{resource_type}/{resource_name}",
                            "min_replicas": min_replicas,
                            "max_replicas": max_replicas,
                            "metrics": [
                                {
                                    "type": m.type,
                                    "resource": m.resource.name if m.resource else None,
                                }
                                for m in metrics
                            ],
                        },
                        "message": f"Created HorizontalPodAutoscaler {hpa_name}",
                    }

                except client.exceptions.ApiException as e:
                    if e.status == 409:
                        return {"error": f"HPA {hpa_name} already exists"}
                    return {"error": f"Failed to create HPA: {str(e)}"}

            elif action == "delete":
                if not hpa_name:
                    return {"error": "hpa_name is required for delete action"}

                try:
                    autoscaling_v1.delete_namespaced_horizontal_pod_autoscaler(
                        name=hpa_name, namespace=namespace
                    )

                    return {
                        "status": "success",
                        "message": f"Deleted HorizontalPodAutoscaler {hpa_name}",
                        "hpa": hpa_name,
                        "namespace": namespace,
                    }

                except client.exceptions.ApiException as e:
                    return {"error": f"Failed to delete HPA: {str(e)}"}

            elif action == "get":
                if hpa_name:
                    # Get specific HPA
                    try:
                        hpa = autoscaling_v2.read_namespaced_horizontal_pod_autoscaler(
                            hpa_name, namespace
                        )

                        metrics_info = []
                        for metric in hpa.spec.metrics or []:
                            metric_info = {"type": metric.type}
                            if metric.resource:
                                metric_info["resource"] = metric.resource.name
                                if metric.resource.target.average_utilization:
                                    metric_info["target_utilization"] = (
                                        metric.resource.target.average_utilization
                                    )
                            metrics_info.append(metric_info)

                        current_metrics = []
                        for metric in hpa.status.current_metrics or []:
                            current_info = {"type": metric.type}
                            if metric.resource:
                                current_info["resource"] = metric.resource.name
                                if metric.resource.current.average_utilization:
                                    current_info["current_utilization"] = (
                                        metric.resource.current.average_utilization
                                    )
                            current_metrics.append(current_info)

                        return {
                            "hpa": {
                                "name": hpa.metadata.name,
                                "namespace": hpa.metadata.namespace,
                                "target": f"{hpa.spec.scale_target_ref.kind}/{hpa.spec.scale_target_ref.name}",
                                "min_replicas": hpa.spec.min_replicas,
                                "max_replicas": hpa.spec.max_replicas,
                                "current_replicas": hpa.status.current_replicas,
                                "desired_replicas": hpa.status.desired_replicas,
                                "metrics": metrics_info,
                                "current_metrics": current_metrics,
                                "conditions": [
                                    {
                                        "type": c.type,
                                        "status": c.status,
                                        "reason": c.reason,
                                        "message": c.message,
                                    }
                                    for c in (hpa.status.conditions or [])
                                ],
                            }
                        }

                    except client.exceptions.ApiException as e:
                        return {"error": f"Failed to get HPA {hpa_name}: {str(e)}"}
                else:
                    # List all HPAs
                    try:
                        hpas = autoscaling_v2.list_namespaced_horizontal_pod_autoscaler(
                            namespace
                        )

                        hpa_list = []
                        for hpa in hpas.items:
                            hpa_list.append(
                                {
                                    "name": hpa.metadata.name,
                                    "target": f"{hpa.spec.scale_target_ref.kind}/{hpa.spec.scale_target_ref.name}",
                                    "min_replicas": hpa.spec.min_replicas,
                                    "max_replicas": hpa.spec.max_replicas,
                                    "current_replicas": hpa.status.current_replicas,
                                    "desired_replicas": hpa.status.desired_replicas,
                                }
                            )

                        return {
                            "hpas": hpa_list,
                            "count": len(hpa_list),
                            "namespace": namespace,
                        }

                    except client.exceptions.ApiException as e:
                        return {"error": f"Failed to list HPAs: {str(e)}"}

            else:
                return {
                    "error": f"Unknown action: {action}. Supported: create, delete, get"
                }

        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}
        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
