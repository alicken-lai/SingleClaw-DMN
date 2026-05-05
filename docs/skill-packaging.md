# Skill Packaging Specification

> **Version:** 1.0  
> **Applies to:** SingleClaw DMN v0.4+

This document defines how a SingleClaw skill is packaged for distribution and
how the runtime discovers skills that are installed as Python packages.

---

## 1. What is a Skill Package?

A **skill package** is a standard Python wheel (`.whl`) or source distribution
that:

1. Bundles one or more skill directories under a Python module.
2. Declares each bundled skill in `pyproject.toml` under the
   `singleclaw.skills` entry-points group.
3. Follows the directory layout and `skill.yaml` schema described below.

Skill packages are installed with `pip install` just like any other Python
package and are automatically discovered by `SkillRegistry` without any
configuration.

---

## 2. Skill Directory Layout

Every runnable skill lives in its own directory.  The following files are
recognised by the runtime:

```
my_skill_name/
├── skill.yaml          ← required: metadata manifest
├── prompt.md           ← recommended: LLM prompt template
└── examples/
    └── README.md       ← recommended: sample inputs and expected outputs
```

### 2.1 `skill.yaml` – Required Fields

```yaml
name: my_skill_name          # must match the entry-point key (see §4)
description: >
  One-paragraph description of what the skill does.
version: "0.1.0"             # semver
author: Your Name
input_type: application/json # MIME-style hint
output_type: text/markdown   # MIME-style hint
risk_level: low              # low | medium | high | critical
tags:
  - tag1
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✓ | Unique identifier; must match entry-point key |
| `description` | string | ✓ | Human-readable purpose |
| `version` | string | ✓ | Semver (e.g. `"0.1.0"`) |
| `input_type` | string | ✓ | MIME-style input type hint |
| `output_type` | string | ✓ | MIME-style output type hint |
| `risk_level` | string | ✓ | Guardian risk level |
| `author` | string | – | Skill author name |
| `tags` | list[string] | – | Searchable tags |
| `input_schema` | JSON Schema | – | Draft 7 schema for input validation |
| `output_schema` | JSON Schema | – | Draft 7 schema for output validation |
| `prompt_template` | string | – | Inline Jinja2 / f-string prompt template |

### 2.2 JSON Schema Fields (v0.4+)

`input_schema` and `output_schema` are optional inline JSON Schema Draft 7
objects.  When present they are validated by `SkillValidator` before LLM
execution:

```yaml
input_schema:
  type: object
  required: [title, body]
  properties:
    title: { type: string }
    body:  { type: string }

output_schema:
  type: object
  required: [summary]
  properties:
    summary: { type: string }
```

---

## 3. Python Package Layout

A skill package is a normal Python package with the skill directories nested
under it:

```
my_skills_package/
├── pyproject.toml
├── README.md
└── my_skills_package/
    ├── __init__.py
    ├── skills/
    │   ├── __init__.py
    │   ├── summarise/
    │   │   ├── skill.yaml
    │   │   └── prompt.md
    │   └── translate/
    │       ├── skill.yaml
    │       └── prompt.md
    └── _skill_paths.py    ← helper that exposes skill directory paths
```

### 3.1 `_skill_paths.py` – Path Helpers

Each skill that is declared in `pyproject.toml` must be reachable via a
zero-argument callable (or a `Path` object) returned by the entry-point's
`load()`.  A simple helper module avoids repetition:

```python
# my_skills_package/_skill_paths.py
from pathlib import Path

_SKILLS_DIR = Path(__file__).parent / "skills"

def summarise_path() -> Path:
    return _SKILLS_DIR / "summarise"

def translate_path() -> Path:
    return _SKILLS_DIR / "translate"
```

---

## 4. `pyproject.toml` Entry-Point Convention

Declare each skill under the `[project.entry-points."singleclaw.skills"]`
table:

```toml
[project.entry-points."singleclaw.skills"]
summarise = "my_skills_package._skill_paths:summarise_path"
translate  = "my_skills_package._skill_paths:translate_path"
```

**Key** – the entry-point name must match the `name` field in `skill.yaml`.

**Value** – a dotted Python import path to a callable that takes no arguments
and returns a `pathlib.Path` pointing to the skill directory.  Alternatively,
the value may point directly to a `Path` attribute (not a function):

```python
# my_skills_package/_skill_paths.py
from pathlib import Path

SUMMARISE_PATH: Path = Path(__file__).parent / "skills" / "summarise"
```

```toml
[project.entry-points."singleclaw.skills"]
summarise = "my_skills_package._skill_paths:SUMMARISE_PATH"
```

Both forms are supported; `SkillRegistry` calls `ep.load()` and, if the result
is callable, invokes it to obtain the final `Path`.

---

## 5. Discovery by `SkillRegistry`

`SkillRegistry` merges skills from two sources on first access:

| Source | Priority |
|--------|----------|
| Filesystem (`skills/` directory) | High (wins on name conflict) |
| Installed entry-points | Low (skipped when name already exists) |

Discovery logic (simplified):

```python
from importlib.metadata import entry_points

eps = entry_points(group="singleclaw.skills")
for ep in eps:
    value = ep.load()
    skill_dir = value() if callable(value) else Path(value)
    if skill_dir.is_dir():
        skill = registry._load_skill(skill_dir, skill_dir / "skill.yaml")
        # merged into registry
```

Entry-points that fail to load (import errors, non-existent paths, missing
`skill.yaml`) are **silently skipped** so that a broken third-party package
does not prevent the rest of the skills from loading.

---

## 6. Installing a Skill Package

```bash
# From PyPI
pip install my-skills-package

# From a local directory
pip install ./path/to/my_skills_package

# From a Git repository
pip install git+https://github.com/example/my-skills-package.git
```

After installation, the new skills appear immediately in:

```bash
singleclaw skills list
```

---

## 7. Creating a New Skill Package (Checklist)

- [ ] Create a Python package directory with `pyproject.toml`
- [ ] Add one or more skill directories under the package (each with `skill.yaml`)
- [ ] Write `_skill_paths.py` with a path helper function for each skill
- [ ] Declare each skill in `[project.entry-points."singleclaw.skills"]`
- [ ] Validate with `singleclaw skills validate <skill_name>` after install
- [ ] Publish to PyPI with `python -m build && twine upload dist/*`

---

## 8. Risk Levels

| Level | When to use |
|-------|-------------|
| `low` | Read-only; no external side effects; reversible |
| `medium` | Creates local files or calls read-only external APIs |
| `high` | Modifies existing files or calls external write APIs |
| `critical` | Irreversible; requires explicit human confirmation |

Guardian enforces these levels.  Never use a level lower than the true risk of
the skill.
