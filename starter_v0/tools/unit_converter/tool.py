from __future__ import annotations

from typing import Any

from tools._shared import err

_UNIT_MAP = {
    "length": {
        "m": 1.0,
        "km": 1000.0,
        "cm": 0.01,
        "mm": 0.001,
        "mi": 1609.344,
        "ft": 0.3048,
        "in": 0.0254,
    },
    "weight": {
        "kg": 1.0,
        "g": 0.001,
        "lb": 0.45359237,
        "oz": 0.0283495231,
    },
    "temperature": {
        "c": "c",
        "f": "f",
        "k": "k",
    },
}


def _convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    if from_unit == to_unit:
        return value
    if from_unit == "c":
        if to_unit == "f":
            return value * 9.0 / 5.0 + 32.0
        if to_unit == "k":
            return value + 273.15
    if from_unit == "f":
        if to_unit == "c":
            return (value - 32.0) * 5.0 / 9.0
        if to_unit == "k":
            return (value - 32.0) * 5.0 / 9.0 + 273.15
    if from_unit == "k":
        if to_unit == "c":
            return value - 273.15
        if to_unit == "f":
            return (value - 273.15) * 9.0 / 5.0 + 32.0
    raise ValueError(f"Unsupported temperature conversion {from_unit}->{to_unit}")


def convert_unit(value: float | int = 0.0, from_unit: str = "", to_unit: str = "", category: str = "") -> dict[str, Any]:
    try:
        from_unit_norm = str(from_unit or "").strip().lower()
        to_unit_norm = str(to_unit or "").strip().lower()
        category_norm = str(category or "").strip().lower()
        if not from_unit_norm or not to_unit_norm:
            raise ValueError("Missing from_unit or to_unit")
        if category_norm and category_norm not in _UNIT_MAP:
            raise ValueError(f"Unsupported category: {category_norm}")

        if not category_norm:
            for cat, units in _UNIT_MAP.items():
                if from_unit_norm in units and to_unit_norm in units:
                    category_norm = cat
                    break
        if not category_norm:
            raise ValueError(f"Cannot infer category from {from_unit} and {to_unit}")

        if category_norm == "temperature":
            result = _convert_temperature(float(value), from_unit_norm, to_unit_norm)
        else:
            unit_map = _UNIT_MAP.get(category_norm, {})
            if from_unit_norm not in unit_map or to_unit_norm not in unit_map:
                raise ValueError(f"Unsupported conversion in category {category_norm}")
            result = float(value) * unit_map[from_unit_norm] / unit_map[to_unit_norm]

        return {
            "tool": "unit_converter",
            "value": float(value),
            "from_unit": from_unit_norm,
            "to_unit": to_unit_norm,
            "category": category_norm,
            "result": result,
        }
    except Exception as exc:
        return err("unit_converter", exc)
