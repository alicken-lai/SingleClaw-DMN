# Personal Business OS – Example Workflow

This example shows how to use SingleClaw DMN as a **personal business OS**:
storing decisions, meeting notes, and reflections in a single local workspace.

## Workflow

```bash
# 1. Initialise your workspace (once per project)
singleclaw init

# 2. Record a strategic decision
singleclaw remember "Decided to focus on B2B SaaS for Q3" --tag decision

# 3. Store a project note
singleclaw remember "Tech stack: FastAPI + PostgreSQL + React" --tag preference

# 4. After a meeting, convert minutes to a report
singleclaw run meeting_minutes_to_report --input meeting_2024_07.json

# 5. Reflect on recent activity
singleclaw reflect
```

## What You Get

- A `.singleclaw/` folder with your memory and journal
- Human-readable `memory_notes.md` you can open in any editor
- A task audit trail in `journal.jsonl`
