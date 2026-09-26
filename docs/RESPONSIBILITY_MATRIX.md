# Responsibility Matrix

| Responsibility | Provider layer | Workflow/model | GIS | Verifier | Qwen |
|---|---:|---:|---:|---:|---:|
| Find candidate observations | ✅ | | | | |
| Preserve source metadata | ✅ | | | ✅ | |
| Select compatible T1/T2 | ✅ / policy | | | ✅ | |
| NDVI/NDMI | | | ✅ | ✅ | |
| Change mask | | ✅ | optional | ✅ | |
| Area/distance/statistics | | | ✅ | ✅ | |
| Decide whether claim is allowed | | | | ✅ | |
| Interpret user language | | | | policy validates | ✅ |
| Explain verified result | | | | supplies evidence | ✅ |
| Invent missing bands/geometry/metrics | ❌ | ❌ | ❌ | ❌ | ❌ |

The language model is never the source of geospatial truth.
