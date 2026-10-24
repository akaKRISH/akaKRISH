# PROJECT_PROGRESS.md — RURU Profile Overhaul

Adds the RURU.EXE character-dossier experience and rebuilds the profile README around it.
All work in this document is by THIS overhaul only; everything else in the repo predates it.
Every completion state below is evidence-backed (files exist on disk and/or were verified in a browser).

## Milestone 0 — Audit (complete)

Initial state at `main` @ `7d33f13` (working tree clean at start):

- `README.md` — profile README: laser ASCII hero GIF, `/currently-building`, GestureOS flagship,
  selected work, stack, activity cards, 3D contribution field, contribution snake.
- `interactive/index.html` — Pages viewer: single flat SVG (3D contribution graph) on a CSS-3D
  card. Drag rotate ±55°, wheel zoom, Esc reset. Works; kept and linked to the new dossier.
- `.github/workflows/pages.yml` — deploys the repo root to GitHub Pages on pushes touching
  `interactive/**` or `assets/3d/**`. Root-relative source; project page lives under `/akaKRISH/`.
- `.github/workflows/{3d-contrib,activity}.yml` — daily scheduled regenerators that commit
  `assets/3d` and `assets/activity`. Untouched by this overhaul.
- Asset weights: laser GIF 4.6 MB, 3D SVG 188 KB, activity SVGs, snake 36 KB.

Link verification performed earlier via GitHub API (HTTP status):

- OK 200 — `akaKRISH/GestureOS`, `akaKRISH/RuruOS`, `akaKRISH/ruru-protocol`,
  `akaKRISH/GROUNDWATER_PREDICITION_SYSTEM`, `akaKRISH/agent-evaluator-hackathon`,
  `akaKRISH/LeetCode`, and now `akaKRISH/arceus-core` (public release, Oct 2026).
- 404 — CivicOS: does not exist publicly → excluded from the README.

PFP source reference (`scripts/pfp_source.jpg`): self portrait, centered head-and-torso,
reading glasses, dark curly hair, short beard, brown/white checked shirt, holding a phone,
framed by a split neon ring (cyan left, warm gold right). That ring is the signature motif.

## Milestone 1 — Creative direction (complete)

- **Concept:** `RURU.EXE — PLAYER DOSSIER 001`. The portrait is a capture-rig dossier: the
  character stands inside the split portal ring; HUD chips read out class/domain/status/motif.
- **Palette (from the PFP, disciplined):** near-black `#05070b`, midnight `#0b1220`,
  graphite `#1d2a40`, electric cyan `#78c4ff`, ultraviolet `#9b8cff`, single warm accent
  `#ffca7a`. No third hue.
- **Rendering approach:** a hand-drawn **layered 2.5D vector character** — NOT a fake
  "3D model" claim, no animation engine, no added runtime dependency.
- Motion: pointer tilt with per-plane response, gentle cursor sheen, ENGAGE/DISENGAGE toggle,
  keyboard arrows at the card, Esc reset, `prefers-reduced-motion` fallback.

## Milestone 2 — Character experience (complete, verified)

- `character/ruru.svg` — canonical layered character source. Seven depth planes, each an SVG
  group carrying `data-plane`: `layer-portal` (−150), `layer-halo` (−80), `layer-body` (0),
  `layer-face` (+34), `layer-hair` (+58), `layer-glasses` (+86), `layer-hud` (+120).
  Portrait echoes the real PFP: curly silhouette, glasses with cyan data reflections,
  checked-shirt collar, split neon ring. Rebuilt twice from a weaker first draft after
  rendered review (scattered curl dots → unified hair mass; goofy grin → calm expression;
  floating bracelet/kite shirt → clean torso).
- `interactive/character/index.html` — dossier page (vanilla HTML/CSS/JS, zero dependencies):
  two-column stage, card with 3D perspective tilt, frost/sheen/scanline layers at their own
  translateZ, keyboard-engage, touch tilt, reduced-motion handling.
- `interactive/character/art.html` — generated embed of the inline SVG with the per-plane
  parallax client (receives `{rx, ry}` tilt via postMessage; each `data-plane` layer shifts
  at its own amplitude — real multi-plane depth inside the iframe).
- `scripts/embed_art.py` — regenerates `art.html` from `character/ruru.svg` so the two never
  drift. Run after any SVG edit.

## Milestone 3 — Profile README (complete)

- New hierarchy: character dossier poster as hero (`character/ruru.svg`, rendered by GitHub)
  → interactive CTA badges → currently building → flagship GestureOS → selected work
  (CivicOS dropped; ARCEUS added; links real) → stack grouped by purpose → engineering
  journey → "this repository is itself an artifact" lab section → 3D field + activity snake
  → footer nav.
- Two-layer experience per GitHub constraints: the README stays assets-only; all JS runs on
  the Pages deployment `https://akakrish.github.io/akaKRISH/interactive/character/`.
- Removed: laser-print GIF as hero (kept nothing broken), duplicate CTA rows, badge spam.

## Milestone 4 — Workflow (complete)

- `.github/workflows/pages.yml` — added `character/**` and `README.md` path triggers so art
  or README changes republish Pages. Existing deploy model unchanged (repo root, GitHub App).

## Milestone 5 — Verification (complete — browser via puppeteer-core + system Chrome)

- Dossier page: 0 console errors / 0 failed requests; ENGAGE toggle flips `aria-pressed`;
  inner HUD layer visibly shifts under tilt (parallax works cross-origin via postMessage).
- Viewports 390 / 768 / 1024 / 1440: horizontal overflow 0px at every width; screenshots in
  `shots/` (local only, not committed). Mobile header reordered so the brand precedes nav.
- Reduced motion: entry animation and tilt suppressed; card rests flat and composed.
- Contribution-field page (`interactive/`) still loads and links to `character/`.
- `character/ruru.svg` parses as valid XML.

## Local-only artifacts (not committed)

`node_modules/`, `package.json`, `package-lock.json` (puppeteer-core harness), `shot.js`,
`verify.js`, `shots/*`, `character/preview.html`, `character/preview.png`.

## Commands for future modification

```bash
# regenerate the interactive embed after editing character/ruru.svg
python scripts/embed_art.py

# serve locally, then open http://localhost:8765/interactive/character/
python -m http.server 8765 -d .
```
