#!/usr/bin/env python3
"""
generate_ascii.py — Convert PFP into colored ASCII portrait + laser-print GIF.

Outputs:
  assets/ascii/ruru-laser-print.png  (static final portrait)
  assets/ascii/ruru-laser-print.gif  (laser-print animation)
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import struct
import zlib
import math

# ─── Config ──────────────────────────────────────────────────────────────
ASCII_COLS = 160          # characters wide
CHAR_ASPECT = 0.50        # char height/width ratio for monospace
FONT_SIZE = 13            # pixel size per character
BG_COLOR = (5, 7, 11)     # #05070B
LASER_CORE = (170, 221, 255)    # blue-white core
LASER_GLOW = (120, 196, 255)    # #78C4FF cyan
LASER_EDGE = (155, 140, 255)    # #9B8CFF violet
BOOT_COLOR = (120, 196, 255)    # #78C4FF
SCAN_TEXT_COLOR = (148, 163, 184)  # #94A3B8 muted
COMPLETE_COLOR = (120, 196, 255)

# Character density ramp: darkest (space) → brightest (@)
DENSITY_RAMP = " .,:;+*?%S#@"

# GIF timing
BOOT_FRAMES = 6           # terminal boot frames
SCAN_FRAMES = 60           # laser scanning frames
HOLD_FRAMES = 25           # hold completed portrait
COMPLETE_FRAMES = 5        # "SCAN COMPLETE" text frames
FRAME_DURATION_MS = 80     # ms per frame

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
SOURCE_IMG = SCRIPT_DIR / "pfp_source.jpg"
OUT_DIR = REPO_ROOT / "assets" / "ascii"
OUT_PNG = OUT_DIR / "ruru-laser-print.png"
OUT_GIF = OUT_DIR / "ruru-laser-print.gif"


def load_monospace_font(size):
    """Try to load a monospace font, fallback to default."""
    font_candidates = [
        "consola.ttf",        # Windows Consolas
        "cour.ttf",           # Windows Courier New
        "lucon.ttf",          # Windows Lucida Console
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/cour.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ]
    for font_path in font_candidates:
        try:
            return ImageFont.truetype(font_path, size)
        except (OSError, IOError):
            continue
    # Fallback to default
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def image_to_ascii_grid(img_path, cols):
    """Convert image to a grid of (char, r, g, b) tuples."""
    img = Image.open(img_path).convert("RGB")
    
    # Calculate rows based on aspect ratio
    w, h = img.size
    cell_w = w / cols
    cell_h = cell_w / CHAR_ASPECT
    rows = int(h / cell_h)
    
    # Resize image to match grid
    img_resized = img.resize((cols, rows), Image.Resampling.LANCZOS)
    
    grid = []
    for y in range(rows):
        row = []
        for x in range(cols):
            r, g, b = img_resized.getpixel((x, y))
            # Calculate brightness (0-1)
            brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
            # Map brightness to character
            idx = int(brightness * (len(DENSITY_RAMP) - 1))
            idx = max(0, min(idx, len(DENSITY_RAMP) - 1))
            char = DENSITY_RAMP[idx]
            
            # Boost color saturation slightly for visual pop
            avg = (r + g + b) / 3
            if avg > 10:  # Don't boost pure black
                boost = 1.15
                r = min(255, int(r * boost))
                g = min(255, int(g * boost))
                b = min(255, int(b * boost))
            
            row.append((char, r, g, b))
        grid.append(row)
    
    return grid


def measure_char(font):
    """Measure character dimensions for the monospace font."""
    temp = Image.new("RGB", (100, 100))
    draw = ImageDraw.Draw(temp)
    bbox = draw.textbbox((0, 0), "@", font=font)
    char_w = bbox[2] - bbox[0]
    char_h = bbox[3] - bbox[1]
    # Ensure minimum sizes
    char_w = max(char_w, 6)
    char_h = max(char_h, 10)
    return char_w, char_h


def render_ascii_frame(grid, font, char_w, char_h, reveal_rows=None,
                       laser_row=None, overlay_text=None, boot_lines=None):
    """
    Render an ASCII frame.
    
    reveal_rows: how many rows from top are visible (None = all)
    laser_row: y position of laser scanline (None = no laser)
    overlay_text: list of (text, y_fraction) to overlay
    boot_lines: list of strings for terminal boot text
    """
    cols = len(grid[0]) if grid else 0
    rows = len(grid)
    
    padding_x = 30
    padding_y = 20
    
    img_w = cols * char_w + padding_x * 2
    img_h = rows * char_h + padding_y * 2
    
    img = Image.new("RGB", (img_w, img_h), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Draw boot text if present
    if boot_lines is not None:
        y_offset = padding_y
        for line in boot_lines:
            draw.text((padding_x, y_offset), line, fill=BOOT_COLOR, font=font)
            y_offset += char_h + 2
        return img
    
    # Draw ASCII characters
    visible = reveal_rows if reveal_rows is not None else rows
    visible = min(visible, rows)
    
    for y in range(visible):
        for x in range(cols):
            char, r, g, b = grid[y][x]
            if char == ' ':
                continue
            px = padding_x + x * char_w
            py = padding_y + y * char_h
            draw.text((px, py), char, fill=(r, g, b), font=font)
    
    # Draw laser scanline
    if laser_row is not None and 0 <= laser_row < rows:
        laser_y = padding_y + laser_row * char_h
        
        # Violet edge (wider, dimmer)
        for dy in range(-3, 4):
            alpha = max(0, 60 - abs(dy) * 20)
            edge_color = (
                min(255, LASER_EDGE[0] * alpha // 255),
                min(255, LASER_EDGE[1] * alpha // 255),
                min(255, LASER_EDGE[2] * alpha // 255),
            )
            draw.line(
                [(padding_x - 5, laser_y + char_h // 2 + dy),
                 (img_w - padding_x + 5, laser_y + char_h // 2 + dy)],
                fill=edge_color, width=1
            )
        
        # Cyan glow (medium)
        for dy in range(-2, 3):
            alpha = max(0, 180 - abs(dy) * 60)
            glow_color = (
                min(255, LASER_GLOW[0] * alpha // 255),
                min(255, LASER_GLOW[1] * alpha // 255),
                min(255, LASER_GLOW[2] * alpha // 255),
            )
            draw.line(
                [(padding_x - 3, laser_y + char_h // 2 + dy),
                 (img_w - padding_x + 3, laser_y + char_h // 2 + dy)],
                fill=glow_color, width=1
            )
        
        # Core bright line
        draw.line(
            [(padding_x - 2, laser_y + char_h // 2),
             (img_w - padding_x + 2, laser_y + char_h // 2)],
            fill=LASER_CORE, width=1
        )
    
    # Draw overlay text (scan progress, etc.)
    if overlay_text:
        for text, y_frac in overlay_text:
            text_y = int(img_h * y_frac)
            # Right-align the text
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_x = img_w - padding_x - text_w
            draw.text((text_x, text_y), text, fill=SCAN_TEXT_COLOR, font=font)
    
    return img


def generate_static_png(grid, font, char_w, char_h):
    """Generate the final static portrait PNG."""
    print("[+] Generating static PNG...")
    img = render_ascii_frame(grid, font, char_w, char_h)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img.save(str(OUT_PNG), "PNG", optimize=True)
    print(f"    -> {OUT_PNG} ({OUT_PNG.stat().st_size // 1024} KB)")
    return img


def generate_laser_gif(grid, font, char_w, char_h):
    """Generate the laser-print animation GIF."""
    print("[+] Generating laser-print GIF...")
    
    rows = len(grid)
    cols = len(grid[0])
    frames = []
    durations = []
    
    # ── Phase 0: Boot sequence ──
    boot_sequences = [
        ["ruru@lab:~$ ./initialize --profile"],
        ["ruru@lab:~$ ./initialize --profile", "",
         "[SYS] initializing renderer..."],
        ["ruru@lab:~$ ./initialize --profile", "",
         "[SYS] initializing renderer...",
         "[SYS] loading identity..."],
        ["ruru@lab:~$ ./initialize --profile", "",
         "[SYS] initializing renderer...",
         "[SYS] loading identity...",
         "[SYS] loading portrait matrix..."],
        ["ruru@lab:~$ ./initialize --profile", "",
         "[SYS] initializing renderer...",
         "[SYS] loading identity...",
         "[SYS] loading portrait matrix...",
         "[SYS] calibrating optical layer..."],
        ["ruru@lab:~$ ./initialize --profile", "",
         "[SYS] initializing renderer...",
         "[SYS] loading identity...",
         "[SYS] loading portrait matrix...",
         "[SYS] calibrating optical layer...",
         "", "[SYS] SCAN INITIATED"],
    ]
    
    for boot_lines in boot_sequences:
        frame = render_ascii_frame(grid, font, char_w, char_h,
                                   boot_lines=boot_lines)
        frames.append(frame)
        durations.append(350)  # Slower for boot text readability
    
    # ── Phase 1-2: Laser scan ──
    for i in range(SCAN_FRAMES):
        progress = i / (SCAN_FRAMES - 1)  # 0.0 → 1.0
        reveal = int(progress * rows)
        laser = reveal  # Laser is at the leading edge
        
        # Scan progress text
        pct = int(progress * 100)
        overlay = []
        if pct in range(23, 28):
            overlay.append(("SCAN 025%", 0.92))
        elif pct in range(48, 53):
            overlay.append(("SCAN 050%", 0.92))
        elif pct in range(73, 78):
            overlay.append(("SCAN 075%", 0.92))
        elif pct >= 97:
            overlay.append(("SCAN 100%", 0.92))
        
        frame = render_ascii_frame(grid, font, char_w, char_h,
                                   reveal_rows=reveal,
                                   laser_row=laser,
                                   overlay_text=overlay if overlay else None)
        frames.append(frame)
        durations.append(FRAME_DURATION_MS)
    
    # ── Phase 3: Scan complete ──
    for i in range(COMPLETE_FRAMES):
        overlay = [("SCAN COMPLETE", 0.90), ("PORTRAIT ONLINE", 0.93)]
        frame = render_ascii_frame(grid, font, char_w, char_h,
                                   overlay_text=overlay)
        frames.append(frame)
        durations.append(200)
    
    # ── Phase 4: Hold completed portrait ──
    final_frame = render_ascii_frame(grid, font, char_w, char_h)
    for _ in range(HOLD_FRAMES):
        frames.append(final_frame)
        durations.append(120)
    
    # Save as GIF
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"    Total frames: {len(frames)}")
    print(f"    Saving GIF...")
    
    # Convert frames to P mode for GIF with dithering for quality
    # Use the first frame as base
    frames[0].save(
        str(OUT_GIF),
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=False,
    )
    
    size_mb = OUT_GIF.stat().st_size / (1024 * 1024)
    print(f"    -> {OUT_GIF} ({size_mb:.1f} MB)")
    
    return frames


def main():
    if not SOURCE_IMG.exists():
        print(f"[!] Source image not found: {SOURCE_IMG}")
        sys.exit(1)
    
    print("=" * 60)
    print("  RURU ASCII PORTRAIT GENERATOR")
    print("=" * 60)
    print()
    
    # Load font
    font = load_monospace_font(FONT_SIZE)
    char_w, char_h = measure_char(font)
    print(f"[*] Font loaded — char size: {char_w}x{char_h}px")
    
    # Convert image to ASCII grid
    print(f"[*] Converting image to ASCII ({ASCII_COLS} cols)...")
    grid = image_to_ascii_grid(SOURCE_IMG, ASCII_COLS)
    print(f"    Grid: {len(grid[0])} × {len(grid)} (cols × rows)")
    
    # Generate outputs
    generate_static_png(grid, font, char_w, char_h)
    generate_laser_gif(grid, font, char_w, char_h)
    
    print()
    print("[OK] All assets generated successfully.")


if __name__ == "__main__":
    main()
