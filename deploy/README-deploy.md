# اجرا روی سرور اوبونتو (۲۴ساعته)

این راهنما سرویس را به‌صورت دائمی روی یک سرور Ubuntu اجرا می‌کند.

## ۱) پیش‌نیازها

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git ffmpeg
```

## ۲) گرفتن کد و نصب وابستگی‌ها

```bash
sudo mkdir -p /opt/selfsaz && sudo chown $USER:$USER /opt/selfsaz
git clone <REPO_URL> /opt/selfsaz
cd /opt/selfsaz
pip3 install -r requirements.txt
mkdir -p logs sessions
```

## ۳) تنظیم مقادیر (.env)

```bash
cp .env.example .env
nano .env    # مقادیر واقعی را وارد کنید
```

حداقل مقادیر لازم:

| کلید | توضیح |
| --- | --- |
| `API_ID` / `API_HASH` | از my.telegram.org |
| `BOT_TOKEN` | توکن ربات **سلف‌ساز/مدیریت** (از BotFather) |
| `HELPER_BOT_TOKEN` | توکن ربات **هلپر** (یک ربات جدا از BotFather) |
| `ADMIN_ID` | آیدی عددی مالک |
| `HELPER_BOT_USERNAME` | یوزرنیم ربات هلپر (بدون @) |
| `MANAGER_BOT_LINK` | لینک ربات سلف‌ساز، مثل `https://t.me/YourManagerBot` |

## ۴) روش A — systemd (توصیه‌شده)

```bash
sudo cp deploy/selfsaz-manager.service /etc/systemd/system/
sudo cp deploy/selfsaz-helper.service  /etc/systemd/system/
# اگر مسیر/کاربر فرق دارد، فایل‌ها را ویرایش کنید (WorkingDirectory, User, ExecStart)
sudo systemctl daemon-reload
sudo systemctl enable --now selfsaz-manager selfsaz-helper
sudo systemctl status selfsaz-manager selfsaz-helper
```

مشاهدهٔ لاگ‌ها:

```bash
journalctl -u selfsaz-manager -f
tail -f /opt/selfsaz/logs/manager.log
```

## ۴) روش B — اجرای سریع با اسکریپت

```bash
./run.sh        # هر دو ربات را با ری‌استارت خودکار اجرا می‌کند (لاگ در logs/)
```

## ۵) لاگین سلف‌بات (تعاملی — فقط توسط خودتان)

`self.py` را دستی اجرا نکنید. بعد از بالا آمدن ربات‌ها:

1. در تلگرام وارد **ربات سلف‌ساز** شوید و `/start` بزنید.
2. «فعالسازی» → شمارهٔ اکانتی که می‌خواهید سلف روی آن اجرا شود را بفرستید.
3. کدی که تلگرام می‌فرستد را وارد کنید (و در صورت داشتن رمز دومرحله‌ای، آن را هم).
4. پس از لاگین موفق، فایل `sessions/<user_id>.session` ساخته و `self.py` خودکار اجرا می‌شود.

> ⚠️ این مرحله نیازمند شماره و کدِ لحظه‌ای خودتان است و نمی‌تواند به‌صورت خودکار توسط ابزار انجام شود.

## نکات

- فایل‌های `.env` و `sessions/` هرگز نباید کامیت شوند (در `.gitignore` هستند).
- برای قابلیت پخش در ویس‌چت: `pip install py-tgcalls` (و ffmpeg که بالا نصب شد).
