# pylint: disable=redefined-outer-name,no-member
from unittest.mock import patch

import pytest


@pytest.fixture(scope="module")
def mock_kubernetes_config():
    with patch("kubernetes.config.load_kube_config") as mock_load_kube_config:
        yield mock_load_kube_config


@pytest.fixture(scope="module")
def mock_kubernetes_client():
    with patch("kubernetes.client.CoreV1Api") as mock_core_v1_api:
        mock_pod = type("Pod", (object,), {})
        setattr(mock_pod, "metadata", type("Metadata", (object,), {}))
        mock_pod.metadata.name = "test-pod"
        mock_pod.metadata.namespace = "test-namespace"
        setattr(mock_pod, "status", type("Status", (object,), {}))
        mock_pod.status.phase = "Running"
        mock_pod.status.pod_ip = "192.168.1.1"
        setattr(mock_pod, "spec", type("Spec", (object,), {}))
        mock_pod.spec.node_name = "test-node"

        mock_core_v1_api.return_value.list_pod_for_all_namespaces.return_value.items = [
            mock_pod
        ]
        yield mock_core_v1_api


def test_kubernetes_pods_success(api_client):
    response = api_client.post("/tools/kubernetespods")
    assert response.status_code == 200
    assert "pods" in response.json()
    assert len(response.json()["pods"]) > 0
    assert response.json()["pods"][0]["name"] == "test-pod"


def test_kubernetes_pods_tool_error(api_client, mock_kubernetes_client):
    mock_kubernetes_client.return_value.list_pod_for_all_namespaces.side_effect = (
        Exception("Kubernetes API Error")
    )
    response = api_client.post("/tools/kubernetespods")
    assert (
        response.status_code == 200
    )  # FastAPI returns 200 even on tool error, error is in payload
    assert "error" in response.json()
    assert "Kubernetes API Error" in response.json()["error"]
