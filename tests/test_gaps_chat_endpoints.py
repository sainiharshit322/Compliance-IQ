from fastapi.testclient import TestClient
from services.orchestrator_api.main import app

client = TestClient(app)


def test_list_gaps_endpoint():
    response = client.get("/api/v1/gaps")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["data"]) >= 1
    assert "risk_score" in data["data"][0]
    assert "advisory_remediation" in data["data"][0]


def test_list_gaps_with_status_filter():
    response = client.get("/api/v1/gaps?compliance_status=NON_COMPLIANT")
    assert response.status_code == 200
    data = response.json()
    for gap in data["data"]:
        assert gap["compliance_status"] == "NON_COMPLIANT"


def test_list_gaps_with_min_risk_score_filter():
    response = client.get("/api/v1/gaps?min_risk_score=7.0")
    assert response.status_code == 200
    data = response.json()
    for gap in data["data"]:
        assert gap["risk_score"] >= 7.0


def test_chat_json_mode_endpoint():
    payload = {
        "prompt": "What are the human oversight requirements under Article 14 of the EU AI Act?",
        "framework_code": "EU_AI_ACT",
        "stream": False,
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "confidence_score" in data
    assert "citations" in data
    assert len(data["citations"]) >= 1


def test_chat_guardrail_3_ungrounded_query():
    payload = {
        "prompt": "What is the recipes for cooking pizza?",
        "stream": False,
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Insufficient regulatory context retrieved" in data["answer"]


def test_chat_sse_streaming_mode_endpoint():
    payload = {
        "prompt": "What are the infrastructure encryption requirements for SOC 2 CC6.1?",
        "framework_code": "SOC2_TYPE2",
        "stream": True,
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    lines = response.text.split("\n\n")
    assert len(lines) > 1
    assert "data:" in lines[0]
