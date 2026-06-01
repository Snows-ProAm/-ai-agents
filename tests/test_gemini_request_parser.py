from agents.gemini_request_parser import parse_video_email_request_with_gemini


def test_parse_video_email_request_with_gemini(monkeypatch) -> None:
    def fake_generate_content(*, api_key, model, payload):
        assert api_key == "gemini-key"
        assert model == "gemini-2.5-flash"
        assert "send john@example.com" in payload["contents"][0]["parts"][0]["text"]
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": (
                                    '{"query": "best beginner python tutorial", '
                                    '"recipients": ["john@example.com"]}'
                                )
                            }
                        ]
                    }
                }
            ]
        }

    monkeypatch.setattr("agents.gemini_request_parser._generate_content", fake_generate_content)

    request = parse_video_email_request_with_gemini(
        message="send john@example.com the best video for beginner python",
        default_to_email="fallback@example.com",
        api_key="gemini-key",
        model="gemini-2.5-flash",
    )

    assert request.query == "best beginner python tutorial"
    assert request.recipients == ["john@example.com"]


def test_parse_video_email_request_with_gemini_uses_default_recipient(monkeypatch) -> None:
    monkeypatch.setattr(
        "agents.gemini_request_parser._generate_content",
        lambda **kwargs: {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": (
                                    '{"query": "LangGraph tutorial", '
                                    '"recipients": []}'
                                )
                            }
                        ]
                    }
                }
            ]
        },
    )

    request = parse_video_email_request_with_gemini(
        message="find a LangGraph tutorial",
        default_to_email="fallback@example.com, other@example.com",
        api_key="gemini-key",
        model="gemini-2.5-flash",
    )

    assert request.query == "LangGraph tutorial"
    assert request.recipients == ["fallback@example.com", "other@example.com"]
