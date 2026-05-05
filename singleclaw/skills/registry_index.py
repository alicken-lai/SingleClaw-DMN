"""Community Registry Index – load a local ``registry-index.yaml`` catalog.

A ``registry-index.yaml`` file lists skill entries that are available for
installation or direct use.  It is a **local** catalog only; no network
requests are made.

Schema (v1)::

    version: "1"
    skills:
      - name: my_skill
        description: "What it does"
        version: "0.1.0"
        source: local            # "local" | "installed"
        path: /path/to/skill/dir # absolute or relative to this file (optional)

Relative ``path`` values are resolved relative to the directory that contains
the ``registry-index.yaml`` file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


# Supported schema versions.
_SUPPORTED_VERSIONS = {"1"}


@dataclass
class RegistryEntry:
    """A single entry in a community registry index.

    Attributes:
        name:        Skill identifier (matches the ``name`` field in ``skill.yaml``).
        description: Short human-readable description.
        version:     Semver version string (e.g. ``"0.1.0"``).
        source:      Origin of the skill – ``"local"`` or ``"installed"``.
        path:        Resolved absolute path to the skill directory, or ``None``
                     when no ``path`` was declared.
    """

    name: str
    description: str
    version: str
    source: str
    path: Optional[Path] = field(default=None)


class RegistryIndex:
    """Read a ``registry-index.yaml`` catalog file.

    Args:
        index_path: Path to the ``registry-index.yaml`` file.
    """

    def __init__(self, index_path: Path) -> None:
        self._path = Path(index_path)
        self._entries: Optional[list[RegistryEntry]] = None  # lazy

    # ─── public API ───────────────────────────────────────────────────────────

    def list_entries(self) -> list[RegistryEntry]:
        """Return all skill entries declared in the index.

        Raises:
            FileNotFoundError: When the index file does not exist.
            ValueError:        When the file cannot be parsed or uses an
                               unsupported schema version.
        """
        return list(self._load())

    def get_entry(self, name: str) -> Optional[RegistryEntry]:
        """Return the entry with the given *name*, or ``None`` if not found.

        Args:
            name: Skill name to look up.

        Raises:
            FileNotFoundError: When the index file does not exist.
            ValueError:        When the file cannot be parsed.
        """
        for entry in self._load():
            if entry.name == name:
                return entry
        return None

    def to_skill_registry(self) -> "SkillRegistry":  # type: ignore[name-defined]  # noqa: F821
        """Build a :class:`~singleclaw.skills.registry.SkillRegistry` from
        indexed entries that have resolvable local paths.

        Entries without a ``path``, or whose ``path`` does not exist, are
        silently skipped.

        Returns:
            A :class:`~singleclaw.skills.registry.SkillRegistry` instance
            backed by the indexed skill directories.
        """
        from singleclaw.skills.registry import SkillRegistry

        helper = SkillRegistry.__new__(SkillRegistry)
        skills: dict = {}
        for entry in self._load():
            if entry.path is None or not entry.path.is_dir():
                continue
            yaml_path = entry.path / SkillRegistry.SKILL_YAML
            if not yaml_path.exists():
                continue
            skill = helper._load_skill(entry.path, yaml_path)
            skills[skill.name] = skill
        return SkillRegistry._from_prebuilt(skills)

    # ─── internals ────────────────────────────────────────────────────────────

    def _load(self) -> list[RegistryEntry]:
        """Parse the index file (once) and return the entries list."""
        if self._entries is not None:
            return self._entries

        if not self._path.exists():
            raise FileNotFoundError(
                f"Registry index not found: {self._path}"
            )

        try:
            with self._path.open("r", encoding="utf-8") as fh:
                raw = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            raise ValueError(f"Failed to parse registry index: {exc}") from exc

        if not isinstance(raw, dict):
            raise ValueError(
                f"Failed to parse registry index: expected a YAML mapping, got {type(raw).__name__}"
            )

        version = str(raw.get("version", "")).strip()
        if not version:
            raise ValueError(
                "Registry index is missing required 'version' field."
            )
        if version not in _SUPPORTED_VERSIONS:
            raise ValueError(
                f"Unsupported registry index version: {version!r}. "
                f"Supported: {sorted(_SUPPORTED_VERSIONS)}"
            )

        skills_raw = raw.get("skills") or []
        index_dir = self._path.parent
        self._entries = [self._parse_entry(item, index_dir) for item in skills_raw]
        return self._entries

    @staticmethod
    def _parse_entry(item: dict, index_dir: Path) -> RegistryEntry:
        """Parse a single skills list item into a :class:`RegistryEntry`."""
        name = str(item.get("name", ""))
        description = str(item.get("description", ""))
        version = str(item.get("version", ""))
        source = str(item.get("source", "local"))

        raw_path = item.get("path")
        resolved: Optional[Path] = None
        if raw_path is not None:
            p = Path(str(raw_path))
            resolved = p if p.is_absolute() else (index_dir / p).resolve()

        return RegistryEntry(
            name=name,
            description=description,
            version=version,
            source=source,
            path=resolved,
        )
