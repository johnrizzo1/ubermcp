"""Kubernetes set tool for updating resource fields."""

from kubernetes import client, config

from src.base_tool import BaseTool


class KubernetesSetTool(BaseTool):
    """Tool for setting specific fields on Kubernetes resources."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()
            apps_v1 = client.AppsV1Api()

            resource_type = kwargs.get("resource_type", "deployment")
            resource_name = kwargs.get("resource_name", "")
            namespace = kwargs.get("namespace", "default")
            set_type = kwargs.get("set_type", "image")

            if not resource_name:
                return {"error": "resource_name is required"}

            if set_type == "image":
                container_name = kwargs.get("container_name", None)
                image = kwargs.get("image", "")

                if not image:
                    return {"error": "image is required for set_type='image'"}

                try:
                    if resource_type.lower() == "deployment":
                        deployment = apps_v1.read_namespaced_deployment(
                            resource_name, namespace
                        )

                        # Update container image
                        for container in deployment.spec.template.spec.containers:
                            if (
                                container_name is None
                                or container.name == container_name
                            ):
                                container.image = image
                                if container_name:
                                    break

                        # Apply the update
                        apps_v1.patch_namespaced_deployment(
                            name=resource_name, namespace=namespace, body=deployment
                        )

                        return {
                            "status": "success",
                            "message": f"Updated image for deployment {resource_name}",
                            "image": image,
                        }

                    if resource_type.lower() in ["daemonset", "ds"]:
                        daemonset = apps_v1.read_namespaced_daemon_set(
                            resource_name, namespace
                        )

                        for container in daemonset.spec.template.spec.containers:
                            if (
                                container_name is None
                                or container.name == container_name
                            ):
                                container.image = image
                                if container_name:
                                    break

                        apps_v1.patch_namespaced_daemon_set(
                            name=resource_name, namespace=namespace, body=daemonset
                        )

                        return {
                            "status": "success",
                            "message": f"Updated image for daemonset {resource_name}",
                            "image": image,
                        }

                    if resource_type.lower() in ["statefulset", "sts"]:
                        statefulset = apps_v1.read_namespaced_stateful_set(
                            resource_name, namespace
                        )

                        for container in statefulset.spec.template.spec.containers:
                            if (
                                container_name is None
                                or container.name == container_name
                            ):
                                container.image = image
                                if container_name:
                                    break

                        apps_v1.patch_namespaced_stateful_set(
                            name=resource_name, namespace=namespace, body=statefulset
                        )

                        return {
                            "status": "success",
                            "message": f"Updated image for statefulset {resource_name}",
                            "image": image,
                        }

                    return {
                        "error": f"Unsupported resource type for image update: {resource_type}"
                    }

                except client.exceptions.ApiException as e:
                    return {"error": f"Failed to update image: {str(e)}"}
                except Exception as e:
                    return {"error": f"Unexpected error updating image: {str(e)}"}

            if set_type == "resources":
                container_name = kwargs.get("container_name", None)
                limits = kwargs.get("limits", {})
                requests = kwargs.get("requests", {})

                try:
                    if resource_type.lower() == "deployment":
                        deployment = apps_v1.read_namespaced_deployment(
                            resource_name, namespace
                        )

                        for container in deployment.spec.template.spec.containers:
                            if (
                                container_name is None
                                or container.name == container_name
                            ):
                                if not container.resources:
                                    container.resources = (
                                        client.V1ResourceRequirements()
                                    )

                                if limits:
                                    container.resources.limits = limits
                                if requests:
                                    container.resources.requests = requests

                                if container_name:
                                    break

                        apps_v1.patch_namespaced_deployment(
                            name=resource_name, namespace=namespace, body=deployment
                        )

                        return {
                            "status": "success",
                            "message": f"Updated resources for deployment {resource_name}",
                            "limits": limits,
                            "requests": requests,
                        }

                    return {
                        "error": f"Unsupported resource type for resources update: {resource_type}"
                    }

                except client.exceptions.ApiException as e:
                    return {"error": f"Failed to update resources: {str(e)}"}
                except Exception as e:
                    return {"error": f"Unexpected error updating resources: {str(e)}"}

            if set_type == "env":
                container_name = kwargs.get("container_name", None)
                env_vars = kwargs.get("env", {})

                if not env_vars:
                    return {"error": "env is required for set_type='env'"}

                try:
                    if resource_type.lower() == "deployment":
                        deployment = apps_v1.read_namespaced_deployment(
                            resource_name, namespace
                        )

                        for container in deployment.spec.template.spec.containers:
                            if (
                                container_name is None
                                or container.name == container_name
                            ):
                                if not container.env:
                                    container.env = []

                                # Update or add environment variables
                                for key, value in env_vars.items():
                                    found = False
                                    for env_var in container.env:
                                        if env_var.name == key:
                                            env_var.value = str(value)
                                            found = True
                                            break

                                    if not found:
                                        container.env.append(
                                            client.V1EnvVar(name=key, value=str(value))
                                        )

                                if container_name:
                                    break

                        apps_v1.patch_namespaced_deployment(
                            name=resource_name, namespace=namespace, body=deployment
                        )

                        return {
                            "status": "success",
                            "message": f"Updated environment variables for deployment {resource_name}",
                            "env": env_vars,
                        }

                    return {
                        "error": f"Unsupported resource type for env update: {resource_type}"
                    }

                except client.exceptions.ApiException as e:
                    return {
                        "error": f"Failed to update environment variables: {str(e)}"
                    }
                except Exception as e:
                    return {
                        "error": f"Unexpected error updating environment variables: {str(e)}"
                    }

            return {
                "error": f"Unsupported set_type: {set_type}. Supported types: image, resources, env"
            }

        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}
        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
