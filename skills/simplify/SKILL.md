---
name: simplify
description: Simplify the current change in an aidlc-custom project without changing behaviour — reuse existing helpers, drop needless abstraction and dead code, remove repeated work — then apply the fixes and re-run the tests. Use when the user runs /aidlc-custom:simplify, asks to simplify or clean up the change, or TRACK-07 step 2 runs. Pass a git ref (e.g. main) to simplify everything since that ref instead of the uncommitted change.
---

# Simplify

Quality only: this does not hunt for bugs (that is `code-review`). Every fix keeps behaviour exactly as it is.

## 1. Scope

- No argument: the uncommitted change, `git diff HEAD` plus untracked files that belong to it (`git status --short`).
- A ref argument: `git diff <ref>...HEAD` plus the uncommitted change.
- If the scope is empty, say so and stop. Work only on the lines in scope; code outside it is read for context, not edited, except to reuse it.

## 2. Load the checklist

Find `extensions/aidlc-custom/work-tracks/work-tracks.md` under the AI-DLC rule details directory (`.aidlc/aidlc-rules/aws-aidlc-rule-details/`, `.aidlc-rule-details/`, `.kiro/aws-aidlc-rule-details/` or `.amazonq/aws-aidlc-rule-details/`), locate TRACK-07 with `grep -n`, and read its step 2 list only. That list is what to look for. If the file isn't there, tell the user to run `/aidlc-custom:init` and stop.

## 3. Look

For each changed file:
- Read each changed hunk with enough surrounding code to see what it does.
- **Reuse:** for each new function, component, query or block of logic, search the project for something that already does it (`grep` for similar names, the same API call, the same SQL table, the same regex or date format). Check the project's shared folders (`utils`, `lib`, `common`, `shared`, `hooks`, `components`) first.
- **Abstraction:** for each new function, parameter, option, interface or layer, count its callers. One caller and no stated need means inline it.
- **Dead code:** unused imports, variables, parameters, exports, branches that can't be reached, commented-out code, leftover debug logging.
- **Repeated work:** the same query or API call made twice, a query or request inside a loop that one batched call could replace, a value recomputed when it is already in hand.
- **Fit:** names, error handling and structure that differ from the code around it.

## 4. Fix

- Apply each fix directly. Keep each one small and separate so it can be reverted alone.
- Don't change public APIs, response shapes, database schemas, or anything another module or client depends on. Don't add dependencies. Don't reformat lines you aren't otherwise changing.
- If a fix is a judgement call (two reasonable designs), leave it and list it as skipped with the reason.

## 5. Check

Run the `commands.test` and `commands.typecheck` entries in `.aidlc/aidlc-custom.json` that apply to the changed code. If one fails because of a simplify fix, revert that fix and list it as skipped. Never leave the tree failing.

## 6. Report

A short list: each fix applied (`file:line` and one line on what changed), each candidate skipped and why, and the test result. TRACK-07 step 7 copies this into the audit log.
