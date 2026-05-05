"""Tests for the CLI commands – skill show, guardian interactive prompt, reflect --since."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from singleclaw.cli import app
from singleclaw.dmn.memory import MemoryStore
from singleclaw.dmn.journal import TaskJournal


runner = CliRunner()


# ─────────────────────────────────────────────────────────────
# Slice 1 – singleclaw skill show
# ─────────────────────────────────────────────────────────────


class TestSkillShow:
    def test_skill_show_prints_skill_md(self, tmp_path):
        """skill show <name> prints the SKILL.md content."""
        skill_dir = tmp_path / "engineering" / "tdd"
        skill_dir.mkdir(parents=True)
        content = "# TDD Skill\nUse red-green-refactor.\n"
        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")

        from singleclaw.skills.registry import SkillRegistry
        with patch("singleclaw.cli.SkillRegistry") as MockRegistry:
            registry_instance = SkillRegistry(skills_root=tmp_path)
            MockRegistry.return_value = registry_instance

            result = runner.invoke(app, ["skill", "show", "tdd"])

        assert result.exit_code == 0
        assert "TDD Skill" in result.output

    def test_skill_show_unknown_name_exits_nonzero(self, tmp_path):
        """skill show <unknown> exits with code 1."""
        from singleclaw.skills.registry import SkillRegistry
        with patch("singleclaw.cli.SkillRegistry") as MockRegistry:
            registry_instance = SkillRegistry(skills_root=tmp_path)
            MockRegistry.return_value = registry_instance

            result = runner.invoke(app, ["skill", "show", "nonexistent"])

        assert result.exit_code != 0


# ─────────────────────────────────────────────────────────────
# Slice 2 – Guardian interactive prompt for REVIEW_REQUIRED
# ─────────────────────────────────────────────────────────────


def _make_medium_risk_skill(skills_root: Path, name: str = "test_skill") -> Path:
    skill_dir = skills_root / name
    skill_dir.mkdir(parents=True)
    metadata = {
        "name": name,
        "description": "A medium-risk test skill",
        "version": "0.1.0",
        "input_type": "application/json",
        "output_type": "text/markdown",
        "risk_level": "medium",
    }
    import yaml
    (skill_dir / "skill.yaml").write_text(yaml.dump(metadata), encoding="utf-8")
    return skill_dir


class TestGuardianInteractivePrompt:
    def test_review_required_proceeds_on_yes(self, tmp_path):
        """When Guardian returns REVIEW_REQUIRED and user says 'y', skill executes."""
        workspace = tmp_path / ".singleclaw"
        workspace.mkdir()
        (workspace / "memory.jsonl").touch()
        (workspace / "journal.jsonl").touch()
        (workspace / "memory_notes.md").touch()
        skills_root = tmp_path / "skills"
        _make_medium_risk_skill(skills_root)
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps({"key": "value"}), encoding="utf-8")

        from singleclaw.skills.registry import SkillRegistry

        with (
            patch("singleclaw.cli.WorkspaceManager") as MockWM,
            patch("singleclaw.cli.SkillRegistry") as MockRegistry,
            patch("singleclaw.cli.typer.confirm", return_value=True),
        ):
            mock_wm = MockWM.return_value
            mock_wm.is_initialised.return_value = True
            mock_wm.workspace_dir = workspace
            MockRegistry.return_value = SkillRegistry(skills_root=skills_root)

            result = runner.invoke(app, ["run", "test_skill", "--input", str(input_file)])

        assert result.exit_code == 0

    def test_review_required_aborts_on_no(self, tmp_path):
        """When Guardian returns REVIEW_REQUIRED and user says 'n', skill is aborted."""
        workspace = tmp_path / ".singleclaw"
        workspace.mkdir()
        (workspace / "memory.jsonl").touch()
        (workspace / "journal.jsonl").touch()
        (workspace / "memory_notes.md").touch()
        skills_root = tmp_path / "skills"
        _make_medium_risk_skill(skills_root)
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps({"key": "value"}), encoding="utf-8")

        from singleclaw.skills.registry import SkillRegistry

        with (
            patch("singleclaw.cli.WorkspaceManager") as MockWM,
            patch("singleclaw.cli.SkillRegistry") as MockRegistry,
            patch("singleclaw.cli.typer.confirm", return_value=False),
        ):
            mock_wm = MockWM.return_value
            mock_wm.is_initialised.return_value = True
            mock_wm.workspace_dir = workspace
            MockRegistry.return_value = SkillRegistry(skills_root=skills_root)

            result = runner.invoke(app, ["run", "test_skill", "--input", str(input_file)])

        # User declined – should exit cleanly (code 0 = user abort, not an error)
        assert result.exit_code == 0
        assert "aborted" in result.output.lower() or "cancel" in result.output.lower()

    def test_dry_run_flag_skips_prompt(self, tmp_path):
        """Explicit --dry-run flag never prompts the user."""
        workspace = tmp_path / ".singleclaw"
        workspace.mkdir()
        (workspace / "memory.jsonl").touch()
        (workspace / "journal.jsonl").touch()
        (workspace / "memory_notes.md").touch()
        skills_root = tmp_path / "skills"
        _make_medium_risk_skill(skills_root)
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps({"key": "value"}), encoding="utf-8")

        from singleclaw.skills.registry import SkillRegistry

        with (
            patch("singleclaw.cli.WorkspaceManager") as MockWM,
            patch("singleclaw.cli.SkillRegistry") as MockRegistry,
            patch("singleclaw.cli.typer.confirm") as mock_confirm,
        ):
            mock_wm = MockWM.return_value
            mock_wm.is_initialised.return_value = True
            mock_wm.workspace_dir = workspace
            MockRegistry.return_value = SkillRegistry(skills_root=skills_root)

            result = runner.invoke(app, ["run", "test_skill", "--input", str(input_file), "--dry-run"])

        # confirm must never be called when --dry-run is explicit
        mock_confirm.assert_not_called()
        assert result.exit_code == 0


# ─────────────────────────────────────────────────────────────
# Slice 4 – reflect --since DATE
# ─────────────────────────────────────────────────────────────


class TestReflectSince:
    def test_reflect_since_filters_old_memories(self, tmp_path):
        """--since filters out memory items older than the given date."""
        from singleclaw.dmn.reflect import reflect_on_memory

        store = MemoryStore(tmp_path)
        journal = TaskJournal(tmp_path)

        # Add an old item (2 days ago) and a recent item (today)
        old_ts = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        recent_ts = datetime.now(timezone.utc).isoformat()

        store._append_jsonl({"id": "a1", "timestamp": old_ts, "tag": "note", "text": "old item"})
        store._append_jsonl({"id": "a2", "timestamp": recent_ts, "tag": "note", "text": "new item"})
        store._append_note({"id": "a1", "timestamp": old_ts, "tag": "note", "text": "old item"})
        store._append_note({"id": "a2", "timestamp": recent_ts, "tag": "note", "text": "new item"})

        since = datetime.now(timezone.utc) - timedelta(hours=1)
        result = reflect_on_memory(memory=store, journal=journal, since=since)

        # Access the rendered text
        from io import StringIO
        from rich.console import Console
        buf = StringIO()
        c = Console(file=buf, no_color=True)
        c.print(result)
        output = buf.getvalue()

        assert "new item" in output
        assert "old item" not in output

    def test_reflect_since_none_returns_all(self, tmp_path):
        """Without --since, all items are returned (existing behaviour)."""
        from singleclaw.dmn.reflect import reflect_on_memory

        store = MemoryStore(tmp_path)
        journal = TaskJournal(tmp_path)

        old_ts = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        store._append_jsonl({"id": "b1", "timestamp": old_ts, "tag": "note", "text": "old item"})
        store._append_note({"id": "b1", "timestamp": old_ts, "tag": "note", "text": "old item"})

        result = reflect_on_memory(memory=store, journal=journal, since=None)

        from io import StringIO
        from rich.console import Console
        buf = StringIO()
        c = Console(file=buf, no_color=True)
        c.print(result)
        output = buf.getvalue()

        assert "old item" in output

    def test_reflect_since_cli_option_accepted(self, tmp_path):
        """CLI accepts --since YYYY-MM-DD without error."""
        workspace = tmp_path / ".singleclaw"
        workspace.mkdir()
        (workspace / "memory.jsonl").touch()
        (workspace / "journal.jsonl").touch()
        (workspace / "memory_notes.md").touch()

        with patch("singleclaw.cli.WorkspaceManager") as MockWM:
            mock_wm = MockWM.return_value
            mock_wm.is_initialised.return_value = True
            mock_wm.workspace_dir = workspace

            result = runner.invoke(app, ["reflect", "--since", "2026-01-01"])

        assert result.exit_code == 0
