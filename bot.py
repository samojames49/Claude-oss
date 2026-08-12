from pyrogram import Client, filters, enums, idle
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ButtonStyle
from pyrogram.errors import SessionPasswordNeeded, MessageNotModified, RPCError, UserNotParticipant
import json, os, asyncio, subprocess, sys, time, threading, html, random, signal

import config
from db import JSONDatabase
from payments import PaymentError, get_gateway

config.require("BOT_TOKEN", "API_ID", "API_HASH", "ADMIN_ID")

user_temp_codes = {}
active_clients = {}
BOT_TOKEN = config.BOT_TOKEN
API_ID = config.API_ID
API_HASH = config.API_HASH
ADMIN_ID = config.ADMIN_ID
TAX_PERCENT = config.TAX_PERCENT
TAX_MIN_AMOUNT = config.TAX_MIN_AMOUNT
FORCE_CHANNELS = config.FORCE_CHANNELS
COIN_RATE = config.COIN_RATE
TOMAN_PER_COIN = config.TOMAN_PER_COIN
card_info = config.card_info
SESSIONS_DIR = config.SESSIONS_DIR
SELF_SCRIPT = config.SELF_SCRIPT

os.makedirs(SESSIONS_DIR, exist_ok=True)

bot = Client("bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

db = JSONDatabase(
    config.DATABASE_FILE,
    defaults={
        "coin_rate": COIN_RATE,
        "toman_per_coin": TOMAN_PER_COIN,
        "admin_id": ADMIN_ID,
        "tax_percent": TAX_PERCENT,
        "tax_min_amount": TAX_MIN_AMOUNT,
        "transfer_enabled": True,
    },
)
user_timers = {}
# اشیای Popen سلف هر کاربر؛ اجازه می‌دهد دقیقاً همان پروسه را ببندیم
selfbot_processes = {}

class UserTimer:
    def __init__(self, user_id, callback):
        self.user_id, self.callback, self.timer, self.is_running = user_id, callback, None, False
    
    def start(self):
        if self.is_running: 
            self.stop()
        self.is_running = True
        self.timer = threading.Timer(3600, self._on_timer)
        self.timer.start()
        db.set("timers", self.user_id, {"start_time": time.time(), "is_running": True})
    
    def stop(self):
        if self.timer: 
            self.timer.cancel()
        self.is_running = False
        db.delete("timers", self.user_id)
    
    def _on_timer(self):
        self.is_running = False
        db.delete("timers", self.user_id)
        self.callback(self.user_id)
FONTS = {
    '0': '𝟬',
    '1': '𝟭',
    '2': '𝟮',
    '3': '𝟯',
    '4': '𝟰',
    '5': '𝟱',
    '6': '𝟲',
    '7': '𝟳',
    '8': '𝟴',
    '9': '𝟵'
}

async def safe_edit(callback_query, text, reply_markup=None, parse_mode=None):
    """ویرایش پیام پنل بدون توجه به اینکه عکس‌دار است یا متنی.

    اگر پیام عکس داشته باشد، `edit_message_text` از سمت تلگرام خطا می‌دهد؛
    باید کپشن ویرایش شود.
    """
    message = callback_query.message
    try:
        if message.photo:
            await message.edit_caption(caption=text, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            await message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        return True
    except MessageNotModified:
        return True
    except RPCError as error:
        print(f"⚠️ ویرایش پیام ناموفق بود: {error}")
        return False


def font_convert(text):
    if text is None:
        return ""
    result = ""
    for char in str(text):
        if char.isdigit():
            result += FONTS.get(char, char)
        else:
            result += char
    return result

def create_colored_buttons(join_data, cancel_data):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ پیوستن به شرط",
                callback_data=join_data,
                style=ButtonStyle.SUCCESS  # سبز
            ),
            InlineKeyboardButton(
                "⛔ لغو شرط",
                callback_data=cancel_data,
                style=ButtonStyle.DANGER  # قرمز
            )
        ]
    ])

