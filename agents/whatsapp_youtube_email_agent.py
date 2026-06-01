"""WhatsApp webhook that emails the best YouTube video for a requested topic."""

from __future__ import annotations

import os
import sys
import xml.sax.saxutils
from pathlib import Path

from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.youtube_email_service import handle_video_request


load_dotenv()


def create_app():
    from flask import Flask, Response, request

    app = Flask(__name__)

    @app.post("/whatsapp")
    def whatsapp_webhook() -> Response:
        body = request.form.get("Body", "")
        sender = request.form.get("From", "")
        allowed_sender = os.getenv("WHATSAPP_ALLOWED_FROM", "").strip()

        if allowed_sender and sender != allowed_sender:
            reply = "This WhatsApp number is not allowed to use this agent."
            return _twilio_response(reply)

        try:
            reply = handle_video_request(body)
        except Exception as exc:
            reply = f"I could not complete that request: {exc}"

        return _twilio_response(reply)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def _twilio_response(message: str):
    from flask import Response

    escaped = xml.sax.saxutils.escape(message)
    response_xml = (
        f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{escaped}</Message></Response>'
    )
    return Response(response_xml, mimetype="application/xml")


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
