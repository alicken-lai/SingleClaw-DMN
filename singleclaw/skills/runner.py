"""Skill Runner – execute a skill with its input data.

In the MVP the runner validates the input file, prints a dry-run preview (or
executes the placeholder logic), and returns a Rich-renderable result.  Actual
LLM integration is left as a future extension point.

Memory context (a list of recent ``MemoryStore`` records) can be passed to
``execute()`` and is surfaced in the result panel so that future LLM
integration can inject it into prompts.
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
        dry_run: When ``True`` no side effects are produced; a preview panel
                 is returned instead.
    """

    def __init__(self, dry_run: bool = False) -> None:
        self._dry_run = dry_run

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
            memory_context: Optional list of recent DMN memory records.  Included
                            in the result panel for context; will be injected into
                            LLM prompts in v0.2.

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

        # ── Placeholder execution ─────────────────────────────────────────
        # In a real implementation this would call an LLM or subprocess.
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
            snippets = [f"[{m.get('tag','note')}] {m.get('text','')}" for m in memory_context[:_MAX_DISPLAYED_MEMORY_ITEMS]]
            content.append(f"{snippets}\n")

        content.append("\nResult:      ", style="bold")
        content.append(
            "[Placeholder] Skill executed successfully. "
            "Integrate an LLM provider to produce real output.",
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
