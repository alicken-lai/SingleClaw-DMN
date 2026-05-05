# Skill: diagnose

**Category:** engineering  
**Discipline:** Structured Bug Diagnosis  
**Inspired by:** Matt Pocock's engineering-skills

---

## Purpose

Use this skill whenever you encounter a bug, unexpected behaviour, or failing
test.  It prevents shipping speculative fixes and ensures every fix is backed
by a regression test.

---

## When to Apply

- A test is failing and the cause is not immediately obvious.
- A user reports unexpected CLI behaviour.
- A skill produces incorrect output.
- A Guardian decision appears wrong.
- Memory items are corrupted or missing.

---

## Protocol

### Step 1 – Reproduce

1. Write a **minimal failing test** that demonstrates the bug.
   - Prefer a unit test over an integration test.
   - The test must fail *before* any fix is applied.
2. Confirm the test fails consistently (not intermittently).
3. Commit the failing test with a message like `test: reproduce bug in <module>`.

### Step 2 – Minimise

1. Reduce the failing test to the smallest possible input.
2. Remove all irrelevant setup, fixtures, and assertions.
3. The minimal test should still fail for exactly the same reason.

### Step 3 – Hypothesise

1. State your hypothesis about the root cause **in plain English** before
   looking at the implementation.
2. Write it as a comment in the test file or as a GitHub issue comment.
3. Be specific: "I believe the bug is in `RiskClassifier.classify()` because
   the keyword list is case-sensitive", not "something is wrong with risk".

### Step 4 – Instrument

1. Add `print()` statements, `assert` guards, or a debugger breakpoint to
   confirm or refute the hypothesis.
2. Run the failing test with `-s` to see output: `pytest -s tests/test_X.py`.
3. Do not modify production code at this stage.

### Step 5 – Fix

1. Make the **minimum code change** that resolves the root cause.
2. Do not fix unrelated issues in the same commit.
3. Run `pytest` – the failing test must now pass.

### Step 6 – Regression-test

1. Ensure the previously failing test is now in the test suite permanently.
2. Remove any temporary `print()` or debug statements.
3. Run the full test suite: `pytest`.
4. Commit with message: `fix: <one-line description of the bug>`.

---

## Checklist

- [ ] Failing test written before any fix attempt.
- [ ] Hypothesis stated explicitly (in issue, PR, or comment).
- [ ] Root cause confirmed by instrumentation, not assumed.
- [ ] Minimum fix applied (no scope creep).
- [ ] Failing test now passes.
- [ ] Full test suite passes.
- [ ] Debug artefacts removed.

---

## Commands

```bash
# Run a single test with output
pytest -s tests/test_<module>.py::TestClass::test_name -v

# Run full suite
pytest

# Show which tests would run (dry run)
pytest --collect-only
```
