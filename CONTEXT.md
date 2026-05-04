# SingleClaw DMN – Project Context

> Read this file before touching any code.

---

## What is this project?

**SingleClaw DMN** is a single-agent personal AI work OS for knowledge workers and small teams.
It provides a reliable, auditable AI assistant without the complexity of multi-agent frameworks.

- **Single Agent** – one coherent loop: you → agent → skill → memory
- **DMN Memory** – persistent local memory across every session (JSONL-backed)
- **Skill Library** – reusable, composable task templates under `skills/`
- **Guardian Check** – rule-based safety layer; no destructive action without explicit review

Repository: <https://github.com/alicken-lai/SingleClaw-DMN>

---

## Domain Model

| Concept | Location | Role |
|---------|----------|------|
| `MemoryStore` | `singleclaw/dmn/memory.py` | Append-only JSONL store for persistent memory items |
| `TaskJournal` | `singleclaw/dmn/journal.py` | Timestamped audit log of every CLI command |
| `reflect_on_memory` | `singleclaw/dmn/reflect.py` | Produces a Rich Markdown summary of recent activity |
| `GuardianPolicy` | `singleclaw/guardian/policy.py` | Classifies actions as ALLOW / REVIEW_REQUIRED / BLOCK |
| `RiskClassifier` | `singleclaw/guardian/risk.py` | Keyword-based risk inference (low/medium/high/critical) |
| `SkillRegistry` | `singleclaw/skills/registry.py` | Discovers and validates skills under `skills/` |
| `SkillRunner` | `singleclaw/skills/runner.py` | Executes a skill (dry-run or real) |
| `WorkspaceManager` | `singleclaw/workspace/manager.py` | Manages `.singleclaw/` local directory |

---

## Technology Stack

| Layer | Choice |
|-------|--------|
| Language | Python ≥ 3.10 |
| CLI framework | [Typer](https://typer.tiangolo.com/) |
| Terminal output | [Rich](https://rich.readthedocs.io/) |
| Skill schemas | YAML (`skill.yaml`) + JSON Schema |
| Memory | Append-only JSONL files |
| Tests | pytest ≥ 8.0 |
| Linter | ruff |

---

## Current State (v0.1 – Foundation)

- CLI commands: `init`, `remember`, `run`, `reflect`, `guardian-check`
- Guardian policy is keyword-based; no LLM calls yet
- Skill runner returns a placeholder result (LLM integration is v0.2)
- No semantic memory search yet (v0.3)

---

## Development Disciplines (Matt Pocock skills)

This project uses Matt Pocock's engineering-skills approach:

| Skill | When to apply |
|-------|---------------|
| `grill-with-docs` | Clarify domain model **before** coding any new concept |
| `tdd` | Red → Green → Refactor for every new behaviour |
| `diagnose` | Reproduce → minimise → hypothesise → instrument → fix → regression-test |
| `improve-codebase-architecture` | Inspect architecture **before** adding new features |
| `to-issues` | Break plans into small, vertical GitHub issues |

See `skills/engineering/` for the local SKILL.md definitions.

---

## Guardian Contract

Every potentially destructive action **must** pass through `GuardianPolicy.check()`.
The policy is enforced in `singleclaw/cli.py` before any `SkillRunner.execute()` call.

Never bypass the Guardian. See `docs/adr/0002-guardian-before-destructive-actions.md`.

---

## Key Files

```
singleclaw/cli.py                  ← CLI entry point
singleclaw/dmn/memory.py           ← Memory store
singleclaw/dmn/journal.py          ← Task journal
singleclaw/guardian/policy.py      ← Guardian policy
singleclaw/skills/registry.py      ← Skill discovery
skills/                            ← Skill templates (data, not code)
docs/                              ← Architecture docs
docs/adr/                          ← Architecture Decision Records
skills/engineering/                ← Engineering discipline skills
```

---

## What to Do Before Coding

1. Re-read this file.
2. Check `docs/adr/` for any relevant decision.
3. If the change touches the Guardian or memory layer, open a GitHub issue first.
4. Write tests before implementation (TDD).
5. After completing the task, update `TaskJournal` / changelog if applicable.
