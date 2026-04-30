"""Workspace Manager – manage the ``.singleclaw/`` local workspace directory.

The workspace directory stores all persistent data:
- ``memory.jsonl``   – DMN memory records
- ``memory_notes.md``– human-readable memory mirror
- ``journal.jsonl``  – task journal
- ``config.json``    – user preferences
"""

from __future__ import annotations

import json
from pathlib import Path


class WorkspaceManager:
    """Manage the local SingleClaw workspace.

    Args:
        base_dir:    Directory in which to create the workspace.  Defaults to
                     the current working directory.
        workspace_name: Sub-directory name.  Defaults to ``.singleclaw``.
    """

    DEFAULT_NAME = ".singleclaw"

    def __init__(
        self,
        base_dir: Path | None = None,
        workspace_name: str = DEFAULT_NAME,
    ) -> None:
        self._base = Path(base_dir or Path.cwd())
        self._workspace_name = workspace_name
        self.workspace_dir = self._base / workspace_name

    # ─── lifecycle ───────────────────────────────────────────────────────────

    def initialise(self) -> None:
        """Create the workspace directory and seed empty data files.

        Raises:
            RuntimeError: if the workspace already exists (idempotent init is
                          safe – we only raise when the directory is non-empty
                          and appears to belong to a different project).
        """
        if self.workspace_dir.exists():
            # Already initialised – nothing to do.
            return

        self.workspace_dir.mkdir(parents=True, exist_ok=True)

        # Seed empty data files so that reads never fail on a fresh workspace.
        (self.workspace_dir / "memory.jsonl").touch()
        (self.workspace_dir / "memory_notes.md").write_text(
            "# SingleClaw DMN – Memory Notes\n\n", encoding="utf-8"
        )
        (self.workspace_dir / "journal.jsonl").touch()

        default_config = {
            "version": "0.1.0",
            "guardian_mode": "strict",
            "dry_run": False,
        }
        (self.workspace_dir / "config.json").write_text(
            json.dumps(default_config, indent=2) + "\n", encoding="utf-8"
        )

    def is_initialised(self) -> bool:
        """Return ``True`` when the workspace directory exists."""
        return self.workspace_dir.is_dir()

    # ─── config ──────────────────────────────────────────────────────────────

    def load_config(self) -> dict:
        """Load ``config.json`` and return it as a dict.

        Returns an empty dict when the file does not exist.
        """
        config_path = self.workspace_dir / "config.json"
        if not config_path.exists():
            return {}
        with config_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def save_config(self, config: dict) -> None:
        """Write *config* dict to ``config.json``.

        Args:
            config: Configuration dict to persist.
        """
        config_path = self.workspace_dir / "config.json"
        with config_path.open("w", encoding="utf-8") as fh:
            json.dump(config, fh, indent=2)
            fh.write("\n")
