"""Kubernetes run tool for creating deployments and pods."""

from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesRunTool(BaseTool):
    """Tool for quickly running container images in Kubernetes."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()
            apps_v1 = client.AppsV1Api()

            name = kwargs.get("name", "")
            image = kwargs.get("image", "")
            namespace = kwargs.get("namespace", "default")
            replicas = kwargs.get("replicas", 1)
            port = kwargs.get("port", None)
            env_vars = kwargs.get("env", {})
            labels = kwargs.get("labels", {})
            command = kwargs.get("command", None)
            args = kwargs.get("args", None)

            if not name:
                return {"error": "name is required"}
            if not image:
                return {"error": "image is required"}

            # Default labels
            if not labels:
                labels = {"app": name}

            # Create container spec
            container = client.V1Container(
                name=name, image=image, image_pull_policy="Always"
            )

            # Add port if specified
            if port:
                container.ports = [client.V1ContainerPort(container_port=port)]

            # Add environment variables
            if env_vars:
                container.env = [
                    client.V1EnvVar(name=k, value=str(v)) for k, v in env_vars.items()
                ]

            # Add command and args if specified
            if command:
                container.command = command if isinstance(command, list) else [command]
            if args:
                container.args = args if isinstance(args, list) else [args]

            # Create deployment spec
            deployment = client.V1Deployment(
                api_version="apps/v1",
                kind="Deployment",
                metadata=client.V1ObjectMeta(
                    name=name, namespace=namespace, labels=labels
                ),
                spec=client.V1DeploymentSpec(
                    replicas=replicas,
                    selector=client.V1LabelSelector(match_labels=labels),
                    template=client.V1PodTemplateSpec(
                        metadata=client.V1ObjectMeta(labels=labels),
                        spec=client.V1PodSpec(containers=[container]),
                    ),
                ),
            )

            try:
                # Create the deployment
                created_deployment = apps_v1.create_namespaced_deployment(
                    namespace=namespace, body=deployment
                )

                return {
                    "status": "success",
                    "deployment": {
                        "name": created_deployment.metadata.name,
                        "namespace": created_deployment.metadata.namespace,
                        "replicas": created_deployment.spec.replicas,
                        "image": image,
                        "labels": created_deployment.metadata.labels,
                    },
                    "message": f"Deployment {name} created successfully",
                }

            except Exception as e:
                return {"error": f"Failed to create deployment: {str(e)}"}

        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
