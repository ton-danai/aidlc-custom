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
5. Report what changed, the test counts and which spec file(s) changed, then stop. Closing (simplify, review, commit) happens when the user runs `/aidlc-custom:ship` or asks for it.

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

## Compliance Summary Format
When a Track M or Track L stage completes, add one line to the extension compliance summary:

```
aidlc-custom Work Tracks: Track <X> (reason) — compliant
```

Track S has no stage completion message, so it has no compliance summary.
