# Changelog

All notable changes to the `stride-exploratory-testing` plugin are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Full `README.md`: the "Tested = Checked + Explored" model, a safety callout, Stride-marketplace install, prerequisites, the five engines, an enumeration of all five skills / five commands / two agents, an end-to-end quick-start, and a Sources & attribution section (Kaner, Hendrickson's *Explore It!*, SBTM by Jonathan & James Bach, PROOF by Jonathan Bach, Whittaker's Tours, Bach's HTSM).
- `HEURISTICS.md` — a one-page pointer into the `heuristics` skill (does not duplicate its catalog).
- `fixtures/` worked examples of the full flow against a synthetic target: `example-charters.md` (a ranked charter set with a nightmare-headline derivation and a check-vs-charter reframe), `example-session-sheet.md` (a complete SBTM session sheet with Task Breakdown Metrics), and `example-debrief.md` (both the Explored/Found/Unknown and PROOF templates).

## [0.1.0] - 2026-07-20

Initial scaffold of the `stride-exploratory-testing` Claude Code plugin.

### Added

- Plugin manifest (`.claude-plugin/plugin.json`) with name, description, version, author, homepage/repository, MIT license, and keywords.
- Directory skeleton: `skills/`, `commands/`, `agents/`, `lib/`, `fixtures/`.
- `README.md` skeleton, `LICENSE` (MIT), and `.gitignore`.
- Standalone git repository, distributed through the existing `stride-marketplace` catalog.
