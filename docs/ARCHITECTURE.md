# Architecture

## Architectural style

The MVP is a **modular monolith**, not a microservice platform.

One API process owns request orchestration. Model adapters are in-process when dependency-compatible. A model may move to an isolated runner only after an actual runtime/dependency conflict is demonstrated.

## Main components

```text
┌─────────────────────────────────────────────────────────────┐
│                         Web UI                              │
│ Next.js + map/raster viewer + evidence panels              │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI                              │
│ auth/limits • upload • jobs • result transport             │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Input Inspector                          │
│ format • metadata • bands • modality • CRS • time          │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                Language Interpreter                         │
│ open LLM → typed intent / parameters                        │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                Feasibility Validator                        │
│ input contract • required bands • pair semantics            │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 Deterministic Router                        │
│ SINGLE_IMAGE | CHANGE | FLOOD | AGRICULTURE                │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      Workflow                               │
│ validates workflow-specific preconditions                  │
│ coordinates model adapter + geospatial operations          │
└───────────────┬────────────────────────────┬────────────────┘
                │                            │
                ▼                            ▼
┌──────────────────────────┐      ┌───────────────────────────┐
│     Model adapters       │      │    Geo operators          │
│ EarthDial / Open-CD /    │      │ align • reproject •       │
│ AI4G Flood / Prithvi     │      │ polygonize • area • index │
└───────────────┬──────────┘      └────────────┬──────────────┘
                └──────────────┬───────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Verification                             │
│ sensor validity • geometry • output sanity • claim support │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Evidence/result layer                      │
│ answer • mask • boxes • metrics • warnings • provenance    │
└─────────────────────────────────────────────────────────────┘
```

## Package boundaries

```text
satquery/contracts/
```

Typed public domain schemas. No heavy ML/GDAL side effects.

```text
satquery/ingestion/
```

Safe raster inspection, metadata inventory, band mapping, modality state.

```text
satquery/geo/
```

Pure/deterministic geospatial operations: reprojection, alignment checks, mask geometry, area, index math.

```text
satquery/language/
```

Replaceable open-LLM boundary for free-form query interpretation and verified-result explanation. It returns typed schemas and never executes scientific tools directly.

```text
satquery/routing/
```

Maps validated typed intent + input inventory to one of four workflows. Routing is deterministic after language interpretation. No free-form planning loop.

```text
satquery/workflows/
```

Owns domain composition. A workflow is allowed to call one or more model adapters and geo operators.

```text
satquery/model_adapters/
```

One adapter per model family. Each adapter owns exact preprocessing/postprocessing and declares its input contract.

```text
satquery/verification/
```

Checks that result claims are supported by compatible evidence.

```text
satquery/evidence/
```

Writes masks, GeoJSON, previews, traces, and the final structured result.

## Model adapter interface

Conceptually:

```python
class ModelAdapter:
    model_id: str
    capabilities: set[str]

    def validate_input(self, inventory) -> ValidationResult: ...
    def load(self) -> None: ...
    def infer(self, request) -> ModelOutput: ...
    def health(self) -> ModelHealth: ...
```

The interface should remain stable even if a model later moves to a separate process.

## Language model interface

Conceptually:

```python
class LanguageInterpreter:
    def interpret(self, query, input_summary) -> IntentRequest: ...

class ExplanationGenerator:
    def explain(self, verified_result, query) -> str: ...
```

The same underlying Qwen-family model may serve both interfaces, but prompts/schemas stay separate. The language model cannot add unregistered workflow names or bypass feasibility checks.

## Workflow interface

Each workflow receives:

```text
query
input inventory
runtime artifact directory
```

and returns an `AnalysisResult`.

A workflow must not expose raw framework-specific tensors outside its internal/model-adapter boundary.

## State and storage

Do not add PostgreSQL/Redis on day one.

Initial persistence:

```text
runtime/
  analyses/
    <analysis_id>/
      request.json
      inventory.json
      trace.json
      result.json
      artifacts/
```

This is sufficient for deterministic local development and demos.

Add a database only when concurrent users, long-term history, authentication, or distributed workers make it necessary.

## Job execution

Phase 1-4 may use synchronous execution for development.

Before the final UI, long model calls should use a bounded local job queue:

```text
POST /analyses
→ analysis_id

GET /analyses/{id}
→ queued | running | completed | failed
```

No Redis/Celery requirement until one process is insufficient.

## Frontend

Preferred:

```text
Next.js + TypeScript
MapLibre GL JS
```

Raster display should use server-generated tiles/previews rather than loading arbitrary multi-gigabyte GeoTIFFs directly into the browser.

Use `rio-tiler`/COG tile endpoints inside the API before deploying a separate TiTiler service.

## Dependency isolation rule

Do not preemptively create four model services.

Start in one Python environment where possible.

If a qualified adapter forces incompatible dependency versions, isolate **that adapter only** behind a local process/container with a small versioned JSON contract.

## Observability

Each inference trace records:

- analysis ID;
- workflow;
- input IDs/hashes;
- model ID/revision;
- preprocessing profile;
- device;
- start/end timestamps;
- warnings;
- artifact IDs;
- failure code.

Do not expose hidden chain-of-thought.

## Quantitative computation

Physical quantities follow:

```text
model/algorithm mask
      ↓
valid-mask intersection
      ↓
pixel → geospatial geometry
      ↓
project to suitable metric CRS where needed
      ↓
area/distance/count
```

A language model never generates the number.
