# Evidence and Verification

## Evidence-first contract

Every user-visible scientific claim must trace to structured evidence.

```text
AnalysisResult
├─ source observations
├─ workflow
├─ masks / polygons / maps
├─ metrics
├─ warnings
├─ verification state
└─ provenance
```

## Required provenance

- AOI
- provider
- scene/product ID
- satellite/sensor
- exact acquisition dates
- bands/product level
- processing steps
- model/tool version

## Measurement

Area/distance/count are deterministic GIS outputs, never language-model generations.

## Agriculture claim policy

Allowed when supported:

- vegetation increased/decreased
- area crossing a configured threshold
- anomalous regions
- temporal trend

Not allowed without dedicated validation:

- disease cause
- nutrient deficiency
- yield loss

## Urban claim policy

Prefer "land change", "built-up expansion" or "green-cover loss" according to actual workflow evidence. A generic change mask must not be relabeled as construction automatically.

## Verification statuses

```text
PASS
WARN
FAIL
```

Failures include missing required bands, insufficient overlap, unusable quality/cloud conditions, incompatible temporal pair, or invalid geospatial scale for physical measurements.
