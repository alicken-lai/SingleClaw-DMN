# Guardian Check – Safety & Dry-Run Design

## Overview

The Guardian Check is a lightweight, rule-based safety layer that sits between
the user's intent and any action that could cause harm, data loss, or
unintended side effects.

Every CLI action passes through the Guardian before execution.

## Decision Taxonomy

| Decision | Meaning | Example |
|----------|---------|---------|
| `ALLOW` | Safe to execute immediately | `remember`, `reflect`, read-only skills |
| `REVIEW_REQUIRED` | Medium risk – dry-run shown first | write-file skills, API calls |
| `BLOCK` | High/critical risk – execution refused | `delete files`, `git push`, `run shell` |

## Risk Levels

Actions are classified on a four-level scale:

| Level | Description |
|-------|-------------|
| `low` | Read-only, no external side effects |
| `medium` | Writes data locally or calls external read APIs |
| `high` | Deletes/overwrites data, external writes, git operations |
| `critical` | Irreversible destructive operations (drop table, rm -rf) |

## Keyword Rules

The `RiskClassifier` in `singleclaw/guardian/risk.py` uses keyword matching to
infer the risk level from an action description.

**Critical keywords:** `drop database`, `truncate`, `rm -rf`, `wipe`, `destroy`

**High keywords:** `delete file`, `overwrite`, `git push`, `run shell`, `exec`,
`modify database`, `batch update`, `external upload`, `send email`, `publish`

**Medium keywords:** `move file`, `rename file`, `update file`, `write file`,
`create file`, `git commit`, `api call`, `http post/put/patch/delete`

## Dry-Run Behaviour

When an action is `REVIEW_REQUIRED`, the runner automatically enters dry-run
mode.  A preview panel is displayed showing:

```
╭─────────────── ⚡ Dry Run Preview ────────────────╮
│ ACTION:      run skill 'write_report'              │
│ INPUT:       skill=write_report, input_keys=[...]   │
│ RISK LEVEL:  MEDIUM                                │
│                                                    │
│ This is a DRY RUN – no changes were made.          │
╰────────────────────────────────────────────────────╯
```

High-risk skills can be tested with `--dry-run` explicitly:

```bash
singleclaw run my_skill --input data.json --dry-run
```

## Extending the Guardian

To add custom rules, edit `singleclaw/guardian/risk.py` and extend the
`_RULES` list.  A future version will support a YAML-based policy file so
rules can be configured without modifying code.

## Design Principles

1. **Fail safe** – when in doubt, require review.
2. **Transparent** – always tell the user *why* an action was blocked.
3. **Auditable** – every Guardian decision is logged in `journal.jsonl`.
4. **Non-intrusive** – low-risk actions pass through without any friction.
