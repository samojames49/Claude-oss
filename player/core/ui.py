"""توابع مشترک رابط کاربری: اجرای درخواست پخش و پاسخ‌دهی به کاربر."""

from __future__ import annotations

from typing import Any

from ..platforms import telegram_media
from ..strings import Strings
from ..utils.logger import get_logger
from .db import db
from .errors import NoResult
from .service import player, resolve_and_play
from .targets import playback_chat
from .track import Track

LOGGER = get_logger("ui")


def requester_of(message: Any) -> tuple[int, str]:
    user = getattr(message, "from_user", None)
    if user is None:
        return 0, ""
    name = " ".join(filter(None, [user.first_name, user.last_name])).strip()
    return user.id, name or (user.username or str(user.id))


async def _delete(message: Any) -> None:
    if message is None:
        return
    try:
        await message.delete()
    except Exception:  # noqa: BLE001
        pass


async def announce(message: Any, s: Strings, state: str, position: int, track: Track) -> None:
    """اطلاع‌رسانی نتیجهٔ درخواست پخش."""
    if state == "queued":
        await message.reply_text(
            s(
                "added_to_queue",
                position=position,
                title=track.short_title,
                duration=track.duration_text,
                requester=track.requester_mention(),
            ),
            disable_web_page_preview=True,
        )
        return

    # اگر پنل «در حال پخش» در تنظیمات گروه خاموش است، حداقل یک پاسخ کوتاه بدهیم
    chat_id = getattr(getattr(message, "chat", None), "id", None)
    if chat_id is not None and not db.chat_setting(chat_id, "now_playing_message", True):
        await message.reply_text(
            s(
                "now_playing",
                title=track.short_title,
                duration=track.duration_text,
                kind=s(track.kind_key()),
                requester=track.requester_mention(),
            ),
            disable_web_page_preview=True,
        )


async def play_request(
    client: Any,
    message: Any,
    s: Strings,
    *,
    query: str = "",
    video: bool = False,
    force: bool = False,
    download: bool = False,
) -> None:
    """مسیر کامل یک درخواست پخش (فایل ریپلای‌شده یا عبارت/لینک)."""
    chat_id = playback_chat(message.chat.id)
    requester_id, requester_name = requester_of(message)
    replied = getattr(message, "reply_to_message", None)

    if replied is not None and telegram_media.has_playable_media(replied):
        status = await message.reply_text(s("downloading"))
        try:
            track = await telegram_media.to_track(
                client,
                replied,
                video=video,
                requester_id=requester_id,
                requester_name=requester_name,
            )
            state, position = await player.play_or_queue(chat_id, track, force=force)
        finally:
            await _delete(status)
        await announce(message, s, state, position, track)
        return

    if not query:
        await message.reply_text(s("err_need_query"))
        return

    status = await message.reply_text(s("downloading") if download else s("searching"))
    try:
        state, position, track = await resolve_and_play(
            chat_id,
            query,
            video=video,
            requester_id=requester_id,
            requester_name=requester_name,
            force=force,
            download=download,
        )
    except NoResult:
        await message.reply_text(s("err_no_result"))
        return
    finally:
        await _delete(status)
    await announce(message, s, state, position, track)
