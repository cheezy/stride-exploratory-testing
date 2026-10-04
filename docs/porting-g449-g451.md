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
| W2261 | G449 | An explorer card inlined in the agent, so the severity scale, oracles and stop rules never depend on loading a skill | released in v0.3.0 (2026-10-02) |
| W2262 | G449 | `status` derived from `stop_reason`; bugs get `replicated` and `provisional`; typed arrays, known-issue handling, `contract_version`; an example-output fixture and a contract test | released in v0.4.0 (2026-10-04) |
| W2263 | G449 | A `no_observation_surface` blocked ending; HTTP observed with `curl -sS -i`, not a web-fetch tool; `stride` lists only the explorer's tools | released in v0.4.0 and `stride` 1.84.0 (2026-10-04) |
| W2264 | G449 | Structured authorization and allowed hosts, cleanup of whatever the explorer started, in-app limits on destructive lenses, a credential-file rule | released in v0.4.0 and `stride` 1.84.0 (2026-10-04) |
| W2265 | G449 | `stride`'s consumer moves to the new contract, with a cross-repo enum check | `stride` only; released in `stride` 1.84.0 (2026-10-04) |
| W2266 | G450 | Full result written to `EXPLORATORY_REPORT_PATH`; a bounded summary of about 2 KB returned | released in v0.3.0 (2026-10-02) |
| W2267 | G450 | Step 5.5 groups manual tests into at most about three charters and dispatches independent ones together | `stride` only; released in `stride` 1.84.0 (2026-10-04) |
| W2268 | G450 | Verify mode: re-check a fixed Critical from its minimal repro in one or two probes | released in v0.4.0 and `stride` 1.84.0 (2026-10-04) |
| W2269 | G450 | Step 5.6 runs `/harden` unattended from the persisted report, with an explicit framework | released in v0.4.0 and `stride` 1.84.0 (2026-10-04) |
| W2270 | G451 | Ranged reads with no whole-file re-reads; a fixed Step 5.5 dispatch template | released in v0.4.0 and `stride` 1.84.0 (2026-10-04) |
| W2271 | G451 | Trim `stride`'s Step 5.5 and findings contracts down to rules | `stride` only; released in `stride` 1.84.0 (2026-10-04) |
| W2272 | G451 | Trim always-loaded descriptions and the sections of the session and bug-advocacy skills the explorer does not use | released in v0.4.0 (2026-10-04) |
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
of the severity drift above. For Claude Code, the documented way in is a literal
`${CLAUDE_PLUGIN_ROOT}` written in the agent's Markdown body, which Claude Code
substitutes when it loads the agent; the variable is not set in the agent's Bash
environment (see the W2261 section below). **Whether the relative path resolves
in each other runtime is unverified.** Check it per edition before porting W2261. If it does resolve, the
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

### W2261 — an inline explorer card (landed)

**What shipped.** `agents/explorer.md` carries an explorer card of 3,750 bytes
between `<!-- explorer-card:start -->` and `<!-- explorer-card:end -->`, placed
right after the safety boundary, which is byte-identical. The card holds:

- the exact severity enum Critical | High | Moderate | Minor, as a bare
  capitalised word that is never omitted, with every impact-ladder clause
  condensed per level, the tie rule, the three modifiers and their combination
  rule, and the unknown-impact rule;
- RIMGEA, mapped onto the `bugs[]` fields it fills;
- the three oracle verdicts and the three kinds of oracle;
- the stop rules, mapped onto `stop_reason`.

