# Porting the G449–G451 fixes to the other exploratory-testing variants

This guide covers the three improvement goals filed on 2026-10-02 after a
measured review of `stride-exploratory-testing` 0.2.1:

- **G449 — accuracy**
- **G450 — speed**
- **G451 — token usage**

The user's priority order was accuracy, then speed, then tokens. Each fix lands
first in this repository (the Claude Code edition) and in `stride`'s Step 5.5
consumer. This guide records, for each fix, what changes, why, and what a
variant needs to carry it. It also lists the four other editions and how each
one differs.

**Port from landed fixes only.** When a task lands here, change its status below
to *landed* and replace its "Planned change" paragraph with what actually
shipped, including the commit and the release. A planned section describes
intent, not shipped behaviour. All of these tasks were *planned* on 2026-10-02.

## Status

| Task | Goal | Fix | Status |
|---|---|---|---|
| W2261 | G449 | An explorer card inlined in the agent, so the severity scale, oracles and stop rules never depend on loading a skill | planned |
| W2262 | G449 | `status` derived from `stop_reason`; bugs get `replicated` and `provisional`; typed arrays, known-issue handling, `contract_version`; an example-output fixture and a contract test | planned (needs W2261) |
| W2263 | G449 | A `no_observation_surface` blocked ending; HTTP observed with `curl -sS -i`, not a web-fetch tool; `stride` lists only the explorer's tools | planned (needs W2262) |
| W2264 | G449 | Structured authorization and allowed hosts, cleanup of whatever the explorer started, in-app limits on destructive lenses, a credential-file rule | planned (needs W2261) |
| W2265 | G449 | `stride`'s consumer moves to the new contract, with a cross-repo enum check | planned (needs W2262, W2263) |
| W2266 | G450 | Full result written to `EXPLORATORY_REPORT_PATH`; a bounded summary of about 2 KB returned | planned |
| W2267 | G450 | Step 5.5 groups manual tests into at most about three charters and dispatches independent ones together | planned |
| W2268 | G450 | Verify mode: re-check a fixed Critical from its minimal repro in one or two probes | planned (needs W2266) |
| W2269 | G450 | Step 5.6 runs `/harden` unattended from the persisted report, with an explicit framework | planned (needs W2266) |
| W2270 | G451 | Ranged reads with no whole-file re-reads; a fixed Step 5.5 dispatch template | planned |
| W2271 | G451 | Trim `stride`'s Step 5.5 and findings contracts down to rules | planned |
| W2272 | G451 | Trim always-loaded descriptions and the sections of the session and bug-advocacy skills the explorer does not use | planned |
| W2273 | G451 | Measure before and after against the 2026-10-02 baseline | planned (claim last) |

## The baseline

These figures were measured on 2026-10-02 from the session transcripts of the
kanban project. Usage was deduplicated by message id. Every number covers the
Claude Code edition only. No variant has been measured; do not assume a variant
behaves the same.

| Measure | Value |
|---|---|
| Explorer dispatches | 19, all from `stride` Step 5.5, across 7 sessions (2026-09-03 to 2026-10-02). 17 targeted markdown or scripts; 2 targeted a running app |
| Wall clock per dispatch | median 547 s (372–822 s); 2.85 h in total |
| Time spent writing the final report | 39% of all explorer wall clock |
| Input-side tokens per dispatch | median 1.10M (92.7% cache reads); peak context median 89.5k |
| Report returned to the main loop | median 37 KB, 733 KB in total (about 183k tokens) |
| Hand-written dispatch prompts | median 6.8 KB, 124 KB in total |
| Severity labels | only 28 of 101 bugs used the exact tokens Critical, High, Moderate or Minor; 24 distinct strings appeared |
| Skills the explorer loaded | `bug-advocacy` in 1 of 19 dispatches; `heuristics`, `oracles` and `session` never |
| Repeat whole-file reads | 18, in 10 of 19 dispatches |
| How sessions ended | 10 probe-budget exhausted, 8 charter quiet, 1 risk acceptable; 0 tool-call ceiling, 0 blocked |
| JSON output | 19 of 19 parsed on the first try |
| Use of commands and the charter-generator agent | 0 |

The last row matters for scoping. Nobody typed `/explore`, `/charter` or any
other command, and the charter-generator agent was never dispatched. Every real
run was the explorer agent dispatched by `stride`. Port the explorer and Step 5.5
changes first.

## The editions, as checked on 2026-10-02

