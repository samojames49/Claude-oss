"""درگاه پرداخت آنی ریالی.

نسخه قبلی فقط کارت‌به‌کارت دستی داشت: کاربر رسید می‌فرستاد و ادمین باید دستی
تایید می‌کرد. اینجا یک لایه انتزاعی درگاه اضافه شده تا شارژ به‌صورت آنی و بدون
دخالت ادمین انجام شود.

فعال‌سازی با `PAYMENT_GATEWAY_ENABLED=true` در فایل .env. اگر خاموش باشد، ربات
به همان روش کارت‌به‌کارت برمی‌گردد.

افزودن درگاه جدید: یک کلاس از `PaymentGateway` بسازید و در `GATEWAYS` ثبتش کنید.
"""

import asyncio

try:
    import aiohttp
except ImportError:  # aiohttp نصب نیست؛ درگاه آنلاین غیرفعال می‌شود
    aiohttp = None

import config


class PaymentError(Exception):
    """خطای قابل نمایش به کاربر هنگام کار با درگاه."""


class PaymentGateway:
    """رابط مشترک همه درگاه‌ها."""

    name = "base"

    def __init__(self, merchant_id, callback_url, sandbox=False):
        self.merchant_id = merchant_id
        self.callback_url = callback_url
        self.sandbox = sandbox

    async def create_payment(self, amount_toman, description, user_id):
        """ساخت تراکنش. برمی‌گرداند: (authority, pay_url)"""
        raise NotImplementedError

    async def verify_payment(self, authority, amount_toman):
        """بررسی تراکنش. برمی‌گرداند: (موفق؟, ref_id)"""
        raise NotImplementedError


class ZarinpalGateway(PaymentGateway):
    """درگاه زرین‌پال (REST v4).

    مبالغ در API زرین‌پال بر حسب ریال هستند، پس تومان × ۱۰ می‌شود.
    """

    name = "zarinpal"

    @property
    def _base(self):
        return "https://sandbox.zarinpal.com" if self.sandbox else "https://payment.zarinpal.com"

    @property
    def _start_pay(self):
        return f"{self._base}/pg/StartPay/"

    async def _post(self, path, payload):
        if aiohttp is None:
            raise PaymentError("کتابخانه aiohttp نصب نیست؛ درگاه در دسترس نیست.")
        url = f"{self._base}/pg/v4/payment/{path}"
        timeout = aiohttp.ClientTimeout(total=20)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as response:
                    return await response.json(content_type=None)
        except asyncio.TimeoutError:
            raise PaymentError("درگاه پرداخت پاسخ نداد. کمی بعد دوباره تلاش کنید.")
        except aiohttp.ClientError as error:
            raise PaymentError(f"ارتباط با درگاه برقرار نشد: {error}")

    async def create_payment(self, amount_toman, description, user_id):
        data = await self._post(
            "request.json",
            {
                "merchant_id": self.merchant_id,
                "amount": int(amount_toman) * 10,
                "description": description,
                "callback_url": self.callback_url,
                "metadata": {"user_id": str(user_id)},
            },
        )

        body = (data or {}).get("data") or {}
        if body.get("code") == 100 and body.get("authority"):
            authority = body["authority"]
            return authority, f"{self._start_pay}{authority}"

        errors = (data or {}).get("errors") or {}
        message = errors.get("message") if isinstance(errors, dict) else str(errors)
        raise PaymentError(message or "ساخت تراکنش در درگاه ناموفق بود.")

    async def verify_payment(self, authority, amount_toman):
        data = await self._post(
            "verify.json",
            {
                "merchant_id": self.merchant_id,
                "amount": int(amount_toman) * 10,
                "authority": authority,
            },
        )

        body = (data or {}).get("data") or {}
        # کد ۱۰۰ یعنی تایید شد، کد ۱۰۱ یعنی قبلاً تایید شده بود
        if body.get("code") in (100, 101):
            return True, str(body.get("ref_id", ""))

        errors = (data or {}).get("errors") or {}
        message = errors.get("message") if isinstance(errors, dict) else str(errors)
        raise PaymentError(message or "تراکنش تایید نشد.")


GATEWAYS = {
    ZarinpalGateway.name: ZarinpalGateway,
}

_gateway_instance = None


def get_gateway():
    """درگاه پیکربندی‌شده را برمی‌گرداند؛ اگر غیرفعال باشد None."""
    global _gateway_instance

    if not config.PAYMENT_GATEWAY_ENABLED:
        return None

    if _gateway_instance is not None:
        return _gateway_instance

    provider = (config.PAYMENT_GATEWAY_PROVIDER or "").strip().lower()
    gateway_class = GATEWAYS.get(provider)
    if gateway_class is None:
        print(f"⚠️ درگاه ناشناخته: {provider!r}. درگاه‌های موجود: {', '.join(GATEWAYS)}")
        return None

    if not config.PAYMENT_GATEWAY_MERCHANT_ID:
        print("⚠️ PAYMENT_GATEWAY_MERCHANT_ID تنظیم نشده؛ درگاه آنلاین غیرفعال ماند.")
        return None

    _gateway_instance = gateway_class(
        merchant_id=config.PAYMENT_GATEWAY_MERCHANT_ID,
        callback_url=config.PAYMENT_GATEWAY_CALLBACK_URL,
        sandbox=config.PAYMENT_GATEWAY_SANDBOX,
    )
    return _gateway_instance
