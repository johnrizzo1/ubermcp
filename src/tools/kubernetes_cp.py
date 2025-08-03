"""Kubernetes copy tool for copying files to and from containers."""

import io
import os
import tarfile

from kubernetes import client, config
from kubernetes.stream import stream

from src.base_tool import BaseTool


class KubernetesCopyTool(BaseTool):
    """Tool for copying files between local system and Kubernetes pods."""

    def execute(self, **kwargs):
        try:
            config.load_kube_config()
            v1 = client.CoreV1Api()

            pod_name = kwargs.get("pod_name", "")
            namespace = kwargs.get("namespace", "default")
            container = kwargs.get("container", None)
            src_path = kwargs.get("src_path", "")
            dst_path = kwargs.get("dst_path", "")
            direction = kwargs.get(
                "direction", "to"
            )  # "to" (local->pod) or "from" (pod->local)

            if not pod_name:
                return {"error": "pod_name is required"}
            if not src_path:
                return {"error": "src_path is required"}
            if not dst_path:
                return {"error": "dst_path is required"}

            # Get pod to verify it exists
            try:
                pod = v1.read_namespaced_pod(pod_name, namespace)

                # If no container specified and pod has multiple containers, return container list
                if not container and len(pod.spec.containers) > 1:
                    container_names = [c.name for c in pod.spec.containers]
                    return {
                        "error": "Pod has multiple containers, please specify one",
                        "containers": container_names,
                    }

                if not container:
                    container = pod.spec.containers[0].name

            except Exception as e:
                return {"error": f"Failed to get pod: {str(e)}"}

            if direction == "to":
                return self._copy_to_pod(
                    v1, pod_name, namespace, container, src_path, dst_path
                )
            if direction == "from":
                return self._copy_from_pod(
                    v1, pod_name, namespace, container, src_path, dst_path
                )
            return {"error": f"Invalid direction: {direction}. Use 'to' or 'from'"}

        except config.ConfigException as e:
            return {"error": f"Kubernetes configuration error: {str(e)}"}

        except ValueError as e:
            return {"error": f"Invalid parameter value: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    def _copy_to_pod(self, api, pod_name, namespace, container, src_path, dst_path):
        """Copy file from local to pod"""
        try:
            # Read local file
            if not os.path.exists(src_path):
                return {"error": f"Source file not found: {src_path}"}

            # Create tar archive in memory
            tar_buffer = io.BytesIO()
            with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
                # Add file to tar with the destination name
                arcname = os.path.basename(dst_path)
                tar.add(src_path, arcname=arcname)

            tar_buffer.seek(0)
            tar_data = tar_buffer.read()

            # Extract directory from destination path
            dst_dir = os.path.dirname(dst_path)
            if not dst_dir:
                dst_dir = "."

            # Create directory in pod if it doesn't exist
            mkdir_command = ["mkdir", "-p", dst_dir]
            resp = stream(
                api.connect_get_namespaced_pod_exec,
                pod_name,
                namespace,
                command=mkdir_command,
                container=container,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False,
            )

            # Extract tar to pod
            extract_command = ["tar", "-xf", "-", "-C", dst_dir]

            resp = stream(
                api.connect_get_namespaced_pod_exec,
                pod_name,
                namespace,
                command=extract_command,
                container=container,
                stderr=True,
                stdin=True,
                stdout=True,
                tty=False,
                _preload_content=False,
            )

            # Send tar data
            resp.write_stdin(tar_data)
            resp.close()

            # Verify file was copied
            verify_command = ["ls", "-la", dst_path]
            resp = stream(
                api.connect_get_namespaced_pod_exec,
                pod_name,
                namespace,
                command=verify_command,
                container=container,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False,
            )

            return {
                "status": "success",
                "message": f"Copied {src_path} to {pod_name}:{dst_path}",
                "source": src_path,
                "destination": f"{pod_name}:{dst_path}",
                "container": container,
                "namespace": namespace,
                "verification": resp,
            }

        except Exception as e:
            return {"error": f"Failed to copy to pod: {str(e)}"}

    def _copy_from_pod(self, api, pod_name, namespace, container, src_path, dst_path):
        """Copy file from pod to local"""
        try:
            # Create tar command to archive the file
            tar_command = ["tar", "-cf", "-", src_path]

            resp = stream(
                api.connect_get_namespaced_pod_exec,
                pod_name,
                namespace,
                command=tar_command,
                container=container,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False,
                _preload_content=False,
            )

            # Read tar data
            tar_buffer = io.BytesIO()
            while resp.is_open():
                resp.update(timeout=1)
                if resp.peek_stdout():
                    data = resp.read_stdout()
                    tar_buffer.write(data.encode() if isinstance(data, str) else data)

            resp.close()

            # Extract tar
            tar_buffer.seek(0)

            try:
                with tarfile.open(fileobj=tar_buffer, mode="r") as tar:
                    # Get the first member (should be our file)
                    members = tar.getmembers()
                    if not members:
                        return {"error": "No files found in pod at specified path"}

                    # Extract to destination
                    member = members[0]

                    # If dst_path is a directory, preserve filename
                    if os.path.isdir(dst_path):
                        final_dst = os.path.join(
                            dst_path, os.path.basename(member.name)
                        )
                    else:
                        final_dst = dst_path

                    # Create destination directory if needed
                    dst_dir = os.path.dirname(final_dst)
                    if dst_dir and not os.path.exists(dst_dir):
                        os.makedirs(dst_dir)

                    # Extract file
                    with open(final_dst, "wb") as f:
                        extracted = tar.extractfile(member)
                        if extracted:
                            f.write(extracted.read())

                    return {
                        "status": "success",
                        "message": f"Copied {pod_name}:{src_path} to {final_dst}",
                        "source": f"{pod_name}:{src_path}",
                        "destination": final_dst,
                        "container": container,
                        "namespace": namespace,
                        "file_size": os.path.getsize(final_dst),
                    }

            except tarfile.ReadError as e:
                # If tar fails, might be because file doesn't exist
                # Try to get the error from stderr
                stderr = ""
                if hasattr(resp, "read_stderr"):
                    stderr = resp.read_stderr()

                if "No such file or directory" in stderr or "cannot stat" in stderr:
                    return {"error": f"File not found in pod: {src_path}"}
                return {"error": f"Failed to read tar data: {str(e)}, stderr: {stderr}"}

        except Exception as e:
            return {"error": f"Failed to copy from pod: {str(e)}"}
