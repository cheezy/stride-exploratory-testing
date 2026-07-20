# exploratory-testing

**Drive structured, charter-based exploratory testing sessions in Claude Code.**

This plugin brings the discipline of session-based exploratory testing to
Claude Code: plan a charter, run a timeboxed session against your application,
and capture findings, questions, and bugs as you go.

> This is the initial scaffold (v0.1.0). The skills, commands, agents, and
> library helpers are filled in by subsequent tasks. This README is a skeleton
> that the documentation task expands.

## Installation

**From the Stride marketplace:**

```
/plugin marketplace add cheezy/stride-marketplace
/plugin install exploratory-testing@stride-marketplace
```

## Repository layout

| Directory   | Purpose                                              |
|-------------|------------------------------------------------------|
| `skills/`   | Skills that drive the exploratory-testing workflow   |
| `commands/` | Slash commands exposed to Claude Code                |
| `agents/`   | Subagents dispatched during a session                |
| `lib/`      | Helper scripts (validation, harness, tooling)        |
| `fixtures/` | Example charters and session artifacts               |

## License

MIT — see [LICENSE](LICENSE).
