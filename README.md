# SatQuery AI

> **Evidence-grounded remote-sensing analysis through natural-language queries, built from qualified pretrained models and deterministic geospatial tools.**

SatQuery AI is a focused remote-sensing assistant for four workflows:

1. **Single-image analysis** — answer questions about one image and localize visible evidence when the selected model supports grounding.
2. **Paired-image change detection** — identify where two aligned observations differ and return a change mask.
3. **Flood analysis** — map flood extent using a flood-specific model when the sensor/input contract is satisfied.
4. **Agricultural change analysis** — detect vegetation/cropland change from compatible multispectral imagery and use a crop model only when its exact input contract is met.

The system intentionally **does not train or fine-tune models in the initial build**. It integrates existing published checkpoints behind strict adapters, validates the input before inference, preserves geospatial metadata, and keeps language generation separate from physical measurement.

Natural-language understanding is handled by a replaceable open generative LLM (Qwen-family models are the first candidates). The LLM converts free-form queries into typed intents and later explains verified evidence; deterministic policy still decides whether a workflow is allowed and physically possible.

## Core principle

> **A language model may interpret a question and explain evidence. It may not manufacture evidence, missing bands, geometry, area, change, or confidence.**

## Why this rebuild exists

The previous implementation grew too quickly across training, multimodal fusion, orchestration, GIS, evaluation, frontend, and deployment. The rebuild reduces the problem to four vertical slices and adds one capability at a time.

The project is complete only when each workflow can independently pass:

- input-contract tests,
- deterministic geospatial tests,
- model smoke tests,
- failure-policy tests,
- end-to-end evidence tests.

## MVP flow

```text
User query + image(s)
        │
        ▼
Input inspection
(sensor / bands / CRS / time / alignment)
        │
        ▼
Language interpreter
(open LLM → typed intent)
        │
        ▼
Feasibility validator
        │
        ▼
Bounded task router
        │
        ├── single-image
        ├── paired change
        ├── flood
        └── agriculture
        │
        ▼
Qualified model adapter
        +
deterministic geospatial operators
        │
        ▼
Verifier
        │
        ▼
Answer + visual evidence + metrics + warnings + provenance
```

## Initial pretrained-model strategy

| Workflow | Initial model/tool strategy | Status |
|---|---|---|
| Language interpretation / explanation | **Qwen-family open instruct model**, size selected by qualification rather than parameter count | Candidate to qualify |
| Single-image VQA / scene reasoning | **EarthDial 4B** family, using the variant whose published input contract matches the image | Candidate to qualify |
| Visual grounding | EarthDial grounding first; **GeoGround** may be evaluated as a specialist if grounding quality is insufficient | Candidate |
| Generic paired change | **Open-CD** adapter; benchmark available pretrained checkpoints before promoting one default | Candidate family |
| SAR flood | **Microsoft AI4G Flood** pretrained Sentinel-1 model | Primary candidate |
| Optical flood fallback | **IBM/NASA Prithvi-EO-2.0 Sen1Floods11** checkpoint for its documented Sentinel-2 band contract | Later candidate |
| Agricultural crop map | **IBM/NASA Prithvi-EO-1.0 multi-temporal crop-classification** checkpoint when its exact HLS 18-band/3-timestamp contract is satisfied | Primary narrow candidate |
| Generic vegetation change | Deterministic spectral-index change + optional change mask; no unsupported crop/yield inference | Core deterministic workflow |

No model becomes a production default merely because it has a strong paper result. It must pass our own compatibility, inference, and failure tests.

## Repository shape

```text
satquery/
├── apps/
│   ├── api/                  # FastAPI transport only
│   └── web/                  # Next.js + geospatial viewer
├── satquery/
│   ├── contracts/            # shared typed schemas
│   ├── ingestion/            # raster inspection and safe loading
│   ├── geo/                  # CRS, alignment, masks, measurements
│   ├── language/             # open LLM interpretation + explanation
│   ├── routing/              # bounded deterministic workflow selection
│   ├── workflows/
│   │   ├── single_image/
│   │   ├── change/
│   │   ├── flood/
│   │   └── agriculture/
│   ├── model_adapters/       # pretrained model wrappers
│   ├── evidence/             # evidence objects and artifact writing
│   └── verification/         # feasibility and result verification
├── models/                   # registry metadata, no weights in Git
├── tests/
├── runtime/                  # local generated artifacts, gitignored
├── docs/
├── AGENTS.md
├── CLAUDE.md
├── CONTRIBUTING.md
├── SECURITY.md
└── README.md
```

## Start here

Read these in order before implementation:

1. [`docs/PROJECT_SCOPE.md`](docs/PROJECT_SCOPE.md)
2. [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
3. [`docs/WORKFLOWS.md`](docs/WORKFLOWS.md)
4. [`docs/LANGUAGE_LAYER.md`](docs/LANGUAGE_LAYER.md)
5. [`docs/MODEL_SELECTION.md`](docs/MODEL_SELECTION.md)
6. [`docs/INPUT_CONTRACTS.md`](docs/INPUT_CONTRACTS.md)
7. [`docs/EVIDENCE_AND_VERIFICATION.md`](docs/EVIDENCE_AND_VERIFICATION.md)
8. [`docs/DEVELOPMENT_PLAN.md`](docs/DEVELOPMENT_PLAN.md)
9. [`AGENTS.md`](AGENTS.md) for AI-assisted coding rules.

## Non-goals for the initial build

- training or fine-tuning foundation models;
- free-form autonomous agents;
- multi-agent swarms;
- arbitrary Python/shell execution from user queries;
- vector databases or RAG without a demonstrated requirement;
- pretending RGB contains NIR/SWIR;
- pretending arbitrary SAR is Sentinel-1 VV/VH;
- estimating physical area without valid georeferencing;
- producing a numeric confidence percentage that has not been calibrated;
- Kubernetes/Kafka/service-mesh infrastructure;
- supporting every satellite sensor.

## Status

This document pack defines the **fresh rebuild specification**. Implementation should start only after the decisions in [`docs/DECISIONS.md`](docs/DECISIONS.md) are accepted.

**SatQuery AI — ask the Earth, verify the answer.**
