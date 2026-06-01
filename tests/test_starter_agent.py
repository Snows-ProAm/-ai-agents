from agents.starter_agent import respond


def test_respond_handles_message() -> None:
    response = respond("How should I structure an agent?")

    assert "Received: How should I structure an agent?" in response
    assert "Next step" in response


def test_respond_handles_empty_message() -> None:
    assert respond("   ") == "Ask me something and I will respond."
