"""پخش زندهٔ تلویزیون/ماهواره/رادیو با منوی دکمه‌ای."""

from __future__ import annotations

from pyrogram import Client, filters

from ..core.decorators import callback_handler, player_handler
from ..core.filters import argument, command
from ..core.service import player
from ..core.targets import playback_chat
from ..core.ui import announce, requester_of
from ..platforms import livetv
from ..utils.keyboards import live_categories, live_channels

LIVE_ALIASES = ["پخش زنده", "پخش ماهواره", "ماهواره", "تلویزیون", "live", "satellite"]


@Client.on_message(
    command(["live", "livetv", "satellite", "tv"], bare=LIVE_ALIASES) & filters.group,
    group=1,
)
@player_handler(play_permission=True)
async def live_command(_client: Client, message, s):
    """منوی دسته‌ها؛ با نوشتن نام شبکه هم مستقیم پخش می‌شود."""
    query = argument(message)
    if query:
        matches = livetv.search(query)
        if not matches:
            await message.reply_text(s("live_not_found", query=query))
            return
        await _play_channel(message, s, matches[0])
        return

    categories = livetv.categories()
    if not categories:
        await message.reply_text(s("live_empty"))
        return
    await message.reply_text(
        s("live_header", count=livetv.total_channels(), categories=len(categories)),
        reply_markup=live_categories(s.language, categories),
    )


@Client.on_message(
    command(["reloadlive", "livereload"], bare=["بروزرسانی شبکه ها", "بروزرسانی شبکه‌ها"])
    & filters.group,
    group=1,
)
@player_handler(admin_only=True)
async def reload_live_command(_client: Client, message, s):
    """خواندن دوبارهٔ فایل شبکه‌ها بعد از ویرایش آن."""
    categories = livetv.load(force=True)
    await message.reply_text(
        s("live_reloaded", count=livetv.total_channels(), categories=len(categories))
    )


@Client.on_callback_query(filters.regex(r"^live:"))
@callback_handler()
async def live_callback(_client: Client, query, s):
    parts = query.data.split(":")
    action = parts[1] if len(parts) > 1 else "home"

    if action == "home":
        categories = livetv.categories()
        await query.message.edit_text(
            s("live_header", count=livetv.total_channels(), categories=len(categories)),
            reply_markup=live_categories(s.language, categories),
        )
        await query.answer()
        return

    if action == "cat":
        category = livetv.category(parts[2] if len(parts) > 2 else "")
        if category is None:
            await query.answer(s("live_empty"), show_alert=True)
            return
        await query.message.edit_text(
            s("live_category_header", title=category.title, count=len(category.channels)),
            reply_markup=live_channels(s.language, category.id, category.channels),
        )
        await query.answer()
        return

    if action == "play":
        if not await _may_play(query, s):
            return
        channel = livetv.channel(parts[2], int(parts[3])) if len(parts) > 3 else None
        if channel is None:
            await query.answer(s("live_empty"), show_alert=True)
            return
        await query.answer(s("live_starting", name=channel.name))
        await _play_channel(query.message, s, channel, user=query.from_user)


async def _may_play(query, s) -> bool:
    from ..core.admins import can_play

    user = query.from_user
    chat_id = query.message.chat.id if query.message else None
    if chat_id is None or user is None:
        return False
    if await can_play(chat_id, user.id):
        return True
    await query.answer(s("err_play_mode_admins"), show_alert=True)
    return False


async def _play_channel(message, s, channel, user=None) -> None:
    chat_id = playback_chat(message.chat.id)
    if user is not None:
        name = " ".join(filter(None, [user.first_name, user.last_name])) or str(user.id)
        requester_id, requester_name = user.id, name
    else:
        requester_id, requester_name = requester_of(message)
    track = channel.to_track(requester_id=requester_id, requester_name=requester_name)
    state, position = await player.play_or_queue(chat_id, track)
    await announce(message, s, state, position, track)