async def betting_info_handler(client, message):
    info_text = """
🎲 سیستم شرطبندی گروهی 1v1
📋 قوانین شرطبندی:
1️⃣ در گروه با نوشتن `شرطبندی 100` (یا هر مقدار دیگر) می‌توانید شرط ایجاد کنید
2️⃣ نفر دوم می‌تواند با کلیک روی دکمه «پیوستن به شرط» وارد شود
3️⃣ پس از پیوستن نفر دوم، ۵ ثانیه بعد برنده مشخص می‌شود
4️⃣ برنده تمام مبلغ شرط را دریافت می‌کند
5️⃣ اگر در ۵ دقیقه کسی شرکت نکند، شرط لغو و مبلغ بازگردانده می‌شود

💰 مثال:
- شما: `شرطبندی 500`
- حریف: پیوستن به شرط
- برنده: تمام 1000 سکه را می‌برد (500+500)

"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back")]
    ])
    
    await message.edit_text(info_text, reply_markup=keyboard)
def create_numpad_keyboard(prefix="code"):
    buttons = []
    
    row1 = [
        InlineKeyboardButton("1️⃣", callback_data=f"{prefix}_1"),
        InlineKeyboardButton("2️⃣", callback_data=f"{prefix}_2"),
        InlineKeyboardButton("3️⃣", callback_data=f"{prefix}_3")
    ]
    
    row2 = [
        InlineKeyboardButton("4️⃣", callback_data=f"{prefix}_4"),
        InlineKeyboardButton("5️⃣", callback_data=f"{prefix}_5"),
        InlineKeyboardButton("6️⃣", callback_data=f"{prefix}_6")
    ]
    
    row3 = [
        InlineKeyboardButton("7️⃣", callback_data=f"{prefix}_7"),
        InlineKeyboardButton("8️⃣", callback_data=f"{prefix}_8"),
        InlineKeyboardButton("9️⃣", callback_data=f"{prefix}_9")
    ]
    
    row4 = [
        InlineKeyboardButton("⌨️ پاک کن", callback_data=f"{prefix}_clear"),
        InlineKeyboardButton("0️⃣", callback_data=f"{prefix}_0"),
        InlineKeyboardButton("✅ ارسال", callback_data=f"{prefix}_send")
    ]
    
    row5 = [
        InlineKeyboardButton("🔙 انصراف", callback_data=f"{prefix}_cancel")
    ]
    
    buttons.append(row1)
    buttons.append(row2)
    buttons.append(row3)
    buttons.append(row4)
    buttons.append(row5)
    
    return InlineKeyboardMarkup(buttons)

def format_code_display(code):
    if not code:
        return "⚪.⚪.⚪.⚪.⚪"
    
    digits = list(code)
    while len(digits) < 5:
        digits.append("⚪")
    
    return ".".join(digits)
async def handle_code_from_keyboard(client, code_message):
    user_id = code_message.from_user.id
    code = code_message.text 

    code = code.replace(".", "")
    
    temp_data = db.get("temp_data", user_id)
    
    if not temp_data:
        await client.send_message(user_id, "❌ اطلاعات یافت نشد\nلطفا دوباره شماره تلفن را ارسال کنید")
        return
    
    try:
        if user_id in active_clients:
            user_client = active_clients[user_id]
        else:
            session_name = f"sessions/{user_id}"
            user_client = Client(session_name, api_id=API_ID, api_hash=API_HASH)
            await user_client.connect()
            active_clients[user_id] = user_client
        
        try: 
            await user_client.sign_in(temp_data["phone"], temp_data["phone_code_hash"], code)
        except SessionPasswordNeeded:
            await client.send_message(
                user_id,
                "🔒 **رمز دو مرحله‌ای نیاز است**\n\n"
                "لطفا رمز دو مرحله‌ای خود را به صورت متن ارسال کنید:"
            )
            db.set("temp_data", user_id, {**temp_data, "needs_password": True})
            return
        
        user_info = {
            "phone": temp_data["phone"],
            "status": "active", 
            "created_at": time.time(),
            "last_active": time.time(),
            "verified": db.get("users", user_id, {}).get("verified", False)
        }
        db.set("users", user_id, user_info)
        db.delete("temp_data", user_id)
        
        if user_id in active_clients:
            try:
                await active_clients[user_id].disconnect()
                del active_clients[user_id]
            except:
                pass

        if run_selfbot(user_id, temp_data["phone"]):
            credits = db.get("credits", user_id, 0)
            await client.send_message(
                user_id,
                f"✅ **سلف بات فعال شد!**\n\n"
                f"💰 سکه های شما: {credits}\n"
                f"⏰ زمان باقی‌مانده: {credits} ساعت"
            )
        else: 
            await client.send_message(user_id, "❌ خطا در اجرای سلف بات")
        
    except Exception as e: 
        error_msg = str(e)
        if "PHONE_CODE_EXPIRED" in error_msg:
            await client.send_message(
                user_id,
                "❌ **کد منقضی شده!**\n\n"
                "لطفا دوباره شماره تلفن خود را ارسال کنید."
            )
            db.delete("temp_data", user_id)
            if user_id in active_clients:
                try:
                    await active_clients[user_id].disconnect()
                    del active_clients[user_id]
                except:
                    pass
        else:
            await client.send_message(user_id, f"❌ **خطا:** {error_msg}")

async def cancel_group_bet_if_no_joiner(client, bet_key):
    await asyncio.sleep(300) 

    bet_data = db.get("group_bets", bet_key)
    if not bet_data or bet_data.get("finished"):
        return

    participants = bet_data.get("participants", [])
    chat_id = bet_data["chat_id"]
    message_id = bet_data["message_id"]
    amount = bet_data["amount"]
    creator_id = bet_data["creator_id"]
    creator_first_name = html.escape(bet_data.get('creator_name', 'کاربر'))
    creator_mention = f'<a href="tg://user?id={creator_id}"><b>{creator_first_name}</b></a>'
    
    if len(participants) > 0:
        return
    
    if bet_data.get("refunded"):
        return
    
    creator_credits = db.get("credits", creator_id, 0)
    db.set("credits", creator_id, creator_credits + amount)

    bet_data["finished"] = True
    bet_data["is_active"] = False
    bet_data["refunded"] = True
    db.set("group_bets", bet_key, bet_data)

    text = (
        "⛔ شرط به دلیل عدم شرکت‌کننده لغو شد.\n\n"
        f"👤 سازنده: {creator_mention}\n"
        f"💰 مبلغ شرط: <code>{amount}</code> سکه\n"
        "💸 مبلغ به سازنده برگشت داده شد."
    )
    
    try:
        await client.edit_message_text(chat_id, message_id, text, reply_markup=None, parse_mode=enums.ParseMode.HTML)
    except:
        pass

    try:
        await client.send_message(
            creator_id,
            f"⛔ **شرط شما لغو شد!**\n\n"
            f"به دلیل عدم شرکت‌کننده، شرط شما لغو شد.\n"
            f"💰 مبلغ شرط: <code>{amount}</code> سکه\n"
            f"💸 مبلغ به حساب شما برگشت داده شد.\n\n"
            f"📊 موجودی جدید شما: <code>{db.get('credits', creator_id, 0)}</code> سکه"
        )
    except:
        pass

async def finish_group_bet(client, bet_key):
    await asyncio.sleep(5)

    bet_data = db.get("group_bets", bet_key)
    if not bet_data or bet_data.get("finished"):
        return

    chat_id = bet_data["chat_id"]
    message_id = bet_data["message_id"]
    amount = bet_data["amount"]
    creator_id = bet_data["creator_id"]
    creator_first_name = html.escape(bet_data.get('creator_name', 'کاربر'))
    creator_mention = f'<a href="tg://user?id={creator_id}"><b>{creator_first_name}</b></a>'
    participants = bet_data.get("participants", [])
    
    if len(participants) == 0:
        if not bet_data.get("refunded"):
            creator_credits = db.get("credits", creator_id, 0)
            db.set("credits", creator_id, creator_credits + amount)
            bet_data["refunded"] = True

        bet_data["finished"] = True
        bet_data["is_active"] = False
        db.set("group_bets", bet_key, bet_data)

        text = (
            "⛔ <b>شرط به حد نصاب نرسید و لغو شد.</b>\n\n"
            f"💰 <b>مبلغ هر نفر:</b> <code>{amount}</code> سکه\n"
            f"👤 <b>سازنده:</b> {creator_mention}"
        )
        try:
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=None,
                parse_mode=enums.ParseMode.HTML
            )
        except:
            pass
        return
    
    players = [{"id": creator_id, "name": bet_data.get('creator_name', 'کاربر')}] + participants
    player_ids = [creator_id] + [p["id"] for p in participants]
    player_mentions = [creator_mention]
    for p in participants:
        p_name = html.escape(p.get('name', 'کاربر'))
        player_mentions.append(f'<a href="tg://user?id={p["id"]}"><b>{p_name}</b></a>')
    
    pot = (1 + len(participants)) * amount 

    winner_index = random.choice(range(len(players)))
    winner_id = player_ids[winner_index]
    winner_mention = player_mentions[winner_index]
    winner_credits = db.get("credits", winner_id, 0) + pot
    db.set("credits", winner_id, winner_credits)

    bet_data["finished"] = True
    bet_data["is_active"] = False
    bet_data["winner_id"] = winner_id
    bet_data["winner_name"] = players[winner_index].get("name", "کاربر")
    bet_data["pot"] = pot
    db.set("group_bets", bet_key, bet_data)

    players_list = []
    for mention in player_mentions:
        players_list.append(f"• {mention}")
    players_text = "\n".join(players_list)

    result_text = (
        "🎉 <b>نتیجه شرط 1v1</b>\n\n"
        f"💰 <b>مبلغ هر نفر:</b> <code>{amount}</code> سکه\n"
        f"👥 <b>تعداد بازیکنان:</b> <code>{len(players)}</code> نفر\n"
        f"📋 <b>فهرست بازیکنان:</b>\n{players_text}\n\n"
        f"🏆 <b>برنده:</b> {winner_mention}\n"
        f"💎 <b>جایزه:</b> <code>{pot}</code> سکه"
    )

    try:
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=result_text,
            reply_markup=None,
            parse_mode=enums.ParseMode.HTML
        )
    except:
        pass

    try:
        await client.send_message(
            chat_id,
            f"🏆 {winner_mention} برنده شرط <code>{amount}</code> سکه‌ای شد و <b>{pot}</b> سکه دریافت کرد!",
            parse_mode=enums.ParseMode.HTML
        )
    except:
        pass
    try:
        await client.send_message(
            winner_id,
            f"🎉 <b>تبریک! شما برنده شرط شدید!</b>\n\n"
            f"💰 <b>مبلغ شرط:</b> <code>{amount}</code> سکه\n"
            f"💎 <b>جایزه دریافتی:</b> <code>{pot}</code> سکه\n"
            f"👥 <b>تعداد بازیکنان:</b> {len(players)} نفر\n\n"
            f"📊 <b>موجودی جدید شما:</b> <code>{db.get('credits', winner_id, 0)}</code> سکه",
            parse_mode=enums.ParseMode.HTML
        )
    except:
        pass
    for player in players:
        if player["id"] != winner_id:
            try:
                await client.send_message(
                    player["id"],
                    f"😔 <b>متاسفانه شما در شرط باختید!</b>\n\n"
                    f"💰 <b>مبلغ شرط:</b> <code>{amount}</code> سکه\n"
                    f"👥 <b>تعداد بازیکنان:</b> {len(players)} نفر\n"
                    f"🏆 <b>برنده:</b> {winner_mention}\n\n"
                    f"📊 <b>موجودی فعلی شما:</b> <code>{db.get('credits', player['id'], 0)}</code> سکه",
                    parse_mode=enums.ParseMode.HTML
                )
            except:
                pass
JOINED_STATUSES = (
    enums.ChatMemberStatus.OWNER,
    enums.ChatMemberStatus.ADMINISTRATOR,
    enums.ChatMemberStatus.MEMBER,
    enums.ChatMemberStatus.RESTRICTED,
)


async def check_force_join(client, user_id):
    """بررسی عضویت در کانال‌های اجباری.

    نسخه قبلی فقط وضعیت kicked/banned را رد می‌کرد؛ یعنی کاربری که کانال را
    ترک کرده بود (LEFT) از فیلتر رد می‌شد. اینجا فقط وضعیت‌های واقعاً «عضو»
    پذیرفته می‌شوند.
    """
    if not FORCE_CHANNELS:
        return True, []

    not_joined = []
    for ch in FORCE_CHANNELS:
        try:
            member = await client.get_chat_member(ch, user_id)
            if member.status not in JOINED_STATUSES:
                not_joined.append(ch)
        except UserNotParticipant:
            not_joined.append(ch)
        except RPCError as error:
            print(f"⚠️ بررسی عضویت @{ch} ناموفق بود: {error}")
            not_joined.append(ch)

    if not_joined:
        return False, not_joined

    return True, []

BOT_LOOP = None  # حلقه رویداد اصلی؛ در on_startup مقدار می‌گیرد


def schedule_on_bot_loop(coro):
    """اجرای یک کوروتین از داخل ترد غیر-async (مثل تایمر شارژ).

    قبلاً `bot.send_message(...)` بدون await صدا زده می‌شد؛ یعنی کوروتین ساخته
    می‌شد ولی هیچ‌وقت اجرا نمی‌شد و کاربر پیام «سکه تمام شد» را نمی‌گرفت.
    """
    if BOT_LOOP is None or BOT_LOOP.is_closed():
        coro.close()
        return None
    try:
        return asyncio.run_coroutine_threadsafe(coro, BOT_LOOP)
    except RuntimeError as error:
        print(f"⚠️ ارسال پیام ممکن نشد: {error}")
        coro.close()
        return None


def notify_user(user_id, text):
    schedule_on_bot_loop(bot.send_message(user_id, text))


OUT_OF_CREDIT_TEXT = (
    "❌ **سکه های شما تمام شد!**\n\n"
    "سلف بات متوقف شد.\n\n"
    "💰 برای ادامه استفاده، از طریق منوی «افزایش موجودی» حساب خود را شارژ کنید."
)


def deduct_credit_callback(user_id):
    """کسر یک سکه به ازای هر ساعت اجرای سلف."""
    try:
        if not db.get("processes", user_id):
            return

        spent, remaining = db.spend_credits(user_id, 1)
        if not spent or remaining <= 0:
            stop_selfbot(user_id)
            notify_user(user_id, OUT_OF_CREDIT_TEXT)
            return

        if user_id in user_timers:
            user_timers[user_id].start()
    except Exception as e:
        print(f"❌ خطا در deduct_credit_callback: {e}")


def run_selfbot(user_id, phone=None):
    try:
        stop_selfbot(user_id)

        session_file = os.path.join(SESSIONS_DIR, f"{user_id}.session")
        if not os.path.exists(session_file):
            print(f"⚠️ فایل session کاربر {user_id} موجود نیست؛ اجرا لغو شد.")
            return False

        if phone:
            cmd = [sys.executable, SELF_SCRIPT, str(user_id), phone, str(API_ID), API_HASH]
        else:
            cmd = [sys.executable, SELF_SCRIPT, str(user_id)]

        process = subprocess.Popen(cmd)
        pid = process.pid
        selfbot_processes[user_id] = process
        db.set("processes", user_id, pid)

        user_data = db.get("users", user_id, {}) or {}
        user_data["status"] = "active"
        user_data["last_active"] = time.time()
        user_data["started_at"] = time.time()
        if phone:
            user_data["phone"] = phone
        db.set("users", user_id, user_data)

        print(f"✅ سلف‌بات برای کاربر {user_id} راه‌اندازی شد")
        print(f"   📱 شماره: {phone}")
        print(f"   🆔 PID: {pid}")
        print(f"   💰 سکه: {db.get_credits(user_id)}")
        print("-" * 50)

        if user_id not in user_timers:
            user_timers[user_id] = UserTimer(user_id, deduct_credit_callback)
        user_timers[user_id].start()

        return True
    except Exception as e:
        print(f"❌ خطا در اجرای سلف‌بات: {e}")
        return False


def _terminate_pid(pid):
    """پایان دادن به یک پروسه مشخص با PID.

    نکته مهم: نسخه قبلی در انتها `pkill -f "self.py"` اجرا می‌کرد که سلف **همه**
    مشتری‌ها را می‌کشت. اینجا فقط همان PID هدف قرار می‌گیرد.
    """
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return True
    except PermissionError:
        print(f"⚠️ اجازه پایان دادن به پروسه {pid} وجود ندارد")
        return False
    except OSError as error:
        print(f"⚠️ خطا در ارسال SIGTERM به {pid}: {error}")

    for _ in range(20):  # حداکثر ۲ ثانیه فرصت خروج تمیز
        time.sleep(0.1)
        try:
            os.kill(pid, 0)
        except OSError:
            return True

    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        pass
    return True


def stop_selfbot(user_id):
    try:
        if user_id in user_timers:
            user_timers[user_id].stop()

        process = selfbot_processes.pop(user_id, None)
        pid = db.get("processes", user_id)

        if process is not None and process.poll() is None:
            _terminate_pid(process.pid)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
        elif pid:
            _terminate_pid(pid)

        if process is None and not pid:
            return False

        db.delete("processes", user_id)
        user_data = db.get("users", user_id, {}) or {}
        if user_data:
            user_data["status"] = "inactive"
            user_data["stopped_at"] = time.time()
            db.set("users", user_id, user_data)

        legacy_pid_file = f"process_{user_id}.pid"
        if os.path.exists(legacy_pid_file):
            try:
                os.remove(legacy_pid_file)
            except OSError:
                pass

        print(f"✅ سلف‌بات کاربر {user_id} قطع شد (PID: {pid})")
        return True
    except Exception as e:
        print(f"❌ خطا در stop_selfbot: {e}")
        return False


def check_selfbot_status(user_id):
    """آیا پروسه سلف این کاربر واقعاً زنده است؟"""
    pid = db.get("processes", user_id)
    if not pid:
        return False

    process = selfbot_processes.get(user_id)
    if process is not None and process.poll() is not None:
        alive = False
    else:
        try:
            os.kill(pid, 0)
            alive = True
        except OSError:
            alive = False

    if not alive:
        selfbot_processes.pop(user_id, None)
        db.delete("processes", user_id)
        user_data = db.get("users", user_id, {}) or {}
        if user_data:
            user_data["status"] = "inactive"
            db.set("users", user_id, user_data)
    return alive


def stop_all_selfbots():
    try:
        for timer in list(user_timers.values()):
            timer.stop()
        user_timers.clear()

        for user_id_str, pid in list(db.get_all("processes").items()):
            try:
                _terminate_pid(int(pid))
            except (TypeError, ValueError):
                continue
            user_data = db.get("users", user_id_str, {}) or {}
            if user_data:
                user_data["status"] = "inactive"
                db.set("users", user_id_str, user_data)

        selfbot_processes.clear()
        with db.atomic() as data:
            data["processes"] = {}
            data["timers"] = {}
        print("✅ همه سلف‌بات‌ها متوقف شدند")
    except Exception as e:
        print(f"❌ خطا در stop_all_selfbots: {e}")


def restore_running_selfbots():
    """بازیابی وضعیت پس از ری‌استارت ربات مدیریت.

    نسخه قبلی بعد از ری‌استارت، هم PIDهای مرده را «فعال» نشان می‌داد و هم
    تایمر شارژ ساعتی را از دست می‌داد (یعنی سلف بدون کسر سکه اجرا می‌شد).
    """
    revived, cleaned = 0, 0
    for user_id_str in list(db.get_all("processes").keys()):
        try:
            user_id = int(user_id_str)
        except (TypeError, ValueError):
            db.delete("processes", user_id_str)
            continue

        if check_selfbot_status(user_id):
            if user_id not in user_timers:
                user_timers[user_id] = UserTimer(user_id, deduct_credit_callback)
            user_timers[user_id].start()
            revived += 1
            continue

        cleaned += 1
        if config.AUTO_RESTART_ENABLED and db.get_credits(user_id) > 0:
            phone = (db.get("users", user_id, {}) or {}).get("phone")
            if run_selfbot(user_id, phone):
                print(f"♻️ سلف کاربر {user_id} پس از ری‌استارت مجدداً اجرا شد")

    if revived or cleaned:
        print(f"📋 بازیابی وضعیت: {revived} سلف فعال، {cleaned} رکورد مرده پاک‌سازی شد")


async def health_monitor_loop():
    """گزارش سلامت ساعتی به ادمین + اجرای خودکار سلف‌های افتاده.

    این همان قابلیت «گزارش ساعتی و روشن‌شدن خودکار سلف‌ها» است که سرویس‌های
    حرفه‌ای مثل Self VTR دارند.
    """
    interval = max(60, config.HEALTH_REPORT_INTERVAL)
    while True:
        try:
            await asyncio.sleep(interval)
            await run_health_check(send_report=True)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"❌ خطا در health_monitor_loop: {e}")


async def run_health_check(send_report=False):
    """بررسی همه سلف‌ها؛ افتاده‌ها را (در صورت داشتن سکه) دوباره اجرا می‌کند."""
    processes = db.get_all("processes")
    users = db.get_all("users")

    alive, restarted, stopped = 0, 0, 0
    for user_id_str in list(users.keys()):
        try:
            user_id = int(user_id_str)
        except (TypeError, ValueError):
            continue

        user_data = users.get(user_id_str, {}) or {}
        if user_data.get("status") != "active" and user_id_str not in processes:
            continue

        if check_selfbot_status(user_id):
            alive += 1
            continue

        if config.AUTO_RESTART_ENABLED and db.get_credits(user_id) > 0:
            phone = user_data.get("phone")
            if run_selfbot(user_id, phone):
                restarted += 1
        else:
            stop_selfbot(user_id)
            stopped += 1

    if send_report and ADMIN_ID:
        total_users = len(users)
        active_now = len(db.get_all("processes"))
        report = (
            "📊 <b>گزارش ساعتی سلف‌ها</b>\n\n"
            f"👥 کل کاربران: <b>{total_users}</b>\n"
            f"🟢 سلف‌های فعال: <b>{active_now}</b>\n"
            f"✅ سالم: <b>{alive}</b>\n"
            f"♻️ اجرای مجدد: <b>{restarted}</b>\n"
            f"🛑 متوقف‌شده: <b>{stopped}</b>"
        )
        try:
            await bot.send_message(ADMIN_ID, report)
        except Exception as e:
            print(f"⚠️ ارسال گزارش سلامت ناموفق بود: {e}")

    return {"alive": alive, "restarted": restarted, "stopped": stopped}


@bot.on_message(filters.group & filters.regex(r'^موجودی$'))
async def group_balance_handler(client, message: Message):
    user_id = message.from_user.id
    user_first_name = html.escape(message.from_user.first_name or "کاربر")
    user_mention = f'<a href="tg://user?id={user_id}"><b>{user_first_name}</b></a>'
    
    ok, not_joined = await check_force_join(client, user_id)
    if not ok:
        buttons = []
        for ch in FORCE_CHANNELS:
            buttons.append([InlineKeyboardButton(f"● عضویت در @{ch}", url=f"https://t.me/{ch}")])
        buttons.append([InlineKeyboardButton("● بررسی مجدد", callback_data="check_join")])
        
        await message.reply_text(
            "● <b>برای مشاهده موجودی باید در کانال‌های زیر عضو باشید:</b>\n\n" +
            "\n".join([f"• @{channel}" for channel in FORCE_CHANNELS]),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    credits = db.get("credits", user_id, 0)
    user_data = db.get("users", user_id, {})
    phone = user_data.get('phone', 'ثبت نشده')
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"{font_convert(credits)}", 
            callback_data="my_balance"
        )]
    ])
    
    balance_text = f"""
<b>● اطلاعات کاربر●</b>

