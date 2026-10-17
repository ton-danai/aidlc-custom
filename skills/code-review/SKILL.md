---
name: code-review
description: Review the current change in an aidlc-custom project for correctness bugs, permission and data-exposure gaps, and missing tests, verify each finding against the code, and report them ranked by severity. Use when the user runs /aidlc-custom:code-review, asks for a code review of the change, or TRACK-07 step 3 runs. Pass a git ref (e.g. main) to review everything since that ref; pass --fix to apply the fixes after the review; pass deep for a slower, wider review.
---

# Code review

Finds bugs: code that does the wrong thing for some input, user or state. Style and simplification are out of scope (that is `simplify`).

Arguments:
- a git ref: review `git diff <ref>...HEAD` plus the uncommitted change; without one, review the uncommitted change (`git diff HEAD` plus related untracked files)
- `--fix`: after reporting, apply the fixes for every finding and run the tests
- `deep`: also read the callers' callers and the tests of every touched module, and run a second pass over each category

## 1. Scope and context

- Collect the diff. If it is empty, say so and stop.
- For each changed function, type, endpoint or query: find its callers and what it calls (`grep -n` on the name), and read those parts. A change that is right on its own can break a caller.
- Read the tests that cover the changed code, if any.

## 2. Load the checklist

Find `extensions/aidlc-custom/work-tracks/work-tracks.md` under the AI-DLC rule details directory (`.aidlc/aidlc-rules/aws-aidlc-rule-details/`, `.aidlc-rule-details/`, `.kiro/aws-aidlc-rule-details/` or `.amazonq/aws-aidlc-rule-details/`), locate TRACK-06 and TRACK-07 with `grep -n`, and read the TRACK-07 step 3 list and the TRACK-06 security list only. Add any `securityChecklist` items from `.aidlc/aidlc-custom.json`. If the file isn't there, tell the user to run `/aidlc-custom:init` and stop.

## 3. Find candidates

Go through the diff once per checklist category, not once overall: a single read misses most bugs. For each category, write down every place that might be wrong, with the reason.

## 4. Verify each candidate

A candidate becomes a finding only if you can show it fails:
- Trace the code path from an entry point (request, screen action, job) to the line.
- Name a concrete case: the input, user or state, and the wrong result (wrong value, crash, data leak, data loss, unauthorised access).
- Check that nothing upstream already prevents it (validation, a guard, a type, a database constraint).
- Mark whether the diff introduced it or it was already there.

Drop candidates you can't make concrete. Don't report "consider adding…", style, naming, or performance unless it causes a failure users would notice.

## 5. Report

Numbered, most severe first:

```
1. [high] path/to/file.ts:42 — <what is wrong>
   Fails when: <concrete case and wrong result>
   Fix: <one line>
```

Severity: **high** — security, permission or data exposure, data loss or corruption, wrong result in normal use; **medium** — wrong result or crash in an edge case; **low** — a minor wrong result with an easy workaround. Tag pre-existing findings `(pre-existing)`.

If nothing survived verification, say "No findings" and list the categories checked.

## 6. Fix (only with `--fix`)

Without `--fix`, stop after the report; in TRACK-07 the user picks which findings to fix.

With `--fix`: apply each fix with a test that would have caught it, run the `commands.test` and `commands.typecheck` entries from `.aidlc/aidlc-custom.json`, and report which findings were fixed and the test result. If a fix needs a design decision, don't apply it; say what the choice is.
