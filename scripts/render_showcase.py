"""Build self-contained, responsive README artwork. Never renders the locked hero."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets/profile"
INK, PAPER, MUTED = "#0B0A11", "#F5F0ED", "#BEB4CB"
VIOLET, ROSE, ORANGE, GOLD = "#8B5CF6", "#F44984", "#FF865A", "#C9AE78"
REDUCE = "@media(prefers-reduced-motion:reduce){*{animation:none!important}}"


def node(parent, tag, content=None, **attrs):
    element = ET.SubElement(parent, tag, {k.replace('_', '-'): str(v) for k, v in attrs.items()})
    element.text = content
    return element


def text(parent, x, y, content, size=28, color=PAPER, **attrs):
    return node(parent, "text", content, x=x, y=y, font_size=size, fill=color, **attrs)


def line(parent, x1, y1, x2, y2, color="#39313F", **attrs):
    return node(parent, "line", x1=x1, y1=y1, x2=x2, y2=y2, stroke=color, **attrs)


def path(parent, d, color, **attrs):
    return node(parent, "path", **({"d": d, "stroke": color, "fill": "none", "stroke_width": 3} | attrs))


def canvas(name, mobile, height, title):
    width = 720 if mobile else 1200
    svg = ET.Element("svg", {"xmlns": "http://www.w3.org/2000/svg", "width": str(width), "height": str(height), "viewBox": f"0 0 {width} {height}", "role": "img", "aria-labelledby": "title desc"})
    node(svg, "title", title, id="title")
    node(svg, "desc", "Original editorial artwork for Rudransh Singh's GitHub profile. Project diagrams are conceptual studies, not application screenshots.", id="desc")
    node(svg, "style", "text{font-family:Arial,Helvetica,sans-serif;letter-spacing:0}.serif{font-family:Georgia,serif;font-style:italic}.trace{stroke-dasharray:16 24;animation:flow 8s linear infinite}.drift{animation:drift 7s ease-in-out infinite}.scan{animation:scan 9s ease-in-out infinite}@keyframes flow{to{stroke-dashoffset:-160}}@keyframes drift{50%{transform:translateY(-10px)}}@keyframes scan{50%{transform:translateX(90px)}}" + REDUCE)
    node(svg, "rect", width=width, height=height, fill=INK)
    return svg, OUT / f"{name}{'-mobile' if mobile else ''}.svg"


def save(svg, target):
    ET.indent(svg, space="  ")
    ET.ElementTree(svg).write(target, encoding="utf-8", xml_declaration=False)
    print(target.relative_to(ROOT))


def star(parent, x, y, color, scale=1):
    group = node(parent, "g", transform=f"translate({x} {y}) scale({scale})", stroke=color, stroke_width=3)
    for dx, dy in [(18, 0), (0, 18), (13, 13), (13, -13)]:
        line(group, -dx, -dy, dx, dy, color, stroke_width=3)


def section(name, mobile):
    height = 330 if mobile else 260
    title = "Selected experiments" if name == "selected-work" else "Contribution field"
    svg, target = canvas(name, mobile, height, title)
    accent = ROSE if name == "selected-work" else VIOLET
    text(svg, 48, 52, "01   SELECTED EXPERIMENTS" if name == "selected-work" else "03   THE WORK, OVER TIME", 25, accent)
    if mobile:
        words = ["Curiosity,", "made tangible."] if name == "selected-work" else ["Contribution", "field."]
        for i, word in enumerate(words):
            text(svg, 44, 137 + 79 * i, word, 70, PAPER if i == 0 else ORANGE if name == "selected-work" else "#B89AF5", **({"class": "serif"} if i else {}))
        line(svg, 48, 282, 670, 282)
        path(svg, "M48 282H670", accent, **{"class": "trace"})
    else:
        text(svg, 45, 145, "Curiosity," if name == "selected-work" else "Contribution", 91)
        text(svg, 510 if name == "selected-work" else 648, 145, "made tangible." if name == "selected-work" else "field.", 84, ORANGE if name == "selected-work" else "#B89AF5", **{"class": "serif"})
        text(svg, 50, 210, "Intelligent systems. Real interfaces. Five things I had to try." if name == "selected-work" else "Real contributions, seen from a different angle.", 25, MUTED)
        star(svg, 1110, 205, accent, .8)
        line(svg, 48, 246, 1152, 246)
        path(svg, "M48 246H1152", accent, **{"class": "trace"})
    save(svg, target)


def project_base(name, mobile, number, category, words, accent, caption):
    height = 710 if mobile else 440
    svg, target = canvas(name + "-study", mobile, height, f"{name} project study")
    width = 720 if mobile else 1200
    text(svg, 40, 49, number, 26, accent)
    text(svg, 100, 49, category, 24, MUTED)
    for i, word in enumerate(words):
        text(svg, 37, (125 if mobile else 150) + (66 if mobile else 78) * i, word, 63 if mobile else 76, PAPER if i == 0 else accent, **({"class": "serif"} if i else {}))
    text(svg, 42, height - 30, caption, 25 if mobile else 23, MUTED)
    line(svg, 40, height - 72, width - 40, height - 72)
    return svg, target


def gesture(mobile):
    svg, target = project_base("gestureos", mobile, "01", "VISION TO INTERACTION", ["Hands.", "On."], ROSE, "TRACK  >  SMOOTH  >  ACT")
    group = node(svg, "g", transform="translate(170 267) scale(1.08)" if mobile else "translate(680 40) scale(.93)")
    fingers = [[(124, 271), (80, 222), (51, 187), (28, 157)], [(124, 271), (111, 173), (109, 111), (109, 59), (109, 19)], [(124, 271), (157, 166), (161, 92), (163, 41), (164, 2)], [(124, 271), (202, 181), (218, 115), (226, 68), (229, 38)], [(124, 271), (244, 211), (278, 161), (298, 127), (310, 104)]]
    for finger in fingers:
        path(group, "M" + " L".join(f"{x} {y}" for x, y in finger), ROSE, stroke_linecap="round", stroke_linejoin="round")
        for x, y in finger:
            node(group, "rect", x=x-4, y=y-4, width=8, height=8, fill=PAPER)
    path(group, "M28 157L109 19L164 2L229 38L310 104", "#4C2D42", stroke_dasharray="5 8")
    line(group, 0, 321, 350, 321, "#4C2D42")
    path(group, "M0 321H350", ORANGE, **{"class": "trace"})
    for x, y, dx, dy in [(0, 0, 22, 22), (350, 0, -22, 22), (0, 340, 22, -22), (350, 340, -22, -22)]:
        path(group, f"M{x+dx} {y}H{x}V{y+dy}", VIOLET)
    if not mobile:
        text(svg, 44, 313, "A webcam. A hand. A different interface.", 25, MUTED)
        star(svg, 497, 142, ORANGE)
    save(svg, target)


def arceus(mobile):
    svg, target = project_base("arceus", mobile, "02", "LOCAL-FIRST AI RESEARCH", ["Research,", "with receipts."], "#B89AF5", "RETRIEVE  >  VERIFY  >  REASON")
    group = node(svg, "g", transform="translate(58 300)" if mobile else "translate(690 55)")
    if mobile:
        points = [(65, 150), (300, 150), (535, 150)]
    else:
        points = [(42, 170), (190, 65), (340, 170)]
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        path(group, f"M{x1} {y1}L{x2} {y2}", "#493C60", stroke_width=4)
        path(group, f"M{x1} {y1}L{x2} {y2}", VIOLET, **{"class": "trace"})
    for i, (x, y) in enumerate(points):
        node(group, "rect", x=x-37, y=y-37, width=74, height=74, rx=4, fill=INK, stroke=[VIOLET, ROSE, GOLD][i], stroke_width=3)
        if i == 0:
            for off in [-10, 0, 10]:
                line(group, x-13, y+off, x+13, y+off, PAPER, stroke_width=3)
        elif i == 1:
            path(group, f"M{x-15} {y}l10 10 20 -23", PAPER)
        else:
            star(group, x, y, PAPER, .75)
        text(group, x, y+79, ["source", "check", "reason"][i], 29 if mobile else 24, MUTED, text_anchor="middle")
    if not mobile:
        text(svg, 43, 313, "An agent that has to show its working.", 25, MUTED)
    save(svg, target)


def patchpilot(mobile):
    svg, target = project_base("patchpilot", mobile, "03", "REVIEWABLE CODE REPAIR", ["Try the repair.", "Keep the original."], ORANGE, "COPY  >  TEST  >  REVIEW")
    group = node(svg, "g", transform="translate(70 300)" if mobile else "translate(725 77) scale(.75)")
    for y, label, color in [(50, "original", MUTED), (235, "working copy", ORANGE)]:
        line(group, 25, y, 545, y, "#453841", stroke_width=3)
        path(group, f"M25 {y}H545", color, **{"class": "trace"} if y == 235 else {})
        for x in [55, 275, 500]:
            node(group, "rect", x=x-8, y=y-8, width=16, height=16, fill=INK, stroke=color, stroke_width=3)
        text(group, 25, y-30, label, 29, color)
    path(group, "M55 50V235M500 235V50", ROSE, stroke_dasharray="4 8")
    path(group, "M253 236l15 15 33 -37", PAPER, stroke_linejoin="round")
    if not mobile:
        text(svg, 43, 313, "A disposable copy. A patch you can inspect.", 25, MUTED)
    save(svg, target)


def personal(mobile):
    svg, target = canvas("offscreen", mobile, 530 if mobile else 310, "Away from the editor")
    text(svg, 44, 53, "04   AWAY FROM THE EDITOR", 25, ROSE)
    for i, word in enumerate(["Fast feet.", "Restless mind."]):
        text(svg, 40, 134+76*i, word, 69, PAPER if i == 0 else ORANGE, **({"class": "serif"} if i else {}))
    group = node(svg, "g", transform="translate(40 285) scale(.87)" if mobile else "translate(760 26) scale(.9)")
    for i, color in enumerate([ORANGE, ROSE, VIOLET]):
        path(group, f"M20 {40+i*40}H270Q360 {40+i*40} 360 {130+i*40}V270", color, stroke_width=3)
    path(group, "M20 80H270Q360 80 360 170V270", PAPER, **{"class": "trace"})
    star(group, 70, 230, GOLD)
    save(svg, target)


def quiet():
    svg, target = canvas("quiet", False, 100, "A quieter thought to close")
    line(svg, 48, 50, 480, 50, "#68583F")
    star(svg, 600, 50, GOLD, .5)
    line(svg, 720, 50, 1152, 50, "#68583F")
    save(svg, target)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for mobile in (False, True):
        section("selected-work", mobile)
        section("contribution-field", mobile)
        gesture(mobile)
        arceus(mobile)
        patchpilot(mobile)
        personal(mobile)
    quiet()
