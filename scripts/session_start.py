"""SessionStart hook: keep the AI-DLC bookkeeping files small.

1. Point git at the project's hook directory (core.hooksPath) when unset, so
   the spec-sync commit-msg hook is active.
2. Rotate the audit log: entries stamped in an earlier month move to
   <auditArchiveDir>/YYYY-MM.md (appended if that file exists); the header
   and current-month entries stay.
3. Warn when the state file grows past stateLimitBytes.

Does nothing unless the project has .aidlc/aidlc-custom.json. Prints a JSON
hook result only when something happened; never fails the session.
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aidlc_config  # noqa: E402

MONTH = re.compile(r"^\*\*Timestamp\*\*:\s*(\d{4}-\d{2})")


def ensure_hooks_path(cfg):
    root, hooks = cfg["_root"], cfg["gitHooksPath"]
    if not os.path.isdir(os.path.join(root, hooks)):
        return None
    current = subprocess.run(["git", "-C", root, "config", "--get", "core.hooksPath"],
                             capture_output=True, text=True).stdout.strip()
    if current:
        return None
    subprocess.run(["git", "-C", root, "config", "core.hooksPath", hooks], check=True)
    return f"Set git core.hooksPath to {hooks}."


def rotate_audit(cfg, current_month):
    audit = aidlc_config.project_path(cfg, "auditFile")
    archive_dir = aidlc_config.project_path(cfg, "auditArchiveDir")
    if not os.path.exists(audit):
        return None
    lines = open(audit, encoding="utf-8").read().split("\n")
    heads = [i for i, line in enumerate(lines) if line.startswith("## ")]
    if not heads:
        return None
    header, keep, moved = lines[: heads[0]], [], {}
    for k, start in enumerate(heads):
        end = heads[k + 1] if k + 1 < len(heads) else len(lines)
        block = lines[start:end]
        month = next((m.group(1) for line in block if (m := MONTH.match(line))), None)
        if month and month < current_month:
            moved.setdefault(month, []).append(block)
        else:
            keep.append(block)
    if not moved:
        return None
    os.makedirs(archive_dir, exist_ok=True)
    for month, blocks in sorted(moved.items()):
        path = os.path.join(archive_dir, f"{month}.md")
        body = "\n".join("\n".join(b) for b in blocks).rstrip() + "\n"
        if os.path.exists(path):
            with open(path, "a", encoding="utf-8") as f:
                f.write("\n" + body)
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"# AI-DLC Audit Log — {month} (archive)\n\n" + body)
    rest = "\n".join("\n".join(b) for b in keep).rstrip()
    with open(audit, "w", encoding="utf-8") as f:
        f.write("\n".join(header).rstrip() + "\n\n" + (rest + "\n" if rest else ""))
    count = sum(len(b) for b in moved.values())
    return (f"Rotated {count} audit entr{'y' if count == 1 else 'ies'} from {', '.join(sorted(moved))} "
            f"into {cfg['auditArchiveDir']}/.")


def check_state(cfg):
    state = aidlc_config.project_path(cfg, "stateFile")
    limit = int(cfg["stateLimitBytes"])
    if os.path.exists(state) and os.path.getsize(state) > limit:
        kb = round(os.path.getsize(state) / 1000)
        return (f"{cfg['stateFile']} is {kb} KB (limit {limit // 1000} KB). It is an index: move work-item "
                "details into their own files and keep one line per item (TRACK-04, TRACK-06).")
    return None


def main():
    try:
        cfg = aidlc_config.load()
    except Exception as exc:
        print(json.dumps({"systemMessage": f"aidlc-custom: cannot read .aidlc/aidlc-custom.json: {exc}"}))
        return
    if cfg is None:
        return
    notes = []
    now = datetime.now(timezone.utc).strftime("%Y-%m")
    for step in (lambda: ensure_hooks_path(cfg), lambda: rotate_audit(cfg, now), lambda: check_state(cfg)):
        try:
            note = step()
        except Exception as exc:  # never block a session over bookkeeping
            note = f"aidlc-custom session-start step failed: {exc}"
        if note:
            notes.append(note)
    if notes:
        text = " ".join(notes)
        print(json.dumps({
            "systemMessage": text,
            "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text},
        }))


if __name__ == "__main__":
    main()
    sys.exit(0)
