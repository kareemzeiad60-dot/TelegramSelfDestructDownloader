import asyncio
import os
import logging
import base64
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ── Config من environment variables ──
API_ID   = int(os.environ.get("TG_API_ID", 0))
API_HASH = os.environ.get("TG_API_HASH", "")
PHONE    = os.environ.get("TG_PHONE", "")

if not API_ID or not API_HASH or not PHONE:
    log.critical("❌ خطأ: يجب تعيين TG_API_ID و TG_API_HASH و TG_PHONE في السيكريت!")
    exit(1)

raw_size = os.environ.get("TG_MAX_FILE_SIZE_MB", "").strip()
MAX_FILE_SIZE_MB = int(raw_size) if raw_size else 250

INCLUDE_CHAT_TITLE = os.environ.get("TG_INCLUDE_CHAT_TITLE", "true").lower() == "true"
FORWARD_TO_SAVED   = os.environ.get("TG_FORWARD_TO_SAVED", "true").lower() == "true"

SESSION_NAME = f"session_{PHONE.replace('+','').replace(' ','').replace('-','')}"


def restore_session():
    """لو في TG_SESSION_B64 كـ env var، بيكتب الـ session file على الديسك."""
    b64 = os.environ.get("TG_SESSION_B64")
    if not b64:
        return
    path = f"{SESSION_NAME}.session"
    if os.path.exists(path):
        return
    try:
        data = base64.b64decode(b64)
        with open(path, "wb") as f:
            f.write(data)
        log.info(f"Session restored from TG_SESSION_B64 → {path}")
    except Exception as e:
        log.error(f"Failed to restore session: {e}")


async def main():
    restore_session()
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    await client.start(phone=PHONE)
    me = await client.get_me()
    log.info(f"Logged in as: {me.username or f'{me.first_name} {me.last_name}'.strip()}")
    print(f"✅ Logged in as: {me.username or me.first_name}")

    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        msg = event.message

        if msg.out:
            return

        chat_title = "Unknown"
        try:
            chat = await event.get_chat()
            chat_title = getattr(chat, "title", None) \
                      or getattr(chat, "username", None) \
                      or f"{getattr(chat, 'first_name', '')} {getattr(chat, 'last_name', '')}".strip() \
                      or "Unknown"
        except Exception:
            pass

        media = msg.media
        if not media:
            return

        ttl = None
        file_extension = ".bin"  # امتداد افتراضي لو فشل التحديد

        # تحديد نوع الميديا والامتداد المناسب لها
        if isinstance(media, MessageMediaPhoto):
            ttl = getattr(media, "ttl_seconds", None)
            file_extension = ".jpg"  # الصور ذاتية التدمير تكون غالباً JPG
        elif isinstance(media, MessageMediaDocument):
            ttl = getattr(media, "ttl_seconds", None)
            # محاولة جلب الامتداد الفعلي للملف أو تحديد امتداد فيديو افتراضي
            attributes = getattr(media.document, "attributes", [])
            is_video = any(hasattr(attr, "duration") for attr in attributes)
            file_extension = ".mp4" if is_video else ".bin"

        if not ttl:
            return

        log.info(f"View-once media detected from {chat_title} (ttl={ttl}s)")
        print(f"📥 View-once from {chat_title}")

        try:
            data = await msg.download_media(bytes)

            if data is None:
                log.warning(f"Could not download media from {chat_title}")
                return

            size_mb = len(data) / (1024 * 1024)
            if size_mb > MAX_FILE_SIZE_MB:
                log.info(f"Skipping: {size_mb:.1f}MB exceeds limit {MAX_FILE_SIZE_MB}MB")
                print(f"⏭️ Skipping large file ({size_mb:.1f}MB) from {chat_title}")
                return

            if FORWARD_TO_SAVED:
                caption = f"From: {chat_title}" if INCLUDE_CHAT_TITLE else ""
                
                # التعديل هنا: فحص نوع الملف لإرساله بالطريقة الصحيحة للمعاينة
                if file_extension == ".jpg":
                    # إرسال كصورة حقيقية ومضغوطة تظهر في المحادثة مباشرة
                    await client.send_file("me", data, caption=caption, force_file=False)
                    log.info(f"Forwarded as photo to Saved Messages from {chat_title}")
                else:
                    # إرسال كملف فيديو أو مستند مع تعيين الاسم والامتداد
                    temp_filename = f"media_{msg.id}{file_extension}"
                    await client.send_file("me", data, caption=caption, file_name=temp_filename)
                    log.info(f"Forwarded as file ({temp_filename}) to Saved Messages from {chat_title}")
                
                print(f"✅ Forwarded from {chat_title} successfully")

        except Exception as e:
            log.error(f"Error processing message from {chat_title}: {e}")
            print(f"❌ Error from {chat_title}: {e}")

    print("👂 Listening for messages... (Ctrl+C to stop)")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
    
