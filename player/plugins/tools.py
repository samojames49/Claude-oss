"""ابزارها: دانلود آهنگ/ویدیو، جستجو و متن آهنگ."""

from __future__ import annotations

import os
import secrets
from pathlib import Path
from time import time

from pyrogram import Client, filters

from .. import config
from ..core.decorators import callback_handler, player_handler
from ..core.filters import argument, command
from ..core.queues import queues
from ..core.service import player
from ..core.ui import announce, requester_of
from ..platforms import lyrics as lyrics_api
from ..platforms import resolver, youtube
from ..utils.formatters import human_bytes, seconds_to_time
from ..utils.http import download_file
from ..utils.keyboards import search_results
from ..utils.logger import get_logger

LOGGER = get_logger("tools")

_SEARCH_CACHE: dict[str, tuple[float, list[youtube.SearchResult]]] = {}
CACHE_TTL = 900


def _cache_results(results: list[youtube.SearchResult]) -> str:
    token = secrets.token_urlsafe(6)
    _SEARCH_CACHE[token] = (time(), results)
    _prune_cache()
    return token


def _get_cached(token: str) -> list[youtube.SearchResult]:
    entry = _SEARCH_CACHE.get(token)
    return list(entry[1]) if entry else []


def _prune_cache() -> None:
    now = time()
    for token in [key for key, (stamp, _) in _SEARCH_CACHE.items() if now - stamp > CACHE_TTL]:
        _SEARCH_CACHE.pop(token, None)


# ── جستجو ─────────────────────────────────────────────────────────────────────
@Client.on_message(command(["search", "yt"], bare=["جستجو", "سرچ"]), group=1)
@player_handler(group_only=False)
async def search_command(_client: Client, message, s):
    query = argument(message)
    if not query:
        await message.reply_text(s("err_need_query"))
        return
    status = await message.reply_text(s("searching"))
    results = await youtube.search(query, limit=config.SEARCH_RESULTS_LIMIT)
    if not results:
        await status.edit_text(s("err_no_result"))
        return

    lines = [s("search_header", query=query), ""]
    for index, item in enumerate(results, start=1):
        lines.append(
            f"**{index}.** [{item.title}]({item.url})\n"
            f"⏱ `{seconds_to_time(item.duration)}` — 👤 {item.uploader}"
        )
    token = _cache_results(results)
    await status.edit_text(
        "\n".join(lines),
        reply_markup=search_results(s.language, token, len(results)),
        disable_web_page_preview=True,
    )


@Client.on_callback_query(filters.regex(r"^pick:"))
@callback_handler()
async def pick_callback(_client: Client, query, s):
    _, mode, token, index = query.data.split(":", 3)
    results = _get_cached(token)
    try:
        chosen = results[int(index)]
    except (ValueError, IndexError):
        await query.answer(s("err_no_result"), show_alert=True)
        return

    chat = query.message.chat
    if chat.type.name.lower() == "private":
        await query.answer(s("err_group_only"), show_alert=True)
        return

    requester_id, requester_name = requester_of(query)
    await query.answer(s("processing"))
    track = await resolver.track_from_result(
        chosen,
        video=mode == "vplay",
        requester_id=requester_id,
        requester_name=requester_name,
    )
    state, position = await player.play_or_queue(chat.id, track)
    await announce(query.message, s, state, position, track)


# ── دانلود ────────────────────────────────────────────────────────────────────
@Client.on_message(command(["song", "audio", "mp3"], bare=["دانلود آهنگ", "آهنگ"]), group=1)
@player_handler(group_only=False)
async def song_command(client: Client, message, s):
    await _download_media(client, message, s, video=False)


@Client.on_message(command(["video", "vid", "mp4"], bare=["دانلود ویدیو"]), group=1)
@player_handler(group_only=False)
async def video_command(client: Client, message, s):
    await _download_media(client, message, s, video=True)


async def _thumb_for(result: youtube.SearchResult) -> str | None:
    url = result.thumbnail or youtube.thumbnail_url(result.vid_id)
    if not url:
        return None
    path = config.CACHE_DIR / "thumbs" / f"{result.vid_id or secrets.token_hex(4)}_cover.jpg"
    if path.exists() or await download_file(url, path):
        return str(path)
    return None


async def _download_media(client: Client, message, s, *, video: bool) -> None:
    query = argument(message)
    if not query:
        await message.reply_text(s("err_need_query"))
        return

    status = await message.reply_text(s("searching"))
    result = await youtube.details(query)
    if result is None:
        await status.edit_text(s("err_no_result"))
        return

    limit = config.DURATION_LIMIT_MINUTES
    if result.duration and limit and result.duration > limit * 60:
        await status.edit_text(
            s("err_duration_limit", duration=seconds_to_time(result.duration), limit=limit)
        )
        return

    await status.edit_text(s("downloading"))
    path = await youtube.download(result.url, video=video)
    if not path or not Path(path).exists():
        await status.edit_text(s("err_no_result"))
        return

    size = os.path.getsize(path)
    if size > 2000 * 1024 * 1024:
        await status.edit_text(s("err_file_too_big", limit=2000))
        return

    requester_id, requester_name = requester_of(message)
    caption = s(
        "song_caption",
        title=result.title,
        duration=seconds_to_time(result.duration),
        requester=f"[{requester_name}](tg://user?id={requester_id})",
    )
    thumb = await _thumb_for(result)
    try:
        if video:
            await message.reply_video(
                path,
                caption=caption,
                duration=result.duration or 0,
                supports_streaming=True,
                thumb=thumb,
            )
        else:
            await message.reply_audio(
                path,
                caption=caption,
                title=result.title[:60],
                performer=(result.uploader or config.BOT_NAME)[:60],
                duration=result.duration or 0,
                thumb=thumb,
            )
    finally:
        try:
            await status.delete()
        except Exception:  # noqa: BLE001
            pass
    LOGGER.info("فایل %s (%s) ارسال شد.", result.title[:40], human_bytes(size))


# ── متن آهنگ ─────────────────────────────────────────────────────────────────
@Client.on_message(command(["lyrics", "lyric"], bare=["متن آهنگ", "متن"]), group=1)
@player_handler(group_only=False)
async def lyrics_command(_client: Client, message, s):
    if not config.LYRICS_ENABLED:
        await message.reply_text(s("lyrics_disabled"))
        return
    query = argument(message)
    if not query:
        current = queues.current(message.chat.id)
        if current is None:
            await message.reply_text(s("err_need_query"))
            return
        query = current.title

    status = await message.reply_text(s("searching"))
    found = await lyrics_api.search(query)
    if not found:
        await status.edit_text(s("lyrics_not_found"))
        return
    title, text = found
    body = text if len(text) < 3500 else text[:3500] + "\n…"
    await status.edit_text(s("lyrics_result", title=title, lyrics=body))
