"""کلاینت ربات و اکانت‌های اسیستنت (که داخل ویس‌چت می‌روند)."""

from __future__ import annotations

from dataclasses import dataclass, field

from pyrogram import Client
from pyrogram.enums import ParseMode
from pytgcalls import PyTgCalls

from .. import config
from ..utils.logger import get_logger

LOGGER = get_logger("clients")

bot = Client(
    name="player_bot",
    api_id=config.API_ID or 0,
    api_hash=config.API_HASH or "",
    bot_token=config.BOT_TOKEN or "",
    workdir=str(config.SESSION_DIR),
    plugins={"root": "player.plugins"},
    parse_mode=ParseMode.MARKDOWN,
    max_concurrent_transmissions=4,
)


@dataclass
class Assistant:
    """یک اکانت کاربری که به‌عنوان پخش‌کننده وارد ویس‌چت می‌شود."""

    index: int
    client: Client
    calls: PyTgCalls
    id: int = 0
    name: str = ""
    username: str | None = None
    started: bool = field(default=False, repr=False)

    @property
    def mention(self) -> str:
        if self.username:
            return f"@{self.username}"
        if self.id:
            return f"[{self.name or self.id}](tg://user?id={self.id})"
        return self.name or "assistant"

    @property
    def link(self) -> str:
        if self.username:
            return f"https://t.me/{self.username}"
        return f"tg://user?id={self.id}"


def _build_assistants() -> list[Assistant]:
    assistants: list[Assistant] = []
    for index, session in enumerate(config.STRING_SESSIONS, start=1):
        client = Client(
            name=f"player_assistant_{index}",
            api_id=config.API_ID or 0,
            api_hash=config.API_HASH or "",
            session_string=session,
            workdir=str(config.SESSION_DIR),
            parse_mode=ParseMode.MARKDOWN,
            max_concurrent_transmissions=2,
        )
        assistants.append(Assistant(index=index, client=client, calls=PyTgCalls(client)))
    return assistants


assistants: list[Assistant] = _build_assistants()


def assistant_for(chat_id: int) -> Assistant:
    """انتخاب اسیستنت مسئول یک گروه (توزیع ثابت و یکنواخت بین اسیستنت‌ها)."""
    if not assistants:
        raise RuntimeError("هیچ اسیستنتی تنظیم نشده است (STRING_SESSION).")
    return assistants[abs(chat_id) % len(assistants)]


def assistant_by_id(user_id: int) -> Assistant | None:
    for assistant in assistants:
        if assistant.id == user_id:
            return assistant
    return None


async def start_clients() -> None:
    """راه‌اندازی ربات و همهٔ اسیستنت‌ها."""
    await bot.start()
    me = await bot.get_me()
    bot.me = me
    LOGGER.info("ربات @%s (%s) راه‌اندازی شد.", me.username, me.id)

    for assistant in assistants:
        try:
            await assistant.calls.start()  # کلاینت را هم خودش استارت می‌کند
            info = await assistant.client.get_me()
            assistant.id = info.id
            assistant.name = info.first_name or "assistant"
            assistant.username = info.username
            assistant.started = True
            LOGGER.info(
                "اسیستنت %s: %s (%s) آماده است.",
                assistant.index,
                assistant.username or assistant.name,
                assistant.id,
            )
        except Exception as error:  # noqa: BLE001 - نبود یک اسیستنت نباید کل سرویس را بخواباند
            LOGGER.error("راه‌اندازی اسیستنت %s ناموفق بود: %s", assistant.index, error)

    if not any(assistant.started for assistant in assistants):
        raise RuntimeError("هیچ اسیستنتی راه‌اندازی نشد؛ مقدار STRING_SESSION را بررسی کنید.")


async def stop_clients() -> None:
    for assistant in assistants:
        if not assistant.started:
            continue
        try:
            await assistant.client.stop()
        except Exception as error:  # noqa: BLE001
            LOGGER.warning("توقف اسیستنت %s: %s", assistant.index, error)
    try:
        await bot.stop()
    except Exception as error:  # noqa: BLE001
        LOGGER.warning("توقف ربات: %s", error)


def active_assistants() -> list[Assistant]:
    return [assistant for assistant in assistants if assistant.started]
