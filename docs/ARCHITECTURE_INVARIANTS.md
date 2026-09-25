# Architecture Invariants and Final Verification

These rules prevent later phases from silently breaking earlier scientific assumptions.

## Non-negotiable invariants

1. **Language is not science.** The open LLM interprets/explains; it does not create measurements, evidence, missing bands, or confidence.
2. **Feasibility precedes routing.** Query + inputs → inspect → typed intent → validate → deterministic route → workflow.
3. **Each model owns an explicit input contract.** There is no generic "image tensor" contract.
4. **Model-specific differences are preserved until after inference.** Only outputs normalize to shared evidence schemas.
5. **GIS owns physical measurement.** Area/distance/count come from evidence geometry + valid geospatial metadata.
6. **NoData/cloud is not a negative class.**
7. **Every resize/tile/reprojection/resampling transform is reconstructible.**
8. **Model failure never triggers a hidden semantic fallback.**
9. **Explicit model endpoints remain testable during qualification.**
10. **No optical/SAR flood fusion exists until separately specified and evaluated.**
11. **Every run records model ID, revision, preprocessing profile, and checkpoint hash where practical.**
12. **Only qualified adapters may participate in `auto` routing.**
13. **Later UI/router work cannot redefine scientific adapter contracts.**
14. **Workflow A never calls Workflow B.** Shared low-level utilities are composed below workflows.

## Dependency direction

```text
contracts
  ↑
ingestion / geo / language
  ↑
model_adapters
  ↑
workflows
  ↑
verification + evidence
  ↑
API
  ↑
UI
```

Forbidden dependency cycles include:

```text
model_adapter → router
geo → workflow
contracts → model implementation
workflow A → workflow B
```

## Flood architecture

```text
FloodWorkflow
  ├── AI4GFloodAdapter      (Sentinel-1 SAR pre/post VV/VH)
  └── PrithviFloodAdapter   (Sentinel-2 6-band optical)
             ↓
        FloodEvidence
             ↓
        Geo operators
             ↓
          Verifier
             ↓
       AnalysisResult
```

Adapters never select each other.

## Required regression tests

### Routing / endpoint isolation
- `/flood/ai4g` cannot invoke Prithvi.
- `/flood/prithvi` cannot invoke AI4G.
- `auto` refuses if neither input contract matches.
- `compare` refuses unless both compatible inputs are present.

### Scientific contracts
- Prithvi rejects RGB-only input.
- Prithvi rejects missing NIR/SWIR.
- Prithvi preserves cloud/no-data.
- AI4G rejects missing pre/post pair.
- AI4G rejects missing VV/VH.
- Unknown SAR radiometry is not silently marked qualified.
- Missing CRS disables physical area but not otherwise-valid pixel masks.

### Geometry
- output masks map back to original raster coordinates.
- tiled output has no deterministic seam/gap under fixture tests.
- categorical masks use nearest-neighbor reprojection.
- metric area is computed in an appropriate metric/equal-area CRS.

### Failures
- OOM/model exception → `ERROR`.
- invalid evidence geometry → measurement omitted.
- language request cannot bypass scientific validator.
- second flood model is never a hidden fallback.

## Change-control rule

Changing an invariant requires:

1. an ADR update;
2. updated workflow/input contract;
3. regression tests;
4. documented technical reason;
5. explicit approval for major architecture changes.
