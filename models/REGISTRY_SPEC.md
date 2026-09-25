# Model Registry Specification

The code implementation should eventually use a machine-readable registry. This document defines the fields before we create the YAML/JSON.

## Example

```yaml
id: microsoft-ai4g-flood
status: QUALIFIED
publisher: Microsoft AI for Good Research Lab
source_url: https://github.com/microsoft/ai4g-flood
paper_url: https://doi.org/10.1038/s41467-025-60973-1
license: PENDING_EXPLICIT_REPO_AUDIT
revision: <pinned commit>
checkpoint:
  path: external
  sha256: <record after acquisition>
capabilities:
  - flood_segmentation
modalities:
  - SAR
sensors:
  - Sentinel-1
temporal_requirement: PRE_POST
required_bands:
  - VV
  - VH
radiometry: <exact qualified profile>
output_type: raster_mask
preprocessing_profile: ai4g_flood_v1
known_limits:
  - permanent water may require post-filtering
  - unqualified on arbitrary SAR sensors
qualified_on:
  - <manifest id>
```

## Rules

- `status` is explicit.
- `revision` cannot be `main` once qualified.
- missing license information is represented as unresolved, not guessed.
- preprocessing profiles are versioned.
- a model cannot be selected by the router unless `status` is `QUALIFIED` or `DEFAULT`.
- checkpoint hashes are recorded after download.
