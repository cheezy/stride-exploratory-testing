# Porting G503 to the other exploratory-testing variants

This guide covers goal G503. During goal G489, Step 5.5's implementation-time
sessions found none of the 29 bugs that an exploratory campaign found after the
goal shipped. G503 changed two plugins so that those sessions would catch them:

- **Plugin side**, in this repository (the Claude Code edition): change-risk
  lenses, two oracles, a project environment file with a signed-in probe
  harness, and a change mode for the charter-generator. Released in v0.5.0
  (2026-11-05).
- **`stride` side**: Step 5.5 builds its charters from edge cases and change
  risk, reads `.exploratory.md` at Step 0, adds a visual pass, a recorded
  outcome per charter, a goal-scope pass, and charter-ready manual tests at
  task authoring. Released in `stride` 1.87.0 (2026-11-05).

The four port goals (gemini, opencode, copilot, codex) were filed before any of
G503 had landed. This guide records what actually shipped, so that each port
copies the released behaviour rather than the G503 task text.

**Ports shipped so far:** opencode, in `stride-opencode-exploratory-testing`
v0.5.0 (2026-11-06). The editions tables below still show every edition as it
was checked before its port, so read opencode's current state from its own
repository.

**Port from landed sections only.** Every section below describes shipped
behaviour at this repository's commit `88e47cc` (the v0.5.0 release). That
includes `d560bd0`, which rewrote parts of W2580 after it landed, so port from
the release, not from one task's commit.

## Status

| Task | Side | Change | Commit | Status |
|---|---|---|---|---|
| W2578 | plugin | Twelve change-risk lenses in the heuristics catalog, each with a *When it applies* trigger | `752cb55` | released in v0.5.0 (2026-11-05) |
| W2579 | plugin | Two oracles, Adapter Is Not the Wire and Two Decision Sites, in the oracles skill and the explorer card | `88bf46a` | released in v0.5.0 (2026-11-05) |
| W2580 | plugin | `.exploratory.md`, the explorer's optional `PROBE_HARNESS` surface, `session_sheet.surfaces_used`, contract `1.1` | `ca8d62e` | released in v0.5.0 (2026-11-05) |
| W2581 | plugin | The charter-generator's change mode: `change context` input, `change-risk` source, `surface` and `edge_cases_covered` | `1fa19e4` | released in v0.5.0 (2026-11-05) |
| W2582 | `stride` | Step 5.5 fires on manual tests or edge cases and runs the charter-generator in change mode, with a real budget | `b80107d` | `stride` only; released in `stride` 1.87.0 (2026-11-05) |
| W2583 | `stride` | Step 0 reads a confirmed `.exploratory.md`; Step 5.5 sends the harness lines and refuses a signed-out session on an auth-gated charter | `bf66722` | `stride` only; released in `stride` 1.87.0 (2026-11-05) |
| W2584 | `stride` | A bounded main-loop visual pass for a `no_observation_surface` session | `f756394` | `stride` only; released in `stride` 1.87.0 (2026-11-05) |
| W2585 | `stride` | One outcome line per charter, a coverage line, an owner for every charter not performed, checked by `exploratory_outcomes_ok` | `fe5de2e` | `stride` only; released in `stride` 1.87.0 (2026-11-05) |
| W2586 | `stride` | A goal-scope pass when the task is its goal's last open child | `ec65ec1` | `stride` only; released in `stride` 1.87.0 (2026-11-05) |
| W2587 | `stride` | Task authoring writes charter-ready manual tests and lens-driven edge cases | `1db0f72` | `stride` only; released in `stride` 1.87.0 (2026-11-05) |
| W2588 | `stride` | A replay of the new Step 5.5 against G489 | `56b5763` | measured 2026-11-05; `stride` docs only; in no release |

Two commits carry no task:

- `d560bd0` made the plugin's rules and examples app-neutral. It replaced
  W2580's worked example, which was one specific web app, with a generic one,
  and added an *App neutrality* scan to `lib/test-structure.sh`.