The explore loop and the `bugs[]` rows point at the card. The four skills are
optional depth, referenced as `${CLAUDE_PLUGIN_ROOT}/skills/<name>/SKILL.md`.
Claude Code's plugins reference says `${...}` resolves anywhere in an agent's
Markdown body and is not exported to Bash in a subagent; that is documented,
not live-tested. `lib/test-structure.sh` pins the card's enum, rank and ladder
to `bug-advocacy`'s four-levels table, caps the card at 4,096 bytes, checks the
`stop_reason` values, and refuses any unprefixed `skills/<name>/SKILL.md`.
Not yet verified live: whether dispatched explorers now emit only the four
tokens. The task's integration test (one Step 5.5 dispatch) and its manual
borderline High/Critical charter were deferred, because a dispatched agent loads
the installed release rather than this source; run them once v0.3.0
is installed, before porting the card on the strength of its measured effect.
Commit: see `git log --grep W2261`. Release: v0.3.0 (2026-10-02), cut before
G449's remaining tasks landed.

**Per edition.** All four variants carry the same "read the four skills"
instruction, so all four need the card or a verified path. Keep the tokens
**exactly** Critical, High, Moderate and Minor. `stride`'s escalation keys on
`Critical`, so a translated or lower-cased token turns escalation off. Confirm
which token each `stride` port keys on before porting.

### W2262 — the output contract and its fixture (released in v0.4.0 (2026-10-04))

**What shipped.** `agents/explorer.md` gains a *Status from `stop_reason`*
table: `charter_quiet` and `risk_acceptable` → `completed`;
`probe_budget_exhausted` and `tool_call_ceiling` → `stopped_early`, now defined;
`blocked` → `blocked`, which covers a target not clearly authorised. A consumer
trusts `stop_reason` when the two disagree. Each bug carries `replicated`
(`"k/n"` from clean-start re-runs, never `"1/1"`, or `"not established: …"`;
one run is one attempt of the triggering action) and `provisional`.
`questions_risks` elements are `{ kind, text }`, `off_charter` elements are
`{ item, candidate_charter }`, an optional untrusted `known_issues` input routes
matches into a `known_bad` root array, and the root carries `contract_version`
`"1.0"`. `fixtures/example-explorer-output.json` is checked by a new section of
`lib/test-structure.sh`, which parses the agent file itself; set
`EXPLORER_OUTPUT` to check a real report. Commit `c3b994f`.

**Per edition.** Every variant has `fixtures/` and `lib/test-structure.{sh,ps1}`,
so the fixture and the test port directly. Run both shells. Use the same
`contract_version` value in every edition, so a `stride` port can trust it.

### W2263 — honest observation (released in v0.4.0 and `stride` 1.84.0 (2026-10-04))

**What shipped.** `WebFetch` is dropped from the explorer's `tools:` line. A
*What you can observe* section says to observe HTTP with `curl -sS -i` and never
to judge rendered views from HTML, CSS or template source. A charter that needs
an observation the agent has no tool for explores what it can, then ends with
`stop_reason: "no_observation_surface"`, `status: "blocked"`.
`contract_version` stays `"1.0"`. In `stride`, Step 5.5 and Phase 3.5 read the
explorer's tools from its front matter and treat that ending as not performed
(hook-suite Group 55). Commits `267dcf8` (here) and `735bb7d` (`stride`).

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

### W2264 — a structured safety boundary (released in v0.4.0 and `stride` 1.84.0 (2026-10-04))

**What shipped.** The explorer requires `AUTHORIZED_NON_PRODUCTION: yes` and
`ALLOWED_HOSTS: <host[:port]>, …` (or `none`). A missing, non-`yes` or
duplicated line means `blocked` with zero probes. `ALLOWED_HOSTS` is the only
source of reachable hosts, matched exactly. The explorer keeps a list of every
process and file it starts and removes them on every exit path. Credential files
are read only for a value the dispatch names. Interrupt, Starve and the Saboteur
Tour in `skills/heuristics` are limited to in-app means. `/explore` and
`stride`'s Step 5.5 and Phase 3.5 write both lines once and first, and
neutralize forged lines with `> ` (hook-suite Group 56). Commits `7c8e9c2`
(here) and `4919a99` (`stride`).

