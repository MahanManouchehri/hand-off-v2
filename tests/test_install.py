import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
INSTALL = ROOT / 'setup' / 'install.py'
FRAG = (ROOT / 'setup' / 'AGENTS.fragment.md').read_text()


def run_install(home, *args):
    return subprocess.run([sys.executable, str(INSTALL), '--home', str(home), *args], text=True, capture_output=True)


class InstallerTests(unittest.TestCase):
    def test_fresh_and_idempotent_and_other_skill_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Path(tmp)
            other = h / '.agents/skills/compatible-response/SKILL.md'
            other.parent.mkdir(parents=True)
            other.write_text('existing user skill\n')
            before = other.read_bytes()
            dry = run_install(h, '--dry-run')
            self.assertEqual(dry.returncode, 0, dry.stderr)
            self.assertFalse((h / '.codex').exists())
            self.assertEqual(run_install(h).returncode, 0)
            self.assertEqual(run_install(h).returncode, 0)
            agents = (h / '.codex/AGENTS.md').read_text()
            self.assertEqual(agents.count('<!-- BEGIN HAND-OFF AUTO ROUTING -->'), 1)
            self.assertEqual(run_install(h, '--verify').returncode, 0)
            self.assertEqual(other.read_bytes(), before)
            self.assertTrue((h / '.agents/skills/hand-off/assets/llm-context.template.md').exists())

    def test_override_and_legacy_marker_preserves_both_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Path(tmp)
            d = h / '.codex'
            d.mkdir()
            old = '<!-- BEGIN HAND-OFF AUTO ROUTING -->\nold behavior\n<!-- END HAND-OFF AUTO ROUTING -->'
            (d / 'AGENTS.md').write_text('CompatibleResponse global agreement\n\n' + old + '\n')
            (d / 'AGENTS.override.md').write_text('My override rules\n')
            self.assertEqual(run_install(h).returncode, 0)
            a = (d / 'AGENTS.md').read_text()
            o = (d / 'AGENTS.override.md').read_text()
            self.assertIn('CompatibleResponse global agreement', a)
            self.assertIn('My override rules', o)
            self.assertNotIn('old behavior', a)
            self.assertIn('Choose skill mode', o)
            self.assertEqual(run_install(h, '--verify').returncode, 0)

    def test_malformed_marker_is_safe_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Path(tmp)
            d = h / '.codex'
            d.mkdir()
            f = d / 'AGENTS.md'
            f.write_text('Other stuff\n<!-- BEGIN HAND-OFF AUTO ROUTING -->\nrest must survive')
            initial = f.read_bytes()
            proc = run_install(h)
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(f.read_bytes(), initial)
            self.assertFalse((h / '.agents/skills/hand-off').exists())

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Path(tmp)
            d = h / '.codex'
            d.mkdir()
            victim = h / 'victim.txt'
            victim.write_text('unchanged')
            (d / 'AGENTS.md').symlink_to(victim)
            self.assertNotEqual(run_install(h).returncode, 0)
            self.assertEqual(victim.read_text(), 'unchanged')


if __name__ == '__main__':
    unittest.main()
