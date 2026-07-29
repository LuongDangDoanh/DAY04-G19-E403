from __future__ import annotations

import requests
from typing import Any

from tools._shared import TIMEOUT, domain, err


def web_search(query: str = "", max_results: int = 5, region: str = "global") -> dict[str, Any]:
    try:
        if not query:
            raise ValueError("Missing query")
        response = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_redirect": 1, "skip_disambig": 1},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        items: list[dict[str, Any]] = []
        abstract = data.get("AbstractText") or data.get("RelatedTopics", [])
        if isinstance(abstract, str) and abstract:
            items.append({"title": query, "url": "", "source": "duckduckgo.com", "summary": abstract})
        if isinstance(data.get("RelatedTopics"), list):
            for item in data["RelatedTopics"][: max(1, int(max_results or 5))]:
                if isinstance(item, dict):
                    if snippet := item.get("Text"):
                        items.append({
                            "title": item.get("Text", query),
                            "url": item.get("FirstURL", ""),
                            "source": domain(str(item.get("FirstURL", ""))),
                            "summary": item.get("Text", ""),
                        })
        return {
            "tool": "web_search",
            "query": query,
            "region": region,
            "items": items[: int(max_results or 5)],
        }
    except Exception as exc:
        return err("web_search", exc)
