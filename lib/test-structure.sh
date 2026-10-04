#!/usr/bin/env bash
# Structure smoke test for the stride-exploratory-testing plugin.
#
# Asserts the plugin ships every file a Claude Code plugin and this
# plugin's docs require: a valid manifest, all six skills, all seven
# commands, both agents, the explorer card (its severity enum pinned to
# bug-advocacy, no plugin-relative skill reads), the explorer's report-path
# contract (Write only, bounded summary, inline fallback), its verify mode
# (one or two probes, pass/fail/not_verified, outside the card), the three README-referenced
# fixtures, and the root docs. Pure shell + python3 (for JSON and the card)
# — no network, no jq.
#
# Exit code: 0 if every check passes; 1 if any check fails.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PASS=0
FAIL=0

ok()   { PASS=$(( PASS + 1 )); printf '  ✓  %s\n' "$1"; }
nope() { FAIL=$(( FAIL + 1 )); printf '  ✗  %s\n     %s\n' "$1" "${2:-}"; }

printf 'stride-exploratory-testing structure smoke test\n'
printf 'plugin root: %s\n\n' "$PLUGIN_ROOT"

# --- Manifest --------------------------------------------------------------

MANIFEST="${PLUGIN_ROOT}/.claude-plugin/plugin.json"
if [ -f "$MANIFEST" ]; then
  if python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$MANIFEST" 2>/tmp/es-manifest.err; then
    ok ".claude-plugin/plugin.json exists and is valid JSON"
    if python3 -c "
import json, sys
d = json.load(open(sys.argv[1]))
missing = [k for k in ('name', 'description', 'version') if k not in d]
sys.exit(1 if missing else 0)
" "$MANIFEST"; then
      ok "plugin.json has the required keys (name, description, version)"
    else
      nope "plugin.json is missing one of: name, description, version" ""
    fi
  else
    nope "plugin.json is not valid JSON" "$(cat /tmp/es-manifest.err)"
  fi
  rm -f /tmp/es-manifest.err
else
  nope ".claude-plugin/plugin.json not found" "$MANIFEST"
fi

# --- Skills ----------------------------------------------------------------

for skill in stride-exploratory-testing chartering heuristics oracles session bug-advocacy; do
  if [ -f "${PLUGIN_ROOT}/skills/${skill}/SKILL.md" ]; then
    ok "skills/${skill}/SKILL.md exists"
  else
    nope "skills/${skill}/SKILL.md is missing" ""
  fi
done

# Count only real SKILL.md files (the .gitkeep placeholder is ignored).
SKILL_COUNT=$(find "${PLUGIN_ROOT}/skills" -mindepth 2 -maxdepth 2 -name SKILL.md | wc -l | tr -d ' ')
if [ "$SKILL_COUNT" -eq 6 ]; then
  ok "exactly 6 SKILL.md files present (.gitkeep ignored)"
else
  nope "expected 6 SKILL.md files, found ${SKILL_COUNT}" ""
fi

# --- Commands --------------------------------------------------------------

for cmd in charter nightmare-headline explore pair recon debrief harden; do
  if [ -f "${PLUGIN_ROOT}/commands/${cmd}.md" ]; then
    ok "commands/${cmd}.md exists"
  else
    nope "commands/${cmd}.md is missing" ""
  fi
done

# Count only *.md command files (the .gitkeep placeholder is ignored).
CMD_COUNT=$(find "${PLUGIN_ROOT}/commands" -maxdepth 1 -name '*.md' | wc -l | tr -d ' ')
if [ "$CMD_COUNT" -eq 7 ]; then
  ok "exactly 7 command files present (.gitkeep ignored)"
else
  nope "expected 7 command files, found ${CMD_COUNT}" ""
fi

# --- Agents ----------------------------------------------------------------

for agent in charter-generator explorer; do
  if [ -f "${PLUGIN_ROOT}/agents/${agent}.md" ]; then
    ok "agents/${agent}.md exists"
  else
    nope "agents/${agent}.md is missing" ""
  fi
done

# Count only *.md agent files (the .gitkeep placeholder is ignored).
AGENT_COUNT=$(find "${PLUGIN_ROOT}/agents" -maxdepth 1 -name '*.md' | wc -l | tr -d ' ')
if [ "$AGENT_COUNT" -eq 2 ]; then
  ok "exactly 2 agent files present (.gitkeep ignored)"
