# Changelog

All notable changes to the `stride-exploratory-testing` plugin are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **`interfaces` lens** — the Heuristic Test Strategy Model's **I**nterfaces element joins the coverage lens in the `chartering` skill, covering APIs, imports and exports, UI surfaces, and integration points between systems: the boundaries where service-oriented and LLM tool-calling applications most often fail. **Downstream consumers must handle `interfaces` as a new allowed value of a charter object's optional `lens` field** (`agents/charter-generator.md`), alongside the existing `structure`, `function`, `data`, `platform`, `operations`, and `time`.

### Changed

- **`SFDPOT` renamed to `SFDIPOT`** across the plugin — skills, agents, commands, fixtures, and docs. Bach's HTSM (v6.0, 2024) lists seven Product Elements; the six-letter `SFDPOT` the plugin cited is a superseded form of the same heuristic. The `Interfaces` row slots between `Data` and `Platform`; no existing row was renamed, reordered, or dropped. The charter object's `source` enum value is still the literal `sfdpot` — it is a wire value, not the acronym, and renaming it would break existing consumers. The `[0.1.0]` entry below is left as written: it is a historical record of what that release shipped.

## [0.1.0] - 2026-07-20

Initial release of the `stride-exploratory-testing` Claude Code plugin — a complete, charter-based exploratory-testing workflow: the "explored" half of *Tested = Checked + Explored*.

### Added

- **Plugin manifest** (`.claude-plugin/plugin.json`) with name, description, version, author, homepage/repository, MIT license, and keywords; standalone git repository distributed through the existing `stride-marketplace` catalog.
- **Five skills** — `stride-exploratory-testing` (orchestrator that teaches the model and routes requests), `chartering` (frame a mission as an `Explore <target> with <resources> to discover <information>` charter, ranked with SFDPOT and the Nightmare Headline Game), `heuristics` (the canonical catalog of general/web cheat sheets, the variable catalog, and Whittaker's Tours), `oracles` (Never/Always invariants, consistency oracles, and the HTSM quality-criteria checklist), and `session` (the SBTM lifecycle, session sheet, Task Breakdown Metrics, and both debrief templates).
- **Five slash commands** — `/charter`, `/nightmare-headline`, `/explore`, `/recon`, and `/debrief`.
- **Two subagents** — `charter-generator` (target + risk → ranked charters, read-only) and `explorer` (runs one charter to structured findings under an absolute safety boundary).
- **`README.md`** — the "Tested = Checked + Explored" model, a safety callout, Stride-marketplace install, prerequisites, the five engines, an enumeration of all five skills / five commands / two agents, an end-to-end quick-start, and a Sources & attribution section (Kaner, Hendrickson's *Explore It!*, SBTM by Jonathan & James Bach, PROOF by Jonathan Bach, Whittaker's Tours, Bach's HTSM).
- **`HEURISTICS.md`** — a one-page pointer into the `heuristics` skill (does not duplicate its catalog).
- **`fixtures/`** worked examples of the full flow against a synthetic target: `example-charters.md` (a ranked charter set with a nightmare-headline derivation and a check-vs-charter reframe), `example-session-sheet.md` (a complete SBTM session sheet with Task Breakdown Metrics), and `example-debrief.md` (both the Explored/Found/Unknown and PROOF templates).
- **`lib/` smoke-test harness** (pure shell, no network, no jq): `test-structure.sh` (manifest, skills, commands, agents, fixtures, and root docs present), `test-frontmatter.sh` (required YAML frontmatter keys on every skill/command/agent), and `test-all.sh` (a single runner that gates a release — exits non-zero if any check fails).
- `LICENSE` (MIT) and `.gitignore`.

## Release process

This plugin is distributed through the existing [`stride-marketplace`](https://github.com/cheezy/stride-marketplace) catalog. **The plugin's `version` must stay in sync across two repositories.** To cut a release:

1. In **this repo** (`stride-exploratory-testing`): bump `version` in `.claude-plugin/plugin.json`, add a matching dated entry to this `CHANGELOG.md`, commit, `git tag vX.Y.Z`, and push the tag + a matching GitHub release.
2. In **`stride-marketplace`**: set the `stride-exploratory-testing` entry's `version` in `.claude-plugin/marketplace.json` to the **same** `X.Y.Z`, bump the catalog `metadata.version`, update `CHANGELOG.md` and `README.md`, commit, tag, and push.

The marketplace entry `version` and this plugin's `plugin.json` `version` must always match — a mismatch means `/plugin install` / `/plugin update` resolves a version that was never released.
