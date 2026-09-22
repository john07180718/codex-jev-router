from __future__ import annotations
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from tools.install import BEGIN, END, edit_block, run

class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)
        self.codex = self.home / "profile"
        self.codex.mkdir()
        self.rules = self.codex / "AGENTS.md"
        self.rules.write_text("Keep my original rule.\n", encoding="utf-8")
        self.patch = patch("pathlib.Path.home", return_value=self.home)
        self.env = patch.dict(os.environ, {"CODEX_HOME": str(self.codex)})
        self.patch.start(); self.env.start()
    def tearDown(self):
        self.env.stop(); self.patch.stop(); self.temp.cleanup()
    def invoke(self, *args):
        with redirect_stdout(io.StringIO()):
            return run(list(args))
    def test_preview_has_no_changes(self):
        self.assertEqual(self.invoke("--global-rule"), 0)
        self.assertEqual(self.rules.read_text(), "Keep my original rule.\n")
        self.assertFalse((self.home / ".agents").exists())
    def test_install_preserves_rules_and_packages_runtime(self):
        self.assertEqual(self.invoke("--global-rule", "--apply"), 0)
        content = self.rules.read_text()
        self.assertIn("Keep my original rule.", content)
        self.assertEqual(content.count(BEGIN), 1)
        self.assertTrue((self.home / ".agents/skills/jev-assist/scripts/jev_workflow/cli.py").exists())
    def test_install_is_idempotent(self):
        self.invoke("--global-rule", "--apply")
        before = self.rules.read_bytes()
        self.assertEqual(self.invoke("--global-rule", "--apply"), 0)
        self.assertEqual(self.rules.read_bytes(), before)
    def test_uninstall_preserves_later_unrelated_changes(self):
        self.invoke("--global-rule", "--apply")
        self.rules.write_text(self.rules.read_text() + "Later custom rule.\n")
        self.assertEqual(self.invoke("--uninstall", "--apply"), 0)
        self.assertIn("Later custom rule.", self.rules.read_text())
        self.assertIn("Keep my original rule.", self.rules.read_text())
        self.assertNotIn(BEGIN, self.rules.read_text())
    def test_nonempty_override_is_selected(self):
        override = self.codex / "AGENTS.override.md"
        override.write_text("Override rule.\n")
        self.invoke("--global-rule", "--apply")
        self.assertIn(BEGIN, override.read_text())
        self.assertNotIn(BEGIN, self.rules.read_text())
    def test_empty_override_is_skipped(self):
        (self.codex / "AGENTS.override.md").write_text("")
        self.invoke("--global-rule", "--apply")
        self.assertIn(BEGIN, self.rules.read_text())
    def test_modified_skill_not_overwritten(self):
        self.invoke("--apply")
        skill = self.home / ".agents/skills/jev-assist/SKILL.md"
        skill.write_text(skill.read_text() + "User customization\n")
        self.assertEqual(self.invoke("--apply"), 2)
        self.assertIn("User customization", skill.read_text())
    def test_malformed_managed_block_fails(self):
        with self.assertRaises(ValueError):
            edit_block("x " + BEGIN, "new")

if __name__ == "__main__":
    unittest.main()
