from __future__ import annotations

import math
from typing import Any

import numpy as np

GRID_SIZE = 24
DECLINE_THRESHOLD = -0.12
INCREASE_THRESHOLD = 0.12
LAND_CHANGE_THRESHOLD = 0.12
MIN_LAND_REGION_AREA_M2 = 1_000
LAND_CLASS_LABELS = {
    1: "vegetation_to_bare_candidate",
    2: "built_up_like_candidate",
    3: "other_surface_change",
}


def vegetation_statistics(first: np.ndarray, second: np.ndarray, valid: np.ndarray, change: np.ndarray | None = None) -> dict[str, float | int]:
    """Summaries over the same mutually valid pixels as change analysis."""
    before, after = first[valid], second[valid]
    delta = (second - first)[valid] if change is None else change[valid]
    return {
        "valid_pixel_count": int(valid.sum()),
        "ndvi_t2_p10": round(float(np.percentile(after, 10)), 3),
        "ndvi_t2_median": round(float(np.median(after)), 3),
        "ndvi_t2_p90": round(float(np.percentile(after, 90)), 3),
        "ndvi_t2_std": round(float(after.std()), 3),
        "decline_share_pct": round(float(np.mean(delta <= DECLINE_THRESHOLD) * 100), 2),
        "increase_share_pct": round(float(np.mean(delta >= INCREASE_THRESHOLD) * 100), 2),
        "stable_share_pct": round(float(np.mean((delta > DECLINE_THRESHOLD) & (delta < INCREASE_THRESHOLD)) * 100), 2),
    }


def _grid(phase: int) -> tuple[list[list[float]], list[list[float]]]:
    red: list[list[float]] = []
    nir: list[list[float]] = []
    for y in range(GRID_SIZE):
        red_row, nir_row = [], []
        for x in range(GRID_SIZE):
            texture = 0.018 * math.sin(x * 0.7) + 0.012 * math.cos(y * 0.5)
            red_value = 0.20 + texture
            nir_value = 0.56 + texture
            if phase == 2 and 5 <= x <= 13 and 7 <= y <= 16:
                red_value += 0.10
                nir_value -= 0.16
            if phase == 2 and 17 <= x <= 21 and 3 <= y <= 9:
                red_value -= 0.025
                nir_value += 0.08
            red_row.append(red_value)
            nir_row.append(nir_value)
        red.append(red_row)
        nir.append(nir_row)
    return red, nir


def _ndvi(red: list[list[float]], nir: list[list[float]]) -> list[list[float]]:
    return [
        [round((n - r) / (n + r), 4) if n + r else 0.0 for r, n in zip(red_row, nir_row)]
        for red_row, nir_row in zip(red, nir)
    ]


def _demo_multispectral(phase: int) -> np.ndarray:
    blue = np.full((GRID_SIZE, GRID_SIZE), 0.11, dtype=np.float32)
    green = np.full((GRID_SIZE, GRID_SIZE), 0.17, dtype=np.float32)
    red = np.full((GRID_SIZE, GRID_SIZE), 0.20, dtype=np.float32)
    nir = np.full((GRID_SIZE, GRID_SIZE), 0.55, dtype=np.float32)
    swir1 = np.full((GRID_SIZE, GRID_SIZE), 0.23, dtype=np.float32)
    swir2 = np.full((GRID_SIZE, GRID_SIZE), 0.18, dtype=np.float32)
    yy, xx = np.indices((GRID_SIZE, GRID_SIZE))
    texture = 0.012 * np.sin(xx * 0.7) + 0.009 * np.cos(yy * 0.5)
    stack = np.stack([blue + texture, green + texture, red + texture, nir + texture, swir1 + texture, swir2 + texture])
    if phase in {2, 3}:
        region = (xx >= 5) & (xx <= 14) & (yy >= 7) & (yy <= 17)
        stack[0, region] += 0.13
        stack[1, region] += 0.11
        stack[2, region] += 0.15
        stack[3, region] -= 0.20
        stack[4, region] += 0.18
        stack[5, region] += 0.16
        if phase == 2:
            built = (xx >= 17) & (xx <= 21) & (yy >= 3) & (yy <= 9)
            stack[0, built] += 0.05
            stack[1, built] += 0.06
            stack[2, built] += 0.03
            stack[3, built] -= 0.03
            stack[4, built] += 0.20
            stack[5, built] += 0.17
    return stack.astype(np.float32)


