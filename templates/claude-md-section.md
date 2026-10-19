## MANDATORY: Team workflow (aidlc-custom)
This project uses AWS AI-DLC v1 with aidlc-custom work tracks. Read rule files only when a step below says so, never up front.
- Work tracks: `{{RULES}}/extensions/aidlc-custom/work-tracks/work-tracks.md` (find a rule with `grep -n "TRACK-NN"`, read that rule only)
- Core AI-DLC workflow (Track M/L only): `{{WORKFLOW}}`

**1. Size every request first (TRACK-01).** Before changing code, state the track in one line with the reason. The user's "track S/M/L" or "full workflow" wins. Take the highest that applies:
- **L**: requirements still unclear after one round of questions, or waiting on decisions outside the team; several units of work that ship separately; infrastructure design. Size alone is not L.
- **M**: a new module, page group, external system or scheduled job; a migration; a permission or visibility change; a business rule the spec documents; bulk delete/overwrite of user data; ambiguity that 1–2 questions can't settle.
- **S**: everything else: filter, sort, export, label, layout, small bug fix, one-endpoint tweak, and small standalone apps or prototypes with no backend and no real user data (a tic-tac-toe game is S).

**2. Track S.** Don't read the core workflow, stage rules or extension rules, and don't show the AI-DLC welcome message.
1. Intent: 1–3 lines in chat (what, done when). Ask only if it has more than one reasonable meaning: at most 3 questions, in chat.
2. Code and tests in the same change (a bug fix stays where it broke, not in shared code); run `commands.test`/`commands.typecheck` from `.aidlc/aidlc-custom.json`.
3. Spec sync (below).
4. Report and stop. No requirements, plan or design files; no "shall I continue?" between steps.
If a size question above turns into a "yes" mid-work, stop and propose the new track (TRACK-03).

**3. Track M/L.** Read work-tracks.md TRACK-02 to TRACK-04, TRACK-08 and TRACK-10 (TRACK-09 when the user approves several gates at once), then the core workflow, and follow it with those trims. Track M has one approval before code. Ask who can see and who can change each new screen or endpoint; never assume an admin bypass. Extensions follow `extensions` in `.aidlc/aidlc-custom.json`: don't ask an opt-in question it already answers.

**4. Every track.**
- Spec sync (TRACK-05): a `feat`/`fix` that changes behaviour updates `specDir` in the same commit, or says `spec: no behaviour change`. The `commit-msg` hook enforces it. Locate spec rows with `grep -n`.
- Context (TRACK-06): append to the audit log with a heredoc, never read it whole; `aidlc-state.md` is an index.
- Closing (TRACK-07): `/aidlc-custom:ship` or "ship": review scaled to risk (full/light), the user picks fixes (each labelled new or pre-existing), test, spec, log, commit. Small requests that arrive together ship once.
- Fuller docs only on request: `/aidlc-custom:doc` (full spec, change note, Word export).
