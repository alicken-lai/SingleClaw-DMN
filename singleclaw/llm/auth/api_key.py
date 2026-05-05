"""API key authentication helper.

Reads an API key from an environment variable (with optional `.env` loading
already handled by :mod:`singleclaw.llm.config`).
"""

from __future__ import annotations

import os
from typing import Optional


def get_api_key(env_var: str) -> Optional[str]:
    """Return the value of *env_var* from the environment, or ``None``.

    An empty or whitespace-only value is treated as absent.

    Args:
        env_var: Name of the environment variable, e.g. ``"OPENAI_API_KEY"``.

    Returns:
        The API key string, or ``None`` if not set.
    """
    value = os.environ.get(env_var, "").strip()
    return value if value else None
