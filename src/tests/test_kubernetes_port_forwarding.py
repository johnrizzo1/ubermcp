"""Tests for Kubernetes Port Forwarding Tool."""

from unittest.mock import MagicMock, patch

import pytest

from src.tools.kubernetes_port_forwarding import KubernetesPortForwardingTool


class TestKubernetesPortForwardingTool:
    """Test cases for Kubernetes Port Forwarding Tool."""

    @pytest.fixture
    def tool(self):
        """Create a port forwarding tool instance."""
        return KubernetesPortForwardingTool("kubernetesportforwarding")

    @pytest.fixture
    def mock_k8s_client(self):
        """Mock kubernetes client."""
        with patch("kubernetes.config.load_incluster_config") as mock_incluster:
            mock_incluster.side_effect = Exception("Not in cluster")
            with patch("kubernetes.config.load_kube_config"):
                with patch("kubernetes.client.CoreV1Api") as mock_api:
                    yield mock_api

    def test_successful_port_forward(self, tool, mock_k8s_client):
        """Test successful port forwarding setup."""
        # Arrange
        mock_pod = MagicMock()
        mock_pod.metadata.name = "test-pod"
        mock_pod.metadata.namespace = "default"
        mock_pod.status.phase = "Running"

        mock_k8s_client.return_value.read_namespaced_pod.return_value = mock_pod

        # Act
        result = tool.execute(
            pod_name="test-pod", namespace="default", local_port=8080, remote_port=80
        )

        # Assert
        assert "error" not in result
        assert result["status"] == "active"
        assert result["pod_name"] == "test-pod"
        assert result["namespace"] == "default"
        assert result["local_port"] == 8080
        assert result["remote_port"] == 80
        assert "forward_id" in result

    def test_invalid_pod_name(self, tool, mock_k8s_client):
        """Test port forwarding with invalid pod name."""
        # Arrange
        from kubernetes.client.rest import (  # pylint: disable=import-outside-toplevel
            ApiException,
        )

        mock_k8s_client.return_value.read_namespaced_pod.side_effect = ApiException(
            status=404, reason="Not Found"
        )

        # Act
        result = tool.execute(
            pod_name="non-existent-pod",
            namespace="default",
            local_port=8080,
            remote_port=80,
        )

        # Assert
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_invalid_namespace(self, tool, mock_k8s_client):
        """Test port forwarding with invalid namespace."""
        # Arrange
        from kubernetes.client.rest import (  # pylint: disable=import-outside-toplevel
            ApiException,
        )

        mock_k8s_client.return_value.read_namespaced_pod.side_effect = ApiException(
            status=404, reason="Not Found"
        )

        # Act
        result = tool.execute(
            pod_name="test-pod",
            namespace="non-existent-ns",
            local_port=8080,
            remote_port=80,
        )

        # Assert
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_pod_not_running(self, tool, mock_k8s_client):
        """Test port forwarding when pod is not in Running state."""
        # Arrange
        mock_pod = MagicMock()
        mock_pod.metadata.name = "test-pod"
        mock_pod.metadata.namespace = "default"
        mock_pod.status.phase = "Pending"

        mock_k8s_client.return_value.read_namespaced_pod.return_value = mock_pod

        # Act
        result = tool.execute(
            pod_name="test-pod", namespace="default", local_port=8080, remote_port=80
        )

        # Assert
        assert "error" in result
        assert "not running" in result["error"].lower()

    def test_port_conflict_scenario(self, tool, mock_k8s_client):
        """Test port forwarding when local port is already in use."""
        # Arrange
        mock_pod = MagicMock()
        mock_pod.metadata.name = "test-pod"
        mock_pod.metadata.namespace = "default"
        mock_pod.status.phase = "Running"

        mock_k8s_client.return_value.read_namespaced_pod.return_value = mock_pod

        # Simulate port already in use by patching the tool's method
        with patch.object(tool, "_is_port_available", return_value=False):
            # Act
            result = tool.execute(
                pod_name="test-pod",
                namespace="default",
                local_port=8080,
                remote_port=80,
            )

            # Assert
            assert "error" in result
            assert "port" in result["error"].lower()
            assert "in use" in result["error"].lower()

    def test_invalid_port_numbers(self, tool):
        """Test port forwarding with invalid port numbers."""
        # Test negative port
        result = tool.execute(
            pod_name="test-pod", namespace="default", local_port=-1, remote_port=80
        )
        assert "error" in result
        assert "invalid" in result["error"].lower()

        # Test port > 65535
        result = tool.execute(
            pod_name="test-pod", namespace="default", local_port=70000, remote_port=80
        )
        assert "error" in result
        assert "invalid" in result["error"].lower()

    def test_missing_required_params(self, tool):
        """Test port forwarding with missing required parameters."""
        # Test missing pod_name
        result = tool.execute(namespace="default", local_port=8080, remote_port=80)
        assert "error" in result
        assert "missing required parameters" in result["error"].lower()

        # Test missing namespace
        result = tool.execute(pod_name="test-pod", local_port=8080, remote_port=80)
        assert "error" in result
        assert "missing required parameters" in result["error"].lower()

    def test_stop_port_forwarding(self, tool, mock_k8s_client):
        """Test stopping an active port forward."""
        # First, set up a port forward
        mock_pod = MagicMock()
        mock_pod.metadata.name = "test-pod"
        mock_pod.metadata.namespace = "default"
        mock_pod.status.phase = "Running"

        mock_k8s_client.return_value.read_namespaced_pod.return_value = mock_pod

        # Start port forwarding
        result = tool.execute(
            pod_name="test-pod", namespace="default", local_port=8080, remote_port=80
        )

        forward_id = result.get("forward_id")
        assert forward_id is not None

        # Stop port forwarding
        stop_result = tool.execute(action="stop", forward_id=forward_id)

        assert stop_result["status"] == "stopped"
        assert stop_result["forward_id"] == forward_id

    def test_list_active_port_forwards(self, tool, mock_k8s_client):
        """Test listing all active port forwards."""
        # Set up multiple port forwards
        mock_pod = MagicMock()
        mock_pod.metadata.name = "test-pod"
        mock_pod.metadata.namespace = "default"
        mock_pod.status.phase = "Running"

        mock_k8s_client.return_value.read_namespaced_pod.return_value = mock_pod

        # Start first port forward
        result1 = tool.execute(
            pod_name="test-pod-1", namespace="default", local_port=8080, remote_port=80
        )

        # Start second port forward
        result2 = tool.execute(
            pod_name="test-pod-2", namespace="default", local_port=8081, remote_port=80
        )

        # List active port forwards
        list_result = tool.execute(action="list")

        assert "forwards" in list_result
        assert len(list_result["forwards"]) >= 2
        assert any(
            f["forward_id"] == result1["forward_id"] for f in list_result["forwards"]
        )
        assert any(
            f["forward_id"] == result2["forward_id"] for f in list_result["forwards"]
        )
