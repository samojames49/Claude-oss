"""بارگذاری رشته‌های چندزبانه."""

from __future__ import annotations

from .. import config
from . import en, fa

LANGUAGES: dict[str, dict[str, str]] = {
    "fa": fa.STRINGS,
    "en": en.STRINGS,
}

FALLBACK = "en"


def language_names() -> dict[str, str]:
    return {code: table.get("lang_name", code) for code, table in LANGUAGES.items()}


def default_language() -> str:
    code = (config.DEFAULT_LANGUAGE or "fa").lower()
    return code if code in LANGUAGES else "fa"


def get(key: str, language: str | None = None, **kwargs) -> str:
    """متن کلید داده‌شده در زبان مشخص؛ در صورت نبود، به زبان پیش‌فرض برمی‌گردد."""
    code = (language or default_language()).lower()
    table = LANGUAGES.get(code) or LANGUAGES[default_language()]
    text = table.get(key)
    if text is None:
        text = LANGUAGES[FALLBACK].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text


class Strings:
    """دسترسی راحت به رشته‌ها برای یک زبان مشخص."""

    __slots__ = ("language",)

    def __init__(self, language: str | None = None):
        code = (language or default_language()).lower()
        self.language = code if code in LANGUAGES else default_language()

    def __call__(self, key: str, **kwargs) -> str:
        return get(key, self.language, **kwargs)

    def __getitem__(self, key: str) -> str:
        return get(key, self.language)
