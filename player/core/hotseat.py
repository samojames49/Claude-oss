"""بازی «صندلی داغ» ویس‌چت: هر لحظه فقط یک مهمان مایک باز دارد.

مهمان‌ها یک صف دارند؛ با تمام‌شدن زمان نوبت (یا دستور «مهمان بعدی») مایک مهمان فعلی
بسته و مایک نفر بعد باز می‌شود. برای بستن/بازکردن مایک، اسیستنت باید در گروه ادمین با
دسترسی «مدیریت ویدیو چت» باشد؛ بدون آن بازی فقط نوبت‌ها را اعلام می‌کند و پیام هشدار
همراه اعلان نوبت می‌آید.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass, field
from time import time

from .. import config
from ..utils.logger import get_logger
from .calls import calls_service
from .errors import UserError

LOGGER = get_logger("hotseat")

TICK_SECONDS = 2


@dataclass
class Guest:
    user_id: int
    name: str

    @property
    def mention(self) -> str:
        return f"[{self.name or self.user_id}](tg://user?id={self.user_id})"


@dataclass
class Session:
    """یک دور بازی در یک گروه."""

    chat_id: int
    host_id: int
    seconds: int
    queue: list[Guest] = field(default_factory=list)
    current: Guest | None = None
    turn_started: float = 0.0
    paused_left: int | None = None  # زمان باقی‌ماندهٔ نوبت در لحظهٔ توقف
    message_id: int | None = None
    served: int = 0
    mic_failed: bool = False
    muted: set[int] = field(default_factory=set)

    @property
    def paused(self) -> bool:
        return self.paused_left is not None

    @property
    def unlimited(self) -> bool:
        return self.seconds <= 0

    def waiting(self) -> list[Guest]:
        return list(self.queue)

    def size(self) -> int:
        return len(self.queue) + (1 if self.current else 0)

    def has(self, user_id: int) -> bool:
        if self.current is not None and self.current.user_id == user_id:
            return True
        return any(guest.user_id == user_id for guest in self.queue)

    def remaining(self, now: float | None = None) -> int:
        """ثانیهٔ باقی‌ماندهٔ نوبت؛ ‎-1 یعنی نوبت بی‌زمان است."""
        if self.unlimited:
            return -1
        if self.paused_left is not None:
            return max(0, self.paused_left)
        return max(0, self.seconds - int((now or time()) - self.turn_started))


SessionHook = Callable[[Session], Awaitable[None]]


class HotSeatService:
    """صف مهمان‌ها، نوبت‌ها و مایک‌ها را برای هر گروه نگه می‌دارد."""

    def __init__(self) -> None:
        self._sessions: dict[int, Session] = {}
        self._task: asyncio.Task | None = None
        # پلاگین صندلی داغ این دو را پر می‌کند تا اعلان‌ها در گروه فرستاده شوند
        self.on_turn: SessionHook | None = None
        self.on_finish: SessionHook | None = None

    # ── وضعیت ────────────────────────────────────────────────────────────────
    def session(self, chat_id: int) -> Session | None:
        return self._sessions.get(chat_id)

    def is_active(self, chat_id: int) -> bool:
        return chat_id in self._sessions

    def active_chats(self) -> list[int]:
        return list(self._sessions)

    def _require(self, chat_id: int) -> Session:
        session = self._sessions.get(chat_id)
        if session is None:
            raise UserError("hotseat_not_active")
        return session

    # ── چرخهٔ بازی ────────────────────────────────────────────────────────────
    async def start(
        self,
        chat_id: int,
        host_id: int,
        guests: Iterable[Guest] = (),
        seconds: int | None = None,
    ) -> Session:
        if self.is_active(chat_id):
            raise UserError("hotseat_already")
        turn = config.HOTSEAT_TURN_SECONDS if seconds is None else max(0, seconds)
        session = Session(chat_id=chat_id, host_id=host_id, seconds=turn)
        for guest in guests:
            if not session.has(guest.user_id) and len(session.queue) < config.HOTSEAT_MAX_GUESTS:
                session.queue.append(guest)
        self._sessions[chat_id] = session
        self._ensure_loop()
        await self._seat_next(session)
        LOGGER.info("صندلی داغ در %s شروع شد (%s مهمان).", chat_id, session.size())
        return session

    async def add(self, chat_id: int, guest: Guest) -> bool:
        """افزودن مهمان به صف؛ False یعنی از قبل در بازی بوده است."""
        session = self._require(chat_id)
        if session.has(guest.user_id):
            return False
        if session.size() >= config.HOTSEAT_MAX_GUESTS:
            raise UserError("hotseat_limit", limit=config.HOTSEAT_MAX_GUESTS)
        session.queue.append(guest)
        if session.current is None:
            await self._seat_next(session)
        return True

    async def remove(self, chat_id: int, user_id: int) -> Guest | None:
        """حذف مهمان؛ اگر روی صندلی نشسته باشد نوبت به نفر بعد می‌رسد."""
        session = self._require(chat_id)
        if session.current is not None and session.current.user_id == user_id:
            guest = session.current
            await self._silence(session, guest.user_id)
            session.current = None
            await self._seat_next(session)
            return guest
        for position, guest in enumerate(session.queue):
            if guest.user_id == user_id:
                return session.queue.pop(position)
        return None

    async def advance(self, chat_id: int) -> Guest | None:
        """دادن نوبت به مهمان بعدی؛ None یعنی مهمانی در صف نمانده است."""
        session = self._require(chat_id)
        if session.current is not None:
            await self._silence(session, session.current.user_id)
            session.current = None
        return await self._seat_next(session)

    def pause(self, chat_id: int) -> Session:
        session = self._require(chat_id)
        if not session.paused:
            session.paused_left = session.remaining()
        return session

    def resume(self, chat_id: int) -> Session:
        session = self._require(chat_id)
        if session.paused:
            left = session.paused_left or 0
            session.paused_left = None
            if not session.unlimited:
                session.turn_started = time() - (session.seconds - left)
        return session

    async def stop(self, chat_id: int) -> Session | None:
        """پایان بازی و بازگرداندن مایک کسانی که خودمان بسته بودیم."""
        session = self._sessions.pop(chat_id, None)
        if session is None:
            return None
        if session.current is not None:
            await self._silence(session, session.current.user_id)
        await self._restore(session)
        LOGGER.info("صندلی داغ %s پایان یافت (%s نوبت).", chat_id, session.served)
        return session

    # ── مایک‌ها ───────────────────────────────────────────────────────────────
    async def _seat_next(self, session: Session) -> Guest | None:
        if not session.queue:
            session.current = None
            return None
        guest = session.queue.pop(0)
        session.current = guest
        session.served += 1
        session.turn_started = time()
        session.paused_left = None
        await self._open_mic(session, guest.user_id)
        return guest

    async def _open_mic(self, session: Session, user_id: int) -> None:
        opened = await calls_service.set_participant_muted(session.chat_id, user_id, False)
        session.mic_failed = not opened
        if opened:
            await self._mute_others(session, user_id)

    async def _mute_others(self, session: Session, keep: int) -> None:
        participants = await calls_service.raw_participants(session.chat_id)
        if not participants:
            return
        assistant_id = calls_service.assistant(session.chat_id).id
        for participant in participants:
            user_id = int(getattr(getattr(participant, "peer", None), "user_id", 0) or 0)
            if not user_id or user_id in (keep, assistant_id):
                continue
            if getattr(participant, "left", False) or getattr(participant, "muted", False):
                continue
            if await calls_service.set_participant_muted(session.chat_id, user_id, True):
                session.muted.add(user_id)

    async def _silence(self, session: Session, user_id: int) -> None:
        await calls_service.set_participant_muted(session.chat_id, user_id, True)
        session.muted.discard(user_id)

    async def _restore(self, session: Session) -> None:
        for user_id in list(session.muted):
            await calls_service.set_participant_muted(session.chat_id, user_id, False)
        session.muted.clear()

    # ── حلقهٔ زمان‌سنج ─────────────────────────────────────────────────────────
    def _ensure_loop(self) -> None:
        if self._task is not None and not self._task.done():
            return
        try:
            self._task = asyncio.create_task(self._loop())
        except RuntimeError:  # حلقهٔ رویداد فعال نیست (مثلاً در تست‌های همگام)
            self._task = None

    async def _loop(self) -> None:
        while self._sessions:
            await asyncio.sleep(TICK_SECONDS)
            for chat_id in self.active_chats():
                try:
                    await self.tick(chat_id)
                except asyncio.CancelledError:
                    raise
                except Exception as error:  # noqa: BLE001
                    LOGGER.debug("نوبت صندلی داغ %s بررسی نشد: %s", chat_id, error)

    async def tick(self, chat_id: int) -> None:
        """اگر زمان نوبت تمام شده باشد، نوبت را جلو می‌برد یا بازی را می‌بندد."""
        session = self._sessions.get(chat_id)
        if session is None or session.paused or session.current is None:
            return
        if session.remaining() != 0:
            return
        guest = await self.advance(chat_id)
        if guest is None:
            await self.stop(chat_id)
            await self._notify(self.on_finish, session)
            return
        await self._notify(self.on_turn, session)

    async def _notify(self, hook: SessionHook | None, session: Session) -> None:
        if hook is None:
            return
        try:
            await hook(session)
        except Exception as error:  # noqa: BLE001
            LOGGER.debug("اعلان صندلی داغ %s ناموفق بود: %s", session.chat_id, error)


hotseat = HotSeatService()
