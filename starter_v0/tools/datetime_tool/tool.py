from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from tools._shared import err


def current_datetime(format: str = "%Y-%m-%d %H:%M:%S", utc: bool = False) -> dict[str, Any]:
    try:
        now = datetime.now(timezone.utc if utc else None)
        return {"tool": "datetime_tool", "utc": utc, "value": now.strftime(format), "format": format}
    except Exception as exc:
        return err("datetime_tool", exc)
