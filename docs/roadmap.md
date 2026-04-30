# Roadmap

## v0.1 – Foundation (current)

**Status:** ✅ In progress

- [x] Project structure and `pyproject.toml`
- [x] CLI skeleton with Typer (`init`, `remember`, `run`, `reflect`, `guardian-check`)
- [x] DMN Memory (JSONL + Markdown mirror)
- [x] Task Journal (JSONL audit log)
- [x] Guardian Check (rule-based keyword classifier)
- [x] Dry-run support
- [x] Skill Registry (YAML-based discovery)
- [x] Skill Runner (placeholder execution)
- [x] Three example skills: `meeting_minutes_to_report`, `procurement_comparison`, `linkedin_post_writer`
- [x] Documentation (architecture, why_single_agent, guardian_check, skill_spec)

---

## v0.2 – LLM Integration

**Theme:** Connect real AI to skill execution.

- [ ] OpenAI-compatible API client (`singleclaw/llm/`)
- [ ] Prompt rendering with input injection
- [ ] Output parsing and JSON Schema validation
- [ ] Streaming output support in CLI
- [ ] `.env` integration for API keys
- [ ] Token usage logging in journal

---

## v0.3 – Memory Intelligence

**Theme:** Make memory smarter and more useful.

- [ ] Semantic memory search (local embeddings or cosine similarity)
- [ ] Memory tagging and filtering in CLI
- [ ] Context injection – automatically include relevant memories when running a skill
- [ ] Memory export to Markdown or JSON
- [ ] Memory pruning / archiving commands
- [ ] `singleclaw memory list [--tag <tag>]`
- [ ] `singleclaw memory search "query"`

---

## v0.4 – Skill Ecosystem

**Theme:** Make skills easy to share and extend.

- [ ] Skill validation command: `singleclaw skills validate`
- [ ] Skill listing command: `singleclaw skills list`
- [ ] Input schema validation before skill execution
- [ ] Output schema validation after skill execution
- [ ] Skill packaging spec (zip + install from URL or path)
- [ ] Community skill registry (GitHub-based)
- [ ] More built-in skills: `email_draft`, `code_review_summary`, `weekly_report`

---

## Future Ideas (backlog)

- Web UI / dashboard (read-only memory viewer)
- Workspace sync (optional encrypted cloud backup)
- Multi-model support (Anthropic Claude, local Ollama)
- Voice input for `remember` command
- Calendar / time-aware memory ("what did I decide last Monday?")
- Plugin system for custom Guardian rules