<b>● آیدی عددی:</b> <code>{font_convert(user_id)}</code>
<b>● نام:</b> {user_mention}
"""
    
    await message.reply_text(
        balance_text,
        reply_markup=keyboard,
        parse_mode=enums.ParseMode.HTML
    )

@bot.on_message(filters.command("set") & filters.user(ADMIN_ID))
async def set_credits(client, message: Message):
    if len(message.command) != 3:
        await message.reply_text("❌ فرمت: `/set آیدی تعداد`")
        return    
    try:
        target_id = int(message.command[1])
        amount = int(message.command[2])
        db.set("credits", target_id, amount)
        
        await message.reply_text(f"✅ سکه کاربر {target_id} تنظیم شد به {amount}")       
        try:
            await bot.send_message(target_id, f"🔧 موجودی سکه شما تنظیم شد\n💰 جدید: {amount} سکه")
        except: 
            pass        
    except: 
        await message.reply_text("❌ آیدی/تعداد باید عدد باشد")
@bot.on_message(filters.group & filters.regex(r'^شرطبندی\s+(\d+)(?:\s*سکه)?$'))
async def group_bet_handler(client, message: Message):
    chat_id = message.chat.id
    creator_id = message.from_user.id
    try:
        amount = int(message.matches[0].group(1))
    except:
        return
    if amount <= 0:
        await message.reply_text("❌ مقدار شرط باید بیشتر از صفر باشد.")
        return    
    # چک و کسر اتمیک تا با ساخت هم‌زمان چند شرط، موجودی منفی نشود
    spent, creator_credits = db.spend_credits(creator_id, amount)
    if not spent:
        await message.reply_text(
            f"❌ سکه کافی برای ساخت شرط ندارید.\n"
            f"💰 موجودی شما: {creator_credits} سکه"
        )
        return

    creator_first_name = html.escape(message.from_user.first_name or 'کاربر')
    creator_mention = f'<a href="tg://user?id={creator_id}"><b>{creator_first_name}</b></a>'

    bet_text = (
        "🎲 <b>شرطبندی درحال اجرا ...</b>\n\n"
        f"💰 <b>مبلغ هر نفر:</b> <code>{amount}</code> سکه\n"
        f"👤 <b>سازنده:</b> {creator_mention}\n\n"
        "برای شرکت در این شرط روی دکمه «پیوستن به شرط» بزنید.\n"
        "⛔ اگر تا ۵ دقیقه کسی شرکت نکند، شرط لغو و مبلغ به سازنده برمی‌گردد.\n"
        "⏳ پس از پیوستن نفر دوم، ۵ ثانیه بعد برنده مشخص می‌شود."
    )
    keyboard = create_colored_buttons(
        f"joinbet_{chat_id}_waiting",
        f"cancelbet_{chat_id}_waiting"
    )
    sent_msg = await message.reply_text(
        bet_text,
        reply_markup=keyboard,
        parse_mode=enums.ParseMode.HTML
    )
    
    msg_id = sent_msg.id
    bet_key = f"{chat_id}_{msg_id}"
    
    new_keyboard = create_colored_buttons(
        f"joinbet_{chat_id}_{msg_id}",
        f"cancelbet_{chat_id}_{msg_id}"
    )
    
    await sent_msg.edit_reply_markup(
        reply_markup=new_keyboard
    )

    bet_data = {
        "chat_id": chat_id,
        "message_id": msg_id,
        "amount": amount,
        "creator_id": creator_id,
        "creator_name": message.from_user.first_name or "",
        "creator_username": message.from_user.username or "",
        "participants": [],
        "is_active": True,
        "finished": False,
        "timer_started": False,
        "created_at": time.time(),
        "refunded": False
    }

    db.set("group_bets", bet_key, bet_data)
    asyncio.create_task(cancel_group_bet_if_no_joiner(client, bet_key))
@bot.on_message(filters.group & filters.regex(r'^انتقال\s+(\d+)\s*(?:سکه)?\s*$'))
async def transfer_coins_handler(client, message: Message):
    user_id = message.from_user.id

    if not db.get_transfer_status():
        await message.reply_text("⛔ سیستم انتقال سکه در حال حاضر غیرفعال است.")
        return

    ok, not_joined = await check_force_join(client, user_id)
    if not ok:
        buttons = []
        for ch in FORCE_CHANNELS:
            buttons.append([InlineKeyboardButton(f"📢 عضویت در @{ch}", url=f"https://t.me/{ch}")])
        buttons.append([InlineKeyboardButton("🔁 بررسی مجدد", callback_data="check_join")])
        
        await message.reply_text(
            "⚠️ **برای انتقال سکه باید در کانال‌های زیر عضو باشید:**\n\n" +
            "\n".join([f"• @{channel}" for channel in FORCE_CHANNELS]),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return
    
    if not message.reply_to_message:
        await message.reply_text(
            "❌ **فرمت اشتباه!**\n\n"
            "برای انتقال سکه به یک پیام ریپلای کنید:\n"
            "<b>انتقال 10</b>"
        )
        return
    
    try:
        amount = int(message.matches[0].group(1))
    except:
        await message.reply_text("❌ مقدار باید عدد باشد")
        return
    
    if amount <= 0:
        await message.reply_text("❌ مقدار انتقال باید بیشتر از صفر باشد")
        return

    settings = db.data.get("settings", {})
    tax_percent = settings.get("tax_percent", 10)
    tax_min_amount = settings.get("tax_min_amount", 10)
    
    tax_amount = 0
    if amount >= tax_min_amount:
        tax_amount = int(amount * tax_percent / 100)
        if tax_amount < 1:
            tax_amount = 1
    
    final_amount = amount - tax_amount
    
    sender_id = message.from_user.id
    sender_credits = db.get("credits", sender_id, 0)
    
    if sender_credits < amount:
        await message.reply_text(
            f"❌ **سکه کافی ندارید!**\n\n"
            f"💰 موجودی شما: <code>{sender_credits}</code> سکه\n"
            f"💸 نیاز دارید: <code>{amount}</code> سکه\n\n"
            f"📊 <b>جزئیات انتقال:</b>\n"
            f"├─ مبلغ اصلی: <code>{amount}</code> سکه\n"
            f"├─ مالیات ({tax_percent}%): <code>{tax_amount}</code> سکه\n"
            f"└─ مبلغ دریافتی گیرنده: <code>{final_amount}</code> سکه"
        )
        return
    
    receiver = message.reply_to_message.from_user
    receiver_id = receiver.id
    
    if sender_id == receiver_id:
        await message.reply_text("❌ نمی‌توانید به خودتان سکه انتقال دهید!")
        return
    
    if receiver.is_bot:
        await message.reply_text("❌ نمی‌توانید به ربات سکه انتقال دهید!")
        return

    db.set("credits", sender_id, sender_credits - amount)
    receiver_credits = db.get("credits", receiver_id, 0)
    db.set("credits", receiver_id, receiver_credits + final_amount)
    
    if tax_amount > 0:
        admin_credits = db.get("credits", ADMIN_ID, 0)
        db.set("credits", ADMIN_ID, admin_credits + tax_amount)
        
    sender_name = html.escape(message.from_user.first_name or "کاربر")
    receiver_name = html.escape(receiver.first_name or "کاربر")
    sender_mention = f'<a href="tg://user?id={sender_id}"><b>{sender_name}</b></a>'
    receiver_mention = f'<a href="tg://user?id={receiver_id}"><b>{receiver_name}</b></a>'

    await message.reply_text(
        f"✔️ <b>انتقال سکه انجام شد!</b>\n\n"
        f"● <b>فرستنده:</b> {sender_mention}\n"
        f"● <b>گیرنده:</b> {receiver_mention}\n"
        f"● <b>مبلغ اصلی:</b> <code>{amount}</code> سکه\n"
        f"● <b>مالیات ({tax_percent}%):</b> <code>{tax_amount}</code> سکه\n"
        f"● <b>مبلغ دریافتی گیرنده:</b> <code>{final_amount}</code> سکه\n\n"
        f"● <b>موجودی {sender_name}:</b> <code>{db.get('credits', sender_id, 0)}</code> سکه\n"
        f"● <b>موجودی {receiver_name}:</b> <code>{db.get('credits', receiver_id, 0)}</code> سکه",
        parse_mode=enums.ParseMode.HTML
    )
    
    try:
        await client.send_message(
            sender_id,
            f"● <b>انتقال سکه انجام شد!</b>\n\n"
            f"● <b>گیرنده:</b> {receiver_mention}\n"
            f"● <b>مبلغ اصلی:</b> <code>{amount}</code> سکه\n"
            f"● <b>مالیات ({tax_percent}%):</b> <code>{tax_amount}</code> سکه\n"
            f"● <b>مبلغ دریافتی گیرنده:</b> <code>{final_amount}</code> سکه\n\n"
            f"● <b>موجودی جدید شما:</b> <code>{db.get('credits', sender_id, 0)}</code> سکه",
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        print(f"❌ خطا در ارسال پیام به فرستنده: {e}")
      
    try:
        await client.send_message(
            receiver_id,
            f"● <b>سکه دریافت کردید!</b>\n\n"
            f"● <b>از طرف:</b> {sender_mention}\n"
            f"● <b>مبلغ اصلی:</b> <code>{amount}</code> سکه\n"
            f"● <b>مالیات کسر شده:</b> <code>{tax_amount}</code> سکه\n"
            f"● <b>مبلغ دریافتی:</b> <code>{final_amount}</code> سکه\n\n"
            f"● <b>موجودی جدید شما:</b> <code>{db.get('credits', receiver_id, 0)}</code> سکه",
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        print(f"❌ خطا در ارسال پیام به گیرنده: {e}")
@bot.on_message(filters.command("user") & filters.user(ADMIN_ID))
async def user_info(client, message: Message):
    if len(message.command) != 2:
        await message.reply_text("❌ فرمت: `/user آیدی`")
        return
    
    try:
        target_id = int(message.command[1])
        user_data = db.get("users", target_id, {})
        credits = db.get("credits", target_id, 0)
        process = db.get("processes", target_id)
        timer = db.get("timers", target_id)
        
        if not user_data:
            await message.reply_text("❌ کاربر یافت نشد")
            return
        
        status = "🟢 فعال" if user_data.get('status') == 'active' else "🔴 غیرفعال"
        phone = user_data.get('phone', '❌ ثبت نشده')
        created = time.ctime(user_data.get('created_at', time.time()))
        running = "🟢 بله" if process else "🔴 خیر"
        has_timer = "🟢 فعال" if timer and timer.get('is_running') else "🔴 غیرفعال"
        verified_status = "✅ تایید شده" if user_data.get('verified') else "❌ تایید نشده"
        rejected_status = "❌ رد شده" if user_data.get('rejected') else "✅ فعال"
        
        created_time = user_data.get('created_at', time.time())
        time_diff = time.time() - created_time
        days = int(time_diff // 86400)
        hours = int((time_diff % 86400) // 3600)
        
        info_text = f"""
👤 **اطلاعات کاربر {target_id}**

📱 **شماره:** `{phone}`
📊 **وضعیت:** {status}
🔐 **احراز هویت:** {verified_status}
🚫 **وضعیت رد:** {rejected_status}
💰 **سکه ها:** `{credits}`
🔄 **سلف:** {running}
📅 **تاریخ ایجاد:** `{created}`
⏳ **عضو شده:** {days} روز و {hours} ساعت

⏱ **زمان باقی‌مانده:** `{credits}` ساعت
💸 **مصرف سکه:** 1 سکه در ساعت
"""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎯 تنظیم سکه", callback_data=f"set_{target_id}"),
             InlineKeyboardButton("🛑 توقف سلف", callback_data=f"stop_{target_id}")],
            [InlineKeyboardButton("✅ تایید احراز", callback_data=f"verify_approve_{target_id}"),
             InlineKeyboardButton("❌ رد احراز", callback_data=f"verify_reject_{target_id}")]
        ])
        
        await message.reply_text(info_text, reply_markup=keyboard)
        
    except: 
        await message.reply_text("❌ آیدی باید عدد باشد")

@bot.on_message(filters.command("admin") & filters.user(ADMIN_ID))
async def admin_panel(client, message: Message):
    # هر بار باز شدن پنل، حالت‌های در انتظار ادمین پاک می‌شود تا پیام بعدی
    # به‌اشتباه به‌عنوان پیام همگانی یا تنظیم سکه تفسیر نشود.
    db.delete("temp_data", f"admin_broadcast_{ADMIN_ID}")
    db.delete("temp_data", f"admin_set_{ADMIN_ID}")

    users = db.data.get("users", {})
    active_count = len(db.data.get("processes", {}))
    total_credits = sum(db.data.get("credits", {}).values())
    verified_users = len(db.get_verified_users())
    pending_verifications = len(db.get_pending_verifications())
    pending_payments = len(db.get_pending_payments())
    
    today = time.time() - 86400
    new_today = sum(1 for user_data in users.values() if user_data.get('created_at', 0) > today)
    
    transfer_status = db.get_transfer_status()
    transfer_text = "🟢 روشن" if transfer_status else "🔴 خاموش"
    
    stats_text = f"""
🛠 **پنل مدیریت ادمین**

👥 **کل کاربران:** `{len(users)}`
🟢 **کاربران فعال:** `{active_count}`
✅ **کاربران تایید شده:** `{verified_users}`
🆕 **کاربران امروز:** `{new_today}`
💰 **مجموع سکه ها:** `{total_credits}`

📋 **درخواست‌های در انتظار:**
├─ 🔐 احراز هویت: `{pending_verifications}`
└─ 💰 پرداخت: `{pending_payments}`

🔄 **وضعیت انتقال سکه:** {transfer_text}

