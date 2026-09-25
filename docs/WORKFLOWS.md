# Workflow Contracts

## Common lifecycle

Every workflow follows:

```text
inspect → validate → prepare → infer → geospatialize → verify → explain → persist
```

No workflow may skip validation because a model can technically accept a tensor.

---

# 1. Single-image workflow

## Intent examples

- “What is visible in this image?”
- “Is a river present?”
- “Where is the largest built-up region?”
- “Describe the scene.”

## Inputs

One image:

- RGB/PAN rendered imagery; or
- a supported multispectral/SAR input whose selected adapter explicitly documents support.

## Primary model direction

EarthDial 4B family is the first candidate because the published system is designed for remote-sensing VQA, captioning, grounding, multisensor and multitemporal understanding.

Use the model variant that matches the input contract. Do not assume the RGB checkpoint understands arbitrary native SAR bands.

## Output

- textual observation;
- optional boxes/regions if returned by a qualified grounding path;
- `confidence = null` until calibrated;
- warnings about unsupported measurements or sensor ambiguity.

## Forbidden

- hectares from image appearance;
- NDVI from RGB;
- claiming a temporal change from one image;
- claiming a class outside the model's demonstrated/qualified scope as certain.

---

# 2. Paired change workflow

## Intent examples

- “What changed between these images?”
- “Highlight changed regions.”
- “Where did built-up area expand?” — only if a semantic post-stage is qualified.

## Inputs

T1 and T2 must be ordered.

Georeferenced pair:

- overlap must be non-empty;
- CRS must be transformable;
- comparison grid must be explicitly defined;
- resampling method must be recorded.

Benchmark pair without georeferencing:

- may run only when pair correspondence is part of the benchmark/input contract;
- result is marked `pixel_aligned_unverified`.

## Model direction

Use an Open-CD adapter.

Initial smoke candidate:

```text
ChangerEx ResNet-18 checkpoint on LEVIR-CD
```

Do not freeze it as the default until compared with at least one alternative checkpoint on our declared evaluation set.

## Output

- binary change probability/logit output;
- thresholded change mask;
- original-resolution/georeferenced mask;
- changed area only if geospatial metadata permits;
- optional VLM explanation grounded in the mask.

## Sanity tests

- `T1 + T1` should produce near-zero change;
- swapping `T1/T2` must not silently alter a symmetric binary-mask claim;
- non-overlapping georeferenced images must reject;
- deliberately shifted images must not be treated as valid change evidence.

---

# 3. Flood workflow

Flood is one workflow with two explicitly different sensor paths.

## Path A — Microsoft AI4G Flood (Sentinel-1 SAR)

Input contract:

```text
pre-event VV
pre-event VH
post-event VV
post-event VH
+ Sentinel-1-compatible RTC/radiometric preprocessing
+ spatial compatibility
```

The official repository states the model was trained on Sentinel-1 RTC data and warns that preprocessing must be compatible. Arbitrary SAR, unknown polarization, and unknown radiometry are out of qualified scope until separately evaluated.

Output:
- flood mask;
- valid-data mask;
- model provenance;
- permanent-water filtering state;
- area only when georeferencing is valid.

The official repository warns about permanent-water false positives and recommends post-filtering. SATCHETAK must record whether that filter was applied.

## Path B — IBM/NASA Prithvi flood (Sentinel-2 optical)

Model:

`ibm-nasa-geospatial/Prithvi-EO-2.0-300M-TL-Sen1Floods11`

The official model card describes a Sentinel-2 flood-segmentation checkpoint fine-tuned on Sen1Floods11.

Required bands, in model order:

```text
Blue
Green
Red
Narrow NIR
SWIR1
SWIR2
```

Classes:

```text
0  = no water
1  = water/flood
-1 = no data/cloud
```

RGB-only imagery is unsupported. Missing NIR/SWIR must not be synthesized.

## Shared flood evidence

Both adapters normalize output to:

```text
FloodEvidence
  source_model
  source_modality
  flood_mask
  valid_mask
  cloud_or_nodata_mask (optional)
  permanent_water_filter_state
  model_scores (optional)
  warnings
  provenance
```

The shared contract begins after inference. Inputs stay model-specific.

## Explicit evaluation endpoints

```text
POST /api/v1/flood/ai4g
POST /api/v1/flood/prithvi
```

These endpoints never silently switch models.

## Unified product endpoint

After both adapters independently qualify:

```text
POST /api/v1/flood
```

Policy:

```text
valid Sentinel-1 SAR pre/post  → AI4G eligible
valid Sentinel-2 six-band      → Prithvi eligible
both available                 → explicit policy/comparison mode
neither compatible             → UNSUPPORTED
```

## Retirement policy

Do not remove the second adapter from one aggregate benchmark score. Retire it only if the remaining path adequately covers the same operational input domain, product scope drops that domain, or maintenance/license/runtime constraints justify removal.

---

# 4. Agricultural change workflow

## Goal

Report **observable vegetation/cropland changes** without pretending to infer unsupported agronomy.

## Level A: spectral-change workflow

Requirements:

- Red and NIR bands with known semantics for NDVI;
- aligned T1/T2;
- cloud/invalid pixels masked when metadata/quality bands are available.

Compute:

```text
NDVI = (NIR - Red) / (NIR + Red)
ΔNDVI = NDVI(T2) - NDVI(T1)
```

Do not interpret every negative ΔNDVI as crop damage. Possible causes include phenology, harvest, clouds, soil moisture, different acquisition conditions, or land-cover change.

Output language must reflect this:

Good:

> “Vegetation-index values decreased in the highlighted region between the two observations.”

Bad:

> “The crops were damaged by disease.”

## Level B: crop classification workflow

Model:

`ibm-nasa-geospatial/Prithvi-EO-1.0-100M-multi-temporal-crop-classification`

Use only when the documented input is met:

```text
GeoTIFF
3 timestamps
6 channels each:
Blue, Green, Red, Narrow NIR, SWIR1, SWIR2
18 bands in documented order
```

Output:

- crop/land class map;
- per-class map difference;
- area-change statistics where georeferencing supports measurement.

Do not convert the model into a general “agriculture model” for arbitrary imagery.

---

# Language interpretation and router rules

Free-form user language is first converted by the language model into a strict typed intent. The scientific feasibility validator then checks the uploaded data. Routing after that point is deterministic.

The LLM may propose only the bounded intent vocabulary and parameters defined in `LANGUAGE_LAYER.md`.

Routing should be deterministic from validated intent + input inventory.

Examples:

| Query / input | Workflow |
|---|---|
| 1 image, “describe this” | single-image |
| 1 image, “what changed?” | request second input |
| 2 images, generic “what changed?” | change |
| pre/post Sentinel-1 VV/VH, flood query | flood |
| T1/T2 with known Red+NIR, vegetation query | agriculture Level A |
| valid 18-band 3-timestamp HLS crop stack | agriculture Level B |

A generic LLM may assist intent classification only inside these bounded labels. It must not create new workflow names or tool calls.
