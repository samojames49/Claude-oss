"""ساخت STRING_SESSION برای اکانت اسیستنت.

اجرا:  python -m player.tools.gen_session

این اسکریپت شمارهٔ اکانتی که می‌خواهید داخل ویس‌چت پخش کند را می‌گیرد، کد ورود را
تایید می‌کند و رشتهٔ نشست را چاپ می‌کند. آن رشته را در `STRING_SESSION` بگذارید.
"""

from __future__ import annotations

import asyncio
import os

from pyrogram import Client


async def main() -> None:
    print("🔐 ساخت نشست اسیستنت (اکانت کاربری، نه ربات)\n")
    api_id = os.getenv("API_ID") or input("API_ID: ").strip()
    api_hash = os.getenv("API_HASH") or input("API_HASH: ").strip()

    try:
        api_id_int = int(api_id)
    except ValueError:
        print("❌ API_ID باید عدد باشد.")
        return

    async with Client(
        name="gen_session",
        api_id=api_id_int,
        api_hash=api_hash,
        in_memory=True,
    ) as client:
        session = await client.export_session_string()
        me = await client.get_me()
        print("\n✅ نشست ساخته شد برای:", me.first_name, f"(@{me.username})" if me.username else "")
        print("\nمقدار زیر را در STRING_SESSION بگذارید:\n")
        print(session)
        print("\n⚠️ این رشته مثل رمز عبور است؛ در اختیار کسی نگذارید.")
        try:
            await client.send_message("me", "✅ نشست اسیستنت ربات پلیر ساخته شد.")
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    asyncio.run(main())
