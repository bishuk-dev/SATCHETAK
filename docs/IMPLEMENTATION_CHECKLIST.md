# Implementation Checklist

## P0

- [x] Map/lat-long navigation (place-name geocoding remains optional)
- [x] AOI rectangle creation and polygon validation
- [x] Copernicus Sentinel-2 search
- [x] candidate quality filtering
- [x] automatic baseline/latest selection plus intermediate temporal support
- [x] required-band acquisition
- [x] NDVI T1/T2
- [x] ΔNDVI/change regions
- [x] area/statistics
- [x] before/after/evidence UI
- [ ] Qwen structured explanation
- [x] save MonitoredLocation and analysis history

## P1

- [x] deterministic six-band generic urban/land change with temporal support
- [ ] Open-CD qualification
- [ ] Bhoonidhi provider
- [ ] Planetary Computer fallback
- [ ] Bhuvan thematic overlays
- [ ] recurring new-observation check

## Guardrails

- [x] no flood/disaster branch in MVP
- [x] no fake real-time wording
- [x] no unsupported disease/yield/construction claims
- [x] exact dates/provider/sensor visible
- [x] no LLM-generated measurements

Unchecked provider/model items are deliberate post-vertical-slice integrations, not hidden capabilities. The usable product path currently ends in deterministic, evidence-grounded language; Qwen may later paraphrase the same verified contract but must never create measurements.
