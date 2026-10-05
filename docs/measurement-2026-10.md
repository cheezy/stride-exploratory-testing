# Step 5.5 explorer measurement after the G449–G451 goals (W2273)

Measured 2026-10-05 UTC (2026-10-04 local). This is the "after" that
[`porting-g449-g451.md`](porting-g449-g451.md) § The baseline reserves for
W2273; the table there is the "before".

**Read the comparator before any number.** The two sides ran different charters,
on different plugin versions, mostly on different models. Every figure below is
per explorer dispatch, or pooled across dispatches where the row says so. Each
figure names its comparator. No single saving percentage is quoted. With three
dispatches on the after side, every after figure is a small-sample figure.

## The runs

| | Measured ("after") | Comparator ("baseline") |
|---|---|---|
| Dispatches | 3: `ae4f10fc`, `a0c50e89`, `a494e87d` (full ids in the script output) | 19, the dispatches of the 2026-10-02 baseline, listed in [`scripts/baseline-2026-10-02.json`](scripts/baseline-2026-10-02.json) |
| Sessions | 1: `ba8fa028-45d7-4a67-8394-a133716de1f6` | 7: `c1b43d6b`, `9f7ae4df`, `b731341b`, `5bbdaab1`, `a79b81fc`, `06d685b1`, `0286faaf` |
| Dates | 2026-10-05, all three started 01:10:52Z | 2026-09-03 to 2026-10-02 |
| Plugin | `stride-exploratory-testing` **0.4.0** + `stride` **1.84.0** (released and installed) | `stride-exploratory-testing` 0.2.1 (inferred from release dates; one transcript shows the 0.2.1 path) |
| Model | `claude-opus-5-5`, all three | `claude-opus-5` for 17; `claude-opus-5-5` for `adac658e` and `a895e300` |
| How dispatched | from one message, in parallel, with the fixed Step 5.5 template and `EXPLORATORY_REPORT_PATH` | one at a time, with hand-written prompts; findings returned inline |
| Charters | read-only HTTP checks with `curl` against the running kanban dev app (`curl` in 13 of 24, 12 of 23 and 8 of 19 `Bash` calls) | 17 on markdown or scripts (0 `curl` calls); 2 token-leak hunts that ran `ship.sh` / `ship.py` and inspected the process and its output (`adac658e`, `a895e300`: `curl` in 3 of 33 and 3 of 17 `Bash` calls) |
| Transcripts | all 3 present | 16 present; the 3 of `c1b43d6b` are gone, so their rows come from the vendored aggregates file |

**Session position.** The after dispatches sat late in one long session: the
parent's Agent calls are lines 1990–1992 of 2077 at measurement time, sent from
a main-loop context of 350,807 tokens. The baseline dispatches were spread
across 7 sessions at many positions. For the 16 baseline dispatches with a
transcript, the parent's context at dispatch was 232,030–940,376 tokens. **Each
explorer starts with a fresh context.** Main-session position therefore does not
enter any explorer figure below. It is named here because the method requires
it.

**Excluded explorer transcripts**, named so no figure includes them silently:

- `a2e2db22` and `a8b7fab4` (session `eaaaa77d`, 2026-10-02 evening) ran on
  plugin v0.3.0 after the baseline was taken.
- `a48d17d0` (session `ba8fa028`, 2026-10-04) was nested at spawn depth 2 and was
  not a Step 5.5 dispatch.
- `a00662fc` (session `ba8fa028`, 2026-10-05) is W2273's own Step 5.5 check of
  this report, not a measured dispatch.

The script reports any other explorer transcript as unclassified. At the time of
writing there are none.

A third column, **baseline script-run (2)**, appears where it matters. It holds
the two baseline dispatches that exercised something other than markdown:
`adac658e` and `a895e300`, token-leak hunts that ran `ship.sh` / `ship.py` and
inspected the process, its files and its output. They are also the only baseline
rows on the after side's model. **They are not like-for-like.** Their task was
script and process inspection, while the after charters were read-only HTTP
checks with `curl`. So every gap against this column still mixes in a task
difference as well as the plugin change. The script labels them
`script_execution`; with n=2 the column is weak.

## Wall clock per dispatch

wall = last record timestamp − first record timestamp in the explorer transcript.

