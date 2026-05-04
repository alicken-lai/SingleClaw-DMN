# ADR 0002 – Guardian Check Before Every Destructive Action

**Status:** Accepted  
**Date:** 2026-05-04  
**Deciders:** @alicken-lai

---

## Context

SingleClaw DMN can invoke skills that write files, call external APIs, or execute
shell commands.  Without a centralised safety gate, a malformed skill definition
or unexpected input could cause irreversible damage (overwriting files, pushing
to git, deleting records).

The project already contains a `GuardianPolicy` class that classifies actions as
`ALLOW`, `REVIEW_REQUIRED`, or `BLOCK`.  However, there is no explicit architectural
rule enforcing *when* the Guardian must be invoked.

---

## Decision

**The Guardian check is mandatory before any action that could modify, delete, or
expose data outside the current read context.**

Concretely:

1. `singleclaw/cli.py` calls `GuardianPolicy.check()` before every `SkillRunner.execute()`.
2. Any future CLI command that writes, uploads, or deletes must also call the Guardian first.
3. Skills with `risk_level: high` or `risk_level: critical` are **blocked** by default;
   the user must explicitly acknowledge the risk (future `--force` flag or interactive prompt).
4. Copilot and contributors **must not** add code paths that skip the Guardian check.

The `skills/guardian/destructive-action-guard/SKILL.md` file documents the
step-by-step process for contributors adding new destructive capabilities.

---

## Consequences

**Positive:**
- All destructive actions are logged in `journal.jsonl` with a risk level.
- Dry-run previews are always available for medium-risk actions.
- The safety model is auditable and does not require LLM calls.

**Negative / Trade-offs:**
- Every new command requires a conscious risk classification decision.
- The keyword-based `RiskClassifier` will produce false negatives for novel
  action descriptions; this is acceptable for v0.1 and will be improved in v0.3.

**Neutral:**
- The Guardian is synchronous and adds negligible latency.
