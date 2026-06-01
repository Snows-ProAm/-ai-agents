from app import app


def test_health() -> None:
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert response.get_json() == {"service": "telegram-webhook", "status": "ok"}


def test_telegram_health() -> None:
    client = app.test_client()

    response = client.get("/api/telegram")

    assert response.status_code == 200
    assert response.get_json() == {"service": "telegram-webhook", "status": "ok"}


def test_telegram_webhook_handles_update(monkeypatch) -> None:
    calls = []
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setattr(
        "app.handle_update",
        lambda token, update, allowed_chat_id="": calls.append((token, update, allowed_chat_id)),
    )
    client = app.test_client()

    response = client.post(
        "/api/telegram",
        json={"message": {"chat": {"id": 123}, "text": "find me best video on python"}},
    )

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
    assert calls == [
        (
            "token",
            {"message": {"chat": {"id": 123}, "text": "find me best video on python"}},
            "",
        )
    ]
