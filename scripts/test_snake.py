"""Regression checks for generated snake palettes and intact light/dark motion."""
from pathlib import Path
import shutil
import tempfile
import unittest

from validate_profile import ROOT, validate_snakes


class SnakeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        shutil.copytree(ROOT / "assets/snake", self.root / "assets/snake")
        self.dark = self.root / "assets/snake/github-contribution-grid-snake-dark.svg"

    def replace(self, old, new):
        text = self.dark.read_text(encoding="utf-8")
        self.assertIn(old, text)
        self.dark.write_text(text.replace(old, new, 1), encoding="utf-8")

    def test_checked_in_assets_are_valid(self):
        validate_snakes(self.root)

    def test_old_palette_is_rejected(self):
        self.replace("--c1:#8B5CF6", "--c1:#39d353")
        with self.assertRaisesRegex(AssertionError, "palette mismatch"):
            validate_snakes(self.root)

    def test_missing_animation_definition_is_rejected(self):
        self.replace("@keyframes s0{", "@keyframes missing{")
        with self.assertRaisesRegex(AssertionError, "animation references"):
            validate_snakes(self.root)

    def test_mismatched_geometry_is_rejected(self):
        self.replace('width="880"', 'width="881"')
        with self.assertRaisesRegex(AssertionError, "different grids or animations"):
            validate_snakes(self.root)

    def test_conflict_markers_are_rejected(self):
        self.replace("<svg", "<<<<<<< HEAD\n<svg")
        with self.assertRaisesRegex(AssertionError, "Conflict marker"):
            validate_snakes(self.root)

    def test_reduced_motion_override_is_required(self):
        self.replace("@media(prefers-reduced-motion:reduce){*{animation:none!important}}", "")
        with self.assertRaisesRegex(AssertionError, "reduced-motion override"):
            validate_snakes(self.root)


if __name__ == "__main__":
    unittest.main()
