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
        file_extension = ".bin"

        if isinstance(media, MessageMediaPhoto):
            ttl = getattr(media, "ttl_seconds", None)
            file_extension = ".jpg"
        elif isinstance(media, MessageMediaDocument):
            ttl = getattr(media, "ttl_seconds", None)
            attributes = getattr(media.document, "attributes", [])
            is_video = any(hasattr(attr, "duration") for attr in attributes)
            file_extension = ".mp4" if is_video else ".bin"

        if not ttl:
            return

        log.info(f"View-once media detected from {chat_title} (ttl={ttl}s)")
        print(f"📥 View-once from {chat_title}")

        try:
            # تحميل الملف مؤقتاً كـ ملف حقيقي وليس باينري في الذاكرة لتجنب مشكلة unnamed
            temp_filename = f"media_{msg.id}{file_extension}"
            
            # تحميل الميديا مباشرة إلى ملف على القرص
            path = await msg.download_media(file=temp_filename)

            if not path or not os.path.exists(path):
                log.warning(f"Could not download media from {chat_title}")
                return

            size_mb = os.path.getsize(path) / (1024 * 1024)
            if size_mb > MAX_FILE_SIZE_MB:
                log.info(f"Skipping: {size_mb:.1f}MB exceeds limit {MAX_FILE_SIZE_MB}MB")
                print(f"⏭️ Skipping large file ({size_mb:.1f}MB) from {chat_title}")
                try: os.remove(path)
                except: pass
                return

            if FORWARD_TO_SAVED:
                caption = f"From: {chat_title}" if INCLUDE_CHAT_TITLE else ""
                
                # إرسال الملف الحقيقي من المسار، Telethon سيتعرف على امتداده تلقائياً بنسبة 100%
                if file_extension == ".jpg":
                    await client.send_file("me", path, caption=caption, force_file=False)
                else:
                    await client.send_file("me", path, caption=caption)
                
                log.info(f"Forwarded to Saved Messages from {chat_title}")
                print(f"✅ Forwarded from {chat_title} successfully")

            # حذف الملف المؤقت بعد إرساله بنجاح لضمان عدم امتلاء السيرفر
            try:
                os.remove(path)
            except Exception as e:
                log.error(f"Failed to delete temp file {path}: {e}")

        except Exception as e:
            log.error(f"Error processing message from {chat_title}: {e}")
            print(f"❌ Error from {chat_title}: {e}")

    print("👂 Listening for messages... (Ctrl+C to stop)")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
            
