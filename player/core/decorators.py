"""دکوریتورهای مشترک هندلرها: بررسی دسترسی، ثبت گروه/کاربر و مدیریت خطا."""

from __future__ import annotations

from functools import wraps

from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import CallbackQuery, Message

from .. import config
from ..strings import Strings
from ..utils.logger import get_logger
from .admins import can_control, can_play, is_group
from .db import db
from .errors import UserError
from .lang import strings_for
from .queues import queues
from .targets import playback_chat

LOGGER = get_logger("handlers")


def _user_name(user) -> str:
    if user is None:
        return ""
    name = " ".join(filter(None, [user.first_name, user.last_name])).strip()
    return name or (user.username or str(user.id))


def register_activity(message: Message) -> None:
    """ثبت گروه و کاربر برای آمار و پیام همگانی."""
    chat = getattr(message, "chat", None)
    user = getattr(message, "from_user", None)
    if chat is not None and chat.id and is_group(message):
        db.add_chat(chat.id, chat.title or "")
    elif chat is not None and user is not None and chat.id == user.id:
        db.add_user(user.id, _user_name(user))


def player_handler(
    *,
    group_only: bool = True,
    admin_only: bool = False,
    play_permission: bool = False,
    require_active: bool = False,
    sudo_only: bool = False,
):
    """دکوریتور هندلر پیام؛ تابع با امضای `(client, message, s)` صدا زده می‌شود."""

    def decorator(func):
        @wraps(func)
        async def wrapper(client, message: Message):
            chat = getattr(message, "chat", None)
            user = getattr(message, "from_user", None)
            chat_id = chat.id if chat else None
            s: Strings = strings_for(chat_id)

            try:
                register_activity(message)

                if user is not None and db.is_blocked_user(user.id) and not db.is_sudo(user.id):
                    await message.reply_text(s("err_blocked_user"))
                    return
                if chat_id and db.is_blocked_chat(chat_id):
                    return
                if db.maintenance and not (user and db.is_sudo(user.id)):
                    await message.reply_text(s("err_maintenance"))
                    return
                if group_only and not is_group(message):
                    await message.reply_text(s("err_group_only"))
                    return
                if (
                    group_only
                    and config.PRIVATE_MODE
                    and chat_id
                    and not db.chat_setting(chat_id, "approved", False)
                    and not (user and db.is_sudo(user.id))
                ):
                    await message.reply_text(s("err_private_mode"))
                    return
                if sudo_only and not (user and db.is_sudo(user.id)):
                    await message.reply_text(s("err_sudo_only"))
                    return
                if admin_only and chat_id and user and not await can_control(chat_id, user.id):
                    await message.reply_text(s("err_admin_only"))
                    return
                if play_permission and chat_id and user and not await can_play(chat_id, user.id):
                    await message.reply_text(s("err_play_mode_admins"))
                    return
                if require_active and chat_id and not queues.is_active(playback_chat(chat_id)):
                    await message.reply_text(s("err_no_active"))
                    return

                await func(client, message, s)

            except UserError as error:
                await _safe_reply(message, s(error.key, **error.params))
            except FloodWait as error:
                LOGGER.warning("FloodWait %s ثانیه در %s", error.value, chat_id)
            except MessageNotModified:
                pass
            except Exception as error:  # noqa: BLE001
                LOGGER.exception("خطا در هندلر %s: %s", func.__name__, error)
                await _safe_reply(message, s("err_generic", error=str(error)[:300]))

        return wrapper

    return decorator


def callback_handler(*, admin_only: bool = False, require_active: bool = False):
    """دکوریتور هندلر دکمه‌ها؛ تابع با امضای `(client, query, s)` صدا زده می‌شود."""

    def decorator(func):
        @wraps(func)
        async def wrapper(client, query: CallbackQuery):
            chat = getattr(query.message, "chat", None) if query.message else None
            chat_id = chat.id if chat else None
            s: Strings = strings_for(chat_id)
            user = query.from_user
            try:
                if user is not None and db.is_blocked_user(user.id) and not db.is_sudo(user.id):
                    await query.answer(s("err_blocked_user"), show_alert=True)
                    return
                if admin_only and chat_id and user and not await can_control(chat_id, user.id):
                    await query.answer(s("callback_admin_only"), show_alert=True)
                    return
                if require_active and chat_id and not queues.is_active(playback_chat(chat_id)):
                    await query.answer(s("callback_no_active"), show_alert=True)
                    return
                await func(client, query, s)
            except UserError as error:
                await query.answer(s(error.key, **error.params)[:190], show_alert=True)
            except MessageNotModified:
                pass
            except FloodWait as error:
                LOGGER.warning("FloodWait %s ثانیه (callback)", error.value)
            except Exception as error:  # noqa: BLE001
                LOGGER.exception("خطا در دکمهٔ %s: %s", func.__name__, error)
                try:
                    await query.answer(s("err_generic", error=str(error)[:120])[:190], show_alert=True)
                except Exception:  # noqa: BLE001
                    pass

        return wrapper

    return decorator


async def _safe_reply(message: Message, text: str):
    try:
        return await message.reply_text(text, disable_web_page_preview=True)
    except Exception as error:  # noqa: BLE001
        LOGGER.debug("پاسخ ناموفق: %s", error)
        return None
