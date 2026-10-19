# aidlc-custom

An **unofficial** extension for the [AWS AI-DLC workflow](https://github.com/awslabs/aidlc-workflows), packaged as a Claude Code plugin. Not affiliated with or endorsed by AWS.

AI-DLC runs a full staged workflow (requirements → design → code → build/test) with approval gates. That fits large features, but teams skip it for small changes, so those changes leave no design notes and the functional spec drifts. aidlc-custom adds:

- **Work tracks (S / M / L).** Every request is sized first with an 8-question checklist. Track S (filters, exports, small fixes, small standalone prototypes) is intent → code and tests → spec sync → ship, with no design documents and no approval gates; Track M (the default for a clear-scope feature, even a new module or integration) has one requirements + functional-design gate; Track L runs the full AI-DLC workflow, only when requirements stay unclear after a round of questions or the work ships as several units.
- **Small CLAUDE.md.** `CLAUDE.md` holds only a ~2.4 KB team section (sizing and Track S). The ~25 KB core AI-DLC workflow is a separate file read only for Track M/L, so small requests don't pay for it on every call.
- **Extensions per project.** `extensions` in the config turns the large AI-DLC extensions (security, resiliency, property-based testing) on, off or "ask" up front. `init` turns them off for prototypes and frontend-only apps; the read guard refuses the files of an extension that is off.
- **Spec sync, enforced.** Any `feat`/`fix` commit that changes source code must also update the functional spec, or say `spec: no behaviour change`. A `commit-msg` git hook checks this, for AI and human commits alike.
- **Context budget.** Hooks keep the AI-DLC bookkeeping out of the model's context: whole-file reads of the audit log and large spec files are refused (grep, then read a range), the audit log rotates monthly, and an oversized state file triggers a warning.
- **Closing a change (TRACK-07).** simplify → code review → you pick the fixes → tests → spec sync → audit log → commit. It is a rule with its own checklists, so it works in any AI tool (just ask to "ship"); in Claude Code, `/aidlc-custom:ship` runs it. Steps 2 and 3 also exist as `/aidlc-custom:simplify` and `/aidlc-custom:code-review`; `ship` prefers Claude Code's own `simplify`/`code-review` when present. Review is scaled to risk: **full** for permissions, business rules, data changes, APIs and larger server changes; **light** (no subagents) for UI tweaks; findings are labelled new or pre-existing, and pre-existing ones go to the backlog.
- **Fewer re-reads (TRACK-09, TRACK-10).** Approval gates can be batched ("as recommended through code generation"), design and code run in separate sessions with a `## Resume here` hand-off, and small requests that arrive together ship once.
- **Docs on demand.** `/aidlc-custom:doc` writes documentation outside the change flow: the full AS-IS spec from the code (or one area of it), a one-page change note for a Track S change, or a Word export of the spec.

## Requirements

- Claude Code with plugin support
- The AWS AI-DLC **v1** rules in the project (for example `.aidlc/aidlc-rules/`). A copy of v1.0.1 is vendored in `vendor/aidlc-rules/`; `init` offers to install it when the project has none, and `export_to_project.py --with-aidlc` installs it. AI-DLC 2.x uses a different runtime and is not supported.
- `python3` on the PATH (the hooks are small Python scripts with no dependencies)
- Node.js only for the Word export (`/aidlc-custom:doc docx`, `tools/spec-docx/`)

## Install

```text
/plugin marketplace add <owner>/aidlc-custom
/plugin install aidlc-custom@aidlc-custom
```

Then, in each project:

```text
/aidlc-custom:init
```

`init` offers to install the vendored AI-DLC v1 rules if the project has none, then creates `.aidlc/aidlc-custom.json`, installs the `commit-msg` hook into `.githooks/`, adds the Work Tracks extension to the AI-DLC rules, puts the short team section in `CLAUDE.md` (offering to move an inlined core workflow out into its own file), and prepares the state/audit layout. It is safe to re-run.

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

`--with-aidlc` also installs the vendored AWS AI-DLC v1.0.1 rules in AI-DLC's `.aidlc/aidlc-rules/` layout (rule details plus `core-workflow.md`) and, if the project has no `CLAUDE.md` yet, a `CLAUDE.md` with the short team section. Rules already in the project and an existing `CLAUDE.md` are left as is (the script says so; `/aidlc-init` then updates `CLAUDE.md`); leave the flag off if the project already has AI-DLC.

This writes the hook scripts and templates to `.claude/aidlc-custom/`, the skills to `.claude/skills/` as `/aidlc-init`, `/aidlc-ship`, `/aidlc-simplify`, `/aidlc-code-review` and `/aidlc-doc` (with the Word export tool in `.claude/aidlc-custom/tools/spec-docx/`), and merges the hooks into `.claude/settings.json`. Then run `/aidlc-init` in the project and commit `.claude/` (plus `.aidlc/` and `CLAUDE.md` with `--with-aidlc`). Re-run the script to update; each project keeps its own copy.

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

`/aidlc-init` reads the project to fill in `.aidlc/aidlc-custom.json` (source directories, test and type-check commands from `package.json`, `Makefile` or similar, and which extensions the project needs) and asks when unsure. It installs the `commit-msg` hook, adds the Work Tracks extension and writes the team section into `CLAUDE.md`. Check the config it shows, then commit:

```bash
git add .claude .aidlc .githooks CLAUDE.md   # and aidlc-docs/ if init changed it
git commit -m "chore: set up AI-DLC v1 and aidlc-custom"
```

Teammates only pull and open Claude Code; the SessionStart hook sets `core.hooksPath`. Anyone committing outside Claude Code runs `git config core.hooksPath .githooks` once.

If the project has no functional spec yet, the commit hook blocks `feat`/`fix` commits that touch `sourceDirs` until there is one (or the message says `spec: no behaviour change`). For an existing codebase, make the as-is spec the first piece of work, for example "write the as-is functional spec for this system"; AI-DLC reverse-engineers it.

### Day to day

Ask for the change as usual. Claude sizes it first and states the track in one line:

| Request | Track | What runs |
|---|---|---|
| "Add a status filter to the requests list" | S | intent in chat, code, tests, spec update, report; no design documents, no approvals |
| "Make a tic-tac-toe game" (no backend, no real data) | S | the same; the first spec file is a short description of the game |
| "Add an approver column that only managers can see" | M | short requirements and functional design (one approval), then code |
| "Sync employees from the HR system every night" | L | the full AI-DLC workflow with every approval gate |

Say "track M", "track L" or "full workflow" to override; your choice wins.

When the change is done, close it:

```text
> /aidlc-ship              # add "push" to push, "full"/"light" to force a review level, "no-review" for docs-only or trivial changes, "fix-all" to skip the pick
```

It simplifies, reviews, then stops for you to pick which findings to fix (only if it found something).

Documentation beyond the spec update is a separate step, whenever you need it:

```text
> /aidlc-doc                     # list what the spec doesn't cover yet and fill it in
> /aidlc-doc requests module     # write or expand the spec for one area
> /aidlc-doc change HEAD~3..HEAD # one-page change note in aidlc-docs/changes/
> /aidlc-doc docx                # Word export of the spec (needs Node.js)
``` After that it runs the tests, syncs the spec, appends to `aidlc-docs/audit.md` and commits.

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
| `extensions` | `{}` | TRACK-08: `"on"`, `"off"` or `"ask"` per AI-DLC extension (`security-baseline`, `resiliency-baseline`, `property-based-testing`); read guard refuses files of `"off"` ones |
| `securityChecklist` | `[]` | extra Track S checklist items |

A project without this file is untouched: every hook exits without doing anything.

## What's in the box

```text
.claude-plugin/     plugin.json, marketplace.json
hooks/hooks.json    SessionStart and PreToolUse(Read) hooks
scripts/            session_start.py, guard_read.py, aidlc_config.py
skills/             ship, simplify, code-review, doc, init
templates/          work-tracks.md (AI-DLC extension), commit-msg, CLAUDE.md section, config
tools/              export_to_project.py (no-plugin install); spec-docx: optional .docx export of the spec
tests/              python3 -m unittest discover tests
vendor/             AWS AI-DLC v1.0.1 rules (MIT-0), see vendor/README.md
```

## Limits

- Hooks only see Claude Code tool calls: a `cat` through the shell is not intercepted, and the rule "Track S skips the core workflow and extension rule files" can't be enforced by a hook because a hook can't tell the track. Extensions set to `"off"` are enforced for every track.
- The commit hook is a client-side check (`git commit --no-verify` skips it). For a hard gate, run the same check in CI.

## License

MIT, see [LICENSE](LICENSE). The vendored AWS AI-DLC rules in `vendor/aidlc-rules/` keep their own MIT No Attribution license from Amazon.
