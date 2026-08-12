import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

from player.core import callstats
from player.core.db import Database


class TestCallStatsHelpers(unittest.TestCase):
    def test_last_days_starts_from_today(self):
        days = callstats.last_days(3)
        self.assertEqual(len(days), 3)
        self.assertEqual(days[0], date.today().isoformat())
        self.assertEqual(days[-1], (date.today() - timedelta(days=2)).isoformat())

    def test_last_days_is_bounded(self):
        self.assertEqual(len(callstats.last_days(0)), 1)
        self.assertLessEqual(len(callstats.last_days(999)), 40)

    def test_weekday_key_resolves_recent_date(self):
        for name in ("جمعه", "friday", "Friday", "fri"):
            with self.subTest(name=name):
                key = callstats.weekday_key(name)
                self.assertIsNotNone(key)
                self.assertEqual(date.fromisoformat(key).weekday(), 4)
                self.assertLessEqual(date.fromisoformat(key), date.today())

    def test_weekday_key_rejects_unknown(self):
        self.assertIsNone(callstats.weekday_key("فردا"))

    def test_all_persian_weekdays_are_mapped(self):
        names = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]
        mapped = {callstats.WEEKDAYS[name] for name in names}
        self.assertEqual(mapped, set(range(7)))

    def test_weekday_label_includes_persian_name(self):
        friday = callstats.weekday_key("جمعه")
        self.assertIn("جمعه", callstats.weekday_label(friday))


class TestCallStatsStorage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "db.json")
        self.db.load()

    def tearDown(self):
        self.tmp.cleanup()

    def test_time_accumulates_per_user_and_day(self):
        today = date.today().isoformat()
        self.db.add_call_time(-100, 7, 60, name="علی", day=today)
        self.db.add_call_time(-100, 7, 30, day=today)
        self.db.add_call_time(-100, 9, 45, name="سارا", day=today)
        totals = dict(self.db.call_totals(-100, [today]))
        self.assertEqual(totals, {7: 90, 9: 45})
        self.assertEqual(self.db.call_user_name(-100, 7), "علی")

    def test_totals_are_sorted_desc(self):
        today = date.today().isoformat()
        self.db.add_call_time(-100, 1, 10, day=today)
        self.db.add_call_time(-100, 2, 99, day=today)
        self.assertEqual([uid for uid, _ in self.db.call_totals(-100, [today])], [2, 1])

    def test_totals_span_multiple_days(self):
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        self.db.add_call_time(-100, 3, 20, day=today)
        self.db.add_call_time(-100, 3, 25, day=yesterday)
        self.assertEqual(dict(self.db.call_totals(-100, [today])), {3: 20})
        self.assertEqual(dict(self.db.call_totals(-100, [today, yesterday])), {3: 45})

    def test_zero_or_negative_time_is_ignored(self):
        today = date.today().isoformat()
        self.db.add_call_time(-100, 4, 0, day=today)
        self.db.add_call_time(-100, 4, -5, day=today)
        self.assertEqual(self.db.call_totals(-100, [today]), [])

    def test_reset_clears_days_and_names(self):
        today = date.today().isoformat()
        self.db.add_call_time(-100, 5, 60, name="رضا", day=today)
        self.assertEqual(self.db.reset_call_stats(-100), 1)
        self.assertEqual(self.db.call_totals(-100, [today]), [])
        self.assertEqual(self.db.call_user_name(-100, 5), "")

    def test_prune_keeps_recent_days_only(self):
        for offset in range(6):
            day = (date.today() - timedelta(days=offset)).isoformat()
            self.db.add_call_time(-100, 1, 10, day=day)
        self.db.prune_call_stats(-100, 3)
        self.assertEqual(len(self.db.call_recorded_days(-100)), 3)
        self.assertIn(date.today().isoformat(), self.db.call_recorded_days(-100))

    def test_daily_auto_reset_triggers_once_per_day(self):
        today = date.today().isoformat()
        self.db.set_chat_setting(-100, "call_stats_reset", "daily")
        self.db.add_call_time(-100, 1, 60, day=today)
        log = self.db.call_log(-100)
        log["last_reset"] = int((datetime.now() - timedelta(days=1)).timestamp())

        self.assertTrue(self.db.apply_call_stats_reset(-100))
        self.assertEqual(self.db.call_totals(-100, [today]), [])
        self.assertFalse(self.db.apply_call_stats_reset(-100))

    def test_monthly_auto_reset_ignores_same_month(self):
        today = date.today().isoformat()
        self.db.set_chat_setting(-100, "call_stats_reset", "monthly")
        self.db.add_call_time(-100, 1, 60, day=today)
        log = self.db.call_log(-100)
        log["last_reset"] = int((datetime.now() - timedelta(days=1)).timestamp())

        # یک روز قبل هنوز همان ماه است (مگر روز اول ماه باشد)
        if datetime.now().day > 1:
            self.assertFalse(self.db.apply_call_stats_reset(-100))
            self.assertEqual(dict(self.db.call_totals(-100, [today])), {1: 60})

        log["last_reset"] = int((datetime.now() - timedelta(days=62)).timestamp())
        self.assertTrue(self.db.apply_call_stats_reset(-100))

    def test_no_reset_period_never_resets(self):
        self.db.add_call_time(-100, 1, 60)
        self.assertFalse(self.db.apply_call_stats_reset(-100))
        self.assertTrue(self.db.call_totals(-100, [date.today().isoformat()]))


class TestLeaderboard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "db.json")
        self.db.load()
        self.today = date.today().isoformat()
        self._patch = callstats.db
        callstats.db = self.db

    def tearDown(self):
        callstats.db = self._patch
        self.tmp.cleanup()

    def test_accumulate_adds_for_every_present_user(self):
        callstats.accumulate(-100, [1, 2], 60, {1: "الف", 2: "ب"})
        callstats.accumulate(-100, [1], 60, {})
        self.assertEqual(dict(self.db.call_totals(-100, [self.today])), {1: 120, 2: 60})

    def test_leaderboard_respects_limit(self):
        for user_id in range(1, 6):
            self.db.add_call_time(-100, user_id, user_id * 10, day=self.today)
        top = callstats.leaderboard(-100, [self.today], limit=2)
        self.assertEqual([uid for uid, _ in top], [5, 4])

    def test_user_rank(self):
        self.db.add_call_time(-100, 1, 100, day=self.today)
        self.db.add_call_time(-100, 2, 50, day=self.today)
        self.assertEqual(callstats.user_rank(-100, 1, [self.today]), (1, 100, 2))
        self.assertEqual(callstats.user_rank(-100, 2, [self.today]), (2, 50, 2))
        self.assertEqual(callstats.user_rank(-100, 3, [self.today]), (0, 0, 2))

    def test_render_lists_users_with_clock_time(self):
        from player.strings import Strings

        self.db.add_call_time(-100, 1, 3661, name="علی", day=self.today)
        text = callstats.render(-100, Strings("fa"), [self.today], title="امروز")
        self.assertIn("01:01:01", text)
        self.assertIn("علی", text)

    def test_render_reports_empty_period(self):
        from player.strings import Strings

        text = callstats.render(-100, Strings("fa"), [self.today], title="امروز")
        self.assertEqual(text, Strings("fa")("callstats_empty"))


if __name__ == "__main__":
    unittest.main()
