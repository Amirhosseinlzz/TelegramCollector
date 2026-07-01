# Telegram VPN Subscription Collector

این پروژه پیام‌های چند کانال تلگرام را می‌خواند، کانفیگ‌های VPN را استخراج می‌کند، موارد تکراری و خطوط خالی را حذف می‌کند، خروجی را مرتب می‌سازد و فایل `subscriptions.txt` را در مخزن GitHub به‌روزرسانی می‌کند. پس از هر اجرا، فایل از طریق لینک Raw GitHub قابل استفاده است.

> مسئولیت استفاده از این ابزار با شماست. فقط کانال‌هایی را اضافه کنید که اجازه دسترسی به آن‌ها را دارید و قوانین Telegram، GitHub و قوانین محل استفاده را رعایت کنید.

## قابلیت‌ها

- خواندن آخرین پیام‌های کانال‌های تلگرام
- استخراج لینک‌های `vless://`، `vmess://`، `trojan://`، `ss://`، `ssr://`، `hysteria://`، `hysteria2://`، `tuic://` و `wireguard://`
- حذف کانفیگ‌های تکراری
- حذف خطوط خالی
- مرتب‌سازی خروجی
- تغییر لیست کانال‌ها فقط با ویرایش `channels.json`
- لاگ‌گذاری مناسب برای GitHub Actions
- مدیریت خطاهای کانال‌های نامعتبر، خصوصی یا غیرقابل دسترس
- زمان‌بندی خودکار هر ۳۰ دقیقه با GitHub Actions
- امکان اجرای دستی از تب Actions در GitHub

## ساختار پروژه

```text
.
├── .github/
│   └── workflows/
│       └── update.yml
├── scripts/
│   └── generate_string_session.py
├── channels.json
├── config.py
├── deduplicator.py
├── extractor.py
├── logger.py
├── main.py
├── parser.py
├── requirements.txt
├── subscriptions.txt
├── .env.example
├── .gitignore
└── README.md
```

## پیش‌نیازها

- Python 3.11 یا جدیدتر
- حساب Telegram
- مخزن GitHub
- دسترسی به کانال‌هایی که می‌خواهید از آن‌ها پیام بخوانید

## 1. گرفتن Telegram API ID و API Hash

1. با یک اپ رسمی Telegram حساب بسازید یا وارد حساب خود شوید.
2. وارد `https://my.telegram.org` شوید.
3. شماره تلفن خود را وارد کنید. کد ورود در خود Telegram ارسال می‌شود، نه SMS.
4. وارد بخش **API development tools** شوید.
5. فرم ایجاد اپلیکیشن را تکمیل کنید.
6. مقدارهای `api_id` و `api_hash` را یادداشت کنید.

## 2. ایجاد Session یا String Session

برای اجرای خودکار در GitHub Actions، استفاده از `StringSession` توصیه می‌شود؛ چون GitHub Actions نمی‌تواند هر بار کد ورود Telegram را تعاملی دریافت کند.

ابتدا وابستگی‌ها را نصب کنید:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows PowerShell
pip install -r requirements.txt
```

سپس فایل نمونه محیطی را کپی کنید:

```bash
cp .env.example .env
```

در فایل `.env` مقدارهای زیر را قرار دهید:

```env
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=your_api_hash
```

حالا String Session را بسازید:

```bash
python scripts/generate_string_session.py
```

اسکریپت شماره تلفن، کد ورود و در صورت فعال بودن رمز دومرحله‌ای، رمز را می‌پرسد. در پایان مقدار `TELEGRAM_STRING_SESSION` چاپ می‌شود. این مقدار را در هیچ فایلی commit نکنید.

## 3. تنظیم GitHub Secrets

در مخزن GitHub خود مسیر زیر را باز کنید:

`Settings` → `Secrets and variables` → `Actions` → `New repository secret`

سه Secret زیر را بسازید:

| Secret name | مقدار |
|---|---|
| `TELEGRAM_API_ID` | همان API ID گرفته‌شده از Telegram |
| `TELEGRAM_API_HASH` | همان API Hash گرفته‌شده از Telegram |
| `TELEGRAM_STRING_SESSION` | مقدار تولیدشده با `scripts/generate_string_session.py` |

## 4. اجرای پروژه روی GitHub

1. همه فایل‌های پروژه را در یک مخزن GitHub قرار دهید.
2. مطمئن شوید فایل `.github/workflows/update.yml` در همین مسیر وجود دارد.
3. وارد تب **Actions** شوید.
4. Workflow با نام **Update VPN Subscription** را فعال کنید.
5. برای اجرای دستی، روی **Run workflow** کلیک کنید.
6. پس از اجرای موفق، فایل `subscriptions.txt` در مخزن commit و push می‌شود.

لینک Raw GitHub معمولاً چنین ساختاری دارد:

```text
https://raw.githubusercontent.com/USERNAME/REPOSITORY/BRANCH/subscriptions.txt
```

مثلاً اگر نام کاربری `myuser`، نام مخزن `vpn-sub` و شاخه `main` باشد:

```text
https://raw.githubusercontent.com/myuser/vpn-sub/main/subscriptions.txt
```

## 5. اضافه یا حذف کانال جدید

فقط فایل `channels.json` را ویرایش کنید.

نمونه:

```json
{
  "channels": [
    {
      "name": "@public_channel_name",
      "enabled": true
    },
    {
      "name": "https://t.me/another_public_channel",
      "enabled": true
    },
    {
      "name": "@disabled_channel",
      "enabled": false
    }
  ]
}
```

نکات:

- برای کانال عمومی می‌توانید `@channel_name` یا `https://t.me/channel_name` بنویسید.
- برای حذف موقت یک کانال، مقدار `enabled` را `false` کنید.
- برای حذف کامل، کل آبجکت آن کانال را از آرایه `channels` پاک کنید.
- اگر کانال خصوصی است، حساب Telegram مربوط به Session باید عضو آن کانال باشد.