def demo_vegetation_bands(phase: int) -> np.ndarray:
    """Return a display stack whose Red/NIR bands exactly match the demo NDVI inputs."""
    red, nir = _grid(phase)
    red_array = np.asarray(red, dtype=np.float32)
    nir_array = np.asarray(nir, dtype=np.float32)
    blue = np.clip(red_array * 0.55, 0, 1)
    green = np.clip(red_array * 0.82, 0, 1)
    return np.stack([blue, green, red_array, nir_array])


def demo_multispectral_bands(phase: int) -> np.ndarray:
    """Public demo input for services that must render the same analytical pixels."""
    return _demo_multispectral(phase)


def _bbox_area_hectares(aoi: dict[str, Any]) -> float:
    ring = aoi["coordinates"][0]
    lons, lats = zip(*[(point[0], point[1]) for point in ring])
    mid_lat = sum(lats) / len(lats)
    width_m = (max(lons) - min(lons)) * 111_320 * math.cos(math.radians(mid_lat))
    height_m = (max(lats) - min(lats)) * 110_540
    return abs(width_m * height_m) / 10_000


def vegetation_change(aoi: dict[str, Any], t1: dict[str, Any], t2: dict[str, Any]) -> dict[str, Any]:
    red1, nir1 = _grid(1)
    red2, nir2 = _grid(2)
    ndvi1, ndvi2 = _ndvi(red1, nir1), _ndvi(red2, nir2)
    delta = [[round(b - a, 4) for a, b in zip(row1, row2)] for row1, row2 in zip(ndvi1, ndvi2)]
    flat1 = [value for row in ndvi1 for value in row]
    flat2 = [value for row in ndvi2 for value in row]
    flat_delta = [value for row in delta for value in row]
    decline_count = sum(value <= DECLINE_THRESHOLD for value in flat_delta)
    increase_count = sum(value >= INCREASE_THRESHOLD for value in flat_delta)
    aoi_area = _bbox_area_hectares(aoi)
    cell_area = aoi_area / len(flat_delta)
    metrics = {
        "aoi_area_ha_estimate": round(aoi_area, 2),
        "mean_ndvi_t1": round(sum(flat1) / len(flat1), 3),
        "mean_ndvi_t2": round(sum(flat2) / len(flat2), 3),
        "mean_delta_ndvi": round(sum(flat_delta) / len(flat_delta), 3),
        "vegetation_decline_area_ha_estimate": round(decline_count * cell_area, 2),
        "vegetation_increase_area_ha_estimate": round(increase_count * cell_area, 2),
        "decline_pixel_count": decline_count,
        "increase_pixel_count": increase_count,
    }
    metrics.update(vegetation_statistics(np.array(ndvi1), np.array(ndvi2), np.ones((GRID_SIZE, GRID_SIZE), dtype=bool), np.array(delta)))
    explanation = (
        f"The verified demo grid shows a mean NDVI change of {metrics['mean_delta_ndvi']:+.3f}. "
        f"Approximately {metrics['vegetation_decline_area_ha_estimate']:.2f} ha crosses the decline threshold "
        f"and {metrics['vegetation_increase_area_ha_estimate']:.2f} ha crosses the increase threshold. "
        "This indicates vegetation change only; it does not establish disease, yield loss, or a cause."
    )
    return {
        "workflow": "vegetation_change",
        "t1": t1,
        "t2": t2,
        "metrics": metrics,
        "evidence": {
            "grid_size": GRID_SIZE,
            "ndvi_t1": ndvi1,
            "ndvi_t2": ndvi2,
            "delta_ndvi": delta,
            "thresholds": {"decline_lte": DECLINE_THRESHOLD, "increase_gte": INCREASE_THRESHOLD},
            "source_mode": t1.get("source_mode"),
        },
        "warnings": [
            "Prototype area is a bounding-box estimate, not an equal-area polygon measurement.",
            "Demo mode uses deterministic simulated spectral grids; no satellite pixels were downloaded.",
        ],
        "explanation": explanation,
        "explanation_source": "deterministic_template",
    }


