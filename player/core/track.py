"""مدل یک مورد قابل پخش."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..utils.formatters import seconds_to_time


@dataclass
class Track:
    """یک آیتم پخش (آهنگ، ویدیو، فایل تلگرام یا پخش زنده)."""

    title: str
    source: str  # مسیر فایل یا لینکی که به ffmpeg داده می‌شود
    audio_source: str | None = None  # مسیر صوتی جدا (پخش ویدیویی یوتیوب)
    kind: str = "youtube"  # youtube | telegram | live | url | file
    duration: int = 0  # ثانیه؛ صفر یعنی نامعلوم/زنده
    video: bool = False
    url: str | None = None  # لینک قابل‌نمایش برای کاربر
    thumbnail: str | None = None
    vid_id: str | None = None
    requester_id: int = 0
    requester_name: str = ""
    headers: dict[str, str] | None = None
    file_path: str | None = None  # اگر دانلود شده باشد
    message_id: int | None = None  # پیام تلگرامی مبدأ
    speed: float = 1.0
    seek: int = 0
    media_volume: int = 100  # صدای رسانه قبل از ارسال به ویس‌چت (۱ تا ۲۰۰)
    subtitle_path: str | None = None  # زیرنویس چسبیده روی تصویر (SoftSub)
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def is_live(self) -> bool:
        return self.kind == "live" or self.duration <= 0

    @property
    def duration_text(self) -> str:
        if self.is_live:
            return "∞"
        return seconds_to_time(self.duration)

    @property
    def short_title(self) -> str:
        title = self.title.strip() or "بدون نام"
        return title if len(title) <= 45 else title[:42] + "…"

    def requester_mention(self) -> str:
        if self.requester_id:
            name = self.requester_name or str(self.requester_id)
            return f"[{name}](tg://user?id={self.requester_id})"
        return self.requester_name or "-"

    def kind_key(self) -> str:
        if self.is_live:
            return "stream_kind_live"
        return "stream_kind_video" if self.video else "stream_kind_audio"

    def clone(self) -> "Track":
        return Track(
            title=self.title,
            source=self.source,
            audio_source=self.audio_source,
            kind=self.kind,
            duration=self.duration,
            video=self.video,
            url=self.url,
            thumbnail=self.thumbnail,
            vid_id=self.vid_id,
            requester_id=self.requester_id,
            requester_name=self.requester_name,
            headers=dict(self.headers) if self.headers else None,
            file_path=self.file_path,
            message_id=self.message_id,
            speed=self.speed,
            seek=self.seek,
            media_volume=self.media_volume,
            subtitle_path=self.subtitle_path,
            extra=dict(self.extra),
        )
