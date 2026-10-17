"""Tests for the aidlc-custom hooks. Run: python3 -m unittest discover tests"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
COMMIT_MSG = os.path.join(ROOT, "templates", "githooks", "commit-msg")

CONFIG = {
    "sourceDirs": ["backend/src", "frontend/src"],
    "specDir": "aidlc-docs/functional-spec/as-is",
    "auditFile": "aidlc-docs/audit.md",
    "auditArchiveDir": "aidlc-docs/audit",
    "stateFile": "aidlc-docs/aidlc-state.md",
    "gitHooksPath": ".githooks",
    "stateLimitBytes": 15000,
    "extensions": {"resiliency-baseline": "off", "security-baseline": "on"},
}


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


class Project(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.env = {**os.environ, "CLAUDE_PROJECT_DIR": self.dir}
        subprocess.run(["git", "init", "-q", self.dir], check=True)
        write(os.path.join(self.dir, ".aidlc", "aidlc-custom.json"), json.dumps(CONFIG))

    def tearDown(self):
        shutil.rmtree(self.dir)

    def git(self, *args):
        return subprocess.run(["git", "-C", self.dir, *args], check=True, capture_output=True, text=True)


class CommitMsgTest(Project):
    def check(self, message):
        msg = os.path.join(self.dir, "MSG")
        write(msg, message)
        return subprocess.run([sys.executable, COMMIT_MSG, msg], cwd=self.dir, capture_output=True, text=True).returncode

    def stage(self, rel, text="x"):
        write(os.path.join(self.dir, rel), text)
        self.git("add", rel)

    def test_feat_with_code_only_is_blocked(self):
        self.stage("backend/src/a.ts")
        self.assertEqual(self.check("feat(x): add thing"), 1)

    def test_fix_with_code_only_is_blocked(self):
        self.stage("backend/src/a.ts")
        self.assertEqual(self.check("fix: bug"), 1)

    def test_other_types_pass(self):
        self.stage("backend/src/a.ts")
        self.assertEqual(self.check("chore: deps"), 0)

    def test_exemption_line_passes(self):
        self.stage("backend/src/a.ts")
        self.assertEqual(self.check("feat(ui): colour\n\nspec: no behaviour change"), 0)

    def test_non_conventional_subject_passes(self):
        self.stage("backend/src/a.ts")
        self.assertEqual(self.check("feature flag stuff"), 0)

    def test_code_with_spec_passes(self):
        self.stage("backend/src/a.ts")
        self.stage("aidlc-docs/functional-spec/as-is/06.md")
        self.assertEqual(self.check("feat(x): add thing"), 0)

    def test_test_files_only_pass(self):
        self.stage("backend/src/a.spec.ts")
        self.assertEqual(self.check("feat(x): tests"), 0)

    def test_no_config_passes(self):
        os.remove(os.path.join(self.dir, ".aidlc", "aidlc-custom.json"))
        self.stage("backend/src/a.ts")
        self.assertEqual(self.check("feat(x): add thing"), 0)


class GuardReadTest(Project):
    def setUp(self):
        super().setUp()
        write(os.path.join(self.dir, "aidlc-docs", "audit.md"), "# log\n")
        write(os.path.join(self.dir, "aidlc-docs", "audit", "2026-01.md"), "# old\n")
        spec = os.path.join(self.dir, "aidlc-docs", "functional-spec", "as-is")
        write(os.path.join(spec, "06-big.md"), "x" * 20000)
        write(os.path.join(spec, "07-small.md"), "small\n")
        write(os.path.join(self.dir, "backend", "src", "main.ts"), "code\n")

    def decide(self, payload):
        out = subprocess.run([sys.executable, "-I", os.path.join(SCRIPTS, "guard_read.py")], input=payload,
                             env=self.env, capture_output=True, text=True).stdout.strip()
        return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out else "allow"

    def read(self, rel, **extra):
        return self.decide(json.dumps({"tool_input": {"file_path": os.path.join(self.dir, rel), **extra}}))

    def test_cases(self):
        ext = ".aidlc/aidlc-rules/aws-aidlc-rule-details/extensions"
        cases = [
            ("aidlc-docs/audit.md", {}, "deny"),
            ("aidlc-docs/audit.md", {"offset": 10, "limit": 50}, "allow"),
            ("aidlc-docs/audit/2026-01.md", {}, "deny"),
            ("aidlc-docs/functional-spec/as-is/06-big.md", {}, "deny"),
            ("aidlc-docs/functional-spec/as-is/06-big.md", {"limit": 2000}, "deny"),
            ("aidlc-docs/functional-spec/as-is/06-big.md", {"offset": 1, "limit": 120}, "allow"),
            ("aidlc-docs/functional-spec/as-is/07-small.md", {}, "allow"),
            ("backend/src/main.ts", {}, "allow"),
            (f"{ext}/resiliency/baseline/resiliency-baseline.md", {}, "deny"),
            (f"{ext}/resiliency/baseline/resiliency-baseline.md", {"offset": 1, "limit": 50}, "deny"),
            (f"{ext}/resiliency/baseline/resiliency-baseline.opt-in.md", {}, "deny"),
            (f"{ext}/security/baseline/security-baseline.md", {}, "allow"),
            (f"{ext}/testing/property-based/property-based-testing.md", {}, "allow"),
        ]
        for rel, extra, expected in cases:
            with self.subTest(rel=rel, extra=extra):
                self.assertEqual(self.read(rel, **extra), expected)

    def test_bad_json_fails_open(self):
        self.assertEqual(self.decide("not json"), "allow")

    def test_no_config_allows_everything(self):
        os.remove(os.path.join(self.dir, ".aidlc", "aidlc-custom.json"))
        self.assertEqual(self.read("aidlc-docs/audit.md"), "allow")


class SessionStartTest(Project):
    def run_hook(self):
        out = subprocess.run([sys.executable, "-I", os.path.join(SCRIPTS, "session_start.py")], input="{}",
                             env=self.env, capture_output=True, text=True).stdout.strip()
        return json.loads(out)["systemMessage"] if out else ""

    def test_rotates_earlier_months_and_is_idempotent(self):
        audit = os.path.join(self.dir, "aidlc-docs", "audit.md")
        write(audit, "# AI-DLC Audit Log\n\n> header\n\n"
                     "## Old A\n**Timestamp**: 2001-08-31T10:00:00Z\n**User Input**: \"a\"\n\n---\n\n"
                     "## Old B\n**Timestamp**: 2001-09-30T10:00:00Z\n**User Input**: \"b\"\n\n---\n\n"
                     "## New\n**Timestamp**: 2999-01-01T01:00:00Z\n**User Input**: \"c\"\n\n---\n")
        write(os.path.join(self.dir, "aidlc-docs", "audit", "2001-09.md"),
              "# AI-DLC Audit Log — 2001-09 (archive)\n\n## Earlier\n**Timestamp**: 2001-09-01T00:00:00Z\n")
        msg = self.run_hook()
        self.assertIn("Rotated 2 audit entries", msg)
        kept = read(audit)
        self.assertIn("> header", kept)
        self.assertIn("## New", kept)
        self.assertNotIn("## Old", kept)
        sep = read(os.path.join(self.dir, "aidlc-docs", "audit", "2001-09.md"))
        self.assertLess(sep.index("## Earlier"), sep.index("## Old B"))
        self.assertIn("## Old A", read(os.path.join(self.dir, "aidlc-docs", "audit", "2001-08.md")))
        self.assertNotIn("Rotated", self.run_hook())

    def test_warns_on_large_state(self):
        write(os.path.join(self.dir, "aidlc-docs", "aidlc-state.md"), "x" * 16000)
        self.assertIn("aidlc-state.md is 16 KB", self.run_hook())

    def test_sets_hooks_path_when_unset(self):
        os.makedirs(os.path.join(self.dir, ".githooks"))
        self.assertIn("core.hooksPath", self.run_hook())
        self.assertEqual(self.git("config", "--get", "core.hooksPath").stdout.strip(), ".githooks")

    def test_no_config_does_nothing(self):
        os.remove(os.path.join(self.dir, ".aidlc", "aidlc-custom.json"))
        write(os.path.join(self.dir, "aidlc-docs", "aidlc-state.md"), "x" * 16000)
        self.assertEqual(self.run_hook(), "")


if __name__ == "__main__":
    unittest.main()
