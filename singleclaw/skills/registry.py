"""Skill Registry – discover and load skills from the ``/skills`` directory.

Skills are defined as directories containing a ``skill.yaml`` metadata file.
The registry scans the skills root, validates each manifest, and provides a
simple ``get()`` / ``list_all()`` API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


# Required keys that every skill.yaml must provide.
_REQUIRED_KEYS = {"name", "description", "version", "input_type", "output_type", "risk_level"}


@dataclass
class Skill:
    """A discovered and validated skill.

    Attributes:
        name:       Unique skill identifier (matches the directory name).
        path:       Absolute path to the skill directory.
        metadata:   Parsed content of ``skill.yaml``.
        errors:     Validation error messages, if any.
    """

    name: str
    path: Path
    metadata: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Return ``True`` when the skill has no validation errors."""
        return len(self.errors) == 0


class SkillRegistry:
    """Discover and cache skills from the skills root directory.

    Args:
        skills_root: Path to the top-level ``skills/`` directory.  Defaults to
                     ``skills/`` relative to the current working directory.
    """

    SKILL_YAML = "skill.yaml"

    def __init__(self, skills_root: Optional[Path] = None) -> None:
        if skills_root is None:
            # Try project root relative to this file first, then cwd.
            candidate = Path(__file__).resolve().parent.parent.parent / "skills"
            skills_root = candidate if candidate.is_dir() else Path.cwd() / "skills"
        self._root = Path(skills_root)
        self._skills: Optional[dict[str, Skill]] = None  # lazy load

    # ─── public API ──────────────────────────────────────────────────────────

    def list_all(self) -> list[Skill]:
        """Return all discovered skills (valid and invalid)."""
        return list(self._load().values())

    def list_valid(self) -> list[Skill]:
        """Return only skills that passed validation."""
        return [s for s in self._load().values() if s.is_valid]

    def get(self, name: str) -> Optional[Skill]:
        """Return the skill with the given name, or ``None`` if not found.

        Args:
            name: Skill directory name / ``name`` field in ``skill.yaml``.
        """
        return self._load().get(name)

    # ─── internals ───────────────────────────────────────────────────────────

    def _load(self) -> dict[str, Skill]:
        if self._skills is not None:
            return self._skills

        self._skills = {}
        if not self._root.is_dir():
            return self._skills

        for skill_dir in sorted(self._root.iterdir()):
            if not skill_dir.is_dir():
                continue
            yaml_path = skill_dir / self.SKILL_YAML
            if not yaml_path.exists():
                continue
            skill = self._load_skill(skill_dir, yaml_path)
            self._skills[skill.name] = skill

        return self._skills

    def _load_skill(self, skill_dir: Path, yaml_path: Path) -> Skill:
        """Parse a skill directory and return a ``Skill`` object."""
        errors: list[str] = []
        metadata: dict = {}

        try:
            with yaml_path.open("r", encoding="utf-8") as fh:
                metadata = yaml.safe_load(fh) or {}
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Failed to parse skill.yaml: {exc}")
            return Skill(name=skill_dir.name, path=skill_dir, metadata={}, errors=errors)

        missing = _REQUIRED_KEYS - set(metadata.keys())
        if missing:
            errors.append(f"Missing required fields: {sorted(missing)}")

        name = metadata.get("name", skill_dir.name)
        return Skill(name=name, path=skill_dir, metadata=metadata, errors=errors)
