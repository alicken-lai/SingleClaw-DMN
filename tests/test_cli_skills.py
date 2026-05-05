"""Tests for `singleclaw skills list` and `singleclaw skills validate` CLI commands.

Written before the implementation (TDD red phase).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import yaml
from typer.testing import CliRunner

from singleclaw.cli import app
from singleclaw.skills.registry import SkillRegistry


runner = CliRunner()


# ─── helpers ──────────────────────────────────────────────────────────────────


def _make_registry(tmp_path: Path, skills: list[dict]) -> SkillRegistry:
    """Build a SkillRegistry pointing at a tmp_path populated with skills."""
    for skill_meta in skills:
        name = skill_meta["name"]
        skill_dir = tmp_path / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        metadata: dict = {
            "description": "A test skill description",
            "version": "0.1.0",
            "input_type": "application/json",
            "output_type": "text/markdown",
            "risk_level": "low",
        }
        metadata.update(skill_meta)
        (skill_dir / "skill.yaml").write_text(yaml.dump(metadata), encoding="utf-8")
    return SkillRegistry(skills_root=tmp_path)


# ─── skills list ──────────────────────────────────────────────────────────────


class TestSkillsList:
    def test_lists_skills_in_table(self, tmp_path):
        """skills list shows discovered skills."""
        registry = _make_registry(tmp_path, [
            {"name": "alpha_skill"},
            {"name": "beta_skill"},
        ])
        with patch("singleclaw.cli.SkillRegistry", return_value=registry):
            result = runner.invoke(app, ["skills", "list"])

        assert result.exit_code == 0
        assert "alpha_skill" in result.output
        assert "beta_skill" in result.output

    def test_shows_risk_level(self, tmp_path):
        registry = _make_registry(tmp_path, [{"name": "risky_skill", "risk_level": "high"}])
        with patch("singleclaw.cli.SkillRegistry", return_value=registry):
            result = runner.invoke(app, ["skills", "list"])

        assert result.exit_code == 0
        assert "high" in result.output

    def test_shows_version(self, tmp_path):
        registry = _make_registry(tmp_path, [{"name": "versioned_skill", "version": "1.2.3"}])
        with patch("singleclaw.cli.SkillRegistry", return_value=registry):
            result = runner.invoke(app, ["skills", "list"])

        assert result.exit_code == 0
        assert "1.2.3" in result.output

    def test_empty_skills_dir_shows_message(self, tmp_path):
        registry = SkillRegistry(skills_root=tmp_path)
        with patch("singleclaw.cli.SkillRegistry", return_value=registry):
            result = runner.invoke(app, ["skills", "list"])

        assert result.exit_code == 0
        assert "No skills found" in result.output

    def test_shows_schema_presence_indicator(self, tmp_path):
        """Skills with input_schema show an indicator in the table."""
        schema = {"type": "object"}
        registry = _make_registry(tmp_path, [{"name": "schema_skill", "input_schema": schema}])
        with patch("singleclaw.cli.SkillRegistry", return_value=registry):
            result = runner.invoke(app, ["skills", "list"])

        assert result.exit_code == 0
        assert "schema_skill" in result.output

    def test_invalid_skill_shown_as_invalid(self, tmp_path):
        """Skills with validation errors are shown with an invalid status."""
        skill_dir = tmp_path / "broken_skill"
        skill_dir.mkdir()
        (skill_dir / "skill.yaml").write_text(
            yaml.dump({"name": "broken_skill"}), encoding="utf-8"
        )
        registry = SkillRegistry(skills_root=tmp_path)
        with patch("singleclaw.cli.SkillRegistry", return_value=registry):
            result = runner.invoke(app, ["skills", "list"])

        assert result.exit_code == 0
        assert "broken_skill" in result.output


# ─── skills validate ──────────────────────────────────────────────────────────


class TestSkillsValidate:
    def test_valid_skill_exits_zero(self, tmp_path):
        registry = _make_registry(tmp_path, [{"name": "good_skill"}])
        with patch("singleclaw.cli.SkillRegistry", return_value=registry):
            result = runner.invoke(app, ["skills", "validate", "good_skill"])

        assert result.exit_code == 0

    def test_valid_skill_shows_success_message(self, tmp_path):
        registry = _make_registry(tmp_path, [{"name": "good_skill"}])
        with patch("singleclaw.cli.SkillRegistry", return_value=registry):
            result = runner.invoke(app, ["skills", "validate", "good_skill"])

        assert "good_skill" in result.output

    def test_unknown_skill_exits_one(self, tmp_path):
        registry = SkillRegistry(skills_root=tmp_path)
        with patch("singleclaw.cli.SkillRegistry", return_value=registry):
            result = runner.invoke(app, ["skills", "validate", "no_such_skill"])

        assert result.exit_code == 1

    def test_skill_with_bad_schema_exits_one(self, tmp_path):
        bad_schema = {"type": 999}  # invalid JSON Schema
        registry = _make_registry(tmp_path, [{"name": "bad_schema_skill", "input_schema": bad_schema}])
        with patch("singleclaw.cli.SkillRegistry", return_value=registry):
            result = runner.invoke(app, ["skills", "validate", "bad_schema_skill"])

        assert result.exit_code == 1

    def test_skill_with_bad_schema_shows_error(self, tmp_path):
        bad_schema = {"type": 999}
        registry = _make_registry(tmp_path, [{"name": "bad_schema_skill", "input_schema": bad_schema}])
        with patch("singleclaw.cli.SkillRegistry", return_value=registry):
            result = runner.invoke(app, ["skills", "validate", "bad_schema_skill"])

        assert len(result.output) > 0

    def test_skill_with_valid_schemas_exits_zero(self, tmp_path):
        in_schema = {"type": "object", "required": ["title"]}
        out_schema = {"type": "string"}
        registry = _make_registry(tmp_path, [{
            "name": "schema_skill",
            "input_schema": in_schema,
            "output_schema": out_schema,
        }])
        with patch("singleclaw.cli.SkillRegistry", return_value=registry):
            result = runner.invoke(app, ["skills", "validate", "schema_skill"])

        assert result.exit_code == 0

