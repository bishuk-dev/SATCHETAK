from __future__ import annotations

import struct
import zlib
from pathlib import Path
from typing import Any

import numpy as np

from .schemas import AnalysisArtifact


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class ArtifactStore:
    """Filesystem storage for immutable, analysis-scoped evidence artifacts."""

    def __init__(self, root: Path):
        self.root = root

    def write_png(self, analysis_id: str, artifact_id: str, rgba: np.ndarray) -> Path:
        directory = self.root / analysis_id
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{artifact_id}.png"
        path.write_bytes(encode_png_rgba(rgba))
        return path

    def path(self, analysis_id: str, artifact_id: str) -> Path:
        return self.root / analysis_id / f"{artifact_id}.png"


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)


def encode_png_rgba(rgba: np.ndarray) -> bytes:
    """Encode an HxWx4 uint8 array without adding an image-library dependency."""
    if rgba.ndim != 3 or rgba.shape[2] != 4 or rgba.dtype != np.uint8:
        raise ValueError("PNG input must be an HxWx4 uint8 array")
    height, width, _ = rgba.shape
    scanlines = b"".join(b"\x00" + rgba[row].tobytes() for row in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return PNG_SIGNATURE + _png_chunk(b"IHDR", header) + _png_chunk(b"IDAT", zlib.compress(scanlines, 9)) + _png_chunk(b"IEND", b"")


def _shared_true_color(first: np.ndarray, second: np.ndarray, valid1: np.ndarray, valid2: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if first.shape != second.shape or first.ndim != 3 or first.shape[0] < 3:
        raise ValueError("true-color artifacts require aligned B02/B03/B04 stacks")
    rgb1 = first[[2, 1, 0]].astype(np.float32)
    rgb2 = second[[2, 1, 0]].astype(np.float32)
    if not valid1.any() or not valid2.any():
        raise ValueError("true-color artifacts require valid pixels")

    def render(rgb: np.ndarray, valid: np.ndarray) -> np.ndarray:
        # Stretch each acquisition for readable visual inspection. Analysis always uses raw reflectance.
        samples = rgb[:, valid]
        low = float(np.percentile(samples, 2))
        high = float(np.percentile(samples, 98))
        span = max(high - low, 1e-6)
        stretched = np.clip((rgb - low) / span, 0, 1)
        stretched = np.power(stretched, 0.85)
        output = np.zeros((*valid.shape, 4), dtype=np.uint8)
        output[..., :3] = np.moveaxis((stretched * 255).astype(np.uint8), 0, -1)
        output[..., 3] = np.where(valid, 255, 0).astype(np.uint8)
        return output

    return render(rgb1, valid1), render(rgb2, valid2)


def _change_overlay(result: dict[str, Any], valid: np.ndarray) -> tuple[np.ndarray, list[dict[str, str]]]:
    overlay = np.zeros((*valid.shape, 4), dtype=np.uint8)
    evidence = result["evidence"]
    if result["workflow"] == "generic_land_change":
        classification = np.asarray(evidence.get("change_classification", evidence["change_mask"]), dtype=np.uint8)
        clearing = (classification == 1) & valid
        built_up = (classification == 2) & valid
        other = (classification == 3) & valid
        overlay[clearing] = [230, 111, 45, 220]
        overlay[built_up] = [190, 48, 95, 220]
        overlay[other] = [229, 190, 48, 210]
        legend = [
            {"label": "Vegetation-to-bare / disturbed candidate", "color": "#e66f2d"},
            {"label": "Built-up-like candidate", "color": "#be305f"},
            {"label": "Other surface change", "color": "#e5be30"},
        ]
    else:
        delta = np.asarray(evidence["delta_ndvi"], dtype=np.float32)
        thresholds = evidence["thresholds"]
        decline = valid & (delta <= thresholds["decline_lte"])
        increase = valid & (delta >= thresholds["increase_gte"])
        overlay[decline] = [217, 75, 55, 210]
        overlay[increase] = [127, 181, 79, 210]
        legend = [
            {"label": "Vegetation decline", "color": "#d94b37"},
            {"label": "Vegetation increase", "color": "#7fb54f"},
        ]
    return overlay, legend


def aoi_image_coordinates(aoi: dict[str, Any]) -> list[list[float]]:
    ring = aoi["coordinates"][0]
    west = min(point[0] for point in ring)
    east = max(point[0] for point in ring)
    south = min(point[1] for point in ring)
    north = max(point[1] for point in ring)
    return [[west, north], [east, north], [east, south], [west, south]]


def create_raster_artifacts(
    *,
    store: ArtifactStore,
    analysis_id: str,
    result: dict[str, Any],
    bands1: np.ndarray,
    valid1: np.ndarray,
    bands2: np.ndarray,
    valid2: np.ndarray,
    coordinates: list[list[float]],
) -> list[AnalysisArtifact]:
    """Create presentation artifacts from the same aligned pixels used by analysis."""
    valid_overlap = valid1 & valid2
    first, second = _shared_true_color(bands1, bands2, valid1, valid2)
    overlay, legend = _change_overlay(result, valid_overlap)
    rendered = {
        "t1_true_color": first,
        "t2_true_color": second,
        "change_overlay": overlay,
    }
    for artifact_id, image in rendered.items():
        store.write_png(analysis_id, artifact_id, image)

    source_mode = result["evidence"]["source_mode"]
    simulated = source_mode.startswith("demo")
    qualifier = "Simulated true-color visualization" if simulated else "Individually contrast-stretched Sentinel-2 true-color visualization"
    height, width = valid_overlap.shape
    base_url = f"/api/v1/analyses/{analysis_id}/artifacts"
    return [
        AnalysisArtifact(
            id="t1_true_color", role="t1", kind="true_color", title="Before — satellite image",
            url=f"{base_url}/t1_true_color", coordinates=coordinates, width=width, height=height,
            acquisition_time=result["t1"]["acquisition_time"], source_mode=source_mode,
            description=f"{qualifier} from the same aligned pixel stack used by this analysis. Display stretch does not alter calculations.",
        ),
        AnalysisArtifact(
            id="t2_true_color", role="t2", kind="true_color", title="After — satellite image",
            url=f"{base_url}/t2_true_color", coordinates=coordinates, width=width, height=height,
            acquisition_time=result["t2"]["acquisition_time"], source_mode=source_mode,
            description=f"{qualifier} from the same aligned pixel stack used by this analysis. Display stretch does not alter calculations.",
        ),
        AnalysisArtifact(
            id="change_overlay", role="change", kind="change_overlay", title="Candidate change overlay",
            url=f"{base_url}/change_overlay", coordinates=coordinates, width=width, height=height,
            acquisition_time=result["t2"]["acquisition_time"], source_mode=source_mode,
            description="Transparent threshold pixels aligned exactly with the T1/T2 analytical rasters.",
            legend=legend,
        ),
    ]
