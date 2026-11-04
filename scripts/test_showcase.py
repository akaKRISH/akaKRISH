"""Protect the locked identity, visible real data, and new responsive artwork."""
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from freeze_contributions import freeze
from validate_profile import ROOT


class Visibility(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.visible = set()

    def handle_starttag(self, tag, attrs):
        if tag == "details":
            self.depth += 1
        if not self.depth:
            self.visible.update(v for k, v in attrs if k in {"src", "srcset"})

    def handle_endtag(self, tag):
        if tag == "details":
            self.depth -= 1


class ShowcaseTests(unittest.TestCase):
    def test_opening_and_gita_are_unchanged(self):
        # The user locked both sections and their original image bytes for this redesign.
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        opening = text.split("## Selected Experiments")[0]
        closing = text[text.index("<picture>", text.index("<br>")):]
        self.assertEqual(hashlib.sha256(opening.encode()).hexdigest(), "2c812d0e5dc1d4ac462fec0e091e5634c30d99ebfda125d0f3749a2a06ebb88d")
        self.assertEqual(hashlib.sha256(closing.encode()).hexdigest(), "6c75bd08b6d0469e18783ba3f71ae9cf158d287385df3ccedc6a193a5048f6ca")
        for name, expected in {
            "portrait.jpg": "21720fe5e11773a0bcb8af16ec5bd97e52a010ac6e7935f85e4c64a973a2e09f",
            "hero-static.png": "6db018ec03e1d67ec18366cecc210353042328c59f9d9d024dc020b1e78e7ccd",
            "hero-assembly.gif": "261d4df3ab609156edac0c0c6d987fc4691e2b76d5c742c61622b06e24075a8c",
            "closing.png": "56c1f3a75d4c84f979a18d7943cc59a99bf23ac11b6e5e562fbca1f7beb49e51",
            "closing-mobile.png": "159d904e635a7acfb16f7affb72f4145409bede8ddb3e3fe0b7a7e022402c64e",
        }.items():
            self.assertEqual(hashlib.sha256((ROOT / "assets/profile" / name).read_bytes()).hexdigest(), expected, name)

    def test_contributions_and_screenshots_are_not_hidden(self):
        parser = Visibility()
        parser.feed((ROOT / "README.md").read_text(encoding="utf-8"))
        for asset in ["assets/snake/github-contribution-grid-snake-dark.svg", "assets/snake/github-contribution-grid-snake.svg", "assets/3d/profile-night-rainbow.svg", "assets/3d/profile-night-rainbow-static.svg", "assets/activity/github-overview.svg", "assets/activity/github-languages.svg", "assets/profile/gdgoc-preview.jpg", "assets/profile/bloodbond-preview.jpg"]:
            self.assertIn(asset, parser.visible)

    def test_toolkit_includes_every_real_technology_in_both_layouts(self):
        technologies = ["Python", "Java", "JavaScript", "TypeScript", "React", "Tailwind CSS", "Vite", "Motion", "Three.js", "Node.js", "Express", "FastAPI", "SQLAlchemy", "OpenCV", "MediaPipe", "Ollama", "Git", "GitHub Actions", "Docker", "pytest"]
        for name in ["toolkit.svg", "toolkit-mobile.svg"]:
            text = " ".join(ET.parse(ROOT / "assets/profile" / name).getroot().itertext())
            for technology in technologies:
                self.assertIn(technology, text, name)

    def test_responsive_artwork_is_self_contained_and_motion_safe(self):
        for path in (ROOT / "assets/profile").glob("*.svg"):
            tree = ET.parse(path)
            source = path.read_text(encoding="utf-8")
            self.assertLess(path.stat().st_size, 60_000)
            self.assertIn("prefers-reduced-motion", source)
            self.assertIsNotNone(tree.find("{http://www.w3.org/2000/svg}title"))
            for element in tree.iter():
                self.assertNotIn(element.tag.rsplit("}", 1)[-1], {"script", "foreignObject"})
                self.assertFalse(any(k.startswith("on") or k.endswith("href") for k in element.attrib))

    def test_static_contributions_retain_geometry_and_visible_color(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "animated.svg"
            target = Path(directory) / "still.svg"
            source.write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect height="42"><animate attributeName="fill" values="red;violet"/><animate attributeName="height" values="1;42"/></rect><rect fill="ivory" width="7"/></svg>', encoding="utf-8")
            freeze(source, target)
            tree = ET.parse(target)
            rectangles = list(tree.getroot())
            self.assertEqual(rectangles[0].attrib, {"height": "42", "fill": "violet"})
            self.assertEqual(rectangles[1].attrib, {"fill": "ivory", "width": "7"})
            self.assertEqual(len(rectangles[0]), 0)
        static = ET.parse(ROOT / "assets/3d/profile-night-rainbow-static.svg")
        self.assertFalse(any(e.tag.rsplit("}", 1)[-1].startswith("animate") for e in static.iter()))

    def test_static_field_matches_the_current_generated_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "field.svg"
            freeze(ROOT / "assets/3d/profile-night-rainbow.svg", target)
            self.assertEqual(target.read_bytes(), (ROOT / "assets/3d/profile-night-rainbow-static.svg").read_bytes())


if __name__ == "__main__":
    unittest.main()
