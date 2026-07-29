from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from tools._shared import err


def summarize_csv(csv_path: str = "", max_rows: int = 5) -> dict[str, Any]:
    try:
        if not csv_path:
            raise ValueError("Missing csv_path")
        path = Path(csv_path)
        if not path.exists() or not path.is_file():
            raise ValueError(f"CSV file not found: {csv_path}")
        with path.open("r", encoding="utf-8", errors="replace") as file:
            reader = csv.DictReader(file)
            rows = []
            row_count = 0
            for row in reader:
                if row_count < max(1, int(max_rows or 5)):
                    rows.append(row)
                row_count += 1
            headers = reader.fieldnames or []
        return {
            "tool": "csv_summary",
            "csv_path": str(path),
            "headers": headers,
            "row_count": row_count,
            "sample_rows": rows,
        }
    except Exception as exc:
        return err("csv_summary", exc)
