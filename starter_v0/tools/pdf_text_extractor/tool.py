from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from tools._shared import err


def extract_pdf_text(pdf_path: str = "", max_pages: int = 5) -> dict[str, Any]:
    try:
        if not pdf_path:
            raise ValueError("Missing pdf_path")
        path = Path(pdf_path)
        if not path.exists() or not path.is_file():
            raise ValueError(f"PDF file not found: {pdf_path}")
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("Install pypdf first: pip install pypdf") from exc

        reader = PdfReader(str(path))
        pages_to_read = min(max(1, int(max_pages or 5)), len(reader.pages))
        text_parts: list[str] = []
        for page in reader.pages[:pages_to_read]:
            text_parts.append(page.extract_text() or "")
        text = "\n\n".join(part for part in text_parts if part.strip())
        return {
            "tool": "pdf_text_extractor",
            "pdf_path": str(path),
            "page_count": len(reader.pages),
            "pages_read": pages_to_read,
            "text": text[:20000],
        }
    except Exception as exc:
        return err("pdf_text_extractor", exc)
