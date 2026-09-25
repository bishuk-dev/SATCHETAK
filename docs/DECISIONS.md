# Architectural Decision Log

This file records decisions that should not be silently reversed.

## ADR-001 — Rebuild from a narrow MVP

**Status:** Accepted

**Decision:** The fresh implementation supports only single-image analysis, paired change, flood, and agriculture change.

**Reason:** The prior codebase attempted too many interacting systems before individual workflows were independently reliable.

---

## ADR-002 — No model training in the initial rebuild

**Status:** Accepted

**Decision:** Use existing pretrained checkpoints. No LoRA, PEFT, fine-tuning, or custom foundation-model training.

**Reason:** The project goal is integration, evidence, sensor validity, and product reliability. Training adds large scientific/debugging risk and is unnecessary for an MVP when suitable published models exist.

**Revisit when:** A required capability cannot meet evaluation targets with available checkpoints and the team can justify/execute adaptation scientifically.

---

## ADR-003 — Modular monolith first

**Status:** Accepted

**Decision:** One FastAPI application with modular packages. No service mesh/microservice split by default.

**Reason:** Minimal operational complexity and easier debugging.

**Exception:** Isolate one model runner if dependency/runtime conflicts are proven.

---

## ADR-004 — Specialist models produce evidence

**Status:** Accepted

**Decision:** VLM is not the universal analysis engine. Change/flood/crop masks come from specialist workflows.

**Reason:** Spatial evidence is more auditable and task-specific.

---

## ADR-005 — EarthDial as first single-image VLM candidate

**Status:** Accepted as candidate, not yet DEFAULT

**Reason:** CVPR 2025 remote-sensing-specific VLM with published support for multiple EO modalities/tasks and available 4B checkpoints.

**Risk:** dependency stack and exact modality-specific input behavior must be verified locally.

---

## ADR-006 — Open-CD as change-detection integration surface

**Status:** Accepted as candidate framework

**Reason:** Apache-2.0 toolbox, pretrained checkpoints, direct inference API, multiple published models.

**Checkpoint:** not frozen until qualification comparison.

---

## ADR-007 — Microsoft AI4G Flood for primary SAR flood workflow

**Status:** Accepted as primary candidate

**Reason:** official pretrained artifact, official inference code, and associated peer-reviewed Nature Communications publication.

**Restriction:** only model-compatible Sentinel-1 preprocessing/polarizations are qualified.

---

## ADR-008 — Agriculture is conservative

**Status:** Accepted

**Decision:** Generic agricultural change begins with spectral-index change. Crop classification is enabled only for the official Prithvi checkpoint's exact HLS multi-temporal input.

**Reason:** Avoid unsupported claims about crop type, health, yield, or disease.

---

## ADR-009 — No fake numeric confidence

**Status:** Accepted

**Decision:** `confidence = null` until calibration exists. Model probabilities may be exposed as model scores.

---

## ADR-010 — Geospatial metadata is first-class

**Status:** Accepted

**Decision:** CRS, transform, bounds, time, bands, radiometry and NoData are carried through the entire workflow.

---

## ADR-011 — Measurements are deterministic

**Status:** Accepted

**Decision:** Area/distance/count comes from masks/geometry + geospatial metadata, never LLM generation.

---

## ADR-012 — Model qualification precedes routing

**Status:** Accepted

**Decision:** The router may only select models/workflows marked `QUALIFIED` for the detected input contract.

---

## ADR-013 — Storage remains filesystem-based initially

**Status:** Accepted

**Decision:** Persist analysis manifests/artifacts under a runtime directory.

**Reason:** Database infrastructure is unnecessary until concurrency/history/auth demands it.

---

## ADR-014 — Preserve the legacy attempt

**Status:** Accepted

**Decision:** Do not delete or overwrite the prior project history. Treat it as read-only reference/evidence while the new implementation starts clean.

See `REBUILD_PLAN.md`.

---

## ADR-015 — Open generative LLM for the language layer

**Status:** Accepted

**Decision:** Use a replaceable open instruction-tuned generative LLM for query interpretation and final explanation. Qwen-family models are the first candidates to evaluate.

**Reason:** SATCHETAK requires flexible natural-language understanding, paraphrase handling, structured parameter extraction, clarification, and concise explanation. A general open instruct model is sufficient for these language tasks and avoids creating separate intent/NER/summarization models.

**Constraint:** The language model does not decide scientific feasibility and does not execute tools. It returns typed intents. Deterministic policy validates the request and selects only registered workflows.

**Sizing rule:** Choose the smallest model that passes the language evaluation suite; do not select by parameter count alone.

---

## ADR-016 — Language intelligence and remote-sensing intelligence are separate

**Status:** Accepted

**Decision:** Qwen-like text LLMs handle language. EarthDial/specialist models handle perception. GIS handles measurement. The verifier handles validity.

**Reason:** This prevents a fluent text model from becoming the source of physical or spatial truth.


---

## ADR-017 — Dual flood adapters during qualification

**Status:** Accepted

Use Microsoft AI4G Flood for qualified Sentinel-1 pre/post VV/VH SAR and IBM/NASA Prithvi-EO-2.0-300M-TL-Sen1Floods11 for qualified Sentinel-2 six-band optical imagery.

They share a post-inference `FloodEvidence` schema, not a common input tensor.

---

## ADR-018 — Explicit flood endpoints before unified routing

**Status:** Accepted

Qualification endpoints:

```text
POST /api/v1/flood/ai4g
POST /api/v1/flood/prithvi
```

Unified `/api/v1/flood` is added only after both adapters independently qualify.

---

## ADR-019 — No automatic flood-mask fusion in MVP

**Status:** Accepted

If both masks exist, comparison is allowed. Union/intersection/weighted fusion requires separate research and evaluation.

---

## ADR-020 — Flood retirement requires domain coverage

**Status:** Accepted

A higher aggregate metric alone does not justify deleting the second adapter. Removal requires evidence that the remaining path covers the removed adapter's operating domain, or an explicit scope/maintenance decision.
