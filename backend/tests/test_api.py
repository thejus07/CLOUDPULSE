"""
Integration tests for CloudPulse REST API endpoints
"""

import pytest
import json
from backend.app.main import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_api_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "HEALTHY"


def test_api_servers_crud(client):
    # Register server
    payload = {
        "id": "srv-api-test-01",
        "hostname": "api-test.cloudpulse.internal",
        "os_name": "Linux",
        "cpu_cores": 4,
        "total_memory_mb": 8192.0,
        "total_disk_gb": 100.0
    }
    res = client.post("/api/servers", json=payload)
    assert res.status_code in (200, 201)

    # List servers
    list_res = client.get("/api/servers")
    assert list_res.status_code == 200
    servers = list_res.get_json()
    assert any(s["id"] == "srv-api-test-01" for s in servers)

    # Get single server
    get_res = client.get("/api/servers/srv-api-test-01")
    assert get_res.status_code == 200
    assert get_res.get_json()["hostname"] == "api-test.cloudpulse.internal"


def test_api_metrics_ingestion_and_query(client):
    metric_payload = {
        "server_id": "srv-api-test-01",
        "cpu_percent": 35.0,
        "load_1m": 0.5,
        "load_5m": 0.4,
        "load_15m": 0.3,
        "memory_percent": 55.0,
        "memory_used_mb": 4500.0,
        "memory_available_mb": 3692.0,
        "disk_percent": 40.0,
        "disk_used_gb": 40.0,
        "disk_available_gb": 60.0
    }
    ingest_res = client.post("/api/metrics", json=metric_payload)
    assert ingest_res.status_code == 201

    get_metrics_res = client.get("/api/metrics?server_id=srv-api-test-01&limit=5")
    assert get_metrics_res.status_code == 200
    metrics = get_metrics_res.get_json()
    assert len(metrics) >= 1
    assert metrics[-1]["cpu_percent"] == 35.0


def test_api_diagnostics_run(client):
    res = client.post("/api/diagnostics/run", json={
        "diagnostic_type": "CPU",
        "server_id": "srv-api-test-01"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["diagnostic_type"] == "CPU"
    assert "findings" in data


def test_api_reports_summary(client):
    res = client.get("/api/reports/summary")
    assert res.status_code == 200
    summary = res.get_json()
    assert "fleet" in summary
    assert "incidents" in summary
    assert "total_servers" in summary["fleet"]


def test_api_reports_export_json(client):
    res = client.get("/api/reports/export?format=json")
    assert res.status_code == 200
    assert res.content_type == "application/json"


def test_api_reports_export_csv(client):
    res = client.get("/api/reports/export?format=csv")
    assert res.status_code == 200
    assert "text/csv" in res.content_type
