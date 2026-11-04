#!/usr/bin/env python3
"""Render the two deterministic, self-contained README toolkit fields.

Run: python -B scripts/render_toolkit.py
The built-in checks run before either SVG is written. No dependencies required.
"""

from pathlib import Path
import xml.etree.ElementTree as ET

NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)
OUT = Path(__file__).resolve().parent.parent / "assets" / "profile"
INK, IVORY, MUTED = "#0B0A11", "#F5F0ED", "#BEB4CB"
VIOLET, ROSE, FLARE, GOLD = "#8B5CF6", "#F44984", "#FF865A", "#C9AE78"

GROUPS = (
    ("LANGUAGES", VIOLET, ("Python", "Java", "JavaScript", "TypeScript")),
    ("CREATIVE WEB", ROSE, ("React", "Tailwind CSS", "Vite", "Motion", "Three.js")),
    ("BACKEND", FLARE, ("Node.js", "Express", "FastAPI", "SQLAlchemy")),
    ("AI & VISION", GOLD, ("OpenCV", "MediaPipe", "Ollama")),
    ("SHIP & VERIFY", VIOLET, ("Git", "GitHub Actions", "Docker", "pytest")),
)

GLYPHS = (
    ("M-21-15 0-26 21-15 0-4Z", "M-21-1 0 10 21-1", "M-21 13 0 24 21 13"),
    ("M-24-8 0-22 24-8 0 6Z", "M-24 7 0 21 24 7", "M-24-8V7M24-8V7M0 6V21"),
    ("M-24-18H13L25-6V17H-12L-24 5Z", "M-24-18-12-6H25M-12-6V17", "M0 6H13"),
    ("M-23-6V-22H-7M7-22H23V-6M23 7V23H7M-7 23H-23V7", "M-12 0 0-12 12 0 0 12Z"),
    ("M-23 8-8 23 24-20", "M-23-10H-8M7 24H24V7"),
)


def add(parent, tag, value=None, **attributes):
    node = ET.SubElement(parent, f"{{{NS}}}{tag}", {
        key.rstrip("_").replace("_", "-"): str(val) for key, val in attributes.items()
    })
    node.text = value
    return node


def label(parent, x, y, value, size, color=IVORY, **attributes):
    return add(parent, "text", value, x=x, y=y, font_size=size, fill=color, **attributes)


def glyph(parent, kind, x, y, color, scale=1):
    group = add(parent, "g", transform=f"translate({x} {y}) scale({scale})", fill="none",
                stroke=color, stroke_width=1.8, stroke_linejoin="miter", aria_hidden="true")
    for path in GLYPHS[kind]:
        add(group, "path", d=path)


def traces(svg, mobile):
    art = add(svg, "g", aria_hidden="true", fill="none", stroke_linecap="round", stroke_linejoin="round")
    if mobile:
        routes = (
            "M80 212V227M80 296V396Q80 418 104 418H598Q622 418 622 438",
            "M622 488V580Q622 605 598 605H104Q80 605 80 627",
            "M80 677V773Q80 798 104 798H598Q622 798 622 818",
            "M622 868V960Q622 984 598 984H104Q80 984 80 1007",
            "M80 1056V1164L111 1195H234",
        )
        accent = "M80 296V396Q80 418 104 418H598Q622 418 622 438"
    else:
        routes = (
            "M76 176V187M76 246V401L105 430H335L362 403",
            "M337 216H370L402 184",
            "M691 211H844L896 263",
            "M492 396H548L580 428V453",
            "M954 455H879L850 484",
            "M1018 566L1080 498L1142 560L1082 620",
        )
        accent = "M691 211H844L896 263"
    for route in routes:
        add(art, "path", d=route, stroke=MUTED, stroke_opacity=0.17, stroke_width=1.4)
    add(art, "path", d=accent, stroke=VIOLET, stroke_opacity=0.55, stroke_width=2,
        stroke_dasharray="8 40", class_="field-trace")
    # A single cut plane gives the field an editorial signature, not a UI frame.
    if not mobile:
        add(art, "path", d="M1000 57H1143L1103 97H1048Z", stroke=VIOLET, stroke_opacity=0.65, stroke_width=1.5)
        add(art, "path", d="M1048 97 1026 119H1122L1143 97", stroke=ROSE, stroke_opacity=0.5, stroke_width=1.5)


def heading(svg, mobile):
    if mobile:
        title = label(svg, 48, 98, None, 72, font_weight=400)
        add(title, "tspan", "A working", x=48, y=98)
        add(title, "tspan", "toolkit.", x=48, y=185, font_family="Georgia,serif", font_style="italic", font_size=94)
    else:
        title = label(svg, 56, 108, "A working ", 78, font_weight=400)
        add(title, "tspan", "toolkit.", font_family="Georgia,serif", font_style="italic", font_size=86)


