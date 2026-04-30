# Why Single-Agent Architecture?

## The Multi-Agent Trap

The AI tooling landscape has converged on multi-agent frameworks as the
default answer to complex tasks.  The idea is appealing: specialise each agent,
let them collaborate, and emergent intelligence will solve hard problems.

In practice, for **personal and small-team knowledge work**, multi-agent systems
introduce more problems than they solve:

| Problem | Multi-Agent | Single-Agent (SingleClaw) |
|---------|-------------|---------------------------|
| Coordination overhead | High – agents negotiate, hand off, retry | None |
| Memory continuity | Fragile – state lost between agent calls | Durable JSONL memory |
| Auditability | Hard – who did what? | Full journal log |
| Debugging | Complex – which agent failed? | Single call stack |
| Cost | Higher – more LLM calls | Minimal |
| Safety | Distributed risk | Centralised Guardian |

## The SingleClaw Hypothesis

> **One well-memoried agent with a good skill library outperforms a swarm
> of forgetful agents for personal knowledge work.**

The human brain doesn't delegate its thinking to ten sub-brains.  It maintains
a single coherent model of the world (the DMN – Default Mode Network) and
applies focused skills when needed.

SingleClaw DMN mirrors this architecture:

```
Human ──▶ Single Agent ──▶ Skill ──▶ Memory Update
              ▲                           │
              └───────────────────────────┘
                      (context loop)
```

## What Multi-Agent IS Good For

Multi-agent is genuinely powerful for:

- Large-scale parallel research (crawl thousands of pages simultaneously)
- Long-horizon autonomous pipelines (days-long tasks with human checkpoints)
- Organisations with well-defined, isolated roles

SingleClaw does not pretend to replace those use cases.  It is optimised for
the **solo knowledge worker or small team** who needs a reliable, auditable AI
assistant – not a sprawling agent network.

## References & Further Reading

- [The DMN in neuroscience](https://en.wikipedia.org/wiki/Default_mode_network)
- [Agents vs. Pipelines (Anthropic)](https://www.anthropic.com/research)
- "Building Effective Agents" – Anthropic blog post
