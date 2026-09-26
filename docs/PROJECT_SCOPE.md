# Project Scope — SATCHETAK Land Intelligence

## Frozen commercial MVP

SATCHETAK is an AI-powered satellite land-monitoring platform for **Agriculture** and **Urban/Land Development**.

It turns recurring Earth-observation data for a user-defined AOI into evidence-grounded change maps, vegetation/land metrics, and natural-language insights.

## Problem

Businesses and organizations own or manage large land assets, but repeated manual inspection and remote-sensing analysis are expensive and specialist-heavy.

SATCHETAK answers:

```text
What changed?
Where?
How much?
Should I inspect it?
```

## Primary product primitive

```text
MonitoredLocation = AOI + purpose + observation policy + history
```

The user selects a location once; imagery is discovered automatically.

## Vertical 1 — Agriculture

In scope:

- NDVI
- NDMI when required bands exist
- vegetation increase/decrease
- temporal trend
- field/anomaly regions
- spatial extent and area
- optional Prithvi crop classification only for compatible inputs

Out of scope unless later validated:

- disease diagnosis
- nutrient deficiency diagnosis
- yield prediction
- causal agronomy claims

## Vertical 2 — Urban / Land Development

In scope:

- generic land change
- large-area built-up/development expansion when supported
- green-cover change
- disturbed/cleared land
- temporal change polygons
- area statistics

Resolution constraint:

Sentinel-2 10 m imagery is appropriate for large-area change, not one-house, wall-level, or parcel-level surveillance.

## Removed from commercial MVP

- flood analysis
- disaster-response workflow
- SAR flood preprocessing
- permanent-water flood filtering
- disaster demo

## Delivery model

SATCHETAK is best framed as **Observation as a Service / monitored-location intelligence**:

```text
register AOI
→ establish baseline
→ discover new valid observation
→ analyze
→ surface meaningful change
→ dashboard / report / alert
```

## Commercial reference

SatSure validates the broader Earth-intelligence market: customers pay for derived decision intelligence, not raw pixels. SATCHETAK's initial wedge is self-service monitored-location intelligence with map-first UX, natural-language queries, visible evidence and provenance.

## MVP success definition

A real user can draw an AOI, select Agriculture or Urban/Land, select a period, automatically obtain valid T1/T2 observations, view before/after evidence and quantified change, ask a natural-language question about the result, and save the site for future monitoring.
