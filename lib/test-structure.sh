#!/usr/bin/env bash
# Structure smoke test for the stride-exploratory-testing plugin.
#
# Asserts the plugin ships every file a Claude Code plugin and this
# plugin's docs require: a valid manifest, all six skills, all six
# commands, both agents, the three README-referenced fixtures, and the
# root docs. Pure shell + python3 (for JSON) — no network, no jq.
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

for cmd in charter nightmare-headline explore pair recon debrief; do
  if [ -f "${PLUGIN_ROOT}/commands/${cmd}.md" ]; then
    ok "commands/${cmd}.md exists"
  else
    nope "commands/${cmd}.md is missing" ""
  fi
done

# Count only *.md command files (the .gitkeep placeholder is ignored).
CMD_COUNT=$(find "${PLUGIN_ROOT}/commands" -maxdepth 1 -name '*.md' | wc -l | tr -d ' ')
if [ "$CMD_COUNT" -eq 6 ]; then
  ok "exactly 6 command files present (.gitkeep ignored)"
else
  nope "expected 6 command files, found ${CMD_COUNT}" ""
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
