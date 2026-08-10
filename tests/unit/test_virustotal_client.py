from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.services.virustotal_client import (
    _DEFAULT_VT_DATA,
    _VT_CACHE,
    get_domain_info,
)


class TestVirusTotalClient:
    def setup_method(self):
        _VT_CACHE.clear()

    @pytest.mark.asyncio
    async def test_get_domain_info_returns_defaults_when_no_domain(self):
        result = await get_domain_info("")
        assert result == _DEFAULT_VT_DATA

    @pytest.mark.asyncio
    async def test_get_domain_info_returns_defaults_on_error(self, monkeypatch):
        monkeypatch.setenv("VIRUSTOTAL_API_KEY", "test-key")
        async_mock = AsyncMock()
        async_mock.get.side_effect = Exception("connection failed")

        with patch("backend.services.virustotal_client.httpx.AsyncClient", return_value=async_mock):
            result = await get_domain_info("example.com")

        assert result == _DEFAULT_VT_DATA

    @pytest.mark.asyncio
    async def test_get_domain_info_parses_valid_response(self, monkeypatch):
        monkeypatch.setenv("VIRUSTOTAL_API_KEY", "test-key")
        payload = {
            "data": {
                "attributes": {
                    "creation_date": 1700000000,
                    "last_analysis_stats": {
                        "malicious": 3,
                        "harmless": 23,
                    },
                }
            }
        }

        # httpx.Response methods are sync — only client.get() is async — so this
        # must be a MagicMock, not AsyncMock, or .json() returns an unawaited coroutine.
        response_mock = MagicMock()
        response_mock.raise_for_status.return_value = None
        response_mock.json.return_value = payload

        async_client_mock = AsyncMock()
        async_client_mock.__aenter__.return_value = async_client_mock
        async_client_mock.get.return_value = response_mock

        with patch("backend.services.virustotal_client.httpx.AsyncClient", return_value=async_client_mock):
            result = await get_domain_info("example.com")

        assert result["vt_malicious_votes"] == 3
        assert result["vt_harmless_votes"] == 23
        assert isinstance(result["domain_age_days"], int)

    @pytest.mark.asyncio
    async def test_get_domain_info_uses_cache(self):
        _VT_CACHE["example.com"] = {"domain_age_days": 10, "vt_malicious_votes": 1, "vt_harmless_votes": 2}
        with patch("backend.services.virustotal_client._fetch_domain_info", side_effect=AssertionError("Should not be called")):
            result = await get_domain_info("example.com")
        assert result["domain_age_days"] == 10
        assert result["vt_malicious_votes"] == 1
        assert result["vt_harmless_votes"] == 2