Paths are relative to the kanban checkout. Each cell comes from `ls`, `grep` or
`wc -c`. Re-check a cell before relying on it.

| Edition | Version | Explorer agent | Explorer tools (frontmatter) | Outer turn/call bound | Commands | Distribution |
|---|---|---|---|---|---|---|
| `stride-exploratory-testing` (Claude Code) | v0.2.1 | `agents/explorer.md`, 18,041 B | `Read, Grep, Glob, Bash, WebFetch` | none in frontmatter; the 60-call ceiling is counted by the agent itself | `commands/*.md` | URL pin in `stride-marketplace` |
| `stride-gemini-exploratory-testing` | v0.2.1 | `agents/explorer.md`, 20,244 B | `read_file, grep_search, glob, run_shell_command, web_fetch` | **`max_turns: 60`, which the runtime enforces** | `commands/*.toml` | `stride-gemini-marketplace` `extensions.json` entry |
| `stride-opencode-exploratory-testing` | v0.2.1 | `agents/explorer.md`, 18,108 B | `read, grep, glob, bash, webfetch: true; edit: false` | none found | `commands/*.md` | its own repo only (install script); no marketplace |
| `stride-copilot-exploratory-testing` | v0.2.0 | `agents/explorer.agent.md`, 18,271 B | `["read", "search", "glob", "run"]` (no web fetch) | none found | none; command entry points are `skills/stride-exploratory-testing-*` | vendored in `stride-copilot-marketplace/plugins/` |
| `stride-codex-exploratory-testing` | v0.2.0 | `agents/explorer.md`, 19,149 B | `["read", "search", "glob", "shell"]` (no web fetch) | none found | none; command entry points are `skills/stride-exploratory-testing-*` | vendored in `stride-codex-marketplace` |

Every edition's explorer tells the agent to read
`skills/heuristics|oracles|bug-advocacy|session/SKILL.md` by a path relative to
the plugin (Claude Code `agents/explorer.md:13-14`; gemini and opencode
`:20-21`; copilot and codex `:12-13`). In the Claude Code edition that path does
not resolve from the project directory where the agent runs, which is the cause
of the severity drift above. **Whether it resolves in each other runtime is
unverified.** Check it per edition before porting W2261. If it does resolve, the
card is still worth porting for its size, but it is no longer an accuracy fix
there.

**Where each consumer lives.** The `stride` ports do not have `stride`'s
`optional-exploratory-testing.md`. In `stride-codex`, `stride-copilot`,
`stride-gemini` and `stride-opencode`, Step 5.5 lives in
`skills/stride-workflow/SKILL.md` and `skills/stride-subagent-workflow/SKILL.md`,
and the findings mapping lives in `skills/stride-completing-tasks/SKILL.md`. In
`stride-lite`, `stride-copilot-lite`, `stride-opencode-lite` and `stride-pi`,
only the single workflow skill mentions the plugin. Find each port's text with
`grep -rl exploratory-testing <port>/skills`.

---

## G449 — accuracy

### W2261 — an inline explorer card (planned)

**Planned change.** Add a card of at most about 4 KB to the explorer agent:

- the exact severity enum Critical | High | Moderate | Minor, with the ladder
  clauses and the modifier rule;
- one-line RIMGEA reminders;
- the three oracle classes;
- the stop rules.

Reading the four skills becomes optional depth rather than a dependency. Before
writing the card, verify how a plugin agent can reach plugin files, and record
the answer.

**Per edition.** All four variants carry the same "read the four skills"
instruction, so all four need the card or a verified path. Keep the tokens
**exactly** Critical, High, Moderate and Minor. `stride`'s escalation keys on
`Critical`, so a translated or lower-cased token turns escalation off. Confirm
which token each `stride` port keys on before porting.

### W2262 — the output contract and its fixture (planned)

**Planned change.**

- A table that derives `status` from `stop_reason`, covering every stop reason
  including an unauthorised target.
- `replicated` (for example `"1/5"`) and `provisional` (a boolean) on each bug.
- Defined element types for `questions_risks` and `off_charter`.
- A `known_issues` input and a `known_bad` output slot.
- `contract_version` in the output.
- `fixtures/example-explorer-output.json`, plus a lib test that checks its keys
  and enums against the agent file.

**Per edition.** Every variant has `fixtures/` and `lib/test-structure.{sh,ps1}`,
so the fixture and the test port directly. Run both shells. Use the same
`contract_version` value in every edition, so a `stride` port can trust it.

