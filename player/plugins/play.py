"""دستورهای پخش: /play، /vplay، /playforce، /stream و پخش فایل ریپلای‌شده."""

from __future__ import annotations

from pyrogram import Client, filters

from ..core.decorators import player_handler
from ..core.filters import argument, command
from ..core.ui import play_request

PLAY_ALIASES = ["پخش", "بزن", "پلی"]
VPLAY_ALIASES = ["پخش ویدیو", "ویدیو پخش", "پخش فیلم"]


@Client.on_message(command(["play", "p"], bare=PLAY_ALIASES) & filters.group, group=1)
@player_handler(play_permission=True)
async def play_command(client: Client, message, s):
    await play_request(client, message, s, query=argument(message), video=False)


@Client.on_message(command(["vplay", "playvideo"], bare=VPLAY_ALIASES) & filters.group, group=1)
@player_handler(play_permission=True)
async def vplay_command(client: Client, message, s):
    await play_request(client, message, s, query=argument(message), video=True)


@Client.on_message(command(["playforce", "fplay"], bare=["پخش فوری"]) & filters.group, group=1)
@player_handler(admin_only=True)
async def playforce_command(client: Client, message, s):
    await play_request(client, message, s, query=argument(message), video=False, force=True)


@Client.on_message(command(["vplayforce", "fvplay"], bare=["ویدیو فوری"]) & filters.group, group=1)
@player_handler(admin_only=True)
async def vplayforce_command(client: Client, message, s):
    await play_request(client, message, s, query=argument(message), video=True, force=True)


@Client.on_message(
    command(["stream", "radio", "live"], bare=["پخش زنده", "رادیو"]) & filters.group, group=1
)
@player_handler(play_permission=True)
async def stream_command(client: Client, message, s):
    await play_request(client, message, s, query=argument(message), video=False)
