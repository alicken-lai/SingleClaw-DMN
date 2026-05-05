"""Skill Registry – discover and load skills from the ``/skills`` directory.

Skills are defined as directories containing a ``skill.yaml`` metadata file.
The registry scans the skills root, validates each manifest, and provides a
simple ``get()`` / ``list_all()`` API.

Guidance skills are SKILL.md-only templates found in category subdirectories
(e.g. ``skills/engineering/tdd/SKILL.md``).  They are discoverable via
``list_guidance()`` / ``get_guidance()`` but cannot be ``run``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from importlib.metadata import entry_points
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


@dataclass
class GuidanceSkill:
    """A SKILL.md-only guidance template (cannot be ``run``).

    Attributes:
        name:     Directory name of the skill (e.g. ``tdd``).
        path:     Absolute path to the skill directory.
        skill_md: Absolute path to the ``SKILL.md`` file.
        category: Top-level category under ``skills/`` (e.g. ``engineering``).
    """

    name: str
    path: Path
    skill_md: Path
    category: str


class SkillRegistry:
    """Discover and cache skills from the skills root directory.

    In addition to the local filesystem, skills installed as Python packages
    that declare an entry-point under the ``singleclaw.skills`` group are also
    discovered.  Each such entry-point's ``load()`` must return a :class:`Path`
    pointing to a skill directory (or a zero-argument callable that returns
    one).

    Args:
        skills_root: Path to the top-level ``skills/`` directory.  Defaults to
                     ``skills/`` relative to the current working directory.
    """

    SKILL_YAML = "skill.yaml"
    SKILL_MD = "SKILL.md"
    #: Entry-point group used by third-party skill packages.
    ENTRY_POINT_GROUP = "singleclaw.skills"

    def __init__(self, skills_root: Optional[Path] = None) -> None:
        if skills_root is None:
            # Allow environment override (useful for tests and custom deployments).
            env_root = os.environ.get("SINGLECLAW_SKILLS_ROOT", "").strip()
            if env_root:
                skills_root = Path(env_root)
            else:
                # Try project root relative to this file first, then cwd.
                candidate = Path(__file__).resolve().parent.parent.parent / "skills"
                skills_root = candidate if candidate.is_dir() else Path.cwd() / "skills"
        self._root = Path(skills_root)
        self._skills: Optional[dict[str, Skill]] = None  # lazy load
        self._guidance: Optional[dict[str, GuidanceSkill]] = None  # lazy load

    @classmethod
    def _from_prebuilt(cls, skills: dict[str, "Skill"]) -> "SkillRegistry":
        """Create a registry pre-populated with the given skill map.

        Intended for use by :class:`~singleclaw.skills.registry_index.RegistryIndex`
        and tests.  The returned registry will not scan the filesystem.

        Args:
            skills: Mapping of skill name → :class:`Skill` instance.
        """
        inst = cls.__new__(cls)
        inst._root = Path("/dev/null")
        inst._skills = dict(skills)
        inst._guidance = {}
        return inst

    # ─── public API – runnable skills ────────────────────────────────────────

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

    # ─── public API – guidance skills ────────────────────────────────────────

    def list_guidance(self) -> list[GuidanceSkill]:
        """Return all discovered guidance skills (SKILL.md-only)."""
        return list(self._load_guidance().values())

    def get_guidance(self, name: str) -> Optional[GuidanceSkill]:
        """Return the guidance skill with the given name, or ``None``.

        Args:
            name: Directory name of the guidance skill (e.g. ``tdd``).
        """
        return self._load_guidance().get(name)

    # ─── internals – runnable skills ─────────────────────────────────────────

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

        # Merge skills discovered via installed package entry-points.
        for skill in self._load_entry_point_skills():
            # Filesystem skills take precedence over entry-point skills.
            if skill.name not in self._skills:
                self._skills[skill.name] = skill

        return self._skills

    def _load_entry_point_skills(self) -> list[Skill]:
        """Discover skills declared via the ``singleclaw.skills`` entry-point group.

        Each entry-point's ``load()`` should return a :class:`~pathlib.Path`
        to a skill directory, or a zero-argument callable that returns one.
        Malformed or unresolvable entry-points are silently skipped.
        """
        discovered: list[Skill] = []
        try:
            eps = entry_points(group=self.ENTRY_POINT_GROUP)
        except Exception:  # noqa: BLE001
            return discovered

        for ep in eps:
            try:
                value = ep.load()
                if callable(value) and not isinstance(value, Path):
                    skill_dir = Path(value())
                else:
                    skill_dir = Path(value)
                if not skill_dir.is_dir():
                    continue
                yaml_path = skill_dir / self.SKILL_YAML
                if not yaml_path.exists():
                    continue
                skill = self._load_skill(skill_dir, yaml_path)
                discovered.append(skill)
            except Exception:  # noqa: BLE001
                continue

        return discovered

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

    # ─── internals – guidance skills ─────────────────────────────────────────

    def _load_guidance(self) -> dict[str, GuidanceSkill]:
        if self._guidance is not None:
            return self._guidance

        self._guidance = {}
        if not self._root.is_dir():
            return self._guidance

        for md_path in sorted(self._root.rglob(self.SKILL_MD)):
            skill_dir = md_path.parent
            try:
                rel = skill_dir.relative_to(self._root)
                parts = rel.parts
            except ValueError:
                continue
            # Require exactly two levels: <category>/<skill-name>
            if len(parts) < 2:
                continue
            category = parts[0]
            name = parts[-1]
            self._guidance[name] = GuidanceSkill(
                name=name,
                path=skill_dir,
                skill_md=md_path,
                category=category,
            )

        return self._guidance