### W2263 — honest observation (planned)

**Planned change.** A charter that needs an observation the agent has no tool
for returns `blocked` with `stop_reason: "no_observation_surface"`. The consumer
treats that as not performed. HTTP is observed with `curl -sS -i`. A web-fetch
tool is never an oracle source, because it returns a summarised page and hides
status codes and headers. `stride` lists only the explorer's tools when it
decides what a charter can observe.

**Per edition.**
- **gemini** (`web_fetch`) and **opencode** (`webfetch: true`) have a fetch
  tool. Port the curl rule, and either drop the fetch tool from frontmatter or
  forbid it as an oracle source.
- **copilot** and **codex** have no fetch tool. Port only the
  `no_observation_surface` ending and the curl rule, which are already true of
  their tool set.
- In each `stride` port, the Step 5.5 text that decides whether a manual test is
  dispatchable must list the *explorer's* tools in that runtime, not the main
  loop's.

### W2264 — a structured safety boundary (planned)

**Planned change.**

- Required `AUTHORIZED_NON_PRODUCTION: yes` and `ALLOWED_HOSTS:` lines; without
  them the session returns `blocked`.
- The explorer stops processes and removes files it started before returning.
  In 0.2.1, a 45 KB probe file was left in `.exploratory/` for a month.
- Interrupt, Starve and Saboteur are limited to in-app means.
- Credential files are never read in full; only a value the dispatch names.

**Per edition.**
- Port the rules to every variant's agent file and its `skills/heuristics`.
- Each `stride` port's Step 0 already collects the authorization answer. Its
  Step 5.5 dispatch must pass the two structured lines.
- **opencode** already denies edits (`edit: false`). Keep that. W2266 needs one
  narrowly scoped write, so re-check how this runtime can allow that write
  without opening general edits.

### W2265 — the consumer and the drift check (planned)

**Planned change.**

- `stride`'s Step 5.5 and findings text adopt the exact enum, the status table,
  `no_observation_surface`, and the provisional-Critical rule: an unreplicated or
  provisional Critical is recorded as an advisory, while a replicated one still
  escalates.
- The 0.1.x wall-clock and `stopped_early` branches are removed.
- A `stride` hook-suite check compares `stride`'s enums with this repo's fixture,
  and skips cleanly when the repo is absent.

**Per edition.**
- This is `stride`-side work, so it ports to each `stride` port's own Step 5.5
  and findings text, not to the exploratory-testing variants.
- Point each port's drift check at **its own** exploratory edition's fixture: a
  `stride-gemini` check reads `stride-gemini-exploratory-testing`'s fixture, and
  so on.
- Ports without a hook suite carry the enum text and note in their changelog
  that drift is not checked mechanically.

---

## G450 — speed

### W2266 — report file and bounded summary (planned)

**Planned change.** When the caller supplies an absolute
`EXPLORATORY_REPORT_PATH`, the explorer writes its full JSON there and returns
about 2 KB: status, stop reason, counts, `contract_version`, and one line per bug
with severity and replication. A failed write is reported on its own line and
falls back to inline output. With no path supplied, the output stays inline as
before. The caller reads only the path it supplied and deletes the file after a
successful completion.

**Per edition.** Every variant currently has no write tool in its explorer
frontmatter. Each needs the narrowest write the runtime allows; check each
runtime's tool vocabulary and permission model before porting:

- Claude Code: `Write`.
- gemini: a file-write tool.
- opencode: `edit: false` today.
- copilot and codex: a write tool, or `run`/`shell` with an explicit
  one-path rule.

Keep the variable name `EXPLORATORY_REPORT_PATH` in every edition so the `stride`
ports share one contract.

### W2267 — fewer, parallel charters (planned)

**Planned change.** Manual tests that share a target merge into one charter. At
most about three charters run per task; any remainder is recorded as a human
responsibility. Independent observe-only charters are dispatched in one message,
and the main loop does no edits to files the charters exercise while they run.

**Per edition.** This is `stride`-side Step 5.5 text, so it ports to each
`stride` port. Parallel dispatch needs a runtime that can run several subagents
at once; check each runtime before promising it. Where it cannot, keep the
grouping and the cap, and run the charters in sequence.

### W2268 — verify mode (planned)

**Planned change.** A re-check of a fixed Critical builds a charter from that
bug's `minimal_repro`, runs one or two probes, and returns pass or fail with
evidence. When no repro exists, it falls back to the full charter.