| Measure | Baseline (19) | Baseline script-run (2) | After (3) |
|---|---:|---:|---:|
| Median wall | 547 s | 437 s | **263 s** |
| Range | 372–822 s | 372–502 s | 248–281 s |
| Median wall per probe | 51.9 s | 34.8 s | 27.6 s |
| Median wall per tool call, all calls | 24.7 s | 16.8 s | 10.8 s |
| Median wall per probe tool call (comparable; see below) | 24.7 s | 17.5 s | 13.4 s |

Wall per dispatch is lower than both columns. The script-run column still mixes in
a task difference. Because the three ran in
parallel, all three charters finished within 281 s of the dispatch. That figure
is a session effect of W2267, so it is not set against the baseline's per-dispatch
figures. Part of the per-tool-call drop is the charter kind. A `curl` to a local
app returns faster than the reading and grepping the markdown charters needed.
Part is the model: 17 of 19 baseline rows ran on the older model.

**Two tool-call denominators.** Each after dispatch made 4–5 calls that only the
new contract requires: 5, 4 and 5. They are the report `Write`, the
`SubagentHandback`, the `mktemp` for the temp dir, and the cleanup `rm`, `rmdir`
or `kill`. The baseline contract required none of these. Only the two
script-run rows made a handback, one call each. The script prints "probe tool
calls", which are all calls minus those contract-only calls, with a median of 20
before and 21 after. It prints per-tool-call figures on both denominators. **The
probe-call denominator is the comparable one.** The all-calls figures flatter
the after side. In a baseline run, a `Bash` call that named `rm` or `mktemp` was
fixture setup inside the charter, so it stays a probe call there.

## Time spent writing the report

**Comparable definition** (the same for both contracts): end − the last
tool_result before the request that emits the report. That request carries the
final text or the handback on the baseline side and the report `Write` on the
after side. The figure is pooled: the sum of those intervals over the sum of wall.

| Measure | Baseline | Baseline script-run (2) | After (3) |
|---|---:|---:|---:|
| Comparable definition, pooled | 40.2% (16 present) | 20.0% | **21.5%** |
| Old definition (end − last tool_result of any tool), pooled | **38.2%** (16 present); 39% on 19 in the 2026-10-02 review | 0.0% | 0.0% |

The goal's "39%" used the old definition over 19 dispatches. Three of those
transcripts are gone, so it cannot be recomputed; the same definition gives
38.2% over the 16 that remain. Do not use the old definition after the change.
A handback or a report `Write` is itself a tool call, so the old definition
collapses to 0% whenever one is present. That includes the two baseline
script-run rows. On the comparable definition the share fell from 40.2% to 21.5%.
A similar low share appears within the baseline itself: 20.0% on the two
script-run rows. Those rows
returned shorter reports (17–25 KB) and ran on the after side's model. **This
data does not separate the share's fall from the report becoming smaller and the
model changing.**

## Tokens per dispatch

Usage is deduplicated by `message.id`, and the last record's usage wins.
Context per request = `input + cache_creation + cache_read`. input-side =
the sum over a dispatch's requests.

| Measure | Baseline (19) | Baseline script-run (2) | After (3) |
|---|---:|---:|---:|
| Requests, median | 18 | 27.5 | 25 |
| Input-side tokens, median | **1,095,995** | 1,895,710 | **1,492,948** |
| Cache-read share of input-side, pooled | 92.7% | 95.2% | 94.4% |
| Peak context: median of per-dispatch peaks | 89,492 | 91,078 | 79,623 |
| Peak context: max of per-dispatch peaks | 138,173 | 100,739 | 88,162 |
| First-request context (the fixed base), median | 32,280 (16 present) | 32,306 | **41,133** |
| Input-side per probe, median | 97,259 | 149,565 | 164,655 |
| Input-side per tool call (all calls), median | 52,245 | 67,162 | 59,718 |
| Input-side per probe tool call (comparable), median | 52,245 | 69,910 | 77,344 |

**Input-side tokens per dispatch did not improve against the 19-dispatch
baseline. They rose from a median of 1.10M to 1.49M.** Two causes are visible in
the data:

- **More requests.** The median went from 18 to 25, and every request re-sends the
  context.
- **A larger fixed base.** Every request now starts from about 41.1k tokens
  instead of 32.3k. `agents/explorer.md` grew from 18,041 to 49,031 bytes between
  0.2.1 and 0.4.0 (`wc -c` on the installed copies), because G449 inlined the card
  and added the safety boundary, verify mode and the reading rule. W2272's trims
  did not offset that growth. The dispatch prompt shrank by about 5.7 KB, so the
  net gain is roughly 8.8k tokens per request.

