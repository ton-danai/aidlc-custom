"""PreToolUse hook (matcher: Read): stop whole-file reads of the large AI-DLC
files (TRACK-06).

- the audit log and its monthly archives: append with a heredoc; to look
  something up, grep -n first and read a range.
- spec files in specDir larger than specSmallBytes: grep -n for the ID, then
  Read with offset/limit.
- the rule or opt-in file of an AI-DLC extension set to "off" in
  `extensions` (TRACK-08), whatever the range.

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


def disabled_extension(rel, cfg):
    """Name of the "off" extension this extensions/ file belongs to, if any."""
    parts = rel.split("/")
    if "extensions" not in parts[:-1] or not rel.endswith(".md"):
        return None
    name = parts[-1][: -len(".opt-in.md")] if rel.endswith(".opt-in.md") else parts[-1][:-3]
    return name if (cfg.get("extensions") or {}).get(name) == "off" else None


def main():
    try:
        data = json.load(sys.stdin)
        cfg = aidlc_config.load()
        if cfg is None:
            return
        tool_input = data.get("tool_input") or {}
        path = os.path.abspath(tool_input.get("file_path") or "")
        rel = os.path.relpath(path, cfg["_root"]).replace(os.sep, "/")
        off = disabled_extension(rel, cfg)
        if off:
            deny(f"TRACK-08: the {off} extension is \"off\" in .aidlc/aidlc-custom.json. Don't load it or ask "
                 "its opt-in question; record it as disabled in the state file's Extension Configuration.")
            return
        limit = tool_input.get("limit")
        max_lines = int(cfg["maxReadLines"])
        if isinstance(limit, (int, float)) and 0 < limit <= max_lines:
            return
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
