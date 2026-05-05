"""LLM subsystem exceptions."""

from __future__ import annotations


class AuthNotConfiguredError(RuntimeError):
    """Raised when no LLM auth method is available.

    The message always includes instructions on how to configure auth so that
    the CLI can display it directly to the user.
    """

    DEFAULT_MESSAGE = (
        "No LLM authentication configured.\n"
        "  • Set OPENAI_API_KEY (or GEMINI_API_KEY) in your .env file, or\n"
        "  • Run [bold]singleclaw auth login[/bold] to authenticate via browser."
    )

    def __init__(self, message: str = DEFAULT_MESSAGE) -> None:
        super().__init__(message)


class LLMProviderError(RuntimeError):
    """Raised when an LLM provider call fails (network error, bad response, etc.)."""
