"""لایه سازگاری با نسخه استاندارد Pyrogram.

کد اصلی روی یک فورک از Pyrogram نوشته شده بود که دکمه‌های اینلاین رنگی
(`pyrogram.enums.ButtonStyle` و پارامتر `style=` در InlineKeyboardButton) را
پشتیبانی می‌کرد. Pyrogram استاندارد این قابلیت را ندارد و در نتیجه:

  • `from pyrogram.enums import ButtonStyle` خطای ImportError می‌دهد.
  • `InlineKeyboardButton(..., style=...)` خطای TypeError می‌دهد.

این ماژول:
  1. اگر ButtonStyle موجود بود همان را استفاده می‌کند؛
  2. در غیر این صورت یک جایگزین سبک می‌سازد و سازندهٔ InlineKeyboardButton را
     طوری وصله می‌کند که پارامتر style را بپذیرد و نادیده بگیرد (دکمه‌ها بدون
     رنگ ساخته می‌شوند ولی همه‌چیز کار می‌کند).

فقط کافی است بالای فایل‌ها `import compat` انجام شود و `ButtonStyle` از همین
ماژول گرفته شود.
"""

import inspect

from pyrogram.types import InlineKeyboardButton

try:  # فورک رنگی
    from pyrogram.enums import ButtonStyle  # noqa: F401

    NATIVE_BUTTON_STYLE = True
except ImportError:  # Pyrogram استاندارد
    from enum import Enum

    class ButtonStyle(str, Enum):
        DEFAULT = "default"
        PRIMARY = "primary"
        SECONDARY = "secondary"
        SUCCESS = "success"
        DANGER = "danger"
        WARNING = "warning"

    NATIVE_BUTTON_STYLE = False

    _params = inspect.signature(InlineKeyboardButton.__init__).parameters
    if "style" not in _params:
        _original_init = InlineKeyboardButton.__init__

        def _init_with_style(self, *args, style=None, **kwargs):
            # style فقط بلعیده می‌شود؛ سایر آرگومان‌ها بدون تغییر عبور می‌کنند
            _original_init(self, *args, **kwargs)

        InlineKeyboardButton.__init__ = _init_with_style


__all__ = ["ButtonStyle", "NATIVE_BUTTON_STYLE"]
