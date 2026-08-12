"""مدیریت ویس‌چت: عنوان کال، دعوت اعضا و کلیدهای تنظیمات گروه."""

from __future__ import annotations

import random

from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus

from .. import config
from ..core.calls import calls_service
from ..core.db import db
from ..core.decorators import player_handler
from ..core.filters import argument, command
from ..utils.formatters import to_latin_digits

ON_WORDS = ("فعال", "روشن", "on", "active", "enable")
OFF_WORDS = ("غیرفعال", "خاموش", "off", "inactive", "disable")


def switch_value(value: str) -> bool | None:
    word = value.strip().lower()
    if word in OFF_WORDS:
        return False
    if word in ON_WORDS:
        return True
    return None


async def _toggle(message, s, key: str, on_key: str, off_key: str) -> None:
    state = switch_value(argument(message))
    if state is None:
        await message.reply_text(s("callstats_need_switch"))
        return
    db.set_chat_setting(message.chat.id, key, state)
    await message.reply_text(s(on_key if state else off_key))


# ── عنوان ویس‌چت ──────────────────────────────────────────────────────────────
@Client.on_message(
    command(["setcalltitle", "calltitle"], bare=["تنظیم عنوان کال", "عنوان کال", "set title call"])
    & filters.group,
    group=1,
)
@player_handler(admin_only=True)
async def set_call_title_command(_client: Client, message, s):
    title = argument(message)
    if not title:
        await message.reply_text(s("call_title_usage"))
        return
    await calls_service.set_call_title(message.chat.id, title)
    await message.reply_text(s("call_title_set", title=title[:64]))


# ── دعوت به ویس‌چت ────────────────────────────────────────────────────────────
@Client.on_message(
    command(["invitecall", "callinvite"], bare=["دعوت کال اخیر", "invite call recent"])
    & filters.group,
    group=1,
)
@player_handler(admin_only=True)
async def invite_recent_command(_client: Client, message, s):
    """دعوت کاربران فعال اخیر گروه به ویس‌چت."""
    count = _count_argument(message)
    user_ids = await _recent_members(message.chat.id, count)
    await _invite(message, s, user_ids)


@Client.on_message(
    command(["invitevip", "invitecallvip"], bare=["دعوت کال ویژه", "invite call vip"])
    & filters.group,
    group=1,
)
@player_handler(admin_only=True)
async def invite_vip_command(_client: Client, message, s):
    """دعوت اعضای ویژه (کاربران مجاز پلیر) به ویس‌چت."""
    count = _count_argument(message)
    vip = [int(key) for key in db.auth_users(message.chat.id) if str(key).lstrip("-").isdigit()]
    random.shuffle(vip)
    await _invite(message, s, vip[:count])


def _count_argument(message) -> int:
    raw = to_latin_digits(argument(message)).strip()
    if raw.isdigit():
        return max(1, min(int(raw), config.INVITE_CALL_LIMIT))
    return config.INVITE_CALL_LIMIT


async def _recent_members(chat_id: int, count: int) -> list[int]:
    """اعضای اخیر گروه (به‌ترتیبی که تلگرام برمی‌گرداند)، بدون ربات‌ها."""
    from ..core.clients import bot

    found: list[int] = []
    try:
        async for member in bot.get_chat_members(chat_id, limit=min(count * 2, 400)):
            user = getattr(member, "user", None)
            if user is None or user.is_bot or user.is_deleted:
                continue
            if member.status == ChatMemberStatus.BANNED:
                continue
            found.append(user.id)
            if len(found) >= count:
                break
    except Exception:  # noqa: BLE001
        return found
    return found


async def _invite(message, s, user_ids: list[int]) -> None:
    if not user_ids:
        await message.reply_text(s("invite_no_target"))
        return
    status = await message.reply_text(s("invite_started", count=len(user_ids)))
    invited = await calls_service.invite_to_call(message.chat.id, user_ids)
    try:
        await status.edit_text(s("invite_done", invited=invited, total=len(user_ids)))
    except Exception:  # noqa: BLE001
        await message.reply_text(s("invite_done", invited=invited, total=len(user_ids)))


# ── کلیدهای تنظیمات ───────────────────────────────────────────────────────────
@Client.on_message(
    command(["autoclear", "clearauto"], bare=["پاکسازی خودکار", "clearauto"]) & filters.group,
    group=1,
)
@player_handler(admin_only=True)
async def auto_clear_command(_client: Client, message, s):
    await _toggle(message, s, "auto_clear", "autoclear_on", "autoclear_off")


