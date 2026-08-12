"""امنیت کال: تشخیص رفتارهای مشکوک در ویس‌چت و میوت خودکار ورودی‌ها.

تحلیل روی نمونه‌های دوره‌ای لیست شرکت‌کنندگان انجام می‌شود (همان نمونه‌هایی که آمار
کال از آن‌ها ساخته می‌شود) تا درخواست اضافه‌ای به تلگرام زده نشود.

برای میوت کردن اعضا، اسیستنت باید در گروه ادمین با دسترسی «مدیریت ویدیو چت» باشد؛
بدون آن بخش تشخیص و گزارش کار می‌کند ولی میوت انجام نمی‌شود.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from time import time

from .. import config
from ..utils.formatters import seconds_to_clock
from ..utils.logger import get_logger
from .admins import load_admins
from .calls import calls_service
from .db import db

LOGGER = get_logger("security")

# کلیدهای رفتار مشکوک (هرکدام یک رشتهٔ ترجمه‌شده دارد: security_event_<key>)
EVENT_REJOIN = "rejoin"
EVENT_UNMUTED_JOIN = "unmuted_join"
EVENT_VIDEO_REJOIN = "video_rejoin"
EVENT_MULTI_SOURCE = "multi_source"
EVENT_MULTI_ENDPOINT = "multi_endpoint"
EVENT_TIME_GAP = "time_gap"


@dataclass
class MemberState:
    """وضعیت یک عضو ویس‌چت بین نمونه‌ها."""

    joins: int = 0
    video_joins: int = 0
    sources: set[int] = field(default_factory=set)
    endpoints: set[str] = field(default_factory=set)
    join_dates: set[int] = field(default_factory=set)
    present: bool = False
    first_seen: float = field(default_factory=time)
    reported: set[str] = field(default_factory=set)


@dataclass
class CallEvent:
    at: float
    user_id: int
    key: str


def enabled(chat_id: int) -> bool:
    return bool(db.chat_setting(chat_id, "call_security", config.CALL_SECURITY_ENABLED))


def min_age_days(chat_id: int) -> int:
    value = db.chat_setting(chat_id, "security_min_age_days", None)
    if value is None:
        return config.CALL_SECURITY_MIN_AGE_DAYS
    return max(0, int(value))


def _peer_user_id(peer) -> int:
    return int(getattr(peer, "user_id", 0) or 0)


def _endpoint(participant) -> str:
    """نقطهٔ پایانی جریان ویدیویی عضو (برای تشخیص خروجی‌های متعدد)."""
    for attribute in ("video", "presentation"):
        stream = getattr(participant, attribute, None)
        endpoint = getattr(stream, "endpoint", None)
        if endpoint:
            return str(endpoint)
    return ""


class CallSecurityService:
    """حافظهٔ رفتار اعضا در ویس‌چت هر گروه و تشخیص موارد مشکوک."""

    def __init__(self) -> None:
        self._members: dict[int, dict[int, MemberState]] = {}
        self._events: dict[int, list[CallEvent]] = {}
        self._muted: dict[int, set[int]] = {}
        self._opened_at: dict[int, float] = {}

    # ── چرخهٔ حیات ────────────────────────────────────────────────────────────
    def start_session(self, chat_id: int) -> None:
        self._members[chat_id] = {}
        self._events[chat_id] = []
        self._muted[chat_id] = set()
        self._opened_at[chat_id] = time()

    def end_session(self, chat_id: int) -> None:
        self._members.pop(chat_id, None)
        self._events.pop(chat_id, None)
        self._muted.pop(chat_id, None)
        self._opened_at.pop(chat_id, None)

    def events(self, chat_id: int) -> list[CallEvent]:
        return list(self._events.get(chat_id, []))

    # ── تحلیل ────────────────────────────────────────────────────────────────
    async def analyze(self, chat_id: int, participants: list) -> list[CallEvent]:
        """بررسی یک نمونه از شرکت‌کنندگان؛ رویدادهای مشکوکِ تازه را برمی‌گرداند."""
        if not enabled(chat_id):
            return []

        members = self._members.setdefault(chat_id, {})
        if chat_id not in self._opened_at:
            self._opened_at[chat_id] = time()

        privileged = await self._privileged_ids(chat_id)
        seen: set[int] = set()
        fresh: list[CallEvent] = []
        max_joins = max(1, config.CALL_SECURITY_MAX_JOINS)

        for participant in participants:
            user_id = _peer_user_id(getattr(participant, "peer", None))
            if not user_id or getattr(participant, "left", False):
                continue
            seen.add(user_id)
            state = members.setdefault(user_id, MemberState())
            is_new = not state.present
            state.present = True

            join_date = int(getattr(participant, "date", 0) or 0)
            if join_date:
                if state.join_dates and join_date not in state.join_dates:
                    # تاریخ ورود عوض شده بی‌آنکه عضو خارج شده باشد
                    fresh += self._record(chat_id, state, user_id, EVENT_TIME_GAP)
                state.join_dates.add(join_date)

            if is_new:
                state.joins += 1
                if state.joins > max_joins:
                    fresh += self._record(chat_id, state, user_id, EVENT_REJOIN)
                if user_id not in privileged and getattr(participant, "muted", None) is False:
                    fresh += self._record(chat_id, state, user_id, EVENT_UNMUTED_JOIN)

            source = int(getattr(participant, "source", 0) or 0)
            if source:
                state.sources.add(source)
                if len(state.sources) > 1:
                    fresh += self._record(chat_id, state, user_id, EVENT_MULTI_SOURCE)

            endpoint = _endpoint(participant)
            if endpoint:
                state.endpoints.add(endpoint)
                if len(state.endpoints) > 1:
                    fresh += self._record(chat_id, state, user_id, EVENT_MULTI_ENDPOINT)

            if getattr(participant, "video_joined", False):
                if is_new or not state.video_joins:
                    state.video_joins += 1
                if state.video_joins > 1:
                    fresh += self._record(chat_id, state, user_id, EVENT_VIDEO_REJOIN)

            if is_new:
                await self._maybe_mute(chat_id, user_id, participant, privileged)

        for user_id, state in members.items():
            if user_id not in seen:
                state.present = False
                state.video_joins = 0

        return fresh

    def _record(self, chat_id: int, state: MemberState, user_id: int, key: str) -> list[CallEvent]:
        """ثبت یک‌بارهٔ هر نوع رفتار برای هر عضو (تا گروه از گزارش پر نشود)."""
        if key in state.reported:
            return []
        state.reported.add(key)
        event = CallEvent(at=time(), user_id=user_id, key=key)
        self._events.setdefault(chat_id, []).append(event)
        return [event]

    async def _privileged_ids(self, chat_id: int) -> set[int]:
        """کسانی که امنیت کال روی آن‌ها اعمال نمی‌شود: ادمین‌ها، کاربران مجاز و سودوها."""
        ids = set(await load_admins(chat_id))
        ids |= {int(key) for key in db.auth_users(chat_id) if str(key).lstrip("-").isdigit()}
        ids |= db.sudoers()
        return ids

    async def _maybe_mute(self, chat_id: int, user_id: int, participant, privileged: set[int]) -> None:
        """میوت ورودی کال برای کاربران عادی و اکانت‌های تازه‌وارد."""
        if not db.chat_setting(chat_id, "security_mute_on_join", False):
            return
        if user_id in privileged or getattr(participant, "is_self", False):
            return
        if await self._is_old_member(chat_id, user_id):
            return
        if await calls_service.set_participant_muted(chat_id, user_id, True):
            self._muted.setdefault(chat_id, set()).add(user_id)

    async def _is_old_member(self, chat_id: int, user_id: int) -> bool:
        """آیا عضویت کاربر در گروه از «قدمت اکانت» تعیین‌شده قدیمی‌تر است؟"""
        days = min_age_days(chat_id)
        if days <= 0:
            return True
        try:
            member = await calls_service.assistant(chat_id).client.get_chat_member(chat_id, user_id)
        except Exception:  # noqa: BLE001
            return False
        joined = getattr(member, "joined_date", None)
        if joined is None:
            # اعضای قدیمی گروه‌های معمولی تاریخ عضویت ندارند؛ محدودشان نمی‌کنیم
            return True
        if isinstance(joined, datetime):
            joined_ts = joined.timestamp()
        else:
            joined_ts = float(joined)
        return (time() - joined_ts) >= days * 86400

    # ── گزارش ────────────────────────────────────────────────────────────────
    def report_lines(self, s, events: list[CallEvent]) -> list[str]:
        return [
            s(
                "security_event_line",
                user=f"[{event.user_id}](tg://user?id={event.user_id})",
                event=s(f"security_event_{event.key}"),
            )
            for event in events
        ]

    def summary_text(self, chat_id: int, s) -> str | None:
        """خلاصهٔ متنی رفتارهای مشکوک برای ارسال به‌صورت فایل هنگام بسته‌شدن کال."""
        events = self.events(chat_id)
        if not events:
            return None
        started = self._opened_at.get(chat_id, time())
        lines = [
            s("security_summary_title"),
            s("security_summary_meta", chat_id=chat_id, duration=seconds_to_clock(time() - started)),
            "",
        ]
        for event in events:
            stamp = datetime.fromtimestamp(event.at).strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"[{stamp}] {event.user_id} — {s(f'security_event_{event.key}')}")
        counts: dict[str, int] = {}
        for event in events:
            counts[event.key] = counts.get(event.key, 0) + 1
        lines += ["", s("security_summary_totals")]
        for key, count in sorted(counts.items(), key=lambda item: item[1], reverse=True):
            lines.append(f"• {s(f'security_event_{key}')}: {count}")
        return "\n".join(lines)


security = CallSecurityService()
