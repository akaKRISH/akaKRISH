#!/usr/bin/env python3
"""Generate activity cards from GitHub; failed refreshes leave existing cards intact.

Usage: GITHUB_TOKEN=... python scripts/generate_activity.py [username]
Only Python's standard library is required.
"""

import json
import os
import sys
import tempfile
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_USER = "akaKRISH"
INK = "#0B0A11"
IVORY = "#F5F0ED"
ROSE = "#F44984"
VIOLET = "#8B5CF6"
FLARE = "#FF865A"
GOLD = "#C9AE78"
LANGUAGE_COLORS = (ROSE, VIOLET, FLARE, GOLD, IVORY, IVORY)
OUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "activity"
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

USER_QUERY = """
query($login: String!, $after: String, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    login
    repositories(first: 100, after: $after, ownerAffiliations: [OWNER], privacy: PUBLIC) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        id
        languages(first: 100, orderBy: {field: SIZE, direction: DESC}) {
          pageInfo { hasNextPage endCursor }
          edges { size node { name } }
        }
      }
    }
    contributionsCollection(from: $from, to: $to) {
      startedAt
      endedAt
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      contributionCalendar { totalContributions }
    }
  }
}
"""

LANGUAGE_QUERY = """
query($id: ID!, $after: String!) {
  node(id: $id) {
    ... on Repository {
      languages(first: 100, after: $after, orderBy: {field: SIZE, direction: DESC}) {
        pageInfo { hasNextPage endCursor }
        edges { size node { name } }
      }
    }
  }
}
"""


class ActivityDataError(ValueError):
    """The API did not provide a complete, usable snapshot."""


def graphql_query(token, query, variables=None):
    payload = json.dumps({"query": query, "variables": variables or {}}).encode()
    request = urllib.request.Request(
        "https://api.github.com/graphql", data=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "ruru-activity-generator"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        raise ActivityDataError(f"GitHub API returned HTTP {error.code}.") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        raise ActivityDataError("GitHub API request failed.") from None
    if result.get("errors") or not result.get("data"):
        raise ActivityDataError("GitHub returned incomplete data or GraphQL errors.")
    return result["data"]


def next_cursor(connection, seen):
    page = connection["pageInfo"]
    if not page["hasNextPage"]:
        return None
    cursor = page["endCursor"]
    if not cursor or cursor in seen:
        raise ActivityDataError("GitHub pagination did not advance.")
    seen.add(cursor)
    return cursor


def count(value):
    if type(value) is not int or value < 0:
        raise ActivityDataError("GitHub returned an invalid count.")
    return value


def fetch_user_data(token, username, now=None):
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).replace(microsecond=0)
    try:
        start = now.replace(year=now.year - 1)
    except ValueError:  # February 29 has no counterpart in the previous year.
        start = now.replace(year=now.year - 1, day=28)
    variables = {"login": username, "after": None, "from": start.isoformat(), "to": now.isoformat()}
    repositories = []
    repo_ids = set()
    repo_cursors = set()
    user_data = None
    while True:
        user = graphql_query(token, USER_QUERY, variables)["user"]
        if not user:
            raise ActivityDataError("GitHub user was not found.")
        if user_data is None:
            user_data = user
        connection = user["repositories"]
        for repo in connection["nodes"]:
            if repo["id"] in repo_ids:
                raise ActivityDataError("GitHub returned a duplicate repository.")
            repo_ids.add(repo["id"])
            languages = repo["languages"]
            edges = list(languages["edges"])
            language_cursors = set()
            while cursor := next_cursor(languages, language_cursors):
                node = graphql_query(token, LANGUAGE_QUERY, {"id": repo["id"], "after": cursor})["node"]
                languages = node["languages"]
                edges.extend(languages["edges"])
            repo["languages"] = {"edges": edges, "pageInfo": languages["pageInfo"]}
            repositories.append(repo)
        cursor = next_cursor(connection, repo_cursors)
        if cursor is None:
            break
        variables["after"] = cursor
    if len(repositories) != count(user_data["repositories"]["totalCount"]):
        raise ActivityDataError("The public repository list changed during generation; retry the refresh.")
    user_data["repositories"]["nodes"] = repositories
    return user_data


