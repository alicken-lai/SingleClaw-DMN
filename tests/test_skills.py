"""Tests for the skill registry."""

import pytest
import yaml
from pathlib import Path

from singleclaw.skills.registry import SkillRegistry


def _make_skill_dir(root: Path, name: str, extra: dict | None = None) -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    metadata = {
        "name": name,
        "description": "Test skill",
        "version": "0.1.0",
        "input_type": "application/json",
        "output_type": "text/markdown",
        "risk_level": "low",
    }
    if extra:
        metadata.update(extra)
    (skill_dir / "skill.yaml").write_text(yaml.dump(metadata), encoding="utf-8")
    return skill_dir


class TestSkillRegistry:
    def test_discover_valid_skill(self, tmp_path):
        _make_skill_dir(tmp_path, "my_skill")
        registry = SkillRegistry(skills_root=tmp_path)

        skills = registry.list_all()
        assert len(skills) == 1
        assert skills[0].name == "my_skill"
        assert skills[0].is_valid

    def test_get_returns_skill_by_name(self, tmp_path):
        _make_skill_dir(tmp_path, "foo_skill")
        registry = SkillRegistry(skills_root=tmp_path)

        skill = registry.get("foo_skill")
        assert skill is not None
        assert skill.name == "foo_skill"

    def test_get_returns_none_for_missing(self, tmp_path):
        registry = SkillRegistry(skills_root=tmp_path)
        assert registry.get("nonexistent") is None

    def test_invalid_skill_missing_fields(self, tmp_path):
        skill_dir = tmp_path / "bad_skill"
        skill_dir.mkdir()
        (skill_dir / "skill.yaml").write_text(
            yaml.dump({"name": "bad_skill", "description": "incomplete"}),
            encoding="utf-8",
        )
        registry = SkillRegistry(skills_root=tmp_path)

        skill = registry.get("bad_skill")
        assert skill is not None
        assert not skill.is_valid
        assert len(skill.errors) > 0

    def test_empty_skills_dir_returns_empty(self, tmp_path):
        registry = SkillRegistry(skills_root=tmp_path)
        assert registry.list_all() == []

    def test_missing_skills_dir_returns_empty(self, tmp_path):
        registry = SkillRegistry(skills_root=tmp_path / "nonexistent")
        assert registry.list_all() == []

    def test_multiple_skills_discovered(self, tmp_path):
        for name in ["skill_a", "skill_b", "skill_c"]:
            _make_skill_dir(tmp_path, name)
        registry = SkillRegistry(skills_root=tmp_path)

        names = {s.name for s in registry.list_all()}
        assert names == {"skill_a", "skill_b", "skill_c"}

    def test_builtin_skills_are_valid(self):
        """Verify the three built-in example skills pass validation."""
        project_root = Path(__file__).resolve().parent.parent
        registry = SkillRegistry(skills_root=project_root / "skills")

        valid = registry.list_valid()
        names = {s.name for s in valid}

        assert "meeting_minutes_to_report" in names
        assert "procurement_comparison" in names
        assert "linkedin_post_writer" in names
