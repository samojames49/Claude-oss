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
    "help_call": (
        "🎙 **ویس‌چت و بازی**\n\n"
        "• `پنل پلیر` پنل دکمه‌ای همهٔ تنظیمات — `فهرست پیوی` همان پنل در پیوی\n"
        "• `آمار کال` آمار حضور اعضا (`آمار کال 7`، `آمار کال جمعه`) — `آیدی` کارت کاربر\n"
        "• `امنیت کال فعال` گزارش رفتار مشکوک — `میوت ورودی کال`، `قدمت اکانت 7`\n"
        "• `صندلی داغ [دقیقه]` شروع بازی — `افزودن مهمان` / `حذف مهمان` (ریپلای)\n"
        "  `مهمان بعدی`، `صندلی داغ لیست`، `پایان صندلی داغ`\n"
        "• `پخش زنده` منوی شبکه‌های تلویزیون/ماهواره — `فیلم` و `سریال` جستجوی ویدیویی\n"
        "• `زیرنویس` (ریپلای روی فایل srt) چسباندن زیرنویس روی ویدیو\n"
        "• `تنظیم عنوان کال`، `دعوت کال اخیر`، `دعوت کال ویژه`\n"
        "• `زمان پخش 01:20`، `صدا رسانه 150`، `دانلود <لینک>`"
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
    "button_pick_play": "🎧 پخش صوتی",
    "button_pick_vplay": "🎬 پخش ویدیویی",
    "button_pick_song": "⬇️ فایل آهنگ",
    "button_pick_video": "⬇️ فایل ویدیو",
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
    "download_usage": (
        "لینک محتوا را بعد از دستور بنویسید:\n"
        "`دانلود https://www.instagram.com/reel/…`\n\n"
        "یوتیوب، اینستاگرام، تیک‌تاک و هر لینکی که yt-dlp پشتیبانی کند.\n"
        "محتوا باید عمومی باشد و پخش زنده نباشد."
    ),
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
    "timeplay_usage": (
        "زمان دلخواه را بنویسید:\n"
        "• ثانیه: `زمان پخش 45`\n"
        "• دقیقه: `زمان پخش 03:20`\n"
        "• ساعت: `زمان پخش 01:02:03`"
    ),
    "media_volume_set": "🎚 صدای رسانه روی **{volume}%** تنظیم شد.",
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
    "film_usage": "نام فیلم را بنویسید:\n`فیلم اسم فیلم`",
    "serial_usage": "نام سریال را بنویسید:\n`سریال اسم سریال`",
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
    # ── زیرنویس ──────────────────────────────────────────────────────────────
    "subtitle_usage": (
        "روی فایل زیرنویس (`srt`, `vtt`, `ass`) ریپلای کنید و بنویسید «زیرنویس».\n"
        "برای برداشتن زیرنویس: `زیرنویس حذف`"
    ),
    "subtitle_applied": "📝 زیرنویس روی **{title}** چسبانده شد و پخش از همان لحظه ادامه یافت.",
    "subtitle_removed": "📝 زیرنویس برداشته شد.",
    "subtitle_audio_only": "⚠️ زیرنویس فقط روی پخش ویدیویی معنا دارد.",
    "subtitle_disabled": "قابلیت زیرنویس خاموش است.",
    "err_subtitle_audio": "⚠️ زیرنویس فقط روی پخش ویدیویی معنا دارد.",
    # ── پنل پلیر ─────────────────────────────────────────────────────────────
    "panel_home": (
        "🎛 **پنل پلیر — {chat}**\n\n"
        "▫️ اجازهٔ پخش: **{play_mode}**\n"
        "▫️ آمار کال: **{stats}**\n"
        "▫️ امنیت کال: **{security}**\n"
        "▫️ کانال پلیر: **{channel}**\n\n"
        "یک بخش را انتخاب کنید:"
    ),
    "panel_section_header": "🎛 **{section}** — {chat}\n\nروی هر دکمه بزنید تا مقدارش عوض شود:",
    "panel_section_play": "🎚 پخش",
    "panel_section_stats": "🎙 آمار کال",
    "panel_section_security": "🛡 امنیت کال",
    "panel_section_look": "🪴 ظاهر و پیام‌ها",
    "panel_btn_play_mode": "🎚 اجازهٔ پخش: {value}",
    "panel_btn_auto_leave": "🚪 خروج خودکار: {value}",
    "panel_btn_now_playing_message": "📢 پیام پخش: {value}",
    "panel_btn_play_in_channel": "☕️ پخش در کانال: {value}",
    "panel_btn_call_stats": "🎙 ثبت آمار کال: {value}",
    "panel_btn_call_stats_auto": "📨 ارسال خودکار آمار: {value}",
    "panel_btn_call_stats_reset": "🔄 ریست آمار: {value}",
    "panel_btn_call_security": "🛡 امنیت کال: {value}",
    "panel_btn_security_mute_on_join": "🎤 میوت ورودی کال: {value}",
    "panel_btn_security_report": "👏 ارسال گزارش: {value}",
    "panel_btn_security_summary": "🤡 خلاصهٔ ویس‌چت: {value}",
    "panel_btn_security_owners_access": "😴 دسترسی مالکان: {value}",
    "panel_btn_security_min_age_days": "🥶 قدمت اکانت: {value}",
    "panel_btn_classic_mode": "🪴 حالت کلاسیک: {value}",
    "panel_btn_auto_clear": "🧹 پاک‌سازی خودکار: {value}",
    "panel_btn_language": "🌐 زبان: {value}",
    "panel_reset_off": "خاموش",
    "panel_reset_daily": "روزانه",
    "panel_reset_monthly": "ماهیانه",
    "panel_days": "{days} روز",
    "panel_age_0": "بدون محدودیت",
    "panel_age_3": "۳ روز",
    "panel_age_7": "۷ روز",
    "panel_age_14": "۱۴ روز",
    "panel_no_channel": "ندارد",
    "panel_owner_only": "این بخش فقط برای مالک گروه است (دسترسی مالکان خاموش است).",
    "panel_expired": "این پنل منقضی شده؛ دوباره دستور «پنل پلیر» را بزنید.",
    "menupv_sent": "📬 پنل تنظیمات در چت خصوصی برایتان فرستاده شد.",
    "menupv_failed": "❌ نتوانستم پیام بفرستم؛ اول ربات را در پیوی استارت کنید.",
    # ── مدیریت ویس‌چت ────────────────────────────────────────────────────────
    "call_title_usage": "عنوان دلخواه را بعد از دستور بنویسید:\n`تنظیم عنوان کال شب‌نشینی`",
    "call_title_set": "✏️ عنوان ویس‌چت روی **{title}** تنظیم شد.",
    "invite_started": "📨 در حال دعوت {count} نفر به ویس‌چت…",
    "invite_done": "📨 دعوت انجام شد: **{invited}** از {total} نفر.",
    "invite_no_target": "کسی برای دعوت پیدا نشد.",
    "autoclear_on": "🧹 پاک‌سازی خودکار پیام پایان پخش فعال شد.",
    "autoclear_off": "🧹 پاک‌سازی خودکار غیرفعال شد.",
    "classic_on": "🪴 حالت کلاسیک فعال شد؛ پاسخ‌ها ساده و بدون تصویر می‌شوند.",
    "classic_off": "🪴 حالت کلاسیک غیرفعال شد؛ پنل تصویری برگشت.",
    "play_channel_on": "☕️ از این پس پخش در ویس‌چت کانال متصل انجام می‌شود.",
    "play_channel_off": "☕️ پخش به ویس‌چت خود گروه برگشت.",
    "play_channel_missing": "اول با `تنظیم کانال پلیر` یک کانال به گروه وصل کنید.",
    "play_channel_usage": (
        "آیدی یا یوزرنیم کانال را بنویسید:\n"
        "`تنظیم کانال پلیر -1001234567890`\n"
        "یا روی پیامی که از آن کانال فوروارد شده ریپلای کنید.\n"
        "برای حذف: `تنظیم کانال پلیر حذف`"
    ),
    "play_channel_set": "🔗 کانال **{title}** (`{chat_id}`) به پلیر گروه وصل شد.",
    "play_channel_removed": "🔗 اتصال کانال پلیر حذف شد.",
    "play_channel_unreachable": "❌ کانال در دسترس نیست:\n`{error}`",
    # ── پخش زنده تلویزیون/ماهواره ────────────────────────────────────────────
    "live_header": (
        "📡 **پخش زنده**\n\n"
        "{count} شبکه در {categories} دسته.\n"
        "یک دسته را انتخاب کنید یا بنویسید: `پخش زنده نام شبکه`"
    ),
    "live_category_header": "📡 **{title}**\n\n{count} شبکه — یکی را انتخاب کنید:",
    "live_starting": "📡 در حال اتصال به {name}…",
    "live_not_found": "📡 شبکه‌ای با نام «{query}» پیدا نشد.",
    "live_empty": (
        "📡 فهرست شبکه‌ها خالی است.\n"
        "فایل `player/data/live_channels.json` را پر کنید یا مسیر دیگری را با "
        "`LIVE_CHANNELS_FILE` بدهید."
    ),
    "live_reloaded": "♻️ فهرست شبکه‌ها خوانده شد: {count} شبکه در {categories} دسته.",
    # ── آمار کال ─────────────────────────────────────────────────────────────
    "callstats_header": "🎙 **آمار کال — {title}**\n\n",
    "callstats_item": "**{index}.** {user} — `{duration}`\n",
    "callstats_empty": "🎙 برای این بازه آماری ثبت نشده است.",
    "callstats_title_today": "امروز",
    "callstats_title_days": "{count} روز اخیر",
    "callstats_title_day": "{day}",
    "callstats_on": "✅ ثبت آمار کال در این گروه فعال شد.",
    "callstats_off": "🚫 ثبت آمار کال در این گروه غیرفعال شد.",
    "callstats_disabled_hint": "\n\n⚠️ ثبت آمار کال خاموش است؛ با `آمار کال فعال` روشنش کنید.",
    "callstats_auto_on": "✅ ارسال خودکار آمار پس از بسته‌شدن ویس‌چت فعال شد.",
    "callstats_auto_off": "🚫 ارسال خودکار آمار غیرفعال شد.",
    "callstats_need_switch": "بنویسید «فعال» یا «غیرفعال».",
    "callstats_bad_argument": (
        "یکی از این حالت‌ها را بنویسید:\n"
        "• `آمار کال` — امروز\n"
        "• `آمار کال 7` — ۱ تا ۷ روز اخیر\n"
        "• `آمار کال جمعه` — یک روز هفته\n"
        "• `آمار کال فعال` / `آمار کال غیرفعال`"
    ),
    "callstats_reset_done": "🗑 آمار کال گروه پاک شد ({days} روز).",
    "callstats_reset_daily": "🔄 آمار کال هر روز به‌طور خودکار ریست می‌شود.",
    "callstats_reset_monthly": "🔄 آمار کال هر ماه به‌طور خودکار ریست می‌شود.",
    "callstats_reset_off": "🔄 ریست خودکار آمار کال خاموش شد.",
    "id_card": (
        "🆔 **کارت کاربر**\n\n"
        "▫️ **کاربر:** {user}\n"
        "▫️ **آیدی عددی:** `{user_id}`\n"
        "▫️ **گروه:** `{chat_id}`\n"
        "▫️ **رتبهٔ ویس‌چت (۷ روز):** {rank} از {total}\n"
        "▫️ **زمان حضور:** `{duration}`"
    ),
    # ── امنیت کال ────────────────────────────────────────────────────────────
    "security_report_header": "🛡 **گزارش امنیت کال**\n\n",
    "security_event_line": "• {user} — {event}\n",
    "security_event_rejoin": "ورود متعدد به کال",
    "security_event_unmuted_join": "مایک فعال به هنگام ورود",
    "security_event_video_rejoin": "ورود ویدیویی متعدد",
    "security_event_multi_source": "منابع پخش متعدد",
    "security_event_multi_endpoint": "خروجی‌های متعدد",
    "security_event_time_gap": "وقفهٔ زمانی غیرعادی",
    "security_summary_title": "خلاصهٔ امنیت ویس‌چت",
    "security_summary_meta": "گروه: {chat_id} | مدت کال: {duration}",
    "security_summary_totals": "جمع‌بندی:",
    "security_summary_caption": "🛡 خلاصهٔ رفتارهای مشکوک این ویس‌چت.",
    "security_on": "🛡 امنیت کال فعال شد.",
    "security_off": "🛡 امنیت کال غیرفعال شد.",
    "security_age_set": "🥶 قدمت عضویت لازم روی **{days} روز** تنظیم شد.",
    "security_age_prompt": "تعداد روز را بفرستید (مثال: `قدمت اکانت 7`).",
    "mute_join_on": "🎤 میوت ورودی کال فعال شد؛ اعضای تازه‌وارد باید اجازهٔ صحبت بگیرند.",
    "mute_join_off": "🎤 میوت ورودی کال غیرفعال شد.",
    "call_message_on": "💬 پیام‌های ویس‌چت در گروه نگه داشته می‌شوند.",
    "call_message_off": "💬 پیام‌های ویس‌چت از این پس پاک می‌شوند.",
    # ── صندلی داغ ────────────────────────────────────────────────────────────
    "hotseat_started": (
        "🔥 **صندلی داغ شروع شد!**\n\n"
        "▫️ زمان هر نوبت: **{turn}**\n"
        "▫️ مهمان‌ها: **{count}**\n\n"
        "با ریپلای روی کاربر و «افزودن مهمان» نفرات را اضافه کنید."
    ),
    "hotseat_turn": (
        "🔥 **صندلی داغ**\n\n"
        "🎤 نوبت {guest}\n"
        "⏳ زمان نوبت: **{turn}**\n"
        "👥 در انتظار: **{waiting}** نفر"
    ),
    "hotseat_status": (
        "🔥 **صندلی داغ — {chat}**\n\n"
        "🎤 روی صندلی: {guest}\n"
        "⏳ باقی‌مانده: **{left}**\n"
        "🔁 نوبت‌های انجام‌شده: **{served}**\n\n"
        "👥 **صف مهمان‌ها:**\n{waiting}"
    ),
    "hotseat_waiting_item": "**{index}.** {guest}\n",
    "hotseat_no_guests": "صف مهمان‌ها خالی است.",
    "hotseat_empty_seat": "کسی روی صندلی نیست",
    "hotseat_unlimited": "بی‌زمان",
    "hotseat_paused": "⏸ نوبت متوقف شد؛ زمان نگه داشته شد.",
    "hotseat_resumed": "▶️ نوبت ادامه یافت.",
    "hotseat_finished": "🔥 **صندلی داغ تمام شد.**\n🔁 مجموع نوبت‌ها: **{served}**",
    "hotseat_already": "🔥 یک بازی صندلی داغ در جریان است؛ اول با «پایان صندلی داغ» تمامش کنید.",
    "hotseat_not_active": "🔥 بازی صندلی داغ فعال نیست؛ با «صندلی داغ» شروعش کنید.",
    "hotseat_usage": (
        "🔥 **صندلی داغ**\n\n"
        "• `صندلی داغ` شروع با زمان پیش‌فرض نوبت\n"
        "• `صندلی داغ 3` زمان هر نوبت ۳ دقیقه (`صندلی داغ 0` بی‌زمان)\n"
        "• با ریپلای روی یک کاربر، او اولین مهمان می‌شود."
    ),
    "hotseat_need_guest": "روی پیام کاربر ریپلای کنید یا آیدی/یوزرنیم او را بنویسید.",
    "hotseat_guest_added": "🔥 {user} به مهمان‌های صندلی داغ اضافه شد (نفر {position} صف).",
    "hotseat_guest_exists": "{user} از قبل در بازی است.",
    "hotseat_guest_removed": "🔥 {user} از بازی حذف شد.",
    "hotseat_guest_missing": "{user} در بازی نیست.",
    "hotseat_limit": "سقف مهمان‌های هر بازی {limit} نفر است.",
    "hotseat_mic_hint": (
        "\n\n⚠️ نتوانستم مایک‌ها را مدیریت کنم؛ اسیستنت باید ادمین گروه با دسترسی "
        "«مدیریت ویدیو چت» باشد."
    ),
    "button_hotseat_next": "⏭ مهمان بعدی",
    "button_hotseat_pause": "⏸ توقف نوبت",
    "button_hotseat_resume": "▶️ ادامهٔ نوبت",
    "button_hotseat_end": "⏹ پایان بازی",
    # ── لاگ ──────────────────────────────────────────────────────────────────
    "log_new_chat": "🆕 **گروه جدید**\nنام: {title}\nآیدی: `{chat_id}`\nافزوده توسط: {user}",
    "log_left_chat": "👋 **خروج از گروه**\nنام: {title}\nآیدی: `{chat_id}`",
    "log_new_user": "🆕 **کاربر جدید**\n{user} — `{user_id}`",
    "log_play": "▶️ **پخش**\nگروه: {title} (`{chat_id}`)\nمورد: {track}\nکاربر: {user}",
}