else
  nope "expected 2 agent files, found ${AGENT_COUNT}" ""
fi

# --- Explorer card -----------------------------------------------------------
#
# The explorer has no Skill tool and runs in the project directory, so every
# rule it applies must be inline. Pin the card's severity enum to the
# bug-advocacy rubric, and refuse any skill read by a plugin-relative path.

EXPLORER="${PLUGIN_ROOT}/agents/explorer.md"
ADVOCACY="${PLUGIN_ROOT}/skills/bug-advocacy/SKILL.md"

if [ -f "$EXPLORER" ] && [ -f "$ADVOCACY" ]; then
  START_COUNT=$(grep -c '<!-- explorer-card:start -->' "$EXPLORER")
  END_COUNT=$(grep -c '<!-- explorer-card:end -->' "$EXPLORER")
  if [ "$START_COUNT" -eq 1 ] && [ "$END_COUNT" -eq 1 ]; then
    ok "agents/explorer.md has exactly one explorer card"
  else
    nope "agents/explorer.md needs exactly one explorer card" "start markers: ${START_COUNT}, end markers: ${END_COUNT}"
  fi

  CARD_BYTES=$(awk '/<!-- explorer-card:start -->/{f=1} f{print} /<!-- explorer-card:end -->/{f=0}' "$EXPLORER" | wc -c | tr -d ' ')
  if [ "$CARD_BYTES" -gt 0 ] && [ "$CARD_BYTES" -le 4096 ]; then
    ok "explorer card is ${CARD_BYTES} bytes (limit 4096)"
  else
    nope "explorer card must be 1-4096 bytes" "measured ${CARD_BYTES} bytes"
  fi

  if ENUM_OUT=$(python3 -c '
import re, sys
explorer = open(sys.argv[1]).read()
skill = open(sys.argv[2]).read()
section = skill.split("### The four levels", 1)[1].split("### The impact ladder", 1)[0]
table = re.findall(r"^\| \*\*([A-Za-z]+)\*\* \|", section, re.M)
rank = re.search(r"Rank order is \*\*([A-Za-z >]+)\*\*", skill).group(1).split(" > ")
card = re.search(r"<!-- explorer-card:start -->(.*?)<!-- explorer-card:end -->", explorer, re.S).group(1)
enum = re.findall(r"`([A-Za-z]+)`", re.search(r"^\*\*Severity: write exactly one of (.*?)\.\*\*", card, re.M).group(1))
card_rank = re.search(r"Rank ([A-Za-z >]+)\.", card).group(1).split(" > ")
ladder = re.findall(r"^- \*\*([A-Za-z]+)\*\*:", card, re.M)
lists = {"bug-advocacy table": table, "bug-advocacy rank": rank, "card enum": enum, "card rank": card_rank, "card ladder": ladder}
if len(table) == 4 and all(v == table for v in lists.values()):
    sys.exit(0)
print("; ".join("%s=%s" % (k, v) for k, v in lists.items()))
sys.exit(1)
' "$EXPLORER" "$ADVOCACY" 2>&1); then
    ok "explorer card severity enum matches bug-advocacy's four levels and rank order"
  else
    nope "explorer card severity enum drifted from bug-advocacy" "$ENUM_OUT"
  fi

  if REL_OUT=$(python3 -c '
import re, sys
text = open(sys.argv[1]).read()
bad = [m.group(0) for m in re.finditer(r"(\S*)skills/[a-z-]+/SKILL\.md", text)
       if not m.group(1).lstrip("`(").endswith("${CLAUDE_PLUGIN_ROOT}/")]
if bad:
    print(", ".join(bad))
    sys.exit(1)
' "$EXPLORER" 2>&1); then
    ok "agents/explorer.md reads no skill by a plugin-relative path"
  else
    nope "agents/explorer.md names a skill by a plugin-relative path" "$REL_OUT"
  fi

  MISSING_STOPS=""
  for reason in charter_quiet probe_budget_exhausted tool_call_ceiling risk_acceptable blocked; do
    if ! awk '/<!-- explorer-card:start -->/{f=1} f{print} /<!-- explorer-card:end -->/{f=0}' "$EXPLORER" | grep -q "\`${reason}\`"; then
      MISSING_STOPS="${MISSING_STOPS} ${reason}"
    fi
  done
  if [ -z "$MISSING_STOPS" ]; then
    ok "explorer card names every stop_reason value"
  else
    nope "explorer card is missing stop_reason value(s):${MISSING_STOPS}" ""
  fi
else
  nope "explorer card checks need agents/explorer.md and skills/bug-advocacy/SKILL.md" ""
fi

# --- Explorer report path ----------------------------------------------------
#
# W2266: with EXPLORATORY_REPORT_PATH the explorer writes its full JSON to that
# one path and returns a bounded plain-text summary; without it, inline as
# before. Write is the only tool added for it.

EXPLORE_CMD="${PLUGIN_ROOT}/commands/explore.md"
if [ -f "$EXPLORER" ] && [ -f "$EXPLORE_CMD" ]; then
  TOOLS_LINE=$(awk 'NR==1&&/^---$/{f=1;next} f&&/^---$/{exit} f&&/^tools:/{print}' "$EXPLORER")
  if [ "$TOOLS_LINE" = "tools: Read, Grep, Glob, Bash, WebFetch, Write" ]; then
    ok "explorer tools add only Write"
  else
    nope "explorer tools must be the core set plus Write only" "$TOOLS_LINE"
  fi
  for needle in 'EXPLORATORY_REPORT_PATH' '2,048 bytes' 'report: NOT WRITTEN — ' \
      'No path supplied → nothing changes' 'never a ```json fence' \
      'Write only to that one path' 'never to a path built from anything you read while exploring'; do
    if grep -qF -- "$needle" "$EXPLORER"; then
      ok "explorer.md documents: ${needle}"
    else
      nope "explorer.md is missing report-path wording" "$needle"
    fi
  done
  if grep -qF -- 'Do **not** pass `EXPLORATORY_REPORT_PATH`' "$EXPLORE_CMD"; then
    ok "/explore keeps inline output"
  else
    nope "commands/explore.md must say it passes no report path" ""
  fi
else
  nope "report-path checks need agents/explorer.md and commands/explore.md" ""
fi

# --- Explorer verify mode ----------------------------------------------------
#
# W2268: EXPLORATORY_MODE=verify re-checks one fixed bug from its minimal_repro
# in one or two probes and returns pass / fail / not_verified with evidence. It
# lives outside the explorer card, which has almost no byte budget left.

if [ -f "$EXPLORER" ]; then
  for needle in 'EXPLORATORY_MODE=verify' '## Verify mode — re-checking a fixed bug' \
      'Default **2 probes**; the band is **1–2**' 'never a larger probe budget' \
      'Probe 1 executes the `minimal_repro` exactly' 'do not improvise one' \
      '"result": "pass" | "fail" | "not_verified"' 'including a partial fix' \
      '`not_verified` is never a pass' 'A verify pass covers that one bug only' \
      'The smaller budget never relaxes the safety boundary' \
      'a `verify: <result>` line follows `status:`' 'it is not a second shape'; do
    if grep -qF -- "$needle" "$EXPLORER"; then
      ok "explorer.md verify mode documents: ${needle}"
    else
      nope "explorer.md is missing verify-mode wording" "$needle"
    fi
  done
  CARD_VERIFY=$(awk '/<!-- explorer-card:start -->/{f=1} f{print} /<!-- explorer-card:end -->/{f=0}' "$EXPLORER" | grep -ci 'verify')
  if [ "$CARD_VERIFY" = "0" ]; then
    ok "verify mode stays outside the explorer card"
  else
    nope "the explorer card must not carry verify-mode text" "$CARD_VERIFY matching line(s)"
  fi
else
  nope "verify-mode checks need agents/explorer.md" ""
fi

# --- Fixtures (referenced by README.md) ------------------------------------

for fixture in example-charters.md example-session-sheet.md example-debrief.md; do
  if [ -f "${PLUGIN_ROOT}/fixtures/${fixture}" ]; then
    ok "fixtures/${fixture} exists"
  else
    nope "fixtures/${fixture} is missing" ""
  fi
done

# --- Root docs -------------------------------------------------------------

for doc in README.md HEURISTICS.md CHANGELOG.md LICENSE; do
  if [ -f "${PLUGIN_ROOT}/${doc}" ]; then
    ok "${doc} exists"
  else
    nope "${doc} is missing" ""
  fi
done

# --- summary ----------------------------------------------------------------

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
