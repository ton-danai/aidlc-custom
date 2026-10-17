# Changelog

## 0.1.0 — unreleased

First version, extracted from a team's AI-DLC setup.

- Work Tracks extension (TRACK-01..06): classify S/M/L, what each track runs, escalation, recording, spec sync, context budget
- `commit-msg` hook: feat/fix commits that touch source code must update the spec or say `spec: no behaviour change`
- Hooks: read guard for audit/spec files, monthly audit rotation, state-size warning, `core.hooksPath` setup
- Skills: `/aidlc-custom:ship`, `/aidlc-custom:init`
- `tools/spec-docx`: Markdown functional spec → Word document
