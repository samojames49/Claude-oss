import copy
import json
import tempfile
import unittest
from pathlib import Path

from player import config
from player.platforms import livetv


SAMPLE = {
    "categories": [
        {
            "id": "sport",
            "title": "⚽️ ورزشی",
            "channels": [
                {"name": "Sport One", "url": "https://example.com/one.m3u8"},
                {"name": "Sport Two", "url": "https://example.com/two.m3u8", "video": False},
            ],
        },
        {
            "id": "empty",
            "title": "بدون شبکه",
            "channels": [],
        },
        {
            "id": "news",
            "title": "📰 خبری",
            "channels": [
                {"name": "News", "url": "https://example.com/news.m3u8"},
                {"name": "بی‌نام", "url": ""},
            ],
        },
    ]
}


class TestLiveTv(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "live.json"
        self.data = copy.deepcopy(SAMPLE)
        self.path.write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")
        self._backup = config.LIVE_CHANNELS_FILE
        config.LIVE_CHANNELS_FILE = str(self.path)
        livetv._CACHE = None

    def tearDown(self):
        config.LIVE_CHANNELS_FILE = self._backup
        livetv._CACHE = None
        self.tmp.cleanup()

    def test_empty_categories_are_dropped(self):
        ids = [entry.id for entry in livetv.categories()]
        self.assertEqual(ids, ["sport", "news"])

    def test_channels_without_url_are_dropped(self):
        news = livetv.category("news")
        self.assertEqual([channel.name for channel in news.channels], ["News"])

    def test_total_channels(self):
        self.assertEqual(livetv.total_channels(), 3)

    def test_channel_lookup_by_index(self):
        channel = livetv.channel("sport", 1)
        self.assertEqual(channel.name, "Sport Two")
        self.assertFalse(channel.video)
        self.assertIsNone(livetv.channel("sport", 5))
        self.assertIsNone(livetv.channel("nope", 0))

    def test_search_is_case_insensitive(self):
        found = livetv.search("sport")
        self.assertEqual(len(found), 2)
        self.assertEqual(livetv.search("  "), [])
        self.assertEqual(livetv.search("nothing"), [])

    def test_track_from_channel_is_live_and_keeps_video_flag(self):
        track = livetv.channel("sport", 0).to_track(requester_id=5, requester_name="علی")
        self.assertTrue(track.is_live)
        self.assertEqual(track.kind, "live")
        self.assertTrue(track.video)
        self.assertEqual(track.duration, 0)
        self.assertEqual(track.requester_id, 5)

    def test_missing_file_returns_empty_list(self):
        config.LIVE_CHANNELS_FILE = str(Path(self.tmp.name) / "absent.json")
        livetv._CACHE = None
        self.assertEqual(livetv.categories(), [])

    def test_broken_file_returns_empty_list(self):
        self.path.write_text("{not json", encoding="utf-8")
        livetv._CACHE = None
        self.assertEqual(livetv.categories(), [])

    def test_reload_picks_up_edits(self):
        self.assertEqual(livetv.total_channels(), 3)
        self.data["categories"][0]["channels"].append(
            {"name": "Sport Three", "url": "https://example.com/three.m3u8"}
        )
        self.path.write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")
        livetv.load(force=True)
        self.assertEqual(livetv.total_channels(), 4)

    def test_shipped_file_is_valid(self):
        config.LIVE_CHANNELS_FILE = ""
        livetv._CACHE = None
        categories = livetv.load(force=True)
        self.assertTrue(categories, "فایل پیش‌فرض شبکه‌ها باید حداقل یک دسته داشته باشد")
        for entry in categories:
            with self.subTest(category=entry.id):
                self.assertTrue(entry.channels)
                for channel in entry.channels:
                    self.assertTrue(channel.url.startswith("http"))


if __name__ == "__main__":
    unittest.main()
