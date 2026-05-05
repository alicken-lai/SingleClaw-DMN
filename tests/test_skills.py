"""Tests for the skill registry and runner."""

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


class TestGuidanceSkillDiscovery:
    def _make_guidance_dir(self, root: Path, category: str, name: str, content: str = "# Guide\n") -> Path:
        skill_dir = root / category / name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
        return skill_dir

    def test_discovers_skill_md_files(self, tmp_path):
        self._make_guidance_dir(tmp_path, "engineering", "tdd")
        registry = SkillRegistry(skills_root=tmp_path)

        guidance = registry.list_guidance()
        assert len(guidance) == 1
        assert guidance[0].name == "tdd"

    def test_guidance_skill_has_correct_category(self, tmp_path):
        self._make_guidance_dir(tmp_path, "guardian", "destructive-action-guard")
        registry = SkillRegistry(skills_root=tmp_path)

        guidance = registry.list_guidance()
        assert guidance[0].category == "guardian"

    def test_get_guidance_by_name(self, tmp_path):
        self._make_guidance_dir(tmp_path, "engineering", "diagnose", content="# Diagnose\n")
        registry = SkillRegistry(skills_root=tmp_path)

        g = registry.get_guidance("diagnose")
        assert g is not None
        assert g.name == "diagnose"
        assert g.skill_md.exists()

    def test_get_guidance_returns_none_for_missing(self, tmp_path):
        registry = SkillRegistry(skills_root=tmp_path)
        assert registry.get_guidance("nonexistent") is None

    def test_multiple_categories_discovered(self, tmp_path):
        self._make_guidance_dir(tmp_path, "engineering", "tdd")
        self._make_guidance_dir(tmp_path, "guardian", "destructive-action-guard")
        self._make_guidance_dir(tmp_path, "dmn", "reflection-loop")
        self._make_guidance_dir(tmp_path, "memory", "memory-retrieval-before-action")
        registry = SkillRegistry(skills_root=tmp_path)

        names = {g.name for g in registry.list_guidance()}
        assert names == {"tdd", "destructive-action-guard", "reflection-loop", "memory-retrieval-before-action"}

    def test_skill_yaml_dirs_not_returned_as_guidance(self, tmp_path):
        """Top-level skill.yaml skills must not appear in list_guidance()."""
        skill_dir = tmp_path / "my_skill"
        skill_dir.mkdir()
        metadata = {
            "name": "my_skill", "description": "d", "version": "0.1.0",
            "input_type": "text", "output_type": "text", "risk_level": "low",
        }
        (skill_dir / "skill.yaml").write_text(yaml.dump(metadata), encoding="utf-8")

        registry = SkillRegistry(skills_root=tmp_path)
        assert registry.list_guidance() == []

    def test_builtin_guidance_skills_discovered(self):
        """Verify real SKILL.md files in the repo are discoverable."""
        project_root = Path(__file__).resolve().parent.parent
        registry = SkillRegistry(skills_root=project_root / "skills")

        names = {g.name for g in registry.list_guidance()}
        assert "tdd" in names
        assert "diagnose" in names
        assert "destructive-action-guard" in names
        assert "reflection-loop" in names


class TestSkillRunnerMemoryContext:
    def _make_skill(self, tmp_path: Path) -> "Skill":  # type: ignore[name-defined]  # noqa: F821
        import yaml
        from singleclaw.skills.registry import Skill
        skill_dir = tmp_path / "my_skill"
        skill_dir.mkdir()
        metadata = {
            "name": "my_skill",
            "description": "A test skill",
            "version": "0.1.0",
            "input_type": "application/json",
            "output_type": "text/markdown",
            "risk_level": "low",
        }
        (skill_dir / "skill.yaml").write_text(yaml.dump(metadata), encoding="utf-8")
        return Skill(name="my_skill", path=skill_dir, metadata=metadata)

    def test_memory_context_appears_in_result(self, tmp_path):
        """Memory context items are surfaced in the result panel."""
        import json
        from io import StringIO
        from rich.console import Console
        from singleclaw.skills.runner import SkillRunner

        skill = self._make_skill(tmp_path)
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps({"key": "val"}), encoding="utf-8")

        context = [{"tag": "decision", "text": "Use B2B focus for Q3", "timestamp": "2026-05-01"}]
        runner = SkillRunner(dry_run=False)
        panel = runner.execute(skill=skill, input_file=str(input_file), memory_context=context)

        buf = StringIO()
        c = Console(file=buf, no_color=True)
        c.print(panel)
        output = buf.getvalue()

        assert "B2B focus for Q3" in output

    def test_no_memory_context_runs_cleanly(self, tmp_path):
        """execute() without memory_context produces a valid result."""
        import json
        from singleclaw.skills.runner import SkillRunner
        from rich.panel import Panel

        skill = self._make_skill(tmp_path)
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps({"key": "val"}), encoding="utf-8")

        runner = SkillRunner(dry_run=False)
        result = runner.execute(skill=skill, input_file=str(input_file))
        assert isinstance(result, Panel)

    def test_runner_does_not_import_memory_store(self):
        """SkillRunner must not import MemoryStore (architecture invariant)."""
        import ast
        import pathlib
        runner_src = pathlib.Path(__file__).parent.parent / "singleclaw" / "skills" / "runner.py"
        tree = ast.parse(runner_src.read_text())
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.add(node.module)
        assert not any("dmn" in m for m in imported_modules), (
            "SkillRunner must not import from singleclaw.dmn – pass context via parameter"
        )