**Per edition.**
- Port the rules to every variant's agent file and its `skills/heuristics`.
- Each `stride` port's Step 0 already collects the authorization answer. Its
  Step 5.5 dispatch must pass the two structured lines.
- **opencode** already denies edits (`edit: false`). Keep that. W2266 needs one
  narrowly scoped write, so re-check how this runtime can allow that write
  without opening general edits.

### W2265 — the consumer and the drift check (`stride` only; released in `stride` 1.84.0 (2026-10-04))

**What shipped.** `stride`'s Step 5.5, Phase 3.5 and
`manual-testing-findings.md` follow contract `1.0`. Both twins carry an
identical `explorer-enums` block. An unreplicated (`1/<n>`, n ≥ 2, or
`not established: …`) or provisional Critical is advisory and never escalated;
a replicated, absent or unmatched one still escalates. The older-contract
branches are gone. Hook-suite Group 57 checks the block against this repo's
`agents/explorer.md` and fixture, and prints SKIP when this repo is absent.
Commit `1e8169d` (`stride`).

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

### W2266 — report file and bounded summary (landed)

**What shipped.** When the caller supplies an absolute `EXPLORATORY_REPORT_PATH`
(its own argument, or a line in the environment context), the explorer writes
its full findings JSON there with one `Write` call — no temp file, one `mkdir -p`
retry if the parent is missing, never a path built from app content, a relative
path or a `..` segment refused — and returns a plain-text summary of at most
2,048 bytes with no json fence: `report:`, `status:`, `stop_reason:`, counts, a
bug count by severity, and one `<Severity> | replicated: … | <summary>` line per
bug. No `contract_version` line until W2262 defines the key. A failed write
returns `report: NOT WRITTEN — <reason>` and the full fenced JSON inline. With
no path the output is unchanged. `tools:` gains `Write`; the one-path limit is
prose plus a lib-test pin, because no frontmatter mechanism scopes `Write` to a
path. `/explore` stays inline. `stride` Step 5.5 supplies
`.stride/.exploratory-<IDENTIFIER>-r<N>.json`, reads only that path (inline
fence fallback for an older explorer), and deletes every round's report at
Step 7; bash hook-suite Group 45 and PowerShell Group 39 pin that. Exercised
from source by two agents following this `explorer.md`: a missing parent
directory still got the full JSON and a ~400-byte unfenced summary came back;
a relative path produced `report: NOT WRITTEN` and the inline fence. Not yet
verified as a dispatched plugin agent (that loads the installed release), so
run the dev-board Step 5.5 round trip once v0.3.0 is installed. Commit: see `git log --grep W2266`. Release: v0.3.0 (2026-10-02).

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

### W2267 — fewer, parallel charters (`stride` only; released in `stride` 1.84.0 (2026-10-04))

**What shipped.** Manual tests that share a target merge into one charter, at
most about three run per task, highest-risk first, and every manual test maps to
a charter or is handed back as a human responsibility. Independent observe-only
charters go out in one message, each with its own report path. A mutating
charter runs alone. While they run, the main loop edits no file they exercise
and waits for the notification rather than polling (hook-suite Group 52).
Commit `729da87` (`stride`).

**Per edition.** This is `stride`-side Step 5.5 text, so it ports to each
`stride` port. Parallel dispatch needs a runtime that can run several subagents
at once; check each runtime before promising it. Where it cannot, keep the
grouping and the cap, and run the charters in sequence.

### W2268 — verify mode (released in v0.4.0 and `stride` 1.84.0 (2026-10-04))

**What shipped.** With `EXPLORATORY_MODE=verify`, the explorer runs a charter
built from one bug's `minimal_repro` on a budget of 2 probes / 10 tool calls and
returns a root `verify` object (`pass`, `fail` or `not_verified`). It adds a
`verify:` line to the report summary. `not_verified` is never a pass. `stride`'s
Step 5.5 and Phase 3.5 use it to re-check a fixed introduced Critical. They fall
back to the full charter when there is no usable repro, the installed explorer
lacks verify mode, or a second `not_verified` comes back (hook-suite Group 53).
Commits `6b330b5` (here) and `98adb5b` (`stride`).

