"""انتخاب زبان هر گروه."""

from __future__ import annotations

from ..strings import LANGUAGES, Strings, default_language
from .db import db


def chat_language(chat_id: int | None) -> str:
    if chat_id is None:
        return default_language()
    code = db.chat_setting(chat_id, "language", None) if chat_id else None
    if code in LANGUAGES:
        return code
    return default_language()


def strings_for(chat_id: int | None) -> Strings:
    return Strings(chat_language(chat_id))
