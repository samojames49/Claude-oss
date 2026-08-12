"""لایهٔ ارتباط با ویس‌چت (PyTgCalls) — ورود، پخش، کنترل و خروج."""

from __future__ import annotations

import asyncio
from typing import Any

from pyrogram import raw
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


def _subtitle_filter(path: str) -> str:
    """فیلتر زیرنویس ffmpeg برای یک مسیر دلخواه.

    مسیر دو مرحله فرار می‌خورد: یک‌بار برای پارسر فیلترگراف ffmpeg (که `:` و `'` را
    جداکننده می‌داند) و یک‌بار برای `shlex` که pytgcalls رشتهٔ پارامترها را با آن
    می‌شکند؛ گیومهٔ دوتایی لازم است تا مسیرهای دارای فاصله یک آرگومان بمانند.
    """
    for_ffmpeg = path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    for_shlex = for_ffmpeg.replace("\\", "\\\\").replace('"', '\\"')
    return f'subtitles="{for_shlex}"'


def build_stream(track: Track) -> MediaStream:
    """ساخت MediaStream مناسب برای یک آیتم پخش."""
    ffmpeg_parameters: list[str] = []
    if track.seek > 0:
        ffmpeg_parameters += ["-ss", str(int(track.seek))]

    # فیلترهای صوتی باید در یک ‎-af جمع شوند؛ ffmpeg فقط آخرین ‎-af را می‌بیند.
    audio_filters: list[str] = []
    if track.speed and abs(track.speed - 1.0) > 0.01:
        audio_filters.append(f"atempo={track.speed:g}")
    if track.media_volume and track.media_volume != 100:
        audio_filters.append(f"volume={max(1, track.media_volume) / 100:g}")
    if audio_filters:
        # نشانهٔ -atmid یعنی این پارامترها بعد از ورودی (‎-i) بیایند
        ffmpeg_parameters += ["--audio", "-atmid", "-af", ",".join(audio_filters)]

    if track.video and track.subtitle_path:
        # pytgcalls خودش ‎-vf scale=… را بعد از mid اضافه می‌کند و ffmpeg تنها آخرین ‎-vf را
        # اعمال می‌کند؛ پس زیرنویس و مقیاس را با هم در انتهای دستور می‌گذاریم.
        width, height, _ = video_quality().value
        ffmpeg_parameters += [
            "--video",
            "-vtend",
            "-vf",
            f"{_subtitle_filter(track.subtitle_path)},scale={width}:{height}",
        ]

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

    async def participants(self, chat_id: int) -> list[Any] | None:
        """لیست شرکت‌کنندگان ویس‌چت؛ در صورت خطا None (یعنی «نامعلوم»)."""
        assistant = self.assistant(chat_id)
        try:
            return list(await assistant.calls.get_participants(chat_id) or [])
        except Exception as error:  # noqa: BLE001
            LOGGER.debug("خواندن شرکت‌کنندگان %s ناموفق بود: %s", chat_id, error)
            return None

    async def listeners_count(self, chat_id: int) -> int:
        """تعداد شنوندگان (بدون خود اسیستنت)؛ ‎-1 یعنی قابل تشخیص نبود."""
        assistant = self.assistant(chat_id)
        people = await self.participants(chat_id)
        if people is None:
            return -1
        return len([person for person in people if getattr(person, "user_id", 0) != assistant.id])

    # ── ویس‌چت از دید MTProto (بدون نیاز به حضور اسیستنت در کال) ──────────────
    async def input_call(self, chat_id: int) -> Any | None:
        """`InputGroupCall` ویس‌چت فعال گروه؛ None یعنی ویس‌چتی روشن نیست."""
        assistant = self.assistant(chat_id)
        try:
            peer = await assistant.client.resolve_peer(chat_id)
            if isinstance(peer, raw.types.InputPeerChannel):
                full = await assistant.client.invoke(
                    raw.functions.channels.GetFullChannel(
                        channel=raw.types.InputChannel(
                            channel_id=peer.channel_id, access_hash=peer.access_hash
                        )
                    )
                )
            else:
                full = await assistant.client.invoke(
                    raw.functions.messages.GetFullChat(chat_id=abs(chat_id))
                )
            return getattr(full.full_chat, "call", None)
        except Exception as error:  # noqa: BLE001
            LOGGER.debug("خواندن ویس‌چت %s ناموفق بود: %s", chat_id, error)
            return None

    async def raw_participants(self, chat_id: int, limit: int = 200) -> list[Any] | None:
        """شرکت‌کنندگان ویس‌چت با جزئیات کامل (میوت، ویدیو، تاریخ ورود، منبع).

        برخلاف `participants`، اسیستنت لازم نیست داخل کال باشد؛ فقط باید عضو گروه باشد.
        None یعنی ویس‌چت روشن نیست یا خواندن ممکن نشد.
        """
        call = await self.input_call(chat_id)
        if call is None:
            return None
        assistant = self.assistant(chat_id)
        try:
            result = await assistant.client.invoke(
                raw.functions.phone.GetGroupParticipants(
                    call=call, ids=[], sources=[], offset="", limit=limit
                )
            )
            return list(result.participants or [])
        except Exception as error:  # noqa: BLE001
            LOGGER.debug("خواندن شرکت‌کنندگان خام %s ناموفق بود: %s", chat_id, error)
            return None

    async def set_call_title(self, chat_id: int, title: str) -> None:
        """تنظیم عنوان ویس‌چت گروه."""
        call = await self.input_call(chat_id)
        if call is None:
            raise NoVoiceChat()
        assistant = self.assistant(chat_id)
        try:
            await assistant.client.invoke(
                raw.functions.phone.EditGroupCallTitle(call=call, title=title[:64])
            )
        except Exception as error:  # noqa: BLE001
            raise UserError("err_generic", error=str(error)[:200]) from error

    async def invite_to_call(self, chat_id: int, user_ids: list[int]) -> int:
        """دعوت کاربران به ویس‌چت؛ تعداد دعوت‌های موفق را برمی‌گرداند."""
        call = await self.input_call(chat_id)
        if call is None:
            raise NoVoiceChat()
        assistant = self.assistant(chat_id)
        invited = 0
        for chunk_start in range(0, len(user_ids), 10):
            chunk = user_ids[chunk_start : chunk_start + 10]
            users = []
            for user_id in chunk:
                try:
                    users.append(await assistant.client.resolve_peer(user_id))
                except Exception:  # noqa: BLE001
                    continue
            users = [user for user in users if isinstance(user, raw.types.InputPeerUser)]
            if not users:
                continue
            try:
                await assistant.client.invoke(
                    raw.functions.phone.InviteToGroupCall(
                        call=call,
                        users=[
                            raw.types.InputUser(user_id=user.user_id, access_hash=user.access_hash)
                            for user in users
                        ],
                    )
                )
                invited += len(users)
            except FloodWait as error:
                LOGGER.info("دعوت به کال %s با فلود مواجه شد: %s", chat_id, error.value)
                break
            except Exception as error:  # noqa: BLE001
                LOGGER.debug("دعوت به کال %s ناموفق بود: %s", chat_id, error)
            await asyncio.sleep(1)
        return invited

    async def set_participant_muted(self, chat_id: int, user_id: int, muted: bool) -> bool:
        """میوت/آنمیوت یک عضو ویس‌چت (اسیستنت باید دسترسی مدیریت ویس‌چت داشته باشد)."""
        call = await self.input_call(chat_id)
        if call is None:
            return False
        assistant = self.assistant(chat_id)
        try:
            peer = await assistant.client.resolve_peer(user_id)
            await assistant.client.invoke(
                raw.functions.phone.EditGroupCallParticipant(
                    call=call, participant=peer, muted=muted
                )
            )
            return True
        except Exception as error:  # noqa: BLE001
            LOGGER.debug("تغییر وضعیت مایک %s در %s ناموفق بود: %s", user_id, chat_id, error)
            return False

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
