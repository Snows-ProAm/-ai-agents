import pytest

from agents.video_finder import (
    VideoResult,
    build_video_email,
    extract_video_query,
    video_result_from_youtube_item,
)
from agents.youtube_email_service import parse_video_email_request
from agents import youtube_email_service


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("find me best video on learning python on youtube", "learning python"),
        ("find me the best video about supabase youtube", "supabase"),
        ("best video for AI agents", "AI agents"),
        ("youtube LangGraph tutorial", "LangGraph tutorial"),
        ("best prompt engineering course", "best prompt engineering course"),
    ],
)
def test_extract_video_query(message: str, expected: str) -> None:
    assert extract_video_query(message) == expected


def test_extract_video_query_rejects_empty_message() -> None:
    with pytest.raises(ValueError, match="Message cannot be empty"):
        extract_video_query("   ")


def test_video_result_from_youtube_item() -> None:
    item = {
        "id": {"videoId": "abc123"},
        "snippet": {
            "title": "Python Agents",
            "channelTitle": "Code Channel",
            "description": "A practical guide.",
        },
    }

    result = video_result_from_youtube_item(item)

    assert result == VideoResult(
        title="Python Agents",
        channel="Code Channel",
        url="https://www.youtube.com/watch?v=abc123",
        description="A practical guide.",
    )


def test_build_video_email() -> None:
    subject, body = build_video_email(
        "python agents",
        VideoResult(
            title="Python Agents",
            channel="Code Channel",
            url="https://www.youtube.com/watch?v=abc123",
            description="A practical guide.",
        ),
    )

    assert subject == "Best YouTube video for: python agents"
    assert "Python Agents" in body
    assert "https://www.youtube.com/watch?v=abc123" in body


def test_parse_video_email_request_uses_recipients_from_message() -> None:
    request = parse_video_email_request(
        "find me best video on learning python on youtube send to sam@example.com and jo@example.com",
        "fallback@example.com",
    )

    assert request.query == "learning python"
    assert request.recipients == ["sam@example.com", "jo@example.com"]


def test_parse_video_email_request_falls_back_to_default_recipients() -> None:
    request = parse_video_email_request(
        "find me best video on learning python on youtube",
        "fallback@example.com, other@example.com",
    )

    assert request.query == "learning python"
    assert request.recipients == ["fallback@example.com", "other@example.com"]


def test_parse_request_uses_default_gemini_model_when_env_is_blank(monkeypatch) -> None:
    seen = {}

    def fake_gemini_parse(*, message, default_to_email, api_key, model):
        seen["model"] = model
        return youtube_email_service.VideoEmailRequest(
            query="python tutorial",
            recipients=["person@example.com"],
        )

    monkeypatch.setenv("GEMINI_API_KEY", "key")
    monkeypatch.setenv("GEMINI_MODEL", "")
    monkeypatch.setattr(
        youtube_email_service,
        "parse_video_email_request_with_gemini",
        fake_gemini_parse,
    )

    request = youtube_email_service._parse_request(
        "send person@example.com a python tutorial",
        "fallback@example.com",
    )

    assert seen["model"] == "gemini-2.5-flash"
    assert request.query == "python tutorial"