Against the two script-run rows, input-side was lower: 1.49M against 1.90M. That
gap mixes a task difference (script and process inspection against HTTP checks)
with the plugin change. Peak context is lower than both columns, with the max
down from 138,173 to 88,162. The script-run column carries the same task
difference. Per probe and per probe tool call, the cost rose against both
columns.

**Output tokens are not comparable.** The baseline review dropped dispatches with
`output_tokens` ≤ 1,000 as stream-start-only records; that rule removed 2 of 19,
leaving a median of 25,222 over 17. All 3 after transcripts record ≤ 1,000
(166–224 in total), so the rule removes every after dispatch.

## What reached the main loop

| Measure | Baseline (19) | Baseline script-run (2) | After (3) |
|---|---:|---:|---:|
| Returned to the main loop, median | **37,314 B** | 20,964 B | **525 B** |
| Returned, total | 733,247 B | 41,927 B | 1,565 B |
| Full report written to `EXPLORATORY_REPORT_PATH`, median | n/a (the report was the returned text) | n/a | 14,367 B |
| Dispatch prompt, median | 6,824 B | 3,384 B | 1,106 B |
| Dispatch prompt, total | 123,742 B | 6,768 B | 3,401 B |

Returned bytes are the explorer's handback message, or its last text when there
was no handback. The full findings did not disappear. They moved to a file of
about 14 KB, which the main loop had not read at measurement time. If a later
step reads it, that step pays those bytes. The file is also smaller than a
baseline report. Most of that comes from fewer bugs per session: 2 each after,
against a baseline median of 6.

## Severity labels

| Measure | Baseline (19) | Baseline script-run (2) | After (3) |
|---|---:|---:|---:|
| Bugs with an exact token (Critical, High, Moderate, Minor) | **28 of 101** | 8 of 8 | **6 of 6** |
| Distinct severity strings | 24 | 4 | 3 |

**The after side gives no evidence that the label fix worked.** Six bugs is a
very small sample. The two baseline script-run rows, on 0.2.1 but on the after side's
model, already used exact tokens 8 of 8 times. The improvement against the
19-dispatch baseline is real as a count. It cannot be credited to the card from
this data.

## Skills, repeat reads, endings

| Measure | Baseline (19) | Baseline script-run (2) | After (3) |
|---|---:|---:|---:|
| Dispatches that loaded a plugin skill or agent file | 1 (`bug-advocacy`) | 1 | 0 |
| Read of a path already Read (any range) | 18, in 10 dispatches | 0 | 0 |
| Read of the same path and the same offset/limit | 0 (16 present; not recorded for the 3 missing) | 0 | 0 |
| Whole-file repeat: a Read with neither offset nor limit of a path already Read | 0 (16 present; not recorded for the 3 missing) | 0 | 0 |
| Probes attempted, median (session sheet) | 10 | 12.5 | 10 |
| Tool calls, median (all tool_use records) | 20 | 27.5 | 25 |
| Probe tool calls, median (minus contract-only calls; comparable) | 20 | 26.5 | 21 |
| How sessions ended | 10 probe-budget, 8 charter quiet, 1 risk acceptable | 1 probe-budget, 1 risk acceptable | 3 charter quiet |

The baseline's "repeat whole-file reads" label was wrong. On the 16 baseline
transcripts still present, all 16 repeats re-read a **different** range, and
none was a same-range or whole-file repeat. **The after zero proves nothing about
W2270's reading rule.** The three after explorers made no `Read` calls at all;
every probe was a `Bash` command. A re-read through `Bash` `cat` or `sed` is not
counted by either metric. Skills: 0 after is what W2261's inlined card intends.
With n=3 it is consistent with that change, not proof of it.

## Is any saving explained by a smaller task?

This is the task's manual test. The answer is **partly, and the data cannot say
how much.**

- **Not fewer probes.** The after explorers attempted 9–10 probes each, with a
  budget of 12, against a baseline median of 10 (budget 10–15). They made 21 probe
  tool calls against 20, or 25 calls against 20 counting the 4–5 contract-only
  calls. By probes and probe tool calls, the after task was about the same size,
  not smaller.
