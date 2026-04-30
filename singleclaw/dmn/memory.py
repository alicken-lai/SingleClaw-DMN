"""DMN Memory – persistent, human-readable local memory store.

Records are stored as JSONL in ``.singleclaw/memory.jsonl`` and mirrored as a
Markdown note file in ``.singleclaw/memory_notes.md`` for easy browsing.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class MemoryStore:
    """Local JSONL-backed memory store for the SingleClaw workspace.

    Args:
        workspace_dir: Path to the ``.singleclaw/`` directory.
    """

    MEMORY_FILE = "memory.jsonl"
    NOTES_FILE = "memory_notes.md"

    def __init__(self, workspace_dir: Path) -> None:
        self._dir = Path(workspace_dir)
        self._memory_path = self._dir / self.MEMORY_FILE
        self._notes_path = self._dir / self.NOTES_FILE

    # ─── write ──────────────────────────────────────────────────────────────

    def add(
        self,
        text: str,
        tag: str = "note",
        metadata: Optional[dict] = None,
    ) -> dict:
        """Append a memory item and return the stored record.

        Args:
            text: The content to remember.
            tag:  Category / tag for the item (e.g. ``decision``, ``preference``).
            metadata: Optional extra key/value pairs to include in the record.

        Returns:
            The full record dict that was persisted.
        """
        record = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tag": tag,
            "text": text,
            **(metadata or {}),
        }
        self._append_jsonl(record)
        self._append_note(record)
        return record

    # ─── read ───────────────────────────────────────────────────────────────

    def list_all(self) -> list[dict]:
        """Return all memory records in chronological order."""
        return self._load_all()

    def recent(self, n: int = 10) -> list[dict]:
        """Return the *n* most recent memory records.

        Args:
            n: Maximum number of records to return.
        """
        return self._load_all()[-n:]

    def by_tag(self, tag: str) -> list[dict]:
        """Return all records matching the given tag.

        Args:
            tag: The tag to filter by.
        """
        return [r for r in self._load_all() if r.get("tag") == tag]

    # ─── internals ──────────────────────────────────────────────────────────

    def _load_all(self) -> list[dict]:
        if not self._memory_path.exists():
            return []
        records: list[dict] = []
        with self._memory_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass  # skip corrupt lines
        return records

    def _append_jsonl(self, record: dict) -> None:
        with self._memory_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")

    def _append_note(self, record: dict) -> None:
        timestamp = record.get("timestamp", "")
        tag = record.get("tag", "note")
        text = record.get("text", "")
        line = f"- [{timestamp}] **[{tag}]** {text}\n"
        with self._notes_path.open("a", encoding="utf-8") as fh:
            fh.write(line)
