"""Shared service for finding a YouTube video and emailing it."""

from __future__ import annotations

import os
import re

from agents.video_finder import build_video_email, extract_video_query, find_best_youtube_video
from agents.gemini_request_parser import parse_video_email_request_with_gemini
from agents.video_email_request import EMAIL_PATTERN, VideoEmailRequest, extract_email_addresses
from shared.email_client import send_gmail_message


def handle_video_request(message: str) -> str:
    youtube_api_key = _required_env("YOUTUBE_API_KEY")
    gmail_address = _required_env("GMAIL_ADDRESS")
    gmail_app_password = _required_env("GMAIL_APP_PASSWORD")
    default_to_email = os.getenv("EMAIL_TO", gmail_address).strip()
    request = _parse_request(message, default_to_email)

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


def _parse_request(message: str, default_to_email: str) -> VideoEmailRequest:
    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model = os.getenv("GEMINI_MODEL", "").strip() or "gemini-2.5-flash"
    if gemini_api_key:
        try:
            return parse_video_email_request_with_gemini(
                message=message,
                default_to_email=default_to_email,
                api_key=gemini_api_key,
                model=gemini_model,
            )
        except Exception:
            pass

    return parse_video_email_request(message, default_to_email)


def parse_video_email_request(message: str, default_to_email: str) -> VideoEmailRequest:
    recipients = extract_email_addresses(message) or extract_email_addresses(default_to_email)
    if not recipients:
        raise ValueError("No recipient email address was provided.")

    query_message = _remove_recipient_instruction(message) if extract_email_addresses(message) else message
    query = extract_video_query(query_message)
    return VideoEmailRequest(query=query, recipients=recipients)


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
