#!/usr/bin/env python3
"""W2273: per-dispatch measurement of stride Step 5.5 explorer sessions,
before and after the G449-G451 goals, against the 2026-10-02 baseline.

Why this exists rather than the 2026-10-02 et-usage scripts: those globbed
every `stride-exploratory-testing` agent in every project, so re-running them
today silently adds every later dispatch (22 explorer transcripts exist now
against the baseline's 19). They also lived in a volatile scratchpad. This
script names every dispatch by id and states each definition where it is
computed. Every run except --self-test re-derives the baseline and checks it
against the 2026-10-02 figures; after printing, it exits 1 if any reproducible
figure mismatches, so a measurement is never reported over a baseline that
did not reproduce.

Which dispatches:

  * baseline — the 19 dispatches of `baseline-2026-10-02.json` (plugin 0.2.1,
    2026-09-03..2026-10-02). 16 are re-derived from raw transcripts; the 3 of
    session c1b43d6b (transcripts gone) come from that vendored file, where
    they are marked `transcript_missing`.
  * after — the three W2273 dispatches of session ba8fa028 (plugin 0.4.0 +
    stride 1.84.0, 2026-10-05), resolved from the subagents directory by id
    prefix and checked to be `stride-exploratory-testing:explorer`.
  * excluded — every other explorer transcript, each named with its reason.
    Any explorer transcript in no list is reported as unclassified.

Counting rules. These follow stride/docs/token-baseline.md § Counting rules
except where stated:

  * A request is one assistant `message.id`; Claude Code writes one record per
    content block. Usage is deduplicated by message id, and this script keeps
    the LAST record's usage per id, like w2259-multitask.py and the
    2026-10-02 et-usage scripts and unlike token-baseline.md's sum_usage
    (which keeps the first). Input-side totals are identical either way; output
    totals differ (an early record's output_tokens is a streaming partial).
  * Context per request = input_tokens + cache_creation_input_tokens +
    cache_read_input_tokens. input_side = sum over requests; peak_context =
    max over requests (summaries give the median of those peaks AND the max).
  * first_context = context of the explorer's first request: the fixed base
    (system prompt, agent definition, dispatch prompt) every request re-sends.
  * wall_s = max - min record timestamp in the explorer transcript.
  * returned_bytes = what reached the main loop: the explorer's
    SubagentHandback message if it sent one, else its last non-empty text.
  * report_file_bytes (after only) = bytes of the content of the explorer's
    Write to its EXPLORATORY_REPORT_PATH. Baseline: n/a (the report was the
    returned text).
  * report-writing share (comparable for both contracts) = (end - timestamp of
    the last tool_result before the request that emits the report) / wall,
    pooled. The emitting request is the one carrying the final text or
    handback (baseline) or the report Write (after). The OLD definition
    (end - last tool_result of any kind) is printed for the baseline too; it
    is what produced the 2026-10-02 "39%".
  * severity: bugs[].severity, exact member of {Critical, High, Moderate,
    Minor}. Baseline: first ```json fence of the returned text; after: the
    Write content. Distinct strings are unioned through sha256[:12] hashes so
    the vendored rows carry no text.
  * repeat reads: a Read of a path already Read (any range); a Read of the
    same path with the same offset/limit; and a whole-file repeat, a Read with
    neither offset nor limit of a path already Read. Bash cat/sed re-reads are
    not counted.
  * skills loaded: Read/Bash paths matching
    stride-exploratory-testing/<ver>/(skills|agents)/...md, plus Skill tool use.
  * probe_tool_calls = tool calls minus the calls only the contract requires
    (see contract_only: the handback on both sides; after only, the report
    Write and the mktemp/cleanup Bash calls). Per-tool-call figures are
    printed on both denominators; the probe-call one is the comparable one.
  * output tokens: the baseline dropped dispatches with out_tok <= 1000 as
    stream-start-only usage (the summary prints the median over the rest);
    where that rule bites, output is not comparable.

Aggregates only: no prompt, transcript text or record content is printed.

Usage:
  python3 measure-explorer-sessions.py --self-test
  python3 measure-explorer-sessions.py --baseline-check
  python3 measure-explorer-sessions.py [--json]
"""
import argparse
import collections
import glob
import hashlib
import json
import os
import re
import statistics
import sys
from datetime import datetime

PROJECT = os.path.expanduser("~/.claude/projects/-Users-cheezy-dev-elixir-kanban")
HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE_FILE = os.path.join(HERE, "baseline-2026-10-02.json")
EXPLORER = "stride-exploratory-testing:explorer"

AFTER_SESSION = "ba8fa028-45d7-4a67-8394-a133716de1f6"
AFTER_PREFIXES = ["ae4f10fc", "a0c50e89", "a494e87d"]

