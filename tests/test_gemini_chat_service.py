from agents.gemini_chat_service import _parse_text_response


def test_parse_text_response() -> None:
    reply = _parse_text_response(
        {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Alex Hormozi is an entrepreneur "},
                            {"text": "and investor."},
                        ]
                    }
                }
            ]
        }
    )

    assert reply == "Alex Hormozi is an entrepreneur and investor."
