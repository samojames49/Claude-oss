"""جستجو، استخراج لینک پخش و دانلود از یوتیوب (و هر سایتی که yt-dlp پشتیبانی می‌کند)."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL

from .. import config
from ..utils.logger import get_logger

LOGGER = get_logger("youtube")

YOUTUBE_URL_RE = re.compile(
    r"(?:https?://)?(?:www\.|m\.|music\.)?"
    r"(?:youtube(?:-nocookie)?\.com|youtu\.be)/\S+",
    re.IGNORECASE,
)
VIDEO_ID_RE = re.compile(
    r"(?:v=|/videos/|embed/|youtu\.be/|/v/|/e/|watch\?v=|shorts/|live/)([\w-]{11})"
)
URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)

_VIDEO_HEIGHT = {
    "uhd": 2160,
    "4k": 2160,
    "qhd": 1440,
    "2k": 1440,
    "fhd": 1080,
    "1080": 1080,
    "hd": 720,
    "720": 720,
    "sd": 480,
    "480": 480,
}


@dataclass
class SearchResult:
    title: str
    url: str
    vid_id: str | None = None
    duration: int = 0
    thumbnail: str | None = None
    uploader: str = ""
    views: int = 0
    is_live: bool = False


@dataclass
class StreamSource:
    """آدرس(های) قابل پخش برای ffmpeg."""

    url: str
    audio_url: str | None = None
    headers: dict[str, str] | None = None
    is_live: bool = False


def is_youtube_url(text: str) -> bool:
    return bool(YOUTUBE_URL_RE.search(text or ""))


def is_url(text: str) -> bool:
    return bool(URL_RE.match((text or "").strip()))


def video_id(url: str) -> str | None:
    match = VIDEO_ID_RE.search(url or "")
    return match.group(1) if match else None


def watch_url(vid_id: str) -> str:
    return f"https://www.youtube.com/watch?v={vid_id}"


def thumbnail_url(vid_id: str | None) -> str | None:
    if not vid_id:
        return None
    return f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"


def _base_options(**extra: Any) -> dict[str, Any]:
    options: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "ignoreerrors": True,
        "skip_download": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "retries": 3,
        "socket_timeout": 20,
        "cachedir": str(config.CACHE_DIR),
    }
    if config.COOKIES_FILE and Path(config.COOKIES_FILE).exists():
        options["cookiefile"] = config.COOKIES_FILE
    if config.YTDLP_PROXY:
        options["proxy"] = config.YTDLP_PROXY
    options.update(extra)
    return options


# اگر یوتیوب برای یک کلاینت پیام «ربات نیستم» بدهد، با کلاینت دیگری دوباره تلاش می‌کنیم
FALLBACK_CLIENTS = ({"youtube": {"player_client": ["tv"]}}, {"youtube": {"player_client": ["web_safari"]}})


def _extract(query: str, options: dict[str, Any]) -> dict[str, Any] | None:
    with YoutubeDL(options) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
        except Exception as error:  # noqa: BLE001 - خطاهای yt-dlp بسیار متنوع‌اند
            LOGGER.warning("yt-dlp نتوانست %r را بخواند: %s", query[:120], error)
            return None
        if info is None:
            return None
        return ydl.sanitize_info(info)


def _extract_with_fallback(query: str, options: dict[str, Any]) -> dict[str, Any] | None:
    """استخراج اطلاعات با تلاش مجدد روی کلاینت‌های دیگر یوتیوب."""
    info = _extract(query, options)
    if info is not None:
        return info
    for extractor_args in FALLBACK_CLIENTS:
        retry = dict(options)
        retry["extractor_args"] = extractor_args
        info = _extract(query, retry)
        if info is not None:
            LOGGER.info("استخراج با کلاینت جایگزین %s موفق شد.", extractor_args)
            return info
    return None


def _entry_to_result(entry: dict[str, Any]) -> SearchResult | None:
    if not entry:
        return None
    if entry.get("ie_key") not in (None, "Youtube"):
        return None
    vid = entry.get("id")
    url = entry.get("url") or entry.get("webpage_url")
    if not url and vid:
        url = watch_url(vid)
    if not url:
        return None
    if vid and len(str(vid)) != 11 and "youtube" in str(url):
        return None
    thumb = entry.get("thumbnail")
    if not thumb:
        thumbs = entry.get("thumbnails") or []
        thumb = thumbs[-1]["url"] if thumbs and thumbs[-1].get("url") else thumbnail_url(vid)
    return SearchResult(
        title=entry.get("title") or "بدون نام",
        url=url,
        vid_id=vid if vid and len(str(vid)) == 11 else None,
        duration=int(entry.get("duration") or 0),
        thumbnail=thumb,
        uploader=entry.get("uploader") or entry.get("channel") or "",
        views=int(entry.get("view_count") or 0),
        is_live=bool(entry.get("is_live") or entry.get("live_status") == "is_live"),
    )


# ── جستجو ─────────────────────────────────────────────────────────────────────
async def search(query: str, limit: int | None = None) -> list[SearchResult]:
    """جستجوی یوتیوب بدون نیاز به کلید API (از خود yt-dlp)."""
    count = max(1, int(limit or config.SEARCH_RESULTS_LIMIT))
    options = _base_options(extract_flat="in_playlist", playlist_items=f"1-{count * 2}")
    info = await asyncio.to_thread(_extract, f"ytsearch{count * 2}:{query}", options)
    if not info:
        return []
    results: list[SearchResult] = []
    for entry in info.get("entries") or []:
        result = _entry_to_result(entry or {})
        if result is None:
            continue
        results.append(result)
        if len(results) >= count:
            break
    return results


async def search_one(query: str) -> SearchResult | None:
    results = await search(query, limit=1)
    return results[0] if results else None


async def details(query: str) -> SearchResult | None:
    """اطلاعات یک لینک یا عبارت جستجو."""
    target = query.strip()
    if not is_url(target):
        return await search_one(target)
    info = await asyncio.to_thread(_extract_with_fallback, target, _base_options())
    if not info:
        return None
    if info.get("_type") == "playlist":
        entries = [entry for entry in (info.get("entries") or []) if entry]
        if not entries:
            return None
        info = entries[0]
    return _entry_to_result(info)


async def playlist(url: str, limit: int = 25) -> list[SearchResult]:
    """آیتم‌های یک پلی‌لیست یوتیوب."""
    options = _base_options(
        extract_flat="in_playlist",
        noplaylist=False,
        playlist_items=f"1-{max(1, limit)}",
    )
    info = await asyncio.to_thread(_extract, url, options)
    if not info:
        return []
    entries = info.get("entries") or []
    results = []
    for entry in entries:
        result = _entry_to_result(entry or {})
        if result is not None:
            results.append(result)
    return results


def is_playlist_url(url: str) -> bool:
    return "list=" in (url or "") and "watch?v=" not in (url or "")


# ── استخراج لینک پخش ─────────────────────────────────────────────────────────
def _format_selector(video: bool) -> str:
    if not video:
        return "bestaudio[ext=m4a]/bestaudio/best"
    height = _VIDEO_HEIGHT.get(config.VIDEO_QUALITY, 720)
    return (
        f"bestvideo[height<={height}][vcodec^=avc1]+bestaudio[ext=m4a]/"
        f"bestvideo[height<={height}]+bestaudio/"
        f"best[height<={height}]/best"
    )


def _pick_urls(info: dict[str, Any]) -> tuple[str | None, str | None, dict[str, str] | None]:
    requested = info.get("requested_formats")
    if requested:
        video_fmt = next((fmt for fmt in requested if fmt.get("vcodec") not in (None, "none")), None)
        audio_fmt = next((fmt for fmt in requested if fmt.get("acodec") not in (None, "none")), None)
        headers = (video_fmt or audio_fmt or {}).get("http_headers")
        return (
            (video_fmt or {}).get("url"),
            (audio_fmt or {}).get("url"),
            headers,
        )
    url = info.get("url")
    headers = info.get("http_headers")
    if info.get("vcodec") not in (None, "none"):
        return url, None, headers
    return None, url, headers


async def stream_source(query: str, video: bool = False) -> StreamSource | None:
    """لینک مستقیم قابل پخش (بدون دانلود کامل) را برمی‌گرداند."""
    target = query if is_url(query) else f"ytsearch1:{query}"
    options = _base_options(format=_format_selector(video))
    info = await asyncio.to_thread(_extract_with_fallback, target, options)
    if not info:
        return None
    if info.get("_type") == "playlist":
        entries = [entry for entry in (info.get("entries") or []) if entry]
        if not entries:
            return None
        info = entries[0]

    is_live = bool(info.get("is_live") or info.get("live_status") == "is_live")
    video_url, audio_url, headers = _pick_urls(info)

    if video:
        if not video_url:
            return None
        return StreamSource(
            url=video_url,
            audio_url=audio_url,
            headers=headers,
            is_live=is_live,
        )
    if not audio_url and not video_url:
        return None
    return StreamSource(url=audio_url or video_url or "", headers=headers, is_live=is_live)


# ── دانلود ────────────────────────────────────────────────────────────────────
def _download(query: str, options: dict[str, Any]) -> str | None:
    with YoutubeDL(options) as ydl:
        try:
            info = ydl.extract_info(query, download=True)
        except Exception as error:  # noqa: BLE001
            LOGGER.warning("دانلود %r ناموفق بود: %s", query[:120], error)
            return None
        if info is None:
            return None
        if info.get("_type") == "playlist":
            entries = [entry for entry in (info.get("entries") or []) if entry]
            if not entries:
                return None
            info = entries[0]
        path = None
        downloads = info.get("requested_downloads") or []
        if downloads:
            path = downloads[0].get("filepath")
        if not path:
            path = ydl.prepare_filename(info)
        return path


async def download_media(
    query: str,
    video: bool = False,
    audio_format: str = "m4a",
    subtitle_lang: str | None = None,
) -> tuple[str | None, str | None]:
    """دانلود فایل و (در صورت درخواست) زیرنویس آن.

    مقدار بازگشتی: (مسیر رسانه، مسیر زیرنویس یا None)
    """
    target = query if is_url(query) else f"ytsearch1:{query}"
    outtmpl = str(config.DOWNLOADS_DIR / "%(id)s_%(format_id)s.%(ext)s")
    options = _base_options(
        skip_download=False,
        outtmpl=outtmpl,
        format=_format_selector(video),
        overwrites=False,
        continuedl=True,
    )
    postprocessors: list[dict[str, Any]] = []
    if video:
        options["merge_output_format"] = "mp4"
    elif audio_format:
        postprocessors.append(
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
                "preferredquality": "0",
            }
        )
    if subtitle_lang:
        options.update(
            writesubtitles=True,
            writeautomaticsub=True,
            subtitleslangs=[subtitle_lang, f"{subtitle_lang}-orig", f"{subtitle_lang}.*"],
            subtitlesformat="srt/vtt/best",
        )
        postprocessors.append({"key": "FFmpegSubtitlesConvertor", "format": "srt"})
    if postprocessors:
        options["postprocessors"] = postprocessors

    path = await asyncio.to_thread(_download, target, options)
    if not path:
        return None, None

    candidate = Path(path)
    if not candidate.exists():
        # پس از پردازش صوتی پسوند تغییر می‌کند
        for sibling in candidate.parent.glob(candidate.stem + ".*"):
            if sibling.suffix.lower() not in (".srt", ".vtt", ".ass", ".part"):
                candidate = sibling
                break
    if not candidate.exists():
        return None, None

    subtitle = _find_subtitle(candidate, subtitle_lang) if subtitle_lang else None
    return str(candidate), subtitle


def _find_subtitle(media: Path, lang: str) -> str | None:
    """زیرنویس دانلودشده در کنار فایل رسانه (yt-dlp نام زبان را به فایل اضافه می‌کند)."""
    for pattern in (f"{media.stem}*.{lang}*.srt", f"{media.stem}*.srt", f"{media.stem}*.vtt"):
        for found in sorted(media.parent.glob(pattern)):
            if found.exists() and found.stat().st_size > 0:
                return str(found)
    return None


async def download(query: str, video: bool = False, audio_format: str = "m4a") -> str | None:
    """دانلود فایل و برگرداندن مسیر آن (برای دستور /song و /video یا حالت download)."""
    path, _ = await download_media(query, video=video, audio_format=audio_format)
    return path
