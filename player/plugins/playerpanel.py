"""«پنل پلیر»: پنل دکمه‌ای همهٔ تنظیمات گروه، شامل بخش امنیت کال.

همان پنل با دستور «فهرست پیوی» به چت خصوصی مدیر هم فرستاده می‌شود؛ چون تلگرام دکمه‌های
یک پیام را به چت دیگر منتقل نمی‌کند، پنل خصوصی به گروه هدف گره خورده است.
"""

from __future__ import annotations

from pyrogram import Client, filters

from .. import config
from ..core.admins import can_control, play_mode
from ..core.db import db
from ..core.decorators import callback_handler, player_handler
from ..core.filters import command
from ..core.lang import strings_for
from ..core.security import min_age_days
from ..strings import LANGUAGES, Strings, language_names
from ..utils.keyboards import (
    PANEL_TOGGLES,
    panel_language,
    player_home,
    player_section,
)

# گروهی که پنل خصوصی هر مدیر روی آن باز است
_PRIVATE_TARGET: dict[int, int] = {}

BOOLEAN_KEYS = (
    "auto_leave",
    "now_playing_message",
    "play_in_channel",
    "call_stats",
    "call_stats_auto",
    "call_security",
    "security_mute_on_join",
    "security_report",
    "security_summary",
    "security_owners_access",
    "classic_mode",
    "auto_clear",
)

DEFAULTS = {
    "auto_leave": lambda: config.AUTO_LEAVE_ASSISTANT,
    "now_playing_message": lambda: True,
    "play_in_channel": lambda: False,
    "call_stats": lambda: config.CALL_STATS_ENABLED,
    "call_stats_auto": lambda: False,
    "call_security": lambda: config.CALL_SECURITY_ENABLED,
    "security_mute_on_join": lambda: False,
    "security_report": lambda: True,
    "security_summary": lambda: True,
    "security_owners_access": lambda: True,
    "classic_mode": lambda: False,
    "auto_clear": lambda: False,
}


def _flag(chat_id: int, key: str) -> bool:
    return bool(db.chat_setting(chat_id, key, DEFAULTS[key]()))


def panel_values(chat_id: int, s: Strings) -> dict[str, str]:
    """متن نمایشی مقدار هر تنظیم برای دکمه‌ها."""
    on_off = lambda flag: s("settings_on") if flag else s("settings_off")  # noqa: E731
    language = db.chat_setting(chat_id, "language", None) or config.DEFAULT_LANGUAGE
    reset = db.chat_setting(chat_id, "call_stats_reset", "") or ""
    values = {key: on_off(_flag(chat_id, key)) for key in BOOLEAN_KEYS}
    values["play_mode"] = (
        s("settings_play_mode_admins")
        if play_mode(chat_id) == "admins"
        else s("settings_play_mode_everyone")
    )
    values["call_stats_reset"] = s(f"panel_reset_{reset or 'off'}")
    values["security_min_age_days"] = s("panel_days", days=min_age_days(chat_id))
    values["language"] = language_names().get(language, language)
    return values


def section_text(chat_id: int, s: Strings, section: str, title: str) -> str:
    return s("panel_section_header", section=s(f"panel_section_{section}"), chat=title)


def home_text(chat_id: int, s: Strings, title: str) -> str:
    return s(
        "panel_home",
        chat=title,
        play_mode=(
            s("settings_play_mode_admins")
            if play_mode(chat_id) == "admins"
            else s("settings_play_mode_everyone")
        ),
        stats=s("settings_on") if _flag(chat_id, "call_stats") else s("settings_off"),
        security=s("settings_on") if _flag(chat_id, "call_security") else s("settings_off"),
        channel=(
            db.chat_setting(chat_id, "player_channel", 0) or s("panel_no_channel")
        ),
    )


@Client.on_message(
    command(["playerpanel", "panel"], bare=["پنل پلیر", "پنل", "player panel"]) & filters.group,
    group=1,
)
@player_handler(admin_only=True)
async def player_panel_command(_client: Client, message, s):
    chat_id = message.chat.id
    await message.reply_text(
        home_text(chat_id, s, message.chat.title or "-"),
        reply_markup=player_home(s.language),
    )


@Client.on_message(
    command(["menupv", "pvmenu"], bare=["فهرست پیوی", "منوی پیوی", "menupv"]) & filters.group,
    group=1,
)
@player_handler(admin_only=True)
async def menu_pv_command(client: Client, message, s):
    """ارسال پنل تنظیمات گروه به چت خصوصی مدیر."""
    chat_id = message.chat.id
    user = message.from_user
    if user is None:
        return
    _PRIVATE_TARGET[user.id] = chat_id
    try:
        await client.send_message(
            user.id,
            home_text(chat_id, s, message.chat.title or "-"),
            reply_markup=player_home(s.language),
        )
    except Exception:  # noqa: BLE001
        await message.reply_text(s("menupv_failed"))
        return
    await message.reply_text(s("menupv_sent"))


