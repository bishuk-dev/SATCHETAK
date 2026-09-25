# API Contract

This is the intended stable product contract. Exact transport details may evolve, but scientific semantics should not.

## Create analysis

```http
POST /api/v1/analyses
```

Multipart or staged-upload request containing:

```json
{
  "query": "Where has flooding expanded?",
  "workflow": "auto",
  "input_ids": ["..."],
  "metadata_overrides": {}
}
```

The free-form `query` is interpreted into a typed intent by the language layer before deterministic feasibility validation and routing.

`workflow` values:

```text
auto
single_image
change
flood
agriculture
```

An explicit workflow is useful for debugging and evaluation.

## Analysis response

For asynchronous operation:

```json
{
  "analysis_id": "an_...",
  "status": "queued"
}
```

## Get analysis

```http
GET /api/v1/analyses/{analysis_id}
```

Statuses:

```text
queued
running
completed
failed
```

Scientific outcome is separate:

```text
SUCCESS
SUCCESS_WITH_WARNING
REQUEST_INPUT
UNSUPPORTED
ABSTAIN
ERROR
```

## Final result

```json
{
  "analysis_id": "an_123",
  "workflow": "flood",
  "outcome": "SUCCESS_WITH_WARNING",
  "answer": "Flood expansion is detected in the highlighted region.",
  "claims": [
    {
      "id": "c1",
      "text": "Flood expansion is detected.",
      "evidence_ids": ["e1"],
      "support_level": "DIRECT_MODEL_EVIDENCE"
    }
  ],
  "evidence": [
    {
      "id": "e1",
      "type": "RASTER_MASK",
      "artifact_url": "/api/v1/analyses/an_123/artifacts/flood_mask.tif",
      "coordinate_space": "MAP_CRS"
    }
  ],
  "metrics": [],
  "warnings": [],
  "model_runs": [
    {
      "model_id": "microsoft-ai4g-flood",
      "revision": "...",
      "preprocessing_profile": "..."
    }
  ]
}
```

## Flood model endpoints

During qualification:

```http
POST /api/v1/flood/ai4g
POST /api/v1/flood/prithvi
```

These validate only their own model contracts, never silently fall back, and normalize successful outputs to the same `FloodEvidence` schema.

After both qualify:

```http
POST /api/v1/flood
```

Suggested policy values:

```text
auto
ai4g
prithvi
compare
```

`compare` is allowed only when both compatible input sets are available. It returns independent evidence objects and performs no automatic mask fusion.

## Artifact access

```http
GET /api/v1/analyses/{id}/artifacts/{artifact}
```

Artifacts may include:

- preview PNG;
- GeoTIFF mask;
- GeoJSON polygons;
- result JSON;
- trace JSON.

## Error semantics

HTTP errors handle transport/security problems.

Scientific unsupported cases should normally return a valid analysis result with:

```text
outcome = REQUEST_INPUT / UNSUPPORTED / ABSTAIN
```

This prevents “unsupported science” from being confused with server failure.

## Versioning

Public schemas are versioned under `/api/v1`.

The language interpreter's internal `IntentRequest` schema is also versioned so prompt/model changes cannot silently alter routing semantics.

Model revisions are independent of API version and always appear in provenance.
