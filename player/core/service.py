"""هستهٔ منطق پخش: شروع، صف، رد کردن، پایان و پنل «در حال پخش»."""

from __future__ import annotations

import asyncio
from time import time

from pyrogram.enums import ParseMode
from pytgcalls import filters as call_filters
from pytgcalls.types import ChatUpdate, StreamEnded

from .. import __version__, config
from ..platforms import resolver
from ..utils.formatters import progress_bar, seconds_to_time
from ..utils.keyboards import player_panel
from ..utils.logger import get_logger
from ..utils.thumbnail import now_playing_image
from .calls import calls_service
from .callwatch import callwatch
from .clients import active_assistants, bot
from .db import db
from .errors import NoResult, QueueFull, UserError
from .lang import strings_for
from .queues import queues
from .track import Track

LOGGER = get_logger("service")


class PlayerService:
    """پیوند دهندهٔ صف، ویس‌چت و پیام‌های گروه."""

    def __init__(self) -> None:
        self.started_at = time()
        self._advancing: set[int] = set()
        self._locks: dict[int, asyncio.Lock] = {}
        self._watcher_task: asyncio.Task | None = None

    # ── ابزارهای داخلی ───────────────────────────────────────────────────────
    def lock(self, chat_id: int) -> asyncio.Lock:
        return self._locks.setdefault(chat_id, asyncio.Lock())

    @property
    def uptime(self) -> int:
        return int(time() - self.started_at)

    # ── راه‌اندازی هندلرها ───────────────────────────────────────────────────
    def setup_handlers(self) -> None:
        for assistant in active_assistants():
            assistant.calls.on_update(call_filters.stream_end(StreamEnded.Type.AUDIO))(
                self._on_stream_end
            )
            assistant.calls.on_update(call_filters.chat_update(ChatUpdate.Status.LEFT_CALL))(
                self._on_left_call
            )
        LOGGER.info("هندلرهای ویس‌چت روی %s اسیستنت نصب شد.", len(active_assistants()))

    async def _on_stream_end(self, _client, update: StreamEnded) -> None:
        if update.stream_type != StreamEnded.Type.AUDIO:
            return
        await self.play_next(update.chat_id)

    async def _on_left_call(self, _client, update: ChatUpdate) -> None:
        chat_id = update.chat_id
        if not queues.is_active(chat_id):
            return
        LOGGER.info("ویس‌چت %s بسته شد یا اسیستنت خارج شد.", chat_id)
        await self.cleanup(chat_id, reason_key="vc_closed")

    # ── شروع پخش / افزودن به صف ──────────────────────────────────────────────
    async def play_or_queue(
        self,
        chat_id: int,
        track: Track,
        *,
        force: bool = False,
    ) -> tuple[str, int]:
        """اگر پخشی در جریان است به صف اضافه می‌کند، وگرنه پخش را شروع می‌کند.

        مقدار بازگشتی: («playing» یا «queued»، جایگاه در صف)
        """
        async with self.lock(chat_id):
            if queues.is_active(chat_id) and await calls_service.is_connected(chat_id):
                if force:
                    current = queues.current(chat_id)
                    if current is not None:
                        resume = current.clone()
                        resume.seek = max(0, await calls_service.played_time(chat_id))
                        queues.add_next(chat_id, resume)
                    await self.start_track(chat_id, track)
                    return "playing", 0
                if queues.size(chat_id) >= config.QUEUE_LIMIT:
                    raise QueueFull(config.QUEUE_LIMIT)
                position = queues.add(chat_id, track)
                return "queued", position

            await self.start_track(chat_id, track)
            return "playing", 0

    async def start_track(self, chat_id: int, track: Track, *, notify: bool = True) -> None:
        """پخش یک آیتم در ویس‌چت گروه و ارسال پنل."""
        if track.video and not self._video_slot_available(chat_id):
            track.video = False
            s = strings_for(chat_id)
            await self._safe_send(chat_id, s("err_video_limit", limit=config.VIDEO_CALL_LIMIT))

        prepared = await resolver.prepare_track(track)
        prepared.media_volume = int(db.chat_setting(chat_id, "media_volume", 100) or 100)
        await calls_service.play(chat_id, prepared)

        callwatch.mark_open(chat_id)
        queues.set_current(chat_id, prepared)
        queues.set_paused(chat_id, False)
        queues.set_muted(chat_id, False)
        db.count_play(chat_id, prepared.title)

        if notify and db.chat_setting(chat_id, "now_playing_message", True):
            await self.send_panel(chat_id, prepared)
        await self._log_play(chat_id, prepared)

    def _video_slot_available(self, chat_id: int) -> bool:
        video_chats = set(queues.video_chats())
        video_chats.discard(chat_id)
        return len(video_chats) < config.VIDEO_CALL_LIMIT

    # ── آیتم بعدی ────────────────────────────────────────────────────────────
    async def play_next(self, chat_id: int, depth: int = 0) -> bool:
        if chat_id in self._advancing and depth == 0:
            return False
        self._advancing.add(chat_id)
        try:
            track = queues.pop_next(chat_id)
            if track is None:
                await self.cleanup(chat_id, reason_key="stream_end_empty")
                return False
            try:
                await self.start_track(chat_id, track)
                return True
            except UserError as error:
                s = strings_for(chat_id)
                await self._safe_send(chat_id, s(error.key, **error.params))
            except Exception as error:  # noqa: BLE001
                LOGGER.exception("پخش آیتم بعدی در %s ناموفق بود: %s", chat_id, error)
                s = strings_for(chat_id)
                await self._safe_send(chat_id, s("err_generic", error=str(error)[:200]))
            if depth < 3:
                return await self.play_next(chat_id, depth + 1)
            await self.cleanup(chat_id, reason_key="stream_end_empty")
            return False
        finally:
            if depth == 0:
                self._advancing.discard(chat_id)

    async def skip(self, chat_id: int) -> Track | None:
        """رد کردن آیتم فعلی؛ آیتم رد‌شده را برمی‌گرداند."""
        current = queues.current(chat_id)
        queues.set_loop(chat_id, 0)
        await self.play_next(chat_id)
        return current

    async def seek(self, chat_id: int, position: int) -> None:
        track = queues.current(chat_id)
        if track is None:
            raise UserError("err_no_active")
        if track.is_live:
            raise UserError("err_live_no_seek")
        if position >= track.duration:
            raise UserError("err_seek_range")
        seeked = track.clone()
        seeked.seek = max(0, position)
        await calls_service.play(chat_id, seeked)
        queues.set_current(chat_id, seeked)
        queues.set_paused(chat_id, False)

    async def set_speed(self, chat_id: int, speed: float) -> None:
        track = queues.current(chat_id)
        if track is None:
            raise UserError("err_no_active")
        played = await calls_service.played_time(chat_id)
        updated = track.clone()
        updated.speed = speed
        updated.seek = max(0, played)
        await calls_service.play(chat_id, updated)
        queues.set_current(chat_id, updated)
        queues.set_paused(chat_id, False)

    async def set_media_volume(self, chat_id: int, volume: int) -> None:
        """صدای خود رسانه (قبل از ارسال به ویس‌چت) را تغییر می‌دهد.

        برخلاف صدای ویس‌چت، این مقدار در ضبط ویس‌چت هم شنیده می‌شود؛ چون روی جریان
        اعمال می‌شود، پخش باید از همان لحظه دوباره شروع شود.
        """
        db.set_chat_setting(chat_id, "media_volume", volume)
        track = queues.current(chat_id)
        if track is None:
            return
        played = await calls_service.played_time(chat_id)
        updated = track.clone()
        updated.media_volume = volume
        if not updated.is_live:
            updated.seek = max(0, played)
        await calls_service.play(chat_id, updated)
        queues.set_current(chat_id, updated)
        queues.set_paused(chat_id, False)

    async def set_subtitle(self, chat_id: int, subtitle_path: str | None) -> Track:
        """چسباندن (یا برداشتن) زیرنویس روی پخش ویدیویی فعلی."""
        track = queues.current(chat_id)
        if track is None:
            raise UserError("err_no_active")
        if not track.video:
            raise UserError("err_subtitle_audio")
        played = await calls_service.played_time(chat_id)
        updated = track.clone()
        updated.subtitle_path = subtitle_path
        if not updated.is_live:
            updated.seek = max(0, played)
        await calls_service.play(chat_id, updated)
        queues.set_current(chat_id, updated)
        queues.set_paused(chat_id, False)
        return updated

    async def replay(self, chat_id: int) -> None:
        track = queues.current(chat_id)
        if track is None:
            raise UserError("err_no_active")
        restart = track.clone()
        restart.seek = 0
        await calls_service.play(chat_id, restart)
        queues.set_current(chat_id, restart)
        queues.set_paused(chat_id, False)

    # ── پایان پخش ────────────────────────────────────────────────────────────
    async def cleanup(self, chat_id: int, *, reason_key: str | None = None, **params) -> None:
        """خروج از ویس‌چت، پاک‌سازی صف و اطلاع‌رسانی."""
        await calls_service.leave(chat_id)
        panel = queues.panel(chat_id)
        queues.reset(chat_id)
        if panel:
            try:
                await bot.delete_messages(chat_id, panel)
            except Exception:  # noqa: BLE001
                pass
        if reason_key:
            s = strings_for(chat_id)
            message = await self._safe_send(chat_id, s(reason_key, **params))
            if message is not None and db.chat_setting(chat_id, "auto_clear", False):
                asyncio.create_task(self._delete_later(chat_id, message.id))

    async def stop(self, chat_id: int, requester: str = "") -> None:
        await self.cleanup(chat_id, reason_key="ended", requester=requester or "-")

    async def _delete_later(self, chat_id: int, message_id: int) -> None:
        """پاک‌سازی خودکار پیام پایان پخش (قابلیت «پاکسازی خودکار»)."""
        await asyncio.sleep(max(1, config.AUTO_CLEAR_SECONDS))
        try:
            await bot.delete_messages(chat_id, message_id)
        except Exception as error:  # noqa: BLE001
            LOGGER.debug("پاک‌سازی خودکار پیام در %s ناموفق بود: %s", chat_id, error)

    # ── پنل «در حال پخش» ─────────────────────────────────────────────────────
    async def send_panel(self, chat_id: int, track: Track) -> None:
        s = strings_for(chat_id)
        caption = s(
            "now_playing",
            title=track.short_title,
            duration=track.duration_text,
            kind=s(track.kind_key()),
            requester=track.requester_mention(),
        )
        keyboard = player_panel(s.language, paused=False, muted=False)

        previous = queues.panel(chat_id)
        image = None
        classic = bool(db.chat_setting(chat_id, "classic_mode", False))
        if classic:
            image = None  # حالت کلاسیک: پاسخ سادهٔ متنی بدون تصویر
        elif track.thumbnail:
            image = await now_playing_image(
                track.thumbnail,
                track.title,
                track.requester_name or "",
                track.duration,
                track.vid_id or str(abs(hash(track.title)))[:12],
            )
        elif config.PLAYER_IMAGE:
            image = config.PLAYER_IMAGE

        message = None
        try:
            if image:
                message = await bot.send_photo(
                    chat_id,
                    image,
                    caption=caption,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN,
                )
            else:
                message = await bot.send_message(
                    chat_id,
                    caption,
                    reply_markup=keyboard,
                    disable_web_page_preview=True,
                    parse_mode=ParseMode.MARKDOWN,
                )
        except Exception as error:  # noqa: BLE001
            LOGGER.warning("ارسال پنل در %s ناموفق بود: %s", chat_id, error)

        if message is not None:
            queues.set_panel(chat_id, message.id)
        if previous:
            try:
                await bot.delete_messages(chat_id, previous)
            except Exception:  # noqa: BLE001
                pass

    async def status_text(self, chat_id: int) -> str:
        """متن وضعیت پخش فعلی (برای /current و دکمهٔ بروزرسانی)."""
        s = strings_for(chat_id)
        track = queues.current(chat_id)
        if track is None:
            return s("err_no_active")
        played = await calls_service.played_time(chat_id)
        total = track.duration
        return s(
            "current_status",
            title=track.short_title,
            played=seconds_to_time(played),
            duration=track.duration_text,
            bar=progress_bar(played, total),
            requester=track.requester_mention(),
        )

    async def queue_text(self, chat_id: int, limit: int = 15) -> str:
        s = strings_for(chat_id)
        current = queues.current(chat_id)
        if current is None:
            return s("err_no_active")
        text = s("queue_header", current=current.short_title)
        items = queues.queue(chat_id)
        if not items:
            return text + s("queue_empty")
        for index, track in enumerate(items[:limit], start=1):
            text += s(
                "queue_item",
                index=index,
                title=track.short_title,
                duration=track.duration_text,
                requester=track.requester_name or "-",
            )
        if len(items) > limit:
            text += s("queue_more", count=len(items) - limit)
        return text

    # ── لاگ و پیام‌ها ────────────────────────────────────────────────────────
    async def _safe_send(self, chat_id: int, text: str, **kwargs):
        try:
            return await bot.send_message(
                chat_id, text, disable_web_page_preview=True, **kwargs
            )
        except Exception as error:  # noqa: BLE001
            LOGGER.debug("ارسال پیام به %s ناموفق بود: %s", chat_id, error)
            return None

    async def _log_play(self, chat_id: int, track: Track) -> None:
        if not config.LOGGER_ID:
            return
        s = strings_for(None)
        title = db.chat_setting(chat_id, "title", "") or str(chat_id)
        try:
            await bot.send_message(
                config.LOGGER_ID,
                s(
                    "log_play",
                    title=title,
                    chat_id=chat_id,
                    track=track.short_title,
                    user=track.requester_mention(),
                ),
                disable_web_page_preview=True,
            )
        except Exception as error:  # noqa: BLE001
            LOGGER.debug("ارسال لاگ پخش ناموفق بود: %s", error)

    # ── نگهبان (خروج خودکار) ─────────────────────────────────────────────────
    def start_watcher(self) -> None:
        if self._watcher_task is None or self._watcher_task.done():
            self._watcher_task = asyncio.create_task(self._watcher_loop())

    async def _watcher_loop(self) -> None:
        interval = max(10, config.WATCHER_INTERVAL_SECONDS)
        while True:
            await asyncio.sleep(interval)
            try:
                await self._watch_once()
            except asyncio.CancelledError:
                raise
            except Exception as error:  # noqa: BLE001
                LOGGER.debug("نگهبان: %s", error)

    async def _watch_once(self) -> None:
        now = time()
        for chat_id in list(queues.active_chats()):
            if not await calls_service.is_connected(chat_id):
                await self.cleanup(chat_id)
                continue

            auto_leave = db.chat_setting(chat_id, "auto_leave", config.AUTO_LEAVE_ASSISTANT)
            if not auto_leave:
                continue

            listeners = await calls_service.listeners_count(chat_id)
            if listeners == 0:
                empty_since = queues.mark_empty(chat_id)
                if now - empty_since >= config.EMPTY_CALL_TIMEOUT_SECONDS:
                    await self.cleanup(chat_id, reason_key="auto_left_empty")
                    continue
            elif listeners > 0:
                queues.clear_empty(chat_id)

            if queues.is_paused(chat_id):
                last = queues.last_activity(chat_id) or queues.started_at(chat_id)
                if last and now - last >= config.INACTIVE_TIMEOUT_SECONDS:
                    await self.cleanup(chat_id, reason_key="auto_left_inactive")

    # ── آمار ─────────────────────────────────────────────────────────────────
    def stats(self) -> dict[str, object]:
        return {
            "chats": len(db.served_chats()),
            "users": len(db.served_users()),
            "plays": db.total_plays(),
            "active": len(queues.active_chats()),
            "assistants": len(active_assistants()),
            "version": __version__,
        }


player = PlayerService()


async def resolve_and_play(
    chat_id: int,
    query: str,
    *,
    video: bool,
    requester_id: int,
    requester_name: str,
    force: bool = False,
    download: bool = False,
) -> tuple[str, int, Track]:
    """میان‌بر: تبدیل عبارت به آیتم و پخش/صف کردن آن."""
    limit = db.chat_setting(chat_id, "duration_limit", config.DURATION_LIMIT_MINUTES)
    resolved = await resolver.resolve_query(
        query,
        video=video,
        requester_id=requester_id,
        requester_name=requester_name,
        limit_minutes=limit,
        download=download,
    )
    first = resolved.first
    if first is None:
        raise NoResult()
    state, position = await player.play_or_queue(chat_id, first, force=force)
    for extra in resolved.tracks[1:]:
        if queues.size(chat_id) >= config.QUEUE_LIMIT:
            break
        queues.add(chat_id, extra)
    return state, position, first
