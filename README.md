# aidlc-custom

An **unofficial** extension for the [AWS AI-DLC workflow](https://github.com/awslabs/aidlc-workflows), packaged as a Claude Code plugin. Not affiliated with or endorsed by AWS.

AI-DLC runs a full staged workflow (requirements → design → code → build/test) with approval gates. That fits large features, but teams skip it for small changes, so those changes leave no design notes and the functional spec drifts. aidlc-custom adds:

- **Work tracks (S / M / L).** Every request is sized first with a 7-question checklist. Track S (filters, exports, small fixes) goes straight to code and tests; Track M adds one functional-design gate; Track L runs the full AI-DLC workflow.
- **Spec sync, enforced.** Any `feat`/`fix` commit that changes source code must also update the functional spec, or say `spec: no behaviour change`. A `commit-msg` git hook checks this, for AI and human commits alike.
- **Context budget.** Hooks keep the AI-DLC bookkeeping out of the model's context: whole-file reads of the audit log and large spec files are refused (grep, then read a range), the audit log rotates monthly, and an oversized state file triggers a warning.
- **Closing a change (TRACK-07).** simplify → code review → you pick the fixes → tests → spec sync → audit log → commit. It is a rule with its own checklists, so it works in any AI tool (just ask to "ship"); in Claude Code, `/aidlc-custom:ship` runs it. Steps 2 and 3 also exist as `/aidlc-custom:simplify` and `/aidlc-custom:code-review`; `ship` prefers Claude Code's own `simplify`/`code-review` when present.

## Requirements

- Claude Code with plugin support
- The AWS AI-DLC **v1** rules in the project (for example `.aidlc-rule-details/`). A copy of v1.0.1 is vendored in `vendor/aidlc-rules/`; `init` offers to install it when the project has none, and `export_to_project.py --with-aidlc` installs it. AI-DLC 2.x uses a different runtime and is not supported.
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

`init` offers to install the vendored AI-DLC v1 rules if the project has none, then creates `.aidlc/aidlc-custom.json`, installs the `commit-msg` hook into `.githooks/`, adds the Work Tracks extension to the AI-DLC rules, inserts a short team-rules section into `CLAUDE.md`, and prepares the state/audit layout. It is safe to re-run.

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

### Without the plugin

To commit everything into the project instead, so nobody installs anything:

```bash
python3 tools/export_to_project.py /path/to/project --with-aidlc   # --dry-run to preview
```

`--with-aidlc` also installs the vendored AWS AI-DLC v1.0.1 rules: `.aidlc-rule-details/` and, if the project has no `CLAUDE.md` yet, `CLAUDE.md` with the core workflow. Rules already in the project and an existing `CLAUDE.md` are left as is (the script says so); leave the flag off if the project already has AI-DLC.

This writes the hook scripts and templates to `.claude/aidlc-custom/`, the skills to `.claude/skills/` as `/aidlc-init`, `/aidlc-ship`, `/aidlc-simplify` and `/aidlc-code-review`, and merges the hooks into `.claude/settings.json`. Then run `/aidlc-init` in the project and commit `.claude/` (plus `.aidlc-rule-details/` and `CLAUDE.md` with `--with-aidlc`). Re-run the script to update; each project keeps its own copy.

## Getting started

Command names below are for the no-plugin install; with the plugin they are `/aidlc-custom:init`, `/aidlc-custom:ship` and so on.

### Once per project

One person sets the project up and commits it for the team:

```bash
python3 tools/export_to_project.py ~/work/my-project --with-aidlc --dry-run   # preview
python3 tools/export_to_project.py ~/work/my-project --with-aidlc
cd ~/work/my-project && claude
> /aidlc-init
```

`/aidlc-init` reads the project to fill in `.aidlc/aidlc-custom.json` (source directories, test and type-check commands from `package.json`, `Makefile` or similar) and asks when unsure. It installs the `commit-msg` hook, adds the Work Tracks extension and inserts the team rules into `CLAUDE.md`. Check the config it shows, then commit:

```bash
git add .claude .aidlc .aidlc-rule-details .githooks CLAUDE.md   # and aidlc-docs/ if init changed it
git commit -m "chore: set up AI-DLC v1 and aidlc-custom"
```

Teammates only pull and open Claude Code; the SessionStart hook sets `core.hooksPath`. Anyone committing outside Claude Code runs `git config core.hooksPath .githooks` once.

If the project has no functional spec yet, the commit hook blocks `feat`/`fix` commits that touch `sourceDirs` until there is one (or the message says `spec: no behaviour change`). For an existing codebase, make the as-is spec the first piece of work, for example "write the as-is functional spec for this system"; AI-DLC reverse-engineers it.

### Day to day

Ask for the change as usual. Claude sizes it first and states the track in one line:

| Request | Track | What runs |
|---|---|---|
| "Add a status filter to the requests list" | S | code, tests, spec update, report; no design documents |
| "Add an approver column that only managers can see" | M | short requirements, functional design (one approval), then code |
| "Sync employees from the HR system every night" | L | the full AI-DLC workflow with every approval gate |

Say "track M", "track L" or "full workflow" to override; your choice wins.

When the change is done, close it:

```text
> /aidlc-ship              # add "push" to push, "no-review" for docs-only or trivial changes
```

It simplifies, reviews, then stops for you to pick which findings to fix. After that it runs the tests, syncs the spec, appends to `aidlc-docs/audit.md` and commits.

### Updating

Re-run `export_to_project.py` and commit the changes under `.claude/`. AI-DLC rules already in the project are not overwritten.

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
| `commands.test`, `commands.typecheck`, `commands.restart` | — | TRACK-07 / `/aidlc-custom:ship` |
| `securityChecklist` | `[]` | extra Track S checklist items |

A project without this file is untouched: every hook exits without doing anything.

## What's in the box

```text
.claude-plugin/     plugin.json, marketplace.json
hooks/hooks.json    SessionStart and PreToolUse(Read) hooks
scripts/            session_start.py, guard_read.py, aidlc_config.py
skills/             ship, simplify, code-review, init
templates/          work-tracks.md (AI-DLC extension), commit-msg, CLAUDE.md section, config
tools/              export_to_project.py (no-plugin install); spec-docx: optional .docx export of the spec
tests/              python3 -m unittest discover tests
vendor/             AWS AI-DLC v1.0.1 rules (MIT-0), see vendor/README.md
```

## Limits

- Hooks only see Claude Code tool calls: a `cat` through the shell is not intercepted, and the rule "Track S skips the extension rule files" can't be enforced by a hook because a hook can't tell the track.
- The commit hook is a client-side check (`git commit --no-verify` skips it). For a hard gate, run the same check in CI.

## License

MIT, see [LICENSE](LICENSE). The vendored AWS AI-DLC rules in `vendor/aidlc-rules/` keep their own MIT No Attribution license from Amazon.
