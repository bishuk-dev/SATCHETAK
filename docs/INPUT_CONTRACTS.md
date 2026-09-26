# Input Contracts

## Primary input

SATCHETAK starts from an **Area of Interest (AOI)** plus a monitoring intent/period.

A latitude/longitude is only a map location. Spatial analysis requires an explicit polygon/rectangle/radius-derived AOI.

## Observation requirements

Every selected observation must preserve:

- provider and product ID
- acquisition time
- satellite/sensor
- spatial footprint
- CRS/transform/GSD when available
- bands/polarizations
- quality/cloud metadata
- asset references

## Vegetation change

Requires:

- two temporal observations
- adequate AOI overlap
- Red and NIR bands
- compatible spatial support
- valid pixels in the AOI

## NDMI

Requires compatible NIR + SWIR bands.

## Land change

Requires:

- T1/T2
- temporal order
- sufficient overlap
- compatible/aligned imagery for the chosen model/workflow

## Crop classification

Use only when the full documented model contract is satisfied. Never fabricate missing bands or timestamps.

## Manual upload

Secondary expert path only. Uploaded imagery must still satisfy the same metadata and workflow-specific validity rules.
