# Architecture

## Implemented prototype stack

```text
Frontend   React 19 + TypeScript + Vite + MapLibre GL
Backend    FastAPI + Pydantic 2 + Uvicorn
Storage    SQLite + filesystem
Testing    Pytest + FastAPI/httpx TestClient
```

The repository remains a modular monolith. FastAPI owns the typed HTTP boundary and OpenAPI contract; domain calculations remain framework-independent. React consumes the API through typed client functions, and the production Vite bundle can be served by FastAPI from `frontend/dist`.

## Product architecture

```text
USER
  │
  ├─ place / lat-long
  ├─ AOI drawing
  ├─ sector: agriculture | urban_land
  └─ period / question
  ▼
AOI SERVICE
  ▼
OBSERVATION PLANNER
  ▼
PROVIDER ADAPTER
  ├─ Copernicus Data Space
  ├─ Bhoonidhi
  └─ Planetary Computer
  ▼
CANDIDATE SCENES
  ▼
QUALITY / CLOUD / COVERAGE FILTER
  ▼
T1 / T2 SELECTOR
  ▼
ACQUISITION + NORMALIZATION
  ▼
DOMAIN WORKFLOW
  ├─ Agriculture
  └─ Urban / Land
  ▼
GIS METRICS + VERIFIER
  ▼
EVIDENCE OBJECT
  ▼
QWEN EXPLANATION
  ▼
MAP / DASHBOARD / REPORT
```

Bhuvan is integrated separately as a thematic/reference-layer provider.

## Primary domain objects

### MonitoredLocation

```text
id
name
AOI
sector
observation_policy
baseline_observation
latest_observation
observation_history
analysis_history
```

### Observation

```text
provider
provider_scene_id
satellite
sensor
acquisition_time
cloud_cover
product_level
bands
CRS
asset_references
quality_state
```

### Analysis

```text
location_id
T1
T2
workflow
evidence
artifacts
metrics
warnings
explanation
```

`evidence` contains numerical scientific inputs/outputs. `artifacts` contains immutable presentation products derived from those same arrays. Keeping the two separate prevents UI rendering concerns from becoming the scientific contract and lets later classifiers add new overlays or polygon products without changing observation acquisition.

Prototype artifact persistence is analysis-scoped filesystem storage beside SQLite. The API authorizes artifact reads through the persisted analysis descriptor instead of exposing arbitrary filesystem paths.

## Provider boundary

Keep the provider contract minimal:

```python
class ImageryProvider:
    search(aoi, date_range, requirements)
    get_metadata(scene_id)
    acquire(scene_id, assets=None)
```

Analytics code must not depend directly on provider HTTP APIs.

## Modular monolith

Use one FastAPI backend initially.

Suggested modules:

```text
satchetak/
├─ contracts/
├─ aoi/
├─ imagery/
│  ├─ provider.py
│  ├─ copernicus.py
│  ├─ bhoonidhi.py
│  ├─ planetary_computer.py
│  └─ ranking.py
├─ workflows/
│  ├─ agriculture/
│  └─ land_change/
├─ geo/
├─ language/
├─ evidence/
└─ verification/
```

## Persistence

Prototype: filesystem + SQLite if persistence is needed.

Do not introduce distributed infrastructure until the working vertical slice requires it.