- **A different kind of charter, on every comparator.** 17 of 19 baseline
  charters read markdown and scripts. The other 2 were token-leak hunts that ran
  `ship.sh` / `ship.py` and inspected the process and its output, with `curl` in
  only 3 of 33 and 3 of 17 `Bash` calls. All 3 after charters were read-only HTTP
  checks against a local app, with `curl` in 13 of 24, 12 of 23 and 8 of 19
  `Bash` calls. A `curl` round trip is quick and its output is short, which
  favours wall per tool call. That part of the speed-up comes from the charter,
  not the plugin. No baseline row shares the after charter kind.
- **Fewer bugs found.** Each after session reported 2 bugs; the baseline median
  was 6. Fewer bugs mean a shorter report, which shortens the report-writing
  interval and the report file. This is a smaller *result*, not a smaller task.
  It still flatters report time and file size.
- **A different model.** 17 of 19 baseline rows ran on `claude-opus-5`. Only the
  two script-run rows share the after side's model. Against them, wall went from
  437 s to 263 s and wall per probe tool call from 17.5 s to 13.4 s. Input-side
  per probe tool call rose from 69,910 to 77,344, and per probe from 149,565 to
  164,655. These gaps hold the model constant but **still mix in the task
  difference** described above, so they do not isolate the plugin.
- **Clearly the changes:** returned bytes (37 KB to 0.5 KB, W2266), dispatch
  prompt bytes (6.8 KB to 1.1 KB, W2270's template) and parallel dispatch
  (W2267). Each follows directly from a contract change, and the charter cannot
  produce it.

n=3, from one session, on one kind of charter. Read every after figure as an
observation, not an estimate.

## Caveats

1. **Three baseline transcripts are gone.** Session `c1b43d6b` (2026-09-03,
   `a25cb0e6`, `a1ba5553`, `a5e50716`) is no longer in `~/.claude/projects`. Its
   rows come from [`scripts/baseline-2026-10-02.json`](scripts/baseline-2026-10-02.json),
   which holds the aggregates the 2026-10-02 scripts recorded (numbers, ids and
   enum values only; severity strings are stored as hashes). Figures that need
   the raw transcript are given over the 16 present: report-writing share,
   same-range re-reads, first-request context and skill loads.
2. **The old 39% is not reproducible on 19.** Its 16-dispatch value (38.2%)
   reproduces exactly. The 2026-10-02 run did not save its per-dispatch
   time-split output.
3. **Plugin version on the baseline side is inferred.** Release tags fall on
   2026-08-21 (v0.2.1) and 2026-10-02 (v0.3.0), and one baseline transcript
   shows the 0.2.1 path.
4. **Session-level overlap.** The three after dispatches overlapped completely,
   so per-dispatch wall is never summed into a session figure.
5. **The report file is not counted as main-loop ingest.** It had not been read
   by the main loop when measured. A later Step 5.6 or a human may read it.
6. **Old scripts glob every explorer.** Re-running the 2026-10-02 `et-usage`
   scripts today would count 22 explorer transcripts, not 19. The new script
   names its dispatches by id and lists the rest as excluded.
7. **Claude Code only.** No variant has been measured. Do not claim a variant
   saving from these numbers.

## Reproduction

```bash
cd stride-exploratory-testing    # from the kanban checkout root

# counting rules: dedupe-last, context arithmetic, report-share boundaries,
# repeat-read classification, severity counting
python3 docs/scripts/measure-explorer-sessions.py --self-test

# reproduce the 2026-10-02 baseline (547 s, 18, 1,095,995, 89,492, 123,742 B,
# 37,314 / 733,247 B, 28 of 101, 24 distinct, 38.2% on 16) and every vendored
# row of the 16 present transcripts; exits 1 on a mismatch
python3 docs/scripts/measure-explorer-sessions.py --baseline-check

# every figure in this document (per-dispatch table, three summary columns
# including the 25,222 output median over 17 and the whole-file repeat count,
# excluded list, baseline check); --json for machine-readable output. Both
# also exit 1, after printing, if any reproducible baseline figure mismatches
python3 docs/scripts/measure-explorer-sessions.py
python3 docs/scripts/measure-explorer-sessions.py --json

# explorer agent definition size per installed version
wc -c ~/.claude/plugins/cache/stride-marketplace/stride-exploratory-testing/{0.2.1,0.4.0}/agents/explorer.md
```

Quoted from outside the script: the release-tag dates
(`git log --tags --simplify-by-decoration`), the `explorer.md` byte sizes (`wc -c`
above), and the check that the main loop had not read the three report files.
That check was a count of tool calls naming those paths after the dispatch;
none was a `Read`. Aggregates and ids only: this document reproduces no
transcript excerpt, prompt or credential.
