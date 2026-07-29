from __future__ import annotations

from typing import Any

from tools._shared import err


def summarize_markdown(markdown_text: str = "", max_sentences: int = 5) -> dict[str, Any]:
    try:
        if not markdown_text:
            raise ValueError("Missing markdown_text")
        lines = [line.strip() for line in markdown_text.splitlines() if line.strip()]
        sentences: list[str] = []
        for line in lines:
            parts = [part.strip() for part in line.split(".") if part.strip()]
            for part in parts:
                if len(sentences) >= int(max_sentences or 5):
                    break
                sentences.append(part)
            if len(sentences) >= int(max_sentences or 5):
                break
        summary = ". ".join(sentences)
        if summary and not summary.endswith("."):
            summary += "."
        return {
            "tool": "markdown_summarizer",
            "summary": summary,
            "sentence_count": len(sentences),
        }
    except Exception as exc:
        return err("markdown_summarizer", exc)
