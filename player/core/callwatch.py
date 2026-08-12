"""نمونه‌بردار ویس‌چت: خوراک‌دهندهٔ «آمار کال» و «امنیت کال».

هر بازه یک‌بار لیست شرکت‌کنندگان هر ویس‌چت باز خوانده می‌شود و همان یک نمونه هم به
آمار و هم به تحلیل امنیتی داده می‌شود؛ پس افزودن این دو قابلیت بار اضافه‌ای روی
تلگرام نمی‌گذارد.
"""

from __future__ import annotations

import asyncio
from time import time

from .. import config
from ..utils.logger import get_logger
from . import callstats
from .calls import calls_service
from .clients import assistant_for, bot
from .db import db
from .hotseat import hotseat
from .lang import strings_for
from .security import security

LOGGER = get_logger("callwatch")


class CallWatchService:
    def __init__(self) -> None:
        self._open: dict[int, float] = {}  # chat_id → زمان آخرین نمونه
        self._task: asyncio.Task | None = None

    # ── باز/بسته شدن ویس‌چت ───────────────────────────────────────────────────
    def is_open(self, chat_id: int) -> bool:
        return chat_id in self._open

    def mark_open(self, chat_id: int) -> None:
        if chat_id in self._open:
            return
        self._open[chat_id] = time()
        db.apply_call_stats_reset(chat_id)
        security.start_session(chat_id)
        LOGGER.info("ویس‌چت %s باز شد؛ پایش شروع شد.", chat_id)

    async def mark_closed(self, chat_id: int) -> None:
        """آخرین نمونه را ثبت و گزارش‌های پایان کال را ارسال می‌کند."""
        if hotseat.is_active(chat_id):
            # با بسته‌شدن ویس‌چت، بازی صندلی داغ هم بی‌معنا می‌شود
            session = await hotseat.stop(chat_id)
            if session is not None:
                s = strings_for(chat_id)
                await self._send(chat_id, s("hotseat_finished", served=session.served))
        if chat_id not in self._open:
            return
        await self._sample(chat_id, closing=True)
        self._open.pop(chat_id, None)
        await self._on_close(chat_id)
        security.end_session(chat_id)
        LOGGER.info("ویس‌چت %s بسته شد؛ پایش پایان یافت.", chat_id)

    # ── حلقهٔ نمونه‌برداری ────────────────────────────────────────────────────
    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._loop())

    async def _loop(self) -> None:
        interval = max(15, config.CALL_STATS_INTERVAL_SECONDS)
        while True:
            await asyncio.sleep(interval)
            for chat_id in list(self._open):
                try:
                    await self._sample(chat_id)
                except asyncio.CancelledError:
                    raise
                except Exception as error:  # noqa: BLE001
                    LOGGER.debug("نمونه‌برداری ویس‌چت %s ناموفق بود: %s", chat_id, error)

    async def _sample(self, chat_id: int, *, closing: bool = False) -> None:
        track_stats = callstats.stats_enabled(chat_id)
        check_security = security.enabled(chat_id)
        if not track_stats and not check_security:
            return

        participants = await calls_service.raw_participants(chat_id)
        if participants is None:
            if not closing:
                await self.mark_closed(chat_id)
            return

        now = time()
        elapsed = int(min(now - self._open.get(chat_id, now), config.CALL_STATS_INTERVAL_SECONDS * 2))
        self._open[chat_id] = now

        if track_stats and elapsed > 0:
            await self._record_presence(chat_id, participants, elapsed)

        if check_security:
            events = await security.analyze(chat_id, participants)
            if events and db.chat_setting(chat_id, "security_report", True):
                s = strings_for(chat_id)
                lines = security.report_lines(s, events)
                await self._send(chat_id, s("security_report_header") + "\n".join(lines))

    async def _record_presence(self, chat_id: int, participants: list, elapsed: int) -> None:
        assistant_id = assistant_for(chat_id).id
        user_ids: list[int] = []
        for participant in participants:
            user_id = int(getattr(getattr(participant, "peer", None), "user_id", 0) or 0)
            if not user_id or user_id == assistant_id:
                continue
            if getattr(participant, "left", False):
                continue
            user_ids.append(user_id)
        if not user_ids:
            return
        names = await self._resolve_names(chat_id, user_ids)
        callstats.accumulate(chat_id, user_ids, elapsed, names)

    async def _resolve_names(self, chat_id: int, user_ids: list[int]) -> dict[int, str]:
        """نام کاربرانی که هنوز در دیتابیس ثبت نشده‌اند را می‌گیرد."""
        unknown = [uid for uid in user_ids if not db.call_user_name(chat_id, uid)]
        if not unknown:
            return {}
        names: dict[int, str] = {}
        client = assistant_for(chat_id).client
        for start in range(0, len(unknown[:50]), 25):
            chunk = unknown[start : start + 25]
            try:
                users = await client.get_users(chunk)
            except Exception as error:  # noqa: BLE001
                LOGGER.debug("خواندن نام اعضای کال ناموفق بود: %s", error)
                continue
            for user in users if isinstance(users, list) else [users]:
                name = (getattr(user, "first_name", "") or "").strip() or (
                    getattr(user, "username", "") or ""
                )
                if name:
                    names[user.id] = name
                    db.set_call_user_name(chat_id, user.id, name)
        return names

    # ── پایان کال ────────────────────────────────────────────────────────────
    async def _on_close(self, chat_id: int) -> None:
        s = strings_for(chat_id)
        if callstats.stats_enabled(chat_id) and db.chat_setting(chat_id, "call_stats_auto", False):
            text = callstats.render(
                chat_id, s, [callstats.today_key()], title=s("callstats_title_today")
            )
            await self._send(chat_id, text)

        if security.enabled(chat_id) and db.chat_setting(chat_id, "security_summary", True):
            summary = security.summary_text(chat_id, s)
            if summary:
                await self._send_summary_file(chat_id, summary, s)

    async def _send_summary_file(self, chat_id: int, summary: str, s) -> None:
        from io import BytesIO

        document = BytesIO(summary.encode("utf-8"))
        document.name = f"call_security_{abs(chat_id)}.txt"
        try:
            await bot.send_document(chat_id, document, caption=s("security_summary_caption"))
        except Exception as error:  # noqa: BLE001
            LOGGER.debug("ارسال خلاصهٔ امنیت کال به %s ناموفق بود: %s", chat_id, error)

    async def _send(self, chat_id: int, text: str) -> None:
        try:
            await bot.send_message(chat_id, text, disable_web_page_preview=True)
        except Exception as error:  # noqa: BLE001
            LOGGER.debug("ارسال پیام پایش کال به %s ناموفق بود: %s", chat_id, error)


callwatch = CallWatchService()
