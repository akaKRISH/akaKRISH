"""Keep a reduced-motion snapshot of the real generated 3D contribution artwork."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
SVG = "http://www.w3.org/2000/svg"


def freeze(source, target):
    tree = ET.parse(source)
    for parent in tree.iter():
        for child in list(parent):
            if child.tag.rsplit("}", 1)[-1] in {"animate", "animateTransform", "animateMotion", "set"}:
                if child.get("attributeName") == "fill" and "fill" not in parent.attrib:
                    values = child.get("values", "").split(";")
                    assert values[0], "Generated contribution color animation has no values"
                    parent.set("fill", values[min(5, len(values) - 1)])
                parent.remove(child)
    ET.register_namespace("", SVG)
    tree.write(target, encoding="utf-8", xml_declaration=False)


if __name__ == "__main__":
    source = ROOT / "assets/3d/profile-night-rainbow.svg"
    freeze(source, source.with_name("profile-night-rainbow-static.svg"))
    print("Generated reduced-motion snapshot from the current real contribution field")
