# Profile Artwork and Verification

This work changes the GitHub profile README and its supporting assets only. It does not add an application, JavaScript to the README, or another website. `interactive/`, `character/ruru.svg`, the existing Pages deployment, and the 3D contribution generator are preserved.

## Rebuild

Node.js, Google Chrome, Python 3, and Pillow are needed for local artwork generation. Install the rendering tools explicitly in this checkout, not an ancestor project:

```sh
npm install --prefix . --no-save @playwright/test sharp
python -m pip install Pillow==12.3.0
```

The repository already ignores local Node verification dependencies. No application package manifest or runtime is added.

```powershell
node scripts/render_profile.mjs "C:\Users\2k25c\Downloads\ruru pfp.png"
python scripts/validate_profile.py
python -m unittest discover -s scripts -p test_activity.py -v
python -m unittest discover -s scripts -p "test_*.py" -v
node scripts/preview_profile.mjs
node scripts/preview_profile.mjs --github
```

Omit the portrait argument to reuse `assets/profile/portrait.jpg`. `render_profile.mjs` uses an offscreen browser composition to produce PNG frames, rasterizes correctly shaped Devanagari text, captures two actual public project previews, and invokes the Pillow encoder. It does not write or modify any interactive page. The first build fetches Google Fonts (DM Sans, Instrument Serif, and Noto Serif Devanagari); fonts are rasterized into the output, not requested by README readers. Font sources are Google Fonts under their respective OFL licenses.

## Assets

- `assets/profile/portrait.jpg`: the supplied real portrait, resized/compressed with metadata stripped; no generated face or retouching.
- `assets/profile/hero-static.png`: complete identity and portrait, also the first and final GIF frame.
- `assets/profile/hero-assembly.gif`: 56 frames, approximately 2.1 MB. The encoded sequence is about 6.3 seconds including its opening/closing holds; the cursor choreography itself is about 4.3 seconds. No loop extension is present, so it settles once rather than flashing repeatedly.
- `assets/profile/closing.png`: 1200x620 gold-on-dark verse composition, with rasterized Devanagari, the supplied English meaning, and signature.
- `assets/profile/closing-mobile.png`: 780x850 version with larger type for narrow viewports.
- `assets/profile/gdgoc-preview.jpg`: actual public community website capture, not an invented UI or a solo-build attribution.
- `assets/profile/bloodbond-preview.jpg`: actual prototype capture; README explicitly identifies sample data and non-operational status.

The hero `<picture>` selects the static PNG when reduced motion is requested. The closing `<picture>` selects the portrait-format composition below 600px. All fallback images have meaningful alternative text. A native text version of the Sanskrit and English is available in the closing disclosure.

## Existing Artwork and Activity

The original character SVG and contribution field remain linked in a disclosure rather than being discarded or visually competing with the introduction. The original ASCII artwork also remains in the repository. The contribution snake retains its real grid/path/animation; its palette and generation workflow are coordinated. Both snake SVGs include a reduced-motion override that freezes their animation when requested.

Activity is generated from GitHub data, with explicit periods and timestamps, not hardcoded totals. The refreshed generator paginates public repositories and their language byte data. Language share includes owned public forks and is explicitly not a proficiency measurement. Failed API refreshes do not synthesize new statistics over existing graphics. Scheduled refreshes continue through the existing activity and snake workflows.

All three generated-asset writers share a branch-specific concurrency group, retain queued runs, and check out the latest branch tip after entering the queue. This prevents them from racing each other's pushes. Only the default branch publishes; manually dispatched feature-branch runs generate and validate without committing over reviewed assets. Snake generation validates both exact palettes, defined animation references, and matching light/dark geometry before publishing, without requiring Pillow.

Scheduled commits on `main` can still conflict with a feature branch that edits the same generated SVGs. Merge `origin/main` into the feature branch, retain the complete valid feature snake outputs when appropriate, and preserve unrelated main assets. Do not splice animation data or use a merge driver that hides real conflicts. These coordination changes take effect for scheduled runs only after the PR is merged.

The existing Pages workflow is unchanged. GitHub suppresses push-triggered runs for commits made using `GITHUB_TOKEN`, so a scheduled 3D refresh alone does not redeploy that viewer; a normal relevant main-branch push or manual Pages dispatch still deploys it. This pre-existing limitation does not affect the repository-hosted README graphics.

## Verification

`validate_profile.py` checks every relative README asset, image alternatives, supported markup, safe self-contained SVGs, the exact Sanskrit, image dimensions, GIF budget, motion frames, duration, no loop, complete first/final identity frames, and the snake palettes, animation consistency, and reduced-motion override. `test_snake.py` exercises old-palette, missing-keyframe, mismatched-geometry, conflict-marker, and missing-reduced-motion regressions. The read-only Actions workflow runs these checks and all activity/snake tests on relevant pull requests.

`preview_profile.mjs` asks GitHub's authenticated Markdown API to sanitize the actual README, then previews that returned markup with GitHub's own loaded stylesheets. It checks 1280px and 375px layouts in light/dark themes, collapsed/expanded disclosures, all decoded images, reduced-motion source selection, mobile closing selection, actual GIF playback, and its stable final frame. Local screenshots and sanitized HTML are written only under ignored `shots/`; there is no preview server or deployed application.

The Markdown API retained both the reduced-motion and mobile `<source media>` attributes during testing. The real branch-rendered README was also tested on GitHub at desktop/mobile sizes, including decoded assets, source selection, GIF playback, and image aspect ratios. That check caught GitHub's fixed-height image distortion under width clamping; README images deliberately omit HTML height attributes, and a regression check enforces this. Browser rendering does not guarantee behavior in every browser or assistive technology.

## Content Decisions

Five project descriptions are tied to inspected source: GestureOS, ARCEUS, PatchPilot, GDGoC, and BloodBond. The live portfolio is a direct contact link rather than another duplicate feature. Java is supported by actual LeetCode implementations. C is omitted because the inspected repositories did not establish authored C implementation; C++ is not mislabeled C. No resume asset or email address was supplied, so neither is invented.

The Sanskrit was cross-checked with [Bhagavad Gita 2.47](https://www.holy-bhagavad-gita.org/chapter/2/verse/47/). The English is the user's supplied meaning, not a claimed quotation of that site's translation. No religious iconography or animation is applied to the verse.

Public portfolio and both preserved interactive URLs returned HTTP 200 during the audit. Existing activity, snake, and 3D generation workflows had successful recent runs. These checks establish availability, not execution quality of every third-party project or backend.
