import unittest
from unittest.mock import patch

from insider_sources import MicrosoftSources


class MicrosoftSourcesTests(unittest.TestCase):
    def test_build_match_requires_numeric_boundaries(self):
        source = MicrosoftSources(26100)
        self.assertTrue(source._matches_build("Windows Insider Preview Build 26100"))
        self.assertTrue(source._matches_build("Version 26100.100"))
        self.assertFalse(source._matches_build("Build 126100"))
        self.assertFalse(source._matches_build("Build 261000"))

    def test_rss_items_are_parsed_and_matched(self):
        feed = """<?xml version='1.0'?><rss><channel>
        <item><title>Windows 11 Insider Preview Build 26100</title>
        <link>https://blogs.windows.com/windows-insider/example</link>
        <description>Improvements &amp; fixes</description></item>
        <item><title>Build 99999</title><link>https://example.com/other</link>
        <description>Other build</description></item>
        </channel></rss>"""
        source = MicrosoftSources(26100)
        with patch.object(source, "_fetch_text", return_value=feed):
            notes = source.search_windows_insider_blog()
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]["source"], "Windows Insider Blog")
        self.assertIn("Improvements & fixes", notes[0]["summary"])

    def test_invalid_rss_returns_no_results(self):
        source = MicrosoftSources(26100)
        with patch.object(source, "_fetch_text", return_value="<rss>"):
            self.assertEqual(source.search_windows_insider_blog(), [])


if __name__ == "__main__":
    unittest.main()
