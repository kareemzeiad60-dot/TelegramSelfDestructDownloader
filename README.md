# Telegram Self-Destruct Downloader (Python)

## الإعداد

### 1. أول مرة — عمل Login وحفظ الـ Session

```bash
pip install -r requirements.txt

TG_API_ID=123456 TG_API_HASH=your_hash TG_PHONE=+201234567890 python main.py
```

ادخل الكود اللي جالك من تيليجرام.
هيتعمل ملف session تلقائياً باسم `session_201234567890.session`

### 2. رفع الـ Session كـ Secret

حوّل الملف لـ Base64:
```bash
base64 session_201234567890.session
```
انسخ الناتج وحطه كـ secret باسم `TG_SESSION_B64`

### 3. النشر على Railway

1. ارفع الملفات على GitHub
2. افتح railway.app → New Project → من GitHub
3. في Variables حط:

| Variable | القيمة |
|----------|--------|
| `TG_API_ID` | رقم API ID |
| `TG_API_HASH` | API Hash |
| `TG_PHONE` | رقم التليفون مع + |
| `TG_SESSION_B64` | ناتج الـ base64 |

4. Deploy ✅

## Variables اختيارية

| Variable | Default | الوصف |
|----------|---------|-------|
| `TG_MAX_FILE_SIZE_MB` | 250 | أقصى حجم للملف |
| `TG_INCLUDE_CHAT_TITLE` | true | إضافة اسم الشات في الـ caption |
| `TG_FORWARD_TO_SAVED` | true | إرسال لـ Saved Messages |
