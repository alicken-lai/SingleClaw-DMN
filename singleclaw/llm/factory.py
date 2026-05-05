"""LLMClientFactory – create the right LLMClient from resolved config.

Usage::

    from singleclaw.llm.factory import LLMClientFactory
    from singleclaw.llm.config import LLMConfig

    config = LLMConfig.resolve(workspace_dir=...)
    client = LLMClientFactory.create(config)
    response = client.complete("Summarise this meeting...")
"""

from __future__ import annotations


from singleclaw.llm.client import LLMClient
from singleclaw.llm.config import AuthMode, LLMConfig, Provider
from singleclaw.llm.exceptions import LLMProviderError


class LLMClientFactory:
    """Build an :class:`~singleclaw.llm.client.LLMClient` from a resolved config."""

    @staticmethod
    def create(config: LLMConfig) -> LLMClient:
        """Instantiate the correct provider implementation.

        Args:
            config: A :class:`~singleclaw.llm.config.LLMConfig` as returned by
                    :meth:`~singleclaw.llm.config.LLMConfig.resolve`.

        Returns:
            An object satisfying the :class:`~singleclaw.llm.client.LLMClient`
            protocol.

        Raises:
            LLMProviderError: for unsupported provider / auth combinations.
        """
        if config.provider == Provider.OPENAI:
            return LLMClientFactory._create_openai(config)

        if config.provider == Provider.GOOGLE:
            return LLMClientFactory._create_google(config)

        if config.provider == Provider.OLLAMA:
            return LLMClientFactory._create_ollama(config)

        raise LLMProviderError(f"Unsupported provider: {config.provider}")

    # ── provider builders ────────────────────────────────────────────────────

    @staticmethod
    def _create_openai(config: LLMConfig) -> LLMClient:
        from singleclaw.llm.providers.openai import OpenAIProvider

        if config.auth_mode != AuthMode.API_KEY or not config.api_key:
            raise LLMProviderError(
                "OpenAI only supports API key authentication. "
                "Set OPENAI_API_KEY in your .env file."
            )
        return OpenAIProvider(api_key=config.api_key)  # type: ignore[return-value]

    @staticmethod
    def _create_google(config: LLMConfig) -> LLMClient:
        from singleclaw.llm.providers.google import GoogleProvider

        if config.auth_mode == AuthMode.API_KEY:
            return GoogleProvider(api_key=config.api_key)  # type: ignore[return-value]

        if config.auth_mode == AuthMode.OAUTH and config.token_path:
            from singleclaw.llm.auth.token_store import TokenStore

            store = TokenStore(config.token_path)
            access_token = store.get_access_token()
            if not access_token:
                raise LLMProviderError("OAuth token is missing or invalid. Run `singleclaw auth login`.")
            return GoogleProvider(access_token=access_token)  # type: ignore[return-value]

        raise LLMProviderError("No valid auth for Google provider.")

    @staticmethod
    def _create_ollama(config: LLMConfig) -> LLMClient:
        """Ollama runs locally and requires no authentication."""
        from singleclaw.llm.providers.openai import OpenAIProvider
        import os

        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        model = os.environ.get("OLLAMA_MODEL", "llama3")
        # Ollama's OpenAI-compatible endpoint accepts any non-empty key.
        return OpenAIProvider(  # type: ignore[return-value]
            api_key="ollama",
            base_url=base_url,
            model=model,
        )