- `88e47cc` is the v0.5.0 release. `stride-marketplace` pins 0.5.0 at its
  commit `fddbeee`.

W2588 landed after the `stride` 1.87.0 release commit (`1bf5191`). No tag
contains it, and the `stride` changelog has no entry for it.

## The editions, as checked on 2026-11-06

Paths are relative to each repository's root. Each cell comes from `ls`,
`grep`, `wc -c` or the card-measuring `awk` in `lib/test-structure.sh`.
Re-check a cell before relying on it. Every repository was clean and level with
its remote when checked.

### Agents

| Edition | Version, HEAD | Explorer agent | Explorer tools (frontmatter) | Outer turn bound | Charter-generator tools | Explorer card / cap | `contract_version` |
|---|---|---|---|---|---|---|---|
| `stride-exploratory-testing` (Claude Code) | 0.5.0, `88e47cc` | `agents/explorer.md`, 54,432 B | `Read, Grep, Glob, Bash, Write` | none in frontmatter; the agent counts its own tool-call ceiling | `Read, Grep, Glob` | 4,305 B / 4,352 | `"1.1"` |
| `stride-gemini-exploratory-testing` | 0.3.2, `450a413` | `agents/explorer.md`, 61,433 B | `read_file`, `grep_search`, `glob`, `run_shell_command` | `max_turns: 60`, `timeout_mins: 30` | `read_file`, `grep_search`, `glob`; `max_turns: 15`, `timeout_mins: 5` | 4,092 B / 4,096 | `"1.0"` |
| `stride-opencode-exploratory-testing` | 0.4.0, `2482772` | `agents/explorer.md`, 54,261 B | `read, grep, glob, bash: true`; `webfetch, edit, write: false` | none found | `read, grep, glob: true`; `bash, edit, write: false` | 4,094 B / 4,096 | `"1.0"` |
| `stride-copilot-exploratory-testing` | 0.3.0, `0bae867` | `agents/explorer.agent.md`, 30,830 B | `["read", "search", "glob", "execute"]` | none found | `["read", "search"]` (no `glob`) | 4,091 B / 4,096 | `"1.0"` |
| `stride-codex-exploratory-testing` | 0.3.0, `3174ef4` | `agents/explorer.md`, 49,658 B | `["read", "search", "glob", "shell"]` | none found | `["read", "search", "glob"]` | 4,071 B / 4,096 | `"1.0"` |

### Packaging

| Edition | How the explorer writes a file | Policy or permission files | `/explore` Step 3 | Installer copies | `docs/`, `templates/` | Changelog head |
|---|---|---|---|---|---|---|
| Claude Code | `Write`, for the report only; probe files go through `Bash` | `allowed-tools` in each command's frontmatter | `commands/explore.md:45` | none; installed from `stride-marketplace` | both exist | `[0.5.0]` |
| gemini | one `run_shell_command` heredoc | `policies/explorer.toml`: deny rules on `run_shell_command` for recursive `rm`, `rm` with a glob, `pkill`/`killall`, `git push`, and `kill` of PID 0 or a negative PID | `commands/explore.toml:37` | `install.sh:88`: `commands skills agents lib fixtures policies`, plus the manifest, `GEMINI.md` and `LICENSE` | neither | `[Unreleased]`, then `[0.3.2]` |
| opencode | one `bash` heredoc | frontmatter only (`edit: false`, `write: false`) | `commands/explore.md:39` | `install.sh:59-67`: `skills`, `commands`, `agents/*.md`, `lib`, `fixtures`, and `AGENTS.md` | neither | `[0.4.0]` |
| copilot | one `execute` command, a `noclobber` heredoc | none | `skills/stride-exploratory-testing-explore/SKILL.md:47` | no installer; `plugin.json` declares `agents/` and `skills/` | neither | `[0.3.0]` |
| codex | one `shell` command, never an edit or patch tool | none | `skills/stride-exploratory-testing-explore/SKILL.md:47` | `install.sh:57-80`: each skill's `SKILL.md` and `references/`, `agents/*.md`, `AGENTS.md`; not `lib/` or `fixtures/` | neither | `[0.3.0]` |

