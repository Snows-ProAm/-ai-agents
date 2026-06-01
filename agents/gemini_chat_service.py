"""General Gemini chat replies for Telegram."""

from __future__ import annotations

import os
from typing import Any

from agents.gemini_request_parser import _generate_content


def handle_gemini_chat(message: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing required environment variable: GEMINI_API_KEY")

    model = os.getenv("GEMINI_MODEL", "").strip() or "gemini-2.5-flash"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "You are a practical personal AI assistant inside Telegram. "
                            "Answer directly and helpfully. Keep replies concise unless the "
                            "user asks for detail. If the user asks for current facts that may "
                            "have changed, say you may need web/search tooling before being "
                            "definitive.\n\n"
                            f"User message: {message}"
                        )
                    }
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 700,
        },
    }

    response_payload = _generate_content(api_key=api_key, model=model, payload=payload)
    reply = _parse_text_response(response_payload)
    if not reply:
        raise RuntimeError("Gemini returned an empty reply.")

    return reply[:3900]


def _parse_text_response(payload: dict[str, Any]) -> str:
    candidates = payload.get("candidates", [])
    if not candidates:
        return ""

    parts = candidates[0].get("content", {}).get("parts", [])
    return "".join(str(part.get("text", "")) for part in parts).strip()
