"""OpenAI provider – Chat Completions API (API key auth only).

Supports any OpenAI-compatible API endpoint (set ``OPENAI_BASE_URL`` to point
at a proxy or local model server such as LM Studio or vLLM).
"""

from __future__ import annotations

import os
from typing import Any, Iterator

import httpx

from singleclaw.llm.client import LLMResponse
from singleclaw.llm.exceptions import LLMProviderError

_DEFAULT_BASE_URL = "https://api.openai.com/v1"
_DEFAULT_MODEL = "gpt-4o-mini"
_CHAT_PATH = "/chat/completions"


class OpenAIProvider:
    """Calls the OpenAI Chat Completions API.

    Args:
        api_key:  OpenAI API key (``sk-…``).
        model:    Model ID to use.  Defaults to ``gpt-4o-mini``.
        base_url: Base URL for the API.  Override to use a compatible proxy.
        http_client: Injectable ``httpx.Client`` for testing.
    """

    def __init__(
        self,
        api_key: str,
        *,
        model: str | None = None,
        base_url: str | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key must not be empty")
        self._api_key = api_key
        self._model = model or os.environ.get("OPENAI_MODEL", _DEFAULT_MODEL)
        self._base_url = (base_url or os.environ.get("OPENAI_BASE_URL", _DEFAULT_BASE_URL)).rstrip("/")
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
        """Send a chat completion request and return the full response."""
        payload = self._build_payload(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        body = self._post(payload)
        choice = body["choices"][0]["message"]["content"]
        usage = body.get("usage", {})
        return LLMResponse(
            text=choice,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            model=body.get("model", self._model),
        )

    def stream(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Iterator[str]:
        """Yield response chunks using server-sent events streaming."""
        import json

        payload = self._build_payload(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        url = self._base_url + _CHAT_PATH
        headers = self._headers()

        try:
            with self._client() as client:
                with client.stream("POST", url, json=payload, headers=headers, timeout=120) as resp:
                    resp.raise_for_status()
                    for line in resp.iter_lines():
                        if not line or line == "data: [DONE]":
                            continue
                        if line.startswith("data: "):
                            chunk_data = json.loads(line[6:])
                            delta = chunk_data["choices"][0].get("delta", {})
                            if content := delta.get("content"):
                                yield content
        except httpx.HTTPStatusError as exc:
            raise LLMProviderError(
                f"OpenAI API error {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"OpenAI network error: {exc}") from exc

    # ── internals ────────────────────────────────────────────────────────────

    def _build_payload(
        self,
        prompt: str,
        system: str | None,
        temperature: float,
        max_tokens: int,
        stream: bool,
    ) -> dict[str, Any]:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = self._base_url + _CHAT_PATH
        headers = self._headers()
        try:
            with self._client() as client:
                resp = client.post(url, json=payload, headers=headers, timeout=120)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as exc:
            raise LLMProviderError(
                f"OpenAI API error {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"OpenAI network error: {exc}") from exc

    def _client(self) -> httpx.Client:
        if self._http is not None:
            return self._http
        return httpx.Client()
