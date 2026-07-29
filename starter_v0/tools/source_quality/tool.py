from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from tools._shared import err


_PRIMARY_DOMAINS = {
    "openai.com", "anthropic.com", "deepmind.google", "ai.google", "microsoft.com",
    "nasa.gov", "nih.gov", "who.int", "arxiv.org", "gov.uk", "europa.eu",
}
_SECONDARY_DOMAINS = {
    "reuters.com", "apnews.com", "bbc.com", "technologyreview.com", "wired.com",
    "theverge.com", "techcrunch.com", "nature.com", "sciencedirect.com",
}


def _base_domain(url: str) -> str:
    host = (urlparse(url).netloc or "").lower().split(":", 1)[0]
    return host[4:] if host.startswith("www.") else host


def source_quality(url: str = "", title: str = "", source: str = "") -> dict[str, Any]:
    try:
        normalized_url = str(url or "").strip()
        parsed = urlparse(normalized_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("url must be an absolute http(s) URL")

        domain = _base_domain(normalized_url)
        is_primary = domain in _PRIMARY_DOMAINS or any(domain.endswith("." + item) for item in _PRIMARY_DOMAINS)
        is_secondary = domain in _SECONDARY_DOMAINS or any(domain.endswith("." + item) for item in _SECONDARY_DOMAINS)
        if is_primary:
            tier, score = "primary", 0.95
            reasons = ["official, institutional, or first-party domain"]
        elif is_secondary:
            tier, score = "secondary", 0.78
            reasons = ["recognized editorial or specialist publication"]
        else:
            tier, score = "unclassified", 0.5
            reasons = ["domain is not in the built-in source registry"]
        if title.strip():
            reasons.append("title metadata supplied")
        if source.strip() and source.strip().lower() not in {domain, f"www.{domain}"}:
            reasons.append("display source differs from resolved domain")
        return {
            "tool": "source_quality",
            "url": normalized_url,
            "domain": domain,
            "tier": tier,
            "score": score,
            "reasons": reasons,
            "caveat": "Metadata quality is not a fact-check of the source content.",
        }
    except Exception as exc:
        return err("source_quality", exc)
