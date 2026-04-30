# Skill Specification

## What is a Skill?

A **skill** is a reusable, self-describing task template.  Each skill lives in
its own directory under `skills/` and contains everything needed to understand,
validate, and execute the task.

## Directory Structure

```
skills/
└── my_skill_name/
    ├── skill.yaml        ← required: metadata
    ├── prompt.md         ← required: LLM prompt template
    ├── input_schema.json ← required: JSON Schema for input validation
    ├── output_schema.json← required: JSON Schema for output structure
    └── examples/
        └── README.md     ← recommended: sample inputs and outputs
```

## `skill.yaml` Schema

```yaml
name: my_skill_name           # must match directory name
description: >
  One-paragraph description of what the skill does.
version: "0.1.0"              # semver
author: Your Name
input_type: application/json  # MIME-style type hint
output_type: text/markdown    # MIME-style type hint
risk_level: low               # low | medium | high | critical
tags:
  - tag1
  - tag2
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique skill identifier |
| `description` | string | What the skill does |
| `version` | string | Semver version |
| `input_type` | string | Type of input data |
| `output_type` | string | Type of output data |
| `risk_level` | string | Guardian risk level |

## `prompt.md` Format

Write the prompt as a Markdown document.  Use clear sections:

1. **Role** – describe the AI persona
2. **Input** – list all expected input fields
3. **Output Format** – show the exact structure expected
4. **Guidelines** – rules the model must follow

Use `{variable_name}` placeholders where input fields should be injected.

## JSON Schemas

Use [JSON Schema Draft-07](https://json-schema.org/draft-07/schema) for both
`input_schema.json` and `output_schema.json`.

Mark required fields explicitly:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["field1", "field2"],
  "properties": {
    "field1": { "type": "string", "description": "..." }
  }
}
```

## Risk Level Guidelines

| Level | When to use |
|-------|-------------|
| `low` | Read-only, no external side effects, reversible |
| `medium` | Creates new files locally or calls read-only external APIs |
| `high` | Modifies existing files, calls external write APIs |
| `critical` | Irreversible – use only with explicit human confirmation |

## Running a Skill

```bash
singleclaw run <skill_name> --input path/to/input.json
```

Use `--dry-run` to preview without executing:

```bash
singleclaw run <skill_name> --input path/to/input.json --dry-run
```

## Creating a New Skill (checklist)

- [ ] Create `skills/<your_skill_name>/` directory
- [ ] Write `skill.yaml` with all required fields
- [ ] Write `prompt.md` with role, input, output format, and guidelines
- [ ] Write `input_schema.json` with `required` fields listed
- [ ] Write `output_schema.json`
- [ ] Add `examples/README.md` with a sample input and expected output
- [ ] Test: `singleclaw run <your_skill_name> --input examples/sample.json --dry-run`