EXCLUDED = {
    "a2e2db22": "2026-10-02 evening (session eaaaa77d), plugin v0.3.0, after the baseline was taken",
    "a8b7fab4": "2026-10-02 evening (session eaaaa77d), plugin v0.3.0, after the baseline was taken",
    "a48d17d0": "2026-10-04 (session ba8fa028), nested at spawn depth 2, not a Step 5.5 dispatch",
    "a00662fc": "2026-10-05 (session ba8fa028), W2273's own Step 5.5 check of this report, not a measured dispatch",
}

CANON = {"Critical", "High", "Moderate", "Minor"}
SKILL_PATH_RE = re.compile(r"stride-exploratory-testing/[0-9.]+/(?:skills|agents)/(\S+?)\.md")
REPORT_PATH_RE = re.compile(r"EXPLORATORY_REPORT_PATH\s*[:=]\s*`?([^\s`]+)")
JSON_FENCE_RE = re.compile(r"```json\s*\n(.*?)\n```", re.S)
STREAM_START_LIMIT = 1000
# Bash calls the 0.4.0 contract adds around the probes: a temp dir, then cleanup.
CONTRACT_BASH_RE = re.compile(r"\b(?:mktemp|rm|rmdir|kill|pkill)\b")
SCRIPT_RUN = "script_execution"

# The goal's 2026-10-02 figures: (key, expected, relative tolerance)
GOAL = [
    ("median wall_s", 547, 0.0),
    ("median requests", 18, 0.0),
    ("median input_side", 1095995, 0.01),
    ("median peak_context", 89492, 0.01),
    ("sum prompt_bytes", 123742, 0.0),
    ("median returned_bytes", 37314, 0.0),
    ("sum returned_bytes", 733247, 0.0),
    ("bugs", 101, 0.0),
    ("severity exact", 28, 0.0),
    ("severity distinct", 24, 0.0),
]
OLD_SHARE_16 = 38.2  # old definition, 16 present transcripts (percent, one decimal)