No explore entry point in the four ports has an `allowed-tools` key. The
plugin's is `Bash(date:*), Bash(mkdir:*), Read, Write, Glob, Grep, Skill, Agent`.
A rule that the plugin enforces through that allowlist must be stated in prose
in a port. The copilot and codex *harden* skills do carry `allowed-tools`; their
explore skills do not.

**No port carries any G503 string yet.** This command finds nothing in any of
the four: `git -C <port> grep -E 'PROBE_HARNESS|\.exploratory\.md|surfaces_used|change-risk|Adapter Is Not|Two Decision|probe_file'`.

**Since the last guide.** Most cells in
[`porting-g449-g451.md`](porting-g449-g451.md)'s editions table, checked on
2026-10-02, have since changed:

- Every version has moved.
- Every explorer has grown: copilot's by about 1.7 times, the others by about
  2.6 to 3 times.
- gemini dropped `web_fetch`. opencode turned `webfetch` off and added
  `write: false`. copilot's shell tool is now `execute`, not `run`.
- The Claude Code edition dropped `WebFetch` and gained `Write`.
- The explorers no longer read skills by a plugin-relative path. gemini's
  uses `${extensionPath}/skills/<name>/SKILL.md`; opencode's, copilot's and
  codex's load skills by name. Every charter-generator, the plugin's included,
  still cites `skills/chartering/SKILL.md` as a plain relative path.

Use the tables above, not that one.

**Where each consumer lives.** The `stride`-side tasks port to the `stride`
ports, not to these variants. In `stride-gemini` (v1.53.0), `stride-opencode`
(v1.42.0), `stride-copilot` (v2.44.0) and `stride-codex` (v1.40.0),
`grep -rl exploratory-testing skills` names `stride-workflow`,
`stride-subagent-workflow`, `stride-completing-tasks`, `stride-creating-tasks`
and `stride-creating-goals`. gemini also has
`skills/stride-workflow/explorer-safety-lines.md`. No `stride` port carries any
of the 1.87.0 Step 5.5 text yet. These cells were checked with `grep` only, so
read each port's own files before porting.

---

## Heuristics and oracles

### W2578 — twelve change-risk lenses (released in v0.5.0 (2026-11-05))

**What shipped.** `skills/heuristics/SKILL.md` gains two sub-sections. Each row
has three columns, `| Heuristic | What to try | When it applies |`, a generic
`E.g.` example, and a trigger that starts "When a change …".

- `### General change-risk lenses`, at the end of *General Heuristics*, holds
  nine: Change the Rights, Shadow Decision, Who Else Is Watching, Pull the Rug,
  Every Surface, Every Locale, Developer Guidebook, Leave No Trace and Telemetry
  Semantics.
- `### Web change-risk lenses`, at the end of *Web Heuristics*, holds three:
  Other Verbs, After the Headers and Response Hardening.

The two older tables keep their two columns. *How to use this catalog* says to
start with the lenses when a charter follows a change. A third paragraph in
*Safety of security-flavored heuristics* keeps Pull the Rug and After the
Headers inside Interrupt's in-app limits. It also limits Other Verbs and
Response Hardening to authorized testing of your own system. `HEURISTICS.md`
gains a *Change-risk lenses* bullet naming all twelve. `lib/test-structure.sh`
gains a *Change-risk lenses* section. It checks one row per lens, under its own
sub-heading and in heading order, with an example and a trigger; that the three
web-only lenses never sit under General; that no lens name collides with a
Tour; that the safety framing is there; and that no task identifier or project
name leaks.

**Per edition.**

- All four ports have the same two-column tables (gemini, opencode and copilot
  at `skills/heuristics/SKILL.md:28` and `:51`; codex at `:32` and `:55`, after
  its *STOP — orchestrator check*). Add the two three-column sub-tables at the
  end of the General and Web sections. Do not widen the older tables.
