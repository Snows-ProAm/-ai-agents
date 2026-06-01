"""Vercel Python function for Telegram updates."""

from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.telegram_youtube_email_bot import handle_update


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        _send_json(self, 200, {"status": "ok", "service": "telegram-webhook"})

    def do_POST(self) -> None:
        token = _required_env("TELEGRAM_BOT_TOKEN")
        allowed_chat_id = os.getenv("TELEGRAM_ALLOWED_CHAT_ID", "").strip()
        update = _read_json_body(self)

        handle_update(token, update, allowed_chat_id)
        _send_json(self, 200, {"status": "ok"})


def _read_json_body(request: BaseHTTPRequestHandler) -> dict:
    length = int(request.headers.get("content-length", "0"))
    if length <= 0:
        return {}

    raw_body = request.rfile.read(length)
    return json.loads(raw_body.decode("utf-8"))


def _send_json(request: BaseHTTPRequestHandler, status_code: int, payload: dict[str, str]) -> None:
    body = json.dumps(payload).encode("utf-8")
    request.send_response(status_code)
    request.send_header("Content-Type", "application/json")
    request.send_header("Content-Length", str(len(body)))
    request.end_headers()
    request.wfile.write(body)


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
