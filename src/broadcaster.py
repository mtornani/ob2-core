#!/usr/bin/env python3
"""Cronjob: legge dati giocatori, formatta con Gemini, posta su X e Telegram."""
import asyncio
import json
import os
from pathlib import Path

import google.generativeai as genai
import tweepy
from telegram import Bot

# --- Env ---
GEMINI_API_KEY      = os.environ["GEMINI_API_KEY"]
X_BEARER_TOKEN      = os.environ["X_BEARER_TOKEN"]
X_API_KEY           = os.environ["X_API_KEY"]
X_API_SECRET        = os.environ["X_API_SECRET"]
X_ACCESS_TOKEN      = os.environ["X_ACCESS_TOKEN"]
X_ACCESS_SECRET     = os.environ["X_ACCESS_SECRET"]
TELEGRAM_BOT_TOKEN  = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]

PREMIUM_LINK = "https://buy.stripe.com/PLACEHOLDER"
DATA_PATH    = Path("eater-of-logs/data.json")

MOCK_DATA = [
    {
        "name": "Sergej Levak",
        "team": "Atalanta U23",
        "value_eur": "800k",
        "free_agent_days_left": 57,
        "appearances": 30,
        "note": "Art.99bis",
    },
    {
        "name": "Chec Benelli Doumbia",
        "team": "Team Altamura",
        "year_of_birth": 2007,
        "free_agent_days_left": 63,
        "serie_a_clubs_interested": 5,
    },
]


def load_players() -> list[dict]:
    if DATA_PATH.exists():
        return json.loads(DATA_PATH.read_text())
    print("[WARN] data.json non trovato — uso mock.")
    return MOCK_DATA


def format_with_gemini(player: dict) -> str:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = (
        "Sei un analista di mercato calcistico. "
        "Scrivi un post per X/Telegram stile Fabrizio Romano ma basato sui dati. "
        "Massimo 220 caratteri (lascia spazio per un link in coda). "
        "Emoji 🚨 consentita solo all'inizio. Niente fronzoli. Solo dati chiave e urgenza. "
        "Lingua: italiano. "
        f"Dati giocatore: {json.dumps(player, ensure_ascii=False)}"
    )
    return model.generate_content(prompt).text.strip()


def post_to_x(text: str) -> None:
    client = tweepy.Client(
        bearer_token=X_BEARER_TOKEN,
        consumer_key=X_API_KEY,
        consumer_secret=X_API_SECRET,
        access_token=X_ACCESS_TOKEN,
        access_token_secret=X_ACCESS_SECRET,
    )
    client.create_tweet(text=text)


async def _send_telegram(text: str) -> None:
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    async with bot:
        await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=text)


def post_to_telegram(text: str) -> None:
    asyncio.run(_send_telegram(text))


def broadcast(player: dict) -> None:
    body    = format_with_gemini(player)
    message = f"{body}\n\n{PREMIUM_LINK}"

    post_to_x(message)
    post_to_telegram(message)
    print(f"[OK] {player.get('name', '?')} — {len(message)} chars")


if __name__ == "__main__":
    for player in load_players():
        broadcast(player)
