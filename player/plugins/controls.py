"""دستورهای کنترل پخش و دکمه‌های پنل."""

from __future__ import annotations

from pyrogram import Client, filters

from ..core.calls import calls_service
from ..core.decorators import callback_handler, player_handler
from ..core.errors import UserError
from ..core.filters import argument, command
from ..core.queues import queues
from ..core.service import player
from ..utils.formatters import seconds_to_time, time_to_seconds, to_latin_digits
from ..utils.keyboards import player_panel, queue_panel

DEFAULT_LOOP_ROUNDS = 5


# ── دستورها ───────────────────────────────────────────────────────────────────
@Client.on_message(command(["pause"], bare=["توقف", "پاز"]) & filters.group, group=1)
@player_handler(admin_only=True, require_active=True)
async def pause_command(_client: Client, message, s):
    chat_id = message.chat.id
    if queues.is_paused(chat_id):
        await message.reply_text(s("already_paused"))
        return
    await calls_service.pause(chat_id)
    queues.set_paused(chat_id, True)
    await message.reply_text(s("paused"))


@Client.on_message(command(["resume", "continue"], bare=["ادامه", "ریزوم"]) & filters.group, group=1)
@player_handler(admin_only=True, require_active=True)
async def resume_command(_client: Client, message, s):
    chat_id = message.chat.id
    if not queues.is_paused(chat_id):
        await message.reply_text(s("already_playing"))
        return
    await calls_service.resume(chat_id)
    queues.set_paused(chat_id, False)
    await message.reply_text(s("resumed"))


@Client.on_message(command(["skip", "next"], bare=["بعدی", "رد"]) & filters.group, group=1)
@player_handler(admin_only=True, require_active=True)
async def skip_command(_client: Client, message, s):
    chat_id = message.chat.id
    raw = to_latin_digits(argument(message))
    if raw.isdigit():
        removed = queues.remove(chat_id, int(raw))
        if removed is None:
            await message.reply_text(s("err_invalid_number"))
            return
        await message.reply_text(s("skipped_index", title=removed.short_title))
        return
    current = await player.skip(chat_id)
    if current is not None:
        await message.reply_text(s("skipped", title=current.short_title))


@Client.on_message(
    command(["end", "stop", "stopplay", "leave"], bare=["پایان", "خروج"]) & filters.group,
    group=1,
)
@player_handler(admin_only=True, require_active=True)
async def end_command(_client: Client, message, s):
    user = message.from_user
    await player.stop(message.chat.id, user.mention if user else "")


@Client.on_message(command(["mute"], bare=["بی صدا", "بیصدا"]) & filters.group, group=1)
@player_handler(admin_only=True, require_active=True)
async def mute_command(_client: Client, message, s):
    chat_id = message.chat.id
    await calls_service.mute(chat_id)
    queues.set_muted(chat_id, True)
    await message.reply_text(s("muted"))


@Client.on_message(command(["unmute"], bare=["با صدا", "باصدا"]) & filters.group, group=1)
@player_handler(admin_only=True, require_active=True)
async def unmute_command(_client: Client, message, s):
    chat_id = message.chat.id
    await calls_service.unmute(chat_id)
    queues.set_muted(chat_id, False)
    await message.reply_text(s("unmuted"))


@Client.on_message(command(["volume", "vol"], bare=["صدا"]) & filters.group, group=1)
@player_handler(admin_only=True, require_active=True)
async def volume_command(_client: Client, message, s):
    chat_id = message.chat.id
    raw = to_latin_digits(argument(message))
    if not raw.isdigit():
        await message.reply_text(s("volume_range"))
        return
    volume = int(raw)
    if not 1 <= volume <= 200:
        await message.reply_text(s("volume_range"))
        return
    await calls_service.set_volume(chat_id, volume)
    queues.set_volume(chat_id, volume)
    await message.reply_text(s("volume_set", volume=volume))


@Client.on_message(command(["seek"], bare=["جلو"]) & filters.group, group=1)
@player_handler(admin_only=True, require_active=True)
async def seek_command(_client: Client, message, s):
    await _seek(message, s, forward=True)


@Client.on_message(command(["seekback", "rewind"], bare=["عقب"]) & filters.group, group=1)
@player_handler(admin_only=True, require_active=True)
async def seekback_command(_client: Client, message, s):
    await _seek(message, s, forward=False)


async def _seek(message, s, *, forward: bool) -> None:
    chat_id = message.chat.id
    offset = time_to_seconds(argument(message))
    if offset <= 0:
        await message.reply_text(s("err_invalid_number"))
        return
    played = await calls_service.played_time(chat_id)
    position = played + offset if forward else max(0, played - offset)
    await player.seek(chat_id, position)
    await message.reply_text(s("seeked", position=seconds_to_time(position)))


