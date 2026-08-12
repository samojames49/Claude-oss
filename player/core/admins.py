"""تشخیص ادمین‌های گروه و کاربران مجاز به کنترل پخش (با کش)."""

from __future__ import annotations

from time import time

from pyrogram.enums import ChatMembersFilter, ChatMemberStatus, ChatType

from .. import config
from ..utils.logger import get_logger
from .clients import bot
from .db import db

LOGGER = get_logger("admins")

_CACHE: dict[int, tuple[float, set[int]]] = {}
CACHE_TTL = 600  # ثانیه


async def load_admins(chat_id: int, force: bool = False) -> set[int]:
    cached = _CACHE.get(chat_id)
    if cached and not force and time() - cached[0] < CACHE_TTL:
        return cached[1]

    admins: set[int] = set()
    try:
        async for member in bot.get_chat_members(
            chat_id, filter=ChatMembersFilter.ADMINISTRATORS
        ):
            user = getattr(member, "user", None)
            if user is None:
                continue
            if not user.is_bot or member.status == ChatMemberStatus.OWNER:
                admins.add(user.id)
    except Exception as error:  # noqa: BLE001
        LOGGER.debug("خواندن ادمین‌های %s ناموفق بود: %s", chat_id, error)
        if cached:
            return cached[1]
        return set()

    _CACHE[chat_id] = (time(), admins)
    return admins


def invalidate(chat_id: int) -> None:
    _CACHE.pop(chat_id, None)


async def is_chat_admin(chat_id: int, user_id: int) -> bool:
    if db.is_sudo(user_id):
        return True
    return user_id in await load_admins(chat_id)


def play_mode(chat_id: int) -> str:
    return db.chat_setting(chat_id, "play_mode", config.PLAY_MODE)


async def can_control(chat_id: int, user_id: int) -> bool:
    """اجازهٔ استفاده از دستورهای کنترلی (توقف، رد کردن، پایان…)."""
    if db.is_sudo(user_id):
        return True
    if db.is_auth_user(chat_id, user_id):
        return True
    return await is_chat_admin(chat_id, user_id)


async def can_play(chat_id: int, user_id: int) -> bool:
    """اجازهٔ درخواست پخش با توجه به حالت گروه."""
    if play_mode(chat_id) != "admins":
        return True
    return await can_control(chat_id, user_id)


def is_group(message) -> bool:
    chat = getattr(message, "chat", None)
    return bool(chat) and chat.type in (ChatType.GROUP, ChatType.SUPERGROUP)
