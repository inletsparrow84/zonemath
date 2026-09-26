"""Table-driven tests for zonemath.core, focused on the awkward cases."""

import unittest
from datetime import datetime, timezone

from zonemath.core import NonexistentTimeError, convert, search_zones


class ConvertTests(unittest.TestCase):
    def test_ordinary_conversion(self):
        cases = [
            # (label, local_time, from_zone, to_zone, expected_target_isoformat)
            (
                "NY to London, summer, both on DST",
                datetime(2026, 6, 15, 12, 0),
                "America/New_York",
                "Europe/London",
                "2026-06-15T17:00:00+01:00",
            ),
            (
                "Kolkata half-hour offset, no DST",
                datetime(2026, 1, 15, 10, 0),
                "Asia/Kolkata",
                "UTC",
                "2026-01-15T04:30:00+00:00",
            ),
            (
                "Chatham Islands 45-minute offset, standard time",
                datetime(2026, 6, 15, 12, 0),
                "Pacific/Chatham",
                "UTC",
                "2026-06-14T23:15:00+00:00",
            ),
        ]
        for label, local_time, from_zone, to_zone, expected in cases:
            with self.subTest(label):
                result = convert(local_time, from_zone, to_zone)
                self.assertEqual(result.target.isoformat(), expected)
                self.assertFalse(result.is_ambiguous)

    def test_nonexistent_times_raise(self):
        cases = [
            # (label, local_time, from_zone)
            ("US spring-forward gap", datetime(2026, 3, 8, 2, 30), "America/New_York"),
            ("Samoa skipped this whole day in 2011", datetime(2011, 12, 30, 12, 0), "Pacific/Apia"),
        ]
        for label, local_time, from_zone in cases:
            with self.subTest(label):
                with self.assertRaises(NonexistentTimeError):
                    convert(local_time, from_zone, "UTC")

    def test_ambiguous_times_use_fold(self):
        cases = [
            # (label, local_time, zone, fold0_offset, fold1_offset)
            ("US fall-back", datetime(2026, 11, 1, 1, 30), "America/New_York", "-04:00", "-05:00"),
            (
                "Sydney fall-back (Southern Hemisphere, opposite month)",
                datetime(2026, 4, 5, 2, 30),
                "Australia/Sydney",
                "+11:00",
                "+10:00",
            ),
        ]
        for label, local_time, zone, fold0_offset, fold1_offset in cases:
            with self.subTest(label):
                result0 = convert(local_time, zone, "UTC", fold=0)
                result1 = convert(local_time, zone, "UTC", fold=1)
                self.assertTrue(result0.is_ambiguous)
                self.assertTrue(result1.is_ambiguous)
                self.assertEqual(result0.source.isoformat()[-6:], fold0_offset)
                self.assertEqual(result1.source.isoformat()[-6:], fold1_offset)

    def test_round_trip_is_stable_for_ordinary_times(self):
        original = datetime(2026, 6, 15, 10, 0)
        via_ny = convert(original, "Europe/London", "America/New_York")
        back = convert(via_ny.target.replace(tzinfo=None), "America/New_York", "Europe/London")
        self.assertEqual(back.target.replace(tzinfo=None), original)

    def test_aware_input_is_rejected(self):
        aware = datetime(2026, 1, 1, tzinfo=timezone.utc)
        with self.assertRaises(ValueError):
            convert(aware, "UTC", "America/New_York")


class SearchZonesTests(unittest.TestCase):
    def test_empty_pattern_returns_everything_sorted(self):
        results = search_zones()
        self.assertIn("America/New_York", results)
        self.assertIn("Pacific/Chatham", results)
        self.assertEqual(results, sorted(results))

    def test_pattern_filters_case_insensitively(self):
        self.assertEqual(search_zones("chatham"), ["Pacific/Chatham"])
        self.assertEqual(search_zones("CHATHAM"), ["Pacific/Chatham"])

    def test_pattern_matches_anywhere_in_the_name(self):
        results = search_zones("indian")
        self.assertIn("America/Indiana/Knox", results)

    def test_unmatched_pattern_returns_empty_list(self):
        self.assertEqual(search_zones("not_a_real_zone_fragment"), [])


if __name__ == "__main__":
    unittest.main()
