"""Offline checks for README paths, safe SVGs, and the one-shot portrait asset."""
from html.parser import HTMLParser
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parent.parent


class Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = set()
        self.images = 0
        self.pictures = 0

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        assert tag not in {"script", "iframe", "canvas", "style"}, f"Unsupported README element: {tag}"
        assert not any(key.startswith("on") for key in attrs), "Inline event handler in README"
        if tag == "img":
            self.images += 1
            assert attrs.get("alt", "").strip(), "An image has no alternative text"
        if tag == "picture":
            self.pictures += 1
        for key in ("src", "srcset", "href"):
            value = attrs.get(key, "")
            if value and not value.startswith(("https://", "http://", "#")):
                assert "," not in value, "Explicit source variants are required"
                self.paths.add(value)


def validate():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assets = Assets()
    assets.feed(text)
    for path in re.findall(r"\]\(([^)]+)\)", text):
        if not path.startswith(("https://", "http://", "#")):
            assets.paths.add(path)
    for path in assets.paths:
        target = (ROOT / path).resolve()
        assert target.is_relative_to(ROOT), f"Path escapes repository: {path}"
        assert target.is_file(), f"Missing relative asset: {path}"
    assert assets.pictures >= 3, "Missing motion/theme/mobile source variants"
    assert "prefers-reduced-motion: reduce" in text
    assert not re.search(r"^#{1,6}\s+/|RURU\s*//|visitor.counter", text, re.M | re.I)
    assert text.count("# Rudransh Singh") == 1
    assert "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।" in text
    assert "मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि॥" in text
    assert not re.search(r"\]\([^)]*(?:resume|cv)\b", text, re.I), "No resume asset was supplied"

    for path in assets.paths:
        if not path.endswith(".svg"):
            continue
        tree = ET.parse(ROOT / path)
        for element in tree.iter():
            tag = element.tag.rsplit("}", 1)[-1]
            assert tag not in {"script", "foreignObject"}, f"Unsafe SVG element: {path}"
            assert not any(key.startswith("on") for key in element.attrib), f"SVG event handler: {path}"
            for key, value in element.attrib.items():
                if key.rsplit("}", 1)[-1] == "href":
                    assert not value.startswith(("http:", "https:")), f"SVG external dependency: {path}"

    gif_path = ROOT / "assets/profile/hero-assembly.gif"
    assert gif_path.stat().st_size < 3_000_000, "Hero GIF exceeds the 3 MB budget"
    with Image.open(gif_path) as gif, Image.open(ROOT / "assets/profile/hero-static.png") as still:
        assert gif.format == "GIF" and gif.size == (1200, 560)
        assert "loop" not in gif.info, "GIF must play once, not loop forever"
        assert 30 <= gif.n_frames <= 80
        first = gif.convert("RGB")
        delta = ImageStat.Stat(ImageChops.difference(first, still.convert("RGB"))).mean
        assert max(delta) < 7, "First GIF frame is not the complete static identity"
        total = 0
        changed = False
        for index in range(gif.n_frames):
            gif.seek(index)
            total += gif.info.get("duration", 0)
            if index == gif.n_frames // 3:
                changed = ImageChops.difference(first, gif.convert("RGB")).getbbox() is not None
        assert changed, "Portrait GIF has no moving frames"
        assert 4000 <= total <= 7500, f"Unexpected duration: {total}"
        assert ImageChops.difference(first, gif.convert("RGB")).getbbox() is None, "Animation does not finish on the complete identity"
    for path, dimensions in [("closing.png", (1200, 620)), ("closing-mobile.png", (780, 850))]:
        with Image.open(ROOT / "assets/profile" / path) as image:
            assert image.size == dimensions
    print(f"PASS: {len(assets.paths)} relative assets; safe SVGs; {assets.images} image alternatives; one-shot GIF and complete first/final frames")


if __name__ == "__main__":
    validate()
