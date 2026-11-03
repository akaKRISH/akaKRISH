"""Run with: python -B -m unittest discover -s scripts -p test_activity.py"""

import copy
import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import generate_activity as activity

NOW = datetime(2026, 11, 4, 12, 34, tzinfo=timezone.utc)


def connection(edges=None, more=False, cursor=None):
    return {"edges": edges or [], "pageInfo": {"hasNextPage": more, "endCursor": cursor}}


def edge(name, size):
    return {"node": {"name": name}, "size": size}


def user_data(nodes=None, total=None, more=False):
    nodes = nodes or []
    return {"login": "akaKRISH", "repositories": {
        "nodes": nodes, "totalCount": len(nodes) if total is None else total,
        "pageInfo": {"hasNextPage": more, "endCursor": "repo-next" if more else None}},
        "contributionsCollection": {"startedAt": "2025-11-04T12:34:00Z", "endedAt": "2026-11-04T12:34:00Z",
                                    "totalCommitContributions": 12, "totalPullRequestContributions": 3,
                                    "totalPullRequestReviewContributions": 2, "totalIssueContributions": 1,
                                    "contributionCalendar": {"totalContributions": 18}}}


class ActivityTests(unittest.TestCase):
    def test_paginates_repositories_and_each_repository_languages(self):
        first = user_data([{"id": "one", "languages": connection([edge("Python", 10)], True, "lang-next")}], total=2, more=True)
        second = user_data([{"id": "two", "languages": connection([edge("Python", 5)])}], total=2)
        responses = [{"user": first}, {"node": {"languages": connection([edge("C", 20)])}}, {"user": second}]
        calls = []

        def query(token, source, variables):
            calls.append(copy.deepcopy(variables))
            return responses.pop(0)

        with patch.object(activity, "graphql_query", side_effect=query):
            result = activity.fetch_user_data("test-token", "akaKRISH", NOW)
        self.assertEqual(len(result["repositories"]["nodes"]), 2)
        self.assertIsNone(calls[0]["after"])
        self.assertEqual(calls[0]["from"], "2025-11-04T12:34:00+00:00")
        self.assertEqual(calls[1], {"id": "one", "after": "lang-next"})
        self.assertEqual(calls[2]["after"], "repo-next")
        self.assertEqual({row["name"]: row["size"] for row in activity.compute_language_stats(result)}, {"C": 20, "Python": 15})

    def test_leap_day_and_changed_repository_count(self):
        calls = []
        with patch.object(activity, "graphql_query", side_effect=lambda token, query, variables: calls.append(dict(variables)) or {"user": user_data()}):
            activity.fetch_user_data("test-token", "akaKRISH", datetime(2024, 2, 29, tzinfo=timezone.utc))
        self.assertTrue(calls[0]["from"].startswith("2023-02-28"))
        with patch.object(activity, "graphql_query", return_value={"user": user_data(total=1)}):
            with self.assertRaises(activity.ActivityDataError):
                activity.fetch_user_data("test-token", "akaKRISH", NOW)

    def test_no_truncated_remainder_or_distorted_bar(self):
        data = user_data([{"id": "one", "languages": connection([edge(f"Language {i}", i) for i in range(1, 9)])}])
        langs = activity.compute_language_stats(data)
        self.assertEqual(len(langs), 6)
        self.assertEqual(langs[-1]["name"], "Other languages")
        self.assertEqual(sum(row["size"] for row in langs), 36)
        self.assertAlmostEqual(sum(row["pct"] for row in langs), 100)
        svg = ET.fromstring(activity.generate_languages_svg(langs, "akaKRISH", 1, NOW))
        segments = [node for node in svg.iter() if node.get("y") == "107"]
        self.assertAlmostEqual(sum(float(node.get("width")) for node in segments), 372, places=5)

    def test_xml_escaping_scope_timestamp_and_no_vanity_counts(self):
        name = "R&D <experimental>"
        data = user_data([{"id": "one", "languages": connection([edge(name, 100)])}])
        langs = activity.compute_language_stats(data)
        for svg in [activity.generate_overview_svg(data, 'name<&"', NOW),
                    activity.generate_languages_svg(langs, 'name<&"', 1, NOW)]:
            root = ET.fromstring(svg)
            content = " ".join(root.itertext())
            self.assertIn('name<&"', content)
            self.assertIn("Generated 04 Nov 2026, 12:34 UTC", content)
            self.assertNotIn("this year", content.lower())
            self.assertNotIn("followers", content.lower())
            self.assertNotIn("stars", content.lower())
            self.assertTrue(all(float(node.get("rx", 0)) <= 8 for node in root.iter()))
        self.assertIn(name, " ".join(ET.fromstring(activity.generate_languages_svg(langs, "akaKRISH", 1, NOW)).itertext()))

    def test_graphql_errors_and_network_failure_reject_partial_data(self):
        partial = io.BytesIO(json.dumps({"data": {"user": user_data()}, "errors": [{"message": "partial"}]}).encode())
        for result in [partial, urllib.error.URLError("offline")]:
            with patch.object(activity.urllib.request, "urlopen", **({"side_effect": result} if isinstance(result, Exception) else {"return_value": result})):
                with self.assertRaises(activity.ActivityDataError):
                    activity.graphql_query("test-token", "query {}")
        with self.assertRaises(activity.ActivityDataError):
            activity.next_cursor(connection(more=True, cursor="same"), {"same"})

    def test_failed_refresh_never_replaces_either_existing_card(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            originals = {name: '<svg xmlns="http://www.w3.org/2000/svg"><text>Last real snapshot</text></svg>'
                         for name in ["github-overview.svg", "github-languages.svg"]}
            for name, value in originals.items():
                (output / name).write_text(value, encoding="utf-8")
            for token in ["", "test-token"]:
                with patch.object(activity, "OUT_DIR", output), patch.dict(os.environ, {"GITHUB_TOKEN": token}), \
                     patch.object(sys, "argv", ["generate_activity.py", "akaKRISH"]), \
                     patch.object(activity, "fetch_user_data", side_effect=activity.ActivityDataError("offline")), \
                     patch("sys.stderr", new_callable=io.StringIO):
                    self.assertEqual(activity.main(), 1)
                for name, value in originals.items():
                    self.assertEqual((output / name).read_text(encoding="utf-8"), value)

    def test_empty_data_is_reported_honestly(self):
        self.assertEqual(activity.compute_language_stats(user_data()), [])
        svg = activity.generate_languages_svg([], "akaKRISH", 0, NOW)
        self.assertIn("No language bytes reported", svg)
        self.assertIn("All 0 owned public repositories", svg)
        with self.assertRaises(activity.ActivityDataError):
            activity.compute_language_stats(user_data([{"id": "bad", "languages": connection([edge("Python", -1)])}]))


if __name__ == "__main__":
    unittest.main()
