# ایمیج ربات پلیر تلگرام
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# ffmpeg برای پخش/تبدیل صدا و ویدیو لازم است.
# deno موتور جاوااسکریپت مورد نیاز نسخه‌های جدید yt-dlp برای یوتیوب است.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        git \
        curl \
        unzip \
        fonts-dejavu-core \
        ca-certificates \
    && curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh -s -- -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY player/requirements.txt /app/player/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/player/requirements.txt

COPY player /app/player

RUN mkdir -p /app/player/downloads /app/player/cache /app/player/sessions

CMD ["python", "-m", "player"]