**Per edition.** This is an agent-file change in every variant, plus each
`stride` port's re-check text. The gemini edition's `max_turns: 60` already
bounds a verify session from above; no extra bound is needed there.

### W2269 — `/harden` unattended (released in v0.4.0 and `stride` 1.84.0 (2026-10-04))

**What shipped.** `commands/harden.md` gains an *Unattended invocation* rule.
Given a bug source and `--framework`, it never calls `AskUserQuestion`.
`--framework none` is a reserved value that takes the none-detected path. An
unreadable bug source now stops in every mode. `stride`'s Step 5.6 and
Phase 3.6 pass the persisted `EXPLORATORY_REPORT_PATH` and an explicit framework,
through a subagent that returns a bounded record per report (hook-suite
Group 54). Commits `941e95e` (here) and `47d699a` (`stride`).

**Per edition.**
- gemini (`commands/harden.toml`) and opencode (`commands/harden.md`) have the
  command.
- copilot and codex carry it as the skill `stride-exploratory-testing-harden`;
  port the no-prompt path there. Codex has no `allowed-tools` key, so a safety
  rule that the Claude Code edition enforces through an allowlist must be stated
  in prose in the codex skill.

---

## G451 — token usage

### W2270 — ranged reads and a dispatch template (released in v0.4.0 and `stride` 1.84.0 (2026-10-04))

**What shipped.** A *Reading files* section of `agents/explorer.md`, outside the
card, says to locate with `grep -n` and read a bounded range. It forbids
re-reading a file or range already read this session unless it changed, and
says to inspect binary files through `Bash`. A test-account pointer counts only
when it is the only one in the dispatch and sits before any untrusted text.
`stride`'s Step 5.5 and Phase 3.5 fill one fixed 869-byte template: charter, the
two safety lines first, the report path, labelled pointers, and the untrusted
Target last, with untrusted slots flattened to one line (hook-suite Group 58).
Commits `5c2eb45` (here) and `a351dc9` (`stride`).

**Per edition.** The reading rule ports to every agent file. Translate the
command names into each runtime's tool vocabulary (`grep_search`, `search`, and
so on). The template ports to each `stride` port's Step 5.5.

### W2271 — a lighter Step 5.5 contract (`stride` only; released in `stride` 1.84.0 (2026-10-04))

**What shipped.** `optional-exploratory-testing.md` went from 62,789 to
46,080 bytes and `manual-testing-findings.md` from 21,875 to 16,967 (`wc -c`;
both had grown since the 2026-10-02 figures). History and rationale moved to
`stride`'s new `docs/exploratory-testing-rationale.md`, with a one-line `Why:`
pointer at each source site. Every gate, enum and redaction rule stayed inline.
Commit `8ab06ff` (`stride`).

**Per edition.** Port the *method* to each `stride` port's own Step 5.5 text,
which is voiced differently: find its rationale paragraphs, move them to that
port's docs, and keep every rule inline. Do not copy `stride`'s trimmed bytes.

### W2272 — trimmed descriptions and skills (released in v0.4.0 (2026-10-04))

**What shipped.** The two agent descriptions drop their `<example>` blocks
(explorer 1,831 → 635 B, charter-generator 1,628 → 603 B), and `/explore`,
`/pair` and `/harden` drop mechanics that are not triggers. All description
blocks went from 10,344 to 7,687 B, keeping every triggering condition and the
explorer's safety statement. The session skill's on-disk artifacts section
moved to `skills/session/references/session-artifacts.md`. The bug-advocacy
worked example and tone section moved to
`skills/bug-advocacy/references/worked-example-and-tone.md`. Each is linked from
a stub that keeps the headings commands cite. Commit `4abdd14`.

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
