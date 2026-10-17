---
name: doc
description: Write documentation on demand in an aidlc-custom project, separately from making a change — write or expand the AS-IS functional spec from the code, write a change note for work that skipped design documents (Track S), or export the spec to Word. Use when the user runs /aidlc-custom:doc or asks for the spec, documentation, a design/change note, or a .docx of the spec. Arguments: an area or path to document (default: what is missing), "change <ref>" for a change note, "docx" for the Word export.
---

# Doc

Documentation is kept out of Track S so small changes stay cheap; this skill produces it when someone asks. It writes documents only: never change source code here, and don't commit unless the user asks (then use the `docs` type; `spec: no behaviour change` is not needed).

If `.aidlc/aidlc-custom.json` is missing, tell the user to run `/aidlc-custom:init` first and stop. Read `specDir` from it (default `aidlc-docs/functional-spec/as-is`).

Pick the mode from the arguments:

| Argument | Mode |
|---|---|
| none, an area, module or path | **Spec** |
| `change <ref or range>` | **Change note** |
| `docx` | **Word export** |

## Spec

Write or expand the AS-IS functional spec: what the system does now, in business terms.

1. **Find the layout.** Find `extensions/aidlc-custom/work-tracks/work-tracks.md` under the AI-DLC rule details directory (`.aidlc/aidlc-rules/aws-aidlc-rule-details/`, `.aidlc-rule-details/`, `.kiro/aws-aidlc-rule-details/` or `.amazonq/aws-aidlc-rule-details/`), locate TRACK-05 with `grep -n` and read that rule only: its table maps each kind of behaviour to a spec file. If the spec already has files, follow their names, headings and ID schemes instead. A new spec also gets `00-README.md` (scope, how the files are organised, and a revision table `| Version | Date | Change |`, which the Word export reads) and a gaps/questions file.
2. **Scope.** With an area or path, document only that. Without one, list what the spec doesn't cover yet (screens, rules, endpoints, tables with no entry) and ask which to do, with a recommendation; for a short prototype spec, offer to expand it into the full layout.
3. **Read the code, not the docs.** Routes and screens, permission checks, validation and business rules, the data model and migrations, scheduled jobs and integrations, error messages. Note the commit (`git rev-parse --short HEAD`) as the baseline.
4. **Write.** Business terms only ("the salary column is hidden unless the user has Finance access", not class or endpoint names), one ID per entry (`BR-`, `SCR-`, `DD-`, `API-`, …) with the next free number. Don't guess: when the code is unclear, write what it does and add a question to the gaps file. Edit existing files in place: find the row with `grep -n` and read only that range (the read guard refuses whole reads of large spec files).
5. **Close.** Add a revision row to `00-README.md` with the date and baseline commit. Report the files written or changed, entry counts, and the open questions added.

## Change note

A short design record for a change that skipped design documents, so a reviewer or auditor can see what changed and why.

1. Read `git log` and `git diff` for the ref or range (default: `HEAD`). If the change touches more than one work item, ask which.
2. Write `aidlc-docs/changes/YYYY-MM-DD-<slug>.md`, at most one page:
   - **Intent**: what the user asked for, in one or two lines
   - **Behaviour**: what a user sees or can do now
   - **Rules, permissions, data**: each one added or changed, with its spec ID if it has one
   - **Tests**: what covers it
   - **Commits** and **spec files** changed
   - **Open points**: anything left undecided
3. If the spec doesn't describe this behaviour yet, say so and offer the Spec mode for it. Append one line to the audit log with a heredoc (`cat >> <auditFile> <<'EOF'`), not by reading it.

## Word export

1. Needs `node` and the build script at `${CLAUDE_PLUGIN_ROOT}/tools/spec-docx/build.mjs`. If `node_modules` is missing there, run `npm ci --prefix ${CLAUDE_PLUGIN_ROOT}/tools/spec-docx` (ask first: it downloads packages).
2. Run `node ${CLAUDE_PLUGIN_ROOT}/tools/spec-docx/build.mjs <specDir> <output> --project "<name>" --baseline "Baseline: commit <sha> (<date>)"`, with `--subtitle` if the README states what the system is. Default output: `aidlc-docs/exports/<project>-functional-spec-<date>.docx`. Take the project name from the spec README or the repository name.
3. Report the output path. The `.docx` is generated: don't commit it unless the user asks.