**📋 دستورات سریع:**
`/set آیدی تعداد` - تنظیم سکه
`/user آیدی` - اطلاعات کاربر
`/admin` - این پنل
"""
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👥 لیست کاربران", callback_data="admin_list", style=ButtonStyle.PRIMARY),
            InlineKeyboardButton("📊 آمار کامل", callback_data="admin_stats", style=ButtonStyle.PRIMARY)
        ],
        [
            InlineKeyboardButton("💰 برترین کاربران", callback_data="admin_top", style=ButtonStyle.SUCCESS),
            InlineKeyboardButton("🛑 توقف همه", callback_data="admin_stop_all", style=ButtonStyle.DANGER)
        ],
        [
            InlineKeyboardButton("🔐 درخواست احراز", callback_data="admin_verifications", style=ButtonStyle.PRIMARY),
            InlineKeyboardButton("💳 درخواست پرداخت", callback_data="admin_payments", style=ButtonStyle.PRIMARY)
        ],
        [
            InlineKeyboardButton("🔄 روشن کردن انتقال", callback_data="admin_transfer_on", style=ButtonStyle.SUCCESS),
            InlineKeyboardButton("⛔ خاموش کردن انتقال", callback_data="admin_transfer_off", style=ButtonStyle.DANGER)
        ],
        [
            InlineKeyboardButton("📸 تنظیم عکس خوش‌آمدگویی", callback_data="admin_set_photo", style=ButtonStyle.PRIMARY)
        ],
        [
            InlineKeyboardButton("📢 پیام همگانی", callback_data="admin_broadcast", style=ButtonStyle.PRIMARY),
            InlineKeyboardButton("♻️ بررسی سلامت سلف‌ها", callback_data="admin_health", style=ButtonStyle.SUCCESS)
        ]
    ])
    
    await message.reply_text(stats_text, reply_markup=keyboard)
@bot.on_callback_query(filters.regex(r'^code_'))
async def numpad_callback(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data
    current_code = user_temp_codes.get(user_id, "")
    
    if data == "code_clear":
        user_temp_codes[user_id] = current_code[:-1]
        display_code = user_temp_codes[user_id]

        formatted = format_code_display(display_code)
        
        try:
            await callback_query.message.edit_text(
                f"🔢 **کد تایید را وارد کنید:**\n\n"
                f"<b><code>{formatted}</code></b>\n\n"
                f"📱 کد {len(display_code)}/5 رقم وارد شد",
                reply_markup=create_numpad_keyboard(),
                parse_mode=enums.ParseMode.HTML
            )
        except Exception as e:
            print(f"❌ خطا در ویرایش پیام: {e}")
        
        await callback_query.answer()
        
    elif data == "code_send":
        if len(current_code) == 5:
            await callback_query.answer("✅ کد ارسال شد...", show_alert=True)
            class FakeMessage:
                def __init__(self, user_id, code):
                    self.from_user = type('obj', (object,), {'id': user_id})()
                    self.text = code
                    self.chat = type('obj', (object,), {'id': user_id})()
                    self.reply_text = None
                    
                async def reply_text(self, text, *args, **kwargs):
                    await client.send_message(user_id, text, *args, **kwargs)
            
            fake_msg = FakeMessage(user_id, current_code)

            await handle_code_from_keyboard(client, fake_msg)
            
            user_temp_codes.pop(user_id, None)
        else:
            await callback_query.answer(f"❌ کد باید 5 رقم باشد (الان {len(current_code)} رقم)", show_alert=True)
            
    elif data == "code_cancel":
        user_temp_codes.pop(user_id, None)
        try:
            await callback_query.message.edit_text(
                "❌ **ورود کد لغو شد**\n\n"
                "برای شروع مجدد از /start استفاده کنید",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="back")]
                ])
            )
        except Exception as e:
            print(f"❌ خطا در ویرایش پیام: {e}")
        
        await callback_query.answer()
        
    else:
        number = data.split("_")[1]
        
        if len(current_code) < 5:
            new_code = current_code + number
            user_temp_codes[user_id] = new_code
            formatted = format_code_display(new_code)
            
            try:
                await callback_query.message.edit_text(
                    f"🔢 **کد تایید را وارد کنید:**\n\n"
                    f"<b><code>{formatted}</code></b>\n\n"
                    f"📱 کد {len(new_code)}/5 رقم وارد شد",
                    reply_markup=create_numpad_keyboard(),
                    parse_mode=enums.ParseMode.HTML
                )
            except Exception as e:
                print(f"❌ خطا در ویرایش پیام: {e}")
            
            await callback_query.answer()
        else:
            await callback_query.answer("❌ کد کامل شده است! روی 'ارسال' کلیک کنید", show_alert=True)

async def admin_callback_handler(client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    if data == "admin_panel":
        if user_id != ADMIN_ID:
            await callback_query.answer("❌ دسترسی غیرمجاز!", show_alert=True)
            return

        await admin_panel(client, callback_query.message)
        await callback_query.answer()
        return
    if data == "admin_transfer_on":
        if user_id != ADMIN_ID:
            await callback_query.answer("❌ دسترسی غیرمجاز!", show_alert=True)
            return
        db.set_transfer_status(True)
        await callback_query.message.edit_text("✅ سیستم انتقال سکه روشن شد.")
        await callback_query.answer()
        return
    
    if data == "admin_transfer_off":
        if user_id != ADMIN_ID:
            await callback_query.answer("❌ دسترسی غیرمجاز!", show_alert=True)
            return
        db.set_transfer_status(False)
        await callback_query.message.edit_text("⛔ سیستم انتقال سکه خاموش شد.")
        await callback_query.answer()
        return
    
    if data == "admin_list":
        users = db.get_all("users")
        if not users:
            await callback_query.message.edit_text("❌ هیچ کاربری ثبت نشده است.")
            return
        
        text = "👥 **لیست کاربران:**\n\n"
        for i, (uid, info) in enumerate(list(users.items())[:20], 1):
            credits = db.get("credits", int(uid), 0)
            status = "🟢" if info.get('status') == 'active' else "🔴"
            verified = "✅" if info.get('verified') else "❌"
            text += f"{i}. {status} {verified} `{uid}` → {credits} سکه\n"
        
        if len(users) > 20:
            text += f"\n... و {len(users) - 20} کاربر دیگر"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")]
        ])
        await callback_query.message.edit_text(text, reply_markup=keyboard)
        await callback_query.answer()
    elif data == "admin_set_photo":
        if user_id != ADMIN_ID:
            await callback_query.answer("❌ دسترسی غیرمجاز!", show_alert=True)
            return
    
        current_photo = db.get_welcome_photo()
        status_text = "✅ تنظیم شده" if current_photo else "❌ تنظیم نشده"
    
        text = (
            f"📸 **تنظیم عکس خوش‌آمدگویی**\n\n"
            f"📊 **وضعیت فعلی:** {status_text}\n\n"
            f"🔹 برای تنظیم عکس جدید، عکس را ارسال کنید.\n"
            f"🔹 برای حذف عکس فعلی، روی دکمه حذف کلیک کنید.\n\n"
            f"⚠️ عکس باید با کیفیت مناسب باشد.\n"
            f"📱 عکس در صفحه شروع و تمام بخش‌ها نمایش داده می‌شود."
        )
    
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 ارسال عکس جدید", callback_data="admin_send_photo", style=ButtonStyle.SUCCESS)],
            [InlineKeyboardButton("🗑️ حذف عکس فعلی", callback_data="admin_delete_photo", style=ButtonStyle.DANGER)],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back", style=ButtonStyle.DANGER)]
        ])
    
        await callback_query.message.edit_text(text, reply_markup=keyboard)
        await callback_query.answer()

    elif data == "admin_send_photo":
        if user_id != ADMIN_ID:
            await callback_query.answer("❌ دسترسی غیرمجاز!", show_alert=True)
            return
    
        text = (
        "📸 **لطفا عکس مورد نظر را ارسال کنید**\n\n"
        "🔹 عکس را به صورت مستقیم در این چت ارسال کنید.\n"
        "🔹 پس از ارسال، به‌طور خودکار ذخیره می‌شود.\n"
        "🔹 در تمام بخش‌های ربات نمایش داده می‌شود."
        )
    
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_set_photo", style=ButtonStyle.DANGER)]
        ])
    
        await callback_query.message.edit_text(text, reply_markup=keyboard)
        db.set("temp_data", f"admin_waiting_photo_{user_id}", True)
        await callback_query.answer()

    elif data == "admin_delete_photo":
        if user_id != ADMIN_ID:
            await callback_query.answer("❌ دسترسی غیرمجاز!", show_alert=True)
            return
    
        current_photo = db.get_welcome_photo()
        if current_photo:
            db.delete_welcome_photo()
            text = "✅ **عکس خوش‌آمدگویی با موفقیت حذف شد!**\n\n🔄 ربات به حالت عادی (بدون عکس) بازگشت."
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به تنظیمات", callback_data="admin_set_photo", style=ButtonStyle.PRIMARY)]
            ])
            await callback_query.message.edit_text(text, reply_markup=keyboard)
        else:
            await callback_query.answer("❌ هیچ عکسی تنظیم نشده است!", show_alert=True)
        await callback_query.answer()    
    elif data == "admin_stats":
        users = db.get_all("users")
        processes = db.get_all("processes")
        credits = db.get_all("credits")
        verifications = db.get_all("verifications")
        payments = db.get_all("payments")
        
        total_users = len(users)
        active_users = len(processes)
        total_credits = sum(credits.values()) if credits else 0
        pending_verif = sum(1 for v in verifications.values() if v.get('status') == 'pending')
        pending_pay = sum(1 for p in payments.values() if p.get('status') == 'pending')
        verified_users = sum(1 for u in users.values() if u.get('verified'))
        rejected_users = sum(1 for u in users.values() if u.get('rejected'))
        
        text = f"""
📊 **آمار کامل سیستم**

👥 **کاربران کل:** {total_users}
🟢 **فعال:** {active_users}
✅ **تایید شده:** {verified_users}
❌ **رد شده:** {rejected_users}

💰 **مجموع سکه‌ها:** {total_credits:,}

🔐 **درخواست احراز:** {pending_verif}
💳 **درخواست پرداخت:** {pending_pay}

