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
| `TaskJournal` | `singleclaw/dmn/journal.py` | Timestamped audit log of every CLI command; records optional `token_usage` |
| `reflect_on_memory` | `singleclaw/dmn/reflect.py` | Produces a Rich Markdown summary; supports `since` date filter |
| `GuardianPolicy` | `singleclaw/guardian/policy.py` | Classifies actions as ALLOW / REVIEW_REQUIRED / BLOCK |
| `RiskClassifier` | `singleclaw/guardian/risk.py` | Keyword-based risk inference (low/medium/high/critical) |
| `SkillRegistry` | `singleclaw/skills/registry.py` | Discovers runnable skills (`skill.yaml`) and guidance skills (`SKILL.md`) |
| `Skill` | `singleclaw/skills/registry.py` | A validated runnable skill (has `skill.yaml`) |
| `GuidanceSkill` | `singleclaw/skills/registry.py` | A SKILL.md-only guidance template (cannot be `run`) |
| `SkillRunner` | `singleclaw/skills/runner.py` | Executes a skill; accepts optional `memory_context` list and `llm_client` |
| `WorkspaceManager` | `singleclaw/workspace/manager.py` | Manages `.singleclaw/` local directory |
| `LLMClient` | `singleclaw/llm/client.py` | Protocol satisfied by all LLM provider implementations |
| `LLMConfig` | `singleclaw/llm/config.py` | Resolves auth mode (API key vs OAuth) from environment |
| `LLMClientFactory` | `singleclaw/llm/factory.py` | Instantiates the correct provider from a resolved `LLMConfig` |
| `OpenAIProvider` | `singleclaw/llm/providers/openai.py` | OpenAI Chat Completions API (API key) |
| `GoogleProvider` | `singleclaw/llm/providers/google.py` | Google Gemini API (API key or OAuth token) |
| `DeviceFlow` | `singleclaw/llm/auth/oauth_device.py` | OAuth 2.0 Device Authorization Grant (RFC 8628) |
| `TokenStore` | `singleclaw/llm/auth/token_store.py` | Persists OAuth tokens in `.singleclaw/auth_token.json` |
| `render_prompt` | `singleclaw/llm/prompt.py` | Renders a skill's `prompt_template` with input data and memory context |

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

## Current State (v0.3 ✅ Complete → v0.4 Next)

### v0.2 – LLM Integration (complete)
- CLI commands: `init`, `remember`, `run`, `reflect [--since DATE]`, `guardian-check`, `skill show`
- `auth login`, `auth logout`, `auth status` – OAuth Device Flow + API key auth
- Real LLM execution in `SkillRunner` via unified `LLMClient` protocol
  - Supports OpenAI (API key) and Google Gemini (API key or OAuth Device Flow)
  - Falls back gracefully to placeholder when no auth is configured
- `prompt_template` field in `skill.yaml` rendered via `singleclaw/llm/prompt.py`
- `singleclaw/llm/` subsystem: client, config, providers, auth, factory
- `TaskJournal.log()` accepts `token_usage` dict to track LLM costs
- Guardian policy is keyword-based; no LLM calls yet in Guardian itself
- `REVIEW_REQUIRED` actions show a dry-run preview and prompt `Proceed? [y/N]` interactively
- Guidance skills (`SKILL.md`-only) discoverable via `SkillRegistry.list_guidance()` / `get_guidance()`
- Streaming support in `OpenAIProvider` and `GoogleProvider`; not yet surfaced in CLI

### v0.3 – Memory Intelligence (complete)
- `MemorySearch` in `singleclaw/dmn/search.py`: TF-IDF cosine similarity over `MemoryStore`
- CLI `run` uses `MemorySearch.query(skill_description, top_k=5)` instead of `recent(n=5)` for relevance-ranked context injection
- `singleclaw memory list [--tag TAG]` – lists all memory items in Rich table; filters by tag
- `singleclaw memory search "query"` – relevance-ranked search with Rich table output
- `singleclaw memory export [--format markdown|json] [--output PATH]` – exports full store (read-only)
- `singleclaw memory archive --before DATE` – moves old records to `memory_archive.jsonl` (destructive; Guardian REVIEW_REQUIRED)

### v0.4 – Skill Ecosystem (next)
- Planned: `singleclaw skills validate`, `singleclaw skills list`
- Planned: input/output JSON Schema validation
- Planned: skill packaging spec and community registry

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
singleclaw/dmn/journal.py          ← Task journal (with token_usage)
singleclaw/guardian/policy.py      ← Guardian policy
singleclaw/skills/registry.py      ← Skill discovery
singleclaw/skills/runner.py        ← Skill execution (with LLM integration)
singleclaw/llm/                    ← LLM subsystem (v0.2)
singleclaw/llm/client.py           ← LLMClient protocol + LLMResponse
singleclaw/llm/config.py           ← Auth mode detection (API key / OAuth)
singleclaw/llm/factory.py          ← Build LLMClient from LLMConfig
singleclaw/llm/prompt.py           ← Prompt template rendering
singleclaw/llm/providers/openai.py ← OpenAI provider
singleclaw/llm/providers/google.py ← Google Gemini provider
singleclaw/llm/auth/api_key.py     ← API key reader
singleclaw/llm/auth/oauth_device.py← OAuth Device Flow (RFC 8628)
singleclaw/llm/auth/token_store.py ← Token persistence
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
