# API Contract — Prototype

## Query planning

```text
POST /api/v1/requests/plan
```

The planner converts a bounded user question into a typed `sector`, `workflow`, required-band contract, requested outputs, confidence and claim limitations. Supported workflows are `observation_discovery`, `vegetation_change`, and `generic_land_change`. Ambiguous or domain-only questions fall back to discovery rather than guessing an analysis.

## AOI

```text
POST /api/v1/locations
GET  /api/v1/locations/{id}
```

Create a monitored location with AOI, sector and period.

Completed reports for a saved location are available newest-first:

```text
GET /api/v1/locations/{location_id}/analyses
```

## Observation discovery

```text
POST /api/v1/observations/search
```

Request:

```json
{
  "aoi": {"type": "Polygon", "coordinates": []},
  "period": {"from": "2026-03-01", "to": "2026-09-01"},
  "sector": "agriculture"
}
```

Response returns candidate metadata and selected T1/T2 when possible.

## Analyze

```text
POST /api/v1/analyses
GET  /api/v1/analyses/{id}
```

Initial workflow values:

```text
vegetation_change
generic_land_change
```

An analysis response includes typed raster artifact descriptors for `t1`, `t2`, and `change`. Each descriptor carries its media type, dimensions, acquisition date, source mode, WGS84 image-corner coordinates, legend, and an immutable analysis-scoped URL.

```text
GET /api/v1/analyses/{analysis_id}/artifacts/{artifact_id}
```

Only artifacts registered in the persisted analysis can be retrieved. Current raster artifacts are PNG presentation products; numerical grids, thresholds, CRS, resolution, metrics, and warnings remain in the structured analysis response.

Generic land-change responses also include `change_regions`, `observable_effects`, `observation_dates`, and a `temporal_support_count` grid. Metrics distinguish `repeat_observed_area_ha` from `latest_only_area_ha`. A repeated category means the same baseline-relative category occurred in multiple comparison observations; it is not a causal or legal conclusion.

All completed analyses include a structured `interpretation` and `evidence.observation_summary`. These fields provide the human-facing reasoning chain and observation-selection provenance while retaining the legacy `explanation` string for backward compatibility.

Optional Qwen narration is returned in `interpretation.plain_language_summary` with `language_source` and `language_status`. Unconfigured, unavailable, malformed, or numerically inconsistent model output falls back to verified deterministic wording.

Additional product endpoints:

```text
GET  /api/v1/capabilities
POST /api/v1/providers/{provider}/search
POST /api/v1/locations/{location_id}/monitor/check
POST /api/v1/locations/{location_id}/price-comparables
GET  /api/v1/locations/{location_id}/price-summary
```

Price summaries accept verified user-provided comparables only and reject mixed currencies rather than inferring conversion.

## Upload — secondary

A later expert endpoint may accept user-supplied imagery, but upload is not the primary product path.
