# ADR 0001 – Skill-Driven Agent Development

**Status:** Accepted  
**Date:** 2026-05-04  
**Deciders:** @alicken-lai

---

## Context

SingleClaw DMN needs a principled approach to adding new capabilities without
accumulating technical debt or shipping untested behaviour.  Ad-hoc feature
additions have historically led to inconsistent interfaces, untested edge cases,
and architectures that are hard to reason about.

Matt Pocock's [engineering-skills](https://github.com/mattpocock/skills) approach
defines a small set of reusable development disciplines that keep a codebase
healthy as it grows.  The same concept – a "skill" as a reusable, composable
template – maps directly onto SingleClaw DMN's own Skill Library.

---

## Decision

We adopt Matt Pocock's engineering-skills approach as the **mandatory development
discipline** for this project, implemented as local `SKILL.md` files under
`skills/engineering/`.

The disciplines adopted are:

| Skill | Trigger condition |
|-------|-------------------|
| `grill-with-docs` | Before implementing any new concept or domain entity |
| `tdd` | For every new externally observable behaviour |
| `diagnose` | For every bug report or unexpected regression |
| `improve-codebase-architecture` | Before adding a new subsystem or cross-cutting concern |
| `to-issues` | When a plan contains more than one logical slice of work |

All five skills are defined in `skills/engineering/<skill-name>/SKILL.md`.

---

## Consequences

**Positive:**
- Consistent, reproducible process for every code change.
- `grill-with-docs` prevents domain model drift before it starts.
- TDD ensures a regression test exists for every new behaviour.
- `diagnose` prevents shipping speculative fixes for bugs that aren't fully understood.
- Architecture ADRs provide an auditable record of design decisions.

**Negative / Trade-offs:**
- Small cosmetic changes still nominally require checking whether TDD applies
  (low overhead in practice – it usually doesn't).
- New contributors must read the skills before contributing.

**Neutral:**
- The SKILL.md files are Markdown-only; they add no runtime dependencies.
