---
name: ship
description: Close out the current change in an aidlc-custom project — simplify, code review, apply the fixes the user picks, run the configured tests, sync the functional spec, log to aidlc-docs, and commit. Use when the user runs /aidlc-custom:ship or asks to finish, wrap up or ship the current work. Pass "push" to also push, "no-review" to skip the review steps.
---

# Ship

The closing sequence after every change: simplify → code review → fixes → tests → spec sync → log → commit. Only step 4 waits for the user. Run every other step without asking.

Project settings come from `.aidlc/aidlc-custom.json` (`commands`, `specDir`, `auditFile`, `stateFile`). If that file is missing, tell the user to run `/aidlc-custom:init` and stop.

Arguments:
- `push`: push to the remote after committing
- `no-review`: skip steps 2–4, for docs-only or trivial changes

## 1. Check the change

- `git status` and `git diff --stat`. If nothing changed, say so and stop.
- If unrelated changes are mixed in (stray untracked files, edits from another work item), list them and leave them out of the commit. Never `git add -A`. Stage files by path.
- Note which parts of the code changed (for example server, client, or both), to pick the commands in step 5.

## 2. Simplify

If a `simplify` skill is available, invoke it and let it apply its fixes. Note what it applied and skipped for the log. If it isn't available, skip this step.

## 3. Review

If a `code-review` skill is available, invoke it on the working tree without `--fix`. Otherwise review the diff yourself for correctness bugs.

## 4. Choose fixes (the only stop)

If the review found nothing, say so and go to step 5.

Otherwise, list the findings numbered, most severe first, one line each with `file:line`, and add a recommendation (for example "fix 1–3; 4 is pre-existing"). Then wait for the user to pick.

- Apply the chosen fixes, with a test for each behaviour change.
- For findings not chosen that are real but out of scope, ask once whether to record them in the project's backlog file, if it has one, following its existing format.

## 5. Verify

Run the `commands.test` and `commands.typecheck` entries from the config that apply to the changed code, in parallel where possible. If a migration was added, check that it applies and reverts on the dev database.

If anything fails, fix it and run it again. If you can't fix it, stop: report the failing output and don't commit.

If `commands.restart` is set and server code changed, run it and confirm the server started.

## 6. Spec sync

Follow `work-tracks.md` TRACK-05. Compare the final diff with the spec directory (`specDir`):
- If behaviour changed and the spec doesn't describe it yet, edit the matching file(s) now, using the table in TRACK-05. Locate rows with `grep -n` and read only those lines; don't read whole spec files.
- If the change is exempt, the commit message will carry `spec: no behaviour change`.

Don't regenerate document exports here.

## 7. Log

- Append to the audit file with `cat >> <auditFile> <<'EOF'`; don't read or rewrite it. Add one entry per step that ran (Simplify, Code Review Fixes, Ship), in the project's audit format, with the user's raw input and an ISO timestamp. Include the test counts.
- Update the state file according to TRACK-04: for Track S, one line under `## Track S Log`; for Track M/L, mark the work item complete. Fill in the commit sha after step 8 if the project records it.

## 8. Commit

Match the repo's commit style (see `git log`). Typical shape:

```
<type>(<scope>): <summary in the user's terms>

<1–2 short paragraphs: what the user sees and the rules it follows>

- notable change
- ...
```

- Types: `feat`, `fix`, `refactor`, `docs`, `chore`. The scope is the page or module.
- Add `spec: no behaviour change` on its own line when step 6 found the change exempt.
- End with the attribution lines the session asks for, if any.
- One commit per work item; include the `aidlc-docs/` updates in it.
- Commit on the current branch. Push only with the `push` argument.

## 9. Report

At most six lines: the commit sha and subject, the fixes applied, test counts, the spec files updated (or "spec: no behaviour change"), backlog items added, and whether it was pushed.
