"""Register the deployed Telegram webhook URL."""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parents[1]))


def main() -> None:
    load_dotenv()
    token = _required_env("TELEGRAM_BOT_TOKEN")

    if len(sys.argv) != 2:
        raise SystemExit("Usage: python agents/set_telegram_webhook.py https://your-app.vercel.app/api/telegram")

    webhook_url = sys.argv[1].strip()
    if not webhook_url.startswith("https://"):
        raise SystemExit("Telegram webhook URL must start with https://")

    response = set_telegram_webhook(token, webhook_url)
    print(json.dumps(response, indent=2))


def set_telegram_webhook(token: str, webhook_url: str) -> dict:
    api_url = f"https://api.telegram.org/bot{token}/setWebhook"
    data = urllib.parse.urlencode({"url": webhook_url}).encode("utf-8")
    request = urllib.request.Request(api_url, data=data, method="POST")

    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


if __name__ == "__main__":
    main()
