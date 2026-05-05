# ADR 0003 – DMN Memory and Reflection Loop

**Status:** Accepted  
**Date:** 2026-05-04  
**Deciders:** @alicken-lai

---

## Context

A core differentiator of SingleClaw DMN is persistent memory across sessions.
Many AI assistants start each conversation with a blank slate, forcing the user
to re-explain context.  The Default Mode Network (DMN) metaphor describes the
brain's resting-state network that consolidates and surfaces relevant memories
when needed.

The project needs a clear architectural commitment to *how* memory is stored,
*when* it is retrieved, and *how* the agent reflects on it – before adding LLM
integration in v0.2/v0.3.

---

## Decision

**Memory is append-only, local, and human-readable by default.**

Specifically:

1. **Storage** – all memory is written to `.singleclaw/memory.jsonl` (machine-readable)
   and mirrored to `.singleclaw/memory_notes.md` (human-readable).  Records are
   never deleted or mutated; only appended.

2. **Retrieval** – before any skill execution, the agent retrieves relevant memory
   items.  In v0.1 this is recency-based (`MemoryStore.recent()`).  In v0.3 it
   will be semantic-similarity-based.

3. **Reflection loop** – the `reflect` command produces a Markdown summary of
   recent memory and journal entries.  This is the human-in-the-loop mechanism
   for reviewing what the agent has accumulated.

4. **Memory before action** – the discipline in `skills/memory/memory-retrieval-before-action/SKILL.md`
   documents the expected sequence: retrieve context → check Guardian → execute skill →
   write result to memory → log to journal.

---

## Consequences

**Positive:**
- Memory is recoverable; no data loss from agent errors.
- Human-readable `.md` mirror enables review without CLI tooling.
- Append-only design is trivially safe to implement and test.

**Negative / Trade-offs:**
- Memory grows unboundedly; compaction/pruning will be needed at v0.3+.
- Recency-based retrieval is a poor proxy for relevance; acceptable for v0.1.

**Neutral:**
- The JSONL format is line-delimited; partial writes produce at most one corrupt
  line, which is silently skipped by `MemoryStore._load_all()`.
