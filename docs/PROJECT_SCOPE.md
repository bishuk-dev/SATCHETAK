# Project Scope

## Product definition

SatQuery AI is an evidence-grounded interface over pretrained remote-sensing models and deterministic GIS operations.

The MVP is deliberately small.

## Supported workflows

### 1. Single-image analysis

Input:

```text
one compatible image
+
natural-language question
```

Outputs may include:

- scene answer;
- object/region description;
- bounding box or mask when the selected grounded model supports it;
- metadata warnings;
- provenance.

This workflow is qualitative unless a separate deterministic geospatial operation supplies a quantitative result.

### 2. Paired-image change detection

Input:

```text
T1 + T2
```

Required:

- spatial compatibility;
- known or user-confirmed temporal order;
- a model-compatible visual representation.

Output:

- binary change mask;
- changed-area geometry when georeferencing permits;
- optional text explanation grounded in the mask.

Initial scope is **change / no-change**, not universal semantic change classification.

### 3. Flood analysis

Primary MVP path:

```text
Sentinel-1 compatible pre-event VV/VH
+
Sentinel-1 compatible post-event VV/VH
→ flood mask
```

The first candidate is the Microsoft AI4G Flood model, whose official implementation expects Sentinel-1 RTC-style inputs and documents preprocessing constraints.

Optional later optical path:

```text
compatible Sentinel-2 six-band input
→ Prithvi Sen1Floods11 flood segmentation
```

Do not route arbitrary SAR or RGB into either model.

### 4. Agricultural change analysis

This workflow has two levels.

**Level A — broadly useful deterministic vegetation change**

When Red and NIR semantics are known:

```text
NDVI(T1)
NDVI(T2)
ΔNDVI
```

Additional indices are allowed only when their required bands exist.

Outputs:

- vegetation-index rasters;
- thresholded change regions when a threshold policy is explicitly defined;
- area/statistics from GIS tools.

**Level B — narrow crop classification**

Use the official IBM/NASA Prithvi multi-temporal crop-classification checkpoint only when the documented input is satisfied:

```text
3 timestamps × 6 HLS-style bands
Blue, Green, Red, Narrow NIR, SWIR1, SWIR2
= 18-band GeoTIFF contract
```

A crop-map difference may then support an agricultural change statement.

## Non-goals

Initial SatQuery will not:

- train/fine-tune any model;
- predict crop yield;
- diagnose crop disease from arbitrary imagery;
- infer soil chemistry;
- estimate damage cost;
- perform generic object detection for every possible class;
- support every satellite;
- align unrelated scenes automatically with an opaque learned registrar;
- generate numeric confidence without calibration;
- execute arbitrary LLM-selected code.

## Success definition

The MVP succeeds when all four workflows:

1. reject incompatible inputs correctly;
2. run one qualified pretrained implementation;
3. preserve original geospatial context;
4. return spatial evidence;
5. produce deterministic measurements only when metadata supports them;
6. expose model/version/preprocessing provenance;
7. pass at least one golden success case and one negative/refusal case.

## Design priority

```text
correctness
> traceability
> robustness
> usability
> latency
> feature count
```

Latency matters, but never by silently weakening preprocessing or verification.
