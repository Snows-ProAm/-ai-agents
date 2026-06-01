"""Vercel Flask entrypoint for the Telegram webhook."""

from __future__ import annotations

import os

from flask import Flask, request

from agents.telegram_youtube_email_bot import handle_update


app = Flask(__name__)


@app.get("/")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "telegram-webhook"}


@app.get("/api/telegram")
def telegram_health() -> dict[str, str]:
    return {"status": "ok", "service": "telegram-webhook"}


@app.post("/api/telegram")
def telegram_webhook() -> tuple[dict[str, str], int]:
    token = _required_env("TELEGRAM_BOT_TOKEN")
    allowed_chat_id = os.getenv("TELEGRAM_ALLOWED_CHAT_ID", "").strip()
    update = request.get_json(silent=True) or {}

    handle_update(token, update, allowed_chat_id)
    return {"status": "ok"}, 200


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
