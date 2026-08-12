"""رشته‌های فارسی ربات پلیر."""

STRINGS = {
    # ── عمومی ────────────────────────────────────────────────────────────────
    "lang_name": "فارسی",
    "start_private": (
        "🎧 **{bot_name}** خوش آمدید {mention}!\n\n"
        "من می‌توانم آهنگ و ویدیو را در **ویس‌چت گروه‌ها** پخش کنم.\n"
        "کافی است مرا به گروه اضافه و ادمین کنید، ویس‌چت را روشن کنید و بنویسید:\n"
        "`/play نام آهنگ`\n\n"
        "برای دیدن همهٔ دستورها روی «راهنما» بزنید."
    ),
    "start_group": "🎧 **{bot_name}** فعال است!\nبرای پخش: `/play نام آهنگ`\nراهنما: /help",
    "help_header": (
        "📖 **راهنمای {bot_name}**\n\nیک بخش را انتخاب کنید:"
    ),
    "help_play": (
        "🎵 **پخش**\n\n"
        "• `/play <نام یا لینک>` — پخش صوتی (یوتیوب، لینک مستقیم یا فایل ریپلای‌شده)\n"
        "• `/vplay <نام یا لینک>` — پخش ویدیویی\n"
        "• `/playforce` و `/vplayforce` — پخش فوری و پرش از صف\n"
        "• `/stream <لینک>` — پخش زندهٔ رادیو / m3u8 / لایو یوتیوب\n"
        "• ریپلای روی فایل صوتی یا ویدیویی + `/play`\n\n"
        "معادل فارسی: `پخش`، `بزن`، `پخش ویدیو`"
    ),
    "help_control": (
        "🎛 **کنترل پخش** (ادمین یا کاربر مجاز)\n\n"
        "• `/pause` توقف موقت — `/resume` ادامه\n"
        "• `/skip [شماره]` رد کردن — `/end` پایان پخش\n"
        "• `/volume 1-200` تنظیم صدا\n"
        "• `/seek <ثانیه>` و `/seekback <ثانیه>`\n"
        "• `/loop <عدد|off>` تکرار آهنگ فعلی\n"
        "• `/shuffle` بُر زدن صف — `/speed <0.5-2>` سرعت پخش\n"
        "• `/mute` و `/unmute` بی‌صدا کردن اسیستنت\n\n"
        "معادل فارسی: `توقف`، `ادامه`، `بعدی`، `پایان`، `صدا`، `تکرار`"
    ),
    "help_queue": (
        "📜 **صف پخش**\n\n"
        "• `/queue` نمایش صف\n"
        "• `/current` آهنگ در حال پخش\n"
        "• `/remove <شماره>` حذف از صف\n"
        "• `/clear` خالی کردن صف\n\n"
        "معادل فارسی: `صف`، `فعلی`"
    ),
    "help_tools": (
        "🧰 **ابزارها**\n\n"
        "• `/song <نام>` دانلود آهنگ به‌صورت فایل\n"
        "• `/video <نام>` دانلود ویدیو\n"
        "• `/search <نام>` جستجو در یوتیوب\n"
        "• `/lyrics <نام>` متن آهنگ\n"
        "• `/ping` و `/stats` وضعیت ربات\n"
        "• جستجوی اینلاین: `@{bot_username} نام آهنگ`"
    ),
    "help_admin": (
        "⚙️ **مدیریت گروه**\n\n"
        "• `/settings` پنل تنظیمات گروه\n"
        "• `/auth` و `/unauth` (ریپلای) دادن/گرفتن دسترسی پخش به کاربر عادی\n"
        "• `/authlist` لیست کاربران مجاز\n"
        "• `/reload` تازه‌سازی لیست ادمین‌ها\n"
        "• `/userbotjoin` و `/userbotleave` ورود/خروج اسیستنت"
    ),
    "help_sudo": (
        "🛡 **دستورهای سودو**\n\n"
        "• `/stats` آمار کامل — `/logs` ارسال فایل لاگ\n"
        "• `/broadcast <متن>` پیام همگانی (`-pin`, `-user`, `-nogroup`)\n"
        "• `/activevc` لیست پخش‌های فعال\n"
        "• `/addsudo` و `/delsudo` (ریپلای)\n"
        "• `/block` و `/unblock` (ریپلای) مسدودسازی کاربر\n"
        "• `/blockchat <id>` و `/unblockchat <id>`\n"
        "• `/maintenance <on|off>` حالت تعمیرات\n"
        "• `/cleanup` پاک‌سازی فایل‌های کش"
    ),
    "button_help": "📖 راهنما",
    "button_add_group": "➕ افزودن به گروه",
    "button_support": "💬 پشتیبانی",
    "button_channel": "📢 کانال",
    "button_owner": "👤 سازنده",
    "button_close": "✖️ بستن",
    "button_back": "◀️ بازگشت",
    "button_home": "🏠 خانه",
    # ── خطاها و هشدارها ──────────────────────────────────────────────────────
    "err_generic": "❌ خطایی رخ داد:\n`{error}`",
    "err_admin_only": "🚫 این دستور فقط برای **ادمین‌های گروه** است.",
    "err_sudo_only": "🚫 این دستور فقط برای ادمین‌های اصلی ربات است.",
    "err_group_only": "این دستور فقط داخل گروه کار می‌کند.",
    "err_private_only": "این دستور فقط در چت خصوصی ربات کار می‌کند.",
    "err_play_mode_admins": "🚫 در این گروه فقط ادمین‌ها و کاربران مجاز می‌توانند پخش کنند.",
    "err_no_active": "⚠️ در این گروه چیزی در حال پخش نیست.",
    "err_no_vc": (
        "⚠️ ویس‌چت گروه روشن نیست یا اسیستنت اجازهٔ ورود ندارد.\n"
        "ابتدا ویس‌چت را شروع کنید و دوباره تلاش کنید."
    ),
    "err_queue_limit": "⚠️ صف پخش پر است (حداکثر {limit} آهنگ).",
    "err_duration_limit": "⚠️ مدت این مورد {duration} است و از سقف مجاز ({limit} دقیقه) بیشتر است.",
    "err_no_result": "🔍 چیزی پیدا نشد. عبارت دیگری را امتحان کنید.",
    "err_need_query": "چه چیزی پخش کنم؟\nمثال: `/play شادمهر عقیلی`\nیا روی یک فایل صوتی/ویدیویی ریپلای کنید.",
    "err_file_too_big": "⚠️ حجم فایل بیش از حد مجاز است (سقف {limit} مگابایت).",
    "err_blocked_user": "🚫 دسترسی شما به ربات مسدود شده است.",
    "err_blocked_chat": "🚫 این گروه از استفاده از ربات محروم شده است.",
    "err_private_mode": "🚫 ربات در حالت خصوصی است؛ این گروه تایید نشده.",
    "err_maintenance": "🛠 ربات در حال تعمیر است؛ کمی بعد دوباره تلاش کنید.",
    "err_video_limit": "⚠️ سقف پخش ویدیویی هم‌زمان ({limit} گروه) پر است. فعلاً صوتی پخش می‌شود.",
    "err_invalid_number": "یک عدد معتبر بفرستید.",
    "err_not_reply_user": "روی پیام کاربر ریپلای کنید.",
    "err_assistant_banned": "🚫 اسیستنت ({assistant}) در این گروه محروم است؛ لطفاً آزادش کنید.",
    "err_assistant_failed": "❌ اسیستنت نتوانست وارد گروه شود:\n`{error}`",
    "err_live_no_seek": "⚠️ روی پخش زنده امکان جابه‌جایی زمان نیست.",
    "err_seek_range": "⚠️ زمان درخواستی از مدت آهنگ بیشتر است.",
    "force_sub": "📢 برای استفاده از ربات ابتدا در کانال زیر عضو شوید:\n{channel}",
    # ── پخش ──────────────────────────────────────────────────────────────────
    "processing": "🔄 در حال پردازش…",
    "searching": "🔍 در حال جستجو…",
    "downloading": "⬇️ در حال دریافت…",
    "joining": "🔗 اسیستنت در حال ورود به ویس‌چت…",
    "assistant_joined": "✅ اسیستنت وارد گروه شد.",
    "assistant_left": "✅ اسیستنت از گروه خارج شد.",
    "assistant_already_in": "اسیستنت از قبل در گروه حاضر است.",
    "now_playing": (
        "🎧 **در حال پخش**\n\n"
        "▫️ **نام:** {title}\n"
        "▫️ **مدت:** {duration}\n"
        "▫️ **نوع:** {kind}\n"
        "▫️ **درخواست:** {requester}"
    ),
    "added_to_queue": (
        "➕ **به صف اضافه شد** (جایگاه {position})\n\n"
        "▫️ **نام:** {title}\n"
        "▫️ **مدت:** {duration}\n"
        "▫️ **درخواست:** {requester}"
    ),
    "stream_kind_audio": "🎵 صوتی",
    "stream_kind_video": "🎬 ویدیویی",
    "stream_kind_live": "🔴 پخش زنده",
    "paused": "⏸ پخش متوقف شد.\nبرای ادامه: /resume",
    "resumed": "▶️ پخش ادامه یافت.",
    "already_paused": "پخش از قبل متوقف است.",
    "already_playing": "پخش در جریان است.",
    "skipped": "⏭ رد شد: **{title}**",
    "skipped_index": "⏭ از صف حذف شد: **{title}**",
    "ended": "⏹ پخش پایان یافت و اسیستنت خارج شد.\nدرخواست: {requester}",
    "muted": "🔇 اسیستنت بی‌صدا شد.",
    "unmuted": "🔊 صدای اسیستنت برگشت.",
    "volume_set": "🔊 صدا روی **{volume}%** تنظیم شد.",
    "volume_range": "عدد صدا باید بین ۱ تا ۲۰۰ باشد.",
    "seeked": "⏩ به **{position}** پرش شد.",
    "loop_on": "🔁 تکرار برای **{count}** بار بعدی فعال شد.",
    "loop_off": "➡️ تکرار خاموش شد.",
    "shuffled": "🔀 صف بُر زده شد ({count} مورد).",
    "speed_set": "⚡️ سرعت پخش روی **{speed}x** تنظیم شد.",
    "speed_range": "سرعت باید بین ۰٫۵ تا ۲ باشد.",
    "queue_cleared": "🗑 صف پخش خالی شد.",
    "queue_empty": "صف پخش خالی است.",
    "queue_header": "📜 **صف پخش گروه**\n\n🎧 در حال پخش: **{current}**\n\n",
    "queue_item": "**{index}.** {title} — `{duration}` — {requester}\n",
    "queue_more": "\n… و {count} مورد دیگر.",
    "removed_from_queue": "🗑 از صف حذف شد: **{title}**",
    "current_status": (
        "🎧 **در حال پخش**\n\n"
        "▫️ **نام:** {title}\n"
        "▫️ **زمان:** {played} / {duration}\n"
        "{bar}\n"
        "▫️ **درخواست:** {requester}"
    ),
    "next_in_queue": "⏭ آهنگ بعدی: **{title}**",
    "stream_end_empty": "✅ صف پخش تمام شد؛ اسیستنت از ویس‌چت خارج شد.",
    "auto_left_inactive": "💤 چون مدتی پخشی انجام نشد، اسیستنت خارج شد.",
    "auto_left_empty": "👋 کسی در ویس‌چت نبود؛ اسیستنت خارج شد.",
    "vc_closed": "⚠️ ویس‌چت بسته شد؛ پخش متوقف شد.",
    # ── دکمه‌های پنل ─────────────────────────────────────────────────────────
    "button_pause": "⏸ توقف",
    "button_resume": "▶️ ادامه",
    "button_skip": "⏭ بعدی",
    "button_stop": "⏹ پایان",
    "button_replay": "🔄 از اول",
    "button_mute": "🔇 بی‌صدا",
    "button_unmute": "🔊 باصدا",
    "button_queue": "📜 صف",
    "button_vol_up": "🔊 +",
    "button_vol_down": "🔉 −",
    "button_loop": "🔁 تکرار",
    "button_shuffle": "🔀 بُر",
    "button_refresh": "♻️ بروزرسانی",
    "callback_admin_only": "فقط ادمین‌ها می‌توانند کنترل کنند.",
    "callback_done": "انجام شد ✅",
    "callback_no_active": "چیزی در حال پخش نیست.",
    # ── تنظیمات گروه ─────────────────────────────────────────────────────────
    "settings_header": (
        "⚙️ **تنظیمات گروه {chat}**\n\n"
        "▫️ اجازهٔ پخش: **{play_mode}**\n"
        "▫️ زبان: **{language}**\n"
        "▫️ خروج خودکار اسیستنت: **{auto_leave}**\n"
        "▫️ پیام «در حال پخش»: **{now_playing}**\n"
        "▫️ سقف مدت هر مورد: **{duration_limit} دقیقه**"
    ),
    "settings_play_mode_everyone": "همه اعضا",
    "settings_play_mode_admins": "فقط ادمین‌ها",
    "settings_on": "روشن",
    "settings_off": "خاموش",
    "button_toggle_play_mode": "🎚 اجازهٔ پخش: {value}",
    "button_toggle_auto_leave": "🚪 خروج خودکار: {value}",
    "button_toggle_now_playing": "📢 پیام پخش: {value}",
    "button_language": "🌐 زبان: {value}",
    "language_changed": "🌐 زبان گروه روی **{language}** تنظیم شد.",
    # ── دسترسی کاربران ───────────────────────────────────────────────────────
    "auth_added": "✅ {user} به لیست کاربران مجاز اضافه شد.",
    "auth_removed": "✅ {user} از لیست کاربران مجاز حذف شد.",
    "auth_exists": "{user} از قبل در لیست مجاز است.",
    "auth_missing": "{user} در لیست مجاز نیست.",
    "auth_list": "👥 **کاربران مجاز این گروه:**\n\n{users}",
    "auth_list_empty": "لیست کاربران مجاز خالی است.",
    "admins_reloaded": "♻️ لیست ادمین‌ها بروزرسانی شد ({count} ادمین).",
    # ── ابزارها ──────────────────────────────────────────────────────────────
    "song_caption": "🎵 **{title}**\n⏱ {duration}\n👤 درخواست: {requester}",
    "lyrics_result": "📝 **متن {title}**\n\n{lyrics}",
    "lyrics_not_found": "متن این آهنگ پیدا نشد.",
    "lyrics_disabled": "قابلیت متن آهنگ خاموش است.",
    "search_header": "🔍 **نتایج جستجو برای:** {query}\n\nیکی را انتخاب کنید:",
    "inline_no_query": "نام آهنگ را بنویسید…",
    "inline_play_hint": "برای پخش، نتیجه را در گروه بفرستید.",
    "ping_reply": (
        "🏓 **پینگ:** `{ping}ms`\n"
        "⏱ **آپ‌تایم:** `{uptime}`\n"
        "🖥 **CPU:** `{cpu}%` | **RAM:** `{ram}%` | **دیسک:** `{disk}%`\n"
        "🎧 **پخش فعال:** `{active}`"
    ),
    "stats_reply": (
        "📊 **آمار {bot_name}**\n\n"
        "▫️ گروه‌ها: `{chats}`\n"
        "▫️ کاربران: `{users}`\n"
        "▫️ کل پخش‌ها: `{plays}`\n"
        "▫️ پخش فعال: `{active}`\n"
        "▫️ اسیستنت‌ها: `{assistants}`\n"
        "▫️ آپ‌تایم: `{uptime}`\n"
        "▫️ نسخه: `{version}`"
    ),
    "activevc_header": "🎧 **پخش‌های فعال ({count}):**\n\n",
    "activevc_item": "• `{chat_id}` — {title}\n",
    "activevc_empty": "هیچ پخش فعالی وجود ندارد.",
    "broadcast_need_text": "متن پیام همگانی را بنویسید یا روی یک پیام ریپلای کنید.",
    "broadcast_started": "📣 ارسال همگانی شروع شد…",
    "broadcast_done": "✅ پیام همگانی ارسال شد.\nگروه‌ها: {chats}\nکاربران: {users}\nناموفق: {failed}",
    "sudo_added": "✅ {user} به سودوها اضافه شد.",
    "sudo_removed": "✅ {user} از سودوها حذف شد.",
    "sudo_list": "🛡 **سودوها:**\n\n{users}",
    "blocked_user": "🚫 {user} مسدود شد.",
    "unblocked_user": "✅ {user} آزاد شد.",
    "blocked_chat": "🚫 گروه `{chat_id}` محروم شد.",
    "unblocked_chat": "✅ گروه `{chat_id}` آزاد شد.",
    "maintenance_on": "🛠 حالت تعمیرات روشن شد.",
    "maintenance_off": "✅ حالت تعمیرات خاموش شد.",
    "cleanup_done": "🧹 پاک‌سازی انجام شد: {count} فایل ({size}) حذف شد.",
    "logs_missing": "فایل لاگ موجود نیست.",
    # ── لاگ ──────────────────────────────────────────────────────────────────
    "log_new_chat": "🆕 **گروه جدید**\nنام: {title}\nآیدی: `{chat_id}`\nافزوده توسط: {user}",
    "log_left_chat": "👋 **خروج از گروه**\nنام: {title}\nآیدی: `{chat_id}`",
    "log_new_user": "🆕 **کاربر جدید**\n{user} — `{user_id}`",
    "log_play": "▶️ **پخش**\nگروه: {title} (`{chat_id}`)\nمورد: {track}\nکاربر: {user}",
}
