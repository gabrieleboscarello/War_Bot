import asyncio
import pandas as pd
import yfinance as yf
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ==========================
# CONFIG BOT TELEGRAM
# ==========================
TOKEN = "8624709220:AAE2-u1ZlO205PY85K_rxnDFTv1d6DIx57U"
CHAT_ID = "5921119236"

# ==========================
# CONFIG ASSET
# ==========================
SYMBOL = "EURUSD=X"   # cambia in "XAUUSD=X" per oro, "BTC-USD" per crypto
TIMEFRAME = "1h"      # intervallo di controllo dati
PERIOD = "60d"        # quanti giorni di dati prendere

bot = Bot(token=TOKEN)
last_signal = None

# ==========================
# FUNZIONI
# ==========================
def get_data():
    """Scarica dati da Yahoo Finance"""
    df = yf.download(
        SYMBOL,
        period=PERIOD,
        interval=TIMEFRAME,
        progress=False
    )
    if df.empty:
        print(f"⚠️ Nessun dato ricevuto per {SYMBOL}")
    return df

def generate_signal(df):
    """Genera segnali BUY/SELL basati su EMA e RSI"""
    if df.empty:
        return None

    # EMA
    df["ema50"] = df["Close"].ewm(span=50).mean()
    df["ema200"] = df["Close"].ewm(span=200).mean()

    # RSI
    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))

    last = df.iloc[-1]
    price = float(last["Close"])
    rsi = float(last["rsi"])

    # calcolo SL/TP
    sl_tp_pips = 0.0060 if "USD" in SYMBOL else 0.03  # forex vs altri

    if last["ema50"] > last["ema200"] and rsi < 35:
        sl = round(price - sl_tp_pips, 5)
        tp = round(price + sl_tp_pips*2, 5)
        return "BUY", price, sl, tp, rsi

    if last["ema50"] < last["ema200"] and rsi > 65:
        sl = round(price + sl_tp_pips, 5)
        tp = round(price - sl_tp_pips*2, 5)
        return "SELL", price, sl, tp, rsi

    return None

async def check_market():
    """Controlla il mercato e invia segnali su Telegram"""
    global last_signal
    df = get_data()
    signal = generate_signal(df)
    if not signal:
        return

    side, price, sl, tp, rsi = signal
    unique = f"{side}-{price}"
    if unique == last_signal:
        return  # evita duplicati
    last_signal = unique

    msg = (
        f"📊 {SYMBOL} SIGNAL\n"
        f"{'🟢 BUY' if side=='BUY' else '🔴 SELL'}\n"
        f"Entry: {price}\nSL: {sl}\nTP: {tp}\nRSI: {round(rsi,2)}"
    )
    await bot.send_message(chat_id=CHAT_ID, text=msg)

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_market, "interval", minutes=15)
    scheduler.start()
    await bot.send_message(chat_id=CHAT_ID, text=f"✅ Bot {SYMBOL} avviato")
    await asyncio.Event().wait()  # mantiene il bot attivo

# ==========================
# AVVIO BOT
# ==========================
if __name__ == "__main__":
    asyncio.run(main())
