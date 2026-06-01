import io
import json

from api import telegram


class FakeRequest:
    def __init__(self, body: dict | None = None) -> None:
        encoded_body = json.dumps(body or {}).encode("utf-8")
        self.headers = {"content-length": str(len(encoded_body))}
        self.rfile = io.BytesIO(encoded_body)
        self.responses = []
        self.response_headers = []
        self.wfile = io.BytesIO()

    def send_response(self, status_code: int) -> None:
        self.responses.append(status_code)

    def send_header(self, name: str, value: str) -> None:
        self.response_headers.append((name, value))

    def end_headers(self) -> None:
        pass


def test_read_json_body() -> None:
    request = FakeRequest({"message": {"text": "hello"}})

    assert telegram._read_json_body(request) == {"message": {"text": "hello"}}


def test_send_json() -> None:
    request = FakeRequest()

    telegram._send_json(request, 200, {"status": "ok"})

    assert request.responses == [200]
    assert ("Content-Type", "application/json") in request.response_headers
    assert json.loads(request.wfile.getvalue().decode("utf-8")) == {"status": "ok"}


def test_required_env(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")

    assert telegram._required_env("TELEGRAM_BOT_TOKEN") == "token"


def test_handle_update_import_is_patchable(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(
        telegram,
        "handle_update",
        lambda token, update, allowed_chat_id="": calls.append((token, update, allowed_chat_id)),
    )
    telegram.handle_update(
        "token",
        {"message": {"chat": {"id": 123}, "text": "find me best video on python"}},
        "",
    )

    assert calls == [
        (
            "token",
            {"message": {"chat": {"id": 123}, "text": "find me best video on python"}},
            "",
        )
    ]
