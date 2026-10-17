"""PreToolUse hook (matcher: Read): stop whole-file reads of the large AI-DLC
files (TRACK-06).

- the audit log and its monthly archives: append with a heredoc; to look
  something up, grep -n first and read a range.
- spec files in specDir larger than specSmallBytes: grep -n for the ID, then
  Read with offset/limit.

A read with a limit of at most maxReadLines is allowed. Anything else passes.
Does nothing unless the project has .aidlc/aidlc-custom.json; on any error the
read is allowed (fail open).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aidlc_config  # noqa: E402


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}))


def under(rel, directory):
    directory = directory.strip("/")
    return rel == directory or rel.startswith(directory + "/")


def main():
    try:
        data = json.load(sys.stdin)
        cfg = aidlc_config.load()
        if cfg is None:
            return
        tool_input = data.get("tool_input") or {}
        path = os.path.abspath(tool_input.get("file_path") or "")
        limit = tool_input.get("limit")
        max_lines = int(cfg["maxReadLines"])
        if isinstance(limit, (int, float)) and 0 < limit <= max_lines:
            return
        rel = os.path.relpath(path, cfg["_root"]).replace(os.sep, "/")
        if rel == cfg["auditFile"].strip("/") or under(rel, cfg["auditArchiveDir"]):
            deny("TRACK-06: don't read the audit log whole. To add an entry, append with "
                 f"`cat >> {cfg['auditFile']} <<'EOF' ... EOF`. To look something up, `grep -n` first, "
                 f"then Read with offset and a limit of at most {max_lines} lines.")
        elif (under(rel, cfg["specDir"]) and rel.endswith(".md") and os.path.exists(path)
              and os.path.getsize(path) > int(cfg["specSmallBytes"])):
            deny("TRACK-05/06: this spec file is large. `grep -n` for the rule/screen/field ID or a keyword, "
                 f"then Read with offset and a limit of at most {max_lines} lines.")
    except Exception:
        return  # fail open: a broken guard must not block work


if __name__ == "__main__":
    main()
    sys.exit(0)
