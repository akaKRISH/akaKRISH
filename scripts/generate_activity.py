#!/usr/bin/env python3
"""
generate_activity.py -- Generate self-hosted GitHub activity SVG cards.

Uses the GitHub GraphQL API to fetch real user data, then creates
styled SVG cards matching the RURU visual system.

Requires: GITHUB_TOKEN env var (with read:user scope)
Usage:    python scripts/generate_activity.py [username]
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

# ─── Config ──────────────────────────────────────────────────────────────
DEFAULT_USER = "akaKRISH"
BG = "#0B111C"
BG_CARD = "#0F1729"
PRIMARY = "#78C4FF"
SECONDARY = "#9B8CFF"
TEXT = "#F5F7FA"
MUTED = "#94A3B8"
BORDER = "#1B2638"

REPO_ROOT = Path(__file__).parent.parent
OUT_DIR = REPO_ROOT / "assets" / "activity"


def graphql_query(token, query, variables=None):
    """Execute a GitHub GraphQL query."""
    payload = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "ruru-activity-generator",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"[!] GitHub API error: {e.code} {e.reason}")
        body = e.read().decode()
        print(f"    {body[:200]}")
        return None


def fetch_user_data(token, username):
    """Fetch comprehensive user data from GitHub."""
    query = """
    query($login: String!) {
      user(login: $login) {
        name
        login
        repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC) {
          totalCount
          nodes {
            stargazerCount
            primaryLanguage {
              name
              color
            }
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges {
                size
                node {
                  name
                  color
                }
              }
            }
          }
        }
        followers { totalCount }
        contributionsCollection {
          totalCommitContributions
          totalPullRequestContributions
          totalIssueContributions
          totalPullRequestReviewContributions
          contributionCalendar {
            totalContributions
          }
        }
      }
    }
    """
    result = graphql_query(token, query, {"login": username})
    if not result or "data" not in result:
        return None
    return result["data"]["user"]


def compute_language_stats(user_data):
    """Compute language distribution from repos."""
    lang_sizes = {}
    for repo in user_data["repositories"]["nodes"]:
        for edge in repo.get("languages", {}).get("edges", []):
            name = edge["node"]["name"]
            color = edge["node"].get("color", MUTED)
            size = edge["size"]
            if name in lang_sizes:
                lang_sizes[name]["size"] += size
            else:
                lang_sizes[name] = {"size": size, "color": color}

    total = sum(v["size"] for v in lang_sizes.values())
    if total == 0:
        return []

    langs = []
    for name, data in sorted(lang_sizes.items(), key=lambda x: -x[1]["size"]):
        pct = data["size"] / total * 100
        if pct >= 1.0:  # Only show languages >= 1%
            langs.append({
                "name": name,
                "pct": round(pct, 1),
                "color": data["color"] or MUTED,
            })
    return langs[:8]  # Top 8


def generate_overview_svg(user_data, username):
    """Generate the GitHub overview SVG card."""
    cc = user_data["contributionsCollection"]
    total_stars = sum(r["stargazerCount"] for r in user_data["repositories"]["nodes"])
    total_repos = user_data["repositories"]["totalCount"]
    followers = user_data["followers"]["totalCount"]
    total_contribs = cc["contributionCalendar"]["totalContributions"]
    total_commits = cc["totalCommitContributions"]
    total_prs = cc["totalPullRequestContributions"]
    total_issues = cc["totalIssueContributions"]

    stats = [
        ("Total Contributions", f"{total_contribs:,}"),
        ("Commits (this year)", f"{total_commits:,}"),
        ("Pull Requests", f"{total_prs:,}"),
        ("Issues", f"{total_issues:,}"),
        ("Public Repos", f"{total_repos:,}"),
        ("Stars Earned", f"{total_stars:,}"),
        ("Followers", f"{followers:,}"),
    ]

    # Build SVG
    card_w = 420
    row_h = 28
    padding = 24
    header_h = 50
    card_h = header_h + len(stats) * row_h + padding

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{card_w}" height="{card_h}" viewBox="0 0 {card_w} {card_h}">',
        f'<rect width="{card_w}" height="{card_h}" rx="12" fill="{BG_CARD}" stroke="{BORDER}" stroke-width="1"/>',
        # Header
        f'<text x="{padding}" y="36" fill="{PRIMARY}" font-family="Consolas,monospace" font-size="14" font-weight="600">GITHUB OVERVIEW</text>',
        f'<text x="{card_w - padding}" y="36" fill="{MUTED}" font-family="Consolas,monospace" font-size="11" text-anchor="end">@{username}</text>',
        f'<line x1="{padding}" y1="46" x2="{card_w - padding}" y2="46" stroke="{BORDER}" stroke-width="1"/>',
    ]

    y = header_h + 8
    for label, value in stats:
        svg_parts.append(
            f'<text x="{padding}" y="{y}" fill="{MUTED}" font-family="Consolas,monospace" font-size="12">{label}</text>'
        )
        svg_parts.append(
            f'<text x="{card_w - padding}" y="{y}" fill="{TEXT}" font-family="Consolas,monospace" font-size="12" text-anchor="end" font-weight="600">{value}</text>'
        )
        y += row_h

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def generate_languages_svg(langs, username):
    """Generate the language distribution SVG card."""
    if not langs:
        return None

    card_w = 420
    padding = 24
    header_h = 50
    bar_h = 12
    bar_y_start = header_h + 8
    label_start = bar_y_start + bar_h + 20
    row_h = 22
    card_h = label_start + len(langs) * row_h + padding

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{card_w}" height="{card_h}" viewBox="0 0 {card_w} {card_h}">',
        f'<rect width="{card_w}" height="{card_h}" rx="12" fill="{BG_CARD}" stroke="{BORDER}" stroke-width="1"/>',
        # Header
        f'<text x="{padding}" y="36" fill="{SECONDARY}" font-family="Consolas,monospace" font-size="14" font-weight="600">LANGUAGES</text>',
        f'<text x="{card_w - padding}" y="36" fill="{MUTED}" font-family="Consolas,monospace" font-size="11" text-anchor="end">by code size</text>',
        f'<line x1="{padding}" y1="46" x2="{card_w - padding}" y2="46" stroke="{BORDER}" stroke-width="1"/>',
    ]

    # Horizontal stacked bar
    bar_w = card_w - padding * 2
    x = padding
    # Clip path for rounded bar
    svg_parts.append(f'<clipPath id="bar-clip"><rect x="{padding}" y="{bar_y_start}" width="{bar_w}" height="{bar_h}" rx="6"/></clipPath>')
    svg_parts.append(f'<g clip-path="url(#bar-clip)">')
    for lang in langs:
        seg_w = max(2, bar_w * lang["pct"] / 100)
        svg_parts.append(
            f'<rect x="{x}" y="{bar_y_start}" width="{seg_w}" height="{bar_h}" fill="{lang["color"]}"/>'
        )
        x += seg_w
    svg_parts.append("</g>")

    # Labels
    y = label_start
    for lang in langs:
        svg_parts.append(
            f'<circle cx="{padding + 5}" cy="{y - 4}" r="4" fill="{lang["color"]}"/>'
        )
        svg_parts.append(
            f'<text x="{padding + 16}" y="{y}" fill="{TEXT}" font-family="Consolas,monospace" font-size="12">{lang["name"]}</text>'
        )
        svg_parts.append(
            f'<text x="{card_w - padding}" y="{y}" fill="{MUTED}" font-family="Consolas,monospace" font-size="12" text-anchor="end">{lang["pct"]}%</text>'
        )
        y += row_h

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def generate_fallback_overview(username):
    """Generate a minimal fallback card when API is unavailable."""
    card_w = 420
    card_h = 100
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{card_w}" height="{card_h}" viewBox="0 0 {card_w} {card_h}">
<rect width="{card_w}" height="{card_h}" rx="12" fill="{BG_CARD}" stroke="{BORDER}" stroke-width="1"/>
<text x="210" y="45" fill="{PRIMARY}" font-family="Consolas,monospace" font-size="14" text-anchor="middle" font-weight="600">@{username}</text>
<text x="210" y="70" fill="{MUTED}" font-family="Consolas,monospace" font-size="11" text-anchor="middle">github.com/{username}</text>
</svg>"""
    return svg


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USER
    token = os.environ.get("GITHUB_TOKEN")

    if not token:
        print("[!] GITHUB_TOKEN not set. Generating fallback cards.")
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        fallback = generate_fallback_overview(username)
        (OUT_DIR / "github-overview.svg").write_text(fallback, encoding="utf-8")
        print(f"    -> {OUT_DIR / 'github-overview.svg'} (fallback)")
        return

    print(f"[*] Fetching data for @{username}...")
    user_data = fetch_user_data(token, username)

    if not user_data:
        print("[!] Failed to fetch user data. Generating fallback.")
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        fallback = generate_fallback_overview(username)
        (OUT_DIR / "github-overview.svg").write_text(fallback, encoding="utf-8")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Overview card
    overview_svg = generate_overview_svg(user_data, username)
    (OUT_DIR / "github-overview.svg").write_text(overview_svg, encoding="utf-8")
    print(f"    -> {OUT_DIR / 'github-overview.svg'}")

    # Languages card
    langs = compute_language_stats(user_data)
    if langs:
        langs_svg = generate_languages_svg(langs, username)
        if langs_svg:
            (OUT_DIR / "github-languages.svg").write_text(langs_svg, encoding="utf-8")
            print(f"    -> {OUT_DIR / 'github-languages.svg'}")

    print("[OK] Activity cards generated.")


if __name__ == "__main__":
    main()
