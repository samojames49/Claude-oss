import os, subprocess, html
from PIL import Image, ImageChops

OUT = os.path.dirname(os.path.abspath(__file__))
HTML_DIR = os.path.join(OUT, "html")
os.makedirs(HTML_DIR, exist_ok=True)

BG = (14, 22, 33)  # #0e1621

TEMPLATE = """<!doctype html><html dir="rtl"><head><meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:#0e1621; font-family:'Noto Sans Arabic','Noto Naskh Arabic',sans-serif; }}
  .wrap {{ width:460px; padding:20px; }}
  .bar {{ display:flex; align-items:center; gap:10px; padding:8px 4px 14px; }}
  .ava {{ width:38px; height:38px; border-radius:50%;
          background:linear-gradient(135deg,#2aabee,#1c86c9); color:#fff;
          display:flex; align-items:center; justify-content:center; font-weight:700; font-size:15px; }}
  .btitle {{ color:#fff; font-size:15px; font-weight:700; }}
  .bsub {{ color:#6d7f8f; font-size:12px; margin-top:1px; }}
  .bubble {{ background:#182533; border-radius:14px; border-top-right-radius:4px;
             padding:0; overflow:hidden; max-width:100%; box-shadow:0 1px 1px rgba(0,0,0,.2); }}
  .banner {{ height:120px; background:linear-gradient(135deg,#1c2b3a,#24608f);
             display:flex; align-items:center; justify-content:center; color:#dbeafe;
             font-size:20px; font-weight:800; letter-spacing:.3px; }}
  .cap {{ padding:11px 13px 13px; color:#e7f0f7; font-size:14px; line-height:1.9; white-space:pre-wrap; }}
  .cap b {{ color:#fff; }}
  .kb {{ margin-top:6px; display:flex; flex-direction:column; gap:6px; }}
  .row {{ display:flex; gap:6px; }}
  .key {{ flex:1; background:#242f3d; color:#7cc0f7; border-radius:9px;
          padding:11px 8px; text-align:center; font-size:13.5px; font-weight:600;
          border:1px solid rgba(255,255,255,.04); }}
  .key.wide {{ flex-basis:100%; }}
</style></head><body><div class="wrap">
  <div class="bar"><div class="ava">{ava}</div>
    <div><div class="btitle">{title}</div><div class="bsub">{sub}</div></div></div>
  <div class="bubble">{banner}<div class="cap">{cap}</div></div>
  <div class="kb">{kb}</div>
</div></body></html>"""


def esc(s):
    return html.escape(s).replace("\n", "\n")


def render_kb(rows):
    out = []
    for r in rows:
        keys = "".join(f'<div class="key{" wide" if len(r)==1 else ""}">{html.escape(k)}</div>' for k in r)
        out.append(f'<div class="row">{keys}</div>')
    return "".join(out)


def page(fname, title, sub, cap, rows, ava="C", banner_text=None):
    banner = f'<div class="banner">{html.escape(banner_text)}</div>' if banner_text else ""
    cap_html = cap  # allow <b>
    doc = TEMPLATE.format(ava=ava, title=html.escape(title), sub=html.escape(sub),
                          banner=banner, cap=cap_html, kb=render_kb(rows))
    p = os.path.join(HTML_DIR, fname + ".html")
    with open(p, "w", encoding="utf-8") as f:
        f.write(doc)
    return fname, p


PAGES = []

# ---------- MANAGER BOT ----------
PAGES.append(page(
    "01_manager_start", "Creeps | سلف ساز", "bot",
    "<b>Creeps | سلف ساز</b>\n\nبه ربات سلف ساز خوش آمدید!\n👤 کاربر: Creeps\n💰 سکه: ۵ عدد\n⏰ مصرف ۱ سکه در ساعت\n📱 شماره: ثبت نشده\n\n💡 برای شروع روی «فعالسازی» کلیک کنید.",
    [["فعالسازی"], ["حساب کاربری", "شرطبندی"], ["مدیریت سلف", "افزایش موجودی"], ["🛠 پنل ادمین"]],
    banner_text="Creeps | سلف ساز"))

