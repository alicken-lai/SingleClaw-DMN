"""Reflection engine – human-readable summary of recent memory and journal entries.

The ``reflect`` command calls this module to produce a concise Markdown-formatted
summary suitable for printing to the terminal via Rich.
"""

from __future__ import annotations

from rich.markdown import Markdown

from singleclaw.dmn.journal import TaskJournal
from singleclaw.dmn.memory import MemoryStore


def reflect_on_memory(
    memory: MemoryStore,
    journal: TaskJournal,
    n_memory: int = 10,
    n_journal: int = 10,
) -> Markdown:
    """Build a Rich ``Markdown`` summary of recent memory and journal entries.

    Args:
        memory:   The active ``MemoryStore`` instance.
        journal:  The active ``TaskJournal`` instance.
        n_memory: Number of recent memory items to include.
        n_journal: Number of recent journal entries to include.

    Returns:
        A :class:`rich.markdown.Markdown` object ready for ``console.print()``.
    """
    lines: list[str] = ["# SingleClaw DMN – Reflection\n"]

    # ── Memory section ──────────────────────────────────────────────────────
    lines.append("## Recent Memory\n")
    recent_memories = memory.recent(n=n_memory)
    if recent_memories:
        for item in recent_memories:
            ts = item.get("timestamp", "")[:19].replace("T", " ")
            tag = item.get("tag", "note")
            text = item.get("text", "")
            lines.append(f"- `{ts}` **[{tag}]** {text}")
    else:
        lines.append("*No memory items found. Use `singleclaw remember` to add some.*")

    lines.append("")

    # ── Journal section ──────────────────────────────────────────────────────
    lines.append("## Recent Activity\n")
    recent_entries = journal.recent(n=n_journal)
    if recent_entries:
        for entry in recent_entries:
            ts = entry.get("timestamp", "")[:19].replace("T", " ")
            cmd = entry.get("command", "")
            status = entry.get("status", "")
            risk = entry.get("risk_level", "")
            risk_str = f" ⚠ risk={risk}" if risk else ""
            lines.append(f"- `{ts}` **{cmd}** → {status}{risk_str}")
    else:
        lines.append("*No journal entries yet.*")

    # ── Stats ────────────────────────────────────────────────────────────────
    lines.append("")
    lines.append("## Stats\n")
    all_memories = memory.list_all()
    all_entries = journal.load()
    lines.append(f"- Total memory items: **{len(all_memories)}**")
    lines.append(f"- Total journal entries: **{len(all_entries)}**")

    return Markdown("\n".join(lines))
