"""Skill Runner – execute a skill with its input data.

In v0.1 the runner validated the input file and returned a placeholder result.
In v0.2 the runner attempts to call an LLM via ``LLMClient`` (injected by the
CLI).  When no LLM client is available it falls back gracefully to the
placeholder behaviour with a hint to configure auth.

Memory context (a list of recent ``MemoryStore`` records) can be passed to
``execute()`` and is injected into the LLM prompt template when one is present.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from rich.panel import Panel
from rich.text import Text

from singleclaw.guardian.dry_run import dry_run_preview
from singleclaw.skills.registry import Skill

_MAX_DISPLAYED_MEMORY_ITEMS = 3  # max context snippets shown in the result panel


class SkillRunner:
    """Execute a skill, optionally in dry-run mode.

    Args:
        dry_run:    When ``True`` no side effects are produced; a preview panel
                    is returned instead.
        llm_client: An object satisfying the
                    :class:`~singleclaw.llm.client.LLMClient` protocol.  When
                    ``None`` the runner falls back to placeholder output.
    """

    def __init__(self, dry_run: bool = False, llm_client: object = None) -> None:
        self._dry_run = dry_run
        self._llm = llm_client

    def execute(
        self,
        skill: Skill,
        input_file: str,
        memory_context: Optional[list[dict]] = None,
    ) -> Panel:
        """Run *skill* with the data from *input_file*.

        Args:
            skill:          A validated :class:`~singleclaw.skills.registry.Skill`.
            input_file:     Path to a JSON file matching the skill's input schema.
            memory_context: Optional list of recent DMN memory records.  Injected
                            into the LLM prompt template when available.

        Returns:
            A :class:`rich.panel.Panel` summarising the result.
        """
        input_path = Path(input_file)
        input_data: dict = {}

        if not input_path.exists():
            return _error_panel(f"Input file not found: {input_file}")

        try:
            with input_path.open("r", encoding="utf-8") as fh:
                input_data = json.load(fh)
        except json.JSONDecodeError as exc:
            return _error_panel(f"Invalid JSON in input file: {exc}")

        risk = skill.metadata.get("risk_level", "low")
        summary = f"skill={skill.name}, input_keys={list(input_data.keys())}"

        if self._dry_run:
            return dry_run_preview(
                action=f"run skill '{skill.name}'",
                input_summary=summary,
                risk_level=risk,
            )

        # ── LLM execution ────────────────────────────────────────────────────
        if self._llm is not None:
            return self._run_with_llm(skill, input_data, memory_context or [])

        # ── Placeholder execution ─────────────────────────────────────────
        return self._run_placeholder(skill, input_data, memory_context or [])

    # ── private helpers ──────────────────────────────────────────────────────

    def _run_with_llm(
        self,
        skill: Skill,
        input_data: dict,
        memory_context: list[dict],
    ) -> Panel:
        """Call the LLM and return a Rich panel with the result."""
        from singleclaw.llm.prompt import render_prompt
        from singleclaw.llm.exceptions import LLMProviderError

        template = skill.metadata.get("prompt_template", "")
        if not template:
            # No template in skill.yaml – use a sensible default.
            template = (
                "You are a helpful AI assistant.\n\n"
                "Task: {description}\n\n"
                "Input:\n{input_data}\n\n"
                "Recent context:\n{memory_context}"
            )

        # Inject description so it's available as {description} in templates.
        enriched_input = dict(input_data)
        enriched_input.setdefault("description", skill.metadata.get("description", skill.name))

        prompt = render_prompt(template, enriched_input, memory_context)

        try:
            response = self._llm.complete(prompt)  # type: ignore[union-attr]
        except LLMProviderError as exc:
            return _error_panel(f"LLM error: {exc}")

        content = Text()
        content.append("Skill:   ", style="bold")
        content.append(f"{skill.name}\n")
        content.append("Model:   ", style="bold")
        content.append(f"{response.model or 'unknown'}\n")
        content.append("Tokens:  ", style="bold")
        content.append(
            f"prompt={response.prompt_tokens}, "
            f"completion={response.completion_tokens}\n"
        )
        content.append("\n")
        content.append(response.text)

        # Attach token usage to the panel for the CLI to log.
        panel = Panel(
            content,
            title=f"[bold green]✔ Skill: {skill.name}[/bold green]",
            border_style="green",
        )
        # Stash usage data on the panel object for retrieval by the CLI.
        panel._llm_token_usage = {  # type: ignore[attr-defined]
            "prompt_tokens": response.prompt_tokens,
            "completion_tokens": response.completion_tokens,
            "model": response.model,
        }
        return panel

    def _run_placeholder(
        self,
        skill: Skill,
        input_data: dict,
        memory_context: list[dict],
    ) -> Panel:
        """Return the v0.1 placeholder result with a hint to configure auth."""
        description = skill.metadata.get("description", "")
        content = Text()
        content.append("Skill:       ", style="bold")
        content.append(f"{skill.name}\n")
        content.append("Description: ", style="bold")
        content.append(f"{description}\n")
        content.append("Input keys:  ", style="bold")
        content.append(f"{list(input_data.keys())}\n")

        if memory_context:
            content.append("Memory ctx:  ", style="bold")
            snippets = [
                f"[{m.get('tag', 'note')}] {m.get('text', '')}"
                for m in memory_context[:_MAX_DISPLAYED_MEMORY_ITEMS]
            ]
            content.append(f"{snippets}\n")

        content.append("\nResult:      ", style="bold")
        content.append(
            "[Placeholder] Skill executed successfully. "
            "Set OPENAI_API_KEY in .env or run [bold]singleclaw auth login[/bold] "
            "to enable real LLM output.",
            style="dim",
        )

        return Panel(
            content,
            title=f"[bold green]✔ Skill: {skill.name}[/bold green]",
            border_style="green",
        )


def _error_panel(message: str) -> Panel:
    return Panel(
        Text(message, style="red"),
        title="[bold red]✘ Skill Runner Error[/bold red]",
        border_style="red",
    )
