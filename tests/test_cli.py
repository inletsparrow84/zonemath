"""Tests for the zonemath.__main__ command-line entry point."""

import contextlib
import io
import unittest

from zonemath.__main__ import main


class ListZonesTests(unittest.TestCase):
    def test_list_zones_with_pattern_filters_output(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["--list-zones", "chatham"])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue().splitlines(), ["Pacific/Chatham"])

    def test_list_zones_without_pattern_lists_everything(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["--list-zones"])
        self.assertEqual(code, 0)
        names = out.getvalue().splitlines()
        self.assertIn("America/New_York", names)
        self.assertGreater(len(names), 100)

    def test_list_zones_ignores_missing_positional_arguments(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["--list-zones", "chatham"])
        self.assertEqual(code, 0)


class MissingArgumentsTests(unittest.TestCase):
    def test_missing_positionals_without_list_zones_is_an_error(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as ctx:
                main([])
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertIn("required", err.getvalue())


class ConversionTests(unittest.TestCase):
    def test_ordinary_conversion_prints_target_time(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["2026-06-15 09:00", "America/New_York", "Asia/Tokyo"])
        self.assertEqual(code, 0)
        self.assertIn("2026-06-15 22:00:00", out.getvalue())


if __name__ == "__main__":
    unittest.main()
