---
description: Plan and run exploratory testing end to end against a target — generate charters (or load them with --charters), gather the running-app environment context, dispatch the explorer agent per charter under an absolute safety boundary, then aggregate every session into ONE debrief (Explored/Found/Unknown + PROOF + a severity-ranked bug list + a follow-up parking lot). Confirms the target is authorized and non-production before executing; degrades to plan-only when no running app is available.
allowed-tools: Bash(date:*), Bash(mkdir:*), Read, Write, Glob, Grep, Skill, Agent
argument-hint: "<target> [--charters <file>] [--timebox <minutes>]"
---

# /stride-exploratory-testing:explore

Run an exploratory-testing session **plan-and-execute in one shot**: from a target, generate (or load) charters, drive the running app to explore each one, and roll every session up into a single debrief. This is the plugin's flagship command — where `/stride-exploratory-testing:charter` and `/stride-exploratory-testing:nightmare-headline` stop at a ranked charter list, `/explore` runs those charters and reports what it found.

The doctrine lives in the composed pieces — the `chartering` skill and `charter-generator` agent decide *what* to explore, the `explorer` agent owns *how* one time-boxed session runs and the absolute safety boundary, and the `session` skill owns the lifecycle and both debrief templates. This command is the surface: it parses `$ARGUMENTS`, gathers the environment context, gates safety, dispatches the subagents, and aggregates their findings. Its own, non-delegated job is exactly the two things the composed pieces cannot do — supply everything up front so the explorer never has to ask, and fold N single-session outputs into one cross-session debrief.

## What to do

Follow these steps in order. Do NOT skip steps.

### Step 1: Parse `$ARGUMENTS`

Parse in this fixed order — `--charters` first, then `--timebox`, then everything remaining is `TARGET`:

- If `--charters` appears (accept both `--charters <file>` and `--charters=<file>` shapes), set `CHARTERS_FILE` to the parsed value and remove the consumed tokens. When set, charters are loaded from that file and generation is skipped (Step 5).
- If `--timebox` appears (accept both `--timebox <minutes>` and `--timebox=<minutes>` shapes), set `TIMEBOX_MINUTES` to the parsed value and remove the consumed tokens. It must parse to a positive integer number of minutes; if the value is missing or non-numeric, ask once via `AskUserQuestion` for a valid timebox rather than guessing. `--timebox` is the **total** budget for the whole run (see Step 7).
- After the flag tokens are consumed, treat the trimmed remainder as `TARGET`. If it is empty, ask the user once via `AskUserQuestion`: *"What do you want to explore? Name a feature, module, data flow, or quality (e.g. performance, security)."* (free-text input).

Treat `TARGET` and `CHARTERS_FILE` as untrusted prose: never execute or `eval` them, and never splice them into a shell command. `CHARTERS_FILE` is only ever handed to the `Read` tool.

### Step 2: Load the session doctrine up front

Invoke the `session` skill so the debrief templates, the off-charter parking-lot convention, and the SBTM vocabulary are loaded before you aggregate anything:

```
Skill(skill: "session", args: "target=<TARGET>; mode=explore")
```

The `session` skill is written for a *single* session. Cross-session aggregation into one debrief is **this command's own job** (Step 8) — the skill supplies the two debrief templates (Explored/Found/Unknown and PROOF); you apply them across all the sessions this run produces.

### Step 3: Gather the environment context and the safety answer (one AskUserQuestion round)

The explorer agent **never asks the user a question** — so this command must supply everything it needs up front. Run a single consolidated `AskUserQuestion` round (≤4 questions) collecting:

