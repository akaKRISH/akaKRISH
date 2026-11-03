"""Encode deterministic browser-rendered frames with one shared, stable palette."""
import json
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


def encode(directory):
    paths = sorted(directory.glob("[0-9][0-9][0-9].png"))
    durations = json.loads((directory / "timing.json").read_text(encoding="utf-8"))
    if len(paths) != len(durations):
        raise ValueError("Frame count does not match timing data")
    with Image.open(paths[0]) as first:
        palette = first.convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    frames = []
    for path in paths:
        with Image.open(path) as source:
            frames.append(source.convert("RGB").quantize(palette=palette, dither=Image.Dither.NONE))
    target = ROOT / "assets/profile/hero-assembly.gif"
    # Omit the loop extension: the sequence ends on the complete identity, once.
    frames[0].save(target, save_all=True, append_images=frames[1:], duration=durations, optimize=True, disposal=1)
    print(f"Encoded {len(frames)} frames; {target.stat().st_size:,} bytes; one-shot GIF")


if __name__ == "__main__":
    encode(Path(sys.argv[1]).resolve())
