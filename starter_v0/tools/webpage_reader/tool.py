from __future__ import annotations

import re
import requests
from typing import Any

from tools._shared import TIMEOUT, domain, err


def _cleanup_html(html: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", "", html, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _title(html: str) -> str:
    match = re.search(r"<title>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def read_webpage(url: str = "", max_chars: int = 4000) -> dict[str, Any]:
    try:
        if not url:
            raise ValueError("Missing url")
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        html = response.text
        title = _title(html) or url
        summary = _cleanup_html(html)[: int(max(1000, min(int(max_chars or 4000), 10000)))]
        return {
            "tool": "webpage_reader",
            "url": url,
            "title": title,
            "source": domain(url),
            "summary": summary,
        }
    except Exception as exc:
        return err("webpage_reader", exc)
