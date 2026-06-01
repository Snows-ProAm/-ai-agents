"""Gemini-powered parser for Telegram video email requests."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

from agents.video_email_request import EMAIL_PATTERN, VideoEmailRequest, extract_email_addresses


GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def parse_video_email_request_with_gemini(
    *,
    message: str,
    default_to_email: str,
    api_key: str,
    model: str,
) -> VideoEmailRequest:
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "Extract a YouTube search topic and recipient email addresses from "
                            "this Telegram message. Return only JSON with keys query and "
                            "recipients. recipients must contain only explicit email addresses "
                            "from the message. Do not invent emails.\n\n"
                            f"Message: {message}"
                        )
                    }
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
        },
    }

    response_payload = _generate_content(api_key=api_key, model=model, payload=payload)
    parsed = _parse_gemini_json_response(response_payload)
    query = str(parsed.get("query", "")).strip()
    recipients = _clean_gemini_recipients(parsed.get("recipients", []))

    if not query:
        raise ValueError("Gemini did not return a search query.")

    if not recipients:
        recipients = extract_email_addresses(default_to_email)

    if not recipients:
        raise ValueError("No recipient email address was provided.")

    return VideoEmailRequest(query=query, recipients=recipients)


def _generate_content(*, api_key: str, model: str, payload: dict[str, Any]) -> dict[str, Any]:
    encoded_model = urllib.parse.quote(model, safe="")
    url = f"{GEMINI_API_BASE_URL}/{encoded_model}:generateContent?key={api_key}"
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _parse_gemini_json_response(payload: dict[str, Any]) -> dict[str, Any]:
    candidates = payload.get("candidates", [])
    if not candidates:
        raise ValueError("Gemini response did not include candidates.")

    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(str(part.get("text", "")) for part in parts).strip()
    if not text:
        raise ValueError("Gemini response did not include text.")

    return json.loads(text)


def _clean_gemini_recipients(value: Any) -> list[str]:
    values = value if isinstance(value, list) else [value]
    recipients: list[str] = []
    seen: set[str] = set()
    for item in values:
        match = EMAIL_PATTERN.fullmatch(str(item).strip())
        if not match:
            continue

        email = match.group(0).lower()
        if email not in seen:
            recipients.append(email)
            seen.add(email)

    return recipients
