# Implementation Checklist

Use this for every new workflow/model adapter.

## Before coding

- [ ] Current phase permits the work.
- [ ] Official source/paper read.
- [ ] Checkpoint/model revision identified.
- [ ] License/usage terms recorded or explicitly unresolved.
- [ ] Exact input bands/modalities known.
- [ ] Preprocessing known.
- [ ] Output semantics known.
- [ ] Expected hardware known.
- [ ] Failure cases listed.

## Adapter

- [ ] Input contract validator.
- [ ] Lazy model loading.
- [ ] Deterministic preprocessing where possible.
- [ ] Device selection.
- [ ] Inference under `torch.inference_mode()` where appropriate.
- [ ] Output normalized into SatQuery evidence schema.
- [ ] No framework tensor leaks into API schema.
- [ ] Model/version recorded in provenance.

## Geospatial

- [ ] Original dimensions preserved.
- [ ] Resize/tile transform recorded.
- [ ] Mask restored to original coordinate space.
- [ ] NoData/valid mask preserved.
- [ ] CRS/area math unit tested.

## Tests

- [ ] Valid input.
- [ ] Invalid modality.
- [ ] Missing band/polarization.
- [ ] Missing metadata.
- [ ] Empty/degenerate output.
- [ ] Model unavailable.
- [ ] Golden end-to-end case.
- [ ] Refusal/unsupported case.

## Promotion

- [ ] RESEARCHED
- [ ] DOWNLOADED
- [ ] SMOKE_TESTED
- [ ] QUALIFIED
- [ ] DEFAULT only after explicit decision


## Language-layer checklist

- [ ] Intent schema is bounded.
- [ ] Structured output validated by Pydantic/JSON Schema.
- [ ] No arbitrary tool names accepted.
- [ ] One repair retry maximum.
- [ ] Unsupported/ambiguous query produces clarification.
- [ ] Final explanation receives verified evidence only.
- [ ] No scientific confidence invented by the LLM.
- [ ] Language model can be swapped without changing router/workflow code.