📅 **تاریخ:** {time.ctime()}
"""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")]
        ])
        await callback_query.message.edit_text(text, reply_markup=keyboard)
        await callback_query.answer()
    
    elif data == "admin_top":
        credits = db.get_all("credits")
        if not credits:
            await callback_query.message.edit_text("❌ هیچ کاربری سکه ندارد.")
            return
        
        sorted_users = sorted(credits.items(), key=lambda x: x[1], reverse=True)[:10]
        text = "🏆 **برترین کاربران از نظر سکه:**\n\n"
        for i, (uid, amount) in enumerate(sorted_users, 1):
            user_data = db.get("users", int(uid), {})
            name = user_data.get('first_name', 'ناشناس')
            text += f"{i}. {name} → `{amount:,}` سکه\n"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")]
        ])
        await callback_query.message.edit_text(text, reply_markup=keyboard)
        await callback_query.answer()
    
    elif data == "admin_stop_all":
        await callback_query.message.edit_text("🛑 **در حال توقف همه سلف‌بات‌ها...**")
        stop_all_selfbots()
        await asyncio.sleep(1)
        await callback_query.message.edit_text("✅ **همه سلف‌بات‌ها متوقف شدند.**")
        await callback_query.answer()
    
    elif data == "admin_verifications":
        verifications = db.get_pending_verifications()
        if not verifications:
            await callback_query.message.edit_text("❌ هیچ درخواست احراز در انتظاری وجود ندارد.")
            return
        
        text = "🔐 **درخواست‌های احراز هویت:**\n\n"
        for uid, info in list(verifications.items())[:10]:
            name = info.get('first_name', 'ناشناس')
            text += f"👤 {name} → `{uid}`\n"
        
        if len(verifications) > 10:
            text += f"\n... و {len(verifications) - 10} درخواست دیگر"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")]
        ])
        await callback_query.message.edit_text(text, reply_markup=keyboard)
        await callback_query.answer()
    
    elif data == "admin_payments":
        payments = db.get_pending_payments()
        if not payments:
            await callback_query.message.edit_text("❌ هیچ درخواست پرداخت در انتظاری وجود ندارد.")
            return
        
        text = "💳 **درخواست‌های پرداخت:**\n\n"
        for uid, info in list(payments.items())[:10]:
            name = info.get('first_name', 'ناشناس')
            coins = info.get('coins', 0)
            text += f"👤 {name} → `{uid}` | {coins} سکه\n"
        
        if len(payments) > 10:
            text += f"\n... و {len(payments) - 10} درخواست دیگر"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")]
        ])
        await callback_query.message.edit_text(text, reply_markup=keyboard)
        await callback_query.answer()
    
    elif data == "admin_back":
        await admin_panel(client, callback_query.message)
        await callback_query.answer()

    elif data == "admin_broadcast":
        db.set("temp_data", f"admin_broadcast_{user_id}", True)
        await callback_query.message.edit_text(
            "📢 **پیام همگانی**\n\n"
            "پیام مورد نظر خود را ارسال کنید تا برای همه کاربران فرستاده شود.\n"
            "برای لغو، /admin را بزنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 انصراف", callback_data="admin_back")]
            ])
        )
        await callback_query.answer()

    elif data == "admin_health":
        await callback_query.answer("⏳ در حال بررسی...")
        result = await run_health_check(send_report=False)
        await callback_query.message.edit_text(
            "♻️ **نتیجه بررسی سلامت سلف‌ها**\n\n"
            f"✅ سالم: `{result['alive']}`\n"
            f"♻️ اجرای مجدد: `{result['restarted']}`\n"
            f"🛑 متوقف‌شده: `{result['stopped']}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")]
            ])
        )
    
    elif data.startswith("set_"):
        target_id = int(data.split("_")[1])
        db.set("temp_data", f"admin_set_{user_id}", target_id)
        await callback_query.message.edit_text(
            f"💰 **تعداد سکه جدید برای کاربر {target_id} را وارد کنید:**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 انصراف", callback_data="admin_back")]
            ])
        )
        await callback_query.answer()
    
    elif data.startswith("stop_"):
        target_id = int(data.split("_")[1])
        if stop_selfbot(target_id):
            await callback_query.message.edit_text(f"✅ سلف‌بات کاربر {target_id} متوقف شد.")
        else:
            await callback_query.message.edit_text(f"ℹ️ سلف‌بات کاربر {target_id} از قبل متوقف بود.")
        await callback_query.answer()
    
    elif data.startswith("verify_approve_"):
        target_id = int(data.split("_")[2])
        user_data = db.get("users", target_id, {})
        user_data["verified"] = True
        user_data["rejected"] = False
        db.set("users", target_id, user_data)
        db.delete("verifications", target_id)
        
        await callback_query.message.edit_text(f"✅ احراز هویت کاربر {target_id} تایید شد.")
        try:
            await bot.send_message(
                target_id,
                "✅ **احراز هویت شما تایید شد!**\n\n"
                "اکنون می‌توانید از بخش «افزایش موجودی» استفاده کنید."
            )
        except:
            pass
        await callback_query.answer()
    
    elif data.startswith("verify_reject_"):
        target_id = int(data.split("_")[2])
        user_data = db.get("users", target_id, {})
        user_data["verified"] = False
        user_data["rejected"] = True
        db.set("users", target_id, user_data)
        db.delete("verifications", target_id)
        
        await callback_query.message.edit_text(f"❌ احراز هویت کاربر {target_id} رد شد.")
        try:
            await bot.send_message(
                target_id,
                "❌ **احراز هویت شما رد شد!**\n\n"
                "لطفا مجدداً با ارسال عکس واضح‌تر اقدام کنید."
            )
        except:
            pass
        await callback_query.answer()
    
    elif data.startswith("payment_approve_"):
        target_id = int(data.split("_")[2])
        # چک-و-ثبت وضعیت در یک قفل تا با دوبار کلیک، سکه دوباره واریز نشود
        with db.atomic() as data_store:
            payment_data = data_store.get("payments", {}).get(str(target_id))
            already = payment_data and payment_data.get("status") == "approved"
            if payment_data and not already:
                payment_data["status"] = "approved"
                payment_data["approved_at"] = time.time()

        if not payment_data:
            await callback_query.message.edit_text(f"❌ اطلاعات پرداخت کاربر {target_id} یافت نشد.")
            await callback_query.answer()
            return
        if already:
            await callback_query.answer("ℹ️ این پرداخت قبلاً تایید شده بود.", show_alert=True)
            return

        coins = payment_data.get("coins", 0)
        new_balance = db.add_credits(target_id, coins)

        await callback_query.message.edit_text(
            f"✅ پرداخت کاربر {target_id} تایید شد.\n"
            f"💰 {coins} سکه به حسابش اضافه شد."
        )
        try:
            await bot.send_message(
                target_id,
                f"✅ **پرداخت شما تایید شد!**\n\n"
                f"💰 {coins} سکه به حساب شما اضافه شد.\n"
                f"📊 موجودی جدید: {new_balance} سکه"
            )
        except Exception:
            pass
        await callback_query.answer()
    
    elif data.startswith("payment_reject_"):
        target_id = int(data.split("_")[2])
        payment_data = db.get("payments", target_id)
        if payment_data:
            payment_data["status"] = "rejected"
            db.set("payments", target_id, payment_data)
            
            await callback_query.message.edit_text(f"❌ پرداخت کاربر {target_id} رد شد.")
            try:
                await bot.send_message(
                    target_id,
                    "❌ **پرداخت شما رد شد!**\n\n"
                    "لطفا مجدداً با ارسال رسید واضح‌تر اقدام کنید."
                )
            except:
                pass
        else:
            await callback_query.message.edit_text(f"❌ اطلاعات پرداخت کاربر {target_id} یافت نشد.")
        await callback_query.answer()
        
async def broadcast_to_all_users(message):
    """ارسال پیام ادمین به همه کاربران ثبت‌شده."""
    users = db.get_all("users")
    sent, failed = 0, 0
    status = await message.reply_text(f"📤 در حال ارسال به {len(users)} کاربر...")

    for user_id_str in list(users.keys()):
        try:
            await message.copy(int(user_id_str))
            sent += 1
        except (ValueError, RPCError):
            failed += 1
        except Exception:
            failed += 1
        # جلوگیری از محدودیت نرخ تلگرام
        await asyncio.sleep(0.05)

    await status.edit_text(
        f"✅ **پیام همگانی ارسال شد**\n\n"
        f"📨 موفق: `{sent}`\n"
        f"⚠️ ناموفق: `{failed}`"
    )


async def verify_online_payment(client, callback_query):
    """تایید و واریز آنی پرداخت درگاه (با محافظت در برابر دوبار واریز)."""
    user_id = callback_query.from_user.id
    target_id = int(callback_query.data.split("_")[1])

    if user_id != target_id and user_id != ADMIN_ID:
        await callback_query.answer("❌ دسترسی غیرمجاز!", show_alert=True)
        return

    gateway = get_gateway()
    if gateway is None:
        await callback_query.answer("❌ درگاه پرداخت فعال نیست.", show_alert=True)
        return

    payment_data = db.get("payments", target_id)
    if not payment_data or not payment_data.get("authority"):
        await callback_query.answer("❌ تراکنشی برای بررسی یافت نشد.", show_alert=True)
        return
    if payment_data.get("status") == "approved":
        await callback_query.answer("ℹ️ این پرداخت قبلاً واریز شده است.", show_alert=True)
        return

    await callback_query.answer("⏳ در حال بررسی پرداخت...")
    try:
        ok, ref_id = await gateway.verify_payment(
            payment_data["authority"], int(round(payment_data.get("toman", 0)))
        )
    except PaymentError as error:
        await safe_edit(
            callback_query,
            f"❌ پرداخت تایید نشد: {error}\n\nاگر مبلغ کسر شده، تا ۷۲ ساعت به‌صورت خودکار بازمی‌گردد.",
        )
        return

    if not ok:
        await callback_query.answer("❌ پرداخت هنوز تایید نشده است.", show_alert=True)
        return

    # ثبت اتمیک وضعیت تا کلیک دوباره باعث واریز مجدد نشود
    with db.atomic() as data_store:
        record = data_store.get("payments", {}).get(str(target_id))
        already = record and record.get("status") == "approved"
        if record and not already:
            record["status"] = "approved"
            record["ref_id"] = ref_id
            record["approved_at"] = time.time()
    if already:
        await callback_query.answer("ℹ️ این پرداخت قبلاً واریز شده است.", show_alert=True)
        return

    coins = payment_data.get("coins", 0)
    new_balance = db.add_credits(target_id, coins)
    await safe_edit(
        callback_query,
        f"✅ **پرداخت با موفقیت انجام شد!**\n\n"
        f"💰 {coins} سکه به حساب شما اضافه شد.\n"
        f"📊 موجودی جدید: {new_balance} سکه\n"
        f"🧾 کد پیگیری: `{ref_id}`",
    )


@bot.on_callback_query()
async def callback_handler(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data
    
    # دکمه‌های موقتِ پیش از ارسال پیام به شکل joinbet_{chat_id}_waiting هستند،
    # پس مقایسه با رشته ثابت "joinbet_waiting" هیچ‌وقت درست نمی‌شد.
    if data.startswith("joinbet_"):
        if data.endswith("_waiting"):
            await callback_query.answer("⏳ لطفا چند لحظه صبر کنید...", show_alert=True)
            return
        await join_group_bet_handler(client, callback_query)
        return
    
    if data.startswith("cancelbet_"):
        if data.endswith("_waiting"):
            await callback_query.answer("⏳ لطفا چند لحظه صبر کنید...", show_alert=True)
            return
        await cancel_group_bet_handler(client, callback_query)
        return
    
    if data.startswith("verifypay_"):
        await verify_online_payment(client, callback_query)
        return

    if data.startswith(("admin_", "set_", "stop_", "verify_", "payment_")):
        if user_id != ADMIN_ID:
            await callback_query.answer("❌ دسترسی غیرمجاز!", show_alert=True)
            return
        await admin_callback_handler(client, callback_query)
        return
    
    if data == "admin_panel":
        if user_id != ADMIN_ID:
            await callback_query.answer("❌ دسترسی غیرمجاز!", show_alert=True)
            return
        await admin_panel(client, callback_query.message)
        await callback_query.answer()
        return
    
    if data == "back":
        credits = db.get("credits", user_id, 0)
        user_data = db.get("users", user_id, {})
    
        status_text = "🔴 سلف غیرفعال"
        phone_text = ""
        verified_status = "❌ احراز نشده"
    
        if user_data and user_data.get('status') == 'active':
            status_text = "🟢 سلف فعال"
            phone_text = f"\n📱 شماره: {user_data.get('phone', '')}"
    
        if user_data.get('verified'):
            verified_status = "✅ احراز شده"
    
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("● فعالسازی ●", callback_data="login", style=ButtonStyle.SUCCESS)],
            [
                InlineKeyboardButton("● حساب کاربری ●", callback_data="status_credits", style=ButtonStyle.PRIMARY),
                InlineKeyboardButton("● شرطبندی ●", callback_data="bet", style=ButtonStyle.PRIMARY)
            ],
            [
                InlineKeyboardButton("● مدیریت سلف ●", callback_data="self_management", style=ButtonStyle.DANGER),
                InlineKeyboardButton("● افزایش موجودی ●", callback_data="increase_balance", style=ButtonStyle.DANGER)
            ]
        ])
        if user_id == ADMIN_ID:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton("🛠 پنل ادمین", callback_data="admin_panel", style=ButtonStyle.DANGER)
            ])
    
        text = f"""<b>🤖 ربات مدیریت سلف بات</b>

    <b>وضعیت:</b> {status_text}{phone_text}
    <b>🔐 احراز:</b> {verified_status}
    <b>💰 سکه ها:</b> <code>{credits}</code> سکه
    <b>⏰ مصرف:</b> 1 سکه در ساعت"""
    
        photo_id = db.get_welcome_photo()
        if photo_id:
            if callback_query.message.photo:
                await callback_query.message.edit_caption(
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=enums.ParseMode.HTML
                )
            else:
                await callback_query.message.delete()
                await client.send_photo(
                    chat_id=user_id,
                    photo=photo_id,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=enums.ParseMode.HTML
                )
        else:
            await callback_query.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode=enums.ParseMode.HTML
            )
        await callback_query.answer()
        return
    if data == "login":
        credits = db.get("credits", user_id, 0)
        if credits <= 0:
            text = f"❌ <b>سکه کافی ندارید!</b>\n\n💰 سکه های شما: <code>{credits}</code>\n\n💡 برای دریافت سکه با پشتیبانی تماس بگیرید."
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back", style=ButtonStyle.DANGER)]])
            photo_id = db.get_welcome_photo()
            if photo_id:
                if callback_query.message.photo:
                    await callback_query.message.edit_caption(
                        caption=text,
                        reply_markup=keyboard,
                        parse_mode=enums.ParseMode.HTML
                    )
                else:
                    await callback_query.message.delete()
                    await client.send_photo(
                        chat_id=user_id,
                        photo=photo_id,
                        caption=text,
                        reply_markup=keyboard,
                        parse_mode=enums.ParseMode.HTML
                    )
            else:
                await callback_query.message.edit_text(
                    text,
                    reply_markup=keyboard,
                    parse_mode=enums.ParseMode.HTML
                )
            return
        
        text = "📱 <b>لطفا شماره تلفن خود را ارسال کنید:</b>\n\n<b>فرمت:</b> +989123456789\n\n⚠️ شماره باید با کد کشور شروع شود"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back", style=ButtonStyle.DANGER)]])
        photo_id = db.get_welcome_photo()
        if photo_id:
            if callback_query.message.photo:
                await callback_query.message.edit_caption(
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=enums.ParseMode.HTML
                )
            else:
                await callback_query.message.delete()
                await client.send_photo(
                    chat_id=user_id,
                    photo=photo_id,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=enums.ParseMode.HTML
                )
        else:
            await callback_query.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode=enums.ParseMode.HTML
            )
        await callback_query.answer()
    
    elif data == "login_again":
        await callback_query.message.edit_text(
            "📱 <b>لطفا شماره تلفن جدید خود را ارسال کنید:</b>\n\n"
            "<b>فرمت:</b> +989123456789\n\n"
            "⚠️ شماره باید با کد کشور شروع شود",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back")]])
        )
        await callback_query.answer()
    
    elif data == "status_credits":
        user_data = db.get("users", user_id, {})
        credits = db.get("credits", user_id, 0)
    
        if not user_data:
            text = "❌ <b>شما هیچ سلف باتی ندارید</b>\n\nابتدا باید لاگین کنید و سلف بات را فعال کنید."
        elif user_data.get('status') == 'active':
            text = (
                f"🟢 <b>سلف بات فعال</b>\n\n"
                f"📱 <b>شماره:</b> <code>{user_data.get('phone', '')}</code>\n"
                f"💰 <b>سکه باقی‌مانده:</b> <code>{credits}</code>\n"
                f"⏰ <b>زمان باقی‌مانده:</b> <code>{credits}</code> ساعت\n\n"
                f"⏱ <b>مصرف:</b> 1 سکه در ساعت"
            )
        else:
            text = (
                f"🔴 <b>سلف بات غیرفعال</b>\n\n"
                f"📱 <b>شماره:</b> <code>{user_data.get('phone', '')}</code>\n"
                f"💰 <b>سکه های شما:</b> <code>{credits}</code>\n\n"
                f"💡 برای فعال کردن سلف بات روی 'فعالسازی' کلیک کنید."
            )
    
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back", style=ButtonStyle.DANGER)]])
        photo_id = db.get_welcome_photo()
        if photo_id:
            if callback_query.message.photo:
                await callback_query.message.edit_caption(
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=enums.ParseMode.HTML
                )
            else:
                await callback_query.message.delete()
                await client.send_photo(
                    chat_id=user_id,
                    photo=photo_id,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=enums.ParseMode.HTML
                )
        else:
            await callback_query.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode=enums.ParseMode.HTML
            )
        await callback_query.answer()
    
    elif data == "bet":
        info_text = """
