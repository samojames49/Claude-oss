"""دسترسی کاربران عادی به کنترل پخش و تازه‌سازی لیست ادمین‌ها."""

from __future__ import annotations

from pyrogram import Client, filters

from ..core import admins
from ..core.db import db
from ..core.decorators import player_handler
from ..core.filters import argument, command
from ..utils.formatters import to_latin_digits


async def _target_user(client: Client, message):
    replied = getattr(message, "reply_to_message", None)
    if replied is not None and replied.from_user is not None:
        return replied.from_user
    raw = to_latin_digits(argument(message)).lstrip("@")
    if not raw:
        return None
    try:
        return await client.get_users(int(raw) if raw.isdigit() else raw)
    except Exception:  # noqa: BLE001 - کاربر پیدا نشد
        return None


def _name(user) -> str:
    return " ".join(filter(None, [user.first_name, user.last_name])).strip() or str(user.id)


@Client.on_message(command(["auth", "authorize"], bare=["دسترسی"]) & filters.group, group=1)
@player_handler(admin_only=True)
async def auth_command(client: Client, message, s):
    user = await _target_user(client, message)
    if user is None:
        await message.reply_text(s("err_not_reply_user"))
        return
    added = db.add_auth_user(message.chat.id, user.id, _name(user))
    key = "auth_added" if added else "auth_exists"
    await message.reply_text(s(key, user=user.mention))


@Client.on_message(command(["unauth", "unauthorize"], bare=["حذف دسترسی"]) & filters.group, group=1)
@player_handler(admin_only=True)
async def unauth_command(client: Client, message, s):
    user = await _target_user(client, message)
    if user is None:
        await message.reply_text(s("err_not_reply_user"))
        return
    removed = db.remove_auth_user(message.chat.id, user.id)
    key = "auth_removed" if removed else "auth_missing"
    await message.reply_text(s(key, user=user.mention))


@Client.on_message(command(["authlist", "authusers"], bare=["لیست دسترسی"]) & filters.group, group=1)
@player_handler()
async def authlist_command(_client: Client, message, s):
    users = db.auth_users(message.chat.id)
    if not users:
        await message.reply_text(s("auth_list_empty"))
        return
    lines = [
        f"• [{data.get('name') or user_id}](tg://user?id={user_id}) — `{user_id}`"
        for user_id, data in users.items()
    ]
    await message.reply_text(s("auth_list", users="\n".join(lines)))


@Client.on_message(command(["reload", "refresh"], bare=["بروزرسانی ادمین"]) & filters.group, group=1)
@player_handler(admin_only=True)
async def reload_command(_client: Client, message, s):
    chat_id = message.chat.id
    admins.invalidate(chat_id)
    current = await admins.load_admins(chat_id, force=True)
    await message.reply_text(s("admins_reloaded", count=len(current)))
