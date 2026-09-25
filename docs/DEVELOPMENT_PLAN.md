# Development Plan

This rebuild is intentionally sequential. Do not jump ahead.

## Phase 0 — Freeze the specification

Deliverables:

- docs accepted;
- legacy code preserved;
- clean rebuild branch/repository selected;
- model sources recorded;
- no implementation yet.

Exit gate:

```text
scope, architecture, workflows and model policy agreed
```

---

## Phase 1 — Geospatial ingestion foundation

Build only:

- safe upload;
- raster inventory;
- canonical band roles;
- modality state;
- pair overlap/alignment checks;
- original-pixel ↔ map-coordinate transforms;
- runtime artifact folder.

No model inference.

Tests:

- GeoTIFF metadata fixture;
- PNG/JPEG fixture;
- missing CRS;
- bad/corrupt TIFF;
- non-overlapping pair;
- wrong/unknown band metadata.

Exit gate:

> We can explain exactly what data was uploaded and whether a requested workflow is physically feasible.

---

## Phase 2 — Language interpretation contract

Build:

- `IntentRequest` schema;
- bounded intent vocabulary;
- open-LLM adapter (Qwen-family first candidate);
- JSON/schema validation;
- one repair retry;
- clarification generator;
- language test suite.

No scientific workflow execution through the LLM.

Exit gate:

- direct/paraphrased intents parse correctly;
- unsupported requests become `UNKNOWN`/clarification;
- invalid JSON cannot escape validation;
- model can be swapped behind the same interface.

---

## Phase 3 — Single-image vertical slice

Build:

```text
upload → inspect → EarthDial adapter → answer/evidence → verifier → result
```

No router complexity beyond explicitly choosing `single_image`.

Required:

- one qualified RGB path;
- at least one grounded output path if model supports it reliably;
- no fabricated confidence;
- model revision/preprocessing in trace.

Exit gate:

- success case works end to end;
- unsupported quantitative request is rejected;
- model failure does not corrupt the analysis record.

---

## Phase 4 — Generic paired change

Build:

```text
T1/T2 validation
→ target comparison grid
→ Open-CD adapter
→ change mask
→ map back to original/geospatial space
→ metrics
```

Evaluate at least two pretrained checkpoint candidates before naming a default.

Exit gate:

- aligned test pair produces a mask;
- T1/T1 sanity test;
- non-overlap rejection;
- changed-area computation works when CRS permits.

---

## Phase 5 — SAR flood

Build the Microsoft AI4G Flood adapter.

Required:

- exact pre/post VV/VH contract;
- preprocessing profile;
- permanent-water filtering state;
- valid-data mask;
- flood area if georeferenced;
- explicit rejection for unsupported SAR.

Exit gate:

- official/example input reproduces valid inference;
- wrong polarization/radiometry is rejected;
- output mask/area maps correctly to source raster.

---

## Phase 6 — Agriculture

### 6A — deterministic vegetation change

Build:

- NDVI;
- ΔNDVI;
- invalid/cloud masking where available;
- area/statistics.

Exit gate:

- analytical unit tests;
- valid T1/T2 example;
- missing NIR refusal.

### 6B — narrow crop model

Integrate IBM/NASA Prithvi multi-temporal crop classifier.

Exit gate:

- exact 18-band/3-timestamp stack works;
- wrong band count/order rejected;
- class-map change evidence rendered.

---

## Phase 7 — Unified router and API

Only after all four workflows work independently.

Build bounded router:

```text
SINGLE_IMAGE
CHANGE
FLOOD
AGRICULTURE
```

Router chooses from validated capabilities; it does not invent workflows.

Exit gate:

- routing matrix tests;
- every route can be forced explicitly for debugging;
- invalid/ambiguous request returns `REQUEST_INPUT`.

---

## Phase 8 — Frontend

Build:

- upload inventory;
- query box;
- map/image viewer;
- before/after swipe for pair workflows;
- mask/box overlay;
- metrics;
- warnings;
- provenance/trace drawer.

No decorative fake confidence.

Exit gate:

- user can visually inspect evidence in original image/map coordinates.

---

## Phase 9 — Hardening and demo

- pin all model revisions/hashes;
- benchmark qualified models;
- profile GPU/RAM;
- offline/cached demo data;
- failure demo;
- exportable analysis JSON/report;
- security limits;
- clean install script.

Exit gate:

> Fresh machine → documented setup → four prepared workflows execute without manual code edits.

---

# Phase rule for AI agents

At the beginning of every coding task, write:

```text
Current phase:
Exit gate:
This task contributes:
Out of scope:
```

If the requested change belongs to a later phase, do not sneak it in.
