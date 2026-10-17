"""Copy aidlc-custom into a project's .claude/ directory, without the plugin.

    python3 tools/export_to_project.py <project dir> [--with-aidlc] [--dry-run]

Layout written into the project:
  .claude/aidlc-custom/scripts/     hook scripts
  .claude/aidlc-custom/templates/   templates used by /aidlc-init
  .claude/aidlc-custom/tools/spec-docx/  Word export used by /aidlc-doc
  .claude/skills/aidlc-init/        was /aidlc-custom:init
  .claude/skills/aidlc-ship/        was /aidlc-custom:ship (likewise simplify, code-review, doc)
  .claude/settings.json             hooks merged in; other settings kept

With --with-aidlc, also the vendored AWS AI-DLC v1 rules, in AI-DLC's own
.aidlc/aidlc-rules/ layout:
  aws-aidlc-rule-details/           unless the project already has AI-DLC rules
  aws-aidlc-rules/core-workflow.md  read on demand for Track M/L, not every call
  CLAUDE.md                         the short team section, unless CLAUDE.md exists

Plugin paths and command names are rewritten on the way. Files under
.claude/aidlc-custom/ and the two skills are owned by this script and
overwritten on re-run; settings.json is merged and never loses entries.
After exporting, run /aidlc-init in the project as usual.
"""
import argparse
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = ".claude/aidlc-custom"
SKILLS = {"init": "aidlc-init", "ship": "aidlc-ship", "simplify": "aidlc-simplify", "code-review": "aidlc-code-review",
          "doc": "aidlc-doc"}
PARTS = ["scripts", "templates", os.path.join("tools", "spec-docx")]
SKIP_DIRS = {"__pycache__", "node_modules"}
AIDLC = os.path.join("vendor", "aidlc-rules")
WORKFLOW = ".aidlc/aidlc-rules/aws-aidlc-rules/core-workflow.md"
# Where AI-DLC v1 rule details may live, in the order /aidlc-init looks.
RULE_DIRS = [".aidlc/aidlc-rules/aws-aidlc-rule-details", ".aidlc-rule-details",
             ".kiro/aws-aidlc-rule-details", ".amazonq/aws-aidlc-rule-details"]

# Applied to every copied text file, in order.
REWRITES = [
    ("${CLAUDE_PLUGIN_ROOT}", DEST),
    *((f"/aidlc-custom:{old}", f"/{new}") for old, new in SKILLS.items()),
    ("The aidlc-custom plugin hooks", "The aidlc-custom hooks in `.claude/settings.json`"),
    ("the plugin's SessionStart hook", "the SessionStart hook in `.claude/settings.json`"),
    ("- teammates: install the plugin, and run", "- teammates: nothing to install (the hooks are committed in `.claude/`); run"),
]


def rewrite(text):
    for old, new in REWRITES:
        text = text.replace(old, new)
    return text


def plugin_hooks():
    with open(os.path.join(ROOT, "hooks", "hooks.json"), encoding="utf-8") as f:
        hooks = json.load(f)["hooks"]
    text = json.dumps(hooks).replace("${CLAUDE_PLUGIN_ROOT}", "${CLAUDE_PROJECT_DIR}/" + DEST)
    return json.loads(text)


def merge_hooks(settings, hooks):
    """Add each hook group unless a group with the same matcher already runs the same commands."""
    target = settings.setdefault("hooks", {})
    added = 0
    for event, groups in hooks.items():
        existing = target.setdefault(event, [])
        for group in groups:
            commands = {h["command"] for h in group["hooks"]}
            if not any(g.get("matcher") == group.get("matcher")
                       and commands <= {h.get("command") for h in g.get("hooks", [])}
                       for g in existing):
                existing.append(group)
                added += 1
    return added


