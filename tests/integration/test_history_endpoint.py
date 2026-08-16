import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from backend.models.scan import Scan
from tests.conftest import override_db as _override_db


def test_history_without_client_id_returns_empty_and_skips_db(client):
    mock_db = AsyncMock()
    _override_db(mock_db)

    response = client.get("/history")

    assert response.status_code == 200
    assert response.json() == {"scans": [], "total": 0, "limit": 50, "offset": 0}
    mock_db.execute.assert_not_awaited()
    mock_db.scalar.assert_not_awaited()


def test_stats_without_client_id_returns_zeroed_defaults_and_skips_db(client):
    mock_db = AsyncMock()
    _override_db(mock_db)

    response = client.get("/stats")

    assert response.status_code == 200
    assert response.json() == {
        "total_scans": 0,
        "phishing_count": 0,
        "suspicious_count": 0,
        "legitimate_count": 0,
        "avg_confidence_pct": 0,
    }
    mock_db.execute.assert_not_awaited()


def test_history_with_client_id_scopes_the_query_to_that_client(client):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result
    mock_db.scalar.return_value = 0
    _override_db(mock_db)

    response = client.get("/history", params={"client_id": "abc-123"})

    assert response.status_code == 200
    executed_stmt = mock_db.execute.await_args.args[0]
    assert "client_id" in str(executed_stmt)


def test_stats_with_client_id_scopes_the_query_to_that_client(client):
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result
    mock_db.scalar.return_value = 0
    _override_db(mock_db)

    response = client.get("/stats", params={"client_id": "abc-123"})

    assert response.status_code == 200
    executed_stmt = mock_db.execute.await_args.args[0]
    assert "client_id" in str(executed_stmt)


def test_get_scan_requires_client_id(client):
    # No client_id at all — FastAPI/Pydantic rejects it before the handler runs.
    mock_db = AsyncMock()
    _override_db(mock_db)

    response = client.get(f"/scan/{uuid.uuid4()}")

    assert response.status_code == 422
    mock_db.get.assert_not_awaited()


def test_get_scan_404s_when_client_id_does_not_own_the_scan(client):
    # A real scan exists, but the caller's client_id doesn't match it — must 404, not return the
    # record. This is the core IDOR regression test: previously this endpoint had no ownership
    # check at all and would return the scan regardless of who asked.
    scan_id = uuid.uuid4()
    scan = Scan(
        id=scan_id,
        client_id="owner-client",
        url="https://example.com/",
        verdict="legitimate",
        risk_score=0.1,
        risk_pct=10,
        confidence_pct=90,
    )
    mock_db = AsyncMock()
    mock_db.get.return_value = scan
    _override_db(mock_db)

    response = client.get(f"/scan/{scan_id}", params={"client_id": "attacker-client"})

    assert response.status_code == 404


def test_get_scan_returns_the_scan_when_client_id_matches(client):
    scan_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    scan = Scan(
        id=scan_id,
        client_id="owner-client",
        url="https://example.com/",
        verdict="legitimate",
        risk_score=0.1,
        risk_pct=10,
        confidence_pct=90,
        created_at=now,
        last_scanned_at=now,
    )
    mock_db = AsyncMock()
    mock_db.get.return_value = scan
    _override_db(mock_db)

    response = client.get(f"/scan/{scan_id}", params={"client_id": "owner-client"})

    assert response.status_code == 200
    body = response.json()
    assert body["scan_id"] == str(scan_id)
    # client_id is deliberately never in the public response — a leaked scan_id must not be able
    # to pivot into full-history access via /history.
    assert "client_id" not in body


def test_get_scan_invalid_uuid_returns_400(client):
    mock_db = AsyncMock()
    _override_db(mock_db)

    response = client.get("/scan/not-a-uuid", params={"client_id": "owner-client"})

    assert response.status_code == 400
