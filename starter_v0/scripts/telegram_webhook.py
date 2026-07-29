from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env  # noqa: E402
from tools._shared import TIMEOUT  # noqa: E402


def telegram_api(method: str, payload: dict[str, object] | None = None) -> dict[str, object]:
    load_lab_env(ROOT)
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN")
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/{method}",
            json=payload or {},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        message = re.sub(r"/bot[^/\s]+/", "/bot<redacted>/", str(exc))
        raise SystemExit(message) from None


def main() -> None:
    parser = argparse.ArgumentParser(description="Set or delete the Telegram webhook for the research agent.")
    parser.add_argument("--url", help="Public tunnel URL, for example https://example.trycloudflare.com")
    parser.add_argument("--delete", action="store_true", help="Delete the current webhook")
    parser.add_argument("--secret-token", default=os.getenv("TELEGRAM_WEBHOOK_SECRET", ""))
    args = parser.parse_args()

    if args.delete:
        result = telegram_api("deleteWebhook", {"drop_pending_updates": True})
        print({"ok": result.get("ok"), "description": result.get("description")})
        return

    if not args.url:
        raise SystemExit("Provide --url or --delete")

    base_url = args.url.rstrip("/")
    payload: dict[str, object] = {
        "url": f"{base_url}/telegram/webhook",
        "drop_pending_updates": True,
        "allowed_updates": ["message", "edited_message"],
    }
    if args.secret_token:
        payload["secret_token"] = args.secret_token
    result = telegram_api("setWebhook", payload)
    print({"ok": result.get("ok"), "description": result.get("description"), "webhook": payload["url"]})


if __name__ == "__main__":
    main()
