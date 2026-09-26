from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import httpx
import numpy as np
from rasterio.io import MemoryFile
from rasterio.warp import transform, transform_geom

from .config import Settings
from .tls import ssl_context, translate_tls_error

TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
PROCESS_URL = "https://sh.dataspace.copernicus.eu/process/v1"
MAX_OUTPUT_PIXELS = 300_000

NDVI_EVALSCRIPT = """//VERSION=3
function setup() {
  return {input: ["B02", "B03", "B04", "B08", "SCL", "dataMask"], output: {bands: 5, sampleType: "FLOAT32"}};
}
function evaluatePixel(s) {
  const invalid = [0, 1, 3, 8, 9, 10, 11].includes(s.SCL);
  return [s.B02, s.B03, s.B04, s.B08, s.dataMask && !invalid ? 1 : 0];
}
"""

MULTISPECTRAL_EVALSCRIPT = """//VERSION=3
function setup() {
  return {input: ["B02", "B03", "B04", "B08", "B11", "B12", "SCL", "dataMask"], output: {bands: 7, sampleType: "FLOAT32"}};
}
function evaluatePixel(s) {
  const invalid = [0, 1, 3, 8, 9, 10, 11].includes(s.SCL);
  return [s.B02, s.B03, s.B04, s.B08, s.B11, s.B12, s.dataMask && !invalid ? 1 : 0];
}
"""


class ProcessingConfigurationError(RuntimeError):
    pass


@dataclass
class RasterEvidence:
    ndvi: np.ndarray
    bands: np.ndarray
    valid: np.ndarray
    pixel_area_m2: float
    crs: str
    resolution_m: float
    coordinates: list[list[float]]


@dataclass
class MultispectralEvidence:
    bands: np.ndarray
    valid: np.ndarray
    pixel_area_m2: float
    crs: str
    resolution_m: float
    coordinates: list[list[float]]


@dataclass
class _ProcessResult:
    data: np.ndarray
    pixel_area_m2: float
    crs: str
    resolution_m: float
    coordinates: list[list[float]]


def credentials_configured(settings: Settings) -> bool:
    return bool(settings.cdse_client_id and settings.cdse_client_secret)


def _utm_epsg(aoi: dict[str, Any]) -> int:
    ring = aoi["coordinates"][0]
    lon = sum(point[0] for point in ring) / len(ring)
    lat = sum(point[1] for point in ring) / len(ring)
    zone = min(60, max(1, int((lon + 180) // 6) + 1))
    return (32600 if lat >= 0 else 32700) + zone


def _access_token(settings: Settings) -> str:
    if not credentials_configured(settings):
        raise ProcessingConfigurationError("real pixel analysis requires server-side CDSE_CLIENT_ID and CDSE_CLIENT_SECRET")
    try:
        response = httpx.post(
            TOKEN_URL,
            data={"grant_type": "client_credentials", "client_id": settings.cdse_client_id, "client_secret": settings.cdse_client_secret},
            verify=ssl_context(), timeout=30,
        )
    except httpx.HTTPError as exc:
        translated = translate_tls_error(exc, "Copernicus identity service")
        if translated:
            raise translated from exc
        raise
    response.raise_for_status()
    return response.json()["access_token"]


def _process_raster(aoi: dict[str, Any], acquisition_time: str, settings: Settings, max_cloud_cover: float, evalscript: str) -> _ProcessResult:
    epsg = _utm_epsg(aoi)
    crs = f"EPSG:{epsg}"
    projected = transform_geom("EPSG:4326", crs, aoi, precision=3)
    xs = [point[0] for point in projected["coordinates"][0]]
    ys = [point[1] for point in projected["coordinates"][0]]
    resolution = 10.0
    if math.ceil((max(xs) - min(xs)) / resolution) * math.ceil((max(ys) - min(ys)) / resolution) > MAX_OUTPUT_PIXELS:
        raise ValueError("AOI is too large for synchronous 10 m prototype analysis")
    instant = datetime.fromisoformat(acquisition_time.replace("Z", "+00:00"))
    start = instant.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1) - timedelta(seconds=1)
    payload = {
        "input": {
            "bounds": {"geometry": projected, "properties": {"crs": f"http://www.opengis.net/def/crs/EPSG/0/{epsg}"}},
            "data": [{"type": "sentinel-2-l2a", "dataFilter": {
                "timeRange": {"from": start.isoformat().replace("+00:00", "Z"), "to": end.isoformat().replace("+00:00", "Z")},
                "maxCloudCoverage": max_cloud_cover, "mosaickingOrder": "leastCC",
            }}],
        },
        "output": {"resx": resolution, "resy": resolution, "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}]},
        "evalscript": evalscript,
    }
    token = _access_token(settings)
    try:
        response = httpx.post(PROCESS_URL, json=payload, headers={"Authorization": f"Bearer {token}"}, verify=ssl_context(), timeout=120)
    except httpx.HTTPError as exc:
        translated = translate_tls_error(exc, "Copernicus processing service")
        if translated:
            raise translated from exc
        raise
    response.raise_for_status()
    with MemoryFile(response.content) as memory:
        with memory.open() as dataset:
            data = dataset.read().astype(np.float32)
            pixel_area = abs(dataset.transform.a * dataset.transform.e)
            output_crs = dataset.crs.to_string() if dataset.crs else crs
            bounds = dataset.bounds
            xs, ys = transform(
                output_crs,
                "EPSG:4326",
                [bounds.left, bounds.right, bounds.right, bounds.left],
                [bounds.top, bounds.top, bounds.bottom, bounds.bottom],
            )
            coordinates = [[float(x), float(y)] for x, y in zip(xs, ys)]
    return _ProcessResult(
        data=data,
        pixel_area_m2=pixel_area,
        crs=output_crs,
        resolution_m=resolution,
        coordinates=coordinates,
    )


def fetch_ndvi(aoi: dict[str, Any], acquisition_time: str, settings: Settings, max_cloud_cover: float = 30) -> RasterEvidence:
    result = _process_raster(aoi, acquisition_time, settings, max_cloud_cover, NDVI_EVALSCRIPT)
    bands, mask = result.data[:4], result.data[4]
    denominator = bands[3] + bands[2]
    ndvi = np.divide(bands[3] - bands[2], denominator, out=np.zeros_like(denominator), where=denominator != 0)
    valid = (mask > 0.5) & np.all(np.isfinite(bands), axis=0) & np.isfinite(ndvi)
    return RasterEvidence(
        ndvi=ndvi,
        bands=bands,
        valid=valid,
        pixel_area_m2=result.pixel_area_m2,
        crs=result.crs,
        resolution_m=result.resolution_m,
        coordinates=result.coordinates,
    )


def fetch_multispectral(aoi: dict[str, Any], acquisition_time: str, settings: Settings, max_cloud_cover: float = 30) -> MultispectralEvidence:
    result = _process_raster(aoi, acquisition_time, settings, max_cloud_cover, MULTISPECTRAL_EVALSCRIPT)
    bands, mask = result.data[:6], result.data[6]
    valid = (mask > 0.5) & np.all(np.isfinite(bands), axis=0)
    return MultispectralEvidence(
        bands=bands,
        valid=valid,
        pixel_area_m2=result.pixel_area_m2,
        crs=result.crs,
        resolution_m=result.resolution_m,
        coordinates=result.coordinates,
    )
