# Skill: tdd

**Category:** engineering  
**Discipline:** Test-Driven Development  
**Inspired by:** Matt Pocock's engineering-skills

---

## Purpose

Use this skill whenever you are adding new externally observable behaviour to
SingleClaw DMN.  It prevents shipping untested code and ensures every feature
has a regression test that will catch future breakage.

---

## When to Apply

- Adding a new CLI command or option.
- Adding a new method to `MemoryStore`, `TaskJournal`, `GuardianPolicy`, `SkillRegistry`, or `SkillRunner`.
- Adding a new skill that has custom Python logic (not just YAML/Markdown templates).
- Any change that modifies a public interface.

**Do not apply** to: typo fixes in docstrings, comment edits, README updates,
adding new SKILL.md files.

---

## Protocol

### Step 1 – Red (write the failing test)

1. Identify the exact behaviour you want to add.
2. Write a pytest test in `tests/` that asserts the expected behaviour.
3. Run `pytest` – confirm the test **fails** for the right reason (not an import
   error or fixture problem).
4. Do not write any implementation code yet.

### Step 2 – Green (make it pass)

1. Write the minimum production code required to make the test pass.
2. Do not gold-plate.  Inline constants are fine at this stage.
3. Run `pytest` – confirm **only** the new test was failing and now passes.
4. Confirm all pre-existing tests still pass.

### Step 3 – Refactor (clean up)

1. Remove duplication, rename variables for clarity, extract helpers if needed.
2. Run `pytest` and `ruff check .` after every refactor step.
3. Commit when tests are green and the linter is clean.

---

## Checklist

Before marking a task done, confirm:

- [ ] Failing test written and committed before implementation.
- [ ] Test is in `tests/test_<module>.py` matching the module under test.
- [ ] Test name follows `test_<behaviour>` convention.
- [ ] All existing tests still pass.
- [ ] `ruff check .` reports no errors.
- [ ] No production code was written before the test existed.

---

## Commands

```bash
# Run all tests
pytest

# Run tests for a specific module
pytest tests/test_guardian.py -v

# Lint
ruff check .
```