🎲 **سیستم شرطبندی گروهی 1v1**

**📋 قوانین شرطبندی:**
1️⃣ در گروه با نوشتن `شرطبندی 100` (یا هر مقدار دیگر) می‌توانید شرط ایجاد کنید
2️⃣ نفر دوم می‌تواند با کلیک روی دکمه «پیوستن به شرط» وارد شود
3️⃣ پس از پیوستن نفر دوم، ۵ ثانیه بعد برنده مشخص می‌شود
4️⃣ برنده تمام مبلغ شرط را دریافت می‌کند
5️⃣ اگر در ۵ دقیقه کسی شرکت نکند، شرط لغو و مبلغ بازگردانده می‌شود

**💰 مثال:**
- شما: `شرطبندی 500`
- حریف: پیوستن به شرط
- برنده: تمام 1000 سکه را می‌برد (500+500)
    """
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back", style=ButtonStyle.DANGER)]
        ])
    
        photo_id = db.get_welcome_photo()
        if photo_id:
            if callback_query.message.photo:
                await callback_query.message.edit_caption(
                    caption=info_text,
                    reply_markup=keyboard,
                    parse_mode=enums.ParseMode.HTML
                )
            else:
                await callback_query.message.delete()
                await client.send_photo(
                    chat_id=user_id,
                    photo=photo_id,
                    caption=info_text,
                    reply_markup=keyboard,
                    parse_mode=enums.ParseMode.HTML
                )
        else:
            await callback_query.message.edit_text(
                info_text,
                reply_markup=keyboard,
                parse_mode=enums.ParseMode.HTML
            )
        await callback_query.answer()
    
    elif data == "self_management":
        user_data = db.get("users", user_id, {})
        credits = db.get("credits", user_id, 0)

        is_active = check_selfbot_status(user_id)
        process = db.get("processes", user_id)
    
        if is_active and user_data.get('status') != 'active':
            user_data["status"] = "active"
            db.set("users", user_id, user_data)
        elif not is_active and user_data.get('status') == 'active':
            user_data["status"] = "inactive"
            db.set("users", user_id, user_data)
    
        status_text = "🟢 <b>فعال</b>" if is_active and process else "🔴 <b>غیرفعال</b>"
    
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("▶️ روشن کردن سلف", callback_data="self_start", style=ButtonStyle.SUCCESS),
                InlineKeyboardButton("⏹ خاموش کردن سلف", callback_data="self_stop", style=ButtonStyle.DANGER)
            ],
            [
                InlineKeyboardButton("🔄 آپدیت سلف", callback_data="self_update", style=ButtonStyle.PRIMARY)
            ],
            [
                InlineKeyboardButton("🔙 بازگشت", callback_data="back", style=ButtonStyle.DANGER)
            ]
        ])
    
        text = (
            f"⚙️ <b>مدیریت سلف بات</b>\n\n"
            f"📊 <b>وضعیت فعلی:</b> {status_text}\n"
            f"💰 <b>سکه ها:</b> <code>{credits}</code>\n\n"
            f"🔹 <b>روشن کردن:</b> سلف بات را فعال می‌کند\n"
            f"🔹 <b>خاموش کردن:</b> سلف بات را متوقف می‌کند\n"
            f"🔹 <b>آپدیت سلف:</b> سلف بات را مجدداً راه‌اندازی می‌کند\n\n"
            f"📱 <b>شماره:</b> <code>{user_data.get('phone', 'ثبت نشده')}</code>"
        )
    
        photo_id = db.get_welcome_photo()
        if photo_id:
            if callback_query.message.photo:
                await callback_query.message.edit_caption(
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=enums.ParseMode.HTML
                )
            else:
                await callback_query.message.delete()
                await client.send_photo(
                    chat_id=user_id,
                    photo=photo_id,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=enums.ParseMode.HTML
                )
        else:
            await callback_query.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode=enums.ParseMode.HTML
            )
        await callback_query.answer()
    
    elif data == "self_start":
        user_data = db.get("users", user_id, {})
        credits = db.get("credits", user_id, 0)
    
        if credits <= 0:
            await callback_query.message.edit_text(
                f"❌ <b>سکه کافی ندارید!</b>\n\n"
                f"💰 سکه های شما: <code>{credits}</code>\n\n"
            "💡 لطفا ابتدا موجودی خود را افزایش دهید.",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                        "💰 افزایش موجودی",
                            callback_data="increase_balance",
                            style=ButtonStyle.SUCCESS  # سبز
                        )
                    ],
                    [
                        InlineKeyboardButton(
                        "🔙 بازگشت",
                            callback_data="self_management",
                            style=ButtonStyle.DANGER  # قرمز
                        )
                    ]
                ]),
                parse_mode=enums.ParseMode.HTML
            )
            return
    
        if not user_data.get('phone'):
            await callback_query.message.edit_text(
                "❌ <b>شماره تلفن ثبت نشده است!</b>\n\n"
            "لطفا ابتدا از طریق دکمه «فعالسازی» شماره خود را ثبت کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                        "● فعالسازی ●",
                            callback_data="login",
                            style=ButtonStyle.SUCCESS  # سبز
                        )
                    ],
                    [
                        InlineKeyboardButton(
                        "🔙 بازگشت",
                            callback_data="self_management",
                            style=ButtonStyle.DANGER  # قرمز
                        )
                    ]
                ])
            )
            return
    
        if db.get("processes", user_id):
            await callback_query.message.edit_text(
                "ℹ️ <b>سلف بات در حال حاضر فعال است!</b>\n\n"
            "برای راه‌اندازی مجدد از گزینه «آپدیت سلف» استفاده کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                        "🔄 آپدیت سلف",
                            callback_data="self_update",
                            style=ButtonStyle.PRIMARY  # آبی
                        )
                    ],
                    [
                        InlineKeyboardButton(
                        "🔙 بازگشت",
                            callback_data="self_management",
                            style=ButtonStyle.DANGER  # قرمز
                        )
                    ]
                ])
            )
            return
    
        if run_selfbot(user_id, user_data.get('phone')):
            credits = db.get("credits", user_id, 0)
            await callback_query.message.edit_text(
                f"✅ <b>سلف بات با موفقیت روشن شد!</b>\n\n"
                f"💰 <b>سکه باقی‌مانده:</b> <code>{credits}</code>\n"
                f"⏰ <b>زمان باقی‌مانده:</b> <code>{credits}</code> ساعت\n\n"
                f"📱 <b>شماره:</b> <code>{user_data.get('phone')}</code>",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                        "🔙 بازگشت به مدیریت",
                            callback_data="self_management",
                            style=ButtonStyle.DANGER  # قرمز
                        )
                    ]
                ]),
                parse_mode=enums.ParseMode.HTML
            )
        else:
            await callback_query.message.edit_text(
                "❌ <b>خطا در روشن کردن سلف بات!</b>\n\n"
            "لطفا دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                        "🔄 تلاش مجدد",
                            callback_data="self_start",
                            style=ButtonStyle.PRIMARY  # آبی
                        )
                    ],
                    [
                        InlineKeyboardButton(
                        "🔙 بازگشت",
                            callback_data="self_management",
                            style=ButtonStyle.DANGER  # قرمز
                        )
                    ]
                ])
            )
        await callback_query.answer()
    
    elif data == "self_stop":
        if stop_selfbot(user_id):
            await callback_query.message.edit_text(
                "✅ <b>سلف بات با موفقیت خاموش شد!</b>\n\n"
            "برای روشن کردن مجدد از گزینه «روشن کردن سلف» استفاده کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                        "▶️ روشن کردن سلف",
                            callback_data="self_start",
                            style=ButtonStyle.SUCCESS  # سبز
                        )
                    ],
                    [
                        InlineKeyboardButton(
                        "🔙 بازگشت به مدیریت",
                            callback_data="self_management",
                            style=ButtonStyle.DANGER  # قرمز
                        )
                    ]
                ])
            )
        else:
            await callback_query.message.edit_text(
                "ℹ️ <b>سلف بات در حال حاضر خاموش است!</b>\n\n"
            "برای روشن کردن از گزینه «روشن کردن سلف» استفاده کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                        "▶️ روشن کردن سلف",
                            callback_data="self_start",
                            style=ButtonStyle.SUCCESS  # سبز
                        )
                    ],
                    [
                        InlineKeyboardButton(
                        "🔙 بازگشت به مدیریت",
                            callback_data="self_management",
                            style=ButtonStyle.DANGER  # قرمز
                        )
                    ]
                ])
            )
        await callback_query.answer()
    
    elif data == "self_update":
        user_data = db.get("users", user_id, {})
        credits = db.get("credits", user_id, 0)
        
        if credits <= 0:
            await callback_query.message.edit_text(
                f"❌ <b>سکه کافی ندارید!</b>\n\n"
                f"💰 سکه های شما: <code>{credits}</code>\n\n"
                "💡 لطفا ابتدا موجودی خود را افزایش دهید.",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
            "💰 افزایش موجودی",
                            callback_data="increase_balance",
                            style=ButtonStyle.SUCCESS  # سبز
                        )
                    ],
                    [
                        InlineKeyboardButton(
            "🔙 بازگشت",
                            callback_data="self_management",
                            style=ButtonStyle.DANGER  # قرمز
                        )
                    ]
                ]),
                parse_mode=enums.ParseMode.HTML
            )
            return
        
        if not user_data.get('phone'):
            await callback_query.message.edit_text(
                "❌ <b>شماره تلفن ثبت نشده است!</b>\n\n"
                "لطفا ابتدا از طریق دکمه «فعالسازی» شماره خود را ثبت کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
            "● فعالسازی ●",
                            callback_data="login",
                            style=ButtonStyle.SUCCESS  
                        )
                    ],
                    [
                        InlineKeyboardButton(
            "🔙 بازگشت",
                            callback_data="self_management",
                            style=ButtonStyle.DANGER  
                        )
                    ]
                ])
            )
            return
        
        await callback_query.message.edit_text(
            "🔄 <b>در حال آپدیت سلف بات...</b>\n\n"
            "لطفا چند لحظه صبر کنید...",
            reply_markup=None
        )
        
        stop_selfbot(user_id)
        await asyncio.sleep(1)
        
        if run_selfbot(user_id, user_data.get('phone')):
            credits = db.get("credits", user_id, 0)
            await callback_query.message.edit_text(
                f"✅ <b>سلف بات با موفقیت آپدیت شد!</b>\n\n"
                f"💰 <b>سکه باقی‌مانده:</b> <code>{credits}</code>\n"
                f"⏰ <b>زمان باقی‌مانده:</b> <code>{credits}</code> ساعت\n\n"
                f"📱 <b>شماره:</b> <code>{user_data.get('phone')}</code>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت به مدیریت", callback_data="self_management")]
                ]),
                parse_mode=enums.ParseMode.HTML
            )
        else:
            await callback_query.message.edit_text(
                "❌ <b>خطا در آپدیت سلف بات!</b>\n\n"
                "لطفا دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
            "🔄 تلاش مجدد",
                            callback_data="self_update",
                            style=ButtonStyle.SUCCESS  # سبز
                        )
                    ],
                    [
                        InlineKeyboardButton(
            "🔙 بازگشت",
                            callback_data="self_management",
                            style=ButtonStyle.DANGER  # قرمز
                        )
                    ]
                ])
            )
        await callback_query.answer()
    
    elif data == "increase_balance":
        ok, not_joined = await check_force_join(client, user_id)
        if not ok:
            buttons = [
                [InlineKeyboardButton(f"📢 عضویت در @{ch}", url=f"https://t.me/{ch}")]
                for ch in not_joined
            ]
            buttons.append([InlineKeyboardButton("🔄 بررسی عضویت", callback_data="check_join")])
            await safe_edit(
                callback_query,
                "❌ برای استفاده از ربات باید در تمام کانال‌های زیر عضو شوید:",
                InlineKeyboardMarkup(buttons),
            )
            return

        user_data = db.get("users", user_id, {})
    
        if user_data.get('rejected'):
            await callback_query.answer("❌ حساب شما توسط ادمین رد شده است.", show_alert=True)
            return
    
        if not user_data.get('verified'):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("● احراز هویت ●", callback_data="start_verification", style=ButtonStyle.SUCCESS)],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back", style=ButtonStyle.DANGER)]
            ])
        
            text = (
            "🔒 **برای افزایش موجودی نیاز به احراز هویت دارید**\n\n"
            "📋 **مراحل احراز هویت:**\n"
            "1️⃣ کلیک روی دکمه 'احراز هویت'\n"
            "2️⃣ ارسال عکس از کارت بانکی\n"
            "3️⃣ تایید توسط ادمین\n"
            "4️⃣ افزایش موجودی\n\n"
            "⚠️ **توجه:** اطلاعات حساس (CVV2، تاریخ انقضا) در عکس پوشیده شود"
            )
        
            photo_id = db.get_welcome_photo()
            if photo_id:
                if callback_query.message.photo:
                    await callback_query.message.edit_caption(
                        caption=text,
                        reply_markup=keyboard,
                        parse_mode=enums.ParseMode.HTML
                    )
                else:
                    await callback_query.message.delete()
                    await client.send_photo(
                        chat_id=user_id,
                        photo=photo_id,
                        caption=text,
                        reply_markup=keyboard,
                        parse_mode=enums.ParseMode.HTML
                    )
            else:
                await callback_query.message.edit_text(
                    text,
                    reply_markup=keyboard,
                    parse_mode=enums.ParseMode.HTML
                )
            return
    
        text = (
            f"💰 **افزایش موجودی**\n\n"
            f"💎 **نرخ تبدیل:** هر {COIN_RATE} سکه = 50,000 تومان\n"
            f"💵 **قیمت هر سکه:** {TOMAN_PER_COIN:.0f} تومان\n\n"
        "🔢 **تعداد سکه مورد نظر خود را وارد کنید:**\n"
        "مثال: 1440\n\n"
        "💡 **توجه:** فقط عدد وارد کنید (بدون نقطه یا کاما)"
        )
    
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back", style=ButtonStyle.DANGER)]])
    
        photo_id = db.get_welcome_photo()
        if photo_id:
            if callback_query.message.photo:
                await callback_query.message.edit_caption(
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=enums.ParseMode.HTML
                )
            else:
                await callback_query.message.delete()
                await client.send_photo(
                    chat_id=user_id,
                    photo=photo_id,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=enums.ParseMode.HTML
                )
        else:
            await callback_query.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode=enums.ParseMode.HTML
            )
    
        db.delete("temp_data", f"waiting_coins_{user_id}")
        db.set("temp_data", f"waiting_coins_{user_id}", True)
        await callback_query.answer("✅ لطفا تعداد سکه مورد نظر را وارد کنید")

    elif data == "start_verification":
        user_data = db.get("users", user_id, {})
        if user_data.get('rejected'):
            await callback_query.answer("❌ حساب شما توسط ادمین رد شده است.", show_alert=True)
            return
    
        text = (
            "📸 <b>لطفا عکس کارت بانکی خود را ارسال کنید</b>\n\n"
            "⚠️ <b>قبل از ارسال مطمئن شوید:</b>\n"
        "• نام صاحب کارت مشخص باشد\n"
        "• شماره کارت واضح باشد\n"
        "• CVV2 ❌ پوشیده شود\n"
        "• تاریخ انقضا ❌ پوشیده شود\n\n"
        "📎 یک عکس با کیفیت مناسب ارسال کنید"
        )
    
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data="increase_balance", style=ButtonStyle.DANGER)]
        ])
    
        photo_id = db.get_welcome_photo()
        if photo_id:
            if callback_query.message.photo:
                await callback_query.message.edit_caption(
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=enums.ParseMode.HTML
                )
            else:
                await callback_query.message.delete()
                await client.send_photo(
                    chat_id=user_id,
                    photo=photo_id,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=enums.ParseMode.HTML
                )
        else:
            await callback_query.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode=enums.ParseMode.HTML
            )
    
        db.set("temp_data", f"waiting_card_photo_{user_id}", True)
    
    elif data == "check_join":
        ok, not_joined = await check_force_join(client, user_id)
        if ok:
            await callback_query.message.edit_text("✅ عضویت شما در همه کانال‌ها تایید شد!\nدوباره /start بزنید.")
            return
        buttons = []
        for ch in not_joined:
            buttons.append([
                InlineKeyboardButton(
                    f"📢 عضویت در @{ch}", 
                    url=f"https://t.me/{ch}",
                    style=ButtonStyle.PRIMARY  
                )
            ])
        buttons.append([
            InlineKeyboardButton(
                "🔄 بررسی مجدد", 
                callback_data="check_join",
                style=ButtonStyle.SUCCESS  
            )
        ])

        await callback_query.message.edit_text(
    "❌ هنوز عضو همه کانال‌ها نیستید!",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        await callback_query.answer()
@bot.on_message(filters.user(ADMIN_ID) & filters.regex(r'^\d+$'))
async def handle_admin_input(client, message: Message):
    user_id = message.from_user.id
    amount = int(message.text)
    
    set_target = db.get("temp_data", f"admin_set_{user_id}")
    if set_target:
        db.delete("temp_data", f"admin_set_{user_id}")
        db.set("credits", set_target, amount)
        
        await message.reply_text(f"✅ سکه کاربر {set_target} تنظیم شد به {amount}")
        
        try:
            await bot.send_message(set_target, f"🔧 موجودی سکه شما تنظیم شد\n💰 جدید: {amount} سکه")
        except: pass
from pyrogram.enums import ButtonStyle

@bot.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    ok, not_joined = await check_force_join(client, message.from_user.id)
    if not ok:
        buttons = []
        for ch in not_joined:
            buttons.append([InlineKeyboardButton(f"📢 عضویت در @{ch}", url=f"https://t.me/{ch}", style=ButtonStyle.PRIMARY)])
        buttons.append([InlineKeyboardButton("● بررسی عضویت ●", callback_data="check_join", style=ButtonStyle.SUCCESS)])
        await message.reply_text(
            "❌ برای استفاده از ربات باید در تمام کانال‌های زیر عضو شوید:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    user_id = message.from_user.id
    
    existing_user = db.get("users", user_id)
    is_new_user = False
    
    if not existing_user:
        user_info = {
            "status": "inactive",
            "created_at": time.time(),
            "first_name": message.from_user.first_name or "",
            "username": message.from_user.username or "",
            "verified": False,
            "rejected": False
        }
        db.set("users", user_id, user_info)
        is_new_user = True
    else:
        user_info = existing_user
        user_info["first_name"] = message.from_user.first_name or ""
        user_info["username"] = message.from_user.username or ""
        db.set("users", user_id, user_info)
    
    credits = db.get("credits", user_id, 0)
    if is_new_user and credits == 0:
        db.set("credits", user_id, 5)
        credits = 5
    
    user_data = db.get("users", user_id, {})
    phone = user_data.get('phone', '')
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("● فعالسازی ●", callback_data="login", style=ButtonStyle.SUCCESS)
        ],
        [
            InlineKeyboardButton("● حساب کاربری ●", callback_data="status_credits", style=ButtonStyle.PRIMARY),
            InlineKeyboardButton("● شرطبندی ●", callback_data="bet", style=ButtonStyle.PRIMARY)
        ],
        [
            InlineKeyboardButton("● مدیریت سلف ●", callback_data="self_management", style=ButtonStyle.DANGER),
            InlineKeyboardButton("● افزایش موجودی ●", callback_data="increase_balance", style=ButtonStyle.DANGER)
        ]
    ])

    if user_id == ADMIN_ID:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton("🛠 پنل ادمین", callback_data="admin_panel", style=ButtonStyle.DANGER)
        ])
    
    welcome_text = f"""<b>به ربات سلف ساز خوش آمدید!</b>

