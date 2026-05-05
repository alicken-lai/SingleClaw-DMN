"""SingleClaw LLM subsystem – public API.

Importing from this package gives access to the core abstractions used
throughout the rest of the codebase:

    from singleclaw.llm import LLMClient, LLMConfig, LLMClientFactory
    from singleclaw.llm import AuthNotConfiguredError, LLMProviderError
"""

from singleclaw.llm.client import LLMClient, LLMResponse
from singleclaw.llm.config import AuthMode, LLMConfig
from singleclaw.llm.factory import LLMClientFactory
from singleclaw.llm.exceptions import AuthNotConfiguredError, LLMProviderError

__all__ = [
    "LLMClient",
    "LLMResponse",
    "AuthMode",
    "LLMConfig",
    "LLMClientFactory",
    "AuthNotConfiguredError",
    "LLMProviderError",
]
