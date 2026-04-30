"""Task Journal – JSONL audit log of every CLI action.

Every command appends one record to ``.singleclaw/journal.jsonl`` so that the
user always has a full history of what the agent did and why.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class TaskJournal:
    """Append-only JSONL task journal.

    Args:
        workspace_dir: Path to the ``.singleclaw/`` directory.  When the
            workspace has not been initialised yet the log call is silently
            skipped so that CLI commands do not crash before ``init``.
    """

    JOURNAL_FILE = "journal.jsonl"

    def __init__(self, workspace_dir: Path) -> None:
        self._path = Path(workspace_dir) / self.JOURNAL_FILE

    # ─── write ──────────────────────────────────────────────────────────────

    def log(
        self,
        command: str,
        input_summary: str = "",
        status: str = "success",
        risk_level: Optional[str] = None,
        notes: str = "",
    ) -> None:
        """Append a journal record.

        Args:
            command:       The CLI command that was run (e.g. ``run``).
            input_summary: A short summary of the input (≤ 200 chars).
            status:        Outcome – ``success``, ``error``, ``blocked``, etc.
            risk_level:    Guardian risk classification if applicable.
            notes:         Free-form extra notes or error messages.
        """
        if not self._path.parent.exists():
            return  # workspace not yet initialised – skip silently

        record: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "command": command,
            "input_summary": input_summary[:200],
            "status": status,
        }
        if risk_level:
            record["risk_level"] = risk_level
        if notes:
            record["notes"] = notes[:500]

        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")

    # ─── read ────────────────────────────────────────────────────────────────

    def load(self) -> list[dict]:
        """Return all journal records in chronological order."""
        if not self._path.exists():
            return []
        records: list[dict] = []
        with self._path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return records

    def recent(self, n: int = 10) -> list[dict]:
        """Return the *n* most recent journal records.

        Args:
            n: Maximum number of records to return.
        """
        return self.load()[-n:]
