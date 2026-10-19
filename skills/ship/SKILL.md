---
name: ship
description: Close out the current change in an aidlc-custom project — simplify, code review, apply the fixes the user picks, run the configured tests, sync the functional spec, log to aidlc-docs, and commit. Use when the user runs /aidlc-custom:ship or asks to finish, wrap up or ship the current work. Pass "push" to also push, "full" or "light" to force a review level, "no-review" to skip the review steps, "fix-all" to apply the recommended fixes without stopping.
---

# Ship

The closing sequence is rule TRACK-07 in the Work Tracks extension, so it works the same in any AI tool. This skill runs that rule in Claude Code.

1. Find `extensions/aidlc-custom/work-tracks/work-tracks.md` under the AI-DLC rule details directory, in this order: `.aidlc/aidlc-rules/aws-aidlc-rule-details/`, `.aidlc-rule-details/`, `.kiro/aws-aidlc-rule-details/`, `.amazonq/aws-aidlc-rule-details/`. If it isn't there, tell the user to run `/aidlc-custom:init` and stop.
2. Locate TRACK-07 with `grep -n "TRACK-0[5-7]"` and read from TRACK-07 to the next `## Rule` heading only. Read TRACK-05 the same way when you reach step 6.
3. Follow TRACK-07 step by step. Arguments map to its options: `push` → push after committing, `full` / `light` → that review level instead of choosing one in step 1, `no-review` → skip steps 2–4, `fix-all` → step 4 applies the recommended fixes without stopping.

Claude Code specifics:
- Step 1: state the review level before step 2. It decides how steps 2 and 3 run.
- Step 2, **light**: no skill and no agents. Go through the diff yourself once against the TRACK-07 simplify list and apply the fixes.
- Step 2, **full**: invoke the `simplify` skill (Claude Code's own if available, otherwise `/aidlc-custom:simplify`). When the code diff is under ~300 lines, ask it to use one agent for all angles. After Claude Code's own, check the diff against the TRACK-07 simplify list for anything it missed.
- Step 3: invoke the `code-review` skill on the working tree without `--fix` (Claude Code's own if available, otherwise `/aidlc-custom:code-review`). For **light**, pass `low` to Claude Code's own. After Claude Code's own, check the diff against the TRACK-07 review list for anything it missed.
- Step 8: end the commit message with the attribution lines the session asks for, if any.
