"""Kubernetes explain tool for understanding resource schemas."""

from kubernetes import config

from src.base_tool import BaseTool


class KubernetesExplainTool(BaseTool):
    """Tool for explaining Kubernetes resource fields and their schemas."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()

            resource = kwargs.get("resource", "")
            api_version = kwargs.get("api_version", None)

            if not resource:
                return {"error": "resource is required"}

            # Map common resource names to their API details
            resource_map = {
                # Core v1 resources
                "pod": {"api_version": "v1", "kind": "Pod", "namespaced": True},
                "pods": {"api_version": "v1", "kind": "Pod", "namespaced": True},
                "service": {"api_version": "v1", "kind": "Service", "namespaced": True},
                "services": {
                    "api_version": "v1",
                    "kind": "Service",
                    "namespaced": True,
                },
                "svc": {"api_version": "v1", "kind": "Service", "namespaced": True},
                "namespace": {
                    "api_version": "v1",
                    "kind": "Namespace",
                    "namespaced": False,
                },
                "namespaces": {
                    "api_version": "v1",
                    "kind": "Namespace",
                    "namespaced": False,
                },
                "ns": {"api_version": "v1", "kind": "Namespace", "namespaced": False},
                "node": {"api_version": "v1", "kind": "Node", "namespaced": False},
                "nodes": {"api_version": "v1", "kind": "Node", "namespaced": False},
                "configmap": {
                    "api_version": "v1",
                    "kind": "ConfigMap",
                    "namespaced": True,
                },
                "configmaps": {
                    "api_version": "v1",
                    "kind": "ConfigMap",
                    "namespaced": True,
                },
                "cm": {"api_version": "v1", "kind": "ConfigMap", "namespaced": True},
                "secret": {"api_version": "v1", "kind": "Secret", "namespaced": True},
                "secrets": {"api_version": "v1", "kind": "Secret", "namespaced": True},
                "persistentvolume": {
                    "api_version": "v1",
                    "kind": "PersistentVolume",
                    "namespaced": False,
                },
                "persistentvolumes": {
                    "api_version": "v1",
                    "kind": "PersistentVolume",
                    "namespaced": False,
                },
                "pv": {
                    "api_version": "v1",
                    "kind": "PersistentVolume",
                    "namespaced": False,
                },
                "persistentvolumeclaim": {
                    "api_version": "v1",
                    "kind": "PersistentVolumeClaim",
                    "namespaced": True,
                },
                "persistentvolumeclaims": {
                    "api_version": "v1",
                    "kind": "PersistentVolumeClaim",
                    "namespaced": True,
                },
                "pvc": {
                    "api_version": "v1",
                    "kind": "PersistentVolumeClaim",
                    "namespaced": True,
                },
                # Apps v1 resources
                "deployment": {
                    "api_version": "apps/v1",
                    "kind": "Deployment",
                    "namespaced": True,
                },
                "deployments": {
                    "api_version": "apps/v1",
                    "kind": "Deployment",
                    "namespaced": True,
                },
                "deploy": {
                    "api_version": "apps/v1",
                    "kind": "Deployment",
                    "namespaced": True,
                },
                "replicaset": {
                    "api_version": "apps/v1",
                    "kind": "ReplicaSet",
                    "namespaced": True,
                },
                "replicasets": {
                    "api_version": "apps/v1",
                    "kind": "ReplicaSet",
                    "namespaced": True,
                },
                "rs": {
                    "api_version": "apps/v1",
                    "kind": "ReplicaSet",
                    "namespaced": True,
                },
                "statefulset": {
                    "api_version": "apps/v1",
                    "kind": "StatefulSet",
                    "namespaced": True,
                },
                "statefulsets": {
                    "api_version": "apps/v1",
                    "kind": "StatefulSet",
                    "namespaced": True,
                },
                "sts": {
                    "api_version": "apps/v1",
                    "kind": "StatefulSet",
                    "namespaced": True,
                },
                "daemonset": {
                    "api_version": "apps/v1",
                    "kind": "DaemonSet",
                    "namespaced": True,
                },
                "daemonsets": {
                    "api_version": "apps/v1",
                    "kind": "DaemonSet",
                    "namespaced": True,
                },
                "ds": {
                    "api_version": "apps/v1",
                    "kind": "DaemonSet",
                    "namespaced": True,
                },
                # Batch v1 resources
                "job": {"api_version": "batch/v1", "kind": "Job", "namespaced": True},
                "jobs": {"api_version": "batch/v1", "kind": "Job", "namespaced": True},
                "cronjob": {
                    "api_version": "batch/v1",
                    "kind": "CronJob",
                    "namespaced": True,
                },
                "cronjobs": {
                    "api_version": "batch/v1",
                    "kind": "CronJob",
                    "namespaced": True,
                },
                "cj": {
                    "api_version": "batch/v1",
                    "kind": "CronJob",
                    "namespaced": True,
                },
                # Networking v1 resources
                "ingress": {
                    "api_version": "networking.k8s.io/v1",
                    "kind": "Ingress",
                    "namespaced": True,
                },
                "ingresses": {
                    "api_version": "networking.k8s.io/v1",
                    "kind": "Ingress",
                    "namespaced": True,
                },
                "ing": {
                    "api_version": "networking.k8s.io/v1",
                    "kind": "Ingress",
                    "namespaced": True,
                },
                # Autoscaling resources
                "horizontalpodautoscaler": {
                    "api_version": "autoscaling/v2",
                    "kind": "HorizontalPodAutoscaler",
                    "namespaced": True,
                },
                "horizontalpodautoscalers": {
                    "api_version": "autoscaling/v2",
                    "kind": "HorizontalPodAutoscaler",
                    "namespaced": True,
                },
                "hpa": {
                    "api_version": "autoscaling/v2",
                    "kind": "HorizontalPodAutoscaler",
                    "namespaced": True,
                },
            }

            # Check for field path (e.g., "pod.spec.containers")
            field_path = None
            if "." in resource:
                parts = resource.split(".", 1)
                resource = parts[0]
                field_path = parts[1]

            resource_lower = resource.lower()
            if resource_lower not in resource_map:
                return {
                    "error": f"Unknown resource type: {resource}",
                    "suggestion": "Try one of: pod, deployment, service, configmap, secret, etc.",
                }

            resource_info = resource_map[resource_lower]

            # Build explanation
            explanation = {
                "resource": resource,
                "kind": resource_info["kind"],
                "apiVersion": resource_info["api_version"],
                "namespaced": resource_info["namespaced"],
                "description": self._get_resource_description(resource_info["kind"]),
                "fields": self._get_common_fields(resource_info["kind"], field_path),
            }

            # Add examples
            explanation["examples"] = self._get_resource_examples(resource_info["kind"])

            return explanation

        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    def _get_resource_description(self, kind):
        descriptions = {
            "Pod": "A Pod is the smallest deployable unit in Kubernetes, representing a single instance of a running process.",
            "Deployment": "A Deployment provides declarative updates for Pods and ReplicaSets. It manages the rollout of new versions.",
            "Service": "A Service is an abstract way to expose an application running on a set of Pods as a network service.",
            "ConfigMap": "A ConfigMap allows you to decouple configuration artifacts from image content to keep containerized applications portable.",
            "Secret": "A Secret is an object that contains sensitive data such as passwords, OAuth tokens, and SSH keys.",
            "Namespace": "A Namespace provides a scope for names and a mechanism to divide cluster resources between multiple users.",
            "Node": "A Node is a worker machine in Kubernetes, either a virtual or physical machine.",
            "ReplicaSet": "A ReplicaSet ensures that a specified number of pod replicas are running at any given time.",
            "StatefulSet": "A StatefulSet manages the deployment and scaling of a set of Pods with persistent storage and stable network identities.",
            "DaemonSet": "A DaemonSet ensures that all (or some) nodes run a copy of a Pod.",
            "Job": "A Job creates one or more Pods and ensures that a specified number of them successfully terminate.",
            "CronJob": "A CronJob creates Jobs on a repeating schedule, similar to the Unix cron utility.",
            "Ingress": "An Ingress manages external access to services in a cluster, typically HTTP/HTTPS.",
            "HorizontalPodAutoscaler": "HPA automatically scales the number of Pods based on CPU utilization or custom metrics.",
            "PersistentVolume": "A PersistentVolume is a piece of storage provisioned by an administrator or dynamically provisioned.",
            "PersistentVolumeClaim": "A PersistentVolumeClaim is a request for storage by a user.",
        }
        return descriptions.get(kind, f"A {kind} is a Kubernetes resource.")

    def _get_common_fields(self, kind, field_path):
        # Common fields for all resources
        common_fields = {
            "apiVersion": {
                "type": "string",
                "description": "API version of the resource",
            },
            "kind": {
                "type": "string",
                "description": "Kind is a string value representing the resource type",
            },
            "metadata": {
                "type": "object",
                "description": "Standard object's metadata",
                "fields": {
                    "name": {"type": "string", "description": "Name of the resource"},
                    "namespace": {
                        "type": "string",
                        "description": "Namespace of the resource (if namespaced)",
                    },
                    "labels": {
                        "type": "map[string]string",
                        "description": "Map of string keys and values for organizing resources",
                    },
                    "annotations": {
                        "type": "map[string]string",
                        "description": "Map of string keys and values for storing arbitrary metadata",
                    },
                },
            },
        }

        # Kind-specific fields
        if kind == "Pod":
            common_fields["spec"] = {
                "type": "object",
                "description": "Specification of the desired behavior of the pod",
                "fields": {
                    "containers": {
                        "type": "array",
                        "description": "List of containers belonging to the pod",
                        "items": {
                            "name": {
                                "type": "string",
                                "description": "Name of the container",
                            },
                            "image": {
                                "type": "string",
                                "description": "Container image name",
                            },
                            "ports": {
                                "type": "array",
                                "description": "List of ports to expose",
                            },
                            "env": {
                                "type": "array",
                                "description": "List of environment variables",
                            },
                            "resources": {
                                "type": "object",
                                "description": "Compute resource requirements",
                            },
                        },
                    },
                    "restartPolicy": {
                        "type": "string",
                        "description": "Restart policy: Always, OnFailure, Never",
                    },
                },
            }
        elif kind == "Deployment":
            common_fields["spec"] = {
                "type": "object",
                "description": "Specification of the desired behavior of the deployment",
                "fields": {
                    "replicas": {
                        "type": "integer",
                        "description": "Number of desired pods",
                    },
                    "selector": {
                        "type": "object",
                        "description": "Label selector for pods",
                    },
                    "template": {
                        "type": "object",
                        "description": "Pod template specification",
                    },
                    "strategy": {
                        "type": "object",
                        "description": "Deployment strategy to use",
                    },
                },
            }
        elif kind == "Service":
            common_fields["spec"] = {
                "type": "object",
                "description": "Specification of the desired behavior of the service",
                "fields": {
                    "type": {
                        "type": "string",
                        "description": "Service type: ClusterIP, NodePort, LoadBalancer, ExternalName",
                    },
                    "selector": {
                        "type": "map[string]string",
                        "description": "Label selector for pods",
                    },
                    "ports": {
                        "type": "array",
                        "description": "List of ports that are exposed",
                    },
                },
            }

        # If a specific field path was requested, try to extract just that field
        if field_path:
            parts = field_path.split(".")
            current = common_fields
            for part in parts:
                if isinstance(current, dict):
                    if part in current:
                        current = current[part]
                    elif "fields" in current and part in current["fields"]:
                        current = current["fields"][part]
                    else:
                        return {
                            field_path: {
                                "error": f"Field path '{field_path}' not found"
                            }
                        }
            return {field_path: current}

        return common_fields

    def _get_resource_examples(self, kind):
        examples = {
            "Pod": {
                "simple": """apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
spec:
  containers:
  - name: nginx
    image: nginx:latest
    ports:
    - containerPort: 80""",
            },
            "Deployment": {
                "simple": """apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:latest
        ports:
        - containerPort: 80""",
            },
            "Service": {
                "simple": """apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  selector:
    app: nginx
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP""",
            },
        }
        return examples.get(kind, {})