## 6. تغییر فاصله زمانی اجرای GitHub Actions

فایل زیر را باز کنید:

```text
.github/workflows/update.yml
```

بخش زمان‌بندی پیش‌فرض:

```yaml
on:
  schedule:
    - cron: "*/30 * * * *"
  workflow_dispatch:
```

این مقدار یعنی اجرا هر ۳۰ دقیقه. چند نمونه رایج:

```yaml
# هر ۱۵ دقیقه
- cron: "*/15 * * * *"

# هر ۱ ساعت
- cron: "0 * * * *"

# هر روز ساعت 00:00 UTC
- cron: "0 0 * * *"
```

زمان‌بندی GitHub Actions بر اساس UTC اجرا می‌شود. برای کاهش احتمال تأخیر یا ازدحام، بهتر است دقیقه‌های خیلی رایج مثل `0` را در پروژه‌های پرتعداد کمتر استفاده کنید.

## اجرای محلی

فایل `.env` را بسازید:

```bash
cp .env.example .env
```

مقادیر زیر را در `.env` قرار دهید:

```env
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_STRING_SESSION=your_string_session
```

کانال‌ها را در `channels.json` فعال کنید و سپس اجرا کنید:

```bash
pip install -r requirements.txt
python main.py
```

خروجی در فایل `subscriptions.txt` نوشته می‌شود.

## متغیرهای محیطی

| نام | اجباری | پیش‌فرض | توضیح |
|---|---:|---|---|
| `TELEGRAM_API_ID` | بله | ندارد | API ID حساب Telegram |
| `TELEGRAM_API_HASH` | بله | ندارد | API Hash حساب Telegram |
| `TELEGRAM_STRING_SESSION` | برای GitHub Actions بله | ندارد | Session قابل حمل Telethon |
| `TELEGRAM_SESSION_NAME` | خیر | `telegram_vpn_collector` | نام session محلی در صورت نبود String Session |
| `CHANNELS_FILE` | خیر | `channels.json` | مسیر فایل کانال‌ها |
| `OUTPUT_FILE` | خیر | `subscriptions.txt` | مسیر خروجی subscription |
| `MESSAGE_LIMIT_PER_CHANNEL` | خیر | `100` | تعداد آخرین پیام‌ها برای هر کانال |
| `MAX_FLOOD_WAIT_SECONDS` | خیر | `60` | حداکثر زمان انتظار قابل قبول برای FloodWait |
| `REQUEST_DELAY_SECONDS` | خیر | `0.5` | فاصله بین درخواست‌های کانال‌ها |
| `ALLOW_EMPTY_OUTPUT` | خیر | `false` | اگر `false` باشد، خروجی خالی روی فایل قبلی نوشته نمی‌شود |
| `LOG_LEVEL` | خیر | `INFO` | سطح لاگ، مثل `INFO` یا `DEBUG` |

## رفتار خطاها

- اگر یک کانال نامعتبر یا خصوصی باشد، فقط همان کانال رد می‌شود و پردازش ادامه پیدا می‌کند.
- اگر Telegram محدودیت FloodWait کوتاه بدهد، برنامه صبر می‌کند و یک بار دوباره تلاش می‌کند.
- اگر هیچ کانفیگی پیدا نشود و `ALLOW_EMPTY_OUTPUT=false` باشد، فایل خروجی قبلی overwrite نمی‌شود.
- اگر session معتبر نباشد، برنامه با خطا متوقف می‌شود.

## نکات امنیتی

- `TELEGRAM_STRING_SESSION` را مثل رمز عبور نگهداری کنید.
- فایل `.env` را commit نکنید.
- فایل‌های `*.session` را commit نکنید.
- فقط از GitHub Secrets برای اطلاعات حساس استفاده کنید.
- اگر String Session افشا شد، از کلاینت رسمی Telegram نشست‌های فعال را terminate کنید و String Session جدید بسازید.
