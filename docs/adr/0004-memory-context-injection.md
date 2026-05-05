# ADR 0004 – Memory Context Injection into Skill Execution

**Status:** Accepted  
**Date:** 2026-05-05  
**Deciders:** @alicken-lai

---

## Context

Skill execution in v0.1 is stateless: `SkillRunner.execute()` receives only the
skill definition and an input file.  It has no awareness of the DMN memory
accumulated across previous sessions.

When LLM integration lands in v0.2, skills will need relevant memory items
injected into their prompt templates so the agent can reason with accumulated
context (past decisions, user preferences, prior results).

Before v0.2 lands, the injection plumbing needs to be in place so that:
1. The CLI retrieves recent memory before running a skill.
2. `SkillRunner.execute()` accepts and surfaces the memory context.
3. The prompt template format (`{{memory_context}}`) is agreed before any LLM
   code is written.

---

## Decision

**Introduce `memory_context: list[dict] | None` as an optional parameter to
`SkillRunner.execute()`.**

1. **`singleclaw/cli.py` – `run` command** calls `MemoryStore.recent(n=5)` and
   passes the result as `memory_context` to every `SkillRunner.execute()` call.

2. **`singleclaw/skills/runner.py`** – `execute()` accepts `memory_context` and
   includes a summary in the result panel (v0.1 placeholder behaviour).  In v0.2
   this will be injected into the LLM prompt template as `{{memory_context}}`.

3. **Dependency edge** – `singleclaw/cli.py` already imports both `MemoryStore`
   and `SkillRunner`.  The new edge is `cli.py` → `MemoryStore` → passed to
   `SkillRunner`.  `SkillRunner` itself does **not** import `MemoryStore`; it
   receives context as a plain `list[dict]`.  This preserves the architecture
   invariant that `singleclaw/skills/` does not import from `singleclaw/dmn/`.

---

## Consequences

**Positive:**
- LLM prompt integration in v0.2 requires zero structural changes; only the
  placeholder rendering code in `runner.py` is replaced.
- The context is always passed through `cli.py`, keeping the orchestration
  responsibility in the single correct place.
- `SkillRunner` remains independently testable without a `MemoryStore`.

**Negative / Trade-offs:**
- `n=5` recent items is an arbitrary choice for v0.1.  It will be tuned (and
  likely replaced with semantic search) in v0.3.
- Memory context is not yet filtered by relevance; all recent items are passed
  regardless of topic.

**Architecture invariant preserved:**
- `singleclaw/skills/runner.py` must not import `singleclaw/dmn/`.
  Context is injected by the CLI orchestrator, not pulled by the runner.