<b>ربات مدیریت سلف بات حرفه‌ای</b>
├─ ساخت سلف شخصی
📊 وضعیت حساب شما:
├─ 👤 کاربر: {message.from_user.first_name or "ناشناس"}
├─ 💰 سکه: {credits} عدد
└─ ⏰ مصرف 1 سکه در ساعت

📱 شماره: {phone if phone else 'ثبت نشده'}

💡 برای شروع روی «فعالسازی» کلیک کنید."""

    photo_id = db.get_welcome_photo()
    if photo_id:
        await message.reply_photo(
            photo=photo_id,
            caption=welcome_text,
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML
        )
    else:
        await message.reply_text(
            welcome_text,
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML
        )
async def join_group_bet_handler(client, callback_query):
    user_id = callback_query.from_user.id
    user_first_name = html.escape(callback_query.from_user.first_name or 'کاربر')
    user_mention = f'<a href="tg://user?id={user_id}"><b>{user_first_name}</b></a>'
    data = callback_query.data
    _, chat_id_str, msg_id_str = data.split('_')

    chat_id = int(chat_id_str)
    message_id = int(msg_id_str)
    bet_key = f"{chat_id}_{message_id}"

    bet_data = db.get("group_bets", bet_key)
    if not bet_data or not bet_data.get("is_active"):
        await callback_query.answer("❌ این شرط دیگر فعال نیست.", show_alert=True)
        return

    if bet_data.get("finished"):
        await callback_query.answer("❌ این شرط قبلا به پایان رسیده است.", show_alert=True)
        return
    
    if callback_query.message.chat.id != chat_id:
        await callback_query.answer("❌ این دکمه مخصوص گروه اصلی شرط است.", show_alert=True)
        return

    creator_id = bet_data["creator_id"]
    creator_first_name = html.escape(bet_data.get('creator_name', 'کاربر'))
    creator_mention = f'<a href="tg://user?id={creator_id}"><b>{creator_first_name}</b></a>'
    participants = bet_data.get("participants", [])
    
    if user_id == creator_id:
        await callback_query.answer("ℹ️ شما سازنده این شرط هستید و قبلاً داخل شرط هستید.", show_alert=True)
        return
    
    if len(participants) >= 1:
        await callback_query.answer("⛔ ظرفیت این شرط تکمیل شده است.", show_alert=True)
        return

    if user_id in [p["id"] for p in participants]:
        await callback_query.answer("ℹ️ شما قبلا در این شرط شرکت کرده‌اید.", show_alert=True)
        return

    amount = bet_data["amount"]

    # رزرو اتمیک جایگاه: هم‌زمان که ظرفیت را چک می‌کنیم شرکت‌کننده را ثبت می‌کنیم
    # تا دو نفر با کلیک هم‌زمان هر دو وارد نشوند.
    with db.atomic() as data_store:
        stored = data_store.get("group_bets", {}).get(bet_key)
        if not stored or not stored.get("is_active") or stored.get("finished"):
            reserved = "inactive"
        elif len(stored.get("participants", [])) >= 1:
            reserved = "full"
        elif user_id in [p["id"] for p in stored.get("participants", [])]:
            reserved = "already"
        else:
            stored.setdefault("participants", []).append({
                "id": user_id,
                "name": callback_query.from_user.first_name or "",
                "username": callback_query.from_user.username or "",
            })
            bet_data = stored
            participants = stored["participants"]
            reserved = "ok"

    if reserved == "inactive":
        await callback_query.answer("❌ این شرط دیگر فعال نیست.", show_alert=True)
        return
    if reserved == "full":
        await callback_query.answer("⛔ ظرفیت این شرط تکمیل شده است.", show_alert=True)
        return
    if reserved == "already":
        await callback_query.answer("ℹ️ شما قبلا در این شرط شرکت کرده‌اید.", show_alert=True)
        return

    # حالا که جایگاه رزرو شد، سکه را اتمیک کم می‌کنیم؛ اگر کافی نبود، رزرو را پس می‌گیریم
    spent, current_credits = db.spend_credits(user_id, amount)
    if not spent:
        with db.atomic() as data_store:
            stored = data_store.get("group_bets", {}).get(bet_key)
            if stored:
                stored["participants"] = [
                    p for p in stored.get("participants", []) if p["id"] != user_id
                ]
        await callback_query.answer(
            f"❌ سکه کافی ندارید!\n💰 موجودی شما: {current_credits} سکه",
            show_alert=True
        )
        return
    
    try:
        participants_mentions = []
        for p in participants:
            p_name = html.escape(p.get('name', 'کاربر'))
            participants_mentions.append(f'<a href="tg://user?id={p["id"]}"><b>{p_name}</b></a>')
        
        all_players_mentions = [creator_mention] + participants_mentions
        waiting_text = (
            "⏳ <b>در حال قرعه‌کشی...</b>\n\n"
            f"💰 <b>مبلغ هر نفر:</b> <code>{amount}</code> سکه\n"
            f"👥 <b>شرکت‌کننده‌ها:</b> <code>{len(participants) + 1}/2</code> نفر\n"
            f"👤 <b>بازیکنان:</b> {', '.join(all_players_mentions)}\n\n"
            "🔄 ۵ ثانیه دیگر برنده مشخص می‌شود..."
        )
        await callback_query.message.edit_text(
            waiting_text,
            reply_markup=None, 
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        print(f"Error updating bet message: {e}")
    if not bet_data.get("timer_started"):
        bet_data["timer_started"] = True
        db.set("group_bets", bet_key, bet_data)
        asyncio.create_task(finish_group_bet(client, bet_key))
    else:
        db.set("group_bets", bet_key, bet_data)

    await callback_query.answer("✅ در شرط شرکت کردید و سکه از حساب شما کسر شد.")
async def cancel_group_bet_handler(client, callback_query):
    user_id = callback_query.from_user.id
    user_first_name = html.escape(callback_query.from_user.first_name or 'کاربر')
    user_mention = f'<a href="tg://user?id={user_id}"><b>{user_first_name}</b></a>'
    data = callback_query.data
    _, chat_id_str, msg_id_str = data.split('_')

    chat_id = int(chat_id_str)
    message_id = int(msg_id_str)
    bet_key = f"{chat_id}_{message_id}"

    bet_data = db.get("group_bets", bet_key)
    if not bet_data:
        await callback_query.answer("❌ این شرط یافت نشد یا قبلا حذف شده.", show_alert=True)
        return

    creator_id = bet_data["creator_id"]
    creator_first_name = html.escape(bet_data.get('creator_name', 'کاربر'))
    creator_mention = f'<a href="tg://user?id={creator_id}"><b>{creator_first_name}</b></a>'

    if user_id != creator_id:
        await callback_query.answer("❌ فقط سازنده شرط می‌تواند آن را لغو کند.", show_alert=True)
        return

    if bet_data.get("finished"):
        await callback_query.answer("❌ این شرط قبلا تمام شده است.", show_alert=True)
        return

    amount = bet_data["amount"]
    participants = bet_data.get("participants", [])
    if not bet_data.get("refunded"):
        creator_credits = db.get("credits", creator_id, 0)
        db.set("credits", creator_id, creator_credits + amount)
        bet_data["refunded"] = True
    for participant in participants:
        uid = participant["id"]
        credits = db.get("credits", uid, 0)
        db.set("credits", uid, credits + amount)

    bet_data["finished"] = True
    bet_data["is_active"] = False
    db.set("group_bets", bet_key, bet_data)

    participants_mentions = []
    for p in participants:
        p_name = html.escape(p.get('name', 'کاربر'))
        participants_mentions.append(f'<a href="tg://user?id={p["id"]}"><b>{p_name}</b></a>')
    
    all_users_text = creator_mention
    if participants_mentions:
        all_users_text += f", {', '.join(participants_mentions)}"

    text = (
        "⛔ این شرط توسط سازنده لغو شد.\n\n"
        f"👤 سازنده: {creator_mention}\n"
        f"👥 سایر بازیکنان: {', '.join(participants_mentions) if participants_mentions else 'ندارد'}\n"
        f"💰 مبلغ شرط: <code>{amount}</code> سکه\n"
        "💸 مبلغ به تمام افراد (سازنده و شرکت‌کننده‌ها) برگشت داده شد."
    )

    try:
        await callback_query.message.edit_text(text, reply_markup=None, parse_mode=enums.ParseMode.HTML)
    except:
        pass

    await callback_query.answer("✅ شرط با موفقیت لغو شد.", show_alert=True)
@bot.on_message(filters.private & filters.regex(r'^\+\d{10,15}$'))
async def handle_phone(client, message: Message):
    user_id, phone = message.from_user.id, message.text
    
    if user_id in active_clients:
        try:
            await active_clients[user_id].disconnect()
            del active_clients[user_id]
        except:
            pass
    
    credits = db.get("credits", user_id, 0)
    if credits <= 0:
        await message.reply_text(f"❌ سکه کافی ندارید!\nسکه های شما: {credits}")
        return
    
    try:
        session_name = f"sessions/{user_id}"
        temp_client = Client(session_name, api_id=API_ID, api_hash=API_HASH)
        await temp_client.connect()
        
        active_clients[user_id] = temp_client
        sent_code = await temp_client.send_code(phone)
        user_data = db.get("users", user_id, {})
        user_data["phone"] = phone
        db.set("users", user_id, user_data)
        await message.reply_text(
            "✅ **کد تأیید ارسال شد**\n\n"
            "🔢 **کد ۵ رقمی را با دکمه‌های زیر وارد کنید:**\n\n"
            f"<b><code>{format_code_display('')}</code></b>\n\n"
            "📱 کد ارسال شده به شماره شما",
            reply_markup=create_numpad_keyboard(),
            parse_mode=enums.ParseMode.HTML
        )
        
        db.set("temp_data", user_id, {
            "phone": phone, 
            "phone_code_hash": sent_code.phone_code_hash,
            "client_active": True
        })
        
    except Exception as e:
        await message.reply_text(f"❌ **خطا:** {str(e)}")
        if user_id in active_clients:
            try:
                await active_clients[user_id].disconnect()
                del active_clients[user_id]
            except:
                pass
@bot.on_message(filters.private & filters.text)
async def handle_all_messages(client, message: Message):
    user_id = message.from_user.id
    text = message.text
    if db.get("temp_data", f"waiting_coins_{user_id}"):
        try:
            coins_amount = int(text)
            if coins_amount <= 0:
                await message.reply_text("❌ تعداد سکه باید بیشتر از صفر باشد")
                return
            
            toman_amount = coins_amount * TOMAN_PER_COIN
            
            payment_data = {
                "user_id": user_id,
                "coins": coins_amount,
                "toman": toman_amount,
                "timestamp": time.time(),
                "status": "pending",
                "first_name": message.from_user.first_name or "",
                "username": message.from_user.username or ""
            }
            db.delete("temp_data", f"waiting_coins_{user_id}")

            gateway = get_gateway()
            if gateway is not None:
                # مسیر درگاه آنی: لینک پرداخت ساخته می‌شود و کاربر پس از پرداخت
                # روی «بررسی پرداخت» می‌زند تا سکه به‌صورت خودکار واریز شود.
                try:
                    authority, pay_url = await gateway.create_payment(
                        int(round(toman_amount)),
                        f"خرید {coins_amount} سکه",
                        user_id,
                    )
                except PaymentError as error:
                    await message.reply_text(f"❌ خطا در ساخت پرداخت: {error}")
                    return

                payment_data["gateway"] = gateway.name
                payment_data["authority"] = authority
                db.set("payments", user_id, payment_data)

                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("💳 پرداخت آنلاین", url=pay_url)],
                    [InlineKeyboardButton("✅ پرداخت کردم / بررسی", callback_data=f"verifypay_{user_id}")],
                    [InlineKeyboardButton("🔙 انصراف", callback_data="increase_balance")],
                ])
                await message.reply_text(
                    f"💳 **پرداخت آنلاین**\n\n"
                    f"💎 تعداد سکه: {coins_amount}\n"
                    f"💵 مبلغ: {toman_amount:,.0f} تومان\n\n"
                    f"1️⃣ روی «پرداخت آنلاین» بزنید و مبلغ را پرداخت کنید.\n"
                    f"2️⃣ سپس روی «پرداخت کردم / بررسی» بزنید تا سکه‌ها آنی واریز شود.",
                    reply_markup=keyboard,
                )
                return

            # مسیر کارت‌به‌کارت دستی (وقتی درگاه غیرفعال است)
            db.set("payments", user_id, payment_data)
            payment_text = (
                f"💳 **برای پرداخت لطفا مبلغ {toman_amount:,.0f} تومان به حساب زیر واریز کنید:**\n\n"
                f"🏦 **بانک:** {card_info['bank_name']}\n"
                f"🔢 **شماره کارت:** `{card_info['card_number']}`\n"
                f"👤 **به نام:** {card_info['card_owner']}\n\n"
                f"💎 **تعداد سکه دریافتی:** {coins_amount} سکه\n\n"
                f"📸 **پس از واریز، رسید یا عکس پرداخت را ارسال کنید**\n"
                f"⏰ پرداخت شما حداکثر تا 24 ساعت بررسی خواهد شد"
            )
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
            "🔙 انصراف", 
                        callback_data="increase_balance",
                        style=ButtonStyle.DANGER  
                    )
                ]
            ])
            
            await message.reply_text(payment_text, reply_markup=keyboard)
            db.set("temp_data", f"waiting_payment_proof_{user_id}", True)
            
        except ValueError:
            await message.reply_text("❌ لطفا یک عدد معتبر وارد کنید")
        return

    temp_data = db.get("temp_data", user_id)
    if temp_data and temp_data.get("needs_password"):
        try:
            if user_id not in active_clients:
                await message.reply_text("❌ کلاینت فعال نیست. لطفا دوباره شماره را ارسال کنید.")
                return
            
            user_client = active_clients[user_id]
            await user_client.check_password(text)
            
            user_info = {
                "phone": temp_data["phone"],
                "status": "active",
                "created_at": time.time(),
                "last_active": time.time(),
                "verified": db.get("users", user_id, {}).get("verified", False)
            }
            db.set("users", user_id, user_info)
            db.delete("temp_data", user_id)
            
            if user_id in active_clients:
                try:
                    await active_clients[user_id].disconnect()
                    del active_clients[user_id]
                except:
                    pass
            
            if run_selfbot(user_id, temp_data["phone"]):
                credits = db.get("credits", user_id, 0)
                await message.reply_text(
                    f"✅ **سلف بات فعال شد!**\n\n"
                    f"💰 سکه های شما: {credits}\n"
                    f"⏰ زمان باقی‌مانده: {credits} ساعت"
                )
            else: 
                await message.reply_text("❌ خطا در اجرای سلف")
            
        except Exception as e: 
            await message.reply_text(f"❌ رمز اشتباه: {str(e)}")
        return

    if user_id == ADMIN_ID:
        if db.get("temp_data", f"admin_broadcast_{user_id}"):
            db.delete("temp_data", f"admin_broadcast_{user_id}")
            await broadcast_to_all_users(message)
            return

        set_target = db.get("temp_data", f"admin_set_{user_id}")
        if set_target and text.isdigit():
            amount = int(text)
            db.delete("temp_data", f"admin_set_{user_id}")
            db.set("credits", set_target, amount)
            
            await message.reply_text(f"✅ سکه کاربر {set_target} تنظیم شد به {amount}")
            
            try:
                await bot.send_message(set_target, f"🔧 موجودی سکه شما تنظیم شد\n💰 جدید: {amount} سکه")
            except: 
                pass
            return
    
    pass
@bot.on_message(filters.photo & filters.private)
async def handle_admin_photo(client, message: Message):
    user_id = message.from_user.id
    
    if db.get("temp_data", f"admin_waiting_photo_{user_id}"):
        if user_id != ADMIN_ID:
            await message.reply_text("❌ فقط ادمین می‌تونه عکس تنظیم کنه!")
            return
        
        photo_id = message.photo.file_id
        
        db.set_welcome_photo(photo_id)
        db.delete("temp_data", f"admin_waiting_photo_{user_id}")
        
        text = (
            f"✅ **عکس با موفقیت تنظیم شد!**\n\n"
            f"📸 **File ID:**\n`{photo_id}`\n\n"
            f"🔄 از این به بعد در تمام بخش‌ها نمایش داده می‌شود."
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به پنل", callback_data="admin_panel", style=ButtonStyle.PRIMARY)]
        ])
        
        await message.reply_photo(
            photo=photo_id,
            caption=text,
            reply_markup=keyboard
        )
        return
    
    if db.get("temp_data", f"waiting_card_photo_{user_id}"):
        verification_data = {
            "user_id": user_id,
            "first_name": message.from_user.first_name or "",
            "username": message.from_user.username or "",
            "photo_id": message.photo.file_id,
            "timestamp": time.time(),
            "status": "pending"
        }
        
        db.set("verifications", user_id, verification_data)
        db.delete("temp_data", f"waiting_card_photo_{user_id}")
        
        admin_text = f"🆕 **درخواست احراز هویت جدید**\n\n"
        admin_text += f"👤 **کاربر:** {verification_data['first_name']}\n"
        admin_text += f"🆔 **آیدی:** `{user_id}`\n"
        admin_text += f"📧 **یوزرنیم:** @{verification_data['username']}\n"
        admin_text += f"⏰ **زمان:** {time.ctime()}"
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ تایید", callback_data=f"verify_approve_{user_id}", style=ButtonStyle.SUCCESS),
                InlineKeyboardButton("❌ رد", callback_data=f"verify_reject_{user_id}", style=ButtonStyle.DANGER)
            ]
        ])
        
        try:
            await message.forward(ADMIN_ID)
            await bot.send_message(ADMIN_ID, admin_text, reply_markup=keyboard)
            
            text = (
                "✅ **عکس شما دریافت شد و برای تایید به ادمین ارسال شد**\n\n"
                "⏳ لطفا منتظر تایید ادمین باشید\n"
                "🔔 پس از تایید به شما اطلاع داده خواهد شد"
            )
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back", style=ButtonStyle.DANGER)]
            ])
            
            photo_id = db.get_welcome_photo()
            if photo_id:
                await message.reply_photo(
                    photo=photo_id,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=enums.ParseMode.HTML
                )
            else:
                await message.reply_text(
                    text,
                    reply_markup=keyboard,
                    parse_mode=enums.ParseMode.HTML
                )
        except Exception as e:
            await message.reply_text("❌ خطا در ارسال به ادمین. لطفا بعدا تلاش کنید.")
        return
    
    elif db.get("temp_data", f"waiting_payment_proof_{user_id}"):
        payment_data = db.get("payments", user_id)
        if not payment_data:
            await message.reply_text("❌ اطلاعات پرداخت یافت نشد. لطفا دوباره تلاش کنید.")
            return
        
        payment_data["proof_photo_id"] = message.photo.file_id
        payment_data["proof_sent_at"] = time.time()
        db.set("payments", user_id, payment_data)
        
        admin_text = (
            f"💰 **درخواست افزایش موجودی جدید**\n\n"
            f"👤 **کاربر:** {message.from_user.first_name or 'ناشناس'}\n"
            f"🆔 **آیدی:** `{user_id}`\n"
            f"📧 **یوزرنیم:** @{message.from_user.username or 'ندارد'}\n"
            f"💎 **تعداد سکه:** {payment_data['coins']}\n"
            f"💵 **مبلغ:** {payment_data['toman']:,.0f} تومان\n"
            f"⏰ **زمان:** {time.ctime()}"
        )
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ تایید پرداخت", callback_data=f"payment_approve_{user_id}", style=ButtonStyle.SUCCESS),
                InlineKeyboardButton("❌ رد پرداخت", callback_data=f"payment_reject_{user_id}", style=ButtonStyle.DANGER)
            ]
        ])
        
        try:
            await message.forward(ADMIN_ID)
            await bot.send_message(ADMIN_ID, admin_text, reply_markup=keyboard)
            
            text = (
                "✅ **رسید پرداخت شما دریافت شد و برای تایید به ادمین ارسال شد**\n\n"
                "⏳ لطفا منتظر تایید ادمین باشید\n"
                "🔔 پس از تایید، سکه ها به حساب شما اضافه خواهد شد"
            )
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back", style=ButtonStyle.DANGER)]
            ])
            
            photo_id = db.get_welcome_photo()
            if photo_id:
                await message.reply_photo(
                    photo=photo_id,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=enums.ParseMode.HTML
                )
            else:
                await message.reply_text(
                    text,
                    reply_markup=keyboard,
                    parse_mode=enums.ParseMode.HTML
                )
            
            db.delete("temp_data", f"waiting_payment_proof_{user_id}")
            
        except Exception as e:
            await message.reply_text("❌ خطا در ارسال به ادمین. لطفا بعدا تلاش کنید.")
        return
async def _amain():
    """راه‌اندازی ربات به همراه بازیابی وضعیت و کارهای زمان‌بندی‌شده."""
    global BOT_LOOP
    BOT_LOOP = asyncio.get_running_loop()

    await bot.start()
    print("● ربات سلف ساز روشن شد ●")

    # پس از ری‌استارت، سلف‌های زنده دوباره شناسایی و تایمر شارژشان برقرار می‌شود
    restore_running_selfbots()

    background_tasks = []
    if config.HEALTH_REPORT_ENABLED:
        background_tasks.append(asyncio.create_task(health_monitor_loop()))

    try:
        await idle()
    finally:
        for task in background_tasks:
            task.cancel()
        await bot.stop()


def main():
    try:
        bot.run(_amain())
    except KeyboardInterrupt:
        print("\n🛑 توقف ربات...")
    except Exception as e:
        print(f"❌ خطا: {e}")
    finally:
        stop_all_selfbots()
        print("✅ ربات متوقف شد")

if __name__ == "__main__":
    main()
