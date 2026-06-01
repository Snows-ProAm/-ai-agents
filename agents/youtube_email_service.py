"""Shared service for finding a YouTube video and emailing it."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

from agents.video_finder import build_video_email, extract_video_query, find_best_youtube_video
from shared.email_client import send_gmail_message

EMAIL_PATTERN = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", flags=re.IGNORECASE)


@dataclass(frozen=True)
class VideoEmailRequest:
    query: str
    recipients: list[str]


def handle_video_request(message: str) -> str:
    youtube_api_key = _required_env("YOUTUBE_API_KEY")
    gmail_address = _required_env("GMAIL_ADDRESS")
    gmail_app_password = _required_env("GMAIL_APP_PASSWORD")
    default_to_email = os.getenv("EMAIL_TO", gmail_address).strip()
    request = parse_video_email_request(message, default_to_email)

    video = find_best_youtube_video(request.query, youtube_api_key)
    subject, body = build_video_email(request.query, video)

    send_gmail_message(
        gmail_address=gmail_address,
        gmail_app_password=gmail_app_password,
        to_email=request.recipients,
        subject=subject,
        body=body,
    )
    return f"Found and emailed: {video.title} to {', '.join(request.recipients)}"


def parse_video_email_request(message: str, default_to_email: str) -> VideoEmailRequest:
    recipients = _extract_email_addresses(message) or _extract_email_addresses(default_to_email)
    if not recipients:
        raise ValueError("No recipient email address was provided.")

    query_message = _remove_recipient_instruction(message) if _extract_email_addresses(message) else message
    query = extract_video_query(query_message)
    return VideoEmailRequest(query=query, recipients=recipients)


def _extract_email_addresses(value: str) -> list[str]:
    addresses: list[str] = []
    seen: set[str] = set()
    for match in EMAIL_PATTERN.finditer(value):
        address = match.group(0).strip().lower()
        if address not in seen:
            addresses.append(address)
            seen.add(address)
    return addresses


def _remove_recipient_instruction(message: str) -> str:
    first_email = EMAIL_PATTERN.search(message)
    if not first_email:
        return message

    cleaned = message[: first_email.start()]
    trailing_instruction_patterns = [
        r"(?:,|\band\b)?\s*(?:please\s+)?(?:send|email|mail)(?:\s+(?:it|this|that|the\s+video))?\s+(?:to\s*)?$",
        r"(?:,|\band\b)?\s*to\s*$",
    ]
    previous = ""
    while previous != cleaned:
        previous = cleaned
        for pattern in trailing_instruction_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()

    return cleaned


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