def real_vegetation_change(
    t1: dict[str, Any],
    t2: dict[str, Any],
    ndvi1: np.ndarray,
    valid1: np.ndarray,
    ndvi2: np.ndarray,
    valid2: np.ndarray,
    pixel_area_m2: float,
    crs: str,
    resolution_m: float,
) -> dict[str, Any]:
    if ndvi1.shape != ndvi2.shape:
        raise ValueError("T1 and T2 rasters are not aligned")
    valid = valid1 & valid2 & np.isfinite(ndvi1) & np.isfinite(ndvi2)
    if not valid.any():
        raise ValueError("no mutually valid T1/T2 pixels exist inside the AOI")
    delta = np.where(valid, ndvi2 - ndvi1, 0.0)
    decline = valid & (delta <= DECLINE_THRESHOLD)
    increase = valid & (delta >= INCREASE_THRESHOLD)
    hectares_per_pixel = pixel_area_m2 / 10_000
    metrics = {
        "aoi_area_ha_measured": round(float(valid.sum()) * hectares_per_pixel, 2),
        "mean_ndvi_t1": round(float(ndvi1[valid].mean()), 3),
        "mean_ndvi_t2": round(float(ndvi2[valid].mean()), 3),
        "mean_delta_ndvi": round(float(delta[valid].mean()), 3),
        "vegetation_decline_area_ha": round(float(decline.sum()) * hectares_per_pixel, 2),
        "vegetation_increase_area_ha": round(float(increase.sum()) * hectares_per_pixel, 2),
        "valid_pixel_count": int(valid.sum()),
        "decline_pixel_count": int(decline.sum()),
        "increase_pixel_count": int(increase.sum()),
    }
    metrics.update(vegetation_statistics(ndvi1, ndvi2, valid))
    explanation = (
        f"Across {metrics['aoi_area_ha_measured']:.2f} ha of mutually valid pixels, mean NDVI changed "
        f"from {metrics['mean_ndvi_t1']:.3f} to {metrics['mean_ndvi_t2']:.3f}. "
        f"The verified threshold mask identifies {metrics['vegetation_decline_area_ha']:.2f} ha of vegetation decline "
        f"and {metrics['vegetation_increase_area_ha']:.2f} ha of vegetation increase. "
        "This does not establish disease, yield loss, or the cause of change."
    )
    return {
        "workflow": "vegetation_change",
        "t1": t1,
        "t2": t2,
        "metrics": metrics,
        "evidence": {
            "grid_size": list(ndvi1.shape),
            "ndvi_t1": np.where(valid1, ndvi1, 0).round(4).tolist(),
            "ndvi_t2": np.where(valid2, ndvi2, 0).round(4).tolist(),
            "delta_ndvi": delta.round(4).tolist(),
            "valid_mask": valid.astype(np.uint8).tolist(),
            "thresholds": {"decline_lte": DECLINE_THRESHOLD, "increase_gte": INCREASE_THRESHOLD},
            "source_mode": "live_processing_api",
            "crs": crs,
            "resolution_m": resolution_m,
        },
        "warnings": [
            "Sentinel Hub may mosaic multiple tiles from the selected acquisition day using least-cloud ordering.",
            "Vegetation change is an observed spectral change, not a diagnosis or causal attribution.",
        ],
        "explanation": explanation,
        "explanation_source": "deterministic_template",
    }


def generic_land_change(
    aoi: dict[str, Any], t1: dict[str, Any], t2: dict[str, Any], support_dates: list[str] | None = None,
) -> dict[str, Any]:
    stack1 = _demo_multispectral(1)
    stack2 = _demo_multispectral(2)
    valid = np.ones(stack1.shape[1:], dtype=bool)
    area = _bbox_area_hectares(aoi)
    return real_generic_land_change(
        t1, t2, stack1, valid, stack2, valid, area * 10_000 / valid.size,
        "EPSG:4326 demo grid", 10, source_mode="demo_simulation",
        support_observations=[(date, _demo_multispectral(3), valid) for date in support_dates or []],
    )


def _index(first: np.ndarray, second: np.ndarray) -> np.ndarray:
    denominator = first + second
    return np.divide(first - second, denominator, out=np.zeros_like(denominator), where=np.abs(denominator) > 1e-6)


def _location_label(row: float, column: float, rows: int, columns: int) -> str:
    vertical = "north" if row < rows / 3 else "south" if row >= rows * 2 / 3 else "central"
    horizontal = "west" if column < columns / 3 else "east" if column >= columns * 2 / 3 else "central"
    return "centre" if vertical == horizontal == "central" else f"{vertical}-{horizontal}".replace("central-", "").replace("-central", "")


