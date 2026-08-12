"""دستور /start و /help و دکمه‌های راهنما."""

from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .. import config
from ..core.db import db
from ..core.decorators import callback_handler, player_handler
from ..core.filters import command
from ..core.lang import strings_for
from ..utils import keyboards
from ..utils.logger import get_logger

LOGGER = get_logger("start")


async def _force_sub_ok(client: Client, user_id: int) -> bool:
    if not config.FORCE_SUB_CHANNEL:
        return True
    if db.is_sudo(user_id):
        return True
    try:
        await client.get_chat_member(config.FORCE_SUB_CHANNEL, user_id)
        return True
    except UserNotParticipant:
        return False
    except Exception as error:  # noqa: BLE001 - کانال اشتباه نباید ربات را قفل کند
        LOGGER.debug("بررسی عضویت اجباری ناموفق بود: %s", error)
        return True


@Client.on_message(command(["start", "شروع"], bare=["شروع"]) & filters.private, group=1)
@player_handler(group_only=False)
async def start_private(client: Client, message, s):
    user = message.from_user
    if not await _force_sub_ok(client, user.id):
        channel = f"https://t.me/{config.FORCE_SUB_CHANNEL.lstrip('@')}"
        await message.reply_text(
            s("force_sub", channel=channel),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(s("button_channel"), url=channel)]]
            ),
        )
        return

    username = (await client.get_me()).username
    text = s("start_private", bot_name=config.BOT_NAME, mention=user.mention)
    keyboard = keyboards.start_panel(s.language, username)
    if config.START_IMAGE:
        try:
            await message.reply_photo(config.START_IMAGE, caption=text, reply_markup=keyboard)
            return
        except Exception as error:  # noqa: BLE001
            LOGGER.debug("ارسال عکس شروع ناموفق بود: %s", error)
    await message.reply_text(text, reply_markup=keyboard, disable_web_page_preview=True)


@Client.on_message(command(["start", "شروع"], bare=["شروع"]) & filters.group, group=1)
@player_handler()
async def start_group(_client: Client, message, s):
    await message.reply_text(s("start_group", bot_name=config.BOT_NAME))


@Client.on_message(command(["help", "راهنما", "کمک"], bare=["راهنما"]), group=1)
@player_handler(group_only=False)
async def help_command(client: Client, message, s):
    await message.reply_text(
        s("help_header", bot_name=config.BOT_NAME),
        reply_markup=keyboards.help_panel(s.language),
    )


@Client.on_callback_query(filters.regex(r"^help:"))
@callback_handler()
async def help_callback(client: Client, query, s):
    section = query.data.split(":", 1)[1]
    if section == "home":
        await query.message.edit_text(
            s("help_header", bot_name=config.BOT_NAME),
            reply_markup=keyboards.help_panel(s.language),
        )
        await query.answer()
        return

    username = (await client.get_me()).username or ""
    key = f"help_{section}"
    await query.message.edit_text(
        s(key, bot_username=username),
        reply_markup=keyboards.help_back(s.language),
        disable_web_page_preview=True,
    )
    await query.answer()


@Client.on_callback_query(filters.regex(r"^close$"))
@callback_handler()
async def close_callback(_client: Client, query, s):
    try:
        await query.message.delete()
    except Exception:  # noqa: BLE001
        await query.message.edit_reply_markup(reply_markup=None)
    await query.answer(s("callback_done"))


@Client.on_message(filters.new_chat_members, group=2)
async def on_added_to_chat(client: Client, message):
    me = await client.get_me()
    if not any(user.id == me.id for user in message.new_chat_members or []):
        return
    chat = message.chat
    db.add_chat(chat.id, chat.title or "")
    s = strings_for(chat.id)
    try:
        await message.reply_text(s("start_group", bot_name=config.BOT_NAME))
    except Exception:  # noqa: BLE001
        pass
    if config.LOGGER_ID:
        adder = message.from_user.mention if message.from_user else "-"
        try:
            await client.send_message(
                config.LOGGER_ID,
                s("log_new_chat", title=chat.title or "-", chat_id=chat.id, user=adder),
            )
        except Exception as error:  # noqa: BLE001
            LOGGER.debug("لاگ گروه جدید ناموفق بود: %s", error)


@Client.on_message(filters.left_chat_member, group=2)
async def on_removed_from_chat(client: Client, message):
    me = await client.get_me()
    left = message.left_chat_member
    if not left or left.id != me.id:
        return
    chat = message.chat
    if config.LOGGER_ID:
        s = strings_for(None)
        try:
            await client.send_message(
                config.LOGGER_ID,
                s("log_left_chat", title=chat.title or "-", chat_id=chat.id),
            )
        except Exception:  # noqa: BLE001
            pass
    db.remove_chat(chat.id)


@Client.on_message(filters.private & filters.incoming & ~filters.service, group=9)
async def track_private_user(client: Client, message):
    """ثبت کاربران چت خصوصی برای پیام همگانی و آمار."""
    user = message.from_user
    if user is None or user.is_bot:
        return
    name = " ".join(filter(None, [user.first_name, user.last_name])).strip()
    if db.add_user(user.id, name) and config.LOGGER_ID:
        s = strings_for(None)
        try:
            await client.send_message(
                config.LOGGER_ID,
                s("log_new_user", user=user.mention, user_id=user.id),
            )
        except Exception:  # noqa: BLE001
            pass
