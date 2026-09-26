# Architecture Invariants

1. Product input is an explicit AOI/MonitoredLocation.
2. Manual image upload is secondary.
3. Provider-specific networking stays outside analytics.
4. Bhoonidhi and Bhuvan have different roles: EO acquisition vs thematic/reference layers.
5. Exact observation dates and provenance survive to the UI.
6. Temporal change requires valid T1/T2.
7. Missing spectral bands are never fabricated.
8. Physical measurements are deterministic GIS outputs.
9. Qwen interprets/explains but cannot create evidence.
10. Agriculture claims remain conservative unless dedicated models/ground truth justify stronger inference.
11. Urban claims remain resolution-aware.
12. Flood/disaster is not part of the current commercial MVP.
13. One modular monolith is the default deployment shape.
14. No training/fine-tuning before a pretrained workflow proves insufficient.
