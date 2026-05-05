"""Prompt template rendering.

Skills may optionally include a ``prompt_template`` key in their ``skill.yaml``.
This module renders that template by substituting ``{input_data}`` and
``{memory_context}`` placeholders.

Usage::

    from singleclaw.llm.prompt import render_prompt

    prompt = render_prompt(
        template="Summarise the meeting: {input_data}",
        input_data={"agenda": "Q3 review"},
        memory_context=[{"tag": "goal", "text": "Focus on revenue"}],
    )
"""

from __future__ import annotations

import json
from typing import Any, Optional


def render_prompt(
    template: str,
    input_data: dict[str, Any],
    memory_context: Optional[list[dict]] = None,
    *,
    max_memory_items: int = 5,
) -> str:
    """Render *template* with the supplied data.

    Supported placeholders (all optional in the template):

    * ``{input_data}``      – JSON-serialised *input_data* dict.
    * ``{memory_context}``  – Bullet-point list of recent memory items.
    * Any key in *input_data* directly, e.g. ``{agenda}`` when
      ``input_data = {"agenda": "..."}``.

    Unknown placeholders that cannot be filled are left as-is (no error).

    Args:
        template:        The raw template string from ``skill.yaml``.
        input_data:      The skill's JSON input.
        memory_context:  Recent DMN memory records.
        max_memory_items: Maximum number of memory items to include.

    Returns:
        The rendered prompt string.
    """
    memory_context = memory_context or []
    memory_items = memory_context[:max_memory_items]

    # Build the memory context block as a bullet list.
    if memory_items:
        memory_lines = "\n".join(
            f"- [{m.get('tag', 'note')}] {m.get('text', '')}" for m in memory_items
        )
    else:
        memory_lines = "(no memory context)"

    # Build substitution map – special keys first, then individual input keys.
    substitutions: dict[str, str] = {
        "input_data": json.dumps(input_data, ensure_ascii=False, indent=2),
        "memory_context": memory_lines,
    }
    # Also expose each top-level input key directly.
    for k, v in input_data.items():
        if k not in substitutions:
            substitutions[str(k)] = str(v)

    try:
        return template.format_map(_SafeSubstitution(substitutions))
    except Exception:  # noqa: BLE001
        # Never raise on a broken template; return the template unchanged.
        return template


class _SafeSubstitution(dict):
    """A dict subclass that returns the original ``{key}`` when a key is missing.

    This prevents :meth:`str.format_map` from raising ``KeyError`` when the
    template uses placeholders that are not in the substitution map.
    """

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"
