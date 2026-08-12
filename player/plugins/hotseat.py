"""بازی «صندلی داغ»: مدیریت مهمان‌ها، نوبت‌ها و پنل کنترل آن."""

from __future__ import annotations

from pyrogram import Client, filters

from ..core.clients import bot
from ..core.decorators import callback_handler, player_handler
from ..core.filters import argument, command
from ..core.hotseat import Guest, Session, hotseat
from ..core.lang import strings_for
from ..utils.formatters import seconds_to_time, to_latin_digits
from ..utils.keyboards import hotseat_panel

LIST_WORDS = ("لیست", "صف", "وضعیت", "list", "queue", "status")


# ── متن‌ها ────────────────────────────────────────────────────────────────────
def _turn_length(session: Session, s) -> str:
    return s("hotseat_unlimited") if session.unlimited else seconds_to_time(session.seconds)


def _remaining(session: Session, s) -> str:
    left = session.remaining()
    return s("hotseat_unlimited") if left < 0 else seconds_to_time(left)


def _seat(session: Session, s) -> str:
    return session.current.mention if session.current else s("hotseat_empty_seat")


def turn_text(session: Session, s) -> str:
    text = s(
        "hotseat_turn",
        guest=_seat(session, s),
        turn=_turn_length(session, s),
        waiting=len(session.queue),
    )
    if session.mic_failed:
        text += s("hotseat_mic_hint")
    return text


def status_text(session: Session, s, chat_title: str) -> str:
    waiting = "".join(
        s("hotseat_waiting_item", index=index, guest=guest.mention)
        for index, guest in enumerate(session.waiting(), start=1)
    )
    text = s(
        "hotseat_status",
        chat=chat_title,
        guest=_seat(session, s),
        left=_remaining(session, s),
        served=session.served,
        waiting=waiting or s("hotseat_no_guests"),
    )
    if session.mic_failed:
        text += s("hotseat_mic_hint")
    return text


def _guest_of(user) -> Guest:
    name = " ".join(filter(None, [user.first_name, user.last_name])).strip()
    return Guest(user_id=user.id, name=name or (user.username or str(user.id)))


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


async def announce_turn(session: Session, s) -> None:
    """اعلام نوبت تازه در گروه؛ آیدی پیام برای به‌روزرسانی پنل نگه داشته می‌شود."""
    sent = await bot.send_message(
        session.chat_id,
        turn_text(session, s),
        reply_markup=hotseat_panel(s.language, paused=session.paused),
    )
    session.message_id = getattr(sent, "id", None)


# ── قلاب‌های زمان‌سنج ─────────────────────────────────────────────────────────
async def _on_turn(session: Session) -> None:
    await announce_turn(session, strings_for(session.chat_id))


async def _on_finish(session: Session) -> None:
    s = strings_for(session.chat_id)
    await bot.send_message(session.chat_id, s("hotseat_finished", served=session.served))


hotseat.on_turn = _on_turn
hotseat.on_finish = _on_finish


# ── دستورها ───────────────────────────────────────────────────────────────────
@Client.on_message(
    command(["hotseat", "hs"], bare=["صندلی داغ", "شروع صندلی داغ", "hot seat"]) & filters.group,
    group=1,
)
@player_handler(admin_only=True)
async def hotseat_command(_client: Client, message, s):
    """`صندلی داغ [دقیقه]` شروع بازی؛ `صندلی داغ لیست` وضعیت آن."""
    value = argument(message).strip()
    if value.lower() in LIST_WORDS:
        await _reply_status(message, s)
        return

    seconds: int | None = None
    if value:
        digits = to_latin_digits(value)
        if not digits.isdigit():
            await message.reply_text(s("hotseat_usage"))
            return
        seconds = int(digits) * 60

    guests: list[Guest] = []
    replied = getattr(message, "reply_to_message", None)
    if replied is not None and replied.from_user is not None:
        guests.append(_guest_of(replied.from_user))

    host = message.from_user.id if message.from_user else 0
    session = await hotseat.start(message.chat.id, host, guests, seconds)
    await message.reply_text(
        s("hotseat_started", turn=_turn_length(session, s), count=session.size())
    )
    if session.current is not None:
        await announce_turn(session, s)


