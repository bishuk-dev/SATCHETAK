# Architecture Audit

## Automated consistency scan

No stale legacy naming or old single-flood-path wording was found.

## Manual architecture review
- Language interpretation and scientific validity are separated.
- Deterministic validation precedes routing.
- Flood adapters keep different input contracts and share only a post-inference evidence contract.
- Explicit endpoints prevent silent model switching.
- No optical/SAR mask fusion is implied.
- GIS owns measurements.
- Phase gates keep broken model adapters from being hidden by later router/UI work.

## Remaining implementation risks
- Actual model qualification results remain unknown until checkpoints run locally.
- TerraTorch/PyTorch/GDAL dependency compatibility must be tested in Phase 5; isolation is allowed only if a real conflict appears.
- Thresholds and any calibration must come from validation, not documentation guesses.

**Architecture status:** internally coherent and implementation-ready, subject to phase-gate verification.