PAGES.append(page(
    "02_manager_account", "Creeps | سلف ساز", "bot",
    "<b>Creeps | سلف ساز</b>\n\n<b>وضعیت:</b> 🔴 سلف غیرفعال\n<b>🔐 احراز:</b> ❌ احراز نشده\n<b>💰 سکه ها:</b> ۵ سکه\n<b>⏰ مصرف:</b> ۱ سکه در ساعت",
    [["فعالسازی"], ["حساب کاربری", "شرطبندی"], ["مدیریت سلف", "افزایش موجودی"], ["🛠 پنل ادمین"]]))

PAGES.append(page(
    "03_manager_self_management", "Creeps | سلف ساز", "bot",
    "<b>🎛 مدیریت سلف بات</b>\n\n<b>وضعیت:</b> 🔴 غیرفعال\n💰 سکه: ۵",
    [["▶️ روشن کردن سلف", "⏹ خاموش کردن سلف"], ["🔄 آپدیت سلف"], ["🔙 بازگشت"]]))

PAGES.append(page(
    "04_manager_bet", "Creeps | سلف ساز", "bot",
    "🎲 <b>سیستم شرطبندی گروهی 1v1</b>\n\n۱️⃣ در گروه با نوشتن «شرطبندی 100» شرط بساز\n۲️⃣ نفر دوم روی «پیوستن به شرط» می‌زند\n۳️⃣ ۵ ثانیه بعد برنده مشخص می‌شود\n۴️⃣ برنده کل مبلغ را می‌برد\n۵️⃣ اگر ۵ دقیقه کسی نپیوندد، مبلغ برمی‌گردد",
    [["🔙 بازگشت"]]))

PAGES.append(page(
    "05_manager_increase_balance", "Creeps | سلف ساز", "bot",
    "🔒 <b>برای افزایش موجودی نیاز به احراز هویت دارید</b>\n\n📋 مراحل:\n۱️⃣ کلیک روی «احراز هویت»\n۲️⃣ ارسال عکس کارت بانکی\n۳️⃣ تایید توسط ادمین\n۴️⃣ افزایش موجودی\n\n⚠️ اطلاعات حساس (CVV2 و تاریخ انقضا) پوشیده شود",
    [["احراز هویت"], ["🔙 بازگشت"]]))

PAGES.append(page(
    "06_manager_admin_panel", "Creeps | سلف ساز", "bot",
    "🛠 <b>پنل مدیریت ادمین</b>\n\nیکی از گزینه‌های زیر را انتخاب کنید:",
    [["👥 لیست کاربران", "📊 آمار کامل"],
     ["💰 برترین کاربران", "🛑 توقف همه"],
     ["🔐 درخواست احراز", "💳 درخواست پرداخت"],
     ["🔄 روشن کردن انتقال", "⛔ خاموش کردن انتقال"],
     ["📸 تنظیم عکس خوش‌آمدگویی"],
     ["📢 پیام همگانی", "♻️ بررسی سلامت سلف‌ها"]]))

PAGES.append(page(
    "07_manager_force_join", "Creeps | سلف ساز", "bot",
    "❌ <b>برای استفاده از ربات باید در کانال‌های زیر عضو شوید:</b>",
    [["عضویت در @Creeps_Channel"], ["عضویت در @Creeps_News"], ["بررسی مجدد"]]))

