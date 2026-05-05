"""Google Gemini provider – Generative Language API.

Supports both auth modes:
- **API key** (``GEMINI_API_KEY`` env var) – simplest path, recommended for development.
- **OAuth Device Flow** – authenticates as the user's Google account; no API
  key needed.  Requires ``GOOGLE_CLIENT_ID`` and ``GOOGLE_CLIENT_SECRET`` to
  be set (register an OAuth 2.0 app in Google Cloud Console).
"""

from __future__ import annotations

import os
from typing import Any, Iterator

import httpx

from singleclaw.llm.client import LLMResponse
from singleclaw.llm.exceptions import LLMProviderError

_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
_DEFAULT_MODEL = "gemini-1.5-flash"
_GENERATE_PATH = "/models/{model}:generateContent"

# Google OAuth 2.0 Device Flow endpoints.
GOOGLE_DEVICE_AUTH_URL = "https://oauth2.googleapis.com/device/code"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_GEMINI_SCOPE = "https://www.googleapis.com/auth/generative-language"


class GoogleProvider:
    """Calls the Google Gemini Generative Language API.

    Args:
        api_key:     Gemini API key.  Pass ``None`` when using OAuth.
        access_token: OAuth access token.  Pass ``None`` when using an API key.
        model:       Gemini model ID.  Defaults to ``gemini-1.5-flash``.
        http_client: Injectable ``httpx.Client`` for testing.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        access_token: str | None = None,
        model: str | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        if not api_key and not access_token:
            raise ValueError("Either api_key or access_token must be provided.")
        self._api_key = api_key
        self._access_token = access_token
        self._model = model or os.environ.get("GEMINI_MODEL", _DEFAULT_MODEL)
        self._http = http_client

    # ── LLMClient protocol ───────────────────────────────────────────────────

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Send a content-generation request and return the full response."""
        payload = self._build_payload(prompt, system=system, temperature=temperature, max_tokens=max_tokens)
        url = self._build_url()
        body = self._post(url, payload)

        try:
            text = body["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise LLMProviderError(f"Unexpected Gemini response format: {body}") from exc

        usage = body.get("usageMetadata", {})
        return LLMResponse(
            text=text,
            prompt_tokens=usage.get("promptTokenCount", 0),
            completion_tokens=usage.get("candidatesTokenCount", 0),
            model=self._model,
        )

    def stream(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Iterator[str]:
        """Yield response chunks from the Gemini streaming endpoint."""
        import json

        payload = self._build_payload(prompt, system=system, temperature=temperature, max_tokens=max_tokens)
        url = self._build_url(stream=True)
        headers = self._headers()

        try:
            with self._client() as client:
                with client.stream("POST", url, json=payload, headers=headers, timeout=120) as resp:
                    resp.raise_for_status()
                    buffer = ""
                    for chunk in resp.iter_text():
                        buffer += chunk
                        # Gemini streaming returns newline-delimited JSON objects.
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                data = json.loads(line)
                                text = data["candidates"][0]["content"]["parts"][0]["text"]
                                yield text
                            except (KeyError, IndexError, json.JSONDecodeError):
                                pass
        except httpx.HTTPStatusError as exc:
            raise LLMProviderError(
                f"Gemini API error {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"Gemini network error: {exc}") from exc

    # ── internals ────────────────────────────────────────────────────────────

    def _build_url(self, *, stream: bool = False) -> str:
        path = _GENERATE_PATH.format(model=self._model)
        if stream:
            path = path.replace(":generateContent", ":streamGenerateContent")
        url = _GEMINI_BASE_URL + path
        if self._api_key:
            url += f"?key={self._api_key}"
        return url

    def _build_payload(
        self,
        prompt: str,
        *,
        system: str | None,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        return payload

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        return headers

    def _post(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        headers = self._headers()
        try:
            with self._client() as client:
                resp = client.post(url, json=payload, headers=headers, timeout=120)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as exc:
            raise LLMProviderError(
                f"Gemini API error {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"Gemini network error: {exc}") from exc

    def _client(self) -> httpx.Client:
        if self._http is not None:
            return self._http
        return httpx.Client()
