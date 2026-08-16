import uuid

import pytest
from fastapi.testclient import TestClient

from backend.database import get_db
from backend.main import app
from backend.models.scan import Scan


class FakeSession:
    """Stands in for the real DB session. existing_scan controls what the upsert lookup
    (db.scalar(select(Scan)...)) returns — None simulates "no prior scan for this
    (client_id, url)" (insert path), a real Scan instance simulates a match (update path)."""

    def __init__(self):
        self.existing_scan = None
        self.added: list = []

    async def scalar(self, stmt):
        return self.existing_scan

    def add(self, scan):
        self.added.append(scan)
        scan.id = uuid.uuid4()

    async def commit(self):
        pass

    async def refresh(self, scan):
        pass


@pytest.fixture(scope="module")
def db_session():
    return FakeSession()


@pytest.fixture(scope="module")
def client(db_session):
    async def get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = get_test_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_analyze_endpoint_returns_valid_schema(client, mock_analyze_pipeline):
    # extract_url_features's return is the only thing this test needs different from
    # mock_analyze_pipeline's defaults — a fuller feature dict, to exercise real-shaped output.
    mock_analyze_pipeline.extract.return_value = {
        "url_length": 10,
        "digit_ratio": 0.1,
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

    response = client.post("/analyze", json={"url": "https://example.com"})
    assert response.status_code == 200
    body = response.json()
    assert "scan_id" in body
    assert body["verdict"] == "legitimate"
    assert body["risk_pct"] == 5
    assert body["confidence_pct"] == 95
    assert isinstance(body["top_reasons"], list)
    assert isinstance(body["flagged_rules"], list)

    # extract_url_features() must be called with the fetched vt_data — the whole point of fetching
    # VT synchronously is so its vt_malicious_votes reaches fusion for this same response.
    mock_analyze_pipeline.extract.assert_called_once_with(
        "https://example.com/", vt_data=mock_analyze_pipeline.get_domain_info.return_value
    )


def test_rescanning_a_known_url_updates_the_existing_row(client, db_session, mock_analyze_pipeline):
    # Only explain_prediction's return differs from mock_analyze_pipeline's defaults here — this
    # scan resolves to "phishing", not the default "legitimate".
    mock_analyze_pipeline.explain.return_value = {
        "score": 0.9, "risk_pct": 90, "confidence_pct": 90,
        "label": "phishing", "top_reasons": [],
    }

    existing_id = uuid.uuid4()
    db_session.existing_scan = Scan(
        id=existing_id,
        client_id="client-a",
        url="https://example.com/",
        verdict="legitimate",
        risk_score=0.1,
        risk_pct=10,
        confidence_pct=90,
    )
    db_session.added = []
    try:
        response = client.post(
            "/analyze", json={"url": "https://example.com/", "client_id": "client-a"}
        )
        assert response.status_code == 200
        body = response.json()

        # Same scan_id as the pre-existing row — proves this updated it in place rather than
        # inserting a new one.
        assert body["scan_id"] == str(existing_id)
        assert body["verdict"] == "phishing"  # the fresh analysis, not the stale existing value
        assert db_session.added == []  # no new row was added
    finally:
        db_session.existing_scan = None
        db_session.added = []


def test_scanning_a_new_url_with_a_client_id_still_inserts(client, db_session, mock_analyze_pipeline):
    # mock_analyze_pipeline's defaults are exactly what this test needs — no overrides.
    db_session.existing_scan = None  # no prior scan for this (client_id, url)
    db_session.added = []
    try:
        response = client.post(
            "/analyze", json={"url": "https://never-seen-before.example/", "client_id": "client-b"}
        )
        assert response.status_code == 200
        assert len(db_session.added) == 1
        assert response.json()["scan_id"] == str(db_session.added[0].id)
    finally:
        db_session.added = []
