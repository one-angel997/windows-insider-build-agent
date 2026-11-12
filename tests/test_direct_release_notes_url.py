import unittest

from insider_agent import find_direct_release_notes_url


class DirectReleaseNotesUrlTests(unittest.TestCase):
    def test_selects_exact_ubr_when_available(self):
        exact = "https://learn.microsoft.com/en-us/windows-insider/release-notes/experimental-future-platforms/preview-build-29704-1010"
        base = "https://learn.microsoft.com/en-us/windows-insider/release-notes/experimental-future-platforms/preview-build-29704-1000"
        notes = [
            {"source": "Microsoft Learn", "url": base},
            {"source": "Microsoft Learn", "url": exact},
        ]
        self.assertEqual(find_direct_release_notes_url(notes, 29704, 1010), exact)

    def test_falls_back_to_base_ubr_1000(self):
        base = "https://learn.microsoft.com/en-us/windows-insider/release-notes/experimental-future-platforms/preview-build-29704-1000"
        notes = [{"source": "Microsoft Learn", "url": base}]
        self.assertEqual(find_direct_release_notes_url(notes, 29704, 1010), base)

    def test_does_not_use_flight_hub_or_another_build(self):
        notes = [
            {"source": "Microsoft Learn", "url": "https://learn.microsoft.com/en-us/windows-insider/flight-hub/"},
            {"source": "Microsoft Learn", "url": "https://learn.microsoft.com/en-us/windows-insider/release-notes/experimental-future-platforms/preview-build-29705-1000"},
        ]
        self.assertIsNone(find_direct_release_notes_url(notes, 29704, 1010))


if __name__ == "__main__":
    unittest.main()