@Client.on_callback_query(filters.regex(r"^pnl:"))
@callback_handler()
async def panel_callback(_client: Client, query, s):
    parts = query.data.split(":")
    action = parts[1] if len(parts) > 1 else "home"
    chat_id = _panel_chat(query)
    if chat_id is None:
        await query.answer(s("panel_expired"), show_alert=True)
        return

    user = query.from_user
    if user is None or not await can_control(chat_id, user.id):
        await query.answer(s("callback_admin_only"), show_alert=True)
        return

    if action == "home":
        await _render_home(query, chat_id)
        await query.answer()
        return

    if action == "sec":
        section = parts[2] if len(parts) > 2 else "play"
        if section not in PANEL_TOGGLES:
            await query.answer()
            return
        if section == "security" and not await _security_allowed(chat_id, user.id):
            await query.answer(s("panel_owner_only"), show_alert=True)
            return
        await _render_section(query, chat_id, section)
        await query.answer()
        return

    if action == "age":
        if not await _security_allowed(chat_id, user.id):
            await query.answer(s("panel_owner_only"), show_alert=True)
            return
        days = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 7
        db.set_chat_setting(chat_id, "security_min_age_days", days)
        await _render_section(query, chat_id, "security")
        await query.answer(strings_for(chat_id)("security_age_set", days=days))
        return

    if action == "lang":
        code = parts[2] if len(parts) > 2 else ""
        if code not in LANGUAGES:
            await query.answer()
            return
        db.set_chat_setting(chat_id, "language", code)
        await _render_section(query, chat_id, "look")
        await query.answer(Strings(code)("language_changed", language=language_names()[code]))
        return

    if action == "t":
        key = parts[2] if len(parts) > 2 else ""
        section = _section_of(key)
        if section is None:
            await query.answer()
            return
        if section == "security" and not await _security_allowed(chat_id, user.id):
            await query.answer(s("panel_owner_only"), show_alert=True)
            return

        if key == "language":
            await query.message.edit_reply_markup(reply_markup=panel_language(s.language))
            await query.answer()
            return
        if not _apply_toggle(chat_id, key, s):
            await query.answer(s("play_channel_missing"), show_alert=True)
            return
        await _render_section(query, chat_id, section)
        await query.answer(strings_for(chat_id)("callback_done"))


def _apply_toggle(chat_id: int, key: str, s: Strings) -> bool:
    """تغییر مقدار یک تنظیم؛ False یعنی تغییر مجاز نبود."""
    if key == "play_mode":
        current = play_mode(chat_id)
        db.set_chat_setting(chat_id, "play_mode", "everyone" if current == "admins" else "admins")
        return True
    if key == "call_stats_reset":
        order = ["", "daily", "monthly"]
        current = db.chat_setting(chat_id, "call_stats_reset", "") or ""
        nxt = order[(order.index(current) + 1) % len(order)] if current in order else "daily"
        db.set_chat_setting(chat_id, "call_stats_reset", nxt)
        return True
    if key == "security_min_age_days":
        current = min_age_days(chat_id)
        db.set_chat_setting(chat_id, "security_min_age_days", 0 if current >= 30 else current + 7)
        return True
    if key == "play_in_channel":
        if not _flag(chat_id, "play_in_channel") and not db.chat_setting(
            chat_id, "player_channel", 0
        ):
            return False
        db.set_chat_setting(chat_id, "play_in_channel", not _flag(chat_id, "play_in_channel"))
        return True
    if key in BOOLEAN_KEYS:
        db.set_chat_setting(chat_id, key, not _flag(chat_id, key))
        return True
    return False


def _section_of(key: str) -> str | None:
    for section, keys in PANEL_TOGGLES.items():
        if key in keys:
            return section
    return None


async def _security_allowed(chat_id: int, user_id: int) -> bool:
    """امنیت کال را مالک گروه همیشه و سایر مدیران فقط با «دسترسی مالکان» می‌بینند."""
    if db.is_sudo(user_id):
        return True
    if _flag(chat_id, "security_owners_access"):
        return await can_control(chat_id, user_id)
    from pyrogram.enums import ChatMemberStatus

    from ..core.clients import bot

    try:
        member = await bot.get_chat_member(chat_id, user_id)
    except Exception:  # noqa: BLE001
        return False
    return member.status == ChatMemberStatus.OWNER


def _panel_chat(query) -> int | None:
    """گروه هدف پنل؛ در چت خصوصی از آخرین گروهی که «فهرست پیوی» زده شده."""
    chat = getattr(query.message, "chat", None)
    if chat is None:
        return None
    if chat.type.name in ("GROUP", "SUPERGROUP"):
        return chat.id
    user = query.from_user
    return _PRIVATE_TARGET.get(user.id) if user else None


async def _render_home(query, chat_id: int) -> None:
    s = strings_for(chat_id)
    title = await _chat_title(chat_id, query)
    await query.message.edit_text(
        home_text(chat_id, s, title), reply_markup=player_home(s.language)
    )


async def _render_section(query, chat_id: int, section: str) -> None:
    s = strings_for(chat_id)
    title = await _chat_title(chat_id, query)
    await query.message.edit_text(
        section_text(chat_id, s, section, title),
        reply_markup=player_section(s.language, section, panel_values(chat_id, s)),
    )


async def _chat_title(chat_id: int, query) -> str:
    chat = getattr(query.message, "chat", None)
    if chat is not None and chat.id == chat_id and chat.title:
        return chat.title
    return db.chat_setting(chat_id, "title", "") or str(chat_id)


def language_codes() -> list[str]:
    return list(LANGUAGES)
