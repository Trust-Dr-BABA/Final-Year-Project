import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test"
)
# No trained model is committed to the repo, so tests exercise the heuristic fallback (ADR-016
# gates it behind this flag in serving deployments, but development/test keeps it on by default).
os.environ.setdefault("ESA_ALLOW_FALLBACK", "1")

# Must come after the os.environ.setdefault() calls above — backend.database reads DATABASE_URL
# at import time.
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend.database import get_db  # noqa: E402
from backend.main import app  # noqa: E402


# Function-scoped TestClient shared by integration test modules that don't need a specific
# get_db override baked into the fixture itself (test_analyze_endpoint.py's module-scoped
# FakeSession variant has genuinely different lifecycle needs and keeps its own fixture).
@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# Override get_db with a stand-in DB object for the duration of a test.
def override_db(mock_db):
    async def get_test_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_test_db


# Patches the four collaborators /analyze calls before persisting, pre-wired to values that
# produce a valid, boring "legitimate" response — every test using this only needs to override
# whichever mock's behavior it actually cares about, instead of repeating the full 4-patch stack
# and restating every return value even when most of them don't matter for what's being tested.
@pytest.fixture
def mock_analyze_pipeline():
    with (
        patch("backend.routers.analyze.extract_url_features") as mock_extract,
        patch("backend.routers.analyze.evaluate") as mock_evaluate,
        patch("backend.routers.analyze.explain_prediction") as mock_explain,
        patch("backend.routers.analyze.get_domain_info", new_callable=AsyncMock) as mock_get_domain_info,
    ):
        mock_get_domain_info.return_value = {
            "domain_age_days": -1, "vt_malicious_votes": -1, "vt_harmless_votes": -1,
        }
        mock_evaluate.return_value = ([], {})
        mock_extract.return_value = {"url_length": 10}
        mock_explain.return_value = {
            "score": 0.05, "risk_pct": 5, "confidence_pct": 95,
            "label": "legitimate", "top_reasons": [],
        }
        yield SimpleNamespace(
            extract=mock_extract,
            evaluate=mock_evaluate,
            explain=mock_explain,
            get_domain_info=mock_get_domain_info,
        )
