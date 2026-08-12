from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent, InputMediaPhoto
from telegram.ext import Application, CallbackQueryHandler, ContextTypes, InlineQueryHandler, MessageHandler, filters, ChosenInlineResultHandler
import logging
import time
import json
import os
import asyncio

import config
from db import read_only_snapshot

config.require("HELPER_BOT_TOKEN")

TOKEN = config.HELPER_BOT_TOKEN
COMMAND_FILE = "selfbot_commands.json"
SETTINGS_FILE = "settings.json"
REACTION_RESULT_FILE = "reaction_result.json"
PANEL_IMAGE = config.PANEL_IMAGE or "link"
PHOTO_FILE = "panel_photo.json"
ADMIN_ID = config.ADMIN_ID
MANAGER_BOT_LINK = config.MANAGER_BOT_LINK

def save_photo_id(file_id):
    try:
        with open(PHOTO_FILE, 'w', encoding='utf-8') as f:
            json.dump({'photo_id': file_id}, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Error saving photo: {e}")
        return False

def get_photo_id():
    try:
        if os.path.exists(PHOTO_FILE):
            with open(PHOTO_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('photo_id')
        return None
    except Exception as e:
        print(f"Error loading photo: {e}")
        return None

def get_panel_photo():
    photo_id = get_photo_id()
    if photo_id:
        return photo_id
    return PANEL_IMAGE

def get_user_command_file(user_id):
    return f"selfbot_commands_{user_id}.json"

def get_user_settings_file(user_id):
    return f"settings_{user_id}.json"
async def check_selfbot_active(user_id):
    try:
        # خواندن پایگاه‌داده در ترد جدا تا حلقهٔ رویداد قفل نشود؛ خواندن امن که
        # اگر فایل در حال نوشتن باشد از نسخهٔ .bak استفاده می‌کند.
        data = await asyncio.to_thread(read_only_snapshot, config.DATABASE_FILE)
        users = data.get("users", {})
        processes = data.get("processes", {})

        user_data = users.get(str(user_id), {})
        process = processes.get(str(user_id))

        if user_data.get('status') == 'active' and process:
            return True, user_data.get('phone', '')
        return False, None
    except Exception as e:
        print(f"❌ خطا در بررسی سلف: {e}")
        return False, None

def send_command_to_self_bot(command, user_id):
    try:
        command_file = get_user_command_file(user_id)
        
        if not os.path.exists(command_file) or os.path.getsize(command_file) == 0:
            data = {'pending': False, 'command': '', 'user_id': user_id, 'timestamp': 0}
        else:
            with open(command_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        data['pending'] = True
        data['command'] = command
        data['user_id'] = user_id
        data['timestamp'] = time.time()
        
        with open(command_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"❌ خطا: {e}")
        return False

def load_settings(user_id):
    settings_file = f"settings_{user_id}.json"
    try:
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"📂 لود تنظیمات از {settings_file}: {data}") 
                return data
        print(f"⚠️ فایل {settings_file} وجود ندارد، ایجاد می‌شود")
        return {}
    except Exception as e:
        print(f"❌ خطا در load_settings: {e}")
        return {}

def save_settings(user_id, settings):
    settings_file = f"settings_{user_id}.json"
    try:
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
        print(f"💾 ذخیره تنظیمات در {settings_file}: {settings}") 
        return True
    except Exception as e:
        print(f"❌ خطا در save_settings: {e}")
        return False
async def handle_admin_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.photo:
            return
        
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            await update.message.reply_text("❌ شما اجازه این کار را ندارید!")
            return
        
        photo = update.message.photo[-1]
        file_id = photo.file_id
        
        if save_photo_id(file_id):
            await update.message.reply_text(
                "✅ عکس پنل با موفقیت ذخیره شد!\n"
                "🔹 فقط با file_id ذخیره شده"
            )
        else:
            await update.message.reply_text("❌ خطا در ذخیره عکس!")
            
    except Exception as e:
        print(f"❌ خطا: {e}")
        await update.message.reply_text(f"❌ خطا: {e}")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

CLOCK_SIMPLE_TEXT = """
⏰ <b>مدیریت ساعت و فونت</b>

لطفاً ساعت و یا فونت خود را مدیریت کنید.

🔹 برای فعال/غیرفعال کردن ساعت روی دکمه زیر کلیک کنید
🔹 برای تغییر فونت روی دکمه فونت کلیک کنید
"""
HELP_TEXTS = {
    "eavesdrop": """
👁 <b>شنود کاربران (Self Saz)</b>

<b>دستورات قابل کپی:</b>
روی پیام کاربر ریپلای کنید و بزنید:
<code>شنود</code>
<code>حذف شنود</code>
<code>لیست شنود</code>

<b>کاربرد:</b>
تمام پیام‌های کاربرِ هدف (متن/عکس/ویدیو/ویس) بلافاصله به
Saved Messages شما فوروارد می‌شود. برای رصد مخفیانهٔ گفتگوها.
""",
    "friends": """
💚 <b>مدیریت دوستان (Self Saz)</b>

<b>دستورات قابل کپی:</b>
روی پیام کاربر ریپلای کنید و بزنید:
<code>دوست</code>
<code>حذف دوست</code>
سایر دستورها:
<code>لیست دوست</code>
<code>پاک دوستان</code>

<b>کاربرد:</b>
لیست دوستان خود را نگه‌دارید (مکمل «مدیریت دشمنان»).
""",
    "sessions": """
📱 <b>نشست‌ها / گوشی‌ها (Self Saz)</b>

<b>دستورات قابل کپی:</b>
<code>نشست ها</code>
<code>پاک نشست ها</code>

<b>کاربرد:</b>
نمایش همهٔ دستگاه‌ها و نشست‌های فعالِ اکانت شما (مدل دستگاه،
اپلیکیشن، کشور). با «پاک نشست ها» همهٔ نشست‌ها به‌جز نشست فعلی
بسته می‌شوند — برای امنیت اکانت.
""",
    "readall": """
👀 <b>خواندن پیام‌ها (Self Saz)</b>

<b>دستورات قابل کپی:</b>
<code>خواندن همه</code>
<code>خواندن خودکار روشن</code>
<code>خواندن خودکار خاموش</code>

<b>کاربرد:</b>
«خواندن همه» همهٔ چت‌های نخوانده را یک‌جا خوانده می‌کند.
«خواندن خودکار» هر پیام جدید را بلافاصله می‌خواند (تیک دوم).
""",
    "afk": """
🤖 <b>منشی / پاسخ خودکار پیوی (Self Saz)</b>

<b>دستورات قابل کپی:</b>
<code>منشی روشن</code>
<code>منشی روشن الان در دسترس نیستم</code>
<code>منشی خاموش</code>

<b>کاربرد:</b>
وقتی روشن باشد، به هر پیام خصوصی به‌صورت خودکار (با فاصلهٔ زمانی)
پاسخ داده می‌شود. متن دلخواه را بعد از «منشی روشن» بنویسید.
""",
    "randfont": """
🔤 <b>فونت رندوم (Self Saz)</b>

<b>دستورات قابل کپی:</b>
<code>فونت رندوم روشن</code>
<code>فونت رندوم خاموش</code>

<b>کاربرد:</b>
هر پیامی که می‌فرستید، حروف لاتینش با یک فونت فانتزی تصادفی
نمایش داده می‌شود (𝐁𝐨𝐥𝐝 / 𝓼𝓬𝓻𝓲𝓹𝓽 / Ⓒⓘⓡⓒⓛⓔⓓ …).
""",
    "emojiclock": """
🕐 <b>ساعت ایموجی (Self Saz)</b>

<b>دستورات قابل کپی:</b>
<code>ساعت ایموجی روشن</code>
<code>ساعت ایموجی خاموش</code>

<b>کاربرد:</b>
کنار اسم شما یک ایموجی ساعت (🕐🕜…) متناسب با ساعت فعلی درج
می‌شود و هر دقیقه به‌روز می‌شود.
""",
    "calc": """
🧮 <b>حالت محاسبه (Self Saz)</b>

<b>دستورات قابل کپی:</b>
<code>محاسبه روشن</code>
<code>محاسبه خاموش</code>

<b>کاربرد:</b>
وقتی روشن باشد، هر پیامی که فقط یک عبارت ریاضی است
(مثل <code>12*8+5</code>) خودکار حل و به «۱۲*۸+۵ = ۱۰۱» تبدیل می‌شود.
""",
    "watch": """
👁 <b>رصد کاربران (Self VTR)</b>

<b>دستورات قابل کپی:</b>
روی پیام کاربر ریپلای کنید و بزنید:
<code>رصد</code>
<code>حذف رصد</code>
<code>لیست رصد</code>

<b>کاربرد:</b>
هر تغییری در اسم، یوزرنیم، بایو یا عکس پروفایل کاربرِ تحت رصد،
بلافاصله به Saved Messages شما اطلاع داده می‌شود.
""",
    "autoprofile": """
🎭 <b>پروفایل خودکار (Self VTR)</b>

<b>دستورات قابل کپی:</b>
<code>ست پروفایل اسم۱ | اسم۲ | اسم۳</code>
<code>پروفایل خودکار روشن</code>
<code>پروفایل خودکار خاموش</code>

<b>کاربرد:</b>
اسم پروفایل شما به‌صورت چرخشی بین اسم‌های تعیین‌شده تغییر می‌کند.
""",
    "time": """
⏰ <b>مدیریت ساعت</b>

<b>دستورات قابل کپی:</b>
<code>تایم روشن</code>
<code>تایم خاموش</code>

<b>کاربرد:</b>
نمایش زمان کنار نام کاربری
آپدیت خودکار هر دقیقه
فونت‌های مختلف برای زمان

<b>فونت‌های موجود (۱۵ فونت):</b>
𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗 - فونت 1
𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵 - فونت 2  
０１２３４５６７８９ - فونت 3
𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫 - فونت 4
𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡 - فونت 5
0҉1҉2҉3҉4҉5҉6҉7҉8҉9҉ - فونت 6
⓿❶❷❸❹❺❻❼❽❾ - فونت 7
⓪①②③④⑤⑥⑦⑧⑨ - فونت 8
0̷1̷2̷3̷4̷5̷6̷7̷8̷9̷ - فونت 9
【0】【1】【2】【3】【4】【5】【6】【7】【8】【9】 - فونت 10
0️⃣1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣8️⃣9️⃣ - فونت 11
𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿 - فونت 12
⓪⑴⑵⑶⑷⑸⑹⑺⑻⑼ - فونت 13
⁰¹²³⁴⁵⁶⁷⁸⁹ - فونت 14
₀₁₂₃₄₅₆₇₈₉ - فونت 15
""",
    "oneclick": """
⚡ <b>یک کلیک</b>

<b>مدیریت سریع با یک کلیک:</b>
• تنظیمات ساعت
• فرمت‌های متن

<b>کاربرد:</b>
با یک کلیک به تمام تنظیمات سریع دسترسی داشته باشید.
""",
    "dice": """
🎲 <b>سیستم تاس</b>

<b>دستورات قابل کپی:</b>
<code>تاس 6</code>
<code>تاس 5</code>
<code>تاس 4</code>
<code>تاس 3</code>
<code>تاس 2</code>
<code>تاس 1</code>
<code>تاس stop</code>

<b>کاربرد:</b>
• تنظیم عدد دلخواه برای تاس
• عدد بین 1 تا 6

<b>مثال:</b>
<code>تاس 6</code> - همیشه عدد 6 میاد
<code>تاس 1</code> - همیشه عدد 1 میاد

<b>نکته:</b>
فقط توی گروه و کانال ها کار میکنه
""",
    "instagram": """
📥 <b>دانلودر اینستاگرام</b>

<b>دستور قابل کپی:</b>
<code>اینستا لینک_پست</code>

<b>مثال‌ها:</b>
<code>اینستا https://www.instagram.com/reel/DOkym3fCFqg/</code>
<code>اینستا https://www.instagram.com/p/CzuF4KQqJ7q/</code>
<code>اینستا https://www.instagram.com/tv/Cxxxxxxxx/</code>

<b>کاربرد:</b>
• دانلود پست‌های اینستاگرام
• دانلود ریل‌ ها و ویدیو ها
• دانلود عکس‌های پست

<b>قابلیت‌ها:</b>
✅ دانلود با کیفیت اصلی
✅ نمایش توضیحات پست
✅ نمایش اطلاعات کاربر
✅ آپلود در همان چت
""",
    "id": """
🆔 <b>سیستم آیدی پیشرفته</b>

<b>دستور قابل کپی:</b>
<code>ایدی</code>

<b>دو حالت استفاده:</b>

1️⃣ <b>بدون ریپلای:</b>
<code>ایدی</code>
• نمایش اطلاعات خودتان
• نمایش اطلاعات چت فعلی
• نمایش آیدی عددی

2️⃣ <b>با ریپلای:</b>
<code>ایدی</code> (روی پیام کاربر ریپلای)
• نمایش اطلاعات کامل کاربر
• نمایش گروه‌های مشترک  
• نمایش آیدی و یوزرنیم

<b>اطلاعات نمایش داده شده:</b>
✅ آیدی عددی کاربر
✅ یوزرنیم و نام کامل
✅ وضعیت پریمیوم
✅ تعداد عکس‌های پروفایل
✅ آیدی چت و عنوان
✅ تعداد اعضا (در گروه)
✅ گروه‌های مشترک (در صورت وجود)
""",
    "photo": """
📸 <b>ذخیره عکس تایمدار</b>

<b>دستور قابل کپی:</b>
<code>عکس سیو</code> (ریپلای روی عکس)

<b>کاربرد:</b>
ذخیره دستی عکس‌های تایمدار
ارسال اطلاعات کامل کاربر

<b>نکته:</b>
فقط روی عکس‌های تایمدار کار می‌کند
عکس معمولی قابل ذخیره نیست
""",
    "backup": """
💾 <b>پشتیبان‌گیری</b>

<b>دستور قابل کپی:</b>
<code>سیو @یوزرنیم</code>

<b>مثال:</b>
<code>سیو @username</code>

<b>کاربرد:</b>
ذخیره تاریخچه چت در فایل متنی
ارسال فایل به پیام‌های ذخیره شده
""",
    "font": """
🔤 <b>مدیریت فونت</b>

<b>دستورات قابل کپی:</b>
<code>لیست فونت</code>
<code>تنظیم فونت 1</code> تا <code>تنظیم فونت 6</code>

<b>کاربرد:</b>
تغییر فونت نمایش زمان
پیش‌نمایش فونت‌های مختلف
اعمال فونت روی زمان به صورت زنده
""",
    "price": """
💱 <b>قیمت ارز</b>

<b>دستور قابل کپی:</b>
<code>قیمت ارز</code>

<b>مثال‌ها:</b>
<code>قیمت BTC</code>
<code>قیمت ETH</code>
<code>قیمت TON</code>

<b>کاربرد:</b>
نمایش قیمت لحظه‌ای ارزهای دیجیتال
نمایش قیمت تومانی و دلاری
نمایش تغییرات 24 ساعته
میتوانید اسم ارزو رو به فارسی بزارید
""",
    "spam": """
🔁 <b>ارسال اسپم</b>

<b>دستور قابل کپی:</b>
<code>اسپم تعداد متن</code>

<b>مثال‌ها:</b>
<code>اسپم 10 سلام</code>
<code>اسپم 5 تست</code>

<b>کاربرد:</b>
ارسال پیام تکراری
حداکثر 50 پیام در یک دستور
قابلیت ریپلای روی پیام
""",
    "format": """
🎨 <b>سیستم فرمت خودکار HTML</b>

<b>دستورات قابل کپی:</b>
<code>فرمت بولد روشن</code>
<code>فرمت بولد خاموش</code>
<code>فرمت ایتالیک روشن</code>
<code>فرمت ایتالیک خاموش</code>
<code>فرمت زیرخط روشن</code>
<code>فرمت زیرخط خاموش</code>
<code>فرمت خط‌خورده روشن</code>
<code>فرمت خط‌خورده خاموش</code>
<code>فرمت اسپویلر روشن</code>
<code>فرمت اسپویلر خاموش</code>
<code>فرمت کد روشن</code>
<code>فرمت کد خاموش</code>
<code>فرمت پیش‌فرمت روشن</code>
<code>فرمت پیش‌فرمت خاموش</code>
<code>فرمت نقل‌قول روشن</code>
<code>فرمت نقل‌قول خاموش</code>
<code>فرمت وضعیت</code>
<code>فرمت ریست</code>

<b>کاربرد:</b>
تبدیل خودکار پیام‌ ها به فرمت‌ های مختلف
پشتیبانی از تمام تگ‌های HTML تلگرام
امکان استفاده همزمان از چندین فرمت

<b>فرمت‌های پشتیبانی شده:</b>
• <b>بولد</b> - <b>متن بولد</b>
• <i>ایتالیک</i> - <i>متن ایتالیک</i>
• <u>زیرخط</u> - <u>متن زیرخط دار</u>
• <s>خط‌خورده</s> - <s>متن خط خورده</s>
• <code>کد</code> - <code>متن کد</code>
• <pre>پیش‌فرمت</pre> - <pre>متن پیش‌فرمت</pre>
• <blockquote>نقل‌قول</blockquote> - <blockquote>متن نقل قول</blockquote>
""",
    "enemy": """
👿 <b>مدیریت دشمنان</b>

<b>دستورات قابل کپی:</b>
<code>دشمن</code> (ریپلای روی پیام کاربر)
<code>حذف دشمن</code> (ریپلای روی پیام کاربر)
<code>لیست دشمن</code>
<code>دشمنان</code>
<code>پاک کردن دشمنان</code>

<b>کاربرد:</b>
افزودن کاربر به لیست دشمنان
ارسال خودکار فحش رندوم به دشمنان
مدیریت لیست دشمنان
نمایش اطلاعات کامل دشمنان
حذف دشمن از لیست
""",
    "autoreply": """
🤖 <b>پاسخ خودکار</b>

<b>دستورات قابل کپی:</b>
<code>پاسخ افزودن سلام|سلام چطوری</code>
<code>پاسخ حذف سلام</code>
<code>پاسخ لیست</code>

<b>مثال‌ها:</b>
<code>پاسخ افزودن سلا|سلام عزیزم</code>
<code>پاسخ افزودن چطوری|خوبم ممنون</code>
<code>پاسخ حذف سلا</code>

<b>کاربرد:</b>
تنظیم پاسخ خودکار برای کلمات خاص
لیست پاسخ‌ های تنظیم شده
""",
    "insult": """
💢 <b>مدیریت فحش‌ها</b>

<b>دستورات قابل کپی:</b>
<code>فحش افزودن متن فحش</code>
<code>فحش حذف متن فحش</code>

<b>مثال‌ها:</b>
<code>فحش افزودن تو احمقی</code>
<code>فحش افزودن برو گمشو</code>
<code>فحش حذف تو احمقی</code>

<b>کاربرد:</b>
افزودن فحش‌های جدید به لیست
حذف فحش ‌های موجود
ارسال رندوم فحش به دشمنان
""",
    "online": """
🌐 <b>حالت همیشه آنلاین</b>

<b>دستورات قابل کپی:</b>
<code>آنلاین روشن</code>
<code>آنلاین خاموش</code>

<b>کاربرد:</b>
فعال کردن حالت همیشه آنلاین
نمایش آنلاین دائمی در تلگرام
مناسب برای نشان دادن فعالیت دائمی
""",
    "lock": """
🔒 <b>سیستم قفل پیوی</b>

<b>دستورات قابل کپی:</b>
<code>همه روشن</code>
<code>همه خاموش</code>
<code>مدیا روشن</code>
<code>مدیا خاموش</code>
<code>استیکر روشن</code>
<code>استیکر خاموش</code>
<code>فوروارد روشن</code>
<code>فوروارد خاموش</code>
<code>وویس روشن</code>
<code>وویس خاموش</code>
<code>پیام روشن</code>
<code>پیام خاموش</code>
<code>فایل روشن</code>
<code>فایل خاموش</code>
<code>وضعیت قفل</code>
<code>ریست قفل</code>
<code>راهنمای قفل</code>

<b>کاربرد:</b>
محدود کردن ارسال انواع پیام در پیوی
حذف خودکار پیام‌های غیرمجاز
مدیریت دسترسی ‌های کاربران
نمایش وضعیت قفل ‌ها
""",
    "antilogin": """
🛡️ <b>سیستم انتی لاگین</b>

<b>دستورات قابل کپی:</b>
<code>انتی لاگین روشن</code>
<code>انتی لاگین خاموش</code>
<code>انتی لاگین</code>

<b>کاربرد:</b>
منقضی کردن کد اتوماتیک
جلوگیری از ورود به اکانت
""",
    "reaction": """
🎭 <b>سیستم ریکشن خودکار</b>

<b>دستورات قابل کپی:</b>
<code>ریکت ایموجی</code> (ریپلای روی کاربر)
<code>حذف ریکت</code> (ریپلای روی کاربر)
<code>لیست ریکت</code>
<code>پاکسازی ریکت</code>

<b>مثال‌ها:</b>
<code>ریکت 🚀</code> (ریپلای)
<code>ریکت ❤️</code> (ریپلای)
<code>حذف ریکت</code> (ریپلای)

<b>کاربرد:</b>
تنظیم ریکشن خودکار برای کاربران خاص
اعمال ریکشن روی تمام پیام‌ های کاربر
مدیریت لیست ریکشن‌ ‌ها
حذف ریکشن کاربران
""",
    "edit": """
✏️ <b>ویرایش سریع پیام</b>

<b>دستور قابل کپی:</b>
<code>ویرایش کلمه_قدیمی به کلمه_جدید</code> (ریپلای)

<b>مثال‌ها:</b>
<code>ویرایش سلان به سلام</code>
<code>ویرایش احمق به عزیز</code>
<code>ویرایش بد به خوب</code>

<b>کاربرد:</b>
جایگزینی سریع کلمه در پیام
ریپلای روی پیام مورد نظر
حذف خودکار پیام دستور
جایگزینی فقط کلمه مشخص شده
""",
    "banner": """
📢 <b>سیستم مدیریت بنر</b>

<b>دستورات قابل کپی:</b>
<code>تنظیم بنر</code> (ریپلای روی پیام)
<code>لیست بنرها</code>
<code>بنر همگانی کد</code>
<code>بنر همگانی خاموش</code>
<code>بنر ارسال کد</code>
<code>زمان بنر دقیقه</code>
<code>حذف بنر کد</code> 
<code>پاکسازی بنرها</code> 

<b>مثال‌ها:</b>
<code>تنظیم بنر</code> (ریپلای)
<code>بنر همگانی 1</code>
<code>بنر ارسال 1</code>
<code>زمان بنر 5</code>
<code>حذف بنر 1</code> 
<code>پاکسازی بنرها</code> 

<b>کاربرد:</b>
• ثبت پیام به عنوان بنر
• ارسال همگانی به گروه‌ها و سوپرگروه‌ها
• مدیریت بنرهای ثبت شده
• تنظیم زمان بین ارسال‌ها
• ارسال فوری بنر
• <b>حذف بنر خاص</b> 
• <b>پاکسازی همه بنر ها</b>

<b>نکته:</b>
برای حذف بنر، ابتدا با دستور <code>لیست بنرها</code> کد بنر رو پیدا کنید.
""",
    "download": """
📥 <b>دانلودر تلگرام</b>

<b>دستور قابل کپی:</b>
<code>دانلود لینک_پست</code>

<b>مثال‌ها:</b>
<code>دانلود https://t.me/channel/123</code>
<code>دانلود https://t.me/username/456</code>
<code>دانلود https://t.me/c/channel_id/post_id</code>

💡 <b>کاربرد اصلی:</b>
دانلود پست کانال های اسکم یا گروه ها
""",
    "new": """
🆕 <b>دستورات مربوط به کانال و گروه</b>

<b>دستورات قابل کپی:</b>
<code>پینگ</code>
<code>تعداد کانال ها</code>
<code>تعداد گروه ها</code>
<code>خروج همه کانال</code>
<code>خروج همه گروه</code>

<b>کاربرد:</b>
• <code>پینگ</code> - بررسی سرعت ربات
• <code>تعداد کانال ها</code> - نمایش آمار دقیق کانال‌ها
• <code>تعداد گروه ها</code> - نمایش آمار دقیق گروه‌ها
• <code>خروج همه کانال</code> - خروج از تمام کانال‌ها با تاخیر
• <code>خروج همه گروه</code> - خروج از تمام گروه‌ها با تاخیر

<b>نکته:</b>
تاخیر 4 ثانیه‌ ای برای جلوگیری از محدودیت
""",
    "pishi": """
🐱 <b>سیستم پیشی (میو پوینت)</b>

<b>دستورات قابل کپی:</b>
<code>پیشی شروع</code>
<code>پیشی stop</code>
<code>پیشی status</code>
<code>پیشی بگیر</code>
<code>پیشی کمک</code>

<b>کاربرد:</b>
• برداشت خودکار میو پوینت
• محاسبه دقیق زمان برداشت
• ذخیره تسک‌ها در فایل
• تلاش مجدد در صورت خطا
• نمایش آمار برداشت‌ها

<b>نحوه کار:</b>
1. اطلاعات پیشی دریافت می‌شود
2. زمان پر شدن ظرفیت محاسبه می‌شود
3. برداشت خودکار در زمان دقیق
4. محاسبه زمان برداشت بعدی
""",
    "mewo": """
🐱 <b>تایمر میو</b>

<b>دستورات قابل کپی:</b>
<code>میو 5 دقیقه</code>
<code>میو stop</code>
<code>میو status</code>
<code>میو help</code>

<b>مثال‌ها:</b>
<code>میو 5 دقیقه</code> - هر 5 دقیقه
<code>میو 4.30 دقیقه</code> - هر 4.5 دقیقه
<code>میو 0.5 دقیقه</code> - هر 30 ثانیه

<b>کاربرد:</b>
• ارسال خودکار میو
• تکرار بی‌نهایت
• تنظیم زمان دلخواه
• نمایش وضعیت تایمرها
• ارسال فوری اولین میو
""",
    "schedule": """
📅 <b>پیام زمان‌دار</b>

<b>دستورات قابل کپی:</b>
<code>ارسال 15:30 متن</code>
<code>ارسال 15:30:15 متن</code>
<code>لیست زمان‌دار</code>
<code>حذف زمان‌دار کد</code>
<code>پاکسازی زمان‌دار</code>

<b>مثال‌ها:</b>
<code>ارسال 15:30 سلام به همه</code>
<code>ارسال 15:30:15 پیام دقیق</code>
<code>ارسال 15:30 بولد سلام</code>

<b>کاربرد:</b>
• برنامه‌ریزی ارسال پیام
• پشتیبانی از فرمت‌ها
• ریپلای به پیام خاص
• ذخیره‌سازی خودکار
• نمایش لیست پیام‌ها
""",
    "action": """
🎭 <b>مدیریت اکشن‌ها</b>

<b>دستورات قابل کپی:</b>
<code>اکشن لیست</code>
<code>اکشن تایپ روشن</code>
<code>اکشن تایپ خاموش</code>
<code>اکشن وضعیت</code>
<code>اکشن ریست</code>

<b>اکشن‌های موجود:</b>
• تایپ - ⌨️
• اپلود عکس - 📸
• ضبط ویس - 🎤
• اپلود ویدیو - 🎥
• اپلود فایل - 📄
• ضبط ویدیو - 🎬
• اپلود ویس - 🎵
• اپلود ویدیو نوت - 📹
• ضبط ویدیو نوت - 🎞️
• بازی - 🎮
• انتخاب مخاطب - 👤
• پیدا کردن موقعیت - 📍
• انتخاب استیکر - 🎨

<b>کاربرد:</b>
نمایش اکشن خودکار هنگام دریافت پیام
""",
    "group": """
🛠️ <b>دستورات مدیریت گروه</b>

<b>دستورات قابل کپی:</b>
<code>بن</code> (ریپلای)
<code>آنبن @username</code>
<code>کیک</code> (ریپلای)
<code>سکوت</code> (ریپلای)
<code>حذف سکوت</code> (ریپلای)
<code>ادمین</code> (ریپلای)
<code>حذف ادمین</code> (ریپلای)
<code>پاک تعداد</code>
<code>پین</code> (ریپلای)
<code>آنپین</code> (ریپلای)
<code>تنظیم عنوان متن</code>
<code>تنظیم توضیحات متن</code>
<code>تنظیم عکس</code> (ریپلای عکس)
<code>اطلاعات گروه</code>
<code>لیست ادمین</code>
<code>تعداد اعضا</code>
<code>اهسته روشن</code>
<code>اهسته خاموش</code>

<b>کاربرد:</b>
مدیریت کامل گروه‌ها و سوپرگروه‌ها
""",
    "fun": """
🎉 <b>سرگرمی</b>

<b>دستورات قابل کپی:</b>
<code>فال</code>
<code>سکه</code>
<code>گوی سوال شما</code>
<code>جوک</code>
<code>نقل</code>
<code>شمارش 10</code>

<b>کاربرد:</b>
فال حافظ، شیر یا خط، گوی جادویی (پاسخ بله/خیر)،
جوک و نقل‌قول تصادفی، و شمارش معکوس زنده.
""",
    "texttools": """
🔤 <b>ابزار متن</b>

<b>دستورات قابل کپی:</b>
<code>برعکس متن شما</code>
<code>فاصله متن شما</code>
<code>تکرار 3 متن شما</code>
<code>تلگرافی متن شما</code>
<code>حساب 2+3*4</code>

<b>کاربرد:</b>
معکوس‌کردن متن، فاصله‌گذاری حروف، تکرار متن،
افکت تایپ زنده (تلگرافی) و ماشین‌حساب امن.
""",
    "profiletools": """
👤 <b>مدیریت پروفایل</b>

<b>دستورات قابل کپی:</b>
<code>اسم نام جدید</code>
<code>فامیل نام خانوادگی</code>
<code>فامیل</code> (برای حذف نام خانوادگی)
<code>بیو متن بایو</code>

<b>کاربرد:</b>
تغییر سریع نام، نام خانوادگی و بایوی اکانت.
""",
    "timetools": """
🕐 <b>زمان و وضعیت</b>

<b>دستورات قابل کپی:</b>
<code>ساعت</code>
<code>تاریخ</code>
<code>وضعیت سلف</code>
<code>پینگ</code>

<b>کاربرد:</b>
نمایش ساعت و تاریخ (میلادی/شمسی)، آپ‌تایم و پینگ سلف.
""",
    "translate": """
🌐 <b>مترجم</b>

<b>دستورات قابل کپی:</b>
<code>مترجم متن مورد نظر</code>
<code>مترجم en متن فارسی</code>

<b>کاربرد:</b>
ترجمهٔ خودکار متن به فارسی (یا هر زبان با کد دو حرفی مثل en, ar).
""",
    "poll": """
📊 <b>نظرسنجی</b>

<b>دستورات قابل کپی:</b>
<code>نظرسنجی سوال | گزینه۱ | گزینه۲ | گزینه۳</code>

<b>کاربرد:</b>
ساخت نظرسنجی در گروه با جداکنندهٔ «|» (حداکثر ۱۰ گزینه).
""",
    "purge": """
🧹 <b>پاکسازی پیام‌های من</b>

<b>دستورات قابل کپی:</b>
<code>پاک من 10</code>

<b>کاربرد:</b>
حذف آخرین پیام‌های خودتان در همین چت (حداکثر ۱۰۰ پیام).
""",
    "extra": """
🧰 <b>ابزارهای تکمیلی (SelfSaz)</b>

<b>دستورات قابل کپی:</b>
<code>کپی</code> (ریپلای)
<code>بلاک @username</code> / <code>آنبلاک @username</code>
<code>یوزرنیم تنظیم myname</code>
<code>یوزرنیم @username</code>
<code>کارت تنظیم 6037xxxxxxxxxxxx نام صاحب</code>
<code>کارت</code> / <code>کارت حذف</code>
<code>یونیکس 1700000000</code>
<code>سن 1380</code>
<code>کلمه سلام دنیا</code>
<code>اسمم</code> / <code>شماره من</code>
<code>ایدی گروه</code>

<b>کاربرد:</b>
کپی پیام، بلاک/آنبلاک، تنظیم یوزرنیم و شماره کارت،
تبدیل زمان یونیکس، محاسبهٔ سن، ارسال کلمه‌به‌کلمه و اطلاعات حساب.
"""
}

def get_font_preview(font_num):
    sample = "12:34"
    fonts = {
        1: "".join(["𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗"[int(d)] if d.isdigit() else d for d in sample]),
        2: "".join(["𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"[int(d)] if d.isdigit() else d for d in sample]),
        3: "".join(["０１２３４５６７８９"[int(d)] if d.isdigit() else d for d in sample]),
        4: "".join(["𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫"[int(d)] if d.isdigit() else d for d in sample]),
        5: "".join(["𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡"[int(d)] if d.isdigit() else d for d in sample]),
        6: "".join(["0҉1҉2҉3҉4҉5҉6҉7҉8҉9҉"[int(d)*2:(int(d)*2)+2] if d.isdigit() else d for d in sample]),
        7: "".join(["⓿❶❷❸❹❺❻❼❽❾"[int(d)] if d.isdigit() else d for d in sample]),
        8: "".join(["⓪①②③④⑤⑥⑦⑧⑨"[int(d)] if d.isdigit() else d for d in sample]),
        9: "".join(["0̷1̷2̷3̷4̷5̷6̷7̷8̷9̷"[int(d)*2:(int(d)*2)+2] if d.isdigit() else d for d in sample]),
        10: "".join(["【0】【1】【2】【3】【4】【5】【6】【7】【8】【9】"[int(d)*4:(int(d)*4)+4] if d.isdigit() else d for d in sample]),
        11: "".join(["0️⃣1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣8️⃣9️⃣"[int(d)*3:(int(d)*3)+3] if d.isdigit() else d for d in sample]),
        12: "".join(["𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿"[int(d)] if d.isdigit() else d for d in sample]),
        13: "".join(["⓪⑴⑵⑶⑷⑸⑹⑺⑻⑼"[int(d)*3:(int(d)*3)+3] if d.isdigit() else d for d in sample]),
        14: "".join(["⁰¹²³⁴⁵⁶⁷⁸⁹"[int(d)] if d.isdigit() else d for d in sample]),
        15: "".join(["₀₁₂₃₄₅₆₇₈₉"[int(d)] if d.isdigit() else d for d in sample])
    }
    return fonts.get(font_num, sample)

def get_font_buttons(user_id, from_page=1):
    settings = load_settings(user_id) 
    current_font = settings.get('font', 1)
    keyboard = [
        [
            InlineKeyboardButton(
                " 𝟏𝟐:𝟑𝟒", 
                callback_data=f"font_1_{user_id}_{from_page}",
                style="success" if current_font == 1 else "danger"
            ),
            InlineKeyboardButton(
                " 𝟭𝟮:𝟯𝟰", 
                callback_data=f"font_2_{user_id}_{from_page}",
                style="success" if current_font == 2 else "danger"
            )
        ],
        [
            InlineKeyboardButton(
                " １２:３４", 
                callback_data=f"font_3_{user_id}_{from_page}",
                style="success" if current_font == 3 else "danger"
            ),
            InlineKeyboardButton(
                " 𝟣𝟤:𝟥𝟦", 
                callback_data=f"font_4_{user_id}_{from_page}",
                style="success" if current_font == 4 else "danger"
            )
        ],
        [
            InlineKeyboardButton(
                " 𝟙𝟚:𝟛𝟜", 
                callback_data=f"font_5_{user_id}_{from_page}",
                style="success" if current_font == 5 else "danger"
            ),
            InlineKeyboardButton(
                " 1҉2҉:3҉4҉", 
                callback_data=f"font_6_{user_id}_{from_page}",
                style="success" if current_font == 6 else "danger"
            )
        ],
        [
            InlineKeyboardButton(
                " ⓿❶:❷❸", 
                callback_data=f"font_7_{user_id}_{from_page}",
                style="success" if current_font == 7 else "danger"
            ),
            InlineKeyboardButton(
                " ①⑧:③④", 
                callback_data=f"font_8_{user_id}_{from_page}",
                style="success" if current_font == 8 else "danger"
            )
        ],
        [
            InlineKeyboardButton(
                " 1̷2̷:3̷4̷", 
                callback_data=f"font_9_{user_id}_{from_page}",
                style="success" if current_font == 9 else "danger"
            ),
            InlineKeyboardButton(
                " 【1】【2】", 
                callback_data=f"font_10_{user_id}_{from_page}",
                style="success" if current_font == 10 else "danger"
            )
        ],
        [
            InlineKeyboardButton(
                " 1️⃣2️⃣", 
                callback_data=f"font_11_{user_id}_{from_page}",
                style="success" if current_font == 11 else "danger"
            ),
            InlineKeyboardButton(
                " 𝟷𝟸:𝟹𝟺", 
                callback_data=f"font_12_{user_id}_{from_page}",
                style="success" if current_font == 12 else "danger"
            )
        ],
        [
            InlineKeyboardButton(
                " ⑴⑵:⑶⑷", 
                callback_data=f"font_13_{user_id}_{from_page}",
                style="success" if current_font == 13 else "danger"
            ),
            InlineKeyboardButton(
                " ¹²:³⁴", 
                callback_data=f"font_14_{user_id}_{from_page}",
                style="success" if current_font == 14 else "danger"
            )
        ],
        [
            InlineKeyboardButton(
                " ₁₂:₃₄", 
                callback_data=f"font_15_{user_id}_{from_page}",
                style="success" if current_font == 15 else "danger"
            )
        ],
        [
            InlineKeyboardButton(
                "بازگشت به ساعت", 
                callback_data=f"clock_back_{user_id}_{from_page}",
                style="primary"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_clock_buttons(user_id, page=1):
    settings = load_settings(user_id)
    time_status = settings.get('time_status', 'خاموش')
    font_status = settings.get('font', 1)
    
    logger.info(f"🎯 get_clock_buttons - user_id: {user_id}, time_status: {time_status}") 
    
    font_preview = get_font_preview(int(font_status))
    
    if time_status == "روشن":
        button_text = "✔️ ساعت"
        button_style = "success"
    else:
        button_text = "✖️ ساعت"
        button_style = "danger"
    
    keyboard = [
        [
            InlineKeyboardButton(
                button_text,
                callback_data=f"toggle_{user_id}_{page}",
                style=button_style
            )
        ],
        [
            InlineKeyboardButton(
                f"🔤 فونت: {font_preview}", 
                callback_data=f"help_fonts_{user_id}_{page}",
                style="primary"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت", 
                callback_data=f"oneclick_back_{user_id}_{page}",
                style="primary"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_oneclick_buttons(user_id, from_page=1):
    keyboard = [
        [
            InlineKeyboardButton("مدیریت ساعت", callback_data=f"oneclick_time_{user_id}_{from_page}", style="success"),
            InlineKeyboardButton("فرمت متن", callback_data=f"oneclick_format_{user_id}_{from_page}", style="primary")
        ],
        [
            InlineKeyboardButton("🔙", callback_data=f"help_back_{user_id}_{from_page}", style="danger")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_format_buttons(user_id, from_page=1):
    settings = load_settings(user_id)
    format_settings = settings.get('formats', {})
    
    keyboard = []
    
    formats = [
        ("بولد", "bold"),
        ("ایتالیک", "italic"),
        ("زیرخط", "underline"),
        ("خط‌خورده", "s"), 
        ("اسپویلر", "spoiler"),
        ("کد", "code"),
        ("پیش‌فرمت", "pre"),
        ("نقل‌قول", "quote")
    ]
    
    row = []
    for i, (name, key) in enumerate(formats):
        status = format_settings.get(key, False)
        emoji = "✅" if status else "⬜"
        row.append(InlineKeyboardButton(
            f"{emoji} {name}", 
            callback_data=f"format_{key}_{user_id}_{from_page}"
        ))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([
        InlineKeyboardButton("ریست همه فرمت‌ها", callback_data=f"format_reset_{user_id}_{from_page}"),
        InlineKeyboardButton("وضعیت فرمت‌ها", callback_data=f"format_status_{user_id}_{from_page}")
    ])
    keyboard.append([
        InlineKeyboardButton("🔙", callback_data=f"oneclick_back_{user_id}_{from_page}")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_main_menu(user_id):
    """پنل تک‌صفحه‌ای شامل همهٔ دسترسی‌ها (بدون صفحه‌بندی و بدون زیرمنوی جدا)."""
    settings = load_settings(user_id)
    adv = settings.get('advanced', {})

    def mark(key):
        return "✅" if adv.get(key) else "⬜️"

    keyboard = [
        [
            InlineKeyboardButton("ایدی", callback_data=f"help_id_{user_id}_1", style="success"),
            InlineKeyboardButton("یک کلیک", callback_data=f"help_oneclick_{user_id}_1", style="success")
        ],
        [
            InlineKeyboardButton("عکس تایمدار", callback_data=f"help_photo_{user_id}_1", style="danger"),
            InlineKeyboardButton("پشتیبان‌گیری", callback_data=f"help_backup_{user_id}_1", style="danger")
        ],
        [
            InlineKeyboardButton("مدیریت فونت", callback_data=f"help_font_{user_id}_1", style="primary"),
            InlineKeyboardButton("قیمت ارز", callback_data=f"help_price_{user_id}_1", style="primary")
        ],
        [
            InlineKeyboardButton("فرمت متن", callback_data=f"help_format_{user_id}_1", style="success"),
            InlineKeyboardButton("اسپم", callback_data=f"help_spam_{user_id}_1", style="success")
        ],
        [
            InlineKeyboardButton("مدیریت دشمنان", callback_data=f"help_enemy_{user_id}_1", style="danger"),
            InlineKeyboardButton("پاسخ خودکار", callback_data=f"help_autoreply_{user_id}_1", style="danger")
        ],
        [
            InlineKeyboardButton("تاس", callback_data=f"help_dice_{user_id}_1", style="success"),
            InlineKeyboardButton("سیستم پیشی", callback_data=f"help_pishi_{user_id}_1", style="success")
        ],
        [
            InlineKeyboardButton("سیستم فحش", callback_data=f"help_insult_{user_id}_1", style="success"),
            InlineKeyboardButton("همیشه آنلاین", callback_data=f"help_online_{user_id}_1", style="success")
        ],
        [
            InlineKeyboardButton("قفل پیوی", callback_data=f"help_lock_{user_id}_1", style="danger"),
            InlineKeyboardButton("انتی لاگین", callback_data=f"help_antilogin_{user_id}_1", style="danger")
        ],
        [
            InlineKeyboardButton("ریکشن خودکار", callback_data=f"help_reaction_{user_id}_1", style="primary"),
            InlineKeyboardButton("ویرایش سریع", callback_data=f"help_edit_{user_id}_1", style="primary")
        ],
        [
            InlineKeyboardButton("سیستم بنر", callback_data=f"help_banner_{user_id}_1", style="success"),
            InlineKeyboardButton("اینستاگرام", callback_data=f"help_instagram_{user_id}_1", style="success")
        ],
        [
            InlineKeyboardButton("دانلود تلگرام", callback_data=f"help_download_{user_id}_1", style="danger"),
            InlineKeyboardButton("مدیریت گروه/کانال", callback_data=f"help_new_{user_id}_1", style="danger")
        ],
        [
            InlineKeyboardButton("تایمر میو", callback_data=f"help_mewo_{user_id}_1", style="primary"),
            InlineKeyboardButton("پیام زمان‌دار", callback_data=f"help_schedule_{user_id}_1", style="primary")
        ],
        [
            InlineKeyboardButton("مدیریت اکشن", callback_data=f"help_action_{user_id}_1", style="success"),
            InlineKeyboardButton("مدیریت گروه", callback_data=f"help_group_{user_id}_1", style="success")
        ],
        [InlineKeyboardButton(f"{mark('bio_time')} ساعت در بایو", callback_data=f"adv_biotime_{user_id}_1", style="primary")],
        [InlineKeyboardButton(f"{mark('save_deleted')} ذخیره حذفیات", callback_data=f"adv_savedel_{user_id}_1", style="primary")],
        [InlineKeyboardButton(f"{mark('save_edited')} ذخیره ویرایش‌ها", callback_data=f"adv_saveedit_{user_id}_1", style="primary")],
        [
            InlineKeyboardButton("رصد کاربران", callback_data=f"help_watch_{user_id}_1", style="success"),
            InlineKeyboardButton("پروفایل خودکار", callback_data=f"help_autoprofile_{user_id}_1", style="success")
        ],
        [InlineKeyboardButton("انقضا / زمان باقی‌مانده", callback_data=f"adv_expiry_{user_id}_1", style="danger")],
        [InlineKeyboardButton(f"{mark('afk')} منشی (پاسخ خودکار پیوی)", callback_data=f"adv_afk_{user_id}_1", style="primary")],
        [InlineKeyboardButton(f"{mark('auto_read')} خواندن خودکار همه", callback_data=f"adv_autoread_{user_id}_1", style="primary")],
        [
            InlineKeyboardButton(f"{mark('random_font')} فونت رندوم", callback_data=f"adv_randfont_{user_id}_1", style="secondary"),
            InlineKeyboardButton(f"{mark('emoji_clock')} ساعت ایموجی", callback_data=f"adv_emojiclock_{user_id}_1", style="secondary")
        ],
        [InlineKeyboardButton(f"{mark('calc_mode')} حالت محاسبه", callback_data=f"adv_calc_{user_id}_1", style="warning")],
        [
            InlineKeyboardButton("👁 شنود کاربران", callback_data=f"help_eavesdrop_{user_id}_1", style="danger"),
            InlineKeyboardButton("💚 دوستان", callback_data=f"help_friends_{user_id}_1", style="success")
        ],
        [
            InlineKeyboardButton("📱 نشست‌ها / گوشی‌ها", callback_data=f"help_sessions_{user_id}_1", style="danger"),
            InlineKeyboardButton("👀 خواندن همه چت‌ها", callback_data=f"help_readall_{user_id}_1", style="primary")
        ],
        [
            InlineKeyboardButton("🎉 سرگرمی", callback_data=f"help_fun_{user_id}_1", style="warning"),
            InlineKeyboardButton("🔤 ابزار متن", callback_data=f"help_texttools_{user_id}_1", style="warning")
        ],
        [
            InlineKeyboardButton("👤 مدیریت پروفایل", callback_data=f"help_profiletools_{user_id}_1", style="secondary"),
            InlineKeyboardButton("🕐 زمان و وضعیت", callback_data=f"help_timetools_{user_id}_1", style="secondary")
        ],
        [
            InlineKeyboardButton("🌐 مترجم", callback_data=f"help_translate_{user_id}_1", style="primary"),
            InlineKeyboardButton("📊 نظرسنجی", callback_data=f"help_poll_{user_id}_1", style="primary")
        ],
        [
            InlineKeyboardButton("🧹 پاکسازی پیام‌های من", callback_data=f"help_purge_{user_id}_1", style="danger"),
            InlineKeyboardButton("🧰 ابزار تکمیلی", callback_data=f"help_extra_{user_id}_1", style="warning")
        ],
        [InlineKeyboardButton("❌ بستن", callback_data=f"close_{user_id}", style="danger")],
    ]
    return InlineKeyboardMarkup(keyboard)


# سازگاری با فراخوانی‌های قدیمی: همهٔ صفحه‌ها به پنل تک‌صفحه‌ای اشاره می‌کنند.
def get_main_menu_page1(user_id):
    return get_main_menu(user_id)


def get_main_menu_page2(user_id):
    return get_main_menu(user_id)

def get_back_button(user_id, from_page=1):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙", callback_data=f"help_back_{user_id}_{from_page}")]
    ])

def get_reopen_button(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅", callback_data=f"reopen_{user_id}")]
    ])
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    is_active, phone = await check_selfbot_active(user_id)
    
    if not is_active:
        await update.message.reply_text(
            "⛔ **شما سلف بات فعال ندارید!**\n\n"
            "برای استفاده از پنل هلپر، ابتدا باید سلف بات خود را در ربات مدیریت فعال کنید.\n\n"
            "🔹 **مراحل فعالسازی:**\n"
            "1️⃣ به ربات سلف ساز بروید\n"
            "2️⃣ روی دکمه «فعالسازی» کلیک کنید\n"
            "3️⃣ شماره خود را وارد کنید\n"
            "4️⃣ سلف بات را روشن کنید\n\n"
            "✅ پس از فعال شدن سلف، دکمه «بررسی مجدد» را بزنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 بررسی مجدد", callback_data=f"check_selfbot_{user_id}")],
                [InlineKeyboardButton("🔗 رفتن به ربات سلف ساز", url=MANAGER_BOT_LINK)]
            ])
        )
        return
   
    text = "<b>🎛 پنل مدیریت سلف</b>\n\n💡 <i>همهٔ قابلیت‌ها در یک صفحه</i>"
    photo = get_panel_photo()
    
    await update.message.reply_photo(
        photo=photo,
        caption=text,
        reply_markup=get_main_menu(user_id),
        parse_mode='HTML'
    )
async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.inline_query.query.strip().lower()
        user_id = update.inline_query.from_user.id
        is_active, phone = await check_selfbot_active(user_id)        
        if not is_active:
            result = InlineQueryResultArticle(
                id="error",
                title="⛔ سلف فعال نیست!",
                description="لطفا ابتدا سلف بات را فعال کنید",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "⛔ شما سلف بات فعال ندارید!\n\n"
                        "برای استفاده از پنل هلپر، ابتدا سلف بات خود را فعال کنید.\n\n"
                        "🔹 به ربات سلف ساز بروید و سلف را روشن کنید."
                    ),
                    parse_mode='HTML'
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔗 رفتن به ربات سلف ساز", url=MANAGER_BOT_LINK)]
                ]),
                thumbnail_url=PANEL_IMAGE
            )
            await update.inline_query.answer([result], cache_time=0, is_personal=True)
            return
        
        if query == "panel":
            result1 = InlineQueryResultArticle(
                id="1",
                title="🎛 پنل مدیریت سلف",
                description="همهٔ قابلیت‌ها در یک صفحه",
                input_message_content=InputTextMessageContent(
                    message_text="<b>🎛 پنل مدیریت سلف</b>",
                    parse_mode='HTML'
                ),
                reply_markup=get_main_menu(user_id),
                thumbnail_url=PANEL_IMAGE
            )

            await update.inline_query.answer([result1], cache_time=0, is_personal=True)
            logger.info(f"✅ نتایج اینلاین ارسال شد")
            
    except Exception as e:
        logger.error(f"❌ خطا: {e}")

async def handle_chosen_inline_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        logger.info("🔄 شروع handle_chosen_inline_result")
        
        result = update.chosen_inline_result
        user_id = result.from_user.id
        result_id = result.result_id
        inline_message_id = result.inline_message_id
        
        if not inline_message_id:
            logger.warning("⚠️ inline_message_id موجود نیست!")
            return
        
        photo = get_panel_photo()
        await asyncio.sleep(1)
        text = "<b>🎛 پنل مدیریت سلف</b>"
        await context.bot.edit_message_media(
            media=InputMediaPhoto(media=photo, caption=text, parse_mode='HTML'),
            inline_message_id=inline_message_id,
            reply_markup=get_main_menu(user_id)
        )
        logger.info(f"✅ پنل با عکس ادیت شد برای کاربر {user_id}")
            
    except Exception as e:
        logger.error(f"❌ خطا در handle_chosen_inline_result: {e}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data or ""
    user_id = query.from_user.id
    photo = get_panel_photo()

    # دکمه‌های موقت بدون شناسه کاربر
    if data == "wait":
        await query.answer("⏳ لطفا صبر کنید...")
        return

    # دکمهٔ «بررسی مجدد» وقتی سلف فعال نیست
    if data.startswith("check_selfbot_"):
        await query.answer()
        active, phone = await check_selfbot_active(user_id)
        if active:
            await query.edit_message_text("✅ سلف شما فعال است! پنل را دوباره باز کنید.")
        else:
            await query.answer("❌ سلف شما هنوز فعال نیست. ابتدا در ربات سلف‌ساز لاگین کنید.", show_alert=True)
        return

    # کنترل دسترسی: کاربر فقط دکمه‌های خودش را می‌بیند (یک بار answer)
    if f"_{user_id}" not in data:
        await query.answer("❌ دسترسی غیرمجاز!", show_alert=True)
        return

    await query.answer()

    parts = data.split("_")
    if len(parts) >= 2:
        action = parts[0]
        # نکتهٔ باگ قبلی: برای *_back مقدار page از parts[2] (که در واقع user_id
        # است) خوانده می‌شد. page همیشه آخرین بخش است.
        if parts[0] == "help" and parts[1] == "back":
            action = "help_back"
            page = int(parts[-1]) if parts[-1].isdigit() else 1
        elif parts[0] == "clock" and parts[1] == "back":
            action = "clock_back"
            page = int(parts[-1]) if parts[-1].isdigit() else 1
        elif parts[0] == "oneclick" and parts[1] == "back":
            action = "oneclick_back"
            page = int(parts[-1]) if parts[-1].isdigit() else 1
        else:
            page = int(parts[-1]) if parts[-1].isdigit() else 1
    else:
        action = parts[0]
        page = 1
    
    if action == "toggle":

        settings = load_settings(user_id)
        current_status = settings.get('time_status', 'خاموش')
        logger.info(f"📊 وضعیت فعلی: {current_status}")

        if current_status == "روشن":
            new_status = "خاموش"
            send_command_to_self_bot("تایم خاموش", user_id)
        else:
            new_status = "روشن"
            send_command_to_self_bot("تایم روشن", user_id)

        logger.info(f"🔄 وضعیت جدید: {new_status}")

        settings['time_status'] = new_status
        save_settings(user_id, settings)
    
        test_load = load_settings(user_id)
        logger.info(f"📂 تست لود بعد از ذخیره: {test_load.get('time_status', 'ندارد')}")

        try:
            temp_text = f"✅ <b>ساعت {new_status} شد</b>"
            temp_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("⏳ در حال بازگشت...", callback_data="wait", style="primary")]
            ])
        
            await query.edit_message_media(
                media=InputMediaPhoto(media=photo, caption=temp_text, parse_mode='HTML'),
                reply_markup=temp_keyboard
            )
        
            await asyncio.sleep(1)
        
            settings = load_settings(user_id)
            logger.info(f"📊 وضعیت برای دکمه‌ها: {settings.get('time_status', 'ندارد')}")
        
            await query.edit_message_media(
                media=InputMediaPhoto(media=photo, caption=CLOCK_SIMPLE_TEXT, parse_mode='HTML'),
                reply_markup=get_clock_buttons(user_id, page)
            )
            logger.info("✅ پیام با موفقیت ادیت شد!")
        
        except Exception as e:
            if "Message is not modified" not in str(e):
                logger.error(f"❌ خطا در ادیت: {e}")
        return
    if action in ("help_back", "page1", "page2"):
        text = "<b>🎛 پنل مدیریت سلف</b>"
        try:
            await query.edit_message_media(
                media=InputMediaPhoto(media=photo, caption=text, parse_mode='HTML'),
                reply_markup=get_main_menu(user_id)
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                print(f"Error: {e}")
        return
    
    if action == "close":
        # پیام‌های پنل عکس‌دار هستند؛ edit_message_text روی آن‌ها خطا می‌دهد،
        # پس کپشن ویرایش یا خود پیام حذف می‌شود.
        try:
            if query.message and query.message.photo:
                await query.edit_message_caption(caption="✅ پنل بسته شد", parse_mode='HTML')
            else:
                await query.edit_message_text("✅ پنل بسته شد")
        except Exception as e:
            if "Message is not modified" not in str(e):
                try:
                    await query.message.delete()
                except Exception:
                    print(f"Error: {e}")
        return
    
    if action == "help" and len(parts) > 1 and parts[1] == "oneclick":
        text = HELP_TEXTS["oneclick"] + "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📋 زیرمجموعه‌ها:\n\nروی دکمه‌های زیر کلیک کنید."
        try:
            await query.edit_message_media(
                media=InputMediaPhoto(media=photo, caption=text, parse_mode='HTML'),
                reply_markup=get_oneclick_buttons(user_id, page)
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                print(f"Error: {e}")
        return
    
    if action == "oneclick" and len(parts) > 1 and parts[1] == "time":
        text = CLOCK_SIMPLE_TEXT
        try:
            await query.edit_message_media(
                media=InputMediaPhoto(media=photo, caption=text, parse_mode='HTML'),
                reply_markup=get_clock_buttons(user_id, page)
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                print(f"Error: {e}")
        return
    
    if action == "oneclick" and len(parts) > 1 and parts[1] == "format":
        text = HELP_TEXTS["format"] + "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⚡ مدیریت فرمت‌ها:\n\nروی هر دکمه کلیک کنید تا فعال/غیرفعال شود.\n✅ = فعال | ⬜ = غیرفعال"
        try:
            await query.edit_message_media(
                media=InputMediaPhoto(media=photo, caption=text, parse_mode='HTML'),
                reply_markup=get_format_buttons(user_id, page)
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                print(f"Error: {e}")
        return
    
    if action == "clock_back":
        text = CLOCK_SIMPLE_TEXT
        try:
            await query.edit_message_media(
                media=InputMediaPhoto(media=photo, caption=text, parse_mode='HTML'),
                reply_markup=get_clock_buttons(user_id, page)
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                print(f"Error: {e}")
        return
    
    if action == "oneclick_back":
        text = HELP_TEXTS["oneclick"] + "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📋 زیرمجموعه‌ها:\n\nروی دکمه‌های زیر کلیک کنید."
        try:
            await query.edit_message_media(
                media=InputMediaPhoto(media=photo, caption=text, parse_mode='HTML'),
                reply_markup=get_oneclick_buttons(user_id, page)
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                print(f"Error: {e}")
        return
    if action == "font":
        if len(parts) > 1:
            font_num = parts[1]
            send_command_to_self_bot(f"تنظیم فونت {font_num}", user_id)
    
            settings = load_settings(user_id) 
            settings['font'] = int(font_num)
            save_settings(user_id, settings) 
    
            font_preview = get_font_preview(int(font_num))
    
            temp_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("⏳ در حال بازگشت...", callback_data="wait", style="primary")]
            ])
    
            text = f"✅ <b>فونت {font_num} تنظیم شد</b>\n\n🔤 {font_preview}"
    
            try:
                await query.edit_message_media(
                    media=InputMediaPhoto(media=photo, caption=text, parse_mode='HTML'),
                    reply_markup=temp_keyboard
                )
        
                await asyncio.sleep(3)
        
                font_text = "🔤 <b>فونت مورد نظر را انتخاب کنید</b>"
                await query.edit_message_media(
                    media=InputMediaPhoto(media=photo, caption=font_text, parse_mode='HTML'),
                    reply_markup=get_font_buttons(user_id, page)
                )
        
            except Exception as e:
                if "Message is not modified" not in str(e):
                    print(f"Error: {e}")
            return
    if action == "format":
        if len(parts) > 1:
            format_key = parts[1]
        
            if format_key == "reset":
                send_command_to_self_bot("فرمت ریست", user_id)
            
                settings = load_settings(user_id)  
                settings['formats'] = {}
                save_settings(user_id, settings)  
            
                text = "✅ همه فرمت‌ها ریست شدند"
                try:
                    await query.edit_message_media(
                        media=InputMediaPhoto(media=photo, caption=text, parse_mode='HTML'),
                        reply_markup=get_format_buttons(user_id, page)
                    )
                except Exception as e:
                    if "Message is not modified" not in str(e):
                        print(f"Error: {e}")
                return
        
            if format_key == "status":
                send_command_to_self_bot("فرمت وضعیت", user_id)
                await asyncio.sleep(2)
            
                result_file = f"reaction_result_{user_id}.json"
                if os.path.exists(result_file):
                    try:
                        with open(result_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            result = data.get('result', '')
                            try:
                                await query.edit_message_media(
                                    media=InputMediaPhoto(media=photo, caption=result, parse_mode='HTML'),
                                    reply_markup=get_format_buttons(user_id, page)
                                )
                            except Exception as e:
                                if "Message is not modified" not in str(e):
                                    print(f"Error: {e}")
                    except:
                        text = "📊 وضعیت فرمت‌ها:\n\nدریافت نشد"
                        try:
                            await query.edit_message_media(
                                media=InputMediaPhoto(media=photo, caption=text, parse_mode='HTML'),
                                reply_markup=get_format_buttons(user_id, page)
                            )
                        except Exception as e:
                            if "Message is not modified" not in str(e):
                                print(f"Error: {e}")
                return
        
        format_names = {
            "bold": "بولد",
            "italic": "ایتالیک",
            "underline": "زیرخط",
            "s": "خط‌خورده", 
            "spoiler": "اسپویلر",
            "code": "کد",
            "pre": "پیش‌فرمت",
            "quote": "نقل‌قول"
        }
        
        if format_key in format_names:
            settings = load_settings(user_id) 
            if 'formats' not in settings:
                settings['formats'] = {}
            
            current = settings['formats'].get(format_key, False)
            settings['formats'][format_key] = not current
            save_settings(user_id, settings) 
            
            persian_name = format_names[format_key]
            action_text = "روشن" if not current else "خاموش"
            send_command_to_self_bot(f"فرمت {persian_name} {action_text}", user_id)
            
            text = f"✅ فرمت {persian_name} {'فعال' if not current else 'غیرفعال'} شد"
            try:
                await query.edit_message_media(
                    media=InputMediaPhoto(media=photo, caption=text, parse_mode='HTML'),
                    reply_markup=get_format_buttons(user_id, page)
                )
            except Exception as e:
                if "Message is not modified" not in str(e):
                    print(f"Error: {e}")
            return
    if action == "adv":
        feature = parts[1]
        settings = load_settings(user_id)
        adv = settings.setdefault('advanced', {})

        if feature == "expiry":
            send_command_to_self_bot("انقضا", user_id)
            await query.answer("✅ دستور انقضا ارسال شد؛ نتیجه در چت سلف نمایش داده می‌شود.", show_alert=True)
            return

        toggle_map = {
            "biotime": ("bio_time", "بیو تایم"),
            "savedel": ("save_deleted", "سیو حذفیات"),
            "saveedit": ("save_edited", "سیو ادیت"),
            "afk": ("afk", "منشی"),
            "autoread": ("auto_read", "خواندن خودکار"),
            "randfont": ("random_font", "فونت رندوم"),
            "emojiclock": ("emoji_clock", "ساعت ایموجی"),
            "calc": ("calc_mode", "محاسبه"),
        }
        if feature in toggle_map:
            key, cmd = toggle_map[feature]
            new_state = not adv.get(key, False)
            adv[key] = new_state
            save_settings(user_id, settings)
            send_command_to_self_bot(f"{cmd} {'روشن' if new_state else 'خاموش'}", user_id)
            try:
                await query.edit_message_media(
                    media=InputMediaPhoto(
                        media=photo,
                        caption=f"✅ <b>{cmd} {'روشن' if new_state else 'خاموش'} شد</b>",
                        parse_mode='HTML',
                    ),
                    reply_markup=get_main_menu(user_id),
                )
            except Exception as e:
                if "Message is not modified" not in str(e):
                    print(f"Error: {e}")
        return

    if action == "help" and len(parts) > 1 and parts[1] in HELP_TEXTS:
        text = HELP_TEXTS.get(parts[1], "راهنما")
        try:
            await query.edit_message_media(
                media=InputMediaPhoto(media=photo, caption=text, parse_mode='HTML'),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=f"help_back_{user_id}_{page}")]
                ])
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                print(f"Error: {e}")
        return
    
    if action == "help" and len(parts) > 1 and parts[1] == "fonts":
        text = "🔤 <b>فونت مورد نظر را انتخاب کنید</b>"
        try:
            await query.edit_message_media(
                media=InputMediaPhoto(media=photo, caption=text, parse_mode='HTML'),
                reply_markup=get_font_buttons(user_id, page)
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                print(f"Error: {e}")
        return
    
    if action == "format_status":
        settings = load_settings(user_id) 
        format_settings = settings.get('formats', {})
    
        text = "📊 <b>وضعیت فرمت‌ها:</b>\n\n"
        format_names = {
            "bold": "بولد",
            "italic": "ایتالیک",
            "underline": "زیرخط",
            "s": "خط‌خورده",  
            "spoiler": "اسپویلر",
            "code": "کد",
            "pre": "پیش‌فرمت",
            "quote": "نقل‌قول"
        }
    
        for key, name in format_names.items():
            status = format_settings.get(key, False)
            emoji = "✅" if status else "❌"
            text += f"{emoji} {name}\n"
    
        try:
            await query.edit_message_media(
                media=InputMediaPhoto(media=photo, caption=text, parse_mode='HTML'),
                reply_markup=get_format_buttons(user_id, page)
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                print(f"Error: {e}")
        return
    
    await query.answer("⏳ در حال آماده‌سازی...", show_alert=True)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(MessageHandler(filters.PHOTO, handle_admin_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, show_menu))
    app.add_handler(InlineQueryHandler(handle_inline_query))
    app.add_handler(ChosenInlineResultHandler(handle_chosen_inline_result))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_error_handler(error_handler)
    app.add_error_handler(lambda u, c: logger.error(f"❌ خطا: {c.error}"))
    
    print("ربات هلپر اجرا شد")
    app.run_polling()

if __name__ == "__main__":
    main()