# Changelog

## 0.2.0 — 2026-10-17

Lighter path for small work. After updating the plugin, re-run `/aidlc-custom:init` in each project: it updates `CLAUDE.md`, `work-tracks.md` and the config, which a plugin update does not touch.


- Track S is intent → code and tests → spec sync → ship: no core workflow, stage or extension rule files, no welcome message, no design documents, no approval gates; small standalone prototypes with no backend or real data are Track S
- `CLAUDE.md` holds only a ~2.5 KB team section; the core AI-DLC workflow moves to `.aidlc/aidlc-rules/aws-aidlc-rules/core-workflow.md` and is read for Track M/L only. `init` offers to move an inlined workflow out of an existing `CLAUDE.md`
- Fewer stops: Track M folds requirements into the single functional-design approval; ship stops for fix selection only when the review found something, and `fix-all` skips it
- TRACK-08 and the `extensions` config key: security, resiliency and property-based testing are set on/off/ask per project (off for prototypes); the read guard refuses files of extensions set to off
- `/aidlc-custom:doc`: documentation on demand, outside the change flow — the full AS-IS spec from the code, a change note for a Track S change, or the Word export; the no-plugin export now includes it and `tools/spec-docx`
- `--with-aidlc` and `init` install the vendored rules in AI-DLC's `.aidlc/aidlc-rules/` layout

## 0.1.0

First version, extracted from a team's AI-DLC setup.

- Work Tracks extension (TRACK-01..07): classify S/M/L, what each track runs, escalation, recording, spec sync, context budget, closing a change (tool-neutral simplify and review checklists)
- `commit-msg` hook: feat/fix commits that touch source code must update the spec or say `spec: no behaviour change`
- Hooks: read guard for audit/spec files, monthly audit rotation, state-size warning, `core.hooksPath` setup
- Skills: `/aidlc-custom:ship`, `/aidlc-custom:simplify`, `/aidlc-custom:code-review`, `/aidlc-custom:init`
- `tools/spec-docx`: Markdown functional spec → Word document
- `tools/export_to_project.py`: install into a project's `.claude/` without the plugin
- `vendor/aidlc-rules/`: AWS AI-DLC v1.0.1 rules (MIT-0); `export_to_project.py --with-aidlc` installs them with `CLAUDE.md`, and `/aidlc-custom:init` offers to when the project has none, so one repo sets a project up
