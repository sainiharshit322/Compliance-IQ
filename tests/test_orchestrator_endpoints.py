from fastapi.testclient import TestClient
from services.orchestrator_api.main import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["service"] == "orchestrator_api"


def test_list_frameworks_endpoint():
    response = client.get("/api/v1/frameworks")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["data"]) == 5
    codes = [f["code"] for f in data["data"]]
    assert "SOC2_TYPE2" in codes
    assert "EU_AI_ACT" in codes


def test_list_frameworks_with_filter():
    response = client.get("/api/v1/frameworks?code=SOC2_TYPE2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["data"][0]["code"] == "SOC2_TYPE2"


def test_trigger_scan_endpoint():
    payload = {
        "framework_code": "SOC2_TYPE2",
        "collector_type": "AZURE_POLICY",
        "target_resource_id": "/subscriptions/000/resourceGroups/rg-prod/providers/Microsoft.Storage/storageAccounts/stprod01",
        "force_recollect": True,
    }
    response = client.post("/api/v1/scan", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "ENQUEUED"
    assert data["queue_name"] == "evidence-jobs"
    assert "job_id" in data
    assert "enqueued_at" in data


def test_get_control_evidence_endpoint():
    control_id = "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
    response = client.get(f"/api/v1/controls/{control_id}/evidence")
    assert response.status_code == 200
    data = response.json()
    assert data["control_id"] == control_id
    assert data["evidence_count"] >= 1
    assert len(data["evidence_logs"]) >= 1

    first_log = data["evidence_logs"][0]
    assert "sha256_hash" in first_log
    assert "blob_uri" in first_log
    assert first_log["control_id"] == control_id


def test_get_control_evidence_with_status_filter():
    control_id = "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
    response = client.get(f"/api/v1/controls/{control_id}/evidence?status=PENDING_REVIEW")
    assert response.status_code == 200
    data = response.json()
    for log in data["evidence_logs"]:
        assert log["status"] == "PENDING_REVIEW"
