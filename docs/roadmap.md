# Roadmap

## v0.1 – Foundation

**Status:** ✅ Complete

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

**Status:** ✅ Complete

**Theme:** Connect real AI to skill execution.

- [x] OpenAI + Google Gemini provider clients (`singleclaw/llm/`)
- [x] Prompt rendering with input and memory context injection (`singleclaw/llm/prompt.py`)
- [x] `.env` integration for API keys (`LLMConfig.resolve()`)
- [x] Token usage logging in journal (`TaskJournal.log(token_usage=…)`)
- [x] Dual-mode auth: API Key (env var) + OAuth 2.0 Device Flow (RFC 8628)
- [x] `auth login`, `auth logout`, `auth status` CLI sub-commands
- [x] `TokenStore` – OAuth token persistence in `.singleclaw/auth_token.json`
- [x] `LLMClientFactory` – unified provider instantiation; auth-agnostic `SkillRunner`
- [x] Streaming provider support in `OpenAIProvider` and `GoogleProvider`
- [ ] Streaming output surfaced in CLI (deferred to v0.3)
- [ ] Output JSON Schema validation (deferred to v0.4)

---

## v0.3 – Memory Intelligence

**Status:** ✅ Complete

**Theme:** Make memory smarter and more useful.

- [x] Semantic memory search – TF-IDF cosine similarity (`singleclaw/dmn/search.py`)
- [x] Context injection – `MemorySearch.query()` replaces `recent(n=5)` in CLI `run` command
- [x] `singleclaw memory list [--tag TAG]` – list all memory items; filter by tag
- [x] `singleclaw memory search "query"` – relevance-ranked search with Rich table output
- [x] Memory export to Markdown or JSON (`singleclaw memory export`)
- [x] Memory pruning / archiving (`singleclaw memory archive --before DATE`)

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
