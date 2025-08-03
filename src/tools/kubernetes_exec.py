"""Kubernetes exec tool for executing commands in containers."""

from kubernetes import client, config
from kubernetes.stream import stream

from src.base_tool import BaseTool


class KubernetesExecTool(BaseTool):
    """Tool for executing commands inside Kubernetes containers."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()
            v1 = client.CoreV1Api()

            pod_name = kwargs.get("pod_name", "")
            namespace = kwargs.get("namespace", "default")
            container = kwargs.get("container", None)
            command = kwargs.get("command", None)
            stdin = kwargs.get("stdin", "")
            tty = kwargs.get("tty", False)

            if not pod_name:
                return {"error": "pod_name is required"}
            if not command:
                return {"error": "command is required"}

            # Ensure command is a list
            if isinstance(command, str):
                # Simple shell command splitting (doesn't handle quotes properly)
                command = command.split()

            try:
                # Get pod to verify it exists
                pod = v1.read_namespaced_pod(pod_name, namespace)

                # If no container specified and pod has multiple containers, return container list
                if not container and len(pod.spec.containers) > 1:
                    container_names = [c.name for c in pod.spec.containers]
                    return {
                        "error": "Pod has multiple containers, please specify one",
                        "containers": container_names,
                    }

                # Build exec command
                exec_command = command

                # Execute command
                resp = stream(
                    v1.connect_get_namespaced_pod_exec,
                    pod_name,
                    namespace,
                    command=exec_command,
                    container=container,
                    stderr=True,
                    stdin=bool(stdin),
                    stdout=True,
                    tty=tty,
                    _preload_content=False,
                )

                # Send stdin if provided
                if stdin:
                    resp.write_stdin(stdin)

                # Read output
                stdout = ""
                stderr = ""

                while resp.is_open():
                    resp.update(timeout=1)
                    if resp.peek_stdout():
                        stdout += resp.read_stdout()
                    if resp.peek_stderr():
                        stderr += resp.read_stderr()

                resp.close()

                # Get exit code
                exit_code = resp.returncode

                result = {
                    "pod": pod_name,
                    "namespace": namespace,
                    "container": container or pod.spec.containers[0].name,
                    "command": command,
                    "exit_code": exit_code,
                    "stdout": stdout,
                    "stderr": stderr,
                }

                if exit_code != 0:
                    result["status"] = "failed"
                else:
                    result["status"] = "success"

                return result

            except client.exceptions.ApiException as e:
                return {"error": f"Failed to execute command: {str(e)}"}

        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