- Keep the twelve lens names exact. W2581's `lens` field and `stride`'s W2587
  authoring rule quote them by name.
- Add the bullet to each `HEURISTICS.md`.
- Port the test section to both `lib/test-structure.sh` and `.ps1`.
- The lens examples are app-neutral. Keep them that way. Whether a port's
  structure test has a neutrality scan is unchecked.

### W2579 — two oracles: Adapter Is Not the Wire, Two Decision Sites (released in v0.5.0 (2026-11-05))

**What shipped.** `skills/oracles/SKILL.md` gains `## Adapter Is Not the Wire`
and `## Two Decision Sites`, each with an example, between *Approximations* and
the quality-criteria checklist.

- *Adapter Is Not the Wire*: a result seen only through an in-process test
  adapter does not establish streamed or chunked bodies, `HEAD`, connection
  aborts or `Content-Length`. Confirm the claim on a real server you may reach,
  or record it under `debrief.unknown`, never under `found`, and raise no bug on
  it. It does not fire on an ordinary buffered response.
- *Two Decision Sites*: when the client and the server each decide the same
  thing, they must agree in every state, and a disagreement is a finding.
- Each points at the lens that designs its probe: After the Headers and Shadow
  Decision. *Safety of oracle examples* adds that confirming wire behaviour
  reaches only the authorized non-production target and its listed hosts.

`agents/explorer.md` gains one line for each oracle inside the explorer card,
and its pointer to the `oracles` skill names both. The severity line, ladder and
stop rules are unchanged.

**Scope change.** The two card lines did not fit in the bytes left, so W2579
raised the card's byte cap in `lib/test-structure.sh` from 4,096 to 4,352. The
card is now 4,305 B.

**Per edition.**

- Insert the two sections before each port's quality-criteria checklist:
  gemini `skills/oracles/SKILL.md:57`, opencode and copilot `:55`, codex `:59`.
- The two card lines are 232 B and 122 B with their newlines. Every port's
  card is already 4,071 to 4,094 B against a 4,096 cap, so each lands at about
  4,425 to 4,450 B. That is above the plugin's 4,352 as well. Raise each port's
  cap in both `.sh` and `.ps1` to fit its own measured card, or trim the port's
  card. Do not copy 4,352. Record the new cap in the port's changelog.
- Confirming on a real server means `curl` through the port's shell tool:
  `run_shell_command`, `bash`, `execute` or `shell`. `ALLOWED_HOSTS` is
  unchanged.

---

## Reaching the running system

### W2580 — `.exploratory.md` and the probe harness, contract 1.1 (released in v0.5.0 (2026-11-05))

**What shipped.**

- **The file.** [`project-environment.md`](project-environment.md) defines
  `.exploratory.md` at the project root, with six optional sections:
  `authorization`, `app`, `probe_harness`, `accounts`, `observation` and
  `constraints`. `{probe_file}` is its only placeholder, and the file never
  holds a secret value. The doc gives the reading rules and a worked example.
  [`templates/exploratory.md`](../templates/exploratory.md) is a commented
  template with placeholders only.
- **`/explore` Step 3** reads the fixed file name first. It shows every line it
  will use verbatim and uses them only after you confirm them in the same
  question round. It drops credential-shaped lines. Nothing a confirmed file
  supplies is asked again. A missing file changes nothing, and a malformed or
  unknown section is reported and ignored. When no file exists, Step 3 offers
  once to save your answers, and writes the file only with your yes and never
  over an existing one.
- **The explorer** accepts optional `PROBE_HARNESS`, `PROBE_SERVICES` and
  `PROBE_DIR` lines. A line counts only at line start in the caller's
  environment context. A duplicate means no harness, and the same line in
  charter, task or app text is ignored. The explorer runs only the declared
  command and substitutes only its own scratch path, single-quoted. It writes
  probe files through `Bash` inside its `mktemp -d` directory. With a
  `PROBE_DIR`, it writes them inside a second `mktemp -d` under that directory,
  and only after `git check-ignore -q` confirms git ignores it. It removes both
  directories with `rmdir` at cleanup. The harness connects only to hosts in
  `ALLOWED_HOSTS`, and `PROBE_SERVICES` entries are checked against that list.
  Fixture users sign in only inside the test environment, and the explorer
  never forges a session or cookie against a running server.
