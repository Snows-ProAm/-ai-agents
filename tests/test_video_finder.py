import pytest

from agents.video_finder import (
    VideoResult,
    build_video_email,
    extract_video_query,
    video_result_from_youtube_item,
)


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
