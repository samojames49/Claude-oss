import unittest

from player.core.queues import QueueManager
from player.core.track import Track


def make_track(title: str, duration: int = 100) -> Track:
    return Track(title=title, source=f"/tmp/{title}.mp3", duration=duration)


class TestQueueManager(unittest.TestCase):
    def setUp(self):
        self.queues = QueueManager()
        self.chat = -100123

    def test_add_and_size(self):
        self.assertEqual(self.queues.size(self.chat), 0)
        self.assertEqual(self.queues.add(self.chat, make_track("a")), 1)
        self.assertEqual(self.queues.add(self.chat, make_track("b")), 2)
        self.assertEqual(self.queues.size(self.chat), 2)

    def test_pop_order(self):
        self.queues.add(self.chat, make_track("a"))
        self.queues.add(self.chat, make_track("b"))
        self.assertEqual(self.queues.pop_next(self.chat).title, "a")
        self.assertEqual(self.queues.pop_next(self.chat).title, "b")
        self.assertIsNone(self.queues.pop_next(self.chat))

    def test_add_next_jumps_queue(self):
        self.queues.add(self.chat, make_track("a"))
        self.queues.add_next(self.chat, make_track("z"))
        self.assertEqual(self.queues.pop_next(self.chat).title, "z")

    def test_loop_repeats_current(self):
        current = make_track("current")
        self.queues.set_current(self.chat, current)
        self.queues.add(self.chat, make_track("next"))
        self.queues.set_loop(self.chat, 2)

        first = self.queues.pop_next(self.chat)
        self.assertEqual(first.title, "current")
        self.assertEqual(self.queues.loop(self.chat), 1)

        second = self.queues.pop_next(self.chat)
        self.assertEqual(second.title, "current")
        self.assertEqual(self.queues.loop(self.chat), 0)

        third = self.queues.pop_next(self.chat)
        self.assertEqual(third.title, "next")

    def test_loop_off(self):
        self.queues.set_current(self.chat, make_track("current"))
        self.queues.set_loop(self.chat, 3)
        self.assertEqual(self.queues.set_loop(self.chat, 0), 0)
        self.assertIsNone(self.queues.pop_next(self.chat))

    def test_remove(self):
        self.queues.add(self.chat, make_track("a"))
        self.queues.add(self.chat, make_track("b"))
        self.assertIsNone(self.queues.remove(self.chat, 5))
        self.assertIsNone(self.queues.remove(self.chat, 0))
        removed = self.queues.remove(self.chat, 2)
        self.assertEqual(removed.title, "b")
        self.assertEqual(self.queues.size(self.chat), 1)

    def test_shuffle_keeps_items(self):
        for name in "abcde":
            self.queues.add(self.chat, make_track(name))
        self.assertEqual(self.queues.shuffle(self.chat), 5)
        titles = {track.title for track in self.queues.queue(self.chat)}
        self.assertEqual(titles, set("abcde"))

    def test_state_flags(self):
        self.queues.set_current(self.chat, make_track("a"))
        self.assertTrue(self.queues.is_active(self.chat))
        self.queues.set_paused(self.chat, True)
        self.assertTrue(self.queues.is_paused(self.chat))
        self.queues.set_muted(self.chat, True)
        self.assertTrue(self.queues.is_muted(self.chat))
        self.queues.set_volume(self.chat, 150)
        self.assertEqual(self.queues.volume(self.chat), 150)

    def test_reset_clears_everything(self):
        self.queues.set_current(self.chat, make_track("a"))
        self.queues.add(self.chat, make_track("b"))
        self.queues.set_panel(self.chat, 42)
        self.queues.reset(self.chat)
        self.assertFalse(self.queues.is_active(self.chat))
        self.assertEqual(self.queues.size(self.chat), 0)
        self.assertIsNone(self.queues.panel(self.chat))
        self.assertEqual(self.queues.volume(self.chat), 100)

    def test_video_chats(self):
        video_track = make_track("v")
        video_track.video = True
        self.queues.set_current(self.chat, video_track)
        self.queues.set_current(-2, make_track("audio"))
        self.assertEqual(self.queues.video_chats(), [self.chat])

    def test_empty_tracking(self):
        first = self.queues.mark_empty(self.chat)
        self.assertEqual(first, self.queues.mark_empty(self.chat))
        self.queues.clear_empty(self.chat)
        self.assertNotEqual(first, self.queues.mark_empty(self.chat) + 1)


class TestTrack(unittest.TestCase):
    def test_duration_text(self):
        self.assertEqual(make_track("a", 65).duration_text, "1:05")
        self.assertEqual(make_track("a", 0).duration_text, "∞")

    def test_kind_key(self):
        track = make_track("a", 60)
        self.assertEqual(track.kind_key(), "stream_kind_audio")
        track.video = True
        self.assertEqual(track.kind_key(), "stream_kind_video")
        live = make_track("b", 0)
        self.assertEqual(live.kind_key(), "stream_kind_live")

    def test_clone_is_independent(self):
        track = make_track("a")
        track.extra["x"] = 1
        clone = track.clone()
        clone.extra["x"] = 2
        self.assertEqual(track.extra["x"], 1)
        self.assertEqual(clone.title, "a")

    def test_short_title(self):
        self.assertTrue(len(make_track("t" * 100).short_title) <= 45)


if __name__ == "__main__":
    unittest.main()