**Per edition.** This is an agent-file change in every variant, plus each
`stride` port's re-check text. The gemini edition's `max_turns: 60` already
bounds a verify session from above; no extra bound is needed there.

### W2269 — `/harden` unattended (planned)

**Planned change.** Step 5.6 passes the persisted report path and an explicit
`--framework`. `/harden` never prompts when it has both.
`manual-testing-findings.md` no longer says the explorer writes no file.

**Per edition.**
- gemini (`commands/harden.toml`) and opencode (`commands/harden.md`) have the
  command.
- copilot and codex carry it as the skill `stride-exploratory-testing-harden`;
  port the no-prompt path there. Codex has no `allowed-tools` key, so a safety
  rule that the Claude Code edition enforces through an allowlist must be stated
  in prose in the codex skill.

---

## G451 — token usage

### W2270 — ranged reads and a dispatch template (planned)

**Planned change.** The explorer locates text with `grep -n` and reads bounded
ranges. It never re-reads a file it has already read in the session, unless the
file has changed. `stride` uses a fixed dispatch template: the charter, the
structured safety lines, the report path, and pointers rather than pasted
content.

**Per edition.** The reading rule ports to every agent file. Translate the
command names into each runtime's tool vocabulary (`grep_search`, `search`, and
so on). The template ports to each `stride` port's Step 5.5.

### W2271 — a lighter Step 5.5 contract (planned)

**Planned change.** `stride`'s `optional-exploratory-testing.md` (47,699 B) and
`manual-testing-findings.md` (21,286 B) move their history and rationale into
docs, and keep every gate, enum and redaction rule inline.

**Per edition.** Port the *method* to each `stride` port's own Step 5.5 text,
which is voiced differently: find its rationale paragraphs, move them to that
port's docs, and keep every rule inline. Do not copy `stride`'s trimmed bytes.

### W2272 — trimmed descriptions and skills (planned)

**Planned change.**
- Shorten the always-loaded agent and command descriptions, keeping their
  triggering conditions.
- Move the on-disk-artifacts section of `skills/session` and the worked-example
  and tone section of `skills/bug-advocacy` into linked references.

**Per edition.** Every variant has the same five skills plus the command entry
points, so measure each edition's own sizes with `wc -c` before and after. In
copilot and codex, the command entry points are skills, so their descriptions
are always loaded too. Trim those as well.

### W2273 — measurement (planned; last)

**Planned change.** Once the three goals are released and installed, measure at
least three Step 5.5 sessions against the baseline above, naming the comparator
for every figure.

**Per edition.** A variant's measurement needs that runtime's own transcripts.
Do not claim a variant saving from the Claude Code numbers.

---

## Releasing a variant

One release per edition per batch: commit per task, then make one version bump,
changelog entry, tag and release at the end.

| Edition | Release |
|---|---|
| Claude Code | This repo: bump `plugin.json`, changelog, tag, GitHub release. Then `stride-marketplace`: set this plugin's pinned version, bump `metadata.version`, update the changelog and README, tag, release. |
| gemini | Repo: tag and release. Then `stride-gemini-marketplace`: update this extension's entry in `extensions.json` (written with Python's default `ensure_ascii=True`) and the README extensions table, tag, release. |
| opencode | Repo only: tag and release. There is no marketplace, and the version lives in `CHANGELOG.md`. |
| copilot | Repo, then sync its vendored copy in `stride-copilot-marketplace/plugins/`. |
| codex | Repo: bump `.codex-plugin/plugin.json` (exactly four keys), tag, release. Then `stride-codex-marketplace` per its `RELEASE.md`: rsync the vendored copy, update the README version cell, verify, secret-scan, tag, release. |

## Rules for this batch

1. **Port from landed sections only.**
2. **Verify every mechanism a ported sentence names exists in that edition**:
   tools, turn bounds, write permission, parallel dispatch. The editions differ
   on all four.
3. **Keep the exact severity tokens and `contract_version` identical across
   editions.** The `stride` ports key their escalation on those tokens.
4. **Port the explorer and Step 5.5 changes before anything that touches the
   commands.** The commands and the charter-generator had no recorded use in
   this period.
5. **Record what an edition cannot carry** in its changelog, so "not applicable"
   is distinguishable from "missed". Examples: no write tool, no parallel
   dispatch, no hook suite.
