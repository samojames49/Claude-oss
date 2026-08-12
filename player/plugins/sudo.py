"""دستورهای مدیریتی سراسری (فقط برای سودوها)."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait

from .. import config
from ..core.db import db
from ..core.decorators import player_handler
from ..core.filters import argument, command
from ..core.queues import queues
from ..core.service import player
from ..utils.formatters import human_bytes, to_latin_digits
from ..utils.logger import LOG_FILE, get_logger

LOGGER = get_logger("sudo")


async def _target_user(client: Client, message):
    replied = getattr(message, "reply_to_message", None)
    if replied is not None and replied.from_user is not None:
        return replied.from_user
    raw = to_latin_digits(argument(message)).lstrip("@")
    if not raw:
        return None
    try:
        return await client.get_users(int(raw) if raw.isdigit() else raw)
    except Exception:  # noqa: BLE001
        return None


@Client.on_message(command(["addsudo"]), group=1)
@player_handler(group_only=False, sudo_only=True)
async def add_sudo(client: Client, message, s):
    user = await _target_user(client, message)
    if user is None:
        await message.reply_text(s("err_not_reply_user"))
        return
    db.add_sudo(user.id)
    await db.save()
    await message.reply_text(s("sudo_added", user=user.mention))


@Client.on_message(command(["delsudo", "rmsudo"]), group=1)
@player_handler(group_only=False, sudo_only=True)
async def del_sudo(client: Client, message, s):
    user = await _target_user(client, message)
    if user is None:
        await message.reply_text(s("err_not_reply_user"))
        return
    db.remove_sudo(user.id)
    await db.save()
    await message.reply_text(s("sudo_removed", user=user.mention))


@Client.on_message(command(["sudolist", "sudoers"]), group=1)
@player_handler(group_only=False, sudo_only=True)
async def sudo_list(_client: Client, message, s):
    ids = sorted(db.sudoers())
    lines = "\n".join(f"• `{user_id}`" for user_id in ids) or "-"
    await message.reply_text(s("sudo_list", users=lines))


@Client.on_message(command(["block", "ban"]), group=1)
@player_handler(group_only=False, sudo_only=True)
async def block_user(client: Client, message, s):
    user = await _target_user(client, message)
    if user is None:
        await message.reply_text(s("err_not_reply_user"))
        return
    db.block_user(user.id)
    await db.save()
    await message.reply_text(s("blocked_user", user=user.mention))


@Client.on_message(command(["unblock", "unban"]), group=1)
@player_handler(group_only=False, sudo_only=True)
async def unblock_user(client: Client, message, s):
    user = await _target_user(client, message)
    if user is None:
        await message.reply_text(s("err_not_reply_user"))
        return
    db.unblock_user(user.id)
    await db.save()
    await message.reply_text(s("unblocked_user", user=user.mention))


@Client.on_message(command(["blockchat", "banchat"]), group=1)
@player_handler(group_only=False, sudo_only=True)
async def block_chat(_client: Client, message, s):
    raw = to_latin_digits(argument(message)) or str(message.chat.id)
    try:
        chat_id = int(raw)
    except ValueError:
        await message.reply_text(s("err_invalid_number"))
        return
    db.block_chat(chat_id)
    await db.save()
    if queues.is_active(chat_id):
        await player.cleanup(chat_id)
    await message.reply_text(s("blocked_chat", chat_id=chat_id))


@Client.on_message(command(["unblockchat", "unbanchat"]), group=1)
@player_handler(group_only=False, sudo_only=True)
async def unblock_chat(_client: Client, message, s):
    raw = to_latin_digits(argument(message)) or str(message.chat.id)
    try:
        chat_id = int(raw)
    except ValueError:
        await message.reply_text(s("err_invalid_number"))
        return
    db.unblock_chat(chat_id)
    await db.save()
    await message.reply_text(s("unblocked_chat", chat_id=chat_id))


@Client.on_message(command(["approve", "approvechat"]), group=1)
@player_handler(group_only=False, sudo_only=True)
async def approve_chat(_client: Client, message, s):
    raw = to_latin_digits(argument(message)) or str(message.chat.id)
    try:
        chat_id = int(raw)
    except ValueError:
        await message.reply_text(s("err_invalid_number"))
        return
    db.set_chat_setting(chat_id, "approved", True)
    await db.save()
    await message.reply_text(s("unblocked_chat", chat_id=chat_id))


@Client.on_message(command(["maintenance", "maint"]), group=1)
@player_handler(group_only=False, sudo_only=True)
async def maintenance_command(_client: Client, message, s):
    value = argument(message).strip().lower()
    if value in ("on", "روشن", "1", "true"):
        db.set_setting("maintenance", True)
    elif value in ("off", "خاموش", "0", "false"):
        db.set_setting("maintenance", False)
    else:
        db.set_setting("maintenance", not db.maintenance)
    await db.save()
    await message.reply_text(s("maintenance_on") if db.maintenance else s("maintenance_off"))


@Client.on_message(command(["activevc", "activevoice", "actives"]), group=1)
@player_handler(group_only=False, sudo_only=True)
async def active_vc(_client: Client, message, s):
    chats = queues.active_chats()
    if not chats:
        await message.reply_text(s("activevc_empty"))
        return
    text = s("activevc_header", count=len(chats))
    for chat_id in chats:
        track = queues.current(chat_id)
        text += s("activevc_item", chat_id=chat_id, title=track.short_title if track else "-")
    await message.reply_text(text)


@Client.on_message(command(["logs", "log"]), group=1)
@player_handler(group_only=False, sudo_only=True)
async def logs_command(_client: Client, message, s):
    if not Path(LOG_FILE).exists():
        await message.reply_text(s("logs_missing"))
        return
    await message.reply_document(str(LOG_FILE), caption="📄 player.log")


@Client.on_message(command(["cleanup", "clearcache"]), group=1)
@player_handler(group_only=False, sudo_only=True)
async def cleanup_command(_client: Client, message, s):
    removed = 0
    freed = 0
    for directory in (config.DOWNLOADS_DIR, config.CACHE_DIR / "thumbs"):
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if not path.is_file():
                continue
            try:
                size = path.stat().st_size
                path.unlink()
                removed += 1
                freed += size
            except OSError:
                continue
    shutil.rmtree(config.CACHE_DIR / "youtube", ignore_errors=True)
    await message.reply_text(s("cleanup_done", count=removed, size=human_bytes(freed)))


@Client.on_message(command(["broadcast", "gcast"]), group=1)
@player_handler(group_only=False, sudo_only=True)
async def broadcast_command(client: Client, message, s):
    raw = argument(message)
    replied = getattr(message, "reply_to_message", None)
    flags = {flag for flag in raw.split() if flag.startswith("-")}
    text = " ".join(part for part in raw.split() if not part.startswith("-")).strip()

    if not text and replied is None:
        await message.reply_text(s("broadcast_need_text"))
        return

    await message.reply_text(s("broadcast_started"))
    targets: list[int] = []
    if "-nogroup" not in flags:
        targets += db.served_chats()
    if "-user" in flags:
        targets += db.served_users()

    sent = 0
    failed = 0
    groups_done = 0
    users_done = 0
    for chat_id in targets:
        try:
            if replied is not None:
                delivered = await replied.copy(chat_id)
            else:
                delivered = await client.send_message(
                    chat_id, text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
                )
            if "-pin" in flags and delivered is not None:
                try:
                    await delivered.pin(disable_notification=True)
                except Exception:  # noqa: BLE001
                    pass
            sent += 1
            if chat_id < 0:
                groups_done += 1
            else:
                users_done += 1
        except FloodWait as error:
            await asyncio.sleep(int(error.value) + 1)
            failed += 1
        except Exception:  # noqa: BLE001
            failed += 1
        await asyncio.sleep(0.15)

    LOGGER.info("پیام همگانی: %s موفق، %s ناموفق", sent, failed)
    await message.reply_text(
        s("broadcast_done", chats=groups_done, users=users_done, failed=failed)
    )
