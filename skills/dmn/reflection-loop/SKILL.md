# Skill: reflection-loop

**Category:** dmn  
**Discipline:** DMN Memory Reflection  
**Related ADR:** `docs/adr/0003-dmn-memory-reflection-loop.md`

---

## Purpose

Use this skill to ensure the agent surfaces relevant memory context before
acting, and consolidates new information after acting.  It implements the
Default Mode Network metaphor: rest-state consolidation of accumulated knowledge.

---

## When to Apply

- Before running any skill that could benefit from past decisions or context.
- After completing a multi-step task that produced new knowledge.
- When a user asks the agent to "catch up" or "remind me what we decided".
- As part of a scheduled or session-start routine.

---

## The Reflection Loop

```
┌─────────────────────────────────────────────────────┐
│                 DMN Reflection Loop                  │
│                                                      │
│  1. Retrieve    → MemoryStore.recent() / by_tag()   │
│  2. Surface     → Print summary via reflect command  │
│  3. Act         → Run skill (Guardian-checked)       │
│  4. Consolidate → MemoryStore.add() with result tag  │
│  5. Journal     → TaskJournal.log() with status      │
└─────────────────────────────────────────────────────┘
```

---

## Protocol

### Step 1 – Retrieve context

Before acting, retrieve relevant memory:

```python
memory = MemoryStore(workspace_dir)
recent = memory.recent(n=10)
decisions = memory.by_tag("decision")
```

Surface the most relevant items to the user or inject them into the skill prompt.

### Step 2 – Run `singleclaw reflect`

If the user is starting a new work session, run `reflect` first:

```bash
singleclaw reflect
```

This outputs a Markdown summary of recent memory and journal activity.

### Step 3 – Execute the skill

Run the skill in the normal way (Guardian-checked, dry-run if needed):

```bash
singleclaw run <skill_name> --input <file>
```

### Step 4 – Store the result in memory

After a successful skill run, store a summary in memory:

```bash
singleclaw remember "Completed <skill_name> on <date>: <one-line result>" --tag result
```

In Python code:

```python
memory.add(text=f"Completed {skill_name}: {result_summary}", tag="result")
```

### Step 5 – Review the journal

After any significant task, check the journal for unexpected status values:

```bash
cat .singleclaw/journal.jsonl | python -m json.tool
```

---

## Checklist

- [ ] `reflect` run (or `MemoryStore.recent()` called) before acting.
- [ ] Relevant memory items surfaced to user or injected into prompt.
- [ ] Skill executed with Guardian check.
- [ ] Result stored in memory with appropriate tag.
- [ ] Journal entry created with correct status.

---

## Memory Tags Convention

| Tag | Meaning |
|-----|---------|
| `decision` | A significant decision that should influence future actions |
| `preference` | A user preference or working style note |
| `result` | Output or outcome of a completed skill run |
| `note` | General observation (default) |
| `context` | Background context for a project or domain |