def compute_language_stats(user_data):
    """Sum all language bytes, with an explicit remainder rather than dropping it."""
    sizes = {}
    for repo in user_data["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            if not isinstance(name, str) or not name:
                raise ActivityDataError("GitHub returned an invalid language name.")
            sizes[name] = sizes.get(name, 0) + count(edge["size"])
    ordered = sorted(((name, size) for name, size in sizes.items() if size), key=lambda item: (-item[1], item[0]))
    total = sum(size for _, size in ordered)
    if len(ordered) > 6:
        ordered = ordered[:5] + [("Other languages", sum(size for _, size in ordered[5:]))]
    return [{"name": name, "size": size, "pct": size / total * 100, "color": LANGUAGE_COLORS[i]}
            for i, (name, size) in enumerate(ordered)]


def element(parent, tag, text=None, **attributes):
    node = ET.SubElement(parent, f"{{{SVG_NS}}}{tag}", {key.replace("_", "-"): str(value) for key, value in attributes.items()})
    node.text = text
    return node


def text(svg, x, y, value, **attributes):
    return element(svg, "text", value, x=x, y=y, fill=IVORY, font_size=12, **attributes)


def card(title, username, description, generated_at, kind):
    svg = ET.Element(f"{{{SVG_NS}}}svg", {"width": "420", "height": "360", "viewBox": "0 0 420 360",
                     "role": "img", "aria-labelledby": f"{kind}-title {kind}-description",
                     "font-family": "Inter,Segoe UI,Arial,sans-serif"})
    element(svg, "title", f"{title} for @{username}", id=f"{kind}-title")
    element(svg, "desc", description, id=f"{kind}-description")
    element(svg, "rect", x=0.5, y=0.5, width=419, height=359, rx=8, fill=INK, stroke=IVORY, stroke_opacity=0.18)
    heading = text(svg, 24, 34, title, font_weight=600)
    heading.set("font-size", "17")
    handle = text(svg, 396, 34, f"@{username}", text_anchor="end", opacity=0.7)
    handle.set("font-size", "11")
    element(svg, "line", x1=24, y1=87, x2=396, y2=87, stroke=IVORY, stroke_opacity=0.14)
    element(svg, "line", x1=24, y1=316, x2=396, y2=316, stroke=IVORY, stroke_opacity=0.14)
    footer = text(svg, 24, 339, generated_at.astimezone(timezone.utc).strftime("Generated %d %b %Y, %H:%M UTC"), opacity=0.65)
    footer.set("font-size", "10")
    return svg


def serialize(svg):
    ET.indent(svg, space="  ")
    return ET.tostring(svg, encoding="unicode") + "\n"


def generate_overview_svg(user_data, username, generated_at=None):
    generated_at = generated_at or datetime.now(timezone.utc)
    cc = user_data["contributionsCollection"]
    start = datetime.fromisoformat(cc["startedAt"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(cc["endedAt"].replace("Z", "+00:00"))
    svg = card("GitHub activity", username, "Contribution totals for the trailing 12 months. Public repository count is current.", generated_at, "activity")
    text(svg, 24, 57, "Trailing 12 months", opacity=0.8)
    period = text(svg, 24, 75, f"{start:%d %b %Y} - {end:%d %b %Y}", opacity=0.6)
    period.set("font-size", "10")
    total = text(svg, 24, 128, f'{count(cc["contributionCalendar"]["totalContributions"]):,}', font_weight=600)
    total.set("font-size", "32")
    total.set("fill", ROSE)
    text(svg, 24, 148, "Contributions", opacity=0.75)
    stats = [("Commits", cc["totalCommitContributions"]), ("Pull requests", cc["totalPullRequestContributions"]),
             ("Code reviews", cc["totalPullRequestReviewContributions"]), ("Issues", cc["totalIssueContributions"]),
             ("Public repositories (current)", user_data["repositories"]["totalCount"])]
    for i, (label, value) in enumerate(stats):
        text(svg, 24, 183 + i * 27, label, opacity=0.75)
        text(svg, 396, 183 + i * 27, f"{count(value):,}", text_anchor="end", font_weight=600)
    return serialize(svg)


def generate_languages_svg(langs, username, repo_count, generated_at=None):
    generated_at = generated_at or datetime.now(timezone.utc)
    svg = card("Languages by bytes", username, "Share of all language bytes in owned public repositories, including forks. Not proficiency.", generated_at, "languages")
    text(svg, 24, 57, "Code bytes, not proficiency", opacity=0.8)
    scope = text(svg, 24, 75, f"All {count(repo_count):,} owned public repositories; includes forks", opacity=0.6)
    scope.set("font-size", "10")
    if not langs:
        text(svg, 24, 148, "No language bytes reported in public repositories.", opacity=0.75)
        return serialize(svg)
    total = sum(lang["size"] for lang in langs)
    x = 24
    for lang in langs:
        width = 372 * lang["size"] / total
        element(svg, "rect", x=f"{x:.6f}", y=107, width=f"{width:.6f}", height=8, fill=lang["color"], opacity=0.45 if lang["name"] == "Other languages" else 1)
        x += width
    for i, lang in enumerate(langs):
        y = 147 + i * 27
        element(svg, "rect", x=24, y=y - 8, width=7, height=7, rx=2, fill=lang["color"], opacity=0.45 if lang["name"] == "Other languages" else 1)
        text(svg, 42, y, lang["name"])
        value = text(svg, 396, y, f'{lang["size"]:,} B ({lang["pct"]:.1f}%)', text_anchor="end", opacity=0.7)
        value.set("font-size", "10")
    return serialize(svg)


def write_card(path, svg):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as output:
            temporary = Path(output.name)
            output.write(svg)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USER
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN is not set; existing activity cards were left unchanged.", file=sys.stderr)
        return 1
    try:
        generated_at = datetime.now(timezone.utc)
        user_data = fetch_user_data(token, username, generated_at)
        username = user_data["login"]
        langs = compute_language_stats(user_data)
        cards = {"github-overview.svg": generate_overview_svg(user_data, username, generated_at),
                 "github-languages.svg": generate_languages_svg(langs, username, user_data["repositories"]["totalCount"], generated_at)}
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        for name, svg in cards.items():
            write_card(OUT_DIR / name, svg)
    except (ActivityDataError, KeyError, TypeError, ValueError, OSError) as error:
        print(f"Activity refresh failed ({type(error).__name__}); no fallback data was generated.", file=sys.stderr)
        return 1
    print(f"Generated both activity cards for @{username} from {len(user_data['repositories']['nodes'])} public repositories.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
