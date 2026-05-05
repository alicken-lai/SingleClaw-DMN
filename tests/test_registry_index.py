"""Tests for RegistryIndex – local community registry index (issue #24 – TDD).

``RegistryIndex`` reads a ``registry-index.yaml`` file and exposes a list of
skill entries.  Entries may reference local skill directories by path.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from singleclaw.skills.registry_index import RegistryEntry, RegistryIndex


# ─── helpers ──────────────────────────────────────────────────────────────────


def _make_index(tmp_path: Path, content: dict) -> Path:
    """Write a registry-index.yaml and return its path."""
    index_path = tmp_path / "registry-index.yaml"
    index_path.write_text(yaml.dump(content), encoding="utf-8")
    return index_path


def _make_skill_dir(tmp_path: Path, name: str) -> Path:
    """Create a minimal skill directory."""
    skill_dir = tmp_path / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "name": name,
        "description": "Index test skill",
        "version": "0.1.0",
        "input_type": "application/json",
        "output_type": "text/markdown",
        "risk_level": "low",
    }
    (skill_dir / "skill.yaml").write_text(yaml.dump(metadata), encoding="utf-8")
    return skill_dir


# ─── RegistryEntry ────────────────────────────────────────────────────────────


class TestRegistryEntry:
    def test_has_required_fields(self):
        entry = RegistryEntry(
            name="my_skill",
            description="A skill",
            version="0.1.0",
            source="local",
            path=Path("/tmp/my_skill"),
        )
        assert entry.name == "my_skill"
        assert entry.description == "A skill"
        assert entry.version == "0.1.0"
        assert entry.source == "local"
        assert entry.path == Path("/tmp/my_skill")

    def test_path_is_optional(self):
        entry = RegistryEntry(
            name="no_path",
            description="No path yet",
            version="0.1.0",
            source="local",
        )
        assert entry.path is None


# ─── RegistryIndex – loading ──────────────────────────────────────────────────


class TestRegistryIndexLoading:
    def test_loads_valid_index(self, tmp_path):
        skill_dir = _make_skill_dir(tmp_path, "alpha_skill")
        content = {
            "version": "1",
            "skills": [
                {
                    "name": "alpha_skill",
                    "description": "Alpha",
                    "version": "0.1.0",
                    "source": "local",
                    "path": str(skill_dir),
                }
            ],
        }
        index_path = _make_index(tmp_path, content)
        index = RegistryIndex(index_path)
        entries = index.list_entries()
        assert len(entries) == 1
        assert entries[0].name == "alpha_skill"

    def test_loads_multiple_skills(self, tmp_path):
        content = {
            "version": "1",
            "skills": [
                {"name": "skill_a", "description": "A", "version": "1.0.0", "source": "local"},
                {"name": "skill_b", "description": "B", "version": "2.0.0", "source": "local"},
            ],
        }
        index_path = _make_index(tmp_path, content)
        index = RegistryIndex(index_path)
        names = [e.name for e in index.list_entries()]
        assert "skill_a" in names
        assert "skill_b" in names

    def test_empty_skills_list(self, tmp_path):
        content = {"version": "1", "skills": []}
        index_path = _make_index(tmp_path, content)
        index = RegistryIndex(index_path)
        assert index.list_entries() == []

    def test_index_file_not_found_raises(self, tmp_path):
        missing = tmp_path / "no-such-file.yaml"
        with pytest.raises(FileNotFoundError):
            RegistryIndex(missing).list_entries()

    def test_invalid_yaml_raises_value_error(self, tmp_path):
        bad_yaml = tmp_path / "registry-index.yaml"
        bad_yaml.write_text("{unclosed: [bracket", encoding="utf-8")
        with pytest.raises(ValueError, match="Failed to parse"):
            RegistryIndex(bad_yaml).list_entries()

    def test_missing_version_field_raises_value_error(self, tmp_path):
        content = {"skills": []}  # missing 'version'
        index_path = _make_index(tmp_path, content)
        with pytest.raises(ValueError, match="version"):
            RegistryIndex(index_path).list_entries()

    def test_unsupported_version_raises_value_error(self, tmp_path):
        content = {"version": "99", "skills": []}
        index_path = _make_index(tmp_path, content)
        with pytest.raises(ValueError, match="Unsupported"):
            RegistryIndex(index_path).list_entries()


# ─── RegistryIndex – get_entry ────────────────────────────────────────────────


class TestRegistryIndexGetEntry:
    def test_get_existing_entry(self, tmp_path):
        content = {
            "version": "1",
            "skills": [
                {"name": "target", "description": "T", "version": "1.0.0", "source": "local"},
            ],
        }
        index_path = _make_index(tmp_path, content)
        index = RegistryIndex(index_path)
        entry = index.get_entry("target")
        assert entry is not None
        assert entry.name == "target"

    def test_get_missing_entry_returns_none(self, tmp_path):
        content = {"version": "1", "skills": []}
        index_path = _make_index(tmp_path, content)
        index = RegistryIndex(index_path)
        assert index.get_entry("nonexistent") is None


# ─── RegistryIndex – path resolution ─────────────────────────────────────────


class TestRegistryIndexPathResolution:
    def test_absolute_path_preserved(self, tmp_path):
        skill_dir = _make_skill_dir(tmp_path, "abs_skill")
        content = {
            "version": "1",
            "skills": [
                {
                    "name": "abs_skill",
                    "description": "Abs",
                    "version": "0.1.0",
                    "source": "local",
                    "path": str(skill_dir),
                }
            ],
        }
        index_path = _make_index(tmp_path, content)
        index = RegistryIndex(index_path)
        entry = index.get_entry("abs_skill")
        assert entry is not None
        assert entry.path == skill_dir

    def test_relative_path_resolved_from_index_dir(self, tmp_path):
        skill_dir = tmp_path / "skills" / "rel_skill"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "skill.yaml").write_text(
            yaml.dump({
                "name": "rel_skill",
                "description": "Rel",
                "version": "0.1.0",
                "input_type": "application/json",
                "output_type": "text/markdown",
                "risk_level": "low",
            }),
            encoding="utf-8",
        )
        content = {
            "version": "1",
            "skills": [
                {
                    "name": "rel_skill",
                    "description": "Rel",
                    "version": "0.1.0",
                    "source": "local",
                    "path": "skills/rel_skill",
                }
            ],
        }
        index_path = _make_index(tmp_path, content)
        index = RegistryIndex(index_path)
        entry = index.get_entry("rel_skill")
        assert entry is not None
        assert entry.path is not None
        assert entry.path.is_dir()

    def test_entry_without_path_has_none_path(self, tmp_path):
        content = {
            "version": "1",
            "skills": [
                {
                    "name": "no_path_skill",
                    "description": "No path",
                    "version": "0.1.0",
                    "source": "local",
                }
            ],
        }
        index_path = _make_index(tmp_path, content)
        index = RegistryIndex(index_path)
        entry = index.get_entry("no_path_skill")
        assert entry is not None
        assert entry.path is None


# ─── RegistryIndex – to_skill_registry ───────────────────────────────────────


class TestRegistryIndexToSkillRegistry:
    def test_to_skill_registry_returns_registry(self, tmp_path):
        """to_skill_registry() produces a SkillRegistry with the indexed skills."""
        from singleclaw.skills.registry import SkillRegistry

        skill_dir = _make_skill_dir(tmp_path, "indexed_skill")
        content = {
            "version": "1",
            "skills": [
                {
                    "name": "indexed_skill",
                    "description": "Indexed",
                    "version": "0.1.0",
                    "source": "local",
                    "path": str(skill_dir),
                }
            ],
        }
        index_path = _make_index(tmp_path, content)
        index = RegistryIndex(index_path)
        registry = index.to_skill_registry()
        assert isinstance(registry, SkillRegistry)
        assert registry.get("indexed_skill") is not None

    def test_to_skill_registry_skips_missing_paths(self, tmp_path):
        """Entries without a valid path are skipped when building a registry."""
        content = {
            "version": "1",
            "skills": [
                {
                    "name": "ghost",
                    "description": "Gone",
                    "version": "0.1.0",
                    "source": "local",
                    "path": str(tmp_path / "nonexistent"),
                }
            ],
        }
        index_path = _make_index(tmp_path, content)
        index = RegistryIndex(index_path)
        registry = index.to_skill_registry()
        assert registry.get("ghost") is None