def _clean_regions(classification: np.ndarray, pixel_area_m2: float) -> tuple[np.ndarray, list[dict[str, Any]], int]:
    """Keep connected category regions large enough for credible Sentinel-2 screening."""
    rows, columns = classification.shape
    minimum_pixels = max(3, math.ceil(MIN_LAND_REGION_AREA_M2 / pixel_area_m2))
    cleaned = np.zeros_like(classification, dtype=np.uint8)
    regions: list[dict[str, Any]] = []
    for class_id, class_name in LAND_CLASS_LABELS.items():
        target = classification == class_id
        visited = np.zeros_like(target, dtype=bool)
        for start_row, start_column in zip(*np.where(target & ~visited)):
            if visited[start_row, start_column]:
                continue
            stack = [(int(start_row), int(start_column))]
            visited[start_row, start_column] = True
            pixels: list[tuple[int, int]] = []
            while stack:
                row, column = stack.pop()
                pixels.append((row, column))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        next_row, next_column = row + dy, column + dx
                        if (
                            (dx or dy) and 0 <= next_row < rows and 0 <= next_column < columns
                            and target[next_row, next_column] and not visited[next_row, next_column]
                        ):
                            visited[next_row, next_column] = True
                            stack.append((next_row, next_column))
            if len(pixels) < minimum_pixels:
                continue
            pixel_rows = [pixel[0] for pixel in pixels]
            pixel_columns = [pixel[1] for pixel in pixels]
            for row, column in pixels:
                cleaned[row, column] = class_id
            regions.append({
                "category": class_name,
                "pixel_count": len(pixels),
                "area_ha": round(len(pixels) * pixel_area_m2 / 10_000, 2),
                "location": _location_label(float(np.mean(pixel_rows)), float(np.mean(pixel_columns)), rows, columns),
                "centroid_x_pct": round((float(np.mean(pixel_columns)) + 0.5) / columns * 100, 2),
                "centroid_y_pct": round((float(np.mean(pixel_rows)) + 0.5) / rows * 100, 2),
                "_pixels": pixels,
            })
    regions.sort(key=lambda item: item["pixel_count"], reverse=True)
    for index, region in enumerate(regions, 1):
        region["id"] = f"region-{index}"
    return cleaned, regions, minimum_pixels


