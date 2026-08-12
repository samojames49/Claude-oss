"""ساخت تصویر «در حال پخش» (اختیاری و بدون خطا در صورت نبود منابع)."""

from __future__ import annotations

import asyncio
from pathlib import Path

from .. import config
from .formatters import seconds_to_time, shorten
from .http import download_file
from .logger import get_logger

LOGGER = get_logger("thumbnail")

try:  # Pillow اختیاری است
    from PIL import Image, ImageDraw, ImageFilter, ImageFont, features

    PIL_AVAILABLE = True
    # با raqm خود Pillow حروف فارسی را می‌چسباند و راست‌به‌چپ می‌چیند
    RAQM_AVAILABLE = bool(features.check("raqm"))
except ImportError:  # pragma: no cover
    PIL_AVAILABLE = False
    RAQM_AVAILABLE = False

try:  # جایگزین دستی شکل‌دهی حروف وقتی raqm نیست
    import arabic_reshaper
    from bidi.algorithm import get_display

    RESHAPE_AVAILABLE = True
except ImportError:  # pragma: no cover
    RESHAPE_AVAILABLE = False

# DejaVu هم فارسی و هم علائم لاتین را دارد، پس اولویت اول است؛ بقیه جایگزین‌اند.
FONTS = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/vazirmatn/Vazirmatn-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
)


def has_rtl(text: str) -> bool:
    return any(
        "\u0590" <= char <= "\u06ff" or "\ufb50" <= char <= "\ufeff" for char in text or ""
    )


def shape(text: str) -> str:
    """آماده‌سازی متن برای رسم: با raqm دست‌نخورده، وگرنه با reshaper."""
    if not text or RAQM_AVAILABLE or not RESHAPE_AVAILABLE:
        return text
    try:
        return get_display(arabic_reshaper.reshape(text))
    except Exception:  # noqa: BLE001
        return text


def _font(size: int):
    if not PIL_AVAILABLE:
        return None
    for path in FONTS:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    try:
        return ImageFont.load_default(size)
    except TypeError:  # Pillow قدیمی
        return ImageFont.load_default()


def _text_width(draw, text: str, font, direction: str | None) -> float:
    try:
        return draw.textlength(text, font=font, direction=direction)
    except Exception:  # noqa: BLE001 - بعضی نسخه‌ها direction را نمی‌پذیرند
        return draw.textlength(text, font=font)


def _draw_line(draw, text: str, *, left: int, right: int, top: int, size: int, fill) -> None:
    """رسم یک خط متن با اندازهٔ خودکار؛ متن فارسی راست‌چین می‌شود."""
    if not text:
        return
    rtl = has_rtl(text)
    direction = "rtl" if rtl and RAQM_AVAILABLE else None
    max_width = right - left
    font = _font(size)
    while size > 18 and _text_width(draw, text, font, direction) > max_width:
        size -= 4
        font = _font(size)
    while text and _text_width(draw, text, font, direction) > max_width:
        text = text[:-2] + "…"

    kwargs = {"font": font, "fill": fill}
    if direction:
        kwargs["direction"] = direction
    try:
        if rtl:
            draw.text((right, top), text, anchor="ra", **kwargs)
        else:
            draw.text((left, top), text, **kwargs)
    except Exception:  # noqa: BLE001 - نسخه‌های قدیمی Pillow anchor/direction ندارند
        draw.text((left, top), text, font=font, fill=fill)


def _compose(
    source: Path,
    output: Path,
    title: str,
    subtitle: str,
    duration: str,
) -> bool:
    try:
        base = Image.open(source).convert("RGB")
    except Exception as error:  # noqa: BLE001
        LOGGER.debug("باز کردن تامبنیل ناموفق بود: %s", error)
        return False

    width, height = 1280, 720
    background = base.resize((width, height)).filter(ImageFilter.GaussianBlur(24))
    background = Image.blend(background, Image.new("RGB", (width, height), (0, 0, 0)), 0.45)

    art_size = 420
    background.paste(base.resize((art_size, art_size)), (70, (height - art_size) // 2))

    draw = ImageDraw.Draw(background)
    left = 70 + art_size + 60
    right = width - 70

    _draw_line(
        draw,
        shape(shorten(title, 60)),
        left=left,
        right=right,
        top=205,
        size=46,
        fill=(255, 255, 255),
    )
    _draw_line(
        draw,
        shape(shorten(subtitle, 45)),
        left=left,
        right=right,
        top=295,
        size=34,
        fill=(205, 205, 205),
    )
    _draw_line(
        draw, duration, left=left, right=right, top=365, size=28, fill=(180, 180, 180)
    )

    bar_y = 440
    draw.rounded_rectangle((left, bar_y, right, bar_y + 12), radius=6, fill=(90, 90, 90))
    draw.rounded_rectangle(
        (left, bar_y, left + int((right - left) * 0.35), bar_y + 12), radius=6, fill=(255, 255, 255)
    )
    _draw_line(
        draw,
        shape(config.BOT_NAME or "Player"),
        left=left,
        right=right,
        top=bar_y + 28,
        size=28,
        fill=(235, 235, 235),
    )

    try:
        background.save(output, "JPEG", quality=88)
        return True
    except Exception as error:  # noqa: BLE001
        LOGGER.debug("ذخیرهٔ تامبنیل ناموفق بود: %s", error)
        return False


async def now_playing_image(
    thumbnail_url: str | None,
    title: str,
    subtitle: str,
    duration_seconds: int,
    cache_key: str,
) -> str | None:
    """در صورت امکان مسیر تصویر آماده‌شده را برمی‌گرداند، در غیر این صورت None."""
    if not PIL_AVAILABLE or not thumbnail_url:
        return None

    cache_dir = config.CACHE_DIR / "thumbs"
    cache_dir.mkdir(parents=True, exist_ok=True)
    safe_key = "".join(char for char in cache_key if char.isalnum() or char in "-_")[:60]
    raw = cache_dir / f"{safe_key}_raw.jpg"
    output = cache_dir / f"{safe_key}.jpg"

    if output.exists():
        return str(output)
    if not raw.exists() and not await download_file(thumbnail_url, raw):
        return None

    duration_text = "∞" if duration_seconds <= 0 else seconds_to_time(duration_seconds)
    ok = await asyncio.to_thread(_compose, raw, output, title, subtitle, duration_text)
    return str(output) if ok else None