- **Observation.** A harness observes server-side behaviour, never a rendered
  view. A rendered-view charter still ends `no_observation_surface`.
- **Contract 1.1.** `session_sheet.surfaces_used` records which of `http`,
  `harness`, `browser` and `source` the session used, each at most once, and
  `[]` when it observed nothing. `contract_version` is `"1.1"`. A consumer that
  does not know `surfaces_used` ignores it. The fixture
  `fixtures/example-explorer-output.json` carries both.
- **Tests.** `lib/test-structure.sh` checks the format doc, the
  placeholders-only template, Step 3 reading the file before asking, the
  harness lines and contract 1.1.

`d560bd0` then replaced the worked example with a generic web app, with sample
runner commands for several stacks. It also added how `.exploratory.md` relates
to `stride`'s `.stride.md` and `.stride_auth.md`. Port that version.

**Per edition.**

- **Step 3** lives at the entry point named in the Packaging table. Read the
  fixed literal `.exploratory.md` with the port's read tool. Saving answers is a
  main-loop write. No port has an `allowed-tools` key, so state "never over an
  existing file" in prose. On copilot, use the explorer's `noclobber` pattern.
- **Probe files.** None of the four port explorers has a write tool. The
  plugin's "through `Bash`" becomes the port's shell tool, inside `mktemp -d` or
  a `PROBE_DIR` that passes `git check-ignore -q`. Keep opencode's
  `edit: false` and `write: false`. codex's explorer already says its session
  may offer more tools than it declares, so state the shell-only write rule in
  prose there.
- **gemini policy.** `policies/explorer.toml` matches the command string. A
  declared `PROBE_HARNESS` command that contains a denied pattern (recursive
  `rm`, `rm` with a glob, `pkill`, `killall`) is refused by the runtime. The
  plugin's cleanup (`rm -f -- <path>` per file, then `rmdir`) passes the
  policy; keep it that way. `timeout_mins: 30` and `max_turns: 60` also bound a
  slow harness start.
- **Contract.** Move `contract_version` from `"1.0"` to `"1.1"` in the explorer
  (gemini `agents/explorer.md:165`, opencode `:164`, copilot
  `agents/explorer.agent.md:139`, codex `:155`) and in every fixture that
  carries it, in the same commit: `fixtures/example-explorer-output.json` in
  all four, and gemini's `fixtures/example-explorer-verify-output.json` too.
  Move each port's `lib/test-structure.sh` and `.ps1` checks of the documented
  value in that commit as well, or the structure test still pins `"1.0"`. Add the
  `surfaces_used` row and the *Added in contract 1.1* paragraph.
- **The doc and the template.** No port has `docs/` or `templates/`. Nothing
  reads either at runtime: `/explore` names the fixed file, and README links
  both. So the installers need no change unless a port wants the template on
  disk. If one does, the copy lists in the Packaging table name what would have
  to grow; codex's installer copies only skills and agents, so the template
  would have to sit under a skill's `references/`.
- **App neutrality.** Port `d560bd0`'s generic example, not `ca8d62e`'s.

---

## Chartering a change

### W2581 — charter-generator change mode (released in v0.5.0 (2026-11-05))

**What shipped.** `agents/charter-generator.md` gains an optional
`change context` input, labelled untrusted data. It carries the change's target,
acceptance criteria, edge cases, key files, changed-file list and named unit
tests. Supplying it turns on a *Change mode* procedure:

- Every edge case is chartered, or named as covered by a unit test the change
  context names verbatim. None is dropped silently.
