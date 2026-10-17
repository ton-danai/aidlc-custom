---
name: init
description: Set up aidlc-custom in the current repository — project config, the spec-sync commit-msg git hook, the Work Tracks extension for AI-DLC, the CLAUDE.md team-rules section, and the state/audit layout. Use when the user runs /aidlc-custom:init or asks to add or update aidlc-custom in a project. Safe to re-run; it updates what it installed and leaves project edits alone.
---

# Init

Installs aidlc-custom into the current git repository. Templates are in `${CLAUDE_PLUGIN_ROOT}/templates/`. Re-running it is safe: show what would change before overwriting anything the project may have edited.

## 0. Preconditions

- Must be inside a git repository (`git rev-parse --show-toplevel`). If not, stop and say so.
- Find the AI-DLC rule details directory, in this order: `.aidlc/aidlc-rules/aws-aidlc-rule-details/`, `.aidlc-rule-details/`, `.kiro/aws-aidlc-rule-details/`, `.amazonq/aws-aidlc-rule-details/`. If none exists, tell the user that aidlc-custom extends the AWS AI-DLC workflow (github.com/awslabs/aidlc-workflows), which must be installed first, and stop.
- Check that `python3` is on the PATH; the hooks need it.

## 1. Project config — `.aidlc/aidlc-custom.json`

If it exists, keep it and only add keys missing from the template. Otherwise create it from `templates/aidlc-custom.json`, adjusted to this repository:
- `sourceDirs`: the source roots that hold production code (for example `src`, `backend/src`, `frontend/src`, `apps/*/src`). Look at the tree; ask if unclear.
- `testFilePattern`: the project's test file naming.
- `specDir`: where the functional spec lives. Default `aidlc-docs/functional-spec/as-is`. If no spec exists yet, keep the default and mention it in the report.
- `commands.test` / `commands.typecheck` / `commands.restart`: from `package.json` scripts, `Makefile`, or equivalent. Leave `restart` empty unless there is an obvious dev-server restart.

Show the resulting config to the user.

## 2. Git hook

- Copy `templates/githooks/commit-msg` to `<gitHooksPath>/commit-msg` (default `.githooks/`) and make it executable.
- If `core.hooksPath` is unset, set it to `gitHooksPath`. If it is set to something else (Husky, lefthook, …), don't change it: tell the user to call `<gitHooksPath>/commit-msg "$1"` from their existing `commit-msg` hook.
- Teammates who don't use Claude Code need `git config core.hooksPath <gitHooksPath>` once; the plugin's SessionStart hook does it automatically for Claude Code users.

## 3. AI-DLC extension

Copy `templates/work-tracks.md` to `<rule details dir>/extensions/aidlc-custom/work-tracks/work-tracks.md`. There is no `*.opt-in.md`, so AI-DLC always enforces it. If the file exists and differs, show the diff and ask before replacing.

## 4. CLAUDE.md

If `CLAUDE.md` has no `## MANDATORY: Team rules (aidlc-custom)` section, insert `templates/claude-md-section.md` right after the first heading block (before the first `## ` section). If the section exists and differs from the template, show the diff and ask before replacing it.

## 5. State and audit layout

- `aidlc-docs/aidlc-state.md` (the `stateFile`): if it exists, add a row `| aidlc-custom Work Tracks | Yes (always enforced, no opt-in) | <today> |` to the extension configuration table if missing, and a `## Track S Log` section if missing. If it is larger than `stateLimitBytes`, offer to split it: a short index stays, and each work-item section moves unchanged to `aidlc-docs/work-items/NN-<slug>.md`, linked one line per item. Verify no line is lost.
- Audit (`auditFile`): if it holds entries from earlier months, the SessionStart hook will move them to `auditArchiveDir` on the next session start; mention this. Add a one-line note under the title saying new entries are appended with a heredoc and older months live in the archive directory.

## 6. Report

List each file created or changed, the config values chosen, anything skipped and why, and the next steps:
- commit the installed files (one `chore` commit),
- teammates: install the plugin, and run `git config core.hooksPath <gitHooksPath>` if they don't use Claude Code,
- if there is no functional spec yet: the spec-sync hook will block `feat`/`fix` commits that touch `sourceDirs` until one exists, or until each commit says `spec: no behaviour change`.
