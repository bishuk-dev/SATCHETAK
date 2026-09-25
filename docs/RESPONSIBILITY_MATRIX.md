# Intelligence Responsibility Matrix

This document prevents capability leakage between model types.

| Responsibility | Component | May infer? | May measure? |
|---|---|---:|---:|
| Understand user's wording | Open text LLM (Qwen-family candidate) | Yes, linguistic intent | No |
| Decide workflow feasibility | Deterministic validator | No | No |
| Select workflow | Deterministic router | No | No |
| Describe/ground one EO image | EarthDial / grounding specialist | Yes, visual semantics | No physical measurement |
| Detect generic T1/T2 change | Open-CD specialist | Yes, change mask | No physical area by itself |
| Detect SAR flood | Microsoft AI4G Flood | Yes, flood mask | No physical area by itself |
| Detect optical flood | IBM/NASA Prithvi Sen1Floods11 | Yes, water/flood + cloud/nodata mask | No physical area by itself |
| Compute NDVI / ΔNDVI | GIS/spectral operator | Deterministic | Yes |
| Crop-map inference | Qualified Prithvi crop model | Yes, within contract | No physical area by itself |
| Area / distance / counts | GIS operator | No | Yes |
| Verify physical/geometric validity | Verifier | Rule/contract based | Checks only |
| Explain final result | Open text LLM | Linguistic summary only | No |

## Rule

> The component that is best at language is not automatically the component that is trusted for science.

This matrix is normative for the MVP.
