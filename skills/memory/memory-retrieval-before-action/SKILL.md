# Skill: memory-retrieval-before-action

**Category:** memory  
**Discipline:** Retrieve Context Before Acting  
**Related ADR:** `docs/adr/0003-dmn-memory-reflection-loop.md`

---

## Purpose

Use this skill to ensure the agent does not act in an information vacuum.
Retrieving relevant memory before any non-trivial action prevents repeating
past mistakes, contradicting past decisions, and duplicating work.

---

## When to Apply

- Before running any skill.
- Before answering a question that may depend on past decisions.
- Before generating content that should be consistent with prior outputs.
- Before any `singleclaw run` command in an automated pipeline.

---

## Protocol

### Step 1 – Check if the workspace is initialised

```bash
# If not initialised, no memory is available yet
singleclaw init
```

In Python:

```python
manager = WorkspaceManager()
if not manager.is_initialised():
    # handle gracefully – no memory available
    ...
```

### Step 2 – Retrieve recent memory

```python
from singleclaw.dmn.memory import MemoryStore

memory = MemoryStore(manager.workspace_dir)
recent = memory.recent(n=10)
```

If the action is related to a specific topic, filter by tag:

```python
decisions = memory.by_tag("decision")
preferences = memory.by_tag("preference")
```

### Step 3 – Surface memory to the prompt or user

In v0.1 (no LLM), print relevant items before acting:

```python
from rich.console import Console
console = Console()
for item in recent:
    console.print(f"[dim]{item['timestamp'][:10]}[/dim] [{item['tag']}] {item['text']}")
```

In v0.2+ (LLM integration), inject relevant items into the skill prompt template
as a `{{memory_context}}` variable.

### Step 4 – Proceed with the action

Only after memory has been retrieved and reviewed, run the skill or answer the query.

### Step 5 – Store the outcome

After the action completes, record a memory item:

```python
memory.add(text=f"Ran {skill_name} with input {input_summary}", tag="result")
```

---

## Checklist

- [ ] Workspace is initialised before memory retrieval.
- [ ] `MemoryStore.recent()` called before acting.
- [ ] Tag-filtered retrieval used when topic is known.
- [ ] Retrieved items surfaced to user or injected into prompt.
- [ ] Action outcome stored in memory after completion.

---

## Why This Matters

The DMN (Default Mode Network) metaphor is about continuity.  Without memory
retrieval before action, the agent is amnesiac: it cannot avoid contradicting
a past decision, cannot build on previous work, and cannot learn from past errors.

Memory retrieval is cheap (local file read).  There is no excuse to skip it.