def _land_change_signals(bands1: np.ndarray, bands2: np.ndarray, valid: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    blue1, _, red1, nir1, swir11, _ = bands1
    blue2, _, red2, nir2, swir12, _ = bands2
    ndvi1, ndvi2 = _index(nir1, red1), _index(nir2, red2)
    ndbi1, ndbi2 = _index(swir11, nir1), _index(swir12, nir2)
    bsi1 = _index(swir11 + red1, nir1 + blue1)
    bsi2 = _index(swir12 + red2, nir2 + blue2)
    delta_ndvi, delta_ndbi, delta_bsi = ndvi2 - ndvi1, ndbi2 - ndbi1, bsi2 - bsi1
    magnitude = np.where(valid, np.maximum.reduce([np.abs(delta_ndvi), np.abs(delta_ndbi), np.abs(delta_bsi)]), 0.0)
    vegetation_to_bare = valid & (ndvi1 >= 0.30) & (delta_ndvi <= -0.15) & (delta_bsi >= 0.08)
    built_up_like = valid & ~vegetation_to_bare & (delta_ndbi >= 0.12) & (ndbi2 >= -0.10) & (ndvi2 <= 0.45)
    other_change = valid & ~vegetation_to_bare & ~built_up_like & (magnitude >= 0.18)
    classification = np.zeros(valid.shape, dtype=np.uint8)
    classification[vegetation_to_bare] = 1
    classification[built_up_like] = 2
    classification[other_change] = 3
    return magnitude, classification, delta_ndvi, delta_ndbi, delta_bsi


def real_generic_land_change(
    t1: dict[str, Any],
    t2: dict[str, Any],
    bands1: np.ndarray,
    valid1: np.ndarray,
    bands2: np.ndarray,
    valid2: np.ndarray,
    pixel_area_m2: float,
    crs: str,
    resolution_m: float,
    source_mode: str = "live_processing_api",
    support_observations: list[tuple[str, np.ndarray, np.ndarray]] | None = None,
) -> dict[str, Any]:
    if bands1.shape != bands2.shape or bands1.ndim != 3 or bands1.shape[0] != 6:
        raise ValueError("T1/T2 land-change rasters must be aligned B02/B03/B04/B08/B11/B12 stacks")
    valid = valid1 & valid2 & np.all(np.isfinite(bands1), axis=0) & np.all(np.isfinite(bands2), axis=0)
    if not valid.any():
        raise ValueError("no mutually valid T1/T2 pixels exist inside the AOI")
    magnitude, raw_classification, delta_ndvi, delta_ndbi, delta_bsi = _land_change_signals(bands1, bands2, valid)
    classification, regions, minimum_region_pixels = _clean_regions(raw_classification, pixel_area_m2)
    changed = classification > 0
    temporal_support = changed.astype(np.uint8)
    support_dates = [str(t2["acquisition_time"])[:10]]
    for acquisition_time, support_bands, support_valid_mask in support_observations or []:
        if support_bands.shape != bands1.shape or support_valid_mask.shape != valid1.shape:
            raise ValueError("support observation raster is not aligned with T1/T2")
        support_valid = valid1 & support_valid_mask & np.all(np.isfinite(support_bands), axis=0)
        _, support_raw, _, _, _ = _land_change_signals(bands1, support_bands, support_valid)
        support_classification, _, _ = _clean_regions(support_raw, pixel_area_m2)
        temporal_support += (changed & (support_classification == classification)).astype(np.uint8)
        support_dates.append(str(acquisition_time)[:10])
    repeated = changed & (temporal_support >= 2)
    latest_only = changed & (temporal_support == 1)
    hectares_per_pixel = pixel_area_m2 / 10_000
    for region in regions:
        pixels = region.pop("_pixels")
        support_values = np.asarray([temporal_support[row, column] for row, column in pixels])
        repeated_pixels = int((support_values >= 2).sum())
        latest_only_pixels = len(pixels) - repeated_pixels
        region["repeated_area_ha"] = round(repeated_pixels * hectares_per_pixel, 2)
        region["latest_only_area_ha"] = round(latest_only_pixels * hectares_per_pixel, 2)
        region["temporal_status"] = "repeated" if repeated_pixels >= latest_only_pixels else "latest_only"
    metrics = {
        "valid_area_ha": round(float(valid.sum()) * hectares_per_pixel, 2),
        "changed_area_ha": round(float(changed.sum()) * hectares_per_pixel, 2),
        "changed_pixel_count": int(changed.sum()),
        "valid_pixel_count": int(valid.sum()),
        "mean_spectral_change": round(float(magnitude[valid].mean()), 3),
        "change_threshold": LAND_CHANGE_THRESHOLD,
        "changed_share_pct": round(float(changed.sum() / valid.sum() * 100), 2),
        "vegetation_to_bare_area_ha": round(float((classification == 1).sum()) * hectares_per_pixel, 2),
        "built_up_like_area_ha": round(float((classification == 2).sum()) * hectares_per_pixel, 2),
        "other_change_area_ha": round(float((classification == 3).sum()) * hectares_per_pixel, 2),
        "change_region_count": len(regions),
        "largest_region_area_ha": regions[0]["area_ha"] if regions else 0.0,
        "minimum_region_area_ha": round(minimum_region_pixels * hectares_per_pixel, 2),
        "repeat_observed_area_ha": round(float(repeated.sum()) * hectares_per_pixel, 2),
        "latest_only_area_ha": round(float(latest_only.sum()) * hectares_per_pixel, 2),
        "temporal_observation_count": len(support_dates) + 1,
        "support_comparison_count": len(support_dates),
    }
    categories = []
    if metrics["vegetation_to_bare_area_ha"]:
        categories.append(f"{metrics['vegetation_to_bare_area_ha']:.2f} ha vegetation-to-bare/disturbed candidate")
    if metrics["built_up_like_area_ha"]:
        categories.append(f"{metrics['built_up_like_area_ha']:.2f} ha built-up-like candidate")
    if metrics["other_change_area_ha"]:
        categories.append(f"{metrics['other_change_area_ha']:.2f} ha other surface change")
    if categories:
        largest = f" The largest connected region is {metrics['largest_region_area_ha']:.2f} ha in the {regions[0]['location']} part of the selected area."
        temporal = (
            f" {metrics['repeat_observed_area_ha']:.2f} ha has the same category in at least two comparison observations; "
            f"{metrics['latest_only_area_ha']:.2f} ha appears only in the latest comparison and needs another observation for confirmation."
            if len(support_dates) > 1 else
            " Only two endpoint observations were available, so temporal repetition could not be tested."
        )
        explanation = (
            f"Between {str(t1['acquisition_time'])[:10]} and {str(t2['acquisition_time'])[:10]}, "
            f"{metrics['changed_area_ha']:.2f} ha ({metrics['changed_share_pct']:.1f}% of valid land) forms meaningful change regions: "
            + "; ".join(categories) + "." + largest + temporal
            + " These are satellite screening candidates, not confirmation of construction, ownership, or legal development."
        )
    else:
        explanation = (
            f"No connected change region larger than {metrics['minimum_region_area_ha']:.2f} ha met the conservative land-change rules "
            f"between {str(t1['acquisition_time'])[:10]} and {str(t2['acquisition_time'])[:10]}. Isolated changed pixels were removed as noise."
        )
    warnings = [
        "Two-date spectral categories can still be affected by seasonality, soil moisture, shadows, or recent earthworks.",
        "Built-up-like and vegetation-to-bare results are screening candidates and require time-series/reference-layer review.",
        "B11/B12 are native 20 m SWIR bands; 10 m output sampling does not create 10 m SWIR detail.",
    ]
    if source_mode == "demo_simulation":
        warnings.insert(0, "Demo mode uses deterministic simulated spectral grids; no satellite pixels were downloaded.")
    return {
        "workflow": "generic_land_change",
        "t1": t1,
        "t2": t2,
        "metrics": metrics,
        "evidence": {
            "grid_size": list(magnitude.shape),
            "spectral_change_magnitude": magnitude.round(4).tolist(),
            "change_mask": changed.astype(np.uint8).tolist(),
            "change_classification": classification.tolist(),
            "change_regions": regions,
            "temporal_support_count": temporal_support.tolist(),
            "support_observation_dates": support_dates,
            "observation_dates": [str(t1["acquisition_time"])[:10]] + sorted(support_dates),
            "observable_effects": [
                {
                    "category": "vegetation_to_bare_candidate",
                    "area_ha": metrics["vegetation_to_bare_area_ha"],
                    "observed_effect": "Vegetated surface cover decreased while exposed-soil or disturbed-ground signals increased.",
                    "decision_relevance": "Check for clearing, harvest, grading, excavation, or seasonal exposure in this region.",
                },
                {
                    "category": "built_up_like_candidate",
                    "area_ha": metrics["built_up_like_area_ha"],
                    "observed_effect": "The surface response shifted toward material associated with built or hardened cover.",
                    "decision_relevance": "Check for new roofs, paving, compacted ground, or construction activity using site or higher-resolution evidence.",
                },
                {
                    "category": "other_surface_change",
                    "area_ha": metrics["other_change_area_ha"],
                    "observed_effect": "The land surface changed materially but did not satisfy the clearing or built-up-like rules.",
                    "decision_relevance": "Inspect this region before assigning a cause; moisture, shadow, earthworks, and seasonal cover remain possible.",
                },
            ],
            "delta_ndvi": np.where(valid, delta_ndvi, 0).round(4).tolist(),
            "delta_ndbi": np.where(valid, delta_ndbi, 0).round(4).tolist(),
            "delta_bsi": np.where(valid, delta_bsi, 0).round(4).tolist(),
            "valid_mask": valid.astype(np.uint8).tolist(),
            "thresholds": {
                "vegetation_to_bare": "NDVI T1 >= 0.30, delta NDVI <= -0.15, delta BSI >= 0.08",
                "built_up_like": "delta NDBI >= 0.12, NDBI T2 >= -0.10, NDVI T2 <= 0.45",
                "other_change_gte": 0.18,
                "minimum_region_pixels": minimum_region_pixels,
            },
            "source_mode": source_mode,
            "crs": crs,
            "resolution_m": resolution_m,
            "bands": ["B02", "B03", "B04", "B08", "B11", "B12"],
            "effective_swir_resolution_m": max(20, resolution_m),
        },
        "warnings": warnings,
        "explanation": explanation,
        "explanation_source": "deterministic_template",
    }
