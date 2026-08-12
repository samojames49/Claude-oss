#!/usr/bin/env bash
# اجرای سریع سرویس روی سرور اوبونتو (برای تست/اجرای موقت).
# برای اجرای دائمی ۲۴ساعته از systemd استفاده کنید (پوشهٔ deploy/).
set -euo pipefail

cd "$(dirname "$0")"

# ۱) بررسی .env
if [ ! -f .env ]; then
  echo "❌ فایل .env وجود ندارد. اول:  cp .env.example .env  و مقادیر را پر کنید."
  exit 1
fi

# ۲) نصب وابستگی‌ها (در صورت نیاز)
if ! python3 -c "import pyrogram, telegram" >/dev/null 2>&1; then
  echo "📦 نصب وابستگی‌ها..."
  pip install -r requirements.txt
fi

mkdir -p logs sessions

echo "🚀 اجرای ربات سلف‌ساز (bot.py) و ربات هلپر (helper.py)..."

# اجرای هر دو با ری‌استارت خودکار در صورت کرش
run_forever() {
  local name="$1"; shift
  while true; do
    echo "[$(date '+%F %T')] ▶️ شروع $name"
    "$@" >>"logs/${name}.log" 2>&1 || true
    echo "[$(date '+%F %T')] ⚠️ $name متوقف شد؛ ۵ ثانیه دیگر دوباره اجرا می‌شود" >>"logs/${name}.log"
    sleep 5
  done
}

run_forever manager python3 bot.py &
MANAGER_PID=$!
run_forever helper  python3 helper.py &
HELPER_PID=$!

echo "✅ اجرا شد. لاگ‌ها در پوشهٔ logs/ . برای توقف:  kill $MANAGER_PID $HELPER_PID"
echo "   (یا Ctrl+C اگر در پیش‌زمینه اجرا کرده‌اید)"

trap 'echo "⏹ توقف..."; kill $MANAGER_PID $HELPER_PID 2>/dev/null || true; exit 0' INT TERM
wait
