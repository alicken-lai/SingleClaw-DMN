"""Tests for SkillRegistry entry-point discovery (issue #23 – TDD).

Third-party packages expose skills via the ``singleclaw.skills`` entry-points
group.  Each entry-point's ``load()`` must return the ``Path`` to a skill
directory (or a zero-argument callable that returns one).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml

from singleclaw.skills.registry import SkillRegistry


# ─── helpers ──────────────────────────────────────────────────────────────────


def _make_skill_dir(tmp_path: Path, name: str, extra: dict | None = None) -> Path:
    """Create a minimal skill directory and return its path."""
    skill_dir = tmp_path / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    metadata: dict = {
        "name": name,
        "description": "Installed test skill",
        "version": "1.0.0",
        "input_type": "application/json",
        "output_type": "text/markdown",
        "risk_level": "low",
    }
    if extra:
        metadata.update(extra)
    (skill_dir / "skill.yaml").write_text(yaml.dump(metadata), encoding="utf-8")
    return skill_dir


def _mock_entry_point(name: str, skill_dir: Path) -> MagicMock:
    """Build a mock entry-point that returns *skill_dir* on ``load()``."""
    ep = MagicMock()
    ep.name = name
    ep.load.return_value = skill_dir
    return ep


# ─── entry-point discovery ────────────────────────────────────────────────────


class TestEntryPointDiscovery:
    def test_entry_point_skill_appears_in_list_all(self, tmp_path):
        """A skill exposed via entry-point is returned by list_all()."""
        skill_dir = _make_skill_dir(tmp_path, "ep_skill")
        ep = _mock_entry_point("ep_skill", skill_dir)

        empty_root = tmp_path / "empty_skills"
        empty_root.mkdir()

        with patch("singleclaw.skills.registry.entry_points", return_value=[ep]):
            registry = SkillRegistry(skills_root=empty_root)
            names = [s.name for s in registry.list_all()]

        assert "ep_skill" in names

    def test_entry_point_skill_retrievable_by_get(self, tmp_path):
        """A skill exposed via entry-point is retrievable with get()."""
        skill_dir = _make_skill_dir(tmp_path, "ep_skill_get")
        ep = _mock_entry_point("ep_skill_get", skill_dir)

        empty_root = tmp_path / "empty_skills"
        empty_root.mkdir()

        with patch("singleclaw.skills.registry.entry_points", return_value=[ep]):
            registry = SkillRegistry(skills_root=empty_root)
            skill = registry.get("ep_skill_get")

        assert skill is not None
        assert skill.name == "ep_skill_get"

    def test_entry_point_callable_skill_is_resolved(self, tmp_path):
        """load() may return a zero-arg callable that returns a Path."""
        skill_dir = _make_skill_dir(tmp_path, "callable_ep_skill")
        ep = MagicMock()
        ep.name = "callable_ep_skill"
        ep.load.return_value = lambda: skill_dir  # callable returning Path

        empty_root = tmp_path / "empty_skills"
        empty_root.mkdir()

        with patch("singleclaw.skills.registry.entry_points", return_value=[ep]):
            registry = SkillRegistry(skills_root=empty_root)
            skill = registry.get("callable_ep_skill")

        assert skill is not None

    def test_no_entry_points_returns_empty_additions(self, tmp_path):
        """When there are no entry-points, list_all() returns only fs skills."""
        _make_skill_dir(tmp_path / "skills", "local_skill")

        with patch("singleclaw.skills.registry.entry_points", return_value=[]):
            registry = SkillRegistry(skills_root=tmp_path / "skills")
            names = [s.name for s in registry.list_all()]

        assert "local_skill" in names

    def test_entry_point_and_fs_skill_both_discovered(self, tmp_path):
        """Entry-point skills and filesystem skills are both returned."""
        skills_root = tmp_path / "skills"
        skills_root.mkdir()
        _make_skill_dir(skills_root, "fs_skill")

        ep_skill_dir = _make_skill_dir(tmp_path / "installed", "ep_skill_both")
        ep = _mock_entry_point("ep_skill_both", ep_skill_dir)

        with patch("singleclaw.skills.registry.entry_points", return_value=[ep]):
            registry = SkillRegistry(skills_root=skills_root)
            names = [s.name for s in registry.list_all()]

        assert "fs_skill" in names
        assert "ep_skill_both" in names

    def test_entry_point_with_invalid_path_skipped(self, tmp_path):
        """Entry-points pointing at non-existent directories are skipped."""
        ep = MagicMock()
        ep.name = "ghost_skill"
        ep.load.return_value = tmp_path / "does_not_exist"

        empty_root = tmp_path / "empty_skills"
        empty_root.mkdir()

        with patch("singleclaw.skills.registry.entry_points", return_value=[ep]):
            registry = SkillRegistry(skills_root=empty_root)
            names = [s.name for s in registry.list_all()]

        assert "ghost_skill" not in names

    def test_entry_point_load_exception_is_skipped(self, tmp_path):
        """If entry-point.load() raises, that skill is silently skipped."""
        ep = MagicMock()
        ep.name = "broken_ep"
        ep.load.side_effect = Exception("import failed")

        empty_root = tmp_path / "empty_skills"
        empty_root.mkdir()

        with patch("singleclaw.skills.registry.entry_points", return_value=[ep]):
            registry = SkillRegistry(skills_root=empty_root)
            # Should not raise; broken entry-point is skipped
            names = [s.name for s in registry.list_all()]

        assert "broken_ep" not in names

    def test_entry_point_skill_metadata_is_preserved(self, tmp_path):
        """Metadata from an entry-point skill's skill.yaml is readable."""
        skill_dir = _make_skill_dir(tmp_path, "meta_ep_skill", extra={"version": "9.9.9"})
        ep = _mock_entry_point("meta_ep_skill", skill_dir)

        empty_root = tmp_path / "empty_skills"
        empty_root.mkdir()

        with patch("singleclaw.skills.registry.entry_points", return_value=[ep]):
            registry = SkillRegistry(skills_root=empty_root)
            skill = registry.get("meta_ep_skill")

        assert skill is not None
        assert skill.metadata.get("version") == "9.9.9"