@Client.on_message(command(["loop", "repeat"], bare=["تکرار"]) & filters.group, group=1)
@player_handler(admin_only=True, require_active=True)
async def loop_command(_client: Client, message, s):
    chat_id = message.chat.id
    raw = to_latin_digits(argument(message)).lower()
    if raw in ("off", "0", "خاموش", "قطع"):
        queues.set_loop(chat_id, 0)
        await message.reply_text(s("loop_off"))
        return
    if raw.isdigit():
        count = max(1, min(int(raw), 20))
    elif raw in ("", "on", "روشن"):
        count = 0 if queues.loop(chat_id) else DEFAULT_LOOP_ROUNDS
    else:
        await message.reply_text(s("err_invalid_number"))
        return
    if count == 0:
        queues.set_loop(chat_id, 0)
        await message.reply_text(s("loop_off"))
        return
    queues.set_loop(chat_id, count)
    await message.reply_text(s("loop_on", count=count))


@Client.on_message(command(["shuffle"], bare=["بر زدن", "شافل"]) & filters.group, group=1)
@player_handler(admin_only=True, require_active=True)
async def shuffle_command(_client: Client, message, s):
    chat_id = message.chat.id
    count = queues.shuffle(chat_id)
    if count < 2:
        await message.reply_text(s("queue_empty"))
        return
    await message.reply_text(s("shuffled", count=count))


@Client.on_message(command(["speed", "playback"], bare=["سرعت"]) & filters.group, group=1)
@player_handler(admin_only=True, require_active=True)
async def speed_command(_client: Client, message, s):
    raw = to_latin_digits(argument(message)).replace("x", "").strip()
    try:
        speed = float(raw)
    except ValueError:
        await message.reply_text(s("speed_range"))
        return
    if not 0.5 <= speed <= 2.0:
        await message.reply_text(s("speed_range"))
        return
    await player.set_speed(message.chat.id, speed)
    await message.reply_text(s("speed_set", speed=speed))


@Client.on_message(command(["replay", "restart"], bare=["از اول"]) & filters.group, group=1)
@player_handler(admin_only=True, require_active=True)
async def replay_command(_client: Client, message, s):
    await player.replay(message.chat.id)
    await message.reply_text(s("seeked", position=seconds_to_time(0)))


# ── دکمه‌های پنل ───────────────────────────────────────────────────────────────
@Client.on_callback_query(filters.regex(r"^ctl:"))
@callback_handler(admin_only=True, require_active=True)
async def control_callback(_client: Client, query, s):
    action = query.data.split(":", 1)[1]
    chat_id = query.message.chat.id

    if action == "pause":
        await calls_service.pause(chat_id)
        queues.set_paused(chat_id, True)
        await _refresh_panel(query, s)
        await query.answer(s("paused").splitlines()[0])
    elif action == "resume":
        await calls_service.resume(chat_id)
        queues.set_paused(chat_id, False)
        await _refresh_panel(query, s)
        await query.answer(s("resumed"))
    elif action == "skip":
        current = await player.skip(chat_id)
        await query.answer(
            s("skipped", title=current.short_title) if current else s("callback_done")
        )
    elif action == "end":
        user = query.from_user
        await query.answer(s("callback_done"))
        await player.stop(chat_id, user.mention if user else "")
    elif action == "mute":
        await calls_service.mute(chat_id)
        queues.set_muted(chat_id, True)
        await _refresh_panel(query, s)
        await query.answer(s("muted"))
    elif action == "unmute":
        await calls_service.unmute(chat_id)
        queues.set_muted(chat_id, False)
        await _refresh_panel(query, s)
        await query.answer(s("unmuted"))
    elif action in ("vol_up", "vol_down"):
        step = 20 if action == "vol_up" else -20
        volume = max(10, min(200, queues.volume(chat_id) + step))
        await calls_service.set_volume(chat_id, volume)
        queues.set_volume(chat_id, volume)
        await query.answer(s("volume_set", volume=volume))
    elif action == "loop":
        count = 0 if queues.loop(chat_id) else DEFAULT_LOOP_ROUNDS
        queues.set_loop(chat_id, count)
        await query.answer(s("loop_on", count=count) if count else s("loop_off"))
    elif action == "shuffle":
        count = queues.shuffle(chat_id)
        await query.answer(s("shuffled", count=count) if count > 1 else s("queue_empty"))
    elif action == "queue":
        text = await player.queue_text(chat_id)
        await query.message.reply_text(text, reply_markup=queue_panel(s.language))
        await query.answer()
    elif action == "refresh":
        text = await player.status_text(chat_id)
        markup = _panel_markup(chat_id, s)
        try:
            if query.message.caption is not None:
                await query.message.edit_caption(text, reply_markup=markup)
            else:
                await query.message.edit_text(text, reply_markup=markup)
        except Exception:  # noqa: BLE001
            pass
        await query.answer(s("callback_done"))
    else:
        raise UserError("err_generic", error=f"action {action}")


def _panel_markup(chat_id: int, s):
    return player_panel(
        s.language,
        paused=queues.is_paused(chat_id),
        muted=queues.is_muted(chat_id),
    )


async def _refresh_panel(query, s) -> None:
    chat_id = query.message.chat.id
    try:
        await query.message.edit_reply_markup(reply_markup=_panel_markup(chat_id, s))
    except Exception:  # noqa: BLE001
        pass
