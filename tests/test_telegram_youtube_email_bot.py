from agents import telegram_youtube_email_bot


def test_handle_update_ignores_empty_messages(monkeypatch) -> None:
    sent_messages = []
    monkeypatch.setattr(
        telegram_youtube_email_bot,
        "telegram_send_message",
        lambda token, chat_id, text: sent_messages.append((chat_id, text)),
    )

    telegram_youtube_email_bot.handle_update(
        "token",
        {"message": {"chat": {"id": 123}, "text": "   "}},
    )

    assert sent_messages == []


def test_handle_update_rejects_unapproved_chat(monkeypatch) -> None:
    sent_messages = []
    monkeypatch.setattr(
        telegram_youtube_email_bot,
        "telegram_send_message",
        lambda token, chat_id, text: sent_messages.append((chat_id, text)),
    )

    telegram_youtube_email_bot.handle_update(
        "token",
        {"message": {"chat": {"id": 123}, "text": "find me best video on python"}},
        allowed_chat_id="999",
    )

    assert sent_messages == [("123", "This chat is not allowed to use this bot.")]


def test_handle_update_replies_to_help(monkeypatch) -> None:
    sent_messages = []
    monkeypatch.setattr(
        telegram_youtube_email_bot,
        "telegram_send_message",
        lambda token, chat_id, text: sent_messages.append((chat_id, text)),
    )

    telegram_youtube_email_bot.handle_update(
        "token",
        {"message": {"chat": {"id": 123}, "text": "/start"}},
    )

    assert sent_messages == [
        (
            "123",
            "Send a message like: find me best video on learning python on youtube send to person@example.com",
        )
    ]


def test_handle_update_runs_video_request(monkeypatch) -> None:
    sent_messages = []
    monkeypatch.setattr(
        telegram_youtube_email_bot,
        "telegram_send_message",
        lambda token, chat_id, text: sent_messages.append((chat_id, text)),
    )
    monkeypatch.setattr(
        telegram_youtube_email_bot,
        "handle_video_request",
        lambda text: f"handled: {text}",
    )

    telegram_youtube_email_bot.handle_update(
        "token",
        {"message": {"chat": {"id": 123}, "text": "find me best video on python"}},
    )

    assert sent_messages == [("123", "handled: find me best video on python")]


def test_handle_update_stores_contact_instead_of_running_video_request(monkeypatch) -> None:
    sent_messages = []
    video_requests = []
    monkeypatch.setattr(
        telegram_youtube_email_bot,
        "telegram_send_message",
        lambda token, chat_id, text: sent_messages.append((chat_id, text)),
    )
    monkeypatch.setattr(
        telegram_youtube_email_bot,
        "maybe_handle_contact_memory",
        lambda text: "Stored contact: Eva (evabellova@gmail.com)",
    )
    monkeypatch.setattr(
        telegram_youtube_email_bot,
        "handle_video_request",
        lambda text: video_requests.append(text),
    )

    telegram_youtube_email_bot.handle_update(
        "token",
        {"message": {"chat": {"id": 123}, "text": "store Evas email evabellova@gmail.com"}},
    )

    assert sent_messages == [("123", "Stored contact: Eva (evabellova@gmail.com)")]
    assert video_requests == []