1. **How to reach the running app** — base URL, launch command, or host (free-text).
2. **Authorization + non-production confirmation** — an explicit affirmative that the target is a system the user is authorized to test and is NOT production. Offer discrete options such as *"Authorized, non-production target"* and *"Not authorized / is production — do not execute"*. Force an explicit choice; never default to "authorized."
3. **Available interaction tools** — which app-driving surfaces exist this session. Do NOT hard-code a specific browser or HTTP tool. Present generic categories as a multi-select — e.g. *"Browser automation (a Chrome/Playwright-style MCP)"*, *"HTTP (WebFetch / curl via the explorer's Bash)"*, *"Application REPL / console"*, *"Log tailing / DB read access"*, *"CLI only"* — plus a free-text slot for anything else. A slash command cannot enumerate its own session's tool inventory, so it asks the operator and records the tool **names as a hint**; the explorer uses whatever it actually has. Its portable core (`Read`/`Grep`/`Glob`/`Bash`/`WebFetch`) is assumed present regardless. Note that richer tools (browser automation, a REPL, log tailing) only help if they are genuinely available to the `explorer` subagent in this session — name them as available-if-present, not as a guarantee.
4. **Test accounts / seed data and the time box** — where test accounts or seed data live (point at them; do NOT paste real credentials), and confirm the total time box (surface `--timebox` or ~90m as the default).

