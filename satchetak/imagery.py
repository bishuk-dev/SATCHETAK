from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import date, timedelta
from typing import Any

from .tls import ssl_context, translate_tls_error

CDSE_SEARCH_URL = "https://stac.dataspace.copernicus.eu/v1/search"
PLANETARY_SEARCH_URL = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
BHOONIDHI_TOKEN_URL = "https://bhoonidhi-api.nrsc.gov.in/auth/token"
BHOONIDHI_SEARCH_URL = "https://bhoonidhi-api.nrsc.gov.in/data/search"


def _observation(feature: dict[str, Any]) -> dict[str, Any]:
    properties = feature.get("properties", {})
    assets = feature.get("assets", {})
    return {
        "provider": "copernicus_dataspace",
        "provider_scene_id": feature.get("id"),
        "satellite": properties.get("platform", "Sentinel-2"),
        "sensor": "MSI",
        "acquisition_time": properties.get("datetime"),
        "cloud_cover": properties.get("eo:cloud_cover"),
        "product_level": "L2A",
        "bands": [key for key in assets if key in {"B04_10m", "B08_10m", "red", "nir"}],
        "crs": properties.get("proj:code"),
        "asset_references": {key: asset.get("href") for key, asset in assets.items() if key in {"B04_10m", "B08_10m", "red", "nir"}},
        "quality_state": "candidate",
        "source_mode": "live_catalogue",
    }


def _stac_observation(feature: dict[str, Any], provider: str) -> dict[str, Any]:
    properties = feature.get("properties", {})
    assets = feature.get("assets", {})
    cloud = properties.get("eo:cloud_cover")
    band_keys = [key for key in assets if key.upper() in {"B02", "B03", "B04", "B08", "B11", "B12"}]
    return {
        "provider": provider,
        "provider_scene_id": str(feature.get("id")),
        "satellite": properties.get("platform", "Sentinel-2"),
        "sensor": "MSI",
        "acquisition_time": properties.get("datetime") or properties.get("start_datetime"),
        "cloud_cover": cloud,
        "product_level": "L2A",
        "bands": band_keys,
        "crs": properties.get("proj:code") or (f"EPSG:{properties['proj:epsg']}" if properties.get("proj:epsg") else None),
        "asset_references": {key: value.get("href") for key, value in assets.items() if key in band_keys},
        "quality_state": "candidate",
        "source_mode": "live_catalogue",
    }


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "SATCHETAK/0.2", **(headers or {})},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=25, context=ssl_context()) as response:
        return json.load(response)


def search_planetary_computer(aoi: dict[str, Any], period: dict[str, str], max_cloud: float = 30) -> list[dict[str, Any]]:
    payload = {
        "collections": ["sentinel-2-l2a"],
        "datetime": f"{period['from']}T00:00:00Z/{period['to']}T23:59:59Z",
        "intersects": aoi,
        "query": {"eo:cloud_cover": {"lte": max_cloud}},
        "sortby": [{"field": "datetime", "direction": "asc"}],
        "limit": 50,
    }
    try:
        data = _post_json(PLANETARY_SEARCH_URL, payload)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        translated = translate_tls_error(exc, "Planetary Computer catalogue")
        if translated:
            raise translated from exc
        raise RuntimeError(f"Planetary Computer catalogue unavailable: {exc}") from exc
    return [_stac_observation(feature, "planetary_computer") for feature in data.get("features", [])]


def search_bhoonidhi(
    aoi: dict[str, Any], period: dict[str, str], user_id: str, password: str, collection: str, max_cloud: float = 30,
) -> list[dict[str, Any]]:
    try:
        token = _post_json(BHOONIDHI_TOKEN_URL, {"userId": user_id, "password": password, "grant_type": "password"})["access_token"]
        data = _post_json(BHOONIDHI_SEARCH_URL, {
            "collections": [collection],
            "datetime": f"{period['from']}T00:00:00Z/{period['to']}T23:59:59Z",
            "intersects": aoi,
            "limit": 50,
        }, {"Authorization": f"Bearer {token}"})
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
        translated = translate_tls_error(exc, "Bhoonidhi catalogue")
        if translated:
            raise translated from exc
        raise RuntimeError(f"Bhoonidhi catalogue unavailable: {exc}") from exc
    observations = [_stac_observation(feature, "bhoonidhi") for feature in data.get("features", [])]
    return [item for item in observations if item["cloud_cover"] is None or item["cloud_cover"] <= max_cloud]


def search_copernicus(aoi: dict[str, Any], period: dict[str, str], max_cloud: float = 30) -> list[dict[str, Any]]:
    payload = {
        "collections": ["sentinel-2-l2a"],
        "datetime": f"{period['from']}T00:00:00Z/{period['to']}T23:59:59Z",
        "intersects": aoi,
        "query": {"eo:cloud_cover": {"lte": max_cloud}},
        "sortby": [{"field": "datetime", "direction": "asc"}],
        "limit": 50,
    }
    request = urllib.request.Request(
        CDSE_SEARCH_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "SATCHETAK/0.1"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20, context=ssl_context()) as response:
            data = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        translated = translate_tls_error(exc, "Copernicus catalogue")
        if translated:
            raise translated from exc
        raise RuntimeError(f"Copernicus catalogue unavailable: {exc}") from exc
    return [_observation(feature) for feature in data.get("features", [])]


def demo_observations(period: dict[str, str]) -> list[dict[str, Any]]:
    start = date.fromisoformat(period["from"])
    end = date.fromisoformat(period["to"])
    span = end - start
    dates = [
        start + timedelta(days=max(1, span.days // 8)),
        start + timedelta(days=max(2, span.days * 3 // 8)),
        start + timedelta(days=max(3, span.days // 2)),
        start + timedelta(days=max(4, span.days * 5 // 8)),
        end - timedelta(days=max(1, span.days // 8)),
    ]
    clouds = [7.8, 11.2, 42.0, 13.6, 9.4]
    return [
        {
            "provider": "demo_fixture",
            "provider_scene_id": f"DEMO_S2_L2A_{when:%Y%m%d}_{index}",
            "satellite": "Sentinel-2 (simulated)",
            "sensor": "MSI-like demo grid",
            "acquisition_time": f"{when.isoformat()}T05:18:00Z",
            "cloud_cover": cloud,
            "product_level": "L2A-like synthetic fixture",
            "bands": ["B02", "B03", "B04", "B08", "B11", "B12"],
            "crs": "EPSG:4326 demo grid",
            "asset_references": {},
            "quality_state": "candidate" if cloud <= 30 else "rejected_cloud",
            "source_mode": "demo_simulation",
        }
        for index, (when, cloud) in enumerate(zip(dates, clouds), 1)
    ]


def select_pair(observations: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    valid = sorted(
        (item for item in observations if item.get("quality_state") != "rejected_cloud"),
        key=lambda item: item.get("acquisition_time") or "",
    )
    if len(valid) < 2:
        raise ValueError("at least two quality-qualified observations are required")
    first, last = valid[0], valid[-1]
    first["quality_state"] = "selected_t1"
    last["quality_state"] = "selected_t2"
    return first, last
