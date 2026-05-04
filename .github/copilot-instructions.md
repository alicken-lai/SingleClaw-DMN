# Copilot Instructions – SingleClaw DMN

These rules are **mandatory** for GitHub Copilot and all AI coding assistants
working in this repository.  Follow them on every task, without exception.

---

## 1. Always Read Context First

Before writing any code, read `CONTEXT.md` in the repository root.
It describes the domain model, technology stack, current state, and the
Guardian contract.  Do not skip this step.

---

## 2. Prefer Small Vertical Slices

- Break work into the smallest independently-deliverable piece.
- Each slice must be: testable in isolation, reviewable in one PR, and
  deployable without breaking existing behaviour.
- If a task has more than one logical slice, open separate GitHub issues
  (use the `to-issues` skill in `skills/engineering/to-issues/`).

---

## 3. Use TDD for New Behaviour

For every new externally observable behaviour:

1. Write a failing test first (red).
2. Write the minimum code to make it pass (green).
3. Refactor – clean up without breaking the test.

Do not write implementation code before the test exists.
See `skills/engineering/tdd/SKILL.md` for the full protocol.

---

## 4. Never Perform Destructive Actions Without Explicit User Approval

**Destructive actions include (but are not limited to):**
- Deleting or overwriting files
- Running `git push`, `git reset`, `git rebase`, or `git rm`
- Modifying or dropping database records
- Calling external APIs with side effects (POST/PUT/DELETE/PATCH)
- Running shell commands with elevated privileges
- Batch updates that affect more than one record

**Rule:** Before generating code for any of the above, pause and ask the user
for explicit approval.  Include a plain-English description of what will happen
and what cannot be undone.

In code, always route such actions through `GuardianPolicy.check()`.
See `docs/adr/0002-guardian-before-destructive-actions.md`.

---

## 5. Before Changing Architecture, Write an ADR

If a task requires:
- Adding a new top-level module or subsystem,
- Changing the memory storage format,
- Modifying the Guardian policy contract,
- Introducing a new external dependency,

…then write an Architecture Decision Record in `docs/adr/` **before** writing
any implementation code.  Use the existing ADRs as templates.
Number ADRs sequentially (e.g. `0004-`, `0005-`).

---

## 6. Update the Task Journal / Changelog After Each Task

After completing a task:
- If the repository has a `CHANGELOG.md`, add an entry under `[Unreleased]`.
- The CLI's `TaskJournal` is updated automatically by the CLI commands; for
  direct file changes, add a manual note explaining what changed and why.

---

## 7. If Uncertain, Ask Clarifying Questions First

Do not make assumptions about intent.  If the requirements are ambiguous:
- List your assumptions explicitly.
- Ask the user to confirm or correct them before writing code.
- Use the `grill-with-docs` skill (`skills/engineering/grill-with-docs/SKILL.md`)
  to structure your clarifying questions.

---

## 8. For Bugs, Use the Diagnose Loop

When investigating a bug, follow this sequence:

1. **Reproduce** – write a failing test that demonstrates the bug.
2. **Minimise** – reduce the failing case to the smallest possible input.
3. **Hypothesise** – state the probable root cause before looking at code.
4. **Instrument** – add logging / assertions to confirm or refute the hypothesis.
5. **Fix** – make the minimal code change that resolves the root cause.
6. **Regression-test** – ensure the failing test now passes; add it to the suite.

See `skills/engineering/diagnose/SKILL.md`.

---

## 9. For Features: Plan → Tests → Implementation → Review

For every new feature:

1. **Plan** – describe files to create/modify, risk level, and rollback plan.
2. **Tests** – write failing tests covering the new behaviour.
3. **Implementation** – write the minimum code to make tests pass.
4. **Review** – confirm tests pass, linter is clean (`ruff check .`), and
   the `CONTEXT.md` or ADRs need no updates.

---

## Quick Reference

| Situation | Action |
|-----------|--------|
| Starting any task | Read `CONTEXT.md` |
| New behaviour | TDD (`skills/engineering/tdd/SKILL.md`) |
| Bug report | Diagnose loop (`skills/engineering/diagnose/SKILL.md`) |
| Unclear requirements | `grill-with-docs` skill |
| Architecture change | Write ADR in `docs/adr/` first |
| Destructive action | Get explicit user approval + Guardian check |
| Multi-slice task | Open GitHub issues (`to-issues` skill) |
| Completed task | Update journal / changelog |
