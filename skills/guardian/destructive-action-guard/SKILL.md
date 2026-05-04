# Skill: destructive-action-guard

**Category:** guardian  
**Discipline:** Guardian Check Before Destructive Actions  
**Related ADR:** `docs/adr/0002-guardian-before-destructive-actions.md`

---

## Purpose

Use this skill whenever you are adding code that could modify, delete, or expose
data outside the current read context.  It ensures the Guardian contract is
honoured on every new code path.

---

## What Counts as a Destructive Action

| Action | Example |
|--------|---------|
| File write / overwrite | Writing to any path outside `.singleclaw/` |
| File delete | `os.remove()`, `shutil.rmtree()`, `Path.unlink()` |
| Git operations | `git push`, `git reset`, `git rebase`, `git rm` |
| Shell execution | `subprocess.run()`, `os.system()` |
| External API call | Any HTTP POST / PUT / DELETE / PATCH |
| Database mutation | INSERT / UPDATE / DELETE on any data store |
| Batch update | Any loop that modifies more than one record |

---

## Protocol

### Step 1 – Identify the risk level

Use `RiskClassifier` or the table in `docs/guardian_check.md` to assign a risk
level: `low`, `medium`, `high`, or `critical`.

Default assignments:
- `critical` – `rm -rf`, recursive delete, drop database
- `high` – delete file, git push, shell command, external upload
- `medium` – write file, overwrite record, batch read with side effects
- `low` – read only, dry-run preview

### Step 2 – Route through `GuardianPolicy.check()`

In Python code, always call the Guardian before executing:

```python
from singleclaw.guardian.policy import GuardianPolicy

guardian = GuardianPolicy()
decision = guardian.check(action="<plain English description>", risk_level="<level>")

if decision == "BLOCK":
    # refuse and return
    ...
if decision == "REVIEW_REQUIRED":
    # show dry-run preview; do not execute without user confirmation
    ...
# ALLOW → proceed
```

### Step 3 – Log to the journal

After every Guardian check (including BLOCKed ones), log the outcome:

```python
journal.log(command="<command>", input_summary="<summary>", status=decision.lower(), risk_level=risk)
```

### Step 4 – Get explicit user approval for BLOCK-level actions

For `high` or `critical` risk, the CLI must not proceed silently.  Either:
- Print a clear explanation and exit (current MVP behaviour).
- Prompt for interactive confirmation (future `--force` flag).

Never add a `--force` flag that bypasses the journal log.

### Step 5 – Write a test

Add a test in `tests/test_guardian.py` that covers the new action:

```python
def test_my_new_action_is_blocked():
    guardian = GuardianPolicy()
    assert guardian.check("my new destructive action", risk_level="high") == "BLOCK"
```

---

## Checklist

- [ ] Risk level assigned and justified.
- [ ] `GuardianPolicy.check()` called before execution.
- [ ] `TaskJournal.log()` called with `risk_level`.
- [ ] BLOCK / REVIEW paths handled (no silent execution).
- [ ] Test added in `tests/test_guardian.py`.
- [ ] No bypass of Guardian on any code path.
