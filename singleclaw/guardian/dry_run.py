"""Dry-run support for the Guardian layer.

A dry run renders a human-readable preview of what *would* happen if an action
were executed, without actually performing any side effects.
"""

from __future__ import annotations

from rich.panel import Panel
from rich.text import Text


def dry_run_preview(action: str, input_summary: str = "", risk_level: str = "unknown") -> Panel:
    """Build a Rich ``Panel`` showing a dry-run preview of an action.

    Args:
        action:        Human-readable description of the action.
        input_summary: Short summary of the input data.
        risk_level:    The Guardian risk classification.

    Returns:
        A :class:`rich.panel.Panel` object ready for ``console.print()``.
    """
    colour_map = {
        "low": "green",
        "medium": "yellow",
        "high": "red",
        "critical": "bold red",
        "unknown": "white",
    }
    colour = colour_map.get(risk_level.lower(), "white")

    content = Text()
    content.append("ACTION:     ", style="bold")
    content.append(f"{action}\n")
    if input_summary:
        content.append("INPUT:      ", style="bold")
        content.append(f"{input_summary}\n")
    content.append("RISK LEVEL: ", style="bold")
    content.append(risk_level.upper(), style=colour)
    content.append("\n\nThis is a ")
    content.append("DRY RUN", style="bold yellow")
    content.append(" – no changes were made.")

    return Panel(
        content,
        title="[bold yellow]⚡ Dry Run Preview[/bold yellow]",
        border_style="yellow",
    )
