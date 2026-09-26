# Language Layer

## Role

Qwen-family models are candidates for two bounded tasks:

1. convert natural language into a typed observation/analysis request;
2. explain already verified structured evidence.

## Example intent

User:

> "Show where vegetation dropped most over the last six months."

Typed output:

```json
{
  "sector": "agriculture",
  "workflow": "vegetation_change",
  "period_months": 6,
  "requested_outputs": ["decline_regions", "area", "explanation"]
}
```

Deterministic policy validates whether the required data exists.

## Implemented request planner

The prototype currently uses a deterministic, inspectable planner at `POST /api/v1/requests/plan` before adding Qwen. It routes explicit questions to:

```text
observation / availability question -> observation_discovery
vegetation + temporal change        -> vegetation_change
urban / land + temporal change      -> generic_land_change
ambiguous or domain-only question   -> observation_discovery
```

Each plan exposes its recognized terms, confidence, required bands, requested outputs, rationale, and claim limitations. A future Qwen planner must emit the same typed contract and pass the same deterministic validation.

## Implemented evidence brief

Every completed analysis now includes a structured `interpretation` assembled from verified metrics and region summaries. It contains:

- a direct-answer headline;
- a plain-language answer with measured areas or vegetation statistics;
- an explicit confidence label and explanation;
- evidence points supporting the answer;
- decision relevance expressed as conditional implications;
- limitations and a next verification action.

The accompanying `observation_summary` explains candidate, qualified, rejected, and intermediate-scene counts; selected dates; comparison span; selection rationale; and the difference between scene cloud metadata and AOI valid pixels. This is the stable input/output boundary for a future small Qwen model. A model may improve phrasing, but deterministic validation must ensure every number, category, date, and limitation remains unchanged.

## Explanation input

The LLM receives structured values such as:

- T1/T2 dates
- metrics
- evidence region summaries
- warnings
- provider/sensor metadata

It does not calculate NDVI, area, masks, scene selection or cloud validity.

## Chat is not the product

Natural-language interaction sits on top of the monitored-location workflow. The map/evidence/history remain primary.