@Client.on_message(
    command(["addguest", "guest"], bare=["افزودن مهمان", "مهمان جدید", "add guest"])
    & filters.group,
    group=1,
)
@player_handler(admin_only=True)
async def add_guest_command(client: Client, message, s):
    user = await _target_user(client, message)
    if user is None:
        await message.reply_text(s("hotseat_need_guest"))
        return

    guest = _guest_of(user)
    if not await hotseat.add(message.chat.id, guest):
        await message.reply_text(s("hotseat_guest_exists", user=guest.mention))
        return

    session = hotseat.session(message.chat.id)
    if session is None:
        return
    if session.current is not None and session.current.user_id == guest.user_id:
        # صندلی خالی بود و همین مهمان بلافاصله نوبت گرفت
        await announce_turn(session, s)
        return
    await message.reply_text(
        s("hotseat_guest_added", user=guest.mention, position=len(session.queue))
    )


@Client.on_message(
    command(["delguest", "removeguest"], bare=["حذف مهمان", "remove guest"]) & filters.group,
    group=1,
)
@player_handler(admin_only=True)
async def del_guest_command(client: Client, message, s):
    user = await _target_user(client, message)
    if user is None:
        await message.reply_text(s("hotseat_need_guest"))
        return

    guest = _guest_of(user)
    removed = await hotseat.remove(message.chat.id, user.id)
    if removed is None:
        await message.reply_text(s("hotseat_guest_missing", user=guest.mention))
        return
    await message.reply_text(s("hotseat_guest_removed", user=removed.mention))
    session = hotseat.session(message.chat.id)
    if session is not None and session.current is not None:
        await announce_turn(session, s)


@Client.on_message(
    command(["nextguest", "next"], bare=["مهمان بعدی", "نفر بعدی", "next guest"]) & filters.group,
    group=1,
)
@player_handler(admin_only=True)
async def next_guest_command(_client: Client, message, s):
    chat_id = message.chat.id
    session = hotseat.session(chat_id)
    if await hotseat.advance(chat_id) is None:
        finished = await hotseat.stop(chat_id)
        await message.reply_text(
            s("hotseat_finished", served=finished.served if finished else 0)
        )
        return
    if session is not None:
        await announce_turn(session, s)


@Client.on_message(
    command(["hotseatlist", "hslist"], bare=["لیست مهمان", "لیست صندلی داغ", "hot seat list"])
    & filters.group,
    group=1,
)
@player_handler()
async def hotseat_list_command(_client: Client, message, s):
    await _reply_status(message, s)


@Client.on_message(
    command(["endhotseat", "stophotseat"], bare=["پایان صندلی داغ", "پایان صندلی", "end hot seat"])
    & filters.group,
    group=1,
)
@player_handler(admin_only=True)
async def end_hotseat_command(_client: Client, message, s):
    session = await hotseat.stop(message.chat.id)
    if session is None:
        await message.reply_text(s("hotseat_not_active"))
        return
    await message.reply_text(s("hotseat_finished", served=session.served))


async def _reply_status(message, s) -> None:
    session = hotseat.session(message.chat.id)
    if session is None:
        await message.reply_text(s("hotseat_not_active"))
        return
    await message.reply_text(
        status_text(session, s, message.chat.title or str(message.chat.id)),
        reply_markup=hotseat_panel(s.language, paused=session.paused),
        disable_web_page_preview=True,
    )


# ── دکمه‌ها ───────────────────────────────────────────────────────────────────
@Client.on_callback_query(filters.regex(r"^hs:"))
@callback_handler(admin_only=True)
async def hotseat_callback(_client: Client, query, s):
    action = query.data.split(":", 1)[1]
    chat = getattr(query.message, "chat", None)
    if chat is None:
        return
    session = hotseat.session(chat.id)
    if session is None:
        await query.answer(s("hotseat_not_active"), show_alert=True)
        return

    if action == "next":
        guest = await hotseat.advance(chat.id)
        if guest is None:
            await hotseat.stop(chat.id)
            await query.message.reply_text(s("hotseat_finished", served=session.served))
            await query.answer()
            return
        await announce_turn(session, s)
        await query.answer(guest.name[:190])
        return

    if action in ("pause", "resume"):
        if action == "pause":
            hotseat.pause(chat.id)
        else:
            hotseat.resume(chat.id)
        await _refresh(query, session, s)
        await query.answer(s("hotseat_paused" if action == "pause" else "hotseat_resumed"))
        return

    if action == "end":
        await hotseat.stop(chat.id)
        await query.message.reply_text(s("hotseat_finished", served=session.served))
        await query.answer()
        return

    if action == "status":
        await _refresh(query, session, s)
        await query.answer(s("callback_done"))


async def _refresh(query, session: Session, s) -> None:
    chat = getattr(query.message, "chat", None)
    title = getattr(chat, "title", None) or str(session.chat_id)
    await query.message.edit_text(
        status_text(session, s, title),
        reply_markup=hotseat_panel(s.language, paused=session.paused),
        disable_web_page_preview=True,
    )
