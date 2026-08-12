"""لایهٔ ارتباط با ویس‌چت (PyTgCalls) — ورود، پخش، کنترل و خروج."""

from __future__ import annotations

import asyncio
from typing import Any

from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import (
    ChannelInvalid,
    ChannelPrivate,
    ChatAdminRequired,
    FloodWait,
    InviteHashExpired,
    InviteRequestSent,
    UserAlreadyParticipant,
    UserNotParticipant,
)
from pytgcalls.exceptions import NoActiveGroupCall, NotInCallError
from pytgcalls.types import (
    AudioQuality,
    GroupCallConfig,
    MediaStream,
    VideoQuality,
)

from .. import config
from ..utils.logger import get_logger
from .clients import Assistant, active_assistants, assistant_for, bot
from .errors import AssistantBanned, AssistantJoinError, NoVoiceChat, UserError
from .track import Track

LOGGER = get_logger("calls")


def audio_quality() -> AudioQuality:
    return getattr(AudioQuality, config.AUDIO_QUALITY_MAP[config.AUDIO_QUALITY])


def video_quality() -> VideoQuality:
    return getattr(VideoQuality, config.VIDEO_QUALITY_MAP[config.VIDEO_QUALITY])


def build_stream(track: Track) -> MediaStream:
    """ساخت MediaStream مناسب برای یک آیتم پخش."""
    ffmpeg_parameters: list[str] = []
    if track.seek > 0:
        ffmpeg_parameters += ["-ss", str(int(track.seek))]
    if track.speed and abs(track.speed - 1.0) > 0.01:
        # فیلتر atempo باید بعد از ورودی بیاید (نشانهٔ -atmid در pytgcalls)
        ffmpeg_parameters += ["--audio", "-atmid", "-af", f"atempo={track.speed:g}"]

    source = track.file_path or track.source
    audio_source = None if track.file_path else track.audio_source
    return MediaStream(
        source,
        audio_path=audio_source,
        audio_parameters=audio_quality(),
        video_parameters=video_quality(),
        video_flags=(
            MediaStream.Flags.AUTO_DETECT if track.video else MediaStream.Flags.IGNORE
        ),
        audio_flags=MediaStream.Flags.REQUIRED,
        headers=track.headers or None,
        ffmpeg_parameters=" ".join(ffmpeg_parameters) if ffmpeg_parameters else None,
    )


