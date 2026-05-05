"""LLM configuration – auth mode detection and provider selection.

``LLMConfig`` reads environment variables (and the optional ``.env`` file) to
determine which auth mode and provider are active, without making any network
calls.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

# Load .env file if python-dotenv is available and .env exists.
try:
    from dotenv import load_dotenv as _load_dotenv

    _load_dotenv(dotenv_path=Path(".env"), override=False)
except ImportError:  # pragma: no cover – dotenv is optional
    pass


class AuthMode(str, Enum):
    """Authentication mode for LLM provider access."""

    API_KEY = "api_key"
    OAUTH = "oauth"


class Provider(str, Enum):
    """Supported LLM provider identifiers."""

    OPENAI = "openai"
    GOOGLE = "google"
    OLLAMA = "ollama"


# Environment variable names checked for API keys (in priority order per provider).
_API_KEY_ENV: dict[str, str] = {
    Provider.OPENAI: "OPENAI_API_KEY",
    Provider.GOOGLE: "GEMINI_API_KEY",
}

# Default provider used when SINGLECLAW_LLM_PROVIDER is not set.
_DEFAULT_PROVIDER = Provider.OPENAI


@dataclass
class LLMConfig:
    """Resolved LLM configuration.

    Use :meth:`resolve` to build an instance from the current environment.

    Args:
        auth_mode:   Detected authentication mode.
        provider:    Active LLM provider.
        api_key:     API key string (non-empty only for ``API_KEY`` mode).
        token_path:  Path to the OAuth token file (only for ``OAUTH`` mode).
    """

    auth_mode: AuthMode
    provider: Provider
    api_key: str = field(default="", repr=False)
    token_path: Optional[Path] = field(default=None)

    # ── factory ──────────────────────────────────────────────────────────────

    @classmethod
    def resolve(
        cls,
        workspace_dir: Optional[Path] = None,
    ) -> "LLMConfig":
        """Build a :class:`LLMConfig` from the current environment.

        Detection priority:
        1. API key env var set → :attr:`AuthMode.API_KEY`
        2. Stored OAuth token present & unexpired → :attr:`AuthMode.OAUTH`
        3. Neither → raises :class:`~singleclaw.llm.exceptions.AuthNotConfiguredError`

        Args:
            workspace_dir: Path to ``.singleclaw/`` directory.  Defaults to
                           ``Path.cwd() / ".singleclaw"``.

        Returns:
            A resolved :class:`LLMConfig`.

        Raises:
            AuthNotConfiguredError: when no auth method is configured.
        """
        from singleclaw.llm.exceptions import AuthNotConfiguredError

        ws = Path(workspace_dir) if workspace_dir else Path.cwd() / ".singleclaw"
        provider = cls._detect_provider()

        # 1. API key
        api_key = cls._detect_api_key(provider)
        if api_key:
            return cls(auth_mode=AuthMode.API_KEY, provider=provider, api_key=api_key)

        # 2. OAuth token on disk
        token_path = ws / "auth_token.json"
        if token_path.exists():
            from singleclaw.llm.auth.token_store import TokenStore

            store = TokenStore(token_path)
            if store.is_valid():
                return cls(
                    auth_mode=AuthMode.OAUTH,
                    provider=provider,
                    token_path=token_path,
                )

        raise AuthNotConfiguredError()

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _detect_provider() -> Provider:
        """Return the configured provider, defaulting to OpenAI."""
        raw = os.environ.get("SINGLECLAW_LLM_PROVIDER", "").strip().lower()
        try:
            return Provider(raw) if raw else _DEFAULT_PROVIDER
        except ValueError:
            return _DEFAULT_PROVIDER

    @staticmethod
    def _detect_api_key(provider: Provider) -> str:
        """Return the API key for *provider* from the environment, or empty string."""
        env_var = _API_KEY_ENV.get(provider, "")
        if env_var:
            return os.environ.get(env_var, "").strip()
        return ""
