"""English strings for the player bot."""

STRINGS = {
    # ── general ──────────────────────────────────────────────────────────────
    "lang_name": "English",
    "start_private": (
        "🎧 Welcome to **{bot_name}**, {mention}!\n\n"
        "I can stream music and video inside **group voice chats**.\n"
        "Add me to your group as admin, start a voice chat and send:\n"
        "`/play song name`\n\n"
        "Tap “Help” to see every command."
    ),
    "start_group": "🎧 **{bot_name}** is up!\nTo play: `/play song name`\nHelp: /help",
    "help_header": "📖 **{bot_name} help**\n\nPick a section:",
    "help_play": (
        "🎵 **Playback**\n\n"
        "• `/play <name or link>` — audio stream (YouTube, direct link or replied file)\n"
        "• `/vplay <name or link>` — video stream\n"
        "• `/playforce`, `/vplayforce` — play instantly, skipping the queue\n"
        "• `/stream <link>` — live radio / m3u8 / YouTube live\n"
        "• reply to an audio or video file with `/play`"
    ),
    "help_control": (
        "🎛 **Controls** (admins or authorised users)\n\n"
        "• `/pause`, `/resume`\n"
        "• `/skip [number]`, `/end`\n"
        "• `/volume 1-200`\n"
        "• `/seek <seconds>`, `/seekback <seconds>`\n"
        "• `/loop <count|off>`\n"
        "• `/shuffle`, `/speed <0.5-2>`\n"
        "• `/mute`, `/unmute`"
    ),
    "help_queue": (
        "📜 **Queue**\n\n"
        "• `/queue` show the queue\n"
        "• `/current` current track\n"
        "• `/remove <number>` drop one item\n"
        "• `/clear` empty the queue"
    ),
    "help_tools": (
        "🧰 **Tools**\n\n"
        "• `/song <name>` download audio\n"
        "• `/video <name>` download video\n"
        "• `/search <name>` search YouTube\n"
        "• `/lyrics <name>` song lyrics\n"
        "• `/ping`, `/stats` bot status\n"
        "• inline search: `@{bot_username} song name`"
    ),
    "help_admin": (
        "⚙️ **Group management**\n\n"
        "• `/settings` group settings panel\n"
        "• `/auth`, `/unauth` (reply) allow a normal member to control playback\n"
        "• `/authlist` authorised users\n"
        "• `/reload` refresh admin cache\n"
        "• `/userbotjoin`, `/userbotleave` assistant join/leave"
    ),
    "help_sudo": (
        "🛡 **Sudo commands**\n\n"
        "• `/stats`, `/logs`\n"
        "• `/broadcast <text>` (`-pin`, `-user`, `-nogroup`)\n"
        "• `/activevc` active streams\n"
        "• `/addsudo`, `/delsudo` (reply)\n"
        "• `/block`, `/unblock` (reply)\n"
        "• `/blockchat <id>`, `/unblockchat <id>`\n"
        "• `/maintenance <on|off>`\n"
        "• `/cleanup` clear cached files"
    ),
    "button_help": "📖 Help",
    "button_add_group": "➕ Add to group",
    "button_support": "💬 Support",
    "button_channel": "📢 Channel",
    "button_owner": "👤 Owner",
    "button_close": "✖️ Close",
    "button_back": "◀️ Back",
    "button_home": "🏠 Home",
    # ── errors ───────────────────────────────────────────────────────────────
    "err_generic": "❌ Something went wrong:\n`{error}`",
    "err_admin_only": "🚫 This command is for **group admins** only.",
    "err_sudo_only": "🚫 This command is for bot sudo users only.",
    "err_group_only": "This command only works inside groups.",
    "err_private_only": "This command only works in the bot's private chat.",
    "err_play_mode_admins": "🚫 Only admins and authorised users can play here.",
    "err_no_active": "⚠️ Nothing is playing in this chat.",
    "err_no_vc": (
        "⚠️ The group voice chat is off or the assistant cannot join.\n"
        "Start a voice chat and try again."
    ),
    "err_queue_limit": "⚠️ Queue is full (max {limit} items).",
    "err_duration_limit": "⚠️ Duration is {duration}, above the {limit} minute limit.",
    "err_no_result": "🔍 Nothing found. Try another query.",
    "err_need_query": "What should I play?\nExample: `/play imagine dragons`\nOr reply to an audio/video file.",
    "download_usage": (
        "Send the content link after the command:\n"
        "`/dl https://www.instagram.com/reel/…`\n\n"
        "YouTube, Instagram, TikTok and anything yt-dlp supports.\n"
        "The content must be public and not a live stream."
    ),
    "err_file_too_big": "⚠️ File is too large (limit {limit} MB).",
    "err_blocked_user": "🚫 You are blocked from using this bot.",
    "err_blocked_chat": "🚫 This chat is banned from using the bot.",
    "err_private_mode": "🚫 The bot is in private mode and this chat is not approved.",
    "err_maintenance": "🛠 The bot is under maintenance, try again later.",
    "err_video_limit": "⚠️ Video stream limit reached ({limit} chats); playing audio instead.",
    "err_invalid_number": "Send a valid number.",
    "err_not_reply_user": "Reply to a user's message.",
    "err_assistant_banned": "🚫 The assistant ({assistant}) is banned here, please unban it.",
    "err_assistant_failed": "❌ The assistant could not join:\n`{error}`",
    "err_live_no_seek": "⚠️ Seeking is not possible on a live stream.",
    "err_seek_range": "⚠️ Requested position is beyond the track duration.",
    "force_sub": "📢 Join this channel first to use the bot:\n{channel}",
    # ── playback ─────────────────────────────────────────────────────────────
    "processing": "🔄 Processing…",
    "searching": "🔍 Searching…",
    "downloading": "⬇️ Fetching…",
    "joining": "🔗 Assistant is joining the voice chat…",
    "assistant_joined": "✅ Assistant joined the group.",
    "assistant_left": "✅ Assistant left the group.",
    "assistant_already_in": "The assistant is already in this group.",
    "now_playing": (
        "🎧 **Now playing**\n\n"
        "▫️ **Title:** {title}\n"
        "▫️ **Duration:** {duration}\n"
        "▫️ **Type:** {kind}\n"
        "▫️ **Requested by:** {requester}"
    ),
    "added_to_queue": (
        "➕ **Added to queue** (position {position})\n\n"
        "▫️ **Title:** {title}\n"
        "▫️ **Duration:** {duration}\n"
        "▫️ **Requested by:** {requester}"
    ),
    "stream_kind_audio": "🎵 Audio",
    "stream_kind_video": "🎬 Video",
    "stream_kind_live": "🔴 Live",
    "paused": "⏸ Playback paused.\nResume with /resume",
    "resumed": "▶️ Playback resumed.",
    "already_paused": "Playback is already paused.",
    "already_playing": "Playback is already running.",
    "skipped": "⏭ Skipped: **{title}**",
    "skipped_index": "⏭ Removed from queue: **{title}**",
    "ended": "⏹ Playback stopped and the assistant left.\nBy: {requester}",
    "muted": "🔇 Assistant muted.",
    "unmuted": "🔊 Assistant unmuted.",
    "volume_set": "🔊 Volume set to **{volume}%**.",
    "volume_range": "Volume must be between 1 and 200.",
    "seeked": "⏩ Jumped to **{position}**.",
    "timeplay_usage": (
        "Send the target time:\n"
        "• seconds: `Time play 45`\n"
        "• minutes: `Time play 03:20`\n"
        "• hours: `Time play 01:02:03`"
    ),
    "media_volume_set": "🎚 Media volume set to **{volume}%**.",
    "loop_on": "🔁 Loop enabled for the next **{count}** rounds.",
    "loop_off": "➡️ Loop disabled.",
    "shuffled": "🔀 Queue shuffled ({count} items).",
    "speed_set": "⚡️ Playback speed set to **{speed}x**.",
    "speed_range": "Speed must be between 0.5 and 2.",
    "queue_cleared": "🗑 Queue cleared.",
    "queue_empty": "The queue is empty.",
    "queue_header": "📜 **Queue**\n\n🎧 Now playing: **{current}**\n\n",
    "queue_item": "**{index}.** {title} — `{duration}` — {requester}\n",
    "queue_more": "\n… and {count} more.",
    "removed_from_queue": "🗑 Removed: **{title}**",
    "current_status": (
        "🎧 **Now playing**\n\n"
        "▫️ **Title:** {title}\n"
        "▫️ **Position:** {played} / {duration}\n"
        "{bar}\n"
        "▫️ **Requested by:** {requester}"
    ),
    "next_in_queue": "⏭ Up next: **{title}**",
    "stream_end_empty": "✅ Queue finished; the assistant left the voice chat.",
    "auto_left_inactive": "💤 Nothing played for a while, assistant left.",
    "auto_left_empty": "👋 Nobody was in the voice chat, assistant left.",
    "vc_closed": "⚠️ The voice chat was closed; playback stopped.",
    # ── panel buttons ────────────────────────────────────────────────────────
    "button_pause": "⏸ Pause",
    "button_resume": "▶️ Resume",
    "button_skip": "⏭ Skip",
    "button_stop": "⏹ Stop",
    "button_replay": "🔄 Replay",
    "button_mute": "🔇 Mute",
    "button_unmute": "🔊 Unmute",
    "button_queue": "📜 Queue",
    "button_vol_up": "🔊 +",
    "button_vol_down": "🔉 −",
    "button_loop": "🔁 Loop",
    "button_shuffle": "🔀 Shuffle",
    "button_refresh": "♻️ Refresh",
    "callback_admin_only": "Only admins can use these controls.",
    "callback_done": "Done ✅",
    "callback_no_active": "Nothing is playing.",
    # ── group settings ───────────────────────────────────────────────────────
    "settings_header": (
        "⚙️ **Settings for {chat}**\n\n"
        "▫️ Play permission: **{play_mode}**\n"
        "▫️ Language: **{language}**\n"
        "▫️ Assistant auto leave: **{auto_leave}**\n"
        "▫️ Now-playing message: **{now_playing}**\n"
        "▫️ Duration limit: **{duration_limit} min**"
    ),
    "settings_play_mode_everyone": "Everyone",
    "settings_play_mode_admins": "Admins only",
    "settings_on": "on",
    "settings_off": "off",
    "button_toggle_play_mode": "🎚 Play permission: {value}",
    "button_toggle_auto_leave": "🚪 Auto leave: {value}",
    "button_toggle_now_playing": "📢 Now-playing msg: {value}",
    "button_language": "🌐 Language: {value}",
    "language_changed": "🌐 Chat language set to **{language}**.",
    # ── authorisation ────────────────────────────────────────────────────────
    "auth_added": "✅ {user} added to authorised users.",
    "auth_removed": "✅ {user} removed from authorised users.",
    "auth_exists": "{user} is already authorised.",
    "auth_missing": "{user} is not in the authorised list.",
    "auth_list": "👥 **Authorised users here:**\n\n{users}",
    "auth_list_empty": "The authorised list is empty.",
    "admins_reloaded": "♻️ Admin cache refreshed ({count} admins).",
    # ── tools ────────────────────────────────────────────────────────────────
    "song_caption": "🎵 **{title}**\n⏱ {duration}\n👤 By: {requester}",
    "lyrics_result": "📝 **Lyrics — {title}**\n\n{lyrics}",
    "lyrics_not_found": "No lyrics found for that track.",
    "lyrics_disabled": "Lyrics feature is disabled.",
    "search_header": "🔍 **Search results for:** {query}\n\nPick one:",
    "inline_no_query": "Type a song name…",
    "inline_play_hint": "Send the result in a group to play it.",
    "ping_reply": (
        "🏓 **Ping:** `{ping}ms`\n"
        "⏱ **Uptime:** `{uptime}`\n"
        "🖥 **CPU:** `{cpu}%` | **RAM:** `{ram}%` | **Disk:** `{disk}%`\n"
        "🎧 **Active streams:** `{active}`"
    ),
    "stats_reply": (
        "📊 **{bot_name} stats**\n\n"
        "▫️ Chats: `{chats}`\n"
        "▫️ Users: `{users}`\n"
        "▫️ Total plays: `{plays}`\n"
        "▫️ Active streams: `{active}`\n"
        "▫️ Assistants: `{assistants}`\n"
        "▫️ Uptime: `{uptime}`\n"
        "▫️ Version: `{version}`"
    ),
    "activevc_header": "🎧 **Active streams ({count}):**\n\n",
    "activevc_item": "• `{chat_id}` — {title}\n",
    "activevc_empty": "There are no active streams.",
    "broadcast_need_text": "Write the broadcast text or reply to a message.",
    "broadcast_started": "📣 Broadcast started…",
    "broadcast_done": "✅ Broadcast finished.\nChats: {chats}\nUsers: {users}\nFailed: {failed}",
    "sudo_added": "✅ {user} added to sudo users.",
    "sudo_removed": "✅ {user} removed from sudo users.",
    "sudo_list": "🛡 **Sudo users:**\n\n{users}",
    "blocked_user": "🚫 {user} blocked.",
    "unblocked_user": "✅ {user} unblocked.",
    "blocked_chat": "🚫 Chat `{chat_id}` banned.",
    "unblocked_chat": "✅ Chat `{chat_id}` unbanned.",
    "maintenance_on": "🛠 Maintenance mode enabled.",
    "maintenance_off": "✅ Maintenance mode disabled.",
    "cleanup_done": "🧹 Cleanup done: {count} files ({size}) removed.",
    "logs_missing": "Log file not found.",
    # ── voice chat management ────────────────────────────────────────────────
    "call_title_usage": "Write the title after the command:\n`/setcalltitle Movie night`",
    "call_title_set": "✏️ Voice chat title set to **{title}**.",
    "invite_started": "📨 Inviting {count} members to the voice chat…",
    "invite_done": "📨 Invited **{invited}** of {total} members.",
    "invite_no_target": "No one to invite.",
    "autoclear_on": "🧹 Auto-clearing of the stream-ended message enabled.",
    "autoclear_off": "🧹 Auto-clearing disabled.",
    "classic_on": "🪴 Classic mode on: plain replies without artwork.",
    "classic_off": "🪴 Classic mode off: the artwork panel is back.",
    "play_channel_on": "☕️ Playback now happens in the linked channel's voice chat.",
    "play_channel_off": "☕️ Playback moved back to this group's voice chat.",
    "play_channel_missing": "Link a channel first with `/setplayerchannel`.",
    "play_channel_usage": (
        "Send the channel id or username:\n"
        "`/setplayerchannel -1001234567890`\n"
        "Or reply to a message forwarded from that channel.\n"
        "To unlink: `/setplayerchannel remove`"
    ),
    "play_channel_set": "🔗 Channel **{title}** (`{chat_id}`) linked to this group's player.",
    "play_channel_removed": "🔗 Channel link removed.",
    "play_channel_unreachable": "❌ Channel unreachable:\n`{error}`",
    # ── live TV / satellite ──────────────────────────────────────────────────
    "live_header": (
        "📡 **Live TV**\n\n"
        "{count} channels in {categories} categories.\n"
        "Pick a category or type: `/live channel name`"
    ),
    "live_category_header": "📡 **{title}**\n\n{count} channels — pick one:",
    "live_starting": "📡 Connecting to {name}…",
    "live_not_found": "📡 No channel matching “{query}”.",
    "live_empty": (
        "📡 The channel list is empty.\n"
        "Fill `player/data/live_channels.json` or point `LIVE_CHANNELS_FILE` elsewhere."
    ),
    "live_reloaded": "♻️ Channel list reloaded: {count} channels in {categories} categories.",
    # ── voice chat stats ─────────────────────────────────────────────────────
    "callstats_header": "🎙 **Call stats — {title}**\n\n",
    "callstats_item": "**{index}.** {user} — `{duration}`\n",
    "callstats_empty": "🎙 No stats recorded for this period.",
    "callstats_title_today": "today",
    "callstats_title_days": "last {count} days",
    "callstats_title_day": "{day}",
    "callstats_on": "✅ Call stats recording enabled for this chat.",
    "callstats_off": "🚫 Call stats recording disabled for this chat.",
    "callstats_disabled_hint": "\n\n⚠️ Recording is off; turn it on with `Stats call active`.",
    "callstats_auto_on": "✅ Stats will be posted automatically when the voice chat ends.",
    "callstats_auto_off": "🚫 Automatic stats posting disabled.",
    "callstats_need_switch": "Write `active` or `inactive`.",
    "callstats_bad_argument": (
        "Use one of these forms:\n"
        "• `Stats call` — today\n"
        "• `Stats call 7` — last 1..7 days\n"
        "• `Stats call Friday` — a weekday\n"
        "• `Stats call active` / `Stats call inactive`"
    ),
    "callstats_reset_done": "🗑 Call stats cleared ({days} days).",
    "callstats_reset_daily": "🔄 Call stats will reset daily.",
    "callstats_reset_monthly": "🔄 Call stats will reset monthly.",
    "callstats_reset_off": "🔄 Automatic stats reset disabled.",
    "id_card": (
        "🆔 **User card**\n\n"
        "▫️ **User:** {user}\n"
        "▫️ **ID:** `{user_id}`\n"
        "▫️ **Chat:** `{chat_id}`\n"
        "▫️ **Voice chat rank (7d):** {rank} of {total}\n"
        "▫️ **Time in call:** `{duration}`"
    ),
    # ── call security ────────────────────────────────────────────────────────
    "security_report_header": "🛡 **Call security report**\n\n",
    "security_event_line": "• {user} — {event}\n",
    "security_event_rejoin": "repeated joins",
    "security_event_unmuted_join": "unmuted microphone on join",
    "security_event_video_rejoin": "repeated video joins",
    "security_event_multi_source": "multiple stream sources",
    "security_event_multi_endpoint": "multiple endpoints",
    "security_event_time_gap": "abnormal time gap",
    "security_summary_title": "Voice chat security summary",
    "security_summary_meta": "Chat: {chat_id} | call duration: {duration}",
    "security_summary_totals": "Totals:",
    "security_summary_caption": "🛡 Suspicious behaviour summary for this voice chat.",
    "security_on": "🛡 Call security enabled.",
    "security_off": "🛡 Call security disabled.",
    "security_age_set": "🥶 Required membership age set to **{days} days**.",
    "security_age_prompt": "Send the number of days (example: `Account age 7`).",
    # ── logging ──────────────────────────────────────────────────────────────
    "log_new_chat": "🆕 **New chat**\nTitle: {title}\nID: `{chat_id}`\nAdded by: {user}",
    "log_left_chat": "👋 **Left chat**\nTitle: {title}\nID: `{chat_id}`",
    "log_new_user": "🆕 **New user**\n{user} — `{user_id}`",
    "log_play": "▶️ **Play**\nChat: {title} (`{chat_id}`)\nItem: {track}\nUser: {user}",
}
