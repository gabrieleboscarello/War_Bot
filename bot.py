import os
import feedparser
import asyncio
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

# Carica variabili da .env
load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
RSS_URL = os.getenv("RSS_URL")  # Esempio: Google News RSS
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 60))  # default 60 secondi

bot = Bot(token=TOKEN)
sent_links = set()

# Keywords per filtraggio
KEYWORDS = [
    "missile", "attacco", "esplosione",
    "nato", "drone", "russia", "ukraine",
    "gaza", "israel", "iran"
]

async def check_news():
    feed = feedparser.parse(RSS_URL)

    for entry in feed.entries[:10]:
        link = entry.link

        if link in sent_links:
            continue

        title_lower = entry.title.lower()
        if not any(k in title_lower for k in KEYWORDS):
            continue

        sent_links.add(link)
        message = f"🚨 *ULTIMA NOTIZIA GUERRA*\n\n*{entry.title}*\n🔗 {link}"

        try:
            await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
            print(f"Inviata notizia: {entry.title}")
        except Exception as e:
            print(f"Errore invio notizia: {e}")

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_news, "interval", seconds=CHECK_INTERVAL)
    scheduler.start()
    print("Bot avviato...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
