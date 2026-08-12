import asyncio
import unittest
from types import SimpleNamespace

from player.core.filters import argument, command


class FakeClient:
    def __init__(self, username="playerbot"):
        self.me = SimpleNamespace(username=username)


def message(text: str) -> SimpleNamespace:
    return SimpleNamespace(text=text, caption=None)


def matches(flt, text: str, client: FakeClient | None = None) -> SimpleNamespace | None:
    msg = message(text)
    ok = asyncio.run(flt(client or FakeClient(), msg))
    return msg if ok else None


class TestCommandFilter(unittest.TestCase):
    def setUp(self):
        self.filter = command(["play", "p"], bare=["پخش", "پخش ویدیو"])

    def test_slash_command(self):
        msg = matches(self.filter, "/play shadmehr")
        self.assertIsNotNone(msg)
        self.assertEqual(msg.command, ["play", "shadmehr"])
        self.assertEqual(argument(msg), "shadmehr")

    def test_other_prefixes(self):
        for prefix in "!.#":
            self.assertIsNotNone(matches(self.filter, f"{prefix}play song"))

    def test_alias_command(self):
        msg = matches(self.filter, "/p song name")
        self.assertIsNotNone(msg)
        self.assertEqual(argument(msg), "song name")

    def test_bot_username_suffix(self):
        self.assertIsNotNone(matches(self.filter, "/play@playerbot song"))
        self.assertIsNone(matches(self.filter, "/play@otherbot song"))

    def test_bare_persian_command(self):
        msg = matches(self.filter, "پخش شادمهر عقیلی")
        self.assertIsNotNone(msg)
        self.assertEqual(msg.command[0], "پخش")
        self.assertEqual(argument(msg), "شادمهر عقیلی")

    def test_multiword_persian_command_wins(self):
        msg = matches(self.filter, "پخش ویدیو کلیپ جدید")
        self.assertIsNotNone(msg)
        self.assertEqual(msg.command[0], "پخش ویدیو")
        self.assertEqual(argument(msg), "کلیپ جدید")

    def test_persian_with_prefix(self):
        self.assertIsNotNone(matches(self.filter, "/پخش آهنگ"))

    def test_no_match(self):
        self.assertIsNone(matches(self.filter, "hello there"))
        self.assertIsNone(matches(self.filter, "playing music"))
        self.assertIsNone(matches(self.filter, ""))
        self.assertIsNone(matches(self.filter, "/"))

    def test_bare_word_needs_boundary(self):
        self.assertIsNone(matches(self.filter, "پخشیدن آهنگ"))

    def test_command_without_arguments(self):
        msg = matches(self.filter, "/play")
        self.assertIsNotNone(msg)
        self.assertEqual(argument(msg), "")

    def test_caption_is_supported(self):
        msg = SimpleNamespace(text=None, caption="/play from caption")
        self.assertTrue(asyncio.run(self.filter(FakeClient(), msg)))
        self.assertEqual(argument(msg), "from caption")

    def test_client_without_me_attribute(self):
        bare_client = SimpleNamespace()
        self.assertTrue(asyncio.run(self.filter(bare_client, message("/play x"))))


if __name__ == "__main__":
    unittest.main()
