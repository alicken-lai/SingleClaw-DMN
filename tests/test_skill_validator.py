"""Tests for SkillValidator (v0.4 – TDD red phase).

These tests were written *before* the implementation exists.
They define the full contract for singleclaw/skills/validator.py.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from singleclaw.skills.registry import Skill


# ─── helpers ──────────────────────────────────────────────────────────────────


def _make_skill(tmp_path: Path, name: str = "test_skill", extra: dict | None = None) -> Skill:
    """Create a minimal valid skill directory and return the Skill object."""
    skill_dir = tmp_path / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    metadata: dict = {
        "name": name,
        "description": "A test skill",
        "version": "0.1.0",
        "input_type": "application/json",
        "output_type": "text/markdown",
        "risk_level": "low",
    }
    if extra:
        metadata.update(extra)
    (skill_dir / "skill.yaml").write_text(yaml.dump(metadata), encoding="utf-8")
    return Skill(name=name, path=skill_dir, metadata=metadata)


# ─── ValidationResult contract ────────────────────────────────────────────────


class TestValidationResult:
    def test_valid_result_has_no_errors(self):
        from singleclaw.skills.validator import ValidationResult

        r = ValidationResult(is_valid=True, errors=[])
        assert r.is_valid is True
        assert r.errors == []

    def test_invalid_result_carries_errors(self):
        from singleclaw.skills.validator import ValidationResult

        r = ValidationResult(is_valid=False, errors=["field X is missing"])
        assert r.is_valid is False
        assert "field X is missing" in r.errors


# ─── validate_manifest ────────────────────────────────────────────────────────


class TestValidateManifest:
    def test_skill_without_schemas_is_valid(self, tmp_path):
        """A skill with no input_schema / output_schema passes validation."""
        from singleclaw.skills.validator import SkillValidator

        skill = _make_skill(tmp_path)
        result = SkillValidator().validate_manifest(skill)
        assert result.is_valid

    def test_skill_with_valid_input_schema_is_valid(self, tmp_path):
        from singleclaw.skills.validator import SkillValidator

        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        skill = _make_skill(tmp_path, extra={"input_schema": schema})
        result = SkillValidator().validate_manifest(skill)
        assert result.is_valid

    def test_skill_with_valid_output_schema_is_valid(self, tmp_path):
        from singleclaw.skills.validator import SkillValidator

        schema = {"type": "object", "required": ["summary"]}
        skill = _make_skill(tmp_path, extra={"output_schema": schema})
        result = SkillValidator().validate_manifest(skill)
        assert result.is_valid

    def test_skill_with_both_schemas_is_valid(self, tmp_path):
        from singleclaw.skills.validator import SkillValidator

        in_schema = {"type": "object"}
        out_schema = {"type": "string"}
        skill = _make_skill(
            tmp_path,
            extra={"input_schema": in_schema, "output_schema": out_schema},
        )
        result = SkillValidator().validate_manifest(skill)
        assert result.is_valid

    def test_invalid_input_schema_reports_error(self, tmp_path):
        """A schema that is itself invalid (meta-validation failure) is reported."""
        from singleclaw.skills.validator import SkillValidator

        bad_schema = {"type": 12345}  # type must be a string, not int
        skill = _make_skill(tmp_path, extra={"input_schema": bad_schema})
        result = SkillValidator().validate_manifest(skill)
        assert not result.is_valid
        assert len(result.errors) > 0

    def test_invalid_output_schema_reports_error(self, tmp_path):
        from singleclaw.skills.validator import SkillValidator

        bad_schema = {"type": [1, 2, 3]}  # must be string or list of strings
        skill = _make_skill(tmp_path, extra={"output_schema": bad_schema})
        result = SkillValidator().validate_manifest(skill)
        assert not result.is_valid

    def test_invalid_skill_manifest_fails(self, tmp_path):
        """A skill that already failed registry validation is invalid."""
        from singleclaw.skills.validator import SkillValidator

        skill = Skill(
            name="bad",
            path=tmp_path / "bad",
            metadata={},
            errors=["Missing required fields: ['name']"],
        )
        result = SkillValidator().validate_manifest(skill)
        assert not result.is_valid
        assert any("Missing required fields" in e for e in result.errors)


# ─── validate_input ───────────────────────────────────────────────────────────


class TestValidateInput:
    def test_valid_data_passes_input_schema(self, tmp_path):
        from singleclaw.skills.validator import SkillValidator

        schema = {
            "type": "object",
            "required": ["title"],
            "properties": {"title": {"type": "string"}},
        }
        skill = _make_skill(tmp_path, extra={"input_schema": schema})
        result = SkillValidator().validate_input(skill, {"title": "hello"})
        assert result.is_valid

    def test_invalid_data_fails_input_schema(self, tmp_path):
        from singleclaw.skills.validator import SkillValidator

        schema = {
            "type": "object",
            "required": ["title"],
            "properties": {"title": {"type": "string"}},
        }
        skill = _make_skill(tmp_path, extra={"input_schema": schema})
        result = SkillValidator().validate_input(skill, {"title": 999})
        assert not result.is_valid
        assert len(result.errors) > 0

    def test_missing_required_field_fails(self, tmp_path):
        from singleclaw.skills.validator import SkillValidator

        schema = {"type": "object", "required": ["name"]}
        skill = _make_skill(tmp_path, extra={"input_schema": schema})
        result = SkillValidator().validate_input(skill, {})
        assert not result.is_valid

    def test_no_schema_always_passes(self, tmp_path):
        """Without input_schema, any data is accepted (backward compat)."""
        from singleclaw.skills.validator import SkillValidator

        skill = _make_skill(tmp_path)
        result = SkillValidator().validate_input(skill, {"anything": True})
        assert result.is_valid


# ─── validate_output ──────────────────────────────────────────────────────────


class TestValidateOutput:
    def test_valid_output_passes(self, tmp_path):
        from singleclaw.skills.validator import SkillValidator

        schema = {"type": "object", "required": ["summary"]}
        skill = _make_skill(tmp_path, extra={"output_schema": schema})
        result = SkillValidator().validate_output(skill, {"summary": "done"})
        assert result.is_valid

    def test_invalid_output_fails(self, tmp_path):
        from singleclaw.skills.validator import SkillValidator

        schema = {"type": "object", "required": ["summary"]}
        skill = _make_skill(tmp_path, extra={"output_schema": schema})
        result = SkillValidator().validate_output(skill, {})
        assert not result.is_valid

    def test_no_output_schema_always_passes(self, tmp_path):
        from singleclaw.skills.validator import SkillValidator

        skill = _make_skill(tmp_path)
        result = SkillValidator().validate_output(skill, {"anything": True})
        assert result.is_valid
