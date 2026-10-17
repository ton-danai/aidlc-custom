# Changelog

## 0.1.0 — unreleased

First version, extracted from a team's AI-DLC setup.

- Work Tracks extension (TRACK-01..07): classify S/M/L, what each track runs, escalation, recording, spec sync, context budget, closing a change (tool-neutral simplify and review checklists)
- `commit-msg` hook: feat/fix commits that touch source code must update the spec or say `spec: no behaviour change`
- Hooks: read guard for audit/spec files, monthly audit rotation, state-size warning, `core.hooksPath` setup
- Skills: `/aidlc-custom:ship`, `/aidlc-custom:simplify`, `/aidlc-custom:code-review`, `/aidlc-custom:init`
- `tools/spec-docx`: Markdown functional spec → Word document
- `tools/export_to_project.py`: install into a project's `.claude/` without the plugin
- `vendor/aidlc-rules/`: AWS AI-DLC v1.0.1 rules (MIT-0); `export_to_project.py --with-aidlc` installs them with `CLAUDE.md`, and `/aidlc-custom:init` offers to when the project has none, so one repo sets a project up
