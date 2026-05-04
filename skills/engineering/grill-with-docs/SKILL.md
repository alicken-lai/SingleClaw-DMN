# Skill: grill-with-docs

**Category:** engineering  
**Discipline:** Domain Clarification Before Coding  
**Inspired by:** Matt Pocock's engineering-skills

---

## Purpose

Use this skill before implementing any new concept, domain entity, or
integration.  It prevents building the wrong thing by forcing domain questions
to the surface before a line of production code is written.

---

## When to Apply

- You are adding a new concept that does not already exist in `CONTEXT.md`.
- You are unsure how a new feature fits into the existing domain model.
- A user request contains ambiguous terminology (e.g. "memory" could mean
  `MemoryStore`, a future semantic index, or something else entirely).
- You are about to introduce a new external dependency.

---

## Protocol

### Step 1 – Read the existing docs

Before asking any questions, read:

1. `CONTEXT.md` – project context and domain model.
2. `docs/architecture.md` – system design and data flow.
3. Any relevant existing ADR in `docs/adr/`.
4. The relevant Python module(s) in `singleclaw/`.

### Step 2 – Identify what is unclear

Write a list of questions in this format:

```
Q1: [concept] – What exactly is X?  Is it <option A> or <option B>?
Q2: [boundary] – Where does responsibility for Y end?
Q3: [constraint] – Are there any constraints on Z that aren't in the docs?
```

### Step 3 – Ask the user (or the codebase)

- If the answer is in the code, find it yourself.
- If the answer requires a human decision, ask the user – do not assume.
- Phrase each question as a binary or multiple-choice when possible to
  minimise back-and-forth.

### Step 4 – Update the docs

Once the questions are answered:

1. Update `CONTEXT.md` if the domain model is now clearer.
2. If a new architectural decision was made, write an ADR in `docs/adr/`.
3. Only then proceed to implementation.

---

## Checklist

- [ ] `CONTEXT.md` read before any code written.
- [ ] All ambiguous concepts listed as explicit questions.
- [ ] Questions answered (by code reading or user confirmation).
- [ ] `CONTEXT.md` and/or ADR updated to reflect the new understanding.
- [ ] Implementation not started until Step 4 is complete.

---

## Example Questions for SingleClaw DMN

When adding a new skill:
- Is this skill stateless (no memory reads/writes) or stateful?
- What is the expected `risk_level` and why?
- Does it need Guardian approval?

When adding a memory feature:
- Does this add new fields to `memory.jsonl` records?  If so, what is the migration strategy for existing records?
- Should this be recency-based or tag-based retrieval?
