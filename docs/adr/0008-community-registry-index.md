# ADR 0008 – Community Registry Index Format

**Status:** Accepted  
**Date:** 2026-05-05  
**Deciders:** @alicken-lai

---

## Context

v0.4 introduced `SkillValidator` (JSON Schema validation), `singleclaw skills list`,
and `singleclaw skills validate`.  ADR 0007 deferred the community registry
design to a follow-on decision.

As the skill library grows, users need a lightweight mechanism to:

1. **Catalog** a curated set of available skills with their metadata in a
   single file without connecting to the internet.
2. **Reference** local skill directories or installed packages from one
   central index.
3. **Bootstrap** a `SkillRegistry` from that index without scanning multiple
   directory trees.

The design must be **local-only** in this iteration.  Remote registry
protocols (e.g. a PyPI-style index endpoint) are explicitly out of scope and
will be addressed in a future ADR.

---

## Decision

### 1. File format – `registry-index.yaml`

The community registry index is a YAML file, conventionally named
`registry-index.yaml`.  Its schema is versioned; v1 is specified below.

```yaml
version: "1"           # required; only "1" is supported in this iteration
skills:
  - name: my_skill           # required: matches skill.yaml → name
    description: "What it does"  # required: human-readable summary
    version: "0.1.0"         # required: semver
    source: local            # required: "local" | "installed"
    path: ./skills/my_skill  # optional: relative or absolute path to skill dir
```

**Field definitions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | ✓ | Schema version; must be `"1"` |
| `skills` | list | ✓ | Ordered list of skill entries |
| `skills[].name` | string | ✓ | Skill identifier (matches `skill.yaml` name) |
| `skills[].description` | string | ✓ | One-line description |
| `skills[].version` | string | ✓ | Semver |
| `skills[].source` | string | ✓ | `"local"` (file system) or `"installed"` (pip) |
| `skills[].path` | string | – | Path to skill directory; relative paths are resolved from the index file's parent directory |

**Relative path resolution:**  A `path` value of `./skills/my_skill` in a
file at `/workspace/registry-index.yaml` resolves to
`/workspace/skills/my_skill`.

**Entries without `path`:**  Allowed (e.g. for cataloging installed packages
that are discovered through entry-points).  Such entries appear in the index
listing but cannot contribute to a `SkillRegistry` via `to_skill_registry()`.

### 2. `RegistryIndex` – Python reader

A new module `singleclaw/skills/registry_index.py` exposes:

```
RegistryEntry      – dataclass: name, description, version, source, path
RegistryIndex      – reads registry-index.yaml
    .list_entries() -> list[RegistryEntry]
    .get_entry(name) -> Optional[RegistryEntry]
    .to_skill_registry() -> SkillRegistry
```

`to_skill_registry()` builds a `SkillRegistry` from all entries that have
a resolvable local `path` with an existing `skill.yaml`.  Entries without a
path or with a missing path are silently skipped.

**Error handling:**

| Condition | Raised |
|-----------|--------|
| File not found | `FileNotFoundError` |
| Unparseable YAML | `ValueError("Failed to parse …")` |
| Missing `version` field | `ValueError("… missing required 'version' …")` |
| Unsupported version | `ValueError("Unsupported …")` |

### 3. Schema versioning

The `version` field enables forward-compatible evolution:

- `"1"` – the format defined in this ADR.
- Future versions may add fields or restructure entries.
- `RegistryIndex` raises `ValueError` for any version it does not recognise,
  so old readers fail loudly rather than silently misparse new schemas.

### 4. `SkillRegistry._from_prebuilt` – internal factory

To let `RegistryIndex.to_skill_registry()` return a genuine `SkillRegistry`
instance (rather than a duck-typed look-alike), a private class method
`SkillRegistry._from_prebuilt(skills: dict[str, Skill]) -> SkillRegistry` is
added.  It bypasses filesystem scanning and pre-populates the internal skill
map.  This method is intentionally private (`_` prefix); external callers
should use `RegistryIndex.to_skill_registry()`.

---

## Consequences

**Positive:**
- A single YAML file can describe all skills available to a project or team,
  serving as a human-readable manifest.
- `RegistryIndex` is independently testable; no network access is required.
- The `version` field makes forward-compatible schema evolution safe.
- `to_skill_registry()` returns a genuine `SkillRegistry`, so all existing
  CLI commands (`skills list`, `skills validate`, `run`) work without
  modification against an index-built registry.

**Negative / Trade-offs:**
- `registry-index.yaml` files must be maintained manually in this iteration
  (no auto-generation tool yet).
- Entries with `source: installed` and no `path` are informational only; they
  do not contribute skills to a registry unless the package is also registered
  via the `singleclaw.skills` entry-point group (ADR 0007 §3 /
  `docs/skill-packaging.md`).

**Future work (not in scope):**
- Remote index endpoint (HTTP GET returning `registry-index.yaml`).
- `singleclaw registry add <url>` / `singleclaw registry sync` CLI commands.
- Lock-file format for reproducible skill versions.

**Architecture invariants preserved:**
- No destructive action is involved; Guardian policy is not triggered.
- `SkillRegistry` remains the sole runtime registry abstraction; `RegistryIndex`
  is a data-loader that produces one.
