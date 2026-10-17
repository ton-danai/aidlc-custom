# aidlc-custom Work Tracks

## Overview
This extension sizes every request into one of three tracks **before** any AI-DLC stage runs. The track decides which stages execute. It is always enforced: there is no `*.opt-in.md` file.

The full AI-DLC workflow suits large features, but teams end up skipping it for small changes, which then leave no design notes and no spec update. Track S makes the lightweight path a documented one, with the spec kept in sync, instead of a skip.

This file overrides the default "always run Requirements Analysis / Workflow Planning" for Track S, and trims Track M. For Track L, nothing changes: run the workflow in `CLAUDE.md` as written.

Project settings (source directories, spec location, test commands, extra checklist items) live in `.aidlc/aidlc-custom.json`.

---

## Rule TRACK-01: Classify Before Acting

**Rule**: Before writing code or creating any `aidlc-docs/` artifact for a new request, classify it as S, M or L using the checklist below. Then state the track in one line to the user, with the reason, for example:

> Track S: client-side filter on one page, no API, permission or schema change.

The user can override with "track M", "track L" or "full workflow". The override wins.

### Classification Checklist
Answer each question. Take the **highest** track that any "yes" maps to.

| # | Question | Yes → |
|---|---|---|
| 1 | Does it need a new module, page group, external system or scheduled job? (e.g. a nightly sync from a third-party API) | L |
| 2 | Will it be split into more than one unit of work, or take more than about a day? | L |
| 3 | Does it add or change a database table/column, i.e. a migration? | M |
| 4 | Does it add or change a permission, or who can see/edit something? (e.g. hiding a salary column from most users) | M |
| 5 | Does it add or change a business rule that the functional spec documents? (e.g. a new cut-off date for submissions) | M |
| 6 | Does it delete or overwrite user data in bulk? (e.g. a "reset all" action) | M |
| 7 | Is the request ambiguous in a way that one or two clarifying questions can't settle? | M |
| — | None of the above: filter, sort, export, label, layout, small bug fix, one-endpoint tweak | S |

**Verification**:
- The track and its one-line reason were stated before any code change
- A "yes" to any of questions 1–7 was not classified as S

---

## Rule TRACK-02: What Each Track Runs

### Track S — Direct
1. Read the affected code. If the request has more than one reasonable meaning, ask (at most 3 questions). Don't create question files.
2. Implement it, with tests in the same change.
3. Run the affected tests and type checks (`commands` in `.aidlc/aidlc-custom.json`). If a `restart` command is configured and server code changed, run it.
4. Update the functional spec (TRACK-05).
5. Report what changed, the test counts and which spec file(s) changed, then stop. Closing (simplify, review, commit) happens when the user asks for it (TRACK-07).

No requirements, design or plan documents. No approval gates except the clarifications in step 1.

### Track M — Light Design
1. **Requirements**: at minimal depth. Clarify with questions or a question file. Write a short `requirements.md` in the work item folder.
2. **Functional Design**: business rules, data model/migration and the permission matrix only. Wait for approval (standard 2-option message).
3. **Code Generation**: no separate plan approval. Implement, test and report.
4. Skip User Stories, Application Design, Units Generation, NFR and Infrastructure Design, unless the user asks for them.
5. Update the functional spec (TRACK-05) in the same change.

### Track L — Full AI-DLC
Run the workflow in `CLAUDE.md` unchanged, with every approval gate. Also update the functional spec (TRACK-05) in the same commit as the code.

**Verification**:
- Track S produced no `aidlc-docs/inception/` or `aidlc-docs/construction/plans/` files
- Track M had exactly one approval gate before code: Functional Design
- Track L followed every stage gate in `CLAUDE.md`

---

## Rule TRACK-03: Escalate, Never Downgrade Silently

**Rule**: If a question from the checklist turns into a "yes" mid-work, for example a Track S filter turns out to need a migration, stop. Tell the user the new track and why, and continue only after they agree. A track may move down (L→M, M→S) only when the user asks.

**Verification**:
- Every track change in the audit log has a user response recorded after it

---

## Rule TRACK-04: Recording

**Rule**:
- **audit.md**: one entry per user input, as usual. Set `**Context**:` to `Track S`, `Track M — <stage>` or `Track L — <stage>`.
- **aidlc-state.md** is an index:
  - Track S: one line per item under `## Track S Log`: `- YYYY-MM-DD — <title> — <commit sha or "uncommitted">`. Don't add a section per item and don't rewrite `Current Stage`.
  - Track M and Track L: one line under `## Work Items` linking to `aidlc-docs/work-items/NN-<slug>.md`, which holds the stage checklist and details. Keep `Current Stage` to a single short sentence.

