"""Find YouTube videos and format email messages for the WhatsApp agent."""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


@dataclass(frozen=True)
class VideoResult:
    title: str
    channel: str
    url: str
    description: str


def extract_video_query(message: str) -> str:
    cleaned = " ".join(message.strip().split())
    if not cleaned:
        raise ValueError("Message cannot be empty.")

    patterns = [
        r"^find me (?:the )?best video (?:on|about|for)\s+(.+?)(?:\s+on youtube|\s+youtube)?$",
        r"^best video (?:on|about|for)\s+(.+?)(?:\s+on youtube|\s+youtube)?$",
        r"^youtube\s+(.+)$",
    ]
    for pattern in patterns:
        match = re.match(pattern, cleaned, flags=re.IGNORECASE)
        if match:
            return _clean_query(match.group(1))

    lowered = cleaned.lower()
    if "youtube" in lowered:
        without_youtube = re.sub(r"\byoutube\b", "", cleaned, flags=re.IGNORECASE)
        return _clean_query(without_youtube)

    return _clean_query(cleaned)


def find_best_youtube_video(query: str, api_key: str) -> VideoResult:
    cleaned_query = _clean_query(query)
    params = {
        "part": "snippet",
        "q": cleaned_query,
        "type": "video",
        "maxResults": "1",
        "order": "relevance",
        "safeSearch": "moderate",
        "key": api_key,
    }
    url = f"{YOUTUBE_SEARCH_URL}?{urllib.parse.urlencode(params)}"

    with urllib.request.urlopen(url, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))

    items = payload.get("items", [])
    if not items:
        raise RuntimeError(f"No YouTube videos found for: {cleaned_query}")

    return video_result_from_youtube_item(items[0])


def video_result_from_youtube_item(item: dict[str, Any]) -> VideoResult:
    video_id = item["id"]["videoId"]
    snippet = item["snippet"]
    return VideoResult(
        title=snippet["title"],
        channel=snippet["channelTitle"],
        url=f"https://www.youtube.com/watch?v={video_id}",
        description=snippet.get("description", ""),
    )


def build_video_email(query: str, video: VideoResult) -> tuple[str, str]:
    subject = f"Best YouTube video for: {query}"
    body = (
        f"Search: {query}\n\n"
        f"{video.title}\n"
        f"Channel: {video.channel}\n"
        f"Link: {video.url}\n\n"
        f"{video.description}"
    ).strip()
    return subject, body


def _clean_query(value: str) -> str:
    cleaned = value.strip(" .?!")
    if not cleaned:
        raise ValueError("Could not find a YouTube search topic in the message.")
    return cleaned
