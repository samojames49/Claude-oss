"""تشخیص نوع درخواست کاربر و ساخت آیتم(های) قابل پخش."""

from __future__ import annotations

from dataclasses import dataclass, field

from .. import config
from ..core.errors import DurationLimit, NoResult
from ..core.track import Track
from ..utils.formatters import seconds_to_time
from ..utils.logger import get_logger
from . import live, spotify, youtube

LOGGER = get_logger("resolver")


@dataclass
class Resolved:
    tracks: list[Track] = field(default_factory=list)
    playlist_title: str | None = None

    @property
    def first(self) -> Track | None:
        return self.tracks[0] if self.tracks else None


def _check_duration(duration: int, limit_minutes: int) -> None:
    if duration <= 0 or limit_minutes <= 0:
        return
    if duration > limit_minutes * 60:
        raise DurationLimit(seconds_to_time(duration), limit_minutes)


async def _attach_source(
    track: Track, target: str, video: bool, *, force_download: bool = False
) -> Track:
    """آماده‌سازی مسیر پخش: لینک مستقیم یا فایل دانلودشده."""
    if force_download or config.STREAM_MODE == "download":
        # برای ویدیو، اگر زیرنویس در دسترس باشد همان لحظه گرفته و روی تصویر چسبانده می‌شود
        subtitle_lang = config.SUBTITLE_LANG if (video and config.SUBTITLE_ENABLED) else None
        path, subtitle = await youtube.download_media(
            target, video=video, subtitle_lang=subtitle_lang
        )
        if path:
            track.source = path
            track.file_path = path
            if subtitle:
                track.subtitle_path = subtitle
            return track
        LOGGER.warning("دانلود ناموفق بود؛ به پخش لینک مستقیم برمی‌گردیم: %s", target)

    source = await youtube.stream_source(target, video=video)
    if source is None:
        raise NoResult()
    track.source = source.url
    track.audio_source = source.audio_url
    track.headers = source.headers
    if source.is_live:
        track.kind = "live"
        track.duration = 0
    return track


async def track_from_result(
    result: youtube.SearchResult,
    *,
    video: bool = False,
    requester_id: int = 0,
    requester_name: str = "",
    limit_minutes: int | None = None,
    prepare: bool = True,
    download: bool = False,
) -> Track:
    """ساخت Track از نتیجهٔ جستجو یا لینک یوتیوب."""
    limit = config.DURATION_LIMIT_MINUTES if limit_minutes is None else limit_minutes
    if not result.is_live:
        _check_duration(result.duration, limit)

    track = Track(
        title=result.title,
        source=result.url,
        kind="live" if result.is_live else "youtube",
        duration=0 if result.is_live else result.duration,
        video=video,
        url=result.url,
        thumbnail=result.thumbnail or youtube.thumbnail_url(result.vid_id),
        vid_id=result.vid_id,
        requester_id=requester_id,
        requester_name=requester_name,
    )
    if prepare:
        await _attach_source(track, result.url, video, force_download=download)
    else:
        track.extra["download"] = download
    return track


async def resolve_query(
    query: str,
    *,
    video: bool = False,
    requester_id: int = 0,
    requester_name: str = "",
    limit_minutes: int | None = None,
    playlist_limit: int = 20,
    download: bool = False,
) -> Resolved:
    """درخواست متنی کاربر را به یک یا چند آیتم پخش تبدیل می‌کند."""
    text = (query or "").strip()
    if not text:
        raise NoResult()

    limit = config.DURATION_LIMIT_MINUTES if limit_minutes is None else limit_minutes

    # لینک اسپاتیفای → جستجوی نام قطعه در یوتیوب
    if spotify.is_spotify_url(text):
        title = await spotify.to_query(text)
        if not title:
            raise NoResult()
        text = title

    if youtube.is_url(text):
        # لینک رادیو / m3u8 / فایل مستقیم → بدون yt-dlp پخش می‌شود
        if not youtube.is_youtube_url(text) and live.is_streamable_url(text):
            is_live = live.is_live_url(text)
            track = Track(
                title=live.title_from_url(text),
                source=text,
                kind="live" if is_live else "url",
                duration=0,
                video=video,
                url=text,
                requester_id=requester_id,
                requester_name=requester_name,
            )
            return Resolved(tracks=[track])

        # پلی‌لیست یوتیوب
        if youtube.is_playlist_url(text):
            entries = await youtube.playlist(text, limit=playlist_limit)
            if not entries:
                raise NoResult()
            tracks: list[Track] = []
            for index, entry in enumerate(entries):
                try:
                    tracks.append(
                        await track_from_result(
                            entry,
                            video=video,
                            requester_id=requester_id,
                            requester_name=requester_name,
                            limit_minutes=limit,
                            prepare=index == 0,  # بقیه هنگام نوبت پخش آماده می‌شوند
                            download=download,
                        )
                    )
                except DurationLimit:
                    continue
            if not tracks:
                raise NoResult()
            return Resolved(tracks=tracks, playlist_title="پلی‌لیست یوتیوب")

    result = await youtube.details(text)
    if result is None:
        raise NoResult()
    track = await track_from_result(
        result,
        video=video,
        requester_id=requester_id,
        requester_name=requester_name,
        limit_minutes=limit,
        download=download,
    )
    return Resolved(tracks=[track])


async def prepare_track(track: Track) -> Track:
    """آماده‌سازی آیتم‌هایی که هنگام افزودن به صف لینک پخش نگرفته‌اند."""
    if track.file_path or track.kind in ("telegram", "url", "file"):
        return track
    if track.source and track.source != track.url and not youtube.is_youtube_url(track.source):
        return track  # از قبل لینک مستقیم دارد
    target = track.url or track.source
    return await _attach_source(
        track, target, track.video, force_download=bool(track.extra.get("download"))
    )
