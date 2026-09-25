# AGENTS.md

Repository-wide instructions for any AI coding agent working on SatQuery AI.

## Mission

Build a small, reliable remote-sensing system around **qualified pretrained models** and deterministic geospatial operations.

The initial product has one replaceable **language layer** plus exactly four supported scientific workflows:

```text
language interpretation/explanation

single image
paired change
flood
agriculture change
```

Do not broaden scope unless the user explicitly approves it.

## Prime directive

> **The model may explain evidence. It may not invent evidence.**

This means:

- no guessed CRS, GSD, bands, polarization, acquisition date, or sensor;
- no guessed masks, bounding boxes, areas, distances, counts, or confidence;
- no “reasonable default” that changes the physical meaning of data;
- no hidden fallback from a failed specialist to a generic VLM that still returns a confident answer.

## No-training rule

The rebuild starts with **inference only**.

Do not add:

- training loops,
- LoRA/QLoRA,
- PEFT adapters,
- fine-tuning datasets,
- synthetic training data,
- hyperparameter sweeps,

unless the user explicitly changes this decision.

Allowed:

- downloading/pinning approved pretrained checkpoints;
- deterministic preprocessing required by a model card/paper;
- benchmark evaluation;
- threshold selection on a declared validation set;
- post-processing whose assumptions are documented and tested.

## Phase lock

Read `docs/DEVELOPMENT_PLAN.md` before making changes.

Only implement the **current phase**. A later phase must not be started merely because it is convenient.

Every phase has an exit gate. If the gate fails, fix the current phase instead of layering more code over it.

## Mandatory pre-edit routine

Before editing:

1. `git status`
2. `git log --oneline -10`
3. Read:
   - `docs/DECISIONS.md`
   - `docs/DEVELOPMENT_PLAN.md`
   - the workflow doc relevant to the task
   - the exact model/input contract if model inference is involved
4. Inspect the smallest relevant code/test surface.
5. State the intended change boundary before writing code.

If the code and docs disagree, report the conflict. Do not silently choose one.

## Architecture constraints

Keep these boundaries:

```text
transport/API
    ↓
routing
    ↓
workflow
    ↓
model adapter + geo operators
    ↓
verification
    ↓
evidence/result
```

Rules:

- API routes do not contain scientific logic.
- The language model converts free-form language to typed intents and explains verified results; it does not execute scientific tools.
- Deterministic policy validates feasibility and chooses the workflow after language interpretation.
- Model adapters do not perform routing.
- Geospatial math does not depend on the VLM.
- The VLM does not calculate physical area/distance.
- Workflow code may compose model adapters and geo operators.
- Verification runs before a result is declared successful.
- Every model-specific preprocessing step lives with that adapter and cites its source in comments/docs.

Do not create microservices by default.

The language model is accessed through a stable internal interface. Qwen-family models are first candidates, but no code outside `satquery/language/` may depend on Qwen-specific APIs. A model runner may be isolated only when a real dependency/runtime conflict is demonstrated.

## Input safety and semantics

Never classify modality using band count alone.

Prefer, in order:

1. explicit trusted metadata;
2. band descriptions/tags;
3. a user-provided explicit mapping recorded in provenance;
4. otherwise `UNKNOWN`.

Unknown is a valid state. Do not force it to optical or SAR.

For temporal pairs:

- shape equality is not geospatial alignment;
- verify overlap, CRS transformability, transform/grid, and temporal order;
- for benchmark PNG/JPEG pairs without georeferencing, mark alignment as `pixel_aligned_unverified`.

For SAR:

- do not treat values as ordinary image intensity;
- enforce the exact radiometric/polarization contract of the selected model;
- do not infer units from appearance.

## Model adoption policy

Before adding a checkpoint, record:

- official paper/source;
- official repository/model card;
- exact model/revision/checkpoint;
- license;
- input modalities and bands;
- expected band order;
- radiometric domain;
- image/tile size;
- normalization;
- output semantics;
- known domain limits;
- measured local smoke-test result.

A model is one of:

```text
RESEARCHED
DOWNLOADED
SMOKE_TESTED
QUALIFIED
DEFAULT
REJECTED
```

Never call `RESEARCHED` or `DOWNLOADED` a working model.

## Confidence policy

Do not invent percentages.

Until calibration exists:

- VLM textual answers: `confidence = null`;
- segmentation/change models: probabilities may be exposed as **model scores**, not calibrated system confidence;
- system confidence remains `unavailable` unless a documented calibration procedure has been run.

## Failure policy

Use structured outcomes:

```text
SUCCESS
SUCCESS_WITH_WARNING
REQUEST_INPUT
UNSUPPORTED
ABSTAIN
ERROR
```

Examples:

- one image + “what changed?” → `REQUEST_INPUT`;
- RGB image + NDVI request → `UNSUPPORTED`;
- missing CRS + semantic description → `SUCCESS_WITH_WARNING`;
- missing CRS + hectare measurement → `UNSUPPORTED`;
- unsupported SAR radiometry for flood model → `UNSUPPORTED`;
- model crash → `ERROR`, never substitute fabricated output.

## Testing rules

Every scientific feature needs:

1. unit tests for deterministic logic;
2. contract tests for model inputs/outputs;
3. negative tests for invalid data;
4. one end-to-end golden-path test;
5. one end-to-end refusal/failure test.

Use synthetic rasters for deterministic tests. Do not use synthetic data as evidence of model accuracy.

Never modify a test merely to match incorrect behavior.

## AI coding discipline

Avoid the failure pattern this rebuild is designed to prevent.

Do not:

- rewrite many modules in one step;
- add abstractions “for later”;
- change model, preprocessing, API shape, and UI together;
- patch around a failing model with heuristics without documenting it;
- add placeholder values that look real;
- declare a phase complete from compilation alone.

Prefer:

```text
one vertical slice
→ run it
→ inspect artifact
→ test failure cases
→ freeze contract
→ move to next slice
```

## Dependency discipline

- The core API/geospatial environment should stay small.
- Heavy model dependencies are optional extras/adapters.
- Pin exact versions once a model is qualified.
- Do not casually upgrade Transformers, PyTorch, CUDA, MMEngine/MMCV, TerraTorch, or GDAL.
- If two qualified models require incompatible environments, document the conflict before isolating one into a subprocess/container.

## Security

Treat all uploaded rasters and archives as untrusted.

- limit file size, raster dimensions, bands, decompressed pixels, and processing time;
- block path traversal;
- do not execute arbitrary user-controlled shell commands;
- do not use `trust_remote_code=True` without a reviewed, pinned revision and an explicit decision record;
- no secrets or model weights in Git.

## Completion standard

Before reporting a task complete:

- inspect the final diff;
- run targeted tests;
- run broader affected tests;
- run `git diff --check`;
- verify generated artifacts manually when visual/geospatial output changed;
- state exactly what was verified;
- state what remains unverified;
- never claim a benchmark, checkpoint, or deployment worked unless it actually ran.

Use these labels precisely:

```text
implemented
locally verified
model-smoke-tested
benchmark-evaluated
qualified
not yet validated
```