def parse_ts(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def context_of(usage):
    return (usage.get("input_tokens", 0)
            + usage.get("cache_creation_input_tokens", 0)
            + usage.get("cache_read_input_tokens", 0))


def sev_hash(severity):
    return hashlib.sha256(("null" if severity is None else severity).encode()).hexdigest()[:12]


def blocks(record):
    message = record.get("message") or {}
    content = message.get("content") if isinstance(message, dict) else None
    return [b for b in content if isinstance(b, dict)] if isinstance(content, list) else []


def dedupe_usage(records):
    """One entry per assistant message id: {id: (first_line, usage)}.

    The line is the first record's; the usage is the LAST record's. A usage
    record with no message id cannot be deduplicated and is skipped.
    """
    out = {}
    for line, rec in enumerate(records):
        if rec.get("type") != "assistant":
            continue
        message = rec.get("message") or {}
        mid = message.get("id")
        if not mid or "usage" not in message:
            continue
        first = out[mid][0] if mid in out else line
        out[mid] = (first, message["usage"])
    return out


def first_line_of(records, mid):
    for line, rec in enumerate(records):
        if rec.get("type") == "assistant" and (rec.get("message") or {}).get("id") == mid:
            return line
    return None


def tool_uses(records):
    """[(line, block)] for each distinct tool_use id, in order."""
    seen, out = set(), []
    for line, rec in enumerate(records):
        for b in blocks(rec):
            if b.get("type") == "tool_use" and b.get("id") not in seen:
                seen.add(b.get("id"))
                out.append((line, b))
    return out


def timestamps(records):
    return [(line, parse_ts(r["timestamp"])) for line, r in enumerate(records) if r.get("timestamp")]


def report_share(records, emit_line):
    """(seconds, wall) — end minus the last tool_result before emit_line."""
    ts = timestamps(records)
    start, end = min(t for _, t in ts), max(t for _, t in ts)
    last = start
    for line, rec in enumerate(records):
        if line >= emit_line:
            break
        if rec.get("timestamp") and any(b.get("type") == "tool_result" for b in blocks(rec)):
            last = parse_ts(rec["timestamp"])
    return (end - last).total_seconds(), (end - start).total_seconds()


def old_report_share(records):
    """(seconds, wall) by 2026-10-02 11_time_split.py: end - last tool_result of any tool."""
    start = end = last = None
    seen = set()
    for rec in records:
        if not rec.get("timestamp"):
            continue
        t = parse_ts(rec["timestamp"])
        start = start or t
        end = t
        for b in blocks(rec):
            if b.get("type") == "tool_use":
                seen.add(b.get("id"))
            if b.get("type") == "tool_result" and b.get("tool_use_id") in seen:
                last = t
    return (end - (last or start)).total_seconds(), (end - start).total_seconds()


def whole_file_repeats(reads):
    """Reads with neither offset nor limit of a path already Read (any range)."""
    seen, count = set(), 0
    for path, offset, limit in reads:
        count += path in seen and offset is None and limit is None
        seen.add(path)
    return count


def repeat_reads(reads):
    """reads: [(path, offset, limit)] -> (same_path_again, same_range_again, whole_file_again)."""
    by_path = collections.Counter(p for p, _, _ in reads)
    by_range = collections.Counter(reads)
    return (sum(v - 1 for v in by_path.values() if v > 1),
            sum(v - 1 for v in by_range.values() if v > 1),
            whole_file_repeats(reads))


def severity_counts(bugs):
    sev = [b.get("severity") for b in bugs or [] if isinstance(b, dict)]
    return len(sev), sum(s in CANON for s in sev), [sev_hash(s) for s in sev]


def first_json_fence(text):
    found = JSON_FENCE_RE.findall(text or "")
    if not found:
        return None
    try:
        return json.loads(found[0])
    except ValueError:
        return None


def load_jsonl(path):
    out = []
    with open(path) as fh:
        for raw in fh:
            try:
                out.append(json.loads(raw))
            except ValueError:
                continue
    return out


def explorer_metas(project):
    out = {}
    for meta in glob.glob(os.path.join(project, "*", "subagents", "agent-*.meta.json")):
        with open(meta) as fh:
            md = json.load(fh)
        if md.get("agentType") == EXPLORER:
            agent = os.path.basename(meta)[len("agent-"):-len(".meta.json")]
            out[agent] = dict(meta=md, session=meta.split(os.sep)[-3], path=meta[:-len(".meta.json")] + ".jsonl")
    return out


def parent_dispatch(project, session, tool_use_id):
    """(prompt, line, parent context at dispatch, total parent lines) of the parent Agent call."""
    path = os.path.join(project, session + ".jsonl")
    if not os.path.exists(path):
        return None, None, None, None
    records = load_jsonl(path)
    for line, rec in enumerate(records):
        for b in blocks(rec):
            if b.get("type") == "tool_use" and b.get("id") == tool_use_id:
                usage = (rec.get("message") or {}).get("usage") or {}
                return (b.get("input") or {}).get("prompt", ""), line, context_of(usage), len(records)
    return None, None, None, len(records)


ROW_ORDER = ("model", "session", "agent_id", "contract", "transcript_missing", "start_utc", "wall_s",
             "requests", "input_side", "peak_context", "first_context", "cache_read", "output_tokens",
             "tool_calls", "contract_tool_calls", "probe_tool_calls", "bash_calls", "curl_calls", "prompt_bytes", "parent_line", "parent_lines",
             "parent_context_at_dispatch", "returned_bytes", "report_file_bytes", "report_share_s",
             "report_share_wall_s", "old_report_share_s", "bugs", "severity_exact", "severity_hashes",
             "probes_attempted", "probe_budget", "sheet_tool_calls_used", "stop_reason", "reads",
             "reread_same_path", "reread_same_range", "reread_whole_file", "skills_loaded", "skill_tool_uses")


def usage_metrics(records):
    """Request, context and model figures from the deduplicated usage."""
    usage = dedupe_usage(records)
    contexts = [context_of(u) for _, u in usage.values()]
    models = collections.Counter((r.get("message") or {}).get("model") for r in records if r.get("type") == "assistant")
    return dict(model=models.most_common(1)[0][0] if models else None,
                requests=len(usage), input_side=sum(contexts), peak_context=max(contexts),
                first_context=context_of(min(usage.values(), key=lambda v: v[0])[1]),
                cache_read=sum(u.get("cache_read_input_tokens", 0) for _, u in usage.values()),
                output_tokens=sum(u.get("output_tokens", 0) for _, u in usage.values()))


def wall_metrics(records):
    ts = [t for _, t in timestamps(records)]
    return dict(start_utc=min(ts).isoformat()[:16], wall_s=round((max(ts) - min(ts)).total_seconds()))


def _on_read(acc, line, inp):
    acc["reads"].append((inp.get("file_path"), inp.get("offset"), inp.get("limit")))
    acc["skills"] += SKILL_PATH_RE.findall(inp.get("file_path") or "")


def _on_bash(acc, line, inp):
    command = inp.get("command") or ""
    acc["bash"] += 1
    acc["curls"] += "curl " in command
    acc["skills"] += SKILL_PATH_RE.findall(command)


def _on_skill(acc, line, inp):
    acc["skill_tool"] += 1
    acc["skills"].append("Skill:" + str(inp.get("skill") or inp.get("command")))


def _on_handback(acc, line, inp):
    acc["handback"], acc["handback_line"] = inp.get("message", ""), line


TOOL_HANDLERS = {"Read": _on_read, "Bash": _on_bash, "Skill": _on_skill, "SubagentHandback": _on_handback}


def tool_profile(uses):
    """Reads, skill loads, Bash/curl counts and the handback, from the tool_use blocks."""
    acc = dict(reads=[], skills=[], curls=0, bash=0, skill_tool=0, handback=None, handback_line=None)
    for line, b in uses:
        handler = TOOL_HANDLERS.get(b.get("name"))
        if handler:
            handler(acc, line, b.get("input") or {})
    return acc


def last_text(records):
    """(text, line) of the last non-empty assistant text block."""
    text = line_of = None
    for line, rec in enumerate(records):
        if rec.get("type") != "assistant":
            continue
        for b in blocks(rec):
            if b.get("type") == "text" and b.get("text", "").strip():
                text, line_of = b["text"], line
    return text, line_of


def report_path(prompt):
    found = REPORT_PATH_RE.search(prompt or "")
    return found.group(1) if found else None


def write_path(block):
    return (block.get("input") or {}).get("file_path")


def report_write(uses, prompt):
    """(record line, content) of the Write to EXPLORATORY_REPORT_PATH (else the last Write)."""
    wanted = report_path(prompt)
    writes = [(line, b) for line, b in uses if b.get("name") == "Write"]
    match = [w for w in writes if write_path(w[1]) == wanted] or writes[-1:]
    if not match:
        return None, None
    return match[-1][0], (match[-1][1].get("input") or {}).get("content", "")


def parse_json(text):
    try:
        return json.loads(text)
    except ValueError:
        return None


def report_of(contract, uses, prompt, returned, emit_rec_line):
    """(emitting record line, report_file_bytes, parsed findings) for either contract."""
    if contract != "after":
        return emit_rec_line, None, first_json_fence(returned)
    line, content = report_write(uses, prompt)
    if line is None:
        return emit_rec_line, None, None
    return line, len(content.encode()), parse_json(content)


def share_metrics(records, emit_rec_line):
    """Comparable and old report-writing intervals; the emitting request starts at its first record."""
    emit_mid = (records[emit_rec_line].get("message") or {}).get("id") if emit_rec_line is not None else None
    emit_line = first_line_of(records, emit_mid) if emit_mid else emit_rec_line
    share_s, wall = report_share(records, emit_line) if emit_line is not None else (None, None)
    return dict(report_share_s=share_s, report_share_wall_s=wall, old_report_share_s=old_report_share(records)[0])


def findings_metrics(report):
    bugs, exact, hashes = severity_counts((report or {}).get("bugs"))
    sheet = (report or {}).get("session_sheet") or {}
    return dict(bugs=bugs, severity_exact=exact, severity_hashes=hashes,
                probes_attempted=sheet.get("probes_attempted"), probe_budget=sheet.get("probe_budget"),
                sheet_tool_calls_used=sheet.get("tool_calls_used"), stop_reason=sheet.get("stop_reason"))


def contract_only(block, contract):
    """True for a tool call the explorer contract requires rather than a probe.

    Both sides: SubagentHandback (the return path). After (0.4.0) only: the
    report Write and Bash calls naming mktemp/rm/rmdir/kill/pkill (the temp
    dir and the cleanup rule). On the baseline those Bash words were fixture
    setup inside the charter, so they stay probe calls there.
    """
    name = block.get("name")
    if name == "SubagentHandback":
        return True
    if contract != "after":
        return False
    command = (block.get("input") or {}).get("command") or ""
    return name == "Write" or (name == "Bash" and bool(CONTRACT_BASH_RE.search(command)))


def profile_metrics(uses, acc, contract):
    same_path, same_range, whole_file = repeat_reads(acc["reads"])
    contract_calls = sum(contract_only(b, contract) for _, b in uses)
    return dict(tool_calls=len(uses), contract_tool_calls=contract_calls,
                probe_tool_calls=len(uses) - contract_calls, bash_calls=acc["bash"], curl_calls=acc["curls"],
                reads=len(acc["reads"]), reread_same_path=same_path, reread_same_range=same_range,
                reread_whole_file=whole_file, skills_loaded=sorted(set(acc["skills"])),
                skill_tool_uses=acc["skill_tool"])


def measure(project, session, agent, meta, contract):
    """Per-dispatch metrics for one explorer transcript. contract: 'baseline' or 'after'."""
    records = load_jsonl(os.path.join(project, session, "subagents", "agent-%s.jsonl" % agent))
    uses = tool_uses(records)
    prompt, pline, pctx, plen = parent_dispatch(project, session, meta.get("toolUseId"))
    acc = tool_profile(uses)
    final_text, final_line = last_text(records)
    has_handback = acc["handback"] is not None
    returned = acc["handback"] if has_handback else (final_text or "")
    emit_rec_line, file_bytes, report = report_of(
        contract, uses, prompt, returned, acc["handback_line"] if has_handback else final_line)
    m = dict(session=session, agent_id=agent, contract=contract, transcript_missing=False,
             prompt_bytes=len(prompt.encode()) if prompt is not None else None,
             parent_line=pline, parent_lines=plen, parent_context_at_dispatch=pctx,
             returned_bytes=len(returned.encode()), report_file_bytes=file_bytes)
    for part in (usage_metrics(records), wall_metrics(records), share_metrics(records, emit_rec_line),
                 findings_metrics(report), profile_metrics(uses, acc, contract)):
        m.update(part)
    return {k: m[k] for k in ROW_ORDER}


def load_baseline(path):
    with open(path) as fh:
        return json.load(fh)["rows"]


def resolve_after(metas):
    out = []
    for prefix in AFTER_PREFIXES:
        hits = [a for a, m in metas.items() if a.startswith(prefix) and m["session"] == AFTER_SESSION]
        if len(hits) != 1:
            raise SystemExit("after dispatch %s: expected 1 explorer transcript in %s, found %d"
                             % (prefix, AFTER_SESSION, len(hits)))
        out.append(hits[0])
    return out


def baseline_row(project, metas, row):
    """Re-derive a vendored row from its transcript, or carry the vendored aggregates if it is gone."""
    agent = row["agent_id"]
    if agent in metas and not row["transcript_missing"]:
        got = measure(project, row["session"], agent, metas[agent]["meta"], "baseline")
        got["charter_kind"] = row["charter_kind"]
        got["vendored"] = row
        return got
    return dict(row, contract="baseline", transcript_missing=True, model=None, first_context=None,
                reread_same_range=None, skills_loaded=None, report_share_s=None,
                old_report_share_s=None, report_file_bytes=None, reread_whole_file=None,
                # the 2026-10-02 tool counts for these rows hold only Bash and Read
                contract_tool_calls=0, probe_tool_calls=row["tool_calls"])


def after_rows(project, metas):
    rows = []
    for agent in resolve_after(metas):
        got = measure(project, AFTER_SESSION, agent, metas[agent]["meta"], "after")
        got["charter_kind"] = "http_curl_checks"
        rows.append(got)
    return rows


def classify_rest(metas, known):
    """(excluded, unclassified) for every explorer transcript in neither set."""
    excluded, unclassified = [], []
    for agent, m in sorted(metas.items()):
        if agent in known:
            continue
        reason = next((why for p, why in EXCLUDED.items() if agent.startswith(p)), None)
        (excluded if reason else unclassified).append(dict(agent_id=agent, session=m["session"], reason=reason))
    return excluded, unclassified


def collect(project, baseline_path):
    metas = explorer_metas(project)
    baseline = [baseline_row(project, metas, row) for row in load_baseline(baseline_path)]
    after = after_rows(project, metas)
    excluded, unclassified = classify_rest(metas, {r["agent_id"] for r in baseline + after})
    return baseline, after, excluded, unclassified


def med(rows, key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    return statistics.median(vals) if vals else None


def total(rows, key):
    return sum(r[key] for r in rows if r.get(key) is not None)


def per(rows, num, den):
    vals = [r[num] / r[den] for r in rows if r.get(num) is not None and r.get(den)]
    return statistics.median(vals) if vals else None


def pooled_share(rows, key, wall_key):
    present = [r for r in rows if r.get(key) is not None]
    walls = sum(r[wall_key] for r in present)
    return (100.0 * sum(r[key] for r in present) / walls if walls else None), len(present)


SUMMED = ("wall_s", "requests", "input_side", "peak_context", "first_context", "prompt_bytes", "returned_bytes",
          "report_file_bytes", "tool_calls", "probe_tool_calls", "probes_attempted", "output_tokens")
RATIOS = (("input_side", "probes_attempted"), ("input_side", "tool_calls"), ("input_side", "probe_tool_calls"),
          ("wall_s", "probes_attempted"), ("wall_s", "tool_calls"), ("wall_s", "probe_tool_calls"))


def _medians_and_sums(s, rows):
    for key in SUMMED:
        s["median " + key] = med(rows, key)
        s["sum " + key] = total(rows, key)
    s["max peak_context"] = max(r["peak_context"] for r in rows)
    s["cache_read share"] = 100.0 * total(rows, "cache_read") / total(rows, "input_side")


def _share_figures(s, rows):
    share, n = pooled_share(rows, "report_share_s", "report_share_wall_s")
    s["report share (comparable)"], s["report share n"] = share, n
    present = [r for r in rows if r.get("old_report_share_s") is not None]
    s["report share (old)"] = (100.0 * total(present, "old_report_share_s")
                               / total(present, "report_share_wall_s")) if present else None


def _severity_and_output(s, rows):
    s["bugs"] = total(rows, "bugs")
    s["severity exact"] = total(rows, "severity_exact")
    s["severity distinct"] = len({h for r in rows for h in r["severity_hashes"]})
    s["stream-start-only dispatches"] = sum(r["output_tokens"] <= STREAM_START_LIMIT for r in rows)
    kept = [r for r in rows if r["output_tokens"] > STREAM_START_LIMIT]
    s["median output_tokens, out > 1000 only"] = med(kept, "output_tokens")
    s["out > 1000 n"] = len(kept)


def _reads_skills_kinds(s, rows):
    s["reread same path"] = total(rows, "reread_same_path")
    s["reread same path dispatches"] = sum((r.get("reread_same_path") or 0) > 0 for r in rows)
    s["reread same range"] = total(rows, "reread_same_range")
    s["reread same range n"] = sum(r.get("reread_same_range") is not None for r in rows)
    s["reread whole file"] = total(rows, "reread_whole_file")
    s["skill-loading dispatches"] = sum(bool(r.get("skills_loaded")) for r in rows)
    s["skills n"] = sum(r.get("skills_loaded") is not None for r in rows)
    s["charter kinds"] = dict(collections.Counter(r.get("charter_kind") for r in rows))
    s["stop reasons"] = dict(collections.Counter(r.get("stop_reason") for r in rows))


def summarise(rows):
    s = dict(n=len(rows), present=sum(not r["transcript_missing"] for r in rows))
    for part in (_medians_and_sums, _share_figures, _severity_and_output, _reads_skills_kinds):
        part(s, rows)
    for num, den in RATIOS:
        s["median %s per %s" % (num, den)] = per(rows, num, den)
    return s


ROW_KEYS = ("wall_s", "requests", "input_side", "peak_context", "tool_calls", "prompt_bytes",
            "returned_bytes", "bugs", "severity_exact", "severity_hashes", "probes_attempted",
            "reread_same_path", "output_tokens")


def baseline_check(baseline):
    """[(label, expected, got, ok)] — goal figures and per-row re-derivation."""
    s = summarise(baseline)
    out = []
    for key, want, tol in GOAL:
        got = s[key]
        ok = got is not None and abs(got - want) <= tol * want
        out.append((key + " (19)", want, got, ok))
    old16 = s["report share (old)"]
    out.append(("report share, old definition (16 present)", OLD_SHARE_16, round(old16, 1),
                round(old16, 1) == OLD_SHARE_16))
    out.append(("report share 39%, old definition (19)", 39, "not reproducible: 3 transcripts gone", None))
    for row in baseline:
        if row["transcript_missing"]:
            continue
        for key in ROW_KEYS:
            if row["vendored"].get(key) != row.get(key):
                out.append(("row %s %s" % (row["agent_id"][:8], key), row["vendored"].get(key), row.get(key), False))
    return out


def mismatches(checks):
    return sum(ok is False for _, _, _, ok in checks)


def fmt(value):
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return "{:,.1f}".format(value)
    if isinstance(value, int):
        return "{:,}".format(value)
    return str(value)


ROW_HEADER = ("set", "agent", "start", "kind", "wall", "req", "input_side", "peak", "out", "tools", "curl",
              "probes", "prompt_B", "returned_B", "file_B", "share_s", "old_s", "bugs", "exact",
              "rr_path", "rr_range", "skills", "model", "parent_line", "parent_ctx")


def skills_cell(r):
    if r.get("skills_loaded") is None:
        return "n/a"
    return ",".join(r["skills_loaded"]) or "-"


def parent_cell(r):
    return "%s/%s" % (r["parent_line"], r["parent_lines"]) if r.get("parent_line") is not None else None


def row_cells(r):
    return (r["contract"], r["agent_id"][:8] + ("*" if r["transcript_missing"] else ""), r["start_utc"],
            r.get("charter_kind"), r["wall_s"], r["requests"], r["input_side"], r["peak_context"],
            r["output_tokens"], r["tool_calls"], r.get("curl_calls"), r.get("probes_attempted"),
            r["prompt_bytes"], r["returned_bytes"], r.get("report_file_bytes"),
            r.get("report_share_s"), r.get("old_report_share_s"), r["bugs"], r["severity_exact"],
            r.get("reread_same_path"), r.get("reread_same_range"), skills_cell(r), r.get("model"),
            parent_cell(r), r.get("parent_context_at_dispatch"))


def print_rows(rows):
    print("\t".join(ROW_HEADER))
    for r in rows:
        print("\t".join(fmt(c) for c in row_cells(r)))
    print("  (* = transcript missing; vendored aggregates)\n")


DICT_KEYS = ("stop reasons", "charter kinds")


def print_summary(baseline, after):
    pair = [r for r in baseline if r.get("charter_kind") == SCRIPT_RUN]
    sb, sp, sa = summarise(baseline), summarise(pair), summarise(after)
    print("%-42s %16s %16s %16s" % ("metric", "baseline (19)", "base script (2)", "after (3)"))
    for key in (k for k in sb if k not in DICT_KEYS):
        print("%-42s %16s %16s %16s" % (key, fmt(sb[key]), fmt(sp[key]), fmt(sa[key])))
    for key in DICT_KEYS:
        print("%-42s %s | %s | %s" % (key, sb[key], sp[key], sa[key]))
    print("  base script (2) = the two baseline dispatches that exercised something other than markdown:\n"
          "  token-leak hunts that ran ship.sh / ship.py and inspected the process and its output (not HTTP\n"
          "  curl checks like the after set); also the only baseline rows on the after set's model")
    if sa["stream-start-only dispatches"]:
        print("\noutput tokens: %d of %d after dispatches record <= %d (stream-start only) — NOT comparable"
              % (sa["stream-start-only dispatches"], sa["n"], STREAM_START_LIMIT))


def print_excluded(excluded, unclassified):
    print("\nexcluded explorer transcripts:")
    for e in excluded:
        print("  %s (%s): %s" % (e["agent_id"][:8], e["session"][:8], e["reason"]))
    for u in unclassified:
        print("  UNCLASSIFIED %s (%s): in no list — decide and name it" % (u["agent_id"][:8], u["session"][:8]))


def print_report(baseline, after, excluded, unclassified, checks):
    print("W2273 explorer measurement — comparator: 19 baseline dispatches (plugin 0.2.1, "
          "2026-09-03..10-02) vs 3 after dispatches (plugin 0.4.0 + stride 1.84.0, 2026-10-05)\n")
    print_rows(baseline + after)
    print_summary(baseline, after)
    print_excluded(excluded, unclassified)
    print_checks(checks)


def print_checks(checks):
    print("\nbaseline check (transcripts + vendored rows):")
    for label, want, got, ok in checks:
        mark = "ok" if ok else ("--" if ok is None else "MISMATCH")
        print("  %-8s %-46s expected %-12s got %s" % (mark, label, fmt(want), fmt(got)))
    bad = mismatches(checks)
    print("  %s" % ("all reproducible figures match" if not bad else "%d mismatch(es)" % bad))
    return bad


def self_test():
    def asst(mid, usage, content, ts):
        return {"type": "assistant", "timestamp": ts, "message": {"id": mid, "usage": usage, "content": content}}

    def result(ts, tid="t"):
        return {"type": "user", "timestamp": ts, "message": {"content": [{"type": "tool_result", "tool_use_id": tid}]}}

    u = {"input_tokens": 3, "cache_creation_input_tokens": 100, "cache_read_input_tokens": 1000,
         "cache_creation": {"ephemeral_5m_input_tokens": 999}}
    assert context_of(u) == 1103, "context ignores the cache_creation object"

    recs = [asst("m1", dict(u, output_tokens=5), [{"type": "thinking"}], "2026-01-01T00:00:01Z"),
            asst("m1", dict(u, output_tokens=900), [{"type": "text", "text": "x"}], "2026-01-01T00:00:02Z")]
    d = dedupe_usage(recs)
    assert len(d) == 1 and d["m1"][0] == 0 and d["m1"][1]["output_tokens"] == 900, "dedupe keeps last usage, first line"

    T = "2026-01-01T00:00:%02dZ"
    base = [{"type": "user", "timestamp": T % 0, "message": {"content": "go"}},
            asst("a", {}, [{"type": "tool_use", "id": "t1", "name": "Bash", "input": {}}], T % 10),
            result(T % 20, "t1"),
            asst("b", {}, [{"type": "tool_use", "id": "t2", "name": "Bash", "input": {}}], T % 30),
            result(T % 40, "t2")]
    # baseline contract: final text request starts with a thinking record at 60
    old_style = base + [asst("c", {}, [{"type": "thinking"}], T % 50),
                        asst("c", {}, [{"type": "text", "text": "report"}], "2026-01-01T00:01:40Z")]
    assert report_share(old_style, 5) == (60.0, 100.0), "share runs from the last result before the request"
    assert old_report_share(old_style) == (60.0, 100.0)
    # after contract: report Write, its result, then a handback and its result
    new_style = base + [asst("c", {}, [{"type": "tool_use", "id": "t3", "name": "Write", "input": {}}], T % 50),
                        result(T % 55, "t3"),
                        asst("d", {}, [{"type": "tool_use", "id": "t4", "name": "SubagentHandback", "input": {}}], T % 58),
                        result(T % 59, "t4")]
    assert report_share(new_style, 5) == (19.0, 59.0), "results after the emitting request do not count"
    assert old_report_share(new_style) == (0.0, 59.0), "old definition collapses to 0 on a handback"

    reads = [("a", None, None), ("a", None, None), ("a", 10, 20), ("a", 30, 20), ("b", 10, 20)]
    assert repeat_reads(reads) == (3, 1, 1), "same-path vs same-range vs whole-file repeat reads"
    assert repeat_reads([("a", 1, 2), ("b", 1, 2)]) == (0, 0, 0)
    assert repeat_reads([("c", 5, 5), ("c", None, None)]) == (1, 0, 1), "whole read after a ranged read"
    assert repeat_reads([("d", None, None), ("d", 5, 5)]) == (1, 0, 0), "ranged read after a whole read"

    rm = {"name": "Bash", "input": {"command": "rm -f \"$D/x\"; rmdir \"$D\""}}
    probe = {"name": "Bash", "input": {"command": "curl -sS -i http://localhost:4000/"}}
    assert contract_only({"name": "SubagentHandback"}, "baseline") and contract_only({"name": "Write"}, "after")
    assert contract_only(rm, "after") and not contract_only(rm, "baseline"), "cleanup is contract-only after only"
    assert not contract_only(probe, "after") and not contract_only({"name": "Write"}, "baseline")

    n, exact, hashes = severity_counts([{"severity": "High"}, {"severity": "major"}, {}, {"severity": "Minor"}])
    assert (n, exact, len(set(hashes))) == (4, 2, 4), "None counts as a bug and a distinct string"
    assert first_json_fence("x\n```json\n{\"bugs\": []}\n```\n```json\n{}\n```") == {"bugs": []}
    assert first_json_fence("no fence") is None
    assert SKILL_PATH_RE.findall("/p/stride-exploratory-testing/0.2.1/skills/bug-advocacy/SKILL.md") == ["bug-advocacy/SKILL"]
    print("self-test: ok")


def print_json(baseline, after, excluded, unclassified, checks):
    strip = lambda r: {k: v for k, v in r.items() if k not in ("vendored", "severity_hashes")}
    print(json.dumps(dict(
        comparator=dict(baseline="19 dispatches, plugin 0.2.1, 2026-09-03..2026-10-02",
                        after="3 dispatches, plugin 0.4.0 + stride 1.84.0, 2026-10-05, session " + AFTER_SESSION),
        baseline=[strip(r) for r in baseline], after=[strip(r) for r in after],
        summary=dict(baseline=summarise(baseline), after=summarise(after),
                     baseline_script_execution=summarise([r for r in baseline if r.get("charter_kind") == SCRIPT_RUN])),
        excluded=excluded, unclassified=unclassified,
        baseline_check=[dict(label=l, expected=w, got=g, ok=o) for l, w, g, o in checks]),
        indent=1, default=str))


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--project", default=PROJECT, help="Claude Code project transcript directory")
    parser.add_argument("--baseline-file", default=BASELINE_FILE, help="vendored baseline aggregates")
    parser.add_argument("--json", action="store_true", help="print rows, summaries and checks as JSON")
    parser.add_argument("--baseline-check", action="store_true",
                        help="only check the baseline reproduces; exit 1 on a mismatch")
    parser.add_argument("--self-test", action="store_true", help="run the in-memory checks and exit")
    return parser


def run_measurement(args):
    """Every mode but --self-test. Prints, then exits 1 if any reproducible baseline figure mismatches."""
    baseline, after, excluded, unclassified = collect(args.project, args.baseline_file)
    checks = baseline_check(baseline)
    if args.baseline_check:
        print_checks(checks)
    elif args.json:
        print_json(baseline, after, excluded, unclassified, checks)
    else:
        print_report(baseline, after, excluded, unclassified, checks)
    return 1 if mismatches(checks) else 0


def main():
    args = build_parser().parse_args()
    if args.self_test:
        self_test()
        return 0
    return run_measurement(args)


if __name__ == "__main__":
    sys.exit(main())
