import unittest

from player.utils.formatters import (
    human_bytes,
    human_timedelta,
    progress_bar,
    seconds_to_time,
    shorten,
    time_to_seconds,
    to_latin_digits,
)


class TestSecondsToTime(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(seconds_to_time(0), "0:00")
        self.assertEqual(seconds_to_time(5), "0:05")
        self.assertEqual(seconds_to_time(65), "1:05")
        self.assertEqual(seconds_to_time(3600), "1:00:00")
        self.assertEqual(seconds_to_time(3725), "1:02:05")

    def test_invalid(self):
        self.assertEqual(seconds_to_time(None), "0:00")
        self.assertEqual(seconds_to_time(-10), "0:00")
        self.assertEqual(seconds_to_time("abc"), "0:00")


class TestTimeToSeconds(unittest.TestCase):
    def test_colon_format(self):
        self.assertEqual(time_to_seconds("1:05"), 65)
        self.assertEqual(time_to_seconds("1:02:05"), 3725)

    def test_plain_and_units(self):
        self.assertEqual(time_to_seconds("90"), 90)
        self.assertEqual(time_to_seconds("2m"), 120)
        self.assertEqual(time_to_seconds("1h"), 3600)

    def test_persian_digits(self):
        self.assertEqual(time_to_seconds("۹۰"), 90)
        self.assertEqual(time_to_seconds("۱:۳۰"), 90)

    def test_empty(self):
        self.assertEqual(time_to_seconds(""), 0)
        self.assertEqual(time_to_seconds(None), 0)


class TestMisc(unittest.TestCase):
    def test_human_bytes(self):
        self.assertEqual(human_bytes(512), "512B")
        self.assertEqual(human_bytes(2048), "2.0KB")
        self.assertTrue(human_bytes(5 * 1024 * 1024).endswith("MB"))

    def test_progress_bar_length(self):
        bar = progress_bar(30, 60, length=10)
        self.assertEqual(len(bar), 10)
        self.assertIn("🔘", bar)

    def test_progress_bar_live(self):
        self.assertTrue(progress_bar(10, 0).startswith("🔴"))

    def test_human_timedelta(self):
        self.assertEqual(human_timedelta(0), "0s")
        self.assertIn("m", human_timedelta(3700))

    def test_shorten(self):
        self.assertEqual(shorten("abc", 10), "abc")
        self.assertEqual(len(shorten("a" * 50, 10)), 10)

    def test_to_latin_digits(self):
        self.assertEqual(to_latin_digits("۱۲۳"), "123")


if __name__ == "__main__":
    unittest.main()