**Verification**:
- Track S work did not add a work-item section to `aidlc-state.md`
- `Current Stage` is one sentence

---

## Rule TRACK-05: Spec Sync (All Tracks)

**Rule**: The functional spec (`specDir` in `.aidlc/aidlc-custom.json`, default `aidlc-docs/functional-spec/as-is/`) describes the system as it is now. A change that alters behaviour updates the matching spec file **in the same commit** as the code, whatever the track. Behaviour here means what a user sees or can do, a business rule, a permission, an API endpoint, a data field, an integration or a scheduled job. Track S is not exempt: it updates the spec instead of writing design documents.

Where each kind of change goes, for the default AS-IS layout (files `00`–`15`; adapt the table if your spec is organised differently):

| Change | File(s) |
|---|---|
| New or changed screen behaviour (filter, sort, export, button, column) | `07a`–`07d` screens for that module |
| Business rule (calculation, validation, eligibility, date cut-off) | `06-business-rule-catalogue.md` (new or edited `BR-` entry) |
| Permission or visibility | `03-actor-permission-matrix.md` |
| API endpoint added, removed, or its guard changed | `03-actor-permission-matrix.md` (endpoint table); also `02-module-screen-inventory.md` when no screen calls it. If the project generates OpenAPI from code, request/response shapes need no manual edit — keep request types typed so it stays accurate |
| Business process or workflow step | `04-business-process-catalogue.md`, `05-screen-flows.md` |
| Table or column | `08-data-dictionary.md` |
| Status or state change | `09-status-transition-matrix.md` |
| Report or dashboard | `10-reports-dashboards.md` |
| External system or scheduled job | `11-integrations.md` |
| Error or notification message | `12-errors-notifications.md` |
| New screen or menu item | `02-module-screen-inventory.md` |

- **Don't read whole spec files.** Find the row or section with `grep -n` on its ID (BR-, SCR-, CMP-, DD-, API-) or a keyword, read only those lines, and edit in place.
- Match the style of the file being edited: same heading levels and same ID scheme, with the next free number.
- Keep spec text in business terms. Write "the salary column is hidden unless the user has Finance access", not class or endpoint names.
- When a change resolves an open question in the gaps/questions file, mark it resolved.
- **Exempt**: refactors, tests, styling or layout tweaks with no new behaviour, dependency bumps, and `aidlc-docs/` changes. Write `spec: no behaviour change` in the commit message.
- Document exports (`.docx`/`.pdf`) are regenerated at release, or when the user asks, not on every commit.

**Enforced by** the `commit-msg` git hook installed by `/aidlc-custom:init`: a `feat`/`fix` commit that stages files under `sourceDirs` (tests excluded) must also stage a file under `specDir`, or carry `spec: no behaviour change`.

**Verification**:
- Every `feat` or `fix` commit that changes behaviour also touches the spec directory, or says why it's exempt

---

## Rule TRACK-06: Context Budget

**Rule**: Load only what the track needs. Every file read is paid for again on every following turn.

- **Track S:** do not load the stage rule files (`inception/*`, `construction/*`) or the full rule files of opted-in extensions (e.g. `security-baseline.md`, `resiliency-baseline.md`, `property-based-testing.md`). Check the change against this list instead, plus any `securityChecklist` items in `.aidlc/aidlc-custom.json`:
  - every new or changed endpoint has an authorization check
  - request bodies and query parameters are validated against a typed schema
  - no password, token, secret or personal data in logs or responses
  - errors go through the global error handler (no stack traces or SQL in responses)
  - tests cover the changed behaviour

  If an item can't be satisfied without design work, escalate to Track M (TRACK-03).
- **Track M/L:** load the extension and stage rule files as `CLAUDE.md` describes.
- **State:** `aidlc-state.md` is an index. Read it, not the files in `aidlc-docs/work-items/`, unless the user resumes or asks about that item.
- **Audit:** append with `cat >> aidlc-docs/audit.md <<'EOF'`; never read the whole file. It holds the current month only; earlier months are in `aidlc-docs/audit/YYYY-MM.md`.
- **Spec:** grep, then targeted reads (TRACK-05).