class CallsService:
    """کارهای سطح‌پایین ویس‌چت را روی اسیستنت مربوط به هر گروه انجام می‌دهد."""

    def __init__(self) -> None:
        self._join_locks: dict[int, asyncio.Lock] = {}

    # ── اسیستنت ──────────────────────────────────────────────────────────────
    def assistant(self, chat_id: int) -> Assistant:
        return assistant_for(chat_id)

    def _lock(self, chat_id: int) -> asyncio.Lock:
        return self._join_locks.setdefault(chat_id, asyncio.Lock())

    async def ensure_assistant(self, chat_id: int) -> Assistant:
        """اطمینان از عضویت اسیستنت در گروه؛ در صورت نبود، عضو می‌شود."""
        assistant = self.assistant(chat_id)
        async with self._lock(chat_id):
            try:
                member = await assistant.client.get_chat_member(chat_id, assistant.id)
                if member.status == ChatMemberStatus.BANNED:
                    raise AssistantBanned(assistant.mention)
                return assistant
            except UserNotParticipant:
                pass
            except (ChannelInvalid, ChannelPrivate):
                pass
            except AssistantBanned:
                raise
            except Exception as error:  # noqa: BLE001
                LOGGER.debug("بررسی عضویت اسیستنت در %s: %s", chat_id, error)

            invite_link = await self._invite_link(chat_id)
            try:
                await assistant.client.join_chat(invite_link)
            except UserAlreadyParticipant:
                return assistant
            except InviteRequestSent:
                raise AssistantJoinError("درخواست عضویت اسیستنت ارسال شد؛ آن را تایید کنید.")
            except InviteHashExpired:
                raise AssistantJoinError("لینک دعوت گروه منقضی شده است.")
            except FloodWait as error:
                raise AssistantJoinError(f"محدودیت فلود: {error.value} ثانیه صبر کنید.")
            except Exception as error:  # noqa: BLE001
                raise AssistantJoinError(str(error)) from error
            await asyncio.sleep(1)
            return assistant

    async def _invite_link(self, chat_id: int) -> str:
        chat = await bot.get_chat(chat_id)
        if getattr(chat, "username", None):
            return chat.username
        link = getattr(chat, "invite_link", None)
        if not link:
            try:
                link = await bot.export_chat_invite_link(chat_id)
            except ChatAdminRequired:
                raise AssistantJoinError("ربات باید ادمین گروه باشد تا اسیستنت را وارد کند.")
            except Exception as error:  # noqa: BLE001
                raise AssistantJoinError(str(error)) from error
        return link

    async def leave_chat(self, chat_id: int) -> None:
        """خروج کامل اسیستنت از گروه (نه فقط ویس‌چت)."""
        assistant = self.assistant(chat_id)
        try:
            await assistant.client.leave_chat(chat_id)
        except Exception as error:  # noqa: BLE001
            LOGGER.debug("خروج اسیستنت از %s: %s", chat_id, error)

    # ── پخش ──────────────────────────────────────────────────────────────────
    async def play(self, chat_id: int, track: Track) -> Assistant:
        assistant = await self.ensure_assistant(chat_id)
        stream = build_stream(track)
        try:
            await assistant.calls.play(
                chat_id,
                stream,
                config=GroupCallConfig(auto_start=False),
            )
        except NoActiveGroupCall as error:
            raise NoVoiceChat() from error
        return assistant

    async def pause(self, chat_id: int) -> bool:
        return await self._safe_call(chat_id, "pause")

    async def resume(self, chat_id: int) -> bool:
        return await self._safe_call(chat_id, "resume")

    async def mute(self, chat_id: int) -> bool:
        return await self._safe_call(chat_id, "mute")

    async def unmute(self, chat_id: int) -> bool:
        return await self._safe_call(chat_id, "unmute")

    async def _safe_call(self, chat_id: int, method: str) -> bool:
        assistant = self.assistant(chat_id)
        try:
            return bool(await getattr(assistant.calls, method)(chat_id))
        except NotInCallError as error:
            raise UserError("err_no_active") from error

    async def set_volume(self, chat_id: int, volume: int) -> None:
        assistant = self.assistant(chat_id)
        try:
            await assistant.calls.change_volume_call(chat_id, volume)
        except NotInCallError as error:
            raise UserError("err_no_active") from error

    async def leave(self, chat_id: int) -> None:
        assistant = self.assistant(chat_id)
        try:
            await assistant.calls.leave_call(chat_id)
        except (NotInCallError, NoActiveGroupCall):
            pass
        except Exception as error:  # noqa: BLE001
            LOGGER.debug("خروج از ویس‌چت %s: %s", chat_id, error)

    async def played_time(self, chat_id: int) -> int:
        assistant = self.assistant(chat_id)
        try:
            return int(await assistant.calls.time(chat_id))
        except Exception:  # noqa: BLE001
            return 0

    async def is_connected(self, chat_id: int) -> bool:
        assistant = self.assistant(chat_id)
        try:
            calls = await assistant.calls.calls
            return chat_id in calls
        except Exception:  # noqa: BLE001
            return False

    async def participants(self, chat_id: int) -> list[Any]:
        assistant = self.assistant(chat_id)
        try:
            return list(await assistant.calls.get_participants(chat_id) or [])
        except Exception:  # noqa: BLE001
            return []

    async def listeners_count(self, chat_id: int) -> int:
        """تعداد شنوندگان واقعی (بدون حساب کردن خود اسیستنت)."""
        assistant = self.assistant(chat_id)
        people = await self.participants(chat_id)
        return len([person for person in people if getattr(person, "user_id", 0) != assistant.id])

    def ping(self) -> float:
        """میانگین پینگ هستهٔ صوتی روی اسیستنت‌های فعال."""
        pings = []
        for assistant in active_assistants():
            try:
                pings.append(float(assistant.calls.ping))
            except Exception:  # noqa: BLE001
                continue
        return round(sum(pings) / len(pings), 2) if pings else 0.0


calls_service = CallsService()
