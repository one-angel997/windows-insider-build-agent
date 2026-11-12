import unittest

from insider_agent import find_direct_release_notes_url


class DirectReleaseNotesUrlTests(unittest.TestCase):
    def test_selects_exact_microsoft_learn_build_notes(self):
        notes = [
            {"source": "Microsoft Learn", "url": "https://learn.microsoft.com/en-us/windows-insider/flight-hub/"},
            {"source": "Microsoft Learn", "url": "https://learn.microsoft.com/en-us/windows-insider/release-notes/experimental-future-platforms/preview-build-29695-1001"},
        ]
        self.assertEqual(
            find_direct_release_notes_url(notes, 29695, 1001),
            "https://learn.microsoft.com/en-us/windows-insider/release-notes/experimental-future-platforms/preview-build-29695-1001",
        )

    def test_does_not_use_flight_hub_or_another_build(self):
        notes = [
            {"source": "Microsoft Learn", "url": "https://learn.microsoft.com/en-us/windows-insider/flight-hub/"},
            {"source": "Microsoft Learn", "url": "https://learn.microsoft.com/en-us/windows-insider/release-notes/experimental-future-platforms/preview-build-29695-1002"},
        ]
        self.assertIsNone(find_direct_release_notes_url(notes, 29695, 1001))


if __name__ == "__main__":
    unittest.main()
