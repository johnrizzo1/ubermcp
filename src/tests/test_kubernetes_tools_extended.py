# pylint: disable=redefined-outer-name,unused-argument,no-member
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture(scope="session")
def api_client():
    return TestClient(create_app())


@pytest.fixture(scope="module")
def mock_kubernetes_config():
    with patch("kubernetes.config.load_kube_config") as mock_load_kube_config:
        yield mock_load_kube_config


@pytest.fixture(scope="module")
def mock_core_v1_api():
    with patch("kubernetes.client.CoreV1Api") as mock_api:
        yield mock_api


@pytest.fixture(scope="module")
def mock_apps_v1_api():
    with patch("kubernetes.client.AppsV1Api") as mock_api:
        yield mock_api


@pytest.fixture(scope="module")
def mock_networking_v1_api():
    with patch("kubernetes.client.NetworkingV1Api") as mock_api:
        yield mock_api


@pytest.fixture(scope="module")
def mock_batch_v1_api():
    with patch("kubernetes.client.BatchV1Api") as mock_api:
        yield mock_api


def test_kubernetes_events_tool(api_client, mock_kubernetes_config, mock_core_v1_api):
    mock_event = type("Event", (object,), {})
    setattr(mock_event, "metadata", type("Metadata", (object,), {}))
    mock_event.metadata.namespace = "test-namespace"
    mock_event.message = "test-message"
    mock_event.reason = "test-reason"
    mock_event.type = "Normal"
    setattr(mock_event, "involved_object", type("InvolvedObject", (object,), {}))
    mock_event.involved_object.name = "test-object"
    mock_event.involved_object.kind = "Pod"
    mock_event.event_time = None  # Can be None

    mock_core_v1_api.return_value.list_event_for_all_namespaces.return_value.items = [
        mock_event
    ]
    response = api_client.post("/tools/kubernetesevents")
    assert response.status_code == 200
    assert "events" in response.json()
    assert len(response.json()["events"]) > 0
    assert response.json()["events"][0]["message"] == "test-message"


def test_kubernetes_deployments(api_client, mock_kubernetes_config, mock_apps_v1_api):
    mock_deployment = type("Deployment", (object,), {})
    setattr(mock_deployment, "metadata", type("Metadata", (object,), {}))
    mock_deployment.metadata.name = "test-deployment"
    mock_deployment.metadata.namespace = "test-namespace"
    setattr(mock_deployment, "spec", type("Spec", (object,), {}))
    mock_deployment.spec.replicas = 1
    setattr(mock_deployment, "status", type("Status", (object,), {}))
    mock_deployment.status.available_replicas = 1
    mock_deployment.status.ready_replicas = 1

    mock_apps_v1_api.return_value.list_deployment_for_all_namespaces.return_value.items = [
        mock_deployment
    ]
    response = api_client.post("/tools/kubernetesdeployments")
    assert response.status_code == 200
    assert "deployments" in response.json()
    assert len(response.json()["deployments"]) > 0
    assert response.json()["deployments"][0]["name"] == "test-deployment"


def test_kubernetes_services_tool(api_client, mock_kubernetes_config, mock_core_v1_api):
    mock_service = type("Service", (object,), {})
    setattr(mock_service, "metadata", type("Metadata", (object,), {}))
    mock_service.metadata.name = "test-service"
    mock_service.metadata.namespace = "test-namespace"
    setattr(mock_service, "spec", type("Spec", (object,), {}))
    mock_service.spec.cluster_ip = "10.0.0.1"
    mock_service.spec.type = "ClusterIP"
    mock_service.spec.ports = [
        type("Port", (object,), {"name": "http", "port": 80, "protocol": "TCP"})
    ]

    mock_core_v1_api.return_value.list_service_for_all_namespaces.return_value.items = [
        mock_service
    ]
    response = api_client.post("/tools/kubernetesservices")
    assert response.status_code == 200
    assert "services" in response.json()
    assert len(response.json()["services"]) > 0
    assert response.json()["services"][0]["name"] == "test-service"


def test_kubernetes_ingresses_tool(
    api_client, mock_kubernetes_config, mock_networking_v1_api
):
    mock_ingress = type("Ingress", (object,), {})
    setattr(mock_ingress, "metadata", type("Metadata", (object,), {}))
    mock_ingress.metadata.name = "test-ingress"
    mock_ingress.metadata.namespace = "test-namespace"
    setattr(mock_ingress, "spec", type("Spec", (object,), {}))
    mock_ingress.spec.rules = [
        type(
            "Rule",
            (object,),
            {
                "host": "test.example.com",
                "http": type(
                    "HTTP",
                    (object,),
                    {
                        "paths": [
                            type(
                                "Path",
                                (object,),
                                {
                                    "path": "/test",
                                    "path_type": "Prefix",
                                    "backend": type(
                                        "Backend",
                                        (object,),
                                        {
                                            "service": type(
                                                "ServiceBackend",
                                                (object,),
                                                {
                                                    "name": "test-service",
                                                    "port": type(
                                                        "PortSelector",
                                                        (object,),
                                                        {"number": 80},
                                                    ),
                                                },
                                            )
                                        },
                                    ),
                                },
                            )
                        ]
                    },
                ),
            },
        )
    ]

    mock_networking_v1_api.return_value.list_ingress_for_all_namespaces.return_value.items = [
        mock_ingress
    ]
    response = api_client.post("/tools/kubernetesingresses")
    assert response.status_code == 200
    assert "ingresses" in response.json()
    assert len(response.json()["ingresses"]) > 0
    assert response.json()["ingresses"][0]["name"] == "test-ingress"


