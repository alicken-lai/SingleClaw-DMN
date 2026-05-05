"""OAuth 2.0 Device Authorization Grant (RFC 8628) flow implementation.

This module orchestrates the Device Flow for providers that support it
(currently: Google).  It requires no redirect URI, making it ideal for CLI
tools that run in a terminal.

Typical usage::

    flow = DeviceFlow(provider_config=GoogleDeviceFlowConfig())
    token = flow.run()   # opens browser, polls until authorised or timed out
"""

from __future__ import annotations

import time
import webbrowser
from dataclasses import dataclass
from typing import Any, Optional

import httpx
from rich.console import Console

from singleclaw.llm.exceptions import LLMProviderError

_console = Console()

# Default polling / timeout constants (can be overridden per-provider).
_DEFAULT_POLL_INTERVAL = 5   # seconds between token polls
_DEFAULT_TIMEOUT = 300       # 5 minutes total wait
_DEFAULT_SLOW_DOWN_STEP = 5  # extra seconds to add when server returns slow_down


@dataclass
class DeviceFlowConfig:
    """Configuration for one OAuth 2.0 Device Flow provider.

    Args:
        device_authorization_url: Endpoint that issues device and user codes.
        token_url:                Endpoint to poll for the access token.
        client_id:                Registered OAuth 2.0 client ID.
        scope:                    Space-separated OAuth scopes to request.
        poll_interval:            Initial polling interval in seconds.
        timeout:                  Maximum seconds to wait for user authorisation.
    """

    device_authorization_url: str
    token_url: str
    client_id: str
    scope: str
    poll_interval: int = _DEFAULT_POLL_INTERVAL
    timeout: int = _DEFAULT_TIMEOUT


class DeviceFlow:
    """Execute an OAuth 2.0 Device Authorization Grant flow.

    Args:
        config:  Provider-specific :class:`DeviceFlowConfig`.
        console: Rich console for user-facing output (injectable for tests).
    """

    def __init__(
        self,
        config: DeviceFlowConfig,
        *,
        console: Optional[Console] = None,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        self._config = config
        self._console = console or _console
        self._http = http_client  # None → created per-request (real network calls)

    # ── public ───────────────────────────────────────────────────────────────

    def run(self) -> dict[str, Any]:
        """Execute the full Device Flow and return the token response dict.

        Returns:
            A dict containing at minimum ``access_token`` and ``token_type``.
            May also contain ``refresh_token``, ``expires_in``, ``scope``.

        Raises:
            LLMProviderError: on network errors, device code rejection, or timeout.
        """
        device_resp = self._request_device_code()
        device_code = device_resp["device_code"]
        user_code = device_resp["user_code"]
        verification_uri = device_resp.get("verification_url") or device_resp.get("verification_uri", "")
        expires_in = int(device_resp.get("expires_in", self._config.timeout))
        interval = int(device_resp.get("interval", self._config.poll_interval))

        self._display_instructions(verification_uri, user_code)

        deadline = time.monotonic() + min(expires_in, self._config.timeout)

        while time.monotonic() < deadline:
            time.sleep(interval)
            result = self._poll_token(device_code)

            if result is None:
                continue  # authorisation_pending

            if "access_token" in result:
                self._console.print(
                    "[bold green]✔ Authentication successful.[/bold green]"
                )
                return result

            error = result.get("error", "")
            if error == "slow_down":
                interval += _DEFAULT_SLOW_DOWN_STEP
            elif error == "access_denied":
                raise LLMProviderError("User denied access.")
            elif error == "expired_token":
                raise LLMProviderError(
                    "Device code expired. Run [bold]singleclaw auth login[/bold] again."
                )
            # Other errors: keep polling until timeout.

        raise LLMProviderError(
            "Timed out waiting for authorisation. "
            "Run [bold]singleclaw auth login[/bold] again."
        )

    # ── private ──────────────────────────────────────────────────────────────

    def _request_device_code(self) -> dict[str, Any]:
        """POST to the device-authorization endpoint."""
        data = {"client_id": self._config.client_id, "scope": self._config.scope}
        try:
            resp = self._post(self._config.device_authorization_url, data=data)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"Device code request failed: {exc}") from exc

    def _poll_token(self, device_code: str) -> Optional[dict[str, Any]]:
        """Poll the token endpoint.  Returns ``None`` on ``authorization_pending``."""
        data = {
            "client_id": self._config.client_id,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        }
        try:
            resp = self._post(self._config.token_url, data=data)
            body = resp.json()
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"Token poll failed: {exc}") from exc

        if resp.status_code == 200 and "access_token" in body:
            return body

        error = body.get("error", "")
        if error == "authorization_pending":
            return None  # still waiting

        return body  # slow_down, access_denied, expired_token, etc.

    def _display_instructions(self, verification_uri: str, user_code: str) -> None:
        """Display Device Flow instructions via Rich and open the browser."""
        self._console.print()
        self._console.rule("[bold cyan]Browser Authentication Required[/bold cyan]")
        self._console.print(
            f"\n[bold]1.[/bold] Visit: [underline cyan]{verification_uri}[/underline cyan]"
        )
        self._console.print(
            f"[bold]2.[/bold] Enter code: [bold yellow]{user_code}[/bold yellow]\n"
        )
        self._console.print("[dim]Attempting to open your browser…[/dim]")
        try:
            webbrowser.open(verification_uri)
        except Exception:  # noqa: BLE001
            pass  # If the browser can't be opened, the user can visit manually.
        self._console.print("[dim]Waiting for you to authorise in the browser…[/dim]\n")

    def _post(self, url: str, data: dict) -> httpx.Response:
        """Make a POST request, reusing the injected client if provided."""
        if self._http is not None:
            return self._http.post(url, data=data)
        with httpx.Client(timeout=30) as client:
            return client.post(url, data=data)
