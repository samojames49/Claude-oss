import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from player.core.db import Database


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "db.json"
        self.db = Database(self.path)
        self.db.load()

    def tearDown(self):
        self.tmp.cleanup()

    def test_chat_registration(self):
        self.assertTrue(self.db.add_chat(-100, "گروه تست"))
        self.assertFalse(self.db.add_chat(-100, "گروه تست"))
        self.assertTrue(self.db.is_served_chat(-100))
        self.assertEqual(self.db.served_chats(), [-100])
        self.db.remove_chat(-100)
        self.assertFalse(self.db.is_served_chat(-100))

    def test_user_registration(self):
        self.assertTrue(self.db.add_user(5, "علی"))
        self.assertFalse(self.db.add_user(5, "علی"))
        self.assertEqual(self.db.served_users(), [5])

    def test_chat_settings(self):
        self.assertEqual(self.db.chat_setting(-100, "play_mode", "everyone"), "everyone")
        self.db.set_chat_setting(-100, "play_mode", "admins")
        self.assertEqual(self.db.chat_setting(-100, "play_mode", "everyone"), "admins")

    def test_reading_settings_does_not_register_chat(self):
        """خواندن تنظیمات (مثلاً برای زبانِ یک چت خصوصی) نباید گروه جدیدی بسازد."""
        self.assertEqual(self.db.chat_setting(123456, "language", "fa"), "fa")
        self.assertIsNone(self.db.get_chat(123456))
        self.assertEqual(self.db.served_chats(), [])
        self.assertFalse(self.db.is_served_chat(123456))

    def test_chat_setting_falls_back_to_default_for_missing_key(self):
        self.db.add_chat(-100, "گروه")
        self.db.chat(-100).pop("play_mode", None)
        self.assertEqual(self.db.chat_setting(-100, "play_mode", "everyone"), "everyone")

    def test_auth_users(self):
        self.assertTrue(self.db.add_auth_user(-100, 7, "کاربر"))
        self.assertFalse(self.db.add_auth_user(-100, 7, "کاربر"))
        self.assertTrue(self.db.is_auth_user(-100, 7))
        self.assertTrue(self.db.remove_auth_user(-100, 7))
        self.assertFalse(self.db.is_auth_user(-100, 7))

    def test_sudo(self):
        self.assertTrue(self.db.add_sudo(9))
        self.assertTrue(self.db.is_sudo(9))
        self.assertFalse(self.db.add_sudo(9))
        self.assertTrue(self.db.remove_sudo(9))
        self.assertFalse(self.db.is_sudo(9))

    def test_blocking(self):
        self.assertTrue(self.db.block_user(3))
        self.assertTrue(self.db.is_blocked_user(3))
        self.assertTrue(self.db.unblock_user(3))
        self.assertTrue(self.db.block_chat(-5))
        self.assertTrue(self.db.is_blocked_chat(-5))
        self.assertTrue(self.db.unblock_chat(-5))

    def test_maintenance_setting(self):
        self.assertFalse(self.db.maintenance)
        self.db.set_setting("maintenance", True)
        self.assertTrue(self.db.maintenance)

    def test_play_counters(self):
        self.db.count_play(-100, "آهنگ الف")
        self.db.count_play(-100, "آهنگ الف")
        self.db.count_play(-100, "آهنگ ب")
        self.assertEqual(self.db.total_plays(), 3)
        self.assertEqual(self.db.top_tracks(1), [("آهنگ الف", 2)])
        self.assertEqual(self.db.chat(-100)["plays"], 3)

    def test_atomic_save_and_reload(self):
        self.db.add_chat(-100, "گروه")
        self.db.set_chat_setting(-100, "language", "en")
        asyncio.run(self.db.save())

        self.assertTrue(self.path.exists())
        with self.path.open(encoding="utf-8") as handle:
            raw = json.load(handle)
        self.assertIn("-100", raw["chats"])

        fresh = Database(self.path)
        fresh.load()
        self.assertEqual(fresh.chat_setting(-100, "language", "fa"), "en")

    def test_corrupt_file_is_recovered(self):
        self.path.write_text("{not json", encoding="utf-8")
        fresh = Database(self.path)
        fresh.load()
        self.assertEqual(fresh.served_chats(), [])
        self.assertTrue(self.path.with_suffix(".corrupt.json").exists())


if __name__ == "__main__":
    unittest.main()
