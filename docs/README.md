# Documentation Index

This documentation is intentionally split by responsibility so that implementation decisions do not become buried inside a giant README.

| Document | Purpose |
|---|---|
| `PROJECT_SCOPE.md` | exact MVP, non-goals, success definition |
| `ARCHITECTURE.md` | component boundaries and end-to-end data flow |
| `WORKFLOWS.md` | contracts for single-image, change, flood, agriculture |
| `LANGUAGE_LAYER.md` | natural-language interpreter/explainer architecture and Qwen policy |
| `MODEL_SELECTION.md` | pretrained-model choices, qualification policy, licenses |
| `INPUT_CONTRACTS.md` | raster/sensor/band/pair requirements |
| `EVIDENCE_AND_VERIFICATION.md` | output schema, claims, masks, measurements, failure policy |
| `EVALUATION.md` | how models and workflows are evaluated without training |
| `DEVELOPMENT_PLAN.md` | phase order and hard exit gates |
| `API_CONTRACT.md` | public backend contract |
| `UI_UX.md` | minimum evidence-first product interface |
| `DECISIONS.md` | architectural decision log |
| `RESPONSIBILITY_MATRIX.md` | which component is allowed to infer/measure/explain what |
| `REBUILD_PLAN.md` | how to preserve the old attempt while starting clean |
| `RESEARCH_REFERENCES.md` | primary sources supporting major decisions |

The source of truth for current implementation phase is `DEVELOPMENT_PLAN.md`.

The source of truth for frozen architectural choices is `DECISIONS.md`.
