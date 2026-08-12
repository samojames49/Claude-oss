"""آمار کال: نمایش، فعال/غیرفعال کردن، ارسال خودکار و ریست."""

from __future__ import annotations

from pyrogram import Client, filters

from ..core import callstats
from ..core.callwatch import callwatch
from ..core.db import db
from ..core.decorators import player_handler
from ..core.filters import argument, command
from ..utils.formatters import seconds_to_clock, to_latin_digits

ON_WORDS = ("فعال", "روشن", "on", "active", "enable")
OFF_WORDS = ("غیرفعال", "خاموش", "off", "inactive", "disable")


def _switch(value: str) -> bool | None:
    """«فعال» → True، «غیرفعال» → False، غیر این‌ها → None."""
    word = value.strip().lower()
    if word in OFF_WORDS:  # پیش از ON بررسی می‌شود چون «غیرفعال» شامل «فعال» است
        return False
    if word in ON_WORDS:
        return True
    return None


@Client.on_message(
    command(
        ["callstats", "statscall", "stats_call"],
        bare=["آمار کال", "امار کال", "stats call"],
    )
    & filters.group,
    group=1,
)
@player_handler()
async def call_stats_command(_client: Client, message, s):
    """`آمار کال` و حالت‌های آن: فعال/غیرفعال، عدد روز، نام روز هفته."""
    chat_id = message.chat.id
    value = argument(message)

    state = _switch(value)
    if state is not None:
        if not await _require_admin(message, s):
            return
        db.set_chat_setting(chat_id, "call_stats", state)
        await message.reply_text(s("callstats_on" if state else "callstats_off"))
        return

    db.apply_call_stats_reset(chat_id)

    if not value:
        days = [callstats.today_key()]
        title = s("callstats_title_today")
    elif (digits := to_latin_digits(value).strip()).isdigit():
        count = max(1, min(int(digits), 7))
        days = callstats.last_days(count)
        title = s("callstats_title_days", count=count)
    else:
        day = callstats.weekday_key(value)
        if day is None:
            await message.reply_text(s("callstats_bad_argument"))
            return
        days = [day]
        title = s("callstats_title_day", day=callstats.weekday_label(day))

    text = callstats.render(chat_id, s, days, title=title)
    if not callstats.stats_enabled(chat_id):
        text += s("callstats_disabled_hint")
    await message.reply_text(text, disable_web_page_preview=True)


@Client.on_message(
    command(
        ["autocallstats", "autostatscall"],
        bare=["آمار خودکار کال", "امار خودکار کال", "auto stats call"],
    )
    & filters.group,
    group=1,
)
@player_handler(admin_only=True)
async def auto_call_stats_command(_client: Client, message, s):
    """ارسال خودکار آمار هنگام بسته‌شدن ویس‌چت."""
    state = _switch(argument(message))
    if state is None:
        await message.reply_text(s("callstats_need_switch"))
        return
    db.set_chat_setting(message.chat.id, "call_stats_auto", state)
    await message.reply_text(s("callstats_auto_on" if state else "callstats_auto_off"))


@Client.on_message(
    command(
        ["resetcallstats", "resetstatscall"],
        bare=["ریست آمار کال", "ریست امار کال", "reset stats call"],
    )
    & filters.group,
    group=1,
)
@player_handler(admin_only=True)
async def reset_call_stats_command(_client: Client, message, s):
    """`ریست آمار کال` (فوری) و `ریست آمار کال روزانه|ماهیانه` (دوره‌ای)."""
    chat_id = message.chat.id
    value = argument(message).strip().lower()

    if value in ("روزانه", "daily", "روزنه"):
        db.set_chat_setting(chat_id, "call_stats_reset", "daily")
        await message.reply_text(s("callstats_reset_daily"))
        return
    if value in ("ماهیانه", "ماهانه", "monthly"):
        db.set_chat_setting(chat_id, "call_stats_reset", "monthly")
        await message.reply_text(s("callstats_reset_monthly"))
        return
    if value in ("خاموش", "off", "غیرفعال", "none"):
        db.set_chat_setting(chat_id, "call_stats_reset", "")
        await message.reply_text(s("callstats_reset_off"))
        return

    removed = db.reset_call_stats(chat_id)
    await message.reply_text(s("callstats_reset_done", days=removed))


@Client.on_message(
    command(["id", "whoami"], bare=["آیدی", "ایدی"]) & filters.group,
    group=1,
)
@player_handler()
async def id_command(_client: Client, message, s):
    """آیدی کاربر همراه با رتبه و زمان حضورش در ویس‌چت گروه."""
    chat_id = message.chat.id
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    if target is None:
        await message.reply_text(s("err_not_reply_user"))
        return

    days = callstats.last_days(7)
    rank, seconds, total = callstats.user_rank(chat_id, target.id, days)
    name = " ".join(filter(None, [target.first_name, target.last_name])) or str(target.id)
    await message.reply_text(
        s(
            "id_card",
            user=f"[{name}](tg://user?id={target.id})",
            user_id=target.id,
            chat_id=chat_id,
            rank=rank or "-",
            total=total,
            duration=seconds_to_clock(seconds),
        ),
        disable_web_page_preview=True,
    )


# ── پیام‌های سرویسی ویس‌چت (شروع/پایان) ───────────────────────────────────────
@Client.on_message(filters.video_chat_started & filters.group, group=2)
async def voice_chat_started(_client: Client, message):
    callwatch.mark_open(message.chat.id)
    await _clean_service_message(message)


@Client.on_message(filters.video_chat_ended & filters.group, group=2)
async def voice_chat_ended(_client: Client, message):
    await callwatch.mark_closed(message.chat.id)
    await _clean_service_message(message)


@Client.on_message(filters.video_chat_members_invited & filters.group, group=2)
async def voice_chat_invited(_client: Client, message):
    await _clean_service_message(message)


async def _clean_service_message(message) -> None:
    """با «پیام کال غیرفعال» پیام‌های سرویسی ویس‌چت در گروه نگه داشته نمی‌شوند."""
    if db.chat_setting(message.chat.id, "call_service_messages", True):
        return
    try:
        await message.delete()
    except Exception:  # noqa: BLE001
        pass


async def _require_admin(message, s) -> bool:
    from ..core.admins import can_control

    user = message.from_user
    if user and await can_control(message.chat.id, user.id):
        return True
    await message.reply_text(s("err_admin_only"))
    return False
