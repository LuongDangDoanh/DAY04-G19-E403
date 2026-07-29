from __future__ import annotations

import requests
from typing import Any

from tools._shared import TIMEOUT, err


def convert_currency(amount: float = 0.0, from_currency: str = "", to_currency: str = "") -> dict[str, Any]:
    try:
        from_curr = str(from_currency or "").strip().upper()
        to_curr = str(to_currency or "").strip().upper()
        if not from_curr or not to_curr:
            raise ValueError("Missing from_currency or to_currency")
        response = requests.get(
            "https://api.exchangerate.host/convert",
            params={"from": from_curr, "to": to_curr, "amount": amount},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("success", False):
            raise ValueError(data.get("error", "Currency conversion failed"))
        return {
            "tool": "currency_converter",
            "amount": float(amount),
            "from_currency": from_curr,
            "to_currency": to_curr,
            "result": data.get("result"),
            "rate": data.get("info", {}).get("rate"),
        }
    except Exception as exc:
        return err("currency_converter", exc)
