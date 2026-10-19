# Changelog

## 0.3.0 — 2026-10-19

Lessons from running 0.2.0 on a production project: spend design and review tokens where a mistake is expensive. After updating the plugin, re-run `/aidlc-custom:init` in each project to update `work-tracks.md` and `CLAUDE.md`; a project that edited its own `work-tracks.md` should compare first, since init replaces it.

- TRACK-01: size alone no longer makes a request Track L. A new module, page group, external system or scheduled job is Track M; Track L needs requirements that stay unclear after a round of questions, several separately shipped units, or infrastructure design. The checklist has 8 questions
- TRACK-02: Track M asks who can see and who can change each new screen or endpoint (no assumed admin bypass), offers a recommended option for every question, and covers the component layout of a new module in Functional Design; Track L writes one Application Design file; a Track S bug fix stays where it broke
- TRACK-07: ship picks a review level (full / light / none) by risk and states it; `full` and `light` force one. Findings are labelled new or pre-existing, pre-existing ones and shared-code refactors go to the backlog; audit timestamps come from `date -u`; the report suggests a new session after a full cycle
- TRACK-09 (new): batched approvals, with the cases that still stop a batch
- TRACK-10 (new): one session per phase with a `## Resume here` hand-off, and small requests that arrive together ship once

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
