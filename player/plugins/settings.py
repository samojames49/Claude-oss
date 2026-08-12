"""پنل تنظیمات گروه."""

from __future__ import annotations

from pyrogram import Client, filters

from .. import config
from ..core.admins import play_mode
from ..core.db import db
from ..core.decorators import callback_handler, player_handler
from ..core.filters import command
from ..strings import LANGUAGES, Strings, language_names
from ..utils.keyboards import language_panel, settings_panel


def _settings_state(chat_id: int) -> dict:
    language = db.chat_setting(chat_id, "language", None) or config.DEFAULT_LANGUAGE
    if language not in LANGUAGES:
        language = "fa"
    return {
        "play_mode": play_mode(chat_id),
        "language": language,
        "language_name": language_names().get(language, language),
        "auto_leave": bool(db.chat_setting(chat_id, "auto_leave", config.AUTO_LEAVE_ASSISTANT)),
        "now_playing_message": bool(db.chat_setting(chat_id, "now_playing_message", True)),
        "duration_limit": db.chat_setting(chat_id, "duration_limit", config.DURATION_LIMIT_MINUTES),
    }


def _settings_text(chat_title: str, s: Strings, state: dict) -> str:
    return s(
        "settings_header",
        chat=chat_title,
        play_mode=(
            s("settings_play_mode_admins")
            if state["play_mode"] == "admins"
            else s("settings_play_mode_everyone")
        ),
        language=state["language_name"],
        auto_leave=s("settings_on") if state["auto_leave"] else s("settings_off"),
        now_playing=s("settings_on") if state["now_playing_message"] else s("settings_off"),
        duration_limit=state["duration_limit"],
    )


@Client.on_message(command(["settings", "setting"], bare=["تنظیمات"]) & filters.group, group=1)
@player_handler(admin_only=True)
async def settings_command(_client: Client, message, s):
    state = _settings_state(message.chat.id)
    await message.reply_text(
        _settings_text(message.chat.title or "-", s, state),
        reply_markup=settings_panel(s.language, state),
    )


@Client.on_callback_query(filters.regex(r"^set:"))
@callback_handler(admin_only=True)
async def settings_callback(_client: Client, query, s):
    action = query.data.split(":", 1)[1]
    chat_id = query.message.chat.id

    if action == "play_mode":
        current = play_mode(chat_id)
        db.set_chat_setting(chat_id, "play_mode", "everyone" if current == "admins" else "admins")
    elif action == "auto_leave":
        current = bool(db.chat_setting(chat_id, "auto_leave", config.AUTO_LEAVE_ASSISTANT))
        db.set_chat_setting(chat_id, "auto_leave", not current)
    elif action == "now_playing":
        current = bool(db.chat_setting(chat_id, "now_playing_message", True))
        db.set_chat_setting(chat_id, "now_playing_message", not current)
    elif action == "lang":
        await query.message.edit_reply_markup(reply_markup=language_panel(s.language))
        await query.answer()
        return

    state = _settings_state(chat_id)
    s = Strings(state["language"])
    await query.message.edit_text(
        _settings_text(query.message.chat.title or "-", s, state),
        reply_markup=settings_panel(s.language, state),
    )
    await query.answer(s("callback_done"))


@Client.on_callback_query(filters.regex(r"^lang:"))
@callback_handler(admin_only=True)
async def language_callback(_client: Client, query, s):
    code = query.data.split(":", 1)[1]
    if code not in LANGUAGES:
        await query.answer(s("err_generic", error=code), show_alert=True)
        return
    chat_id = query.message.chat.id
    db.set_chat_setting(chat_id, "language", code)
    s = Strings(code)
    state = _settings_state(chat_id)
    await query.message.edit_text(
        _settings_text(query.message.chat.title or "-", s, state),
        reply_markup=settings_panel(code, state),
    )
    await query.answer(s("language_changed", language=state["language_name"]))
