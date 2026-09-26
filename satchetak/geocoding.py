"""Human place search used only to position the AOI map."""
from __future__ import annotations

from typing import Any

import httpx

from .tls import ssl_context, translate_tls_error

NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"


def _result(item: dict[str, Any]) -> dict[str, Any]:
    south, north, west, east = (float(value) for value in item["boundingbox"])
    return {
        "display_name": str(item["display_name"]),
        "latitude": float(item["lat"]),
        "longitude": float(item["lon"]),
        "bounds": {"west": west, "south": south, "east": east, "north": north},
        "type": str(item.get("type", "place")),
    }


def search_places(query: str) -> list[dict[str, Any]]:
    try:
        response = httpx.get(
            NOMINATIM_SEARCH_URL,
            params={"q": query, "format": "jsonv2", "limit": 5, "addressdetails": 1},
            headers={"User-Agent": "SATCHETAK/0.2 location-search", "Accept-Language": "en"},
            verify=ssl_context(),
            timeout=15,
        )
        response.raise_for_status()
        return [_result(item) for item in response.json() if item.get("boundingbox")]
    except httpx.HTTPError as exc:
        translated = translate_tls_error(exc, "OpenStreetMap location search")
        if translated:
            raise translated from exc
        raise RuntimeError(f"Location search is temporarily unavailable: {exc}") from exc
