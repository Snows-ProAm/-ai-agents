"""Shared service for finding a YouTube video and emailing it."""

from __future__ import annotations

import os

from agents.video_finder import build_video_email, extract_video_query, find_best_youtube_video
from shared.email_client import send_gmail_message


def handle_video_request(message: str) -> str:
    youtube_api_key = _required_env("YOUTUBE_API_KEY")
    gmail_address = _required_env("GMAIL_ADDRESS")
    gmail_app_password = _required_env("GMAIL_APP_PASSWORD")
    to_email = os.getenv("EMAIL_TO", gmail_address).strip()

    query = extract_video_query(message)
    video = find_best_youtube_video(query, youtube_api_key)
    subject, body = build_video_email(query, video)

    send_gmail_message(
        gmail_address=gmail_address,
        gmail_app_password=gmail_app_password,
        to_email=to_email,
        subject=subject,
        body=body,
    )
    return f"Found and emailed: {video.title}"


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
