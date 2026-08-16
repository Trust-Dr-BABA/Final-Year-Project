"""
test_rate_limiting.py — Regression test for /analyze's slowapi rate limit.
Resets the shared Limiter's storage before and after so this doesn't consume budget other test
modules rely on — the Limiter instance (backend/rate_limit.py) is a process-wide singleton, so
without an explicit reset its in-memory counters would otherwise leak across test files.
"""

from unittest.mock import AsyncMock

import pytest

from backend.rate_limit import limiter
from tests.conftest import override_db


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    limiter.reset()
    yield
    limiter.reset()


def test_analyze_returns_429_after_ten_requests_per_minute(client, mock_analyze_pipeline):
    override_db(AsyncMock())

    for _ in range(10):
        response = client.post("/analyze", json={"url": "https://example.com"})
        assert response.status_code == 200

    eleventh = client.post("/analyze", json={"url": "https://example.com"})
    assert eleventh.status_code == 429
