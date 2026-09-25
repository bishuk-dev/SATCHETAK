# Evaluation

## Principle

We are not training models, but we still need to **qualify** them.

A published checkpoint is evidence that a model worked under the authors' evaluation protocol. It is not proof that it works for our inputs.

## Two evaluation layers

### 1. Model qualification

Question:

> Does this pretrained checkpoint work correctly for the workflow and input contract we claim?

### 2. System qualification

Question:

> Does SatQuery preserve geometry, reject invalid requests, and return correctly linked evidence?

## Single-image evaluation

Candidate datasets:

- VRSBench for remote-sensing VQA/grounding;
- small manually curated demo set for product behavior.

Metrics depend on task:

```text
VQA accuracy / accepted benchmark protocol
grounding IoU / Acc@threshold
```

Do not use a large language model as the only evaluator of spatial correctness.

## Change detection evaluation

Use the exact test split associated with the candidate checkpoint when reproducing baseline behavior, then a small cross-source holdout for robustness.

Metrics:

```text
Precision
Recall
F1
IoU
```

System sanity:

- T1/T1 near-zero change;
- image shift rejection or clear warning;
- mask coordinate mapping.

The Open-CD framework provides pretrained inference support and benchmark-compatible checkpoints, making it suitable for adapter-level qualification.

## Flood evaluation

Primary SAR candidate:

Microsoft AI4G Flood.

Evaluation should include:

- official/example data that reproduces the published inference path;
- at least one held-out flood event/source if practical;
- false positives over permanent water;
- nodata/swath-boundary behavior.

Metrics:

```text
flood IoU
precision
recall
F1
```

Do not quote paper/global-map performance as our own result.

## Agriculture evaluation

### Spectral change

Deterministic tests:

- synthetic known Red/NIR rasters with analytically known NDVI;
- nodata handling;
- aligned-pair difference;
- area calculation.

Product sanity:

- season/phenology warning;
- clouds/invalid data exclusion when possible.

### Crop classifier

Use the official model's documented dataset/split or demo first.

Metrics:

```text
mIoU / per-class IoU / accuracy
```

Do not claim crop classification on input that does not match the 18-band/3-timestamp contract.

## Golden cases

Maintain a small `tests/golden/` manifest with:

```text
case_id
workflow
inputs
expected status
expected evidence type
required warning/error
```

Golden cases should test contracts, not exact neural pixels unless a checkpoint/version is frozen.

## Sealed evaluation

Once a model is promoted to `DEFAULT`, create a small sealed set that is not used to tune thresholds.

Do not repeatedly tune after observing sealed results.

## Model promotion gate

`QUALIFIED` requires:

- exact revision pinned;
- preprocessing locked;
- smoke test reproducible;
- at least one positive case;
- at least one negative/unsupported case;
- metrics or qualitative acceptance criteria recorded;
- output mapped back to original coordinate space correctly.

## No fake metrics

Rules:

- no estimated benchmark rows;
- no copied paper result labeled as “SatQuery”;
- no 0.00 for a test that did not run;
- no numeric “confidence” because it looks good in the UI.

Use:

```text
NOT_RUN
UNAVAILABLE
NOT_APPLICABLE
```

where appropriate.