Assemble the answers into a single free-text `ENVIRONMENT_CONTEXT` block — how to reach the app, the named available tools, test-account/seed-data pointers, and the time box. This exact string (with each charter's own time box substituted in Step 7) is what you pass to every explorer dispatch. Keep real credentials out of it — reference where they live, never inline them.

### Step 4: Enforce the safety-boundary gate (before any dispatch)

If Step 3's authorization answer is anything other than an explicit *authorized-and-non-production* affirmative, do **NOT** dispatch the explorer. State why and go to the degrade path (Step 6, plan-only). If the target is production-adjacent, unauthorized, or ambiguous, refuse execution and degrade — never "just check." This gate is the command surfacing the explorer's absolute safety boundary early; the explorer enforces the same boundary itself, so this is defense in depth, not a substitute for it. Fail **closed**: when in doubt, degrade rather than execute.

### Step 5: Obtain the charters

**If `CHARTERS_FILE` is set:** `Read` the file and load charters — skip generation entirely. Accept two shapes:

- **Canonical** — a `charter-generator` JSON fence with root keys `target`, `charters`, and `coverage_notes` (exactly what `/charter` emits). This is the fully-featured input; carry every field through.
- **Best-effort** — a markdown charter list (what `/charter --output` writes). This is lossy (it may lack `rank`, `time_box`, `risk`); normalize what you can.

Validate: every charter must have at least a `charter` sentence. Carry `rank`, `target`, `resources`, `information`, `risk`, and `time_box` when present; synthesize `rank` from file order when absent. If the file yields zero parseable charters, report that and stop — do NOT fabricate charters.

**Otherwise (no `CHARTERS_FILE`):** dispatch the `charter-generator` subagent (`stride-exploratory-testing:charter-generator`) via the `Agent` tool with `target=<TARGET>` (and `risk context=` only if the operator volunteered known worries in Step 3). Parse its single ```json fence exactly as `/charter` does — root keys `target`, `charters` (ranked, never empty), `coverage_notes`. If no parseable fence is returned, report that and stop rather than fabricating charters.

Render the ranked charter list to the conversation so the operator sees the plan before execution begins.

### Step 6: Degrade path — plan-only

If no running app is reachable (Step 3 produced no URL/command/host) **or** the safety gate (Step 4) refused execution: STOP before any explorer dispatch. Deliver the generated/loaded charters (rendered in Step 5) plus an explicit statement that execution was skipped and why, point the user at re-running once an authorized non-production target is available, and finish. Plan-only is a **valid terminal state**, not a failure — the charters are still a useful deliverable.

### Step 7: Distribute the time box and dispatch the explorer per charter

**Time-box allocation.** Treat `--timebox` as the **total** budget for the whole run. Allocate top-ranked-first, giving each executed charter a per-session box within the `session` skill's 60–120m band (default ~90m). If the total budget cannot fund every charter at a sane per-session floor, execute the **top-N by rank** that fit and defer the rest to the debrief's follow-up list — never slice a session into a sub-viable fragment. When `--timebox` is absent, default each explorer to ~90m and cap N at a sensible number, deferring the tail. **State the chosen allocation to the operator** so a surprise (only 2 of 6 charters ran) is visible, not silent.

**Dispatch — sequentially, by rank.** For each selected charter, make one `Agent` call to the `explorer` subagent (`stride-exploratory-testing:explorer`) with named args:

- `charter=` the one charter, verbatim.
- `environment context=` the `ENVIRONMENT_CONTEXT` from Step 3, with this charter's allocated time box.

Dispatch **one charter per explorer call** — never batch charters into a single dispatch. Run the charters **sequentially** by rank (not in parallel): N agents driving the same running app concurrently can collide on shared state and muddy which session caused an observed effect. (Parallel dispatch is a future option only when the sessions are genuinely isolated.) Do NOT hand-author what the explorer produces — let it run the session and return findings.

**Collect and parse.** Each explorer returns a single ```json fence with keys `charter`, `status` (`completed`｜`stopped_early`｜`blocked`), `session_sheet`, `notes`, `bugs`, `questions_risks`, `off_charter`, and `debrief` (`{explored, found, unknown}`, optionally `proof`). Parse each result. If a dispatch returns no parseable fence, record that session as **unusable** and continue with the others — do NOT fabricate its findings. A `status: "blocked"` result (e.g. app unreachable for that charter) is real data — carry it into the debrief as an obstacle, never drop it.

### Step 8: Aggregate the sessions into ONE debrief

This is the command's signature work — apply **both** `session`-skill debrief templates across all the sessions:

- **Explored / Found / Unknown (roll-up):** union each session's `debrief.explored` into one coverage narrative (which charters ran, which areas/heuristics, and which charters were deferred or blocked — the honest edge of the map); merge every `found` most-important-first; union every `unknown` plus the residual risk of each deferred/blocked charter.
- **Severity-ranked bug list:** concatenate every session's `bugs`, dedupe obvious cross-session repeats, and rank the combined list by `severity`. This is the actionable core of the report.
- **Merged off-charter parking lot → candidate follow-up charters:** union every session's `off_charter` items plus the charters deferred in Step 7 into one backlog, framed as candidate next charters to feed back into `/charter` or `/nightmare-headline`.
- **Aggregate PROOF review:** synthesize one Past / Results / Obstacles / Outlook / Feelings across the whole run — Past = what the run did; Results = coverage reached plus combined bug/question counts; Obstacles = blocked or unusable sessions and missing tools; Outlook = the follow-up parking lot; Feelings = the cross-session gut read (unease clustering on one charter is a signal).

Represent partial failures **honestly**: blocked or unusable sessions belong under Obstacles and Unknown — never produce a rosy report from only the successful subset. Optionally fold each session's `session_sheet`/TBS into a run-level coverage summary.

### Step 9: Render the debrief and finish

Present the aggregated **Explored / Found / Unknown**, the severity-ranked bug list, the follow-up parking lot, and the **PROOF** review to the conversation. Keep everything generic — no real credentials, customer data, or internal hostnames (redact; the explorer already enforces this — do not reintroduce specifics when summarizing). A result you did not observe belongs under Unknown, never under Found.

If you persist the debrief to a file, gate it behind an explicit path — `mkdir -p "$(dirname "<path>")"` then `Write` — and write only where named. (`--output` is not part of this command's argument surface today, so persistence is optional.)

Finish by pointing at the natural next steps — charter the follow-up parking-lot items with `/stride-exploratory-testing:charter` or `/stride-exploratory-testing:nightmare-headline`, and re-run any deferred charters. Do NOT auto-run another session and do NOT chain into another command.

## What this command does NOT do

- Decide *what* to explore from scratch or restate charter doctrine — that is the `chartering` skill and the `charter-generator` agent.
- Drive the running app itself, design probes, or judge findings — that is the `explorer` agent (composing `heuristics` and `oracles`); this command dispatches and aggregates only.
- Override the explorer's absolute safety boundary — it exercises the app non-destructively, on authorized non-production targets only. This command gates that boundary up front but never relaxes it.
- Execute against an unauthorized or production target — it refuses and degrades to plan-only instead.
- Fabricate findings — an unparseable or blocked session is reported as such; nothing is invented for it.
- Auto-run or chain into another command after the debrief, or modify any file other than an optional written debrief.
