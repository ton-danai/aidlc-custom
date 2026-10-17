# aidlc-custom

An **unofficial** extension for the [AWS AI-DLC workflow](https://github.com/awslabs/aidlc-workflows), packaged as a Claude Code plugin. Not affiliated with or endorsed by AWS.

AI-DLC runs a full staged workflow (requirements → design → code → build/test) with approval gates. That fits large features, but teams skip it for small changes, so those changes leave no design notes and the functional spec drifts. aidlc-custom adds:

- **Work tracks (S / M / L).** Every request is sized first with a 7-question checklist. Track S (filters, exports, small fixes) goes straight to code and tests; Track M adds one functional-design gate; Track L runs the full AI-DLC workflow.
- **Spec sync, enforced.** Any `feat`/`fix` commit that changes source code must also update the functional spec, or say `spec: no behaviour change`. A `commit-msg` git hook checks this, for AI and human commits alike.
- **Context budget.** Hooks keep the AI-DLC bookkeeping out of the model's context: whole-file reads of the audit log and large spec files are refused (grep, then read a range), the audit log rotates monthly, and an oversized state file triggers a warning.
- **`/aidlc-custom:ship`.** One command to close a change: simplify → code review → you pick the fixes → tests → spec sync → audit log → commit.

## Requirements

- Claude Code with plugin support
- The AWS AI-DLC rules installed in the project (for example `.aidlc-rule-details/`)
- `python3` on the PATH (the hooks are small Python scripts with no dependencies)
- Node.js only if you use the optional Word export in `tools/spec-docx/`

## Install

```text
/plugin marketplace add <owner>/aidlc-custom
/plugin install aidlc-custom@aidlc-custom
```

Then, in each project:

```text
/aidlc-custom:init
```

`init` creates `.aidlc/aidlc-custom.json`, installs the `commit-msg` hook into `.githooks/`, adds the Work Tracks extension to the AI-DLC rules, inserts a short team-rules section into `CLAUDE.md`, and prepares the state/audit layout. It is safe to re-run.

To have teammates prompted to install the plugin, add to the project's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "aidlc-custom": { "source": { "source": "github", "repo": "<owner>/aidlc-custom" } }
  },
  "enabledPlugins": { "aidlc-custom@aidlc-custom": true }
}
```

Teammates who commit without Claude Code run `git config core.hooksPath .githooks` once.

## Configuration — `.aidlc/aidlc-custom.json`

| Key | Default | Used by |
|---|---|---|
| `sourceDirs` | — | commit hook: which staged paths count as source code |
| `testFilePattern` | `\.(spec\|test)\.[jt]sx?$` | commit hook: test files don't require a spec change |
| `specDir` | `aidlc-docs/functional-spec/as-is` | commit hook, read guard |
| `auditFile`, `auditArchiveDir` | `aidlc-docs/audit.md`, `aidlc-docs/audit` | read guard, monthly rotation |
| `stateFile`, `stateLimitBytes` | `aidlc-docs/aidlc-state.md`, `15000` | size warning |
| `specSmallBytes`, `maxReadLines` | `12000`, `400` | read guard thresholds |
| `gitHooksPath` | `.githooks` | session start sets `core.hooksPath` |
| `commands.test`, `commands.typecheck`, `commands.restart` | — | `/aidlc-custom:ship` |
| `securityChecklist` | `[]` | extra Track S checklist items |

A project without this file is untouched: every hook exits without doing anything.

## What's in the box

```text
.claude-plugin/     plugin.json, marketplace.json
hooks/hooks.json    SessionStart and PreToolUse(Read) hooks
scripts/            session_start.py, guard_read.py, aidlc_config.py
skills/             ship, init
templates/          work-tracks.md (AI-DLC extension), commit-msg, CLAUDE.md section, config
tools/spec-docx/    optional: build a .docx from a Markdown functional spec
tests/              python3 -m unittest discover tests
```

## Limits

- Hooks only see Claude Code tool calls: a `cat` through the shell is not intercepted, and the rule "Track S skips the extension rule files" can't be enforced by a hook because a hook can't tell the track.
- The commit hook is a client-side check (`git commit --no-verify` skips it). For a hard gate, run the same check in CI.

## License

Not yet decided — this repository is private for now. Choose a license before making it public.
