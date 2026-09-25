# Evidence and Verification

## Goal

A SatQuery answer is a set of **claims linked to evidence**, not merely generated text.

## Result shape

Conceptually:

```json
{
  "status": "SUCCESS",
  "workflow": "FLOOD",
  "answer": "Flood expansion is detected in the highlighted region.",
  "claims": [],
  "evidence": [],
  "metrics": [],
  "warnings": [],
  "model_runs": [],
  "provenance": {}
}
```

## Claim

Each claim contains:

```text
claim_id
text
claim_type
evidence_ids
support_level
```

Support levels:

```text
DIRECT_MODEL_EVIDENCE
DETERMINISTIC_DERIVATION
QUALITATIVE_INTERPRETATION
UNSUPPORTED
```

`UNSUPPORTED` claims are not returned as affirmative conclusions.

## Evidence types

```text
RASTER_MASK
BOUNDING_BOX
POLYGON
MODEL_SCORE
SPECTRAL_INDEX
METADATA
CHANGE_MAP
CLASS_MAP
TEXT_OBSERVATION
```

Each evidence object records its coordinate space:

```text
MODEL_PIXELS
ORIGINAL_PIXELS
MAP_CRS
```

Do not mix coordinate spaces silently.

## Numeric metrics

Examples:

- changed pixels;
- changed hectares;
- flood hectares;
- mean NDVI T1/T2;
- class area.

Each metric records:

```text
value
unit
derivation
source_evidence_ids
CRS / projection used
valid-pixel policy
```

## Confidence

Initial policy:

### VLM
No numeric confidence by default.

```text
confidence = null
```

Language-model token likelihood is not presented as a calibrated probability of factual correctness.

### Segmentation/change
Expose model probabilities as:

```text
model_score
```

not `confidence`, unless calibration has been evaluated.

### System confidence
Disabled until a calibration design exists.

This is preferable to decorative “92% confidence”.

## Verifier categories

### Input validity

- model input contract satisfied?
- required bands present?
- correct number of images?
- compatible modality?
- temporal order known?

### Geometric validity

- overlapping extent?
- alignment state known?
- mask mapped correctly to original coordinates?
- metric uses a valid CRS?

### Physical validity

Examples:

- NDVI requires Red and NIR;
- SAR backscatter cannot directly provide optical color;
- crop model requires exact HLS-style channels/timestamps;
- AI4G flood requires its SAR contract.

### Output sanity

- mask dimensions match adapter contract;
- mask contains finite values;
- probability range valid;
- empty result handled explicitly;
- output artifact can be mapped back to source image.

### Claim support

Every answer sentence making a concrete scientific claim must point to evidence.

The VLM may summarize:

```text
mask says region changed
```

It may not upgrade this into:

```text
illegal construction occurred
```

without a model/tool providing that evidence.

## Failure outcomes

```text
SUCCESS
SUCCESS_WITH_WARNING
REQUEST_INPUT
UNSUPPORTED
ABSTAIN
ERROR
```

### Examples

| Situation | Outcome |
|---|---|
| One image + change question | REQUEST_INPUT |
| Missing NIR + NDVI | UNSUPPORTED |
| Missing CRS + qualitative single-image VQA | SUCCESS_WITH_WARNING |
| Missing CRS + area request | UNSUPPORTED |
| Non-overlapping temporal pair | UNSUPPORTED |
| Unknown SAR preprocessing for AI4G Flood | UNSUPPORTED |
| Model returns empty valid mask | ABSTAIN |
| Model crashes/out of memory | ERROR |

## Language generation

Text explanation is downstream of evidence.

Preferred prompt payload to explanation model:

```text
user question
validated metadata summary
structured evidence summary
computed metrics
warnings
```

Do not pass hidden verifier state and ask the model to “decide whether it is valid”; validity is programmatic.