def test_kubernetes_secrets_tool(api_client, mock_kubernetes_config, mock_core_v1_api):
    mock_secret = type("Secret", (object,), {})
    setattr(mock_secret, "metadata", type("Metadata", (object,), {}))
    mock_secret.metadata.name = "test-secret"
    mock_secret.metadata.namespace = "test-namespace"
    mock_secret.type = "Opaque"
    mock_secret.data = {"key1": "value1_base64"}

    mock_core_v1_api.return_value.list_secret_for_all_namespaces.return_value.items = [
        mock_secret
    ]
    response = api_client.post("/tools/kubernetessecrets")
    assert response.status_code == 200
    assert "secrets" in response.json()
    assert len(response.json()["secrets"]) > 0
    assert response.json()["secrets"][0]["name"] == "test-secret"


def test_kubernetes_pv(api_client, mock_kubernetes_config, mock_core_v1_api):
    mock_pv = type("PersistentVolume", (object,), {})
    setattr(mock_pv, "metadata", type("Metadata", (object,), {}))
    mock_pv.metadata.name = "test-pv"
    setattr(mock_pv, "spec", type("Spec", (object,), {}))
    mock_pv.spec.capacity = {"storage": "1Gi"}
    mock_pv.spec.access_modes = ["ReadWriteOnce"]
    mock_pv.status = type("Status", (object,), {})
    mock_pv.status.phase = "Available"
    mock_pv.spec.claim_ref = None  # Can be None

    mock_core_v1_api.return_value.list_persistent_volume.return_value.items = [mock_pv]
    response = api_client.post("/tools/kubernetespersistentvolumes")
    assert response.status_code == 200
    assert "persistent_volumes" in response.json()
    assert len(response.json()["persistent_volumes"]) > 0
    assert response.json()["persistent_volumes"][0]["name"] == "test-pv"


def test_kubernetes_jobs_tool(api_client, mock_kubernetes_config, mock_batch_v1_api):
    mock_job = type("Job", (object,), {})
    setattr(mock_job, "metadata", type("Metadata", (object,), {}))
    mock_job.metadata.name = "test-job"
    mock_job.metadata.namespace = "test-namespace"
    setattr(mock_job, "spec", type("Spec", (object,), {}))
    mock_job.spec.completions = 1
    setattr(mock_job, "status", type("Status", (object,), {}))
    mock_job.status.succeeded = 1
    mock_job.status.failed = None

    mock_batch_v1_api.return_value.list_job_for_all_namespaces.return_value.items = [
        mock_job
    ]
    response = api_client.post("/tools/kubernetesjobs")
    assert response.status_code == 200
    assert "jobs" in response.json()
    assert len(response.json()["jobs"]) > 0
    assert response.json()["jobs"][0]["name"] == "test-job"


def test_kubernetes_cron_jobs_tool(
    api_client, mock_kubernetes_config, mock_batch_v1_api
):
    mock_cron_job = type("CronJob", (object,), {})
    setattr(mock_cron_job, "metadata", type("Metadata", (object,), {}))
    mock_cron_job.metadata.name = "test-cronjob"
    mock_cron_job.metadata.namespace = "test-namespace"
    setattr(mock_cron_job, "spec", type("Spec", (object,), {}))
    mock_cron_job.spec.schedule = "0 0 * * *"
    mock_cron_job.spec.suspend = False
    setattr(mock_cron_job, "status", type("Status", (object,), {}))
    mock_cron_job.status.last_schedule_time = None

    mock_batch_v1_api.return_value.list_cron_job_for_all_namespaces.return_value.items = [
        mock_cron_job
    ]
    response = api_client.post("/tools/kubernetescronjobs")
    assert response.status_code == 200
    assert "cron_jobs" in response.json()
    assert len(response.json()["cron_jobs"]) > 0
    assert response.json()["cron_jobs"][0]["name"] == "test-cronjob"


def test_kubernetes_routes_tool(api_client, mock_kubernetes_config):
    response = api_client.post("/tools/kubernetesroutes")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "placeholder" in response.json()["message"].lower()


def test_kubernetes_port_forward(api_client, mock_kubernetes_config):
    response = api_client.post("/tools/kubernetesportforwarding")
    assert response.status_code == 200
    assert "error" in response.json()
    assert "missing required parameters" in response.json()["error"].lower()
