"""دکمه‌های شیشه‌ای (inline) ربات."""

from __future__ import annotations

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .. import config
from ..strings import Strings, language_names


def _button(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text, callback_data=data)


def start_panel(lang: str, bot_username: str) -> InlineKeyboardMarkup:
    s = Strings(lang)
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                s("button_add_group"),
                url=f"https://t.me/{bot_username}?startgroup=true",
            )
        ],
        [_button(s("button_help"), "help:home")],
    ]
    third: list[InlineKeyboardButton] = []
    if config.SUPPORT_CHAT:
        third.append(InlineKeyboardButton(s("button_support"), url=_link(config.SUPPORT_CHAT)))
    if config.SUPPORT_CHANNEL:
        third.append(InlineKeyboardButton(s("button_channel"), url=_link(config.SUPPORT_CHANNEL)))
    if third:
        rows.append(third)
    if config.OWNER_USERNAME:
        rows.append(
            [InlineKeyboardButton(s("button_owner"), url=_link(config.OWNER_USERNAME))]
        )
    return InlineKeyboardMarkup(rows)


def _link(value: str) -> str:
    value = value.strip()
    if value.startswith("http"):
        return value
    return f"https://t.me/{value.lstrip('@')}"


def help_panel(lang: str) -> InlineKeyboardMarkup:
    s = Strings(lang)
    return InlineKeyboardMarkup(
        [
            [
                _button("🎵 " + _section(lang, "help_play"), "help:play"),
                _button("🎛 " + _section(lang, "help_control"), "help:control"),
            ],
            [
                _button("📜 " + _section(lang, "help_queue"), "help:queue"),
                _button("🧰 " + _section(lang, "help_tools"), "help:tools"),
            ],
            [
                _button("⚙️ " + _section(lang, "help_admin"), "help:admin"),
                _button("🛡 " + _section(lang, "help_sudo"), "help:sudo"),
            ],
            [_button(s("button_close"), "close")],
        ]
    )


_SECTION_TITLES = {
    "help_play": {"fa": "پخش", "en": "Play"},
    "help_control": {"fa": "کنترل", "en": "Controls"},
    "help_queue": {"fa": "صف", "en": "Queue"},
    "help_tools": {"fa": "ابزار", "en": "Tools"},
    "help_admin": {"fa": "مدیریت", "en": "Admin"},
    "help_sudo": {"fa": "سودو", "en": "Sudo"},
}


def _section(lang: str, key: str) -> str:
    titles = _SECTION_TITLES.get(key, {})
    return titles.get(lang) or titles.get("en") or key


def help_back(lang: str) -> InlineKeyboardMarkup:
    s = Strings(lang)
    return InlineKeyboardMarkup(
        [
            [
                _button(s("button_back"), "help:home"),
                _button(s("button_close"), "close"),
            ]
        ]
    )


def player_panel(lang: str, *, paused: bool = False, muted: bool = False) -> InlineKeyboardMarkup:
    s = Strings(lang)
    play_pause = (
        _button(s("button_resume"), "ctl:resume")
        if paused
        else _button(s("button_pause"), "ctl:pause")
    )
    sound = (
        _button(s("button_unmute"), "ctl:unmute")
        if muted
        else _button(s("button_mute"), "ctl:mute")
    )
    return InlineKeyboardMarkup(
        [
            [play_pause, _button(s("button_skip"), "ctl:skip"), _button(s("button_stop"), "ctl:end")],
            [
                _button(s("button_vol_down"), "ctl:vol_down"),
                sound,
                _button(s("button_vol_up"), "ctl:vol_up"),
            ],
            [
                _button(s("button_queue"), "ctl:queue"),
                _button(s("button_loop"), "ctl:loop"),
                _button(s("button_shuffle"), "ctl:shuffle"),
            ],
            [_button(s("button_refresh"), "ctl:refresh"), _button(s("button_close"), "close")],
        ]
    )


def queue_panel(lang: str) -> InlineKeyboardMarkup:
    s = Strings(lang)
    return InlineKeyboardMarkup(
        [
            [
                _button(s("button_refresh"), "ctl:queue"),
                _button(s("button_close"), "close"),
            ]
        ]
    )


def settings_panel(lang: str, settings: dict) -> InlineKeyboardMarkup:
    s = Strings(lang)
    play_mode = (
        s("settings_play_mode_admins")
        if settings.get("play_mode") == "admins"
        else s("settings_play_mode_everyone")
    )
    on_off = lambda flag: s("settings_on") if flag else s("settings_off")  # noqa: E731
    return InlineKeyboardMarkup(
        [
            [_button(s("button_toggle_play_mode", value=play_mode), "set:play_mode")],
            [
                _button(
                    s("button_toggle_auto_leave", value=on_off(settings.get("auto_leave"))),
                    "set:auto_leave",
                )
            ],
            [
                _button(
                    s(
                        "button_toggle_now_playing",
                        value=on_off(settings.get("now_playing_message")),
                    ),
                    "set:now_playing",
                )
            ],
            [_button(s("button_language", value=settings.get("language_name", "")), "set:lang")],
            [_button(s("button_close"), "close")],
        ]
    )


def language_panel(lang: str) -> InlineKeyboardMarkup:
    s = Strings(lang)
    rows = [
        [_button(name, f"lang:{code}")] for code, name in language_names().items()
    ]
    rows.append([_button(s("button_back"), "set:home"), _button(s("button_close"), "close")])
    return InlineKeyboardMarkup(rows)


def search_results(lang: str, token: str, count: int, video: bool = False) -> InlineKeyboardMarkup:
    """دکمه‌های انتخاب نتیجهٔ جستجو؛ token کلید کش نتایج است."""
    s = Strings(lang)
    prefix = "vplay" if video else "play"
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for index in range(count):
        row.append(_button(str(index + 1), f"pick:{prefix}:{token}:{index}"))
        if len(row) == 5:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([_button(s("button_close"), "close")])
    return InlineKeyboardMarkup(rows)


def live_categories(lang: str, categories: list) -> InlineKeyboardMarkup:
    """منوی دستهٔ شبکه‌های پخش زنده."""
    s = Strings(lang)
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for entry in categories:
        row.append(_button(entry.title, f"live:cat:{entry.id}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([_button(s("button_close"), "close")])
    return InlineKeyboardMarkup(rows)


def live_channels(lang: str, category_id: str, channels: list) -> InlineKeyboardMarkup:
    """منوی شبکه‌های یک دسته؛ هر دکمه شمارهٔ شبکه را می‌فرستد."""
    s = Strings(lang)
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for index, item in enumerate(channels):
        row.append(_button(item.name, f"live:play:{category_id}:{index}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(
        [_button(s("button_back"), "live:home"), _button(s("button_close"), "close")]
    )
    return InlineKeyboardMarkup(rows)


def close_only(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[_button(Strings(lang)("button_close"), "close")]])
