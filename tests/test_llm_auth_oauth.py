"""Tests for OAuth Device Flow – all network calls are mocked."""

from __future__ import annotations

from io import StringIO
from unittest.mock import MagicMock

import pytest
import httpx

from rich.console import Console

from singleclaw.llm.auth.oauth_device import DeviceFlow, DeviceFlowConfig
from singleclaw.llm.exceptions import LLMProviderError


def _make_config() -> DeviceFlowConfig:
    return DeviceFlowConfig(
        device_authorization_url="https://example.com/device",
        token_url="https://example.com/token",
        client_id="test-client-id",
        scope="test.scope",
        poll_interval=0,  # no sleep in tests
        timeout=30,
    )


def _make_response(body: dict, status_code: int = 200) -> httpx.Response:
    """Build a minimal httpx.Response mock with JSON body."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.json.return_value = body
    response.raise_for_status = MagicMock()
    return response


class TestDeviceFlow:
    def _silent_console(self) -> Console:
        return Console(file=StringIO(), no_color=True)

    def test_successful_flow_returns_token(self):
        """Full happy-path: device code → pending → access_token."""
        device_response = _make_response({
            "device_code": "dev_code_123",
            "user_code": "ABCD-1234",
            "verification_url": "https://example.com/activate",
            "expires_in": 1800,
            "interval": 0,
        })
        token_response_pending = _make_response(
            {"error": "authorization_pending"}, status_code=400
        )
        token_response_success = _make_response({
            "access_token": "ya29.success",
            "token_type": "Bearer",
            "expires_in": 3600,
        })

        http_client = MagicMock(spec=httpx.Client)
        http_client.post.side_effect = [
            device_response,
            token_response_pending,
            token_response_success,
        ]

        flow = DeviceFlow(
            config=_make_config(),
            console=self._silent_console(),
            http_client=http_client,
        )
        token = flow.run()

        assert token["access_token"] == "ya29.success"

    def test_raises_on_access_denied(self):
        device_response = _make_response({
            "device_code": "dev_code",
            "user_code": "ZZZZ-0000",
            "verification_url": "https://example.com/activate",
            "expires_in": 300,
            "interval": 0,
        })
        denied_response = _make_response({"error": "access_denied"}, status_code=400)

        http_client = MagicMock(spec=httpx.Client)
        http_client.post.side_effect = [device_response, denied_response]

        flow = DeviceFlow(
            config=_make_config(),
            console=self._silent_console(),
            http_client=http_client,
        )
        with pytest.raises(LLMProviderError, match="denied"):
            flow.run()

    def test_raises_on_expired_device_code(self):
        device_response = _make_response({
            "device_code": "dev_code",
            "user_code": "TTTT-9999",
            "verification_url": "https://example.com/activate",
            "expires_in": 300,
            "interval": 0,
        })
        expired_response = _make_response({"error": "expired_token"}, status_code=400)

        http_client = MagicMock(spec=httpx.Client)
        http_client.post.side_effect = [device_response, expired_response]

        flow = DeviceFlow(
            config=_make_config(),
            console=self._silent_console(),
            http_client=http_client,
        )
        with pytest.raises(LLMProviderError, match="expired"):
            flow.run()

    def test_raises_when_device_code_request_fails(self):
        http_client = MagicMock(spec=httpx.Client)
        http_client.post.side_effect = httpx.ConnectError("Connection refused")

        flow = DeviceFlow(
            config=_make_config(),
            console=self._silent_console(),
            http_client=http_client,
        )
        with pytest.raises(LLMProviderError, match="Device code request failed"):
            flow.run()

    def test_slow_down_increases_poll_interval(self):
        """A slow_down error should increase the polling interval."""
        device_response = _make_response({
            "device_code": "dev_code",
            "user_code": "SLOW-1111",
            "verification_url": "https://example.com/activate",
            "expires_in": 300,
            "interval": 0,
        })
        slow_down_response = _make_response({"error": "slow_down"}, status_code=400)
        success_response = _make_response({
            "access_token": "ya29.afterslowdown",
            "token_type": "Bearer",
        })

        http_client = MagicMock(spec=httpx.Client)
        http_client.post.side_effect = [
            device_response,
            slow_down_response,
            success_response,
        ]

        flow = DeviceFlow(
            config=_make_config(),
            console=self._silent_console(),
            http_client=http_client,
        )
        token = flow.run()
        assert token["access_token"] == "ya29.afterslowdown"
