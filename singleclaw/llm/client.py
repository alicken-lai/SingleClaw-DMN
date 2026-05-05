"""LLMClient – unified protocol for all LLM providers.

Every provider (OpenAI, Google Gemini, …) implements this protocol so that
``SkillRunner`` and the CLI never need to know which provider is active.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Protocol, runtime_checkable


@dataclass
class LLMResponse:
    """Structured response returned by ``LLMClient.complete()``.

    Args:
        text:             The generated text content.
        prompt_tokens:    Number of tokens in the prompt (0 if unavailable).
        completion_tokens: Number of tokens in the completion (0 if unavailable).
        model:            Model identifier string reported by the provider.
    """

    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model: str = ""

    @property
    def total_tokens(self) -> int:
        """Total token count (prompt + completion)."""
        return self.prompt_tokens + self.completion_tokens


@runtime_checkable
class LLMClient(Protocol):
    """Protocol satisfied by all LLM provider implementations.

    Any object that provides ``complete()`` and ``stream()`` methods with the
    correct signatures implicitly satisfies this protocol – no explicit
    inheritance required.
    """

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Send *prompt* to the LLM and return the full response.

        Args:
            prompt:      The user-turn content.
            system:      Optional system-level instruction.
            temperature: Sampling temperature (0 = deterministic).
            max_tokens:  Maximum number of tokens to generate.

        Returns:
            An :class:`LLMResponse` with the generated text and token counts.

        Raises:
            LLMProviderError: on network errors or unexpected API responses.
        """
        ...

    def stream(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Iterator[str]:
        """Yield response chunks as they arrive from the LLM.

        Args:
            prompt:      The user-turn content.
            system:      Optional system-level instruction.
            temperature: Sampling temperature.
            max_tokens:  Maximum number of tokens to generate.

        Yields:
            String chunks of the generated text.

        Raises:
            LLMProviderError: on network errors or unexpected API responses.
        """
        ...
