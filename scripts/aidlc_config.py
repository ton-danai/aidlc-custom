"""Per-project configuration for the aidlc-custom hooks.

A project opts in by having `.aidlc/aidlc-custom.json` (created by
/aidlc-custom:init). Without it every hook does nothing, so installing the
plugin user-wide never affects other repositories.
"""
import json
import os

CONFIG_PATH = os.path.join(".aidlc", "aidlc-custom.json")

DEFAULTS = {
    "auditFile": "aidlc-docs/audit.md",
    "auditArchiveDir": "aidlc-docs/audit",
    "stateFile": "aidlc-docs/aidlc-state.md",
    "stateLimitBytes": 15000,
    "specDir": "aidlc-docs/functional-spec/as-is",
    "specSmallBytes": 12000,
    "maxReadLines": 400,
    "gitHooksPath": ".githooks",
}


def project_root():
    return os.path.abspath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def load(root=None):
    """Return the merged config, or None when the project has not opted in."""
    root = root or project_root()
    path = os.path.join(root, CONFIG_PATH)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {**DEFAULTS, **data, "_root": root}


def project_path(cfg, key):
    return os.path.join(cfg["_root"], cfg[key])