# ---------- HELPER PANEL ----------
PAGES.append(page(
    "08_helper_panel", "پنل هلپر", "inline bot",
    "<b>🎛 پنل مدیریت سلف</b>\n\n💡 همهٔ قابلیت‌ها در یک صفحه",
    [["ایدی", "یک کلیک"],
     ["عکس تایمدار", "پشتیبان‌گیری"],
     ["مدیریت فونت", "قیمت ارز"],
     ["فرمت متن", "اسپم"],
     ["مدیریت دشمنان", "پاسخ خودکار"],
     ["تاس", "سیستم پیشی"],
     ["سیستم فحش", "همیشه آنلاین"],
     ["قفل پیوی", "انتی لاگین"],
     ["ریکشن خودکار", "ویرایش سریع"],
     ["سیستم بنر", "اینستاگرام"],
     ["دانلود تلگرام", "مدیریت گروه/کانال"],
     ["تایمر میو", "پیام زمان‌دار"],
     ["مدیریت اکشن", "مدیریت گروه"],
     ["⬜️ ساعت در بایو"],
     ["⬜️ ذخیره حذفیات"],
     ["⬜️ ذخیره ویرایش‌ها"],
     ["رصد کاربران", "پروفایل خودکار"],
     ["انقضا / زمان باقی‌مانده"],
     ["⬜️ منشی (پاسخ خودکار پیوی)"],
     ["⬜️ خواندن خودکار همه"],
     ["⬜️ فونت رندوم", "⬜️ ساعت ایموجی"],
     ["⬜️ حالت محاسبه"],
     ["👁 شنود کاربران", "💚 دوستان"],
     ["📱 نشست‌ها / گوشی‌ها", "👀 خواندن همه چت‌ها"],
     ["🪙 اقتصاد و گردونه", "🎮 بازی‌های سکه‌ای"],
     ["⏬ دانلود تیک‌تاک/ساندکلاود", "🎧 ویس‌چت / پخش"],
     ["🎉 سرگرمی", "🔤 ابزار متن"],
     ["👤 مدیریت پروفایل", "🕐 زمان و وضعیت"],
     ["🌐 مترجم", "📊 نظرسنجی"],
     ["🧹 پاکسازی پیام‌های من", "🧰 ابزار تکمیلی"],
     ["❌ بستن"]],
    ava="H", banner_text="🎛 پنل مدیریت سلف"))

PAGES.append(page(
    "09_helper_fonts", "پنل هلپر", "inline bot",
    "🔤 <b>فونت مورد نظر را انتخاب کنید</b>",
    [["فونت ۱", "فونت ۲", "فونت ۳"],
     ["فونت ۴", "فونت ۵", "فونت ۶"],
     ["فونت ۷", "فونت ۸", "فونت ۹"],
     ["فونت ۱۰", "فونت ۱۱", "فونت ۱۲"],
     ["فونت ۱۳", "فونت ۱۴", "فونت ۱۵"],
     ["بازگشت به ساعت"]],
    ava="H", banner_text="🔤 انتخاب فونت"))

PAGES.append(page(
    "10_helper_formats", "پنل هلپر", "inline bot",
    "⚡ <b>مدیریت فرمت‌ها</b>\n\nروی هر دکمه بزنید تا فعال/غیرفعال شود.\n✅ = فعال | ⬜ = غیرفعال",
    [["⬜ بولد", "⬜ ایتالیک", "⬜ زیرخط"],
     ["⬜ خط‌خورده", "⬜ اسپویلر", "⬜ کد"],
     ["⬜ پیش‌فرمت", "⬜ نقل‌قول"],
     ["ریست همه فرمت‌ها", "وضعیت فرمت‌ها"],
     ["🔙"]],
    ava="H", banner_text="⚡ مدیریت فرمت‌ها"))


def shoot(fname, path):
    png = os.path.join(OUT, fname + ".png")
    prof = f"/tmp/cp_{fname}"
    subprocess.run(
        ["timeout", "14", "google-chrome", "--headless=old", "--disable-gpu",
         "--no-sandbox", "--disable-dev-shm-usage", "--no-first-run",
         f"--user-data-dir={prof}", "--hide-scrollbars",
         "--force-device-scale-factor=2", "--virtual-time-budget=1800",
         f"--screenshot={png}", "--window-size=460,2200", path],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # autocrop uniform background, then repad
    im = Image.open(png).convert("RGB")
    bg = Image.new("RGB", im.size, BG)
    bbox = ImageChops.difference(im, bg).getbbox()
    if bbox:
        l, t, r, b = bbox
        pad = 24
        l = max(0, l - pad); t = max(0, t - pad)
        r = min(im.size[0], r + pad); b = min(im.size[1], b + pad)
        im = im.crop((l, t, r, b))
    canvas = Image.new("RGB", im.size, BG)
    canvas.paste(im, (0, 0))
    canvas.save(png)
    print("saved", png, canvas.size)


if __name__ == "__main__":
    import sys
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for fname, path in PAGES:
        if only and only not in fname:
            continue
        shoot(fname, path)
    print("DONE")
