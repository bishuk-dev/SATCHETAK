# Supported Workflows

SATCHETAK exposes one shared monitoring pipeline with two domain-specific analysis branches.

## Shared workflow

```text
AOI
→ observation requirements
→ provider search
→ quality/cloud filter
→ T1/T2 selection
→ preprocessing/alignment
→ analysis
→ GIS metrics
→ verification
→ evidence
→ language explanation
```

## Agriculture workflow

### Vegetation change — P0

Input:

- AOI
- requested period
- compatible multispectral observations
- Red + NIR bands

Processing:

```text
NDVI_T1
NDVI_T2
ΔNDVI
threshold/statistical comparison
change regions
area/statistics
```

Outputs:

- T1/T2 imagery
- T1/T2 NDVI
- delta map
- vegetation-decline/increase regions
- area/statistics
- warnings/provenance

### NDMI — P1

Only when NIR + SWIR requirements are satisfied.

### Crop classification — optional

Use the qualified Prithvi crop checkpoint only when its exact temporal/band contract is available. No synthetic band substitution.

## Urban / land-development workflow

### Generic land change — P0/P1

Input:

- AOI
- aligned temporal observations

Processing:

```text
T1/T2
→ qualified change detector or deterministic comparison
→ change mask
→ polygonization
→ changed area
```

Outputs:

- before/after view
- change mask
- changed polygons
- area statistics
- land-cover/green-cover context where supported

Use conservative language: a generic change mask is not automatically "new construction".

## Single-observation semantic questions

An RS-VLM may answer bounded descriptive questions about a selected observation, but it is not the source of physical measurements or temporal-change claims.

## Explicitly unsupported in MVP

- flood/disaster workflow
- real-time emergency monitoring
- arbitrary sensor fusion
- disease/yield diagnosis
- building-level surveillance from Sentinel-2
