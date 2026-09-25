# Input and Data Contracts

The most important SATCHETAK rule is that **a tensor is not enough**. The system needs the physical meaning of its channels and spatial context.

## Raster inventory

For every uploaded raster, record when available:

```text
file ID/hash
driver
width / height
band count
dtype per band
NoData
CRS
affine transform
bounds
pixel size / GSD
band descriptions
color interpretation
sensor/platform
acquisition time
product level
radiometric domain
polarization
```

Do not fill absent fields with guessed values.

## Supported file types

MVP:

```text
GeoTIFF / TIFF
PNG
JPEG
```

PNG/JPEG do not carry sufficient geospatial metadata for physical measurements unless sidecar metadata is explicitly provided.

## Modality classification

Allowed states:

```text
RGB_OR_PAN
MULTISPECTRAL
SAR
UNKNOWN
```

Classification signals, in order:

1. explicit metadata;
2. band descriptions/tags;
3. color interpretation for RGB;
4. explicit user mapping;
5. otherwise UNKNOWN.

Never use only:

```text
1 band = SAR
3 bands = RGB satellite
```

Those assumptions are false in general.

## Band semantics

Use canonical roles internally:

```text
BLUE
GREEN
RED
RED_EDGE_1
RED_EDGE_2
RED_EDGE_3
NIR
NIR_NARROW
SWIR_1
SWIR_2
VV
VH
HH
HV
UNKNOWN
```

A source-specific mapper translates dataset/sensor names to canonical roles.

No spectral index is allowed unless all required roles are present.

## Pair compatibility

For T1/T2:

1. validate temporal order;
2. compute spatial overlap;
3. transform both bounds into a common CRS for comparison;
4. decide a target grid;
5. reproject/resample explicitly if required;
6. record resampling method;
7. create a joint valid-data mask.

### Resampling

Continuous reflectance/intensity:
- bilinear/cubic may be appropriate depending on model contract.

Categorical masks:
- nearest neighbor.

Do not use bilinear interpolation on class labels.

## Pixel-only benchmark pairs

Some public change-detection benchmarks use PNG/JPEG pairs already prepared for pixel correspondence.

Represent this explicitly:

```text
alignment_status = pixel_aligned_unverified
```

Do not fabricate CRS or physical area.

## EarthDial

RGB checkpoint:
- use the exact image preprocessing from the official implementation;
- a visualization composite is not equivalent to native multispectral analysis.

MS/SAR paths:
- accept only channel arrangements documented/verified for that checkpoint;
- record any conversion into a model-specific tensor.

## Open-CD change models

The chosen checkpoint defines:

- expected channel count;
- input size/tiling;
- normalization;
- color order;
- output threshold/logit interpretation.

Adapter owns all of these.

## AI4G Flood

Primary local pair contract:

```text
pre VV
pre VH
post VV
post VH
```

The official repository warns that preprocessing must be compatible with the training/inference pipeline. For ASF-derived imagery it documents RTC Gamma processing, gamma0 radiometry/power scaling, and recommends DEM matching and speckle filtering.

SATCHETAK must reject:

- unknown polarization;
- unknown radiometric domain;
- raw unsupported product;
- non-overlapping pair;
- missing pre/post image.

## Prithvi optical flood

Use only the model card's six-band input semantics.

Do not synthesize missing SWIR/NIR from RGB.

## Prithvi crop classification

Exact MVP contract:

```text
18 bands total
3 timestamps
for each timestamp:
  Blue
  Green
  Red
  Narrow NIR
  SWIR1
  SWIR2
```

Wrong order is an error.

## Agricultural index contract

NDVI:

```text
requires RED + NIR
```

NDMI:

```text
requires NIR + SWIR1
```

Other indices must declare required roles before implementation.

## Measurements

Area requires valid geospatial geometry.

For projected rasters in metric CRS, compute directly.

For geographic CRS (degrees), reproject mask geometry to an appropriate equal-area/local metric CRS before reporting physical area.

Never multiply degree-sized pixels and label the result square metres.
