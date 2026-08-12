import re
import unittest
from dataclasses import dataclass

from pyrogram.handlers import CallbackQueryHandler
from pyrogram.handlers.handler import Handler

from player.utils import keyboards


@dataclass
class _FakeChannel:
    name: str


@dataclass
class _FakeCategory:
    id: str
    title: str
    channels: list


def _callback_data(markup) -> list[str]:
    return [
        button.callback_data
        for row in markup.inline_keyboard
        for button in row
        if button.callback_data
    ]


def _all_button_data() -> set[str]:
    """همهٔ callback_data‌هایی که ربات ممکن است در دکمه‌ها بفرستد."""
    markups = [
        keyboards.start_panel("fa", "playerbot"),
        keyboards.help_panel("fa"),
        keyboards.help_back("fa"),
        keyboards.player_panel("fa", paused=False, muted=False),
        keyboards.player_panel("fa", paused=True, muted=True),
        keyboards.queue_panel("fa"),
        keyboards.language_panel("fa"),
        keyboards.close_only("fa"),
        keyboards.search_results("fa", "tok", 6),
        keyboards.search_results("fa", "tok", 6, video=True),
        keyboards.search_actions("fa", "tok", 0),
        keyboards.hotseat_panel("fa"),
        keyboards.hotseat_panel("fa", paused=True),
        keyboards.settings_panel(
            "fa",
            {
                "play_mode": "admins",
                "auto_leave": True,
                "now_playing_message": False,
                "language_name": "فارسی",
            },
        ),
        keyboards.player_home("fa"),
        keyboards.panel_language("fa"),
        keyboards.live_categories(
            "fa", [_FakeCategory(id="sport", title="ورزشی", channels=[])]
        ),
        keyboards.live_channels(
            "fa", "sport", [_FakeChannel(name="شبکهٔ ۱"), _FakeChannel(name="شبکهٔ ۲")]
        ),
    ]
    markups += [
        keyboards.player_section("fa", section, {})
        for section in keyboards.PANEL_SECTIONS
    ]
    data: set[str] = set()
    for markup in markups:
        data.update(_callback_data(markup))
    return data


def _regex_patterns(flt, found: list[re.Pattern]) -> list[re.Pattern]:
    """استخراج الگوهای regex از یک فیلتر (که ممکن است ترکیبی باشد)."""
    pattern = getattr(flt, "p", None)
    if isinstance(pattern, re.Pattern):
        found.append(pattern)
    for attribute in ("base", "other"):
        nested = getattr(flt, attribute, None)
        if nested is not None:
            _regex_patterns(nested, found)
    return found


class TestPluginLoader(unittest.TestCase):
    """بارگذار پلاگین‌ها باید همهٔ هندلرها را قطعی (بدون نیاز به حلقهٔ رویداد) ثبت کند."""

    @classmethod
    def setUpClass(cls):
        from player.core import clients

        cls.clients = clients
        cls.registered = clients.load_plugins()

    def test_handlers_are_registered(self):
        groups = self.clients.bot.dispatcher.groups
        total = sum(len(handlers) for handlers in groups.values())
        self.assertGreater(total, 30)
        self.assertEqual(total, self.registered)

    def test_groups_are_sorted_and_contain_handlers(self):
        groups = self.clients.bot.dispatcher.groups
        self.assertEqual(list(groups), sorted(groups))
        for handlers in groups.values():
            for handler in handlers:
                self.assertIsInstance(handler, Handler)

    def test_every_button_has_a_handler(self):
        """هیچ دکمه‌ای نباید بی‌پاسخ بماند (دکمهٔ مرده)."""
        patterns: list[re.Pattern] = []
        for handlers in self.clients.bot.dispatcher.groups.values():
            for handler in handlers:
                if isinstance(handler, CallbackQueryHandler) and handler.filters is not None:
                    _regex_patterns(handler.filters, patterns)
        self.assertTrue(patterns, "هیچ هندلر دکمه‌ای پیدا نشد")

        for data in sorted(_all_button_data()):
            with self.subTest(data=data):
                self.assertTrue(
                    any(pattern.search(data) for pattern in patterns),
                    f"دکمهٔ بدون هندلر: {data}",
                )

    def test_loading_twice_does_not_duplicate(self):
        before = sum(len(h) for h in self.clients.bot.dispatcher.groups.values())
        self.assertEqual(self.clients.load_plugins(), before)
        after = sum(len(h) for h in self.clients.bot.dispatcher.groups.values())
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
