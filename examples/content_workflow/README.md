# Content Workflow – Example

This example shows how to use SingleClaw DMN to manage a **content creation
pipeline** for LinkedIn and reports.

## Workflow

```bash
# 1. Initialise workspace
singleclaw init

# 2. Store content strategy context
singleclaw remember "Content pillar: AI productivity for solo founders" --tag strategy

# 3. Write a LinkedIn post from a brief
singleclaw run linkedin_post_writer --input post_brief.json

# 4. Convert a recent talk into a report
singleclaw run meeting_minutes_to_report --input talk_notes.json

# 5. Reflect
singleclaw reflect
```

## Sample Post Brief (`post_brief.json`)

```json
{
  "topic": "Why single-agent AI outperforms multi-agent systems for solo work",
  "talking_points": [
    "Less coordination overhead",
    "Better memory continuity",
    "Easier to debug and audit"
  ],
  "tone": "professional",
  "max_words": 180
}
```
