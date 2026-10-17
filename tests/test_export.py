"""Tests for tools/export_to_project.py. Run: python3 -m unittest discover tests"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT = os.path.join(ROOT, "tools", "export_to_project.py")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class ExportTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        subprocess.run(["git", "init", "-q", self.dir], check=True)

    def tearDown(self):
        shutil.rmtree(self.dir)

    def export(self, *args):
        return subprocess.run([sys.executable, EXPORT, self.dir, *args], capture_output=True, text=True)

    def path(self, *parts):
        return os.path.join(self.dir, *parts)

    def test_writes_layout_and_rewrites_plugin_references(self):
        self.assertEqual(self.export().returncode, 0)
        init = read(self.path(".claude", "skills", "aidlc-init", "SKILL.md"))
        self.assertIn("\nname: aidlc-init\n", init)
        self.assertIn("`.claude/aidlc-custom/templates/`", init)
        for name in ("aidlc-ship", "aidlc-simplify", "aidlc-code-review"):
            self.assertIn(f"\nname: {name}\n", read(self.path(".claude", "skills", name, "SKILL.md")))
        self.assertTrue(os.access(self.path(".claude", "aidlc-custom", "templates", "githooks", "commit-msg"), os.X_OK))
        for root, _, files in os.walk(self.path(".claude")):
            for name in files:
                text = read(os.path.join(root, name))
                self.assertNotIn("CLAUDE_PLUGIN_ROOT", text, name)
                self.assertNotIn("/aidlc-custom:", text, name)

    def test_hook_commands_point_at_project_copy(self):
        self.export()
        hooks = json.loads(read(self.path(".claude", "settings.json")))["hooks"]
        command = hooks["PreToolUse"][0]["hooks"][0]["command"]
        self.assertIn("${CLAUDE_PROJECT_DIR}/.claude/aidlc-custom/scripts/guard_read.py", command)
        script = command.split('"')[1].replace("${CLAUDE_PROJECT_DIR}", self.dir)
        self.assertTrue(os.path.isfile(script))

    def test_keeps_existing_settings_and_rerun_is_idempotent(self):
        os.makedirs(self.path(".claude"))
        with open(self.path(".claude", "settings.json"), "w") as f:
            json.dump({"permissions": {"allow": ["Bash(ls)"]}}, f)
        self.export()
        settings = json.loads(read(self.path(".claude", "settings.json")))
        self.assertEqual(settings["permissions"], {"allow": ["Bash(ls)"]})
        self.assertIn("Already up to date.", self.export().stdout)
        settings = json.loads(read(self.path(".claude", "settings.json")))
        self.assertEqual(len(settings["hooks"]["SessionStart"]), 1)

    def test_removes_files_dropped_from_plugin(self):
        self.export()
        stale = self.path(".claude", "aidlc-custom", "scripts", "old.py")
        with open(stale, "w") as f:
            f.write("x")
        self.export()
        self.assertFalse(os.path.exists(stale))

    def test_dry_run_writes_nothing(self):
        out = self.export("--dry-run").stdout
        self.assertIn("create  .claude/settings.json", out)
        self.assertFalse(os.path.exists(self.path(".claude")))

    def test_with_aidlc_installs_vendored_rules(self):
        self.assertEqual(self.export("--with-aidlc").returncode, 0)
        vendor = os.path.join(ROOT, "vendor", "aidlc-rules")
        self.assertEqual(read(self.path("CLAUDE.md")),
                         read(os.path.join(vendor, "aws-aidlc-rules", "core-workflow.md")))
        self.assertEqual(read(self.path(".aidlc-rule-details", "inception", "requirements-analysis.md")),
                         read(os.path.join(vendor, "aws-aidlc-rule-details", "inception", "requirements-analysis.md")))
        self.assertIn("Already up to date.", self.export("--with-aidlc").stdout)

    def test_with_aidlc_keeps_existing_rules_and_claude_md(self):
        os.makedirs(self.path(".kiro", "aws-aidlc-rule-details"))
        with open(self.path("CLAUDE.md"), "w") as f:
            f.write("# Team rules\n")
        out = self.export("--with-aidlc").stdout
        self.assertFalse(os.path.exists(self.path(".aidlc-rule-details")))
        self.assertEqual(read(self.path("CLAUDE.md")), "# Team rules\n")
        self.assertIn("note: AI-DLC rules already in .kiro/aws-aidlc-rule-details/", out)
        self.assertIn("note: CLAUDE.md exists", out)

    def test_without_flag_skips_aidlc(self):
        self.export()
        self.assertFalse(os.path.exists(self.path("CLAUDE.md")))
        self.assertFalse(os.path.exists(self.path(".aidlc-rule-details")))

    def test_invalid_settings_aborts(self):
        os.makedirs(self.path(".claude"))
        with open(self.path(".claude", "settings.json"), "w") as f:
            f.write("{ // comment\n}")
        self.assertNotEqual(self.export().returncode, 0)


if __name__ == "__main__":
    unittest.main()
