"""Kubernetes Port Forwarding Tool.

This tool provides functionality to manage port forwarding sessions to Kubernetes pods.
It supports starting, stopping, and listing active port forwarding sessions.

Usage:
    # Start a port forward
    POST /tools/kubernetesportforwarding
    {
        "pod_name": "my-pod",
        "namespace": "default",
        "local_port": 8080,
        "remote_port": 80
    }

    # Stop a port forward
    POST /tools/kubernetesportforwarding
    {
        "action": "stop",
        "forward_id": "uuid-here"
    }

    # List active port forwards
    POST /tools/kubernetesportforwarding
    {
        "action": "list"
    }

Limitations:
    - This implementation manages port forward metadata only
    - Actual TCP tunneling is not implemented (would require websockets/streaming)
    - Port forwards are stored in memory and lost on server restart
    - No automatic cleanup of stale port forwards
    - Single instance only (not distributed)

Note: For production use, consider using kubectl port-forward directly or
implementing proper TCP tunneling with websockets for real port forwarding.
"""

import socket
import threading
import uuid
from typing import Any, Callable, Dict, Optional

import kubernetes
from kubernetes.client.rest import ApiException

from src.base_tool import BaseTool


class KubernetesPortForwardingTool(BaseTool):
    """Tool for managing Kubernetes port forwarding."""

    def __init__(self, name: str):
        """Initialize the port forwarding tool."""
        super().__init__(name)
        self._active_forwards: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def _load_k8s_config(self):
        """Load Kubernetes configuration."""
        try:
            kubernetes.config.load_incluster_config()
        except Exception:
            kubernetes.config.load_kube_config()

    def _validate_port(self, port: int) -> bool:
        """Validate port number."""
        return 1 <= port <= 65535

    def _is_port_available(self, port: int) -> bool:
        """Check if a local port is available."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return True
        except OSError:
            return False

    def _start_port_forward(
        self, pod_name: str, namespace: str, local_port: int, remote_port: int
    ) -> Dict[str, Any]:
        """Start a port forward to a pod."""
        # Validate ports first before making any API calls
        if not self._validate_port(local_port):
            return {
                "error": f"Invalid local port: {local_port}. Must be between 1 and 65535"
            }
        if not self._validate_port(remote_port):
            return {
                "error": f"Invalid remote port: {remote_port}. Must be between 1 and 65535"
            }

        # Check if local port is available
        if not self._is_port_available(local_port):
            return {"error": f"Local port {local_port} is already in use"}

        self._load_k8s_config()
        v1 = kubernetes.client.CoreV1Api()

        # Check if pod exists and is running
        try:
            pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            if pod.status.phase != "Running":
                return {
                    "error": f"Pod '{pod_name}' is not running (status: {pod.status.phase})"
                }
        except ApiException as e:
            if e.status == 404:
                return {
                    "error": f"Pod '{pod_name}' not found in namespace '{namespace}'"
                }
            raise

        # Generate forward ID
        forward_id = str(uuid.uuid4())

        # Store forward info
        with self._lock:
            self._active_forwards[forward_id] = {
                "pod_name": pod_name,
                "namespace": namespace,
                "local_port": local_port,
                "remote_port": remote_port,
                "status": "active",
            }

        return {
            "status": "active",
            "forward_id": forward_id,
            "pod_name": pod_name,
            "namespace": namespace,
            "local_port": local_port,
            "remote_port": remote_port,
        }

    def _stop_port_forward(self, forward_id: str) -> Dict[str, Any]:
        """Stop an active port forward."""
        with self._lock:
            if forward_id not in self._active_forwards:
                return {"error": f"Forward ID '{forward_id}' not found"}

            forward_info = self._active_forwards[forward_id]
            forward_info["status"] = "stopped"
            del self._active_forwards[forward_id]

        return {"status": "stopped", "forward_id": forward_id}

    def _list_port_forwards(self) -> Dict[str, Any]:
        """List all active port forwards."""
        with self._lock:
            forwards = [
                {"forward_id": fid, **info}
                for fid, info in self._active_forwards.items()
            ]

        return {"forwards": forwards}

    def _handle_start_action(self, **kwargs) -> Dict[str, Any]:
        """Handle the start action."""
        pod_name = kwargs.get("pod_name")
        namespace = kwargs.get("namespace")
        local_port = kwargs.get("local_port")
        remote_port = kwargs.get("remote_port")

        if not all([pod_name, namespace, local_port, remote_port]):
            return {
                "error": (
                    "Missing required parameters. Need: pod_name, "
                    "namespace, local_port, remote_port"
                )
            }

        # Type validation
        if not isinstance(pod_name, str) or not isinstance(namespace, str):
            return {"error": "pod_name and namespace must be strings"}

        if local_port is None or remote_port is None:
            return {"error": "local_port and remote_port must not be None"}

        try:
            local_port_int = int(local_port)
            remote_port_int = int(remote_port)
        except (TypeError, ValueError):
            return {"error": "local_port and remote_port must be integers"}

        return self._start_port_forward(
            pod_name, namespace, local_port_int, remote_port_int
        )

    def _handle_stop_action(self, **kwargs) -> Dict[str, Any]:
        """Handle the stop action."""
        forward_id = kwargs.get("forward_id")
        if not forward_id:
            return {"error": "Missing required parameter: forward_id"}
        return self._stop_port_forward(forward_id)

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute port forwarding operations."""
        action = kwargs.get("action", "start")

        action_handlers: Dict[str, Callable[..., Dict[str, Any]]] = {
            "start": self._handle_start_action,
            "stop": self._handle_stop_action,
            "list": self._list_port_forwards,
        }

        handler: Optional[Callable[..., Dict[str, Any]]] = action_handlers.get(action)
        if handler:
            return handler(**kwargs)

        return {"error": f"Unknown action: {action}. Valid actions: start, stop, list"}
