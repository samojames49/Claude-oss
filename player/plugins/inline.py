"""جستجوی اینلاین: `@bot نام آهنگ` و پخش با یک ضربه."""

from __future__ import annotations

from pyrogram import Client
from pyrogram.types import (
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from .. import config
from ..core.db import db
from ..core.lang import strings_for
from ..platforms import youtube
from ..utils.formatters import seconds_to_time
from ..utils.logger import get_logger

LOGGER = get_logger("inline")


@Client.on_inline_query()
async def inline_search(_client: Client, inline_query):
    s = strings_for(None)
    user = inline_query.from_user
    if user is not None and db.is_blocked_user(user.id) and not db.is_sudo(user.id):
        await inline_query.answer([], cache_time=5, switch_pm_text=s("err_blocked_user")[:60],
                                  switch_pm_parameter="blocked")
        return

    query = (inline_query.query or "").strip()
    if not query:
        await inline_query.answer(
            [],
            cache_time=5,
            switch_pm_text=s("inline_no_query")[:60],
            switch_pm_parameter="help",
        )
        return

    try:
        results = await youtube.search(query, limit=min(10, config.SEARCH_RESULTS_LIMIT + 4))
    except Exception as error:  # noqa: BLE001
        LOGGER.warning("جستجوی اینلاین ناموفق بود: %s", error)
        results = []

    if not results:
        await inline_query.answer(
            [],
            cache_time=10,
            switch_pm_text=s("err_no_result")[:60],
            switch_pm_parameter="help",
        )
        return

    answers = []
    for index, item in enumerate(results):
        answers.append(
            InlineQueryResultArticle(
                id=f"{index}",
                title=item.title[:60],
                description=f"{seconds_to_time(item.duration)} • {item.uploader}"[:80],
                thumb_url=item.thumbnail or youtube.thumbnail_url(item.vid_id) or "",
                input_message_content=InputTextMessageContent(f"/play {item.url}"),
            )
        )
    await inline_query.answer(answers, cache_time=120)