@Client.on_message(
    command(["classicmode", "oldmode"], bare=["حالت کلاسیک", "حالت قدیمی", "classic mode", "old mode"])
    & filters.group,
    group=1,
)
@player_handler(admin_only=True)
async def classic_mode_command(_client: Client, message, s):
    await _toggle(message, s, "classic_mode", "classic_on", "classic_off")


@Client.on_message(
    command(["playchannel"], bare=["پخش کانال", "play channel"]) & filters.group,
    group=1,
)
@player_handler(admin_only=True)
async def play_channel_command(_client: Client, message, s):
    """پخش در ویس‌چت کانال متصل به گروه (به‌جای خود گروه)."""
    chat_id = message.chat.id
    state = switch_value(argument(message))
    if state is None:
        await message.reply_text(s("callstats_need_switch"))
        return
    if state and not db.chat_setting(chat_id, "player_channel", 0):
        await message.reply_text(s("play_channel_missing"))
        return
    db.set_chat_setting(chat_id, "play_in_channel", state)
    await message.reply_text(s("play_channel_on" if state else "play_channel_off"))


@Client.on_message(
    command(["callsecurity", "security"], bare=["امنیت کال", "call security"]) & filters.group,
    group=1,
)
@player_handler(admin_only=True)
async def call_security_command(_client: Client, message, s):
    await _toggle(message, s, "call_security", "security_on", "security_off")


@Client.on_message(
    command(["muteonjoin"], bare=["میوت ورودی کال", "میوت ورودی", "mute on join"]) & filters.group,
    group=1,
)
@player_handler(admin_only=True)
async def mute_on_join_command(_client: Client, message, s):
    await _toggle(message, s, "security_mute_on_join", "mute_join_on", "mute_join_off")


@Client.on_message(
    command(["accountage"], bare=["قدمت اکانت", "account age"]) & filters.group,
    group=1,
)
@player_handler(admin_only=True)
async def account_age_command(_client: Client, message, s):
    """قدمت عضویتی که کاربر را از میوت خودکار ورودی معاف می‌کند."""
    raw = to_latin_digits(argument(message)).strip()
    if not raw.isdigit():
        await message.reply_text(s("security_age_prompt"))
        return
    days = max(0, min(int(raw), 365))
    db.set_chat_setting(message.chat.id, "security_min_age_days", days)
    await message.reply_text(s("security_age_set", days=days))


@Client.on_message(
    command(["callmessage", "callcomment"], bare=["پیام کال", "مسیج کال", "کامنت کال", "call message", "call comment"])
    & filters.group,
    group=1,
)
@player_handler(admin_only=True)
async def call_message_command(_client: Client, message, s):
    """نگه‌داشتن یا پاک‌کردن پیام‌های سرویسی ویس‌چت (شروع/پایان/دعوت) در گروه."""
    await _toggle(message, s, "call_service_messages", "call_message_on", "call_message_off")


@Client.on_message(
    command(["setplayerchannel", "playerchannel"], bare=["تنظیم کانال پلیر", "set player channel"])
    & filters.group,
    group=1,
)
@player_handler(admin_only=True)
async def set_player_channel_command(_client: Client, message, s):
    """اتصال یک کانال به پلیر گروه (ربات و اسیستنت باید در کانال باشند)."""
    chat_id = message.chat.id
    raw = to_latin_digits(argument(message)).strip()

    if raw in ("حذف", "پاک", "remove", "off", "0"):
        db.set_chat_setting(chat_id, "player_channel", 0)
        db.set_chat_setting(chat_id, "play_in_channel", False)
        await message.reply_text(s("play_channel_removed"))
        return

    target = raw or _linked_channel_id(message)
    if not target:
        await message.reply_text(s("play_channel_usage"))
        return

    from ..core.clients import bot

    try:
        chat = await bot.get_chat(int(target) if str(target).lstrip("-").isdigit() else target)
    except Exception as error:  # noqa: BLE001
        await message.reply_text(s("play_channel_unreachable", error=str(error)[:120]))
        return

    db.set_chat_setting(chat_id, "player_channel", chat.id)
    await message.reply_text(s("play_channel_set", title=chat.title or str(chat.id), chat_id=chat.id))


def _linked_channel_id(message) -> int | str:
    """اگر روی پیام فورواردشده از کانال ریپلای شده باشد، همان کانال."""
    replied = getattr(message, "reply_to_message", None)
    origin = getattr(replied, "forward_from_chat", None) if replied else None
    return getattr(origin, "id", 0) or 0