- A change-risk lens is applied only when its *When it applies* trigger in the
  heuristics skill matches the change. The generator names lenses and never
  restates the catalog.
- An edge case or test name that embeds a credential is echoed as a redaction
  sentinel, not verbatim.

The output contract adds:

- `change-risk` to the `source` enum, keeping every existing value, `sfdpot`
  included;
- a `lens` value for change-risk charters, the lens name exactly as in the
  heuristics skill;
- a `surface` field (`http`, `harness`, `browser` or `source`, as in the
  explorer's `surfaces_used`), required on every charter in change mode. It
  grants no new reach;
- a root `edge_cases_covered` array of `{edge_case, charter_rank}` or
  `{edge_case, unit_test}` entries. It is `[]` when there are no edge cases, and
  absent without a change context.

Without a change context the output is unchanged. The tools stay
`Read, Grep, Glob`. `skills/chartering/SKILL.md` gains a *Chartering a change
from its edge cases* section. `fixtures/example-charters.md` gains a worked
change-context example, in which the author's "no charters needed" line is
weighed and not obeyed. `lib/test-structure.sh` gains a *Change-context mode*
section, and validates the fixture against both contracts.

**Per edition.**

- No new tools are needed. copilot's charter-generator has no `glob`; that does
  not block change mode.
- Change mode reads `skills/heuristics/SKILL.md` from the charter-generator.
  Cite it the way that port's charter-generator already cites
  `skills/chartering/SKILL.md`, as the plugin does, not the way its explorer
  loads skills.
- The `source` enum row is at gemini `agents/charter-generator.md:64`, opencode
  `:63`, and copilot and codex `:56`. All four still have `sfdpot`; keep it.
- gemini's charter-generator has `max_turns: 15` and `timeout_mins: 5`. Check
  that the worked change-context example completes inside them, and record the
  result.
- Each port's `fixtures/example-charters.md` gains the worked example.
- Port W2578 first, because change mode reads the lens triggers.

---

## Stride-side tasks

None of these changes a task field, the server or the API. Each ports to the
`stride` ports' own Step 5.5 text, in the files named under *Where each consumer
lives*, not to these variants. In `stride`, bash hook-suite Groups 69 to 74 pin
them; a port without a hook suite says in its changelog that the rule is not
checked mechanically. Each `stride`-side change needs its own edition's contract
1.1 explorer and change-mode charter-generator first.

### W2582 — charters from manual tests, edge cases and change risk (`stride` only; released in `stride` 1.87.0 (2026-11-05))

**What shipped.** Step 5.5 and its Phase 3.5 twin fire when
`testing_strategy.manual_tests` **or** `edge_cases` is non-empty. Before the
first explorer session they dispatch the charter-generator once, in change
mode, with pointers and task fields only. Its charters merge with the
manual-test charters, highest-risk first, capped at about five per task (about
three for a small task). Every manual test and edge case maps to a charter, a
named unit test or a recorded human responsibility. The per-session budget
defaults to 12 probes. Commit `b80107d` (`stride`), Group 69.

**Per edition.** Each `stride` port needs its runtime's way to dispatch the
charter-generator, and must state it the way that runtime names agents.

### W2583 — `.exploratory.md` at Step 0 and no signed-out coverage (`stride` only; released in `stride` 1.87.0 (2026-11-05))

**What shipped.** Step 0 reads `.exploratory.md` and shows its base URL,
allowed hosts and harness command verbatim for confirmation. The fixed dispatch
template gains a `Probe harness:` label line and the `PROBE_HARNESS`,
`PROBE_SERVICES` and `PROBE_DIR` lines. A charter whose `surface` is `harness`,
or whose target is signed-in only, is not dispatched when there are no test
accounts and no harness; it is recorded with the reason `no signed-in surface`.
The task-runner's `exploratory_env` gains `probe_harness` (at most 120 B),
`probe_services` (60 B) and `probe_dir` (40 B). Commit `bf66722` (`stride`),
Groups 70 and 58.

**Per edition.** The three line names must match the explorer's exactly. A port
with no task-runner skips the `exploratory_env` part and says so.

### W2584 — a main-loop visual pass (`stride` only; released in `stride` 1.87.0 (2026-11-05))

**What shipped.** When a session returns `no_observation_surface` and the main
loop holds a browser tool, the main loop observes the unobserved part itself,
bounded by the charter's probe budget and observe-only, in the user's own
signed-in browser, on a host in `ALLOWED_HOSTS`. Commit `f756394` (`stride`),
Group 71.

**Per edition.** Port it only where that runtime's main loop has a browser
tool. Elsewhere, keep the hand-back and record the gap in the changelog.

### W2585 — an outcome and an owner for every charter (`stride` only; released in `stride` 1.87.0 (2026-11-05))

**What shipped.** `completion_notes` carries one `Exploratory charter r<N>:`
line per charter, `completion_summary` one `Exploratory coverage:` line, and
every charter not performed gets an owner: a follow-up identifier or a
`HANDED BACK:` line. The checker `exploratory_outcomes_ok` gates completion.
A skipped Step 5.5 on a task with manual tests or edge cases records one
`Exploratory testing skipped: <reason>` line. Commit `fe5de2e` (`stride`),
Group 72.

**Per edition.** Keep the line prefixes byte-identical, because the checker
keys on them.

### W2586 — a goal-scope pass (`stride` only; released in `stride` 1.87.0 (2026-11-05))

**What shipped.** When the claimed task is its goal's last open child, Step 5.5
adds one goal-scope pass after the task's own charters: one more change-mode
charter-generator dispatch for cross-task charters, at most about five, from
every child's `key_files` and the lines changed since the goal's base. It
never pushes and never runs `after_goal`. Commit `ec65ec1` (`stride`),
Group 73.

**Per edition.** It needs the port's way to read a goal's slim tree. Port it
after W2582.

### W2587 — charter-ready manual tests at task authoring (`stride` only; released in `stride` 1.87.0 (2026-11-05))

**What shipped.** `stride-creating-tasks` and `stride-creating-goals` require
each `manual_tests` entry to be a risk charter, not a click script, and
`edge_cases` to name each change-risk lens whose trigger matches. The
task-decomposer and task-enricher agents carry the same two rules. The lenses
are named and pointed at, never copied. Commit `1db0f72` (`stride`), Group 74.

**Per edition.** Each `stride` port has the two creation skills and the two
agents (`.agent.md` in copilot). Point at the port's own exploratory edition's
heuristics skill.

---

## Measurement

### W2588 — a replay of Step 5.5 on G489 (measured 2026-11-05; `stride` docs only; in no release)

**What shipped.** `docs/measurement-g489-replay.md` in the `stride` repository,
commit `56b5763`. It replays the 1.87.0 Step 5.5 with v0.5.0's agents on G489's
six tasks at the code before the campaign's first fix. Its comparator is the 29
bugs the G489 exploratory campaign found.

- 14 explorer sessions ran. 17 more charters fell inside the cap but were not
  dispatched.
- Of the 29 bugs, 4 were found (1 of 2 High, 2 of 11 Moderate, 1 of 16 Minor),
  2 need a visual pass, and 23 were missed.
- The largest cause of misses was the cap: 13 bugs had a charter ranked beyond
  it. Three more were in `browser`-tagged charters that were never dispatched.
- None of the 29 was missed for the six causes G503 was built to fix: no
  signed-in surface, edge cases never chartered, no in-process surface, a
  missing lens, no goal-scope session, or nothing gating a hand-back.

**What it does not license.** The doc says so itself:

- It quotes no headline percentage, and with one goal and 14 sessions every
  figure is an observation, not an estimate.
- It is not a run of the installed plugins. Each session was a general-purpose
  agent told to follow the v0.5.0 agent file.
- It is not blind. v0.5.0 and 1.87.0 were designed from this campaign's misses,
  so it does not measure performance on unseen defects.
- It had no server, so no wire and no visual pass.
- It is Claude Code only. No port was replayed.
- No figure in it is a time comparison.

**Per edition.** Nothing to port. A port may not claim a catch rate, a
percentage, a saving or a speed-up from these numbers, and may not say it was
measured. A port's own measurement needs a replay in that runtime.

---

## Strings every edition keeps identical

The `stride` ports read these by name. A translated, re-cased or renamed string
breaks the consumer silently.

| String | Where it is defined here |
|---|---|
| The file name `.exploratory.md`, at the project root | `docs/project-environment.md`, `commands/explore.md` |
| Its six section names: `authorization`, `app`, `probe_harness`, `accounts`, `observation`, `constraints` | `docs/project-environment.md` § The six sections |
| `{probe_file}`, the only placeholder, exactly once in the harness command | `docs/project-environment.md`, `agents/explorer.md` |
| `PROBE_HARNESS`, `PROBE_SERVICES`, `PROBE_DIR` | `agents/explorer.md` inputs |
| `surfaces_used` and its four values `http`, `harness`, `browser`, `source` | `agents/explorer.md` session-sheet table |
| `contract_version` `"1.1"` | `agents/explorer.md`, `fixtures/example-explorer-output.json` |
| The `source` values `change-risk` and `sfdpot` | `agents/charter-generator.md` |
| The `change context` input and the `lens`, `surface` and `edge_cases_covered` fields | `agents/charter-generator.md` |
| The twelve lens names and the two oracle names | `skills/heuristics/SKILL.md`, `skills/oracles/SKILL.md` |
| Unchanged from G449: `EXPLORATORY_REPORT_PATH`, `AUTHORIZED_NON_PRODUCTION`, `ALLOWED_HOSTS`, and the severity tokens Critical, High, Moderate, Minor | `agents/explorer.md` |

## Releasing a variant

One release per edition per batch: commit per task, then make one version bump,
changelog entry, tag and release at the end. The marketplace rows were
spot-checked on 2026-11-06.

| Edition | Release |
|---|---|
| Claude Code | Done: v0.5.0 (`88e47cc`), pinned by `stride-marketplace` `fddbeee`. |
| gemini | Repo: bump `gemini-extension.json`, move the changelog's `[Unreleased]` section to the new version, tag, release. Then `stride-gemini-marketplace`: update this extension's entry in `extensions.json` (written with Python's default `ensure_ascii=True`) and the README extensions table, tag, release. |
| opencode | Repo only: tag and release. There is no marketplace, and the version lives in `CHANGELOG.md`. |
| copilot | Repo: bump `plugin.json`, changelog, tag, release. Then `stride-copilot-marketplace` per its `RELEASE.md`: re-vendor `plugins/stride-copilot-exploratory-testing/`, set the plugin entry version in `.github/plugin/marketplace.json` and the README table, tag in that repo's own series, release. |
| codex | Repo: bump `.codex-plugin/plugin.json` (exactly four keys), tag, release. Then `stride-codex-marketplace` per its `RELEASE.md`: rsync the vendored copy, update the README version cell, verify, secret-scan, tag, release. |

Each `stride` port releases its Step 5.5 changes by its own process.

## Rules for this batch

1. **Port from landed sections only**, at `88e47cc`, including `d560bd0`.
2. **Verify every mechanism a ported sentence names exists in that edition**:
   tools, turn bounds, write mechanism, policy files, installers and the card
   cap. The editions differ on all six.
3. **Keep the strings above identical across editions**, and move the
   explorer, every fixture that carries `contract_version` and the structure
   test's checks of it to `"1.1"` in the same commit.
4. **Port in order.** W2578 before W2581. Each variant's W2580 before its
   `stride` port sends the harness lines or reads `surfaces_used` (W2582 to
   W2586).
5. **Record what an edition cannot carry** in its changelog, so "not
   applicable" is distinguishable from "missed". Examples: no write tool, no
   browser in the main loop, a different card cap, no hook suite.
6. **Claim nothing from W2588** for any port.