def group(svg, index, header, symbol, positions, mobile):
    name, color, technologies = GROUPS[index]
    content = add(svg, "g", role="group", aria_label=name, data_group=name)
    glyph(content, index, *symbol, color, scale=1.1 if mobile else 1)
    label(content, *header, name, 32 if mobile else 26, color=color, font_weight=600)
    for technology, (x, y) in zip(technologies, positions, strict=True):
        label(content, x, y, technology, 34 if mobile else 30, data_technology=technology)


def render(mobile=False):
    width, height = (720, 1250) if mobile else (1200, 680)
    variant = "mobile" if mobile else "desktop"
    svg = ET.Element(f"{{{NS}}}svg", {
        "width": str(width), "height": str(height), "viewBox": f"0 0 {width} {height}",
        "role": "img", "aria-labelledby": f"toolkit-{variant}-title toolkit-{variant}-desc",
        "font-family": "Arial,sans-serif", "letter-spacing": "0",
    })
    add(svg, "title", "A working toolkit.", id=f"toolkit-{variant}-title")
    add(svg, "desc", "Twenty technologies grouped into languages, creative web, backend, AI and vision, and shipping and verification. No proficiency ratings.", id=f"toolkit-{variant}-desc")
    add(svg, "style", ".field-trace{animation:field-drift 24s linear infinite}"
        "@keyframes field-drift{to{stroke-dashoffset:-192}}"
        "@media(prefers-reduced-motion:reduce){*{animation:none!important}}")
    add(svg, "rect", width=width, height=height, fill=INK)
    traces(svg, mobile)
    heading(svg, mobile)

    if mobile:
        layouts = (
            ((136, 270), (80, 258), ((136, 324), (390, 324), (136, 370), (390, 370))),
            ((48, 460), (622, 448), ((48, 514), (248, 514), (48, 560), (218, 560), (422, 560))),
            ((136, 650), (80, 638), ((136, 704), (390, 704), (136, 750), (390, 750))),
            ((48, 840), (622, 828), ((48, 894), (300, 894), (48, 940))),
            ((136, 1030), (80, 1018), ((136, 1084), (270, 1084), (136, 1130), (390, 1130))),
        )
    else:
        layouts = (
            ((116, 230), (76, 214), ((116, 282), (270, 282), (116, 326), (116, 370))),
            ((465, 218), (425, 202), ((465, 270), (633, 270), (465, 314), (610, 314), (465, 358))),
            ((116, 501), (76, 485), ((116, 553), (288, 553), (116, 597), (288, 597))),
            ((968, 290), (928, 274), ((968, 342), (968, 386), (968, 430))),
            ((640, 505), (600, 489), ((640, 557), (754, 557), (640, 601), (820, 601))),
        )
    for index, (header, symbol, positions) in enumerate(layouts):
        group(svg, index, header, symbol, positions, mobile)
    ET.indent(svg, space="  ")
    result = ET.tostring(svg, encoding="unicode") + "\n"
    validate(result, mobile)
    return result


def validate(source, mobile):
    """Small structural checks; actual font bounds are checked in a browser."""
    svg = ET.fromstring(source)
    expected = [technology for _, _, technologies in GROUPS for technology in technologies]
    actual = [node.get("data-technology") for node in svg.iter() if node.get("data-technology")]
    assert len(expected) == len(set(expected)) == 20
    assert actual == expected, "Missing or duplicated toolkit technology"
    minimum = 32 if mobile else 26
    for node in svg.iter():
        tag = node.tag.rsplit("}", 1)[-1]
        assert tag not in {"script", "foreignObject", "image"}
        assert not any(key.startswith("on") or key.endswith("href") for key in node.attrib)
        if "font-size" in node.attrib:
            assert float(node.get("font-size")) >= minimum
    assert "@media(prefers-reduced-motion:reduce){*{animation:none!important}}" in source
    assert svg.find(f"{{{NS}}}title") is not None and svg.find(f"{{{NS}}}desc") is not None


def main():
    assets = {"toolkit.svg": render(), "toolkit-mobile.svg": render(mobile=True)}
    OUT.mkdir(parents=True, exist_ok=True)
    for filename, source in assets.items():
        (OUT / filename).write_text(source, encoding="utf-8", newline="\n")
    print("Generated toolkit.svg (1200x680) and toolkit-mobile.svg (720x1250); 20 technologies in each.")


if __name__ == "__main__":
    main()
