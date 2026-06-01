"""Telegram bot that emails the best YouTube video for a requested topic."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.contact_memory_service import maybe_handle_contact_memory
from agents.gemini_chat_service import handle_gemini_chat
from agents.youtube_email_service import handle_video_request


TELEGRAM_API_URL = "https://api.telegram.org"


def run_bot() -> None:
    _load_dotenv_if_available()
    token = _required_env("TELEGRAM_BOT_TOKEN")
    allowed_chat_id = os.getenv("TELEGRAM_ALLOWED_CHAT_ID", "").strip()
    offset = 0

    print("Telegram YouTube email bot is running. Press Ctrl+C to stop.")
    while True:
        updates = telegram_get_updates(token, offset)
        for update in updates:
            offset = max(offset, update["update_id"] + 1)
            handle_update(token, update, allowed_chat_id)

        time.sleep(1)


def handle_update(token: str, update: dict[str, Any], allowed_chat_id: str = "") -> None:
    message = update.get("message", {})
    chat = message.get("chat", {})
    chat_id = str(chat.get("id", ""))
    text = message.get("text", "").strip()

    if not chat_id or not text:
        return

    if allowed_chat_id and chat_id != allowed_chat_id:
        telegram_send_message(token, chat_id, "This chat is not allowed to use this bot.")
        return

    if text.lower() in {"/start", "help", "/help"}:
        telegram_send_message(
            token,
            chat_id,
            "Send a message like: find me best video on learning python on youtube send to person@example.com",
        )
        return

    try:
        reply = maybe_handle_contact_memory(text)
        if not reply:
            reply = handle_video_request(text) if _looks_like_video_request(text) else handle_gemini_chat(text)
    except Exception as exc:
        reply = f"I could not complete that request: {exc}"

    telegram_send_message(token, chat_id, reply)


def telegram_get_updates(token: str, offset: int) -> list[dict[str, Any]]:
    params = {"timeout": 25, "offset": offset}
    payload = _telegram_request(token, "getUpdates", params)
    return payload.get("result", [])


def telegram_send_message(token: str, chat_id: str, text: str) -> None:
    _telegram_request(token, "sendMessage", {"chat_id": chat_id, "text": text})


def _looks_like_video_request(text: str) -> bool:
    lowered = text.lower()
    video_markers = [
        "youtube",
        "video",
        "videos",
        "best video",
        "find me best",
        "find a good video",
        "grab a useful video",
    ]
    return any(marker in lowered for marker in video_markers)


def _telegram_request(token: str, method: str, params: dict[str, Any]) -> dict[str, Any]:
    url = f"{TELEGRAM_API_URL}/bot{token}/{method}"
    data = urllib.parse.urlencode(params).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Telegram API error {exc.code}: {detail}") from exc

    if not payload.get("ok"):
        description = payload.get("description", "Unknown Telegram API error")
        raise RuntimeError(description)

    return payload


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError:
        return

    load_dotenv()


if __name__ == "__main__":
    run_bot()
