"""
شغّل الملف ده مرة واحدة بس عشان تعمل login وتاخد الـ session
python login.py
"""
import asyncio
import base64
import os
from telethon import TelegramClient

def ask(prompt):
    val = input(prompt).strip()
    if not val:
        print("لازم تدخل قيمة!")
        exit(1)
    return val

async def main():
    print("=== Telegram Login ===\n")
    api_id   = int(ask("API ID: "))
    api_hash = ask("API Hash: ")
    phone    = ask("Phone (with +): ")

    safe     = phone.replace("+","").replace(" ","").replace("-","")
    session  = f"session_{safe}"

    client = TelegramClient(session, api_id, api_hash)
    await client.start(phone=phone)

    me = await client.get_me()
    print(f"\nLogged in as: {me.username or me.first_name}")

    # ── طلع الـ session كـ Base64 ──
    session_file = session + ".session"
    if os.path.exists(session_file):
        with open(session_file, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()

        # احفظه في ملف
        with open("session.b64.txt", "w") as f:
            f.write(b64)

        print("\n" + "="*50)
        print("Session saved to: session.b64.txt")
        print("Copy the contents and add as Railway variable: TG_SESSION_B64")
        print("="*50)
    else:
        print("Session file not found!")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