class Export:
    def __init__(self, project, dry_run):
        self.project, self.dry_run, self.changes, self.notes = project, dry_run, [], []

    def write(self, rel, data, mode=None):
        path = os.path.join(self.project, rel)
        if os.path.exists(path):
            with open(path, "rb") as f:
                if f.read() == data:
                    return
            self.changes.append(f"update  {rel}")
        else:
            self.changes.append(f"create  {rel}")
        if self.dry_run:
            return
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        if mode:
            os.chmod(path, mode)

    def copy(self, src_rel, dest_rel, rename=None, raw=False):
        src = os.path.join(ROOT, src_rel)
        if raw:
            with open(src, "rb") as f:
                self.write(dest_rel, f.read())
            return
        with open(src, encoding="utf-8") as f:
            text = rewrite(f.read())
        if rename:
            text = text.replace(*rename, 1)
        self.write(dest_rel, text.encode("utf-8"), os.stat(src).st_mode & 0o777)

    def copy_tree(self, src_rel, dest_rel, raw=False):
        for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, src_rel)):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in sorted(filenames):
                if name.endswith(".pyc"):
                    continue
                rel = os.path.relpath(os.path.join(dirpath, name), os.path.join(ROOT, src_rel))
                self.copy(os.path.join(src_rel, rel), os.path.join(dest_rel, rel), raw=raw)

    def remove_stale(self, src_rel, dest_rel):
        """Delete files under dest_rel that no longer exist in the plugin."""
        dest = os.path.join(self.project, dest_rel)
        for dirpath, dirnames, filenames in os.walk(dest):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in filenames:
                rel = os.path.relpath(os.path.join(dirpath, name), dest)
                if not os.path.exists(os.path.join(ROOT, src_rel, rel)):
                    self.changes.append(f"remove  {os.path.join(dest_rel, rel)}")
                    if not self.dry_run:
                        os.remove(os.path.join(dirpath, name))

    def settings(self):
        rel = os.path.join(".claude", "settings.json")
        path = os.path.join(self.project, rel)
        settings = {}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                try:
                    settings = json.load(f)
                except json.JSONDecodeError as exc:
                    sys.exit(f"{rel} is not valid JSON ({exc}); fix it and re-run.")
        if merge_hooks(settings, plugin_hooks()):
            self.write(rel, (json.dumps(settings, indent=2) + "\n").encode("utf-8"))

    def aidlc(self):
        """Install the vendored AI-DLC v1 rules, never touching rules or a CLAUDE.md already there."""
        rules = next((d for d in RULE_DIRS if os.path.isdir(os.path.join(self.project, d))), None)
        if rules:
            self.notes.append(f"AI-DLC rules already in {rules}/; left as is.")
        else:
            rules = RULE_DIRS[0]
            self.copy_tree(os.path.join(AIDLC, "aws-aidlc-rule-details"), rules, raw=True)
        if not os.path.exists(os.path.join(self.project, WORKFLOW)):
            self.copy(os.path.join(AIDLC, "aws-aidlc-rules", "core-workflow.md"), WORKFLOW, raw=True)
        if os.path.exists(os.path.join(self.project, "CLAUDE.md")):
            self.notes.append("CLAUDE.md exists and was left as is; /aidlc-init adds the team section "
                              "and offers to move an inlined core workflow out of it.")
            return
        with open(os.path.join(ROOT, "templates", "claude-md-section.md"), encoding="utf-8") as f:
            section = rewrite(f.read()).replace("{{RULES}}", rules).replace("{{WORKFLOW}}", WORKFLOW)
        self.write("CLAUDE.md", f"# Project instructions\n\n{section}".encode("utf-8"))

    def run(self, with_aidlc=False):
        if with_aidlc:
            self.aidlc()
        for part in PARTS:
            self.copy_tree(part, os.path.join(DEST, part))
            self.remove_stale(part, os.path.join(DEST, part))
        for old, new in SKILLS.items():
            src = os.path.join("skills", old, "SKILL.md")
            dest = os.path.join(".claude", "skills", new, "SKILL.md")
            self.copy(src, dest, rename=(f"\nname: {old}\n", f"\nname: {new}\n"))
        self.settings()


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("project", help="target project directory (git repository root)")
    parser.add_argument("--with-aidlc", action="store_true",
                        help="also install the vendored AWS AI-DLC v1 rules and CLAUDE.md if missing")
    parser.add_argument("--dry-run", action="store_true", help="list changes without writing")
    args = parser.parse_args()

    project = os.path.abspath(args.project)
    if not os.path.isdir(os.path.join(project, ".git")):
        sys.exit(f"{project} is not a git repository root.")
    if project == ROOT:
        sys.exit("Target is the aidlc-custom repository itself.")

    export = Export(project, args.dry_run)
    export.run(args.with_aidlc)
    print("\n".join(export.changes) or "Already up to date.")
    for note in export.notes:
        print(f"note: {note}")
    if export.changes and not args.dry_run:
        print("\nNext: open Claude Code in the project and run /aidlc-init, then commit the new files.")


if __name__ == "__main__":
    main()