**Enforced by the aidlc-custom plugin hooks**:
- `guard_read.py` (PreToolUse, Read): denies reading the audit log, its archives, or a spec file over `specSmallBytes` without a line range of at most `maxReadLines` lines
- `session_start.py` (SessionStart): sets `core.hooksPath`, moves earlier-month audit entries into the archive, and warns when the state file passes `stateLimitBytes`
- Not enforceable by a hook: skipping extension rule files for Track S (a hook can't tell the track), so that part stays a rule

**Verification**:
- No extension or stage rule file was read for a Track S item
- `audit.md` was appended to, not read in full

---

## Rule TRACK-07: Closing a Change (Ship)

**Rule**: When the user says "ship", "close", "wrap up" or "commit this" (or runs `/aidlc-custom:ship`), close the change with the steps below, in order. Only step 4 waits for the user; run every other step without asking. The steps don't depend on any particular tool: where your tool has a dedicated simplify or code-review feature you may use it, but it must cover at least the checklist given here, and a missing feature never means skipping the step. aidlc-custom ships `simplify` and `code-review` skills (`SKILL.md` files) that run steps 2 and 3 in any tool that loads skills.

The user may say "push" (push after committing) or "no review" (skip steps 2–4, for docs-only or trivial changes). If `.aidlc/aidlc-custom.json` is missing, tell the user to set aidlc-custom up first and stop.

1. **Check the change.** `git status` and `git diff --stat`. If nothing changed, say so and stop. If unrelated changes are mixed in (stray untracked files, edits from another work item), list them and leave them out. Never `git add -A`; stage files by path. Note which parts of the code changed (for example server, client, or both).
2. **Simplify.** Go through the diff (not the whole codebase) and fix what you find:
   - code that duplicates a helper, component or utility the project already has: use the existing one
   - abstractions, parameters, options or layers with only one caller and no clear need
   - dead code: unused variables, imports, functions, branches, commented-out code
   - work done twice: repeated queries or API calls, a query inside a loop, recomputing a value that is already at hand
   - names or structure that don't match the surrounding code

   Don't change behaviour here. Note what you changed and what you left alone, for the log.
3. **Review.** Read the full diff, plus the code each change calls or is called by, and look for correctness bugs:
   - logic: wrong condition, inverted check, off-by-one, wrong variable, wrong order of operations
   - edge cases: null/undefined, empty list or string, zero, boundary dates and values, duplicates, concurrent requests
   - permissions and data exposure: every new or changed endpoint checks who may call it, users can't reach other users' data, nothing secret or personal goes to logs or responses
   - input validation and error handling: inputs validated, errors not swallowed, failures leave data consistent (transactions where several writes must succeed together)
   - data changes: migrations reversible, existing rows handled, no bulk delete or overwrite without a guard
   - callers and contracts: every caller of a changed function, API or type still works
   - tests: the changed behaviour is covered, including the failure paths
   - the TRACK-06 security list and any `securityChecklist` items

   Report only problems you can point to in the code, with a concrete case that goes wrong. Don't report style preferences.
4. **Choose fixes (the only stop).** If the review found nothing, say so and go on. Otherwise list the findings numbered, most severe first, one line each with `file:line`, and recommend which to fix (for example "fix 1–3; 4 is pre-existing"). Wait for the user to pick. Apply the chosen fixes, each behaviour change with a test. For real but out-of-scope findings not chosen, ask once whether to record them in the project's backlog file, if it has one.
5. **Verify.** Run the `commands.test` and `commands.typecheck` entries that apply to the changed code. If a migration was added, check that it applies and reverts on the dev database. If anything fails, fix it and run it again; if you can't fix it, stop, report the failing output and don't commit. If `commands.restart` is set and server code changed, run it and confirm the server started.
6. **Spec sync.** Compare the final diff with the spec (TRACK-05). If behaviour changed and the spec doesn't describe it yet, edit the matching file(s) now, locating rows with `grep -n`. If the change is exempt, the commit message carries `spec: no behaviour change`. Don't regenerate document exports.
7. **Log.** Append to the audit file with `cat >> <auditFile> <<'EOF'`; don't read or rewrite it. Add one entry per step that ran (Simplify, Code Review Fixes, Ship), in the project's audit format, with the user's raw input, an ISO timestamp and the test counts. Update the state file as TRACK-04 says.
8. **Commit.** Match the repo's commit style (`git log`). Typical shape: `<type>(<scope>): <summary in the user's terms>`, a short body on what the user sees, then a list of notable changes. Types: `feat`, `fix`, `refactor`, `docs`, `chore`; the scope is the page or module. Add `spec: no behaviour change` on its own line when step 6 found the change exempt. One commit per work item, including its `aidlc-docs/` updates. Commit on the current branch; push only when the user said "push".
9. **Report.** At most six lines: commit sha and subject, fixes applied, test counts, spec files updated (or "spec: no behaviour change"), backlog items added, and whether it was pushed.

**Verification**:
- Steps 2 and 3 ran (or the user said "no review"); neither was skipped for lack of a tool feature
- No commit was made with failing tests or type checks
- The commit stages files by path and includes the spec and `aidlc-docs/` updates

---

## Compliance Summary Format
When a Track M or Track L stage completes, add one line to the extension compliance summary:

```
aidlc-custom Work Tracks: Track <X> (reason) — compliant
```

Track S has no stage completion message, so it has no compliance summary.
