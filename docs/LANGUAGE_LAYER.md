# Language Intelligence Layer

## Purpose

SatQuery needs natural-language understanding, but the language model is **not** the scientific decision-maker.

The language layer performs four jobs:

1. **Intent interpretation** — convert free-form user language into a bounded SatQuery task.
2. **Parameter extraction** — identify requested region, temporal relation, measurement request, and desired output.
3. **Clarification** — turn structured validation failures into clear user-facing requests.
4. **Explanation** — convert verified evidence and deterministic metrics into concise natural-language results.

The language model does **not**:

- decide whether a scientific operation is physically valid;
- invent missing bands, dates, CRS, sensor metadata, masks, area, or confidence;
- execute arbitrary tools or Python;
- choose unregistered workflows;
- override input-contract failures.

## Architecture

```text
Natural-language query
        │
        ▼
Language Interpreter
(open generative LLM)
        │
        ▼
Typed Intent + Parameters
        │
        ▼
Input / Feasibility Validator
        │
        ▼
Deterministic Router
        │
        ▼
Qualified Specialist Workflow
        │
        ▼
Evidence + GIS Metrics
        │
        ▼
Verifier
        │
        ▼
Language Explanation Generator
        │
        ▼
User-facing answer
```

The same open-weight LLM may be used for both interpretation and explanation, but these are separate prompts and schemas.

## Candidate model family

Qwen instruction-tuned open-weight models are the preferred first family to evaluate for the language layer.

The required abilities are modest compared with the remote-sensing perception stack:

```text
intent classification
structured JSON output
parameter extraction
clarification
short evidence-grounded explanation
multilingual query handling
```

Do not automatically select the largest available Qwen checkpoint.

Qualification should compare a small/medium local candidate against a larger candidate and choose the smallest model that satisfies the language test suite with acceptable latency.

The language model is replaceable. The system contract depends on typed schemas, not one vendor/model family.

## Typed intent schema

Initial intent vocabulary:

```text
SINGLE_IMAGE
CHANGE
FLOOD
AGRICULTURE
UNKNOWN
```

Example:

```json
{
  "intent": "FLOOD",
  "operation": "detect_new_flooding",
  "requires_pair": true,
  "measurement_requested": true,
  "roi_reference": null,
  "target_description": "newly flooded regions"
}
```

The schema should also support:

```text
requested_output
temporal_reference
spatial_reference
measurement_type
clarification_needed
```

Do not allow the model to create arbitrary workflow/tool names.

## Validation boundary

The language model may output:

```text
intent = AGRICULTURE
measurement = NDVI_CHANGE
```

The scientific validator then checks:

```text
Are there two images?
Are Red and NIR bands known?
Are they spatially compatible?
Is temporal order known?
```

Only after validation may the deterministic router execute the workflow.

This is the core policy:

> **The LLM may request a capability. Deterministic policy decides whether the capability is permitted and physically possible.**

## Structured-output handling

Use strict JSON/Pydantic validation.

Recommended behavior:

```text
LLM output
   ↓
schema valid?
   ├─ yes → continue
   └─ no  → one constrained repair/retry
                 ↓
             still invalid?
                 ↓
          UNKNOWN / clarification
```

Never use:

```python
eval(model_output)
```

Never parse free-form tool commands.

## Generation settings

For intent extraction:

- low temperature;
- short maximum output;
- JSON/schema constrained;
- no chain-of-thought requirement.

For final explanation:

- low-to-moderate temperature;
- evidence/metric payload only;
- explicit instruction not to introduce unsupported facts;
- concise answer with warnings.

## Evidence-grounded explanation

The explanation model receives:

```text
user query
validated input summary
workflow name
structured claims
evidence summary
deterministic metrics
warnings
provenance
```

It does not receive authority to reinterpret rejected evidence.

Example evidence:

```json
{
  "workflow": "FLOOD",
  "claims": [
    {
      "text": "New flood extent is present in the eastern region.",
      "support": "DIRECT_MODEL_EVIDENCE"
    }
  ],
  "metrics": [
    {
      "name": "new_flood_area",
      "value": 1.83,
      "unit": "km2",
      "support": "DETERMINISTIC_DERIVATION"
    }
  ],
  "warnings": [
    "Permanent-water filter not applied."
  ]
}
```

Possible final response:

> Newly detected flooding covers approximately 1.83 km² in the eastern part of the valid overlap. Permanent-water filtering was not applied, so persistent water bodies may still be present in the mask.

The 1.83 km² number comes from GIS computation, not the language model.

## Clarification behavior

Example:

User:

> “What changed here?”

Only one image is uploaded.

Scientific validator returns:

```json
{
  "outcome": "REQUEST_INPUT",
  "missing": ["second_temporal_observation"]
}
```

Language layer converts this to:

> Change analysis needs a second observation of the same area from another time. Upload the second image and, if the acquisition dates are not embedded in the files, specify which observation is earlier.

## Multi-step requests

Some user requests may require more than one allowed operation.

Example:

> “Compare these two images, calculate vegetation decrease inside my polygon, and summarize the result.”

The LLM may produce a bounded plan:

```json
[
  {"workflow": "AGRICULTURE", "operation": "VEGETATION_CHANGE"},
  {"operation": "APPLY_ROI"},
  {"operation": "SUMMARIZE"}
]
```

The router validates every operation against an allowlist.

No arbitrary Python, shell, dynamic imports, or model-selected network calls.

## Confidence

The language model does not generate scientific confidence.

Until calibration exists:

```text
system_confidence = null
```

The explanation layer may communicate warnings and evidence strength, but must not invent percentages.

## Evaluation

Create a language test set containing:

- direct intents;
- paraphrases;
- colloquial phrasing;
- ambiguous queries;
- mixed Hindi/English where relevant;
- unsupported requests;
- queries requiring clarification;
- multi-part requests.

Metrics:

```text
intent accuracy
schema validity rate
parameter extraction accuracy
clarification correctness
unsupported-operation rejection
hallucinated-field rate
latency
memory footprint
```

Promote the smallest model that passes the declared thresholds.

## Deployment

The language model should be served behind a small internal interface:

```text
interpret(query, input_summary) -> IntentRequest
explain(verified_result, query) -> str
```

This keeps it replaceable.

The rest of SatQuery must continue to work if the language model is swapped from Qwen to another open model that satisfies the same contract.
