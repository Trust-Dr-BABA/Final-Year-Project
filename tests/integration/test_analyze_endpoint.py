import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.database import get_db
from backend.main import app


@pytest.fixture(scope="module")
def client():
    class TestSession:
        def add(self, scan):
            scan.id = uuid.uuid4()

        async def commit(self):
            pass

        async def refresh(self, scan):
            pass

    async def get_test_db():
        yield TestSession()

    app.dependency_overrides[get_db] = get_test_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@patch("backend.routers.analyze.get_domain_info", new_callable=AsyncMock)
@patch("backend.routers.analyze.explain_prediction")
@patch("backend.routers.analyze.evaluate")
@patch("backend.routers.analyze.extract_url_features")
def test_analyze_endpoint_returns_valid_schema(
    mock_extract,
    mock_evaluate,
    mock_explain,
    mock_get_domain_info,
    client,
):
    mock_get_domain_info.return_value = {
        "domain_age_days": 10,
        "vt_malicious_votes": 0,
        "vt_harmless_votes": 10,
    }

    mock_evaluate.return_value = ([], {})
    mock_extract.return_value = {
        "url_length": 10,
        "num_digits": 1,
        "num_special_chars": 0,
        "subdomain_depth": 0,
        "has_https": 1,
        "url_entropy": 3.5,
        "has_ip_address": 0,
        "suspicious_tld_flag": 0,
        "brand_impersonation": 0,
        "domain_age_days": 10,
        "vt_malicious_votes": 0,
        "vt_harmless_votes": 10,
    }
    mock_explain.return_value = {
        "score": 0.05,
        "risk_pct": 5,
        "confidence_pct": 95,  # ADR-015: max(p, 1-p) * 100, not the same quantity as risk_pct
        "label": "legitimate",
        "top_reasons": [],
    }

    response = client.post("/analyze", json={"url": "https://example.com"})
    assert response.status_code == 200
    body = response.json()
    assert "scan_id" in body
    assert body["verdict"] == "legitimate"
    assert body["risk_pct"] == 5
    assert body["confidence_pct"] == 95
    assert isinstance(body["top_reasons"], list)
    assert isinstance(body["flagged_rules"], list)
