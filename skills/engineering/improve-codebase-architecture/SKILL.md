# Skill: improve-codebase-architecture

**Category:** engineering  
**Discipline:** Architecture Inspection Before Feature Addition  
**Inspired by:** Matt Pocock's engineering-skills

---

## Purpose

Use this skill before adding any new subsystem, cross-cutting concern, or
significant change to the module boundaries of SingleClaw DMN.  It prevents
architectural drift by making structural decisions explicit and auditable.

---

## When to Apply

- Adding a new top-level module under `singleclaw/` (e.g. `singleclaw/llm/`).
- Changing how skills are discovered, validated, or executed.
- Modifying the Guardian contract or risk classification approach.
- Introducing a new storage format or external dependency.
- Refactoring a module that is imported by more than two other modules.

**Do not apply** to: adding a new skill template (`skill.yaml` + Markdown), fixing
a bug inside an existing function, updating documentation.

---

## Protocol

### Step 1 – Map the current architecture

Before proposing any change:

1. Read `docs/architecture.md` and `CONTEXT.md`.
2. Draw (or describe in text) the current module dependency graph:
   - Which modules import which?
   - Which modules touch the file system?
   - Which modules are on the call path for every CLI command?
3. Identify the module(s) the proposed change would touch.

### Step 2 – Identify the architectural concern

State the concern in one sentence:

> "I am adding `singleclaw/llm/` which will be called by `SkillRunner` and will
> need access to `MemoryStore` context.  This introduces a new dependency edge
> from `skills/runner.py` → `llm/` → `dmn/memory.py`."

### Step 3 – Evaluate options

List at least two structural options and their trade-offs:

| Option | Pros | Cons |
|--------|------|------|
| A | … | … |
| B | … | … |

### Step 4 – Write an ADR

If the decision is non-trivial (affects more than one module or cannot easily
be reversed), write an ADR in `docs/adr/` **before writing any code**.

Use the next sequential number: check `docs/adr/` for the highest existing number.

### Step 5 – Implement

Only after the ADR is written (or the change is confirmed trivial):

1. Make the structural change.
2. Update `docs/architecture.md` to reflect the new module layout.
3. Update `CONTEXT.md` if the domain model table needs a new row.

---

## Checklist

- [ ] `docs/architecture.md` read before any code written.
- [ ] Current dependency graph understood.
- [ ] Architectural concern stated in one sentence.
- [ ] At least two options evaluated.
- [ ] ADR written if the decision is non-trivial.
- [ ] `docs/architecture.md` updated after implementation.

---

## Key Architecture Invariants (do not violate without a new ADR)

1. `singleclaw/guardian/` must not import from `singleclaw/skills/`.
2. `singleclaw/dmn/` must not import from `singleclaw/guardian/` or `singleclaw/skills/`.
3. `singleclaw/cli.py` is the only module allowed to orchestrate across all subsystems.
4. The Guardian check must occur **before** `SkillRunner.execute()` on every code path.
