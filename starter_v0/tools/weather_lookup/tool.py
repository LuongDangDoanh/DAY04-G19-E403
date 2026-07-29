from __future__ import annotations

import requests
from typing import Any

from tools._shared import TIMEOUT, err


def get_weather(location: str = "", units: str = "metric") -> dict[str, Any]:
    try:
        if not location:
            raise ValueError("Missing location")
        geocode = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": location, "count": 1, "language": "en", "format": "json"},
            timeout=TIMEOUT,
        )
        geocode.raise_for_status()
        geo_data = geocode.json()
        results = geo_data.get("results") or []
        if not results:
            raise ValueError(f"Location not found: {location}")
        place = results[0]
        lat = place.get("latitude")
        lon = place.get("longitude")
        weather = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": True,
                "temperature_unit": "celsius" if units == "metric" else "fahrenheit",
                "windspeed_unit": "kmh",
                "timezone": "auto",
            },
            timeout=TIMEOUT,
        )
        weather.raise_for_status()
        current = weather.json().get("current_weather", {})
        return {
            "tool": "weather_lookup",
            "location": location,
            "resolved_name": place.get("name"),
            "country": place.get("country"),
            "latitude": lat,
            "longitude": lon,
            "units": units,
            "weather": current,
        }
    except Exception as exc:
        return err("weather_lookup", exc)
