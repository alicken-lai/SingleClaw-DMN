# Architecture

## Overview

SingleClaw DMN is a **single-agent personal AI work OS**.  All intelligence
flows through one agent loop: a human issues a command, the agent retrieves
memory, checks the Guardian policy, runs the requested skill, and writes the
result back to memory and the journal.

```
User (CLI)
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│                     SingleClaw Agent Loop                    │
│                                                              │
│  ┌─────────┐   ┌────────────┐   ┌──────────────┐           │
│  │  Input  │──▶│  Guardian  │──▶│  Skill Runner│           │
│  │ (CLI)   │   │   Check    │   │              │           │
│  └─────────┘   └────────────┘   └──────┬───────┘           │
│                                         │                    │
│  ┌──────────────────────────────────────▼──────────────┐    │
│  │                   DMN Memory Layer                   │    │
│  │  memory.jsonl · memory_notes.md · journal.jsonl     │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

## Components

### 1. CLI (`singleclaw/cli.py`)

The entry point for all user interaction.  Uses [Typer](https://typer.tiangolo.com/)
to provide a clean, self-documenting command-line interface.

Commands:
| Command | Purpose |
|---------|---------|
| `init` | Create `.singleclaw/` workspace |
| `remember` | Store a memory item |
| `run` | Execute a skill |
| `reflect` | Summarise memory and journal |
| `guardian-check` | Evaluate an action against policy |

### 2. DMN Memory (`singleclaw/dmn/`)

The Default Mode Network (DMN) memory layer persists information across
sessions.  It uses:

- **`memory.jsonl`** – append-only JSONL log of every memory item
- **`memory_notes.md`** – human-readable mirror for browsing in any editor
- **`journal.jsonl`** – timestamped audit log of every CLI command

### 3. Guardian Check (`singleclaw/guardian/`)

A rule-based safety layer that classifies every action as:

- `ALLOW` – safe to execute
- `REVIEW_REQUIRED` – medium risk; dry-run preview shown first
- `BLOCK` – high / critical risk; execution refused

See [guardian_check.md](guardian_check.md) for details.

### 4. Skill Library (`singleclaw/skills/`)

A file-based registry of reusable task templates.  Each skill is a directory
under `skills/` containing a `skill.yaml`, prompt template, and JSON schemas.

See [skill_spec.md](skill_spec.md) for how to write a skill.

### 5. Workspace (`singleclaw/workspace/`)

Manages the `.singleclaw/` local directory – creation, config loading, and
file paths for all persistent data.

## Data Flow (example: `singleclaw run meeting_minutes_to_report --input notes.json`)

```
1. CLI parses command → SkillRegistry.get("meeting_minutes_to_report")
2. GuardianPolicy.check(action, risk_level) → ALLOW
3. TaskJournal.log(command="run", status="pending")
4. SkillRunner.execute(skill, input_file="notes.json")
5. [Placeholder] Result returned and printed
6. TaskJournal.log(command="run", status="success")
```

## Directory Layout

```
singleclaw-dmn/
├── singleclaw/        # Python package
│   ├── cli.py         # Typer CLI
│   ├── dmn/           # Memory, journal, reflection
│   ├── guardian/      # Policy, risk classifier, dry-run
│   ├── skills/        # Registry, runner
│   └── workspace/     # Workspace manager
├── skills/            # Skill templates (data, not code)
├── examples/          # Worked examples
└── docs/              # Documentation
```
