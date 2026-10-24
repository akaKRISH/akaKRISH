"""Regenerate interactive/character/art.html from character/ruru.svg.

Embeds the character SVG inline with a minimal parallax client: the dossier
page (index.html) sends {rx, ry, live} tilt angles via postMessage and each
SVG layer group (data-plane) shifts at its own amplitude, producing real
multi-plane depth inside the card iframe.

Local dev:  python scripts/embed_art.py
Then reload interactive/character/index.html (no server needed; iframe uses
an HTML file so no fetch/XHR is involved).
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SVG_PATH = ROOT / "character" / "ruru.svg"
OUT_PATH = ROOT / "interactive" / "character" / "art.html"

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RURU character art (embedded)</title>
<style>
  html,body{margin:0;height:100%;background:transparent;overflow:hidden}
  svg{width:100%;height:100%;display:block}
  g[data-plane]{transition:transform .18s ease-out;will-change:transform}
  @media (prefers-reduced-motion: reduce){g[data-plane]{transition:none}}
</style>
</head>
<body>
{SVG}
<script>
(function(){
  var MAX_SHIFT = 9; /* px at full tilt for the frontmost plane */
  var layers = [].slice.call(document.querySelectorAll('g[data-plane]'));
  var raf = 0, rx = 0, ry = 0;
  function clamp(v, m){ return Math.max(-m, Math.min(m, v)); }
  function render(){
    raf = 0;
    for (var i = 0; i < layers.length; i++){
      var p = parseFloat(layers[i].getAttribute('data-plane')) || 0;
      /* foreground planes (positive) shift with the tilt; deep planes counter it */
      var f = p / 120 * MAX_SHIFT;
      var x = clamp(-ry / 12 * f, 12), y = clamp(rx / 12 * f, 10);
      layers[i].style.transform = 'translate(' + x.toFixed(2) + 'px,' + y.toFixed(2) + 'px)';
    }
  }
  window.addEventListener('message', function(e){
    var d = e.data || {};
    rx = +d.rx || 0; ry = +d.ry || 0;
    if (!raf) raf = requestAnimationFrame(render);
  });
  render();
})();
</script>
</body>
</html>
"""


def main() -> None:
    svg = SVG_PATH.read_text(encoding="utf-8")
    OUT_PATH.write_text(TEMPLATE.replace("{SVG}", svg), encoding="utf-8")
    print(f"wrote {OUT_PATH.relative_to(ROOT)} ({len(svg)} bytes of SVG)")


if __name__ == "__main__":
    main()
