# SingleClaw DMN

> **Not more agents. Better memory. Safer execution.**

SingleClaw DMN is a single-agent personal AI work OS built for knowledge
workers and small teams who want a reliable, auditable AI assistant – without
the complexity of a multi-agent framework.

---

## What is SingleClaw DMN?

Most AI tooling pushes you toward multi-agent architectures: swarms of
specialised agents that coordinate, hand off tasks, and negotiate.  For
large-scale autonomous pipelines this makes sense.  For personal work – daily
decisions, meeting notes, procurement comparisons, LinkedIn posts – it's
overkill and fragile.

SingleClaw DMN takes a different approach:

| Principle | What it means |
|-----------|--------------|
| **Single Agent** | One coherent loop: you → agent → skill → memory |
| **DMN Memory** | Persistent local memory across every session |
| **Skill Library** | Reusable, composable task templates |
| **Guardian Check** | Rule-based safety layer – no dangerous actions without review |

---

## Why Single-Agent Architecture?

- **Simpler** – no coordination overhead between agents
- **More reliable** – single call stack, easy to debug
- **Better memory** – DMN memory persists across every session
- **Auditable** – full task journal of every action taken
- **Safer** – one centralised Guardian policy

See [docs/why_single_agent.md](docs/why_single_agent.md) for a full comparison
with multi-agent systems.

---

## Installation

```bash
# Clone the repository
git clone https://github.com/alicken-lai/SingleClaw-DMN.git
cd SingleClaw-DMN

# Install in editable mode (creates the `singleclaw` command)
pip install -e .
```

**Requirements:** Python ≥ 3.10

---

## Quickstart

```bash
# 1. Initialise your local workspace
singleclaw init
# → Creates .singleclaw/ in the current directory

# 2. Store a memory item
singleclaw remember "Focus on B2B SaaS for Q3" --tag decision

# 3. Check the safety of an action
singleclaw guardian-check "delete old project files" --risk high

# 4. Run a skill (dry run first)
singleclaw run meeting_minutes_to_report --input my_notes.json --dry-run

# 5. Run for real
singleclaw run meeting_minutes_to_report --input my_notes.json

# 6. Reflect on recent memory and activity
singleclaw reflect
```

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `singleclaw init` | Initialise workspace in the current directory |
| `singleclaw remember "text" [--tag TAG]` | Store a memory item |
| `singleclaw run SKILL --input FILE [--dry-run]` | Execute a skill |
| `singleclaw reflect` | Summarise recent memory and activity |
| `singleclaw guardian-check ACTION [--risk LEVEL]` | Evaluate action safety |
| `singleclaw --help` | Show all commands |

---

## Project Structure

```
singleclaw-dmn/
├── singleclaw/               # Python package
│   ├── cli.py                # Typer CLI entry point
│   ├── dmn/
│   │   ├── memory.py         # JSONL memory store
│   │   ├── journal.py        # Task journal
│   │   └── reflect.py        # Reflection engine
│   ├── guardian/
│   │   ├── policy.py         # Guardian policy (ALLOW/REVIEW/BLOCK)
│   │   ├── risk.py           # Keyword-based risk classifier
│   │   └── dry_run.py        # Dry-run preview renderer
│   ├── skills/
│   │   ├── registry.py       # Skill discovery and validation
│   │   └── runner.py         # Skill execution
│   └── workspace/
│       └── manager.py        # .singleclaw/ directory management
├── skills/                   # Built-in skill templates
│   ├── meeting_minutes_to_report/
│   ├── procurement_comparison/
│   └── linkedin_post_writer/
├── examples/                 # Worked example workflows
│   ├── personal_business_os/
│   ├── procurement_workflow/
│   └── content_workflow/
└── docs/                     # Documentation
    ├── architecture.md
    ├── why_single_agent.md
    ├── guardian_check.md
    ├── skill_spec.md
    └── roadmap.md
```

---

## Safety Model

Every action passes through the **Guardian Check** before execution:

| Decision | Meaning |
|----------|---------|
| `ALLOW` | Safe – executes immediately |
| `REVIEW_REQUIRED` | Medium risk – dry-run preview shown first |
| `BLOCK` | High/critical risk – execution refused |

High-risk examples that are **blocked by default:**
- Delete / overwrite files
- `git push`
- Run shell commands
- Modify databases
- Batch updates
- External uploads

See [docs/guardian_check.md](docs/guardian_check.md) for full details.

---

## Skill Library

Skills are self-describing task templates stored under `skills/`.  Each skill
contains:

- `skill.yaml` – name, description, version, risk level
- `prompt.md` – LLM prompt template
- `input_schema.json` – JSON Schema for input validation
- `output_schema.json` – JSON Schema for output structure
- `examples/` – sample inputs and expected outputs

**Built-in skills:**

| Skill | Description |
|-------|-------------|
| `meeting_minutes_to_report` | Convert meeting notes to a structured report |
| `procurement_comparison` | Compare vendor quotes with a recommendation |
| `linkedin_post_writer` | Draft professional LinkedIn posts from a brief |

See [docs/skill_spec.md](docs/skill_spec.md) to create your own skills.

---

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture.md) | System design and data flow |
| [Why Single Agent](docs/why_single_agent.md) | Comparison with multi-agent systems |
| [Guardian Check](docs/guardian_check.md) | Safety and dry-run design |
| [Skill Spec](docs/skill_spec.md) | How to create new skills |
| [Roadmap](docs/roadmap.md) | v0.1 → v0.4 feature roadmap |

---

## Roadmap

- **v0.1** – Foundation (CLI, memory, journal, guardian, skill registry) ✅
- **v0.2** – LLM integration (OpenAI-compatible API, prompt rendering)
- **v0.3** – Memory intelligence (semantic search, context injection)
- **v0.4** – Skill ecosystem (validation, packaging, community registry)

See [docs/roadmap.md](docs/roadmap.md) for full details.

---

## Contributing

Contributions are welcome!  Please open an issue first to discuss your idea
before submitting a pull request.

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Make your changes
4. Run tests: `pytest`
5. Open a pull request

---

## License

MIT – see [LICENSE](LICENSE).

---

## Philosophy

> The goal is not to build the smartest agent.
> The goal is to build the most *useful* agent for real work.
>
> — SingleClaw DMN
