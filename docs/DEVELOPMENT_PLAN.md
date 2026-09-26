# Development Plan — Fastest Prototype First

## Phase 0 — Skeleton

Create the modular monolith and map-first frontend shell. No model training.

## Phase 1 — AOI

Implement:

- place/lat-long navigation
- map polygon/rectangle drawing
- optional radius around point
- AOI validation

Exit: user can create an explicit analysis polygon.

## Phase 2 — Copernicus observation discovery

Implement one provider first:

```text
AOI + date range + Sentinel-2 L2A
→ candidate scenes
```

Return acquisition date, cloud metadata, geometry and required assets.

## Phase 3 — T1/T2 selection

Prototype policy:

```text
T2 = latest valid observation
T1 = valid observation closest to requested historical target
```

Filter for AOI coverage, required bands and basic quality/cloud criteria.

## Phase 4 — Agriculture vertical slice

Implement first:

```text
B04 + B08
→ NDVI T1/T2
→ ΔNDVI
→ decline/gain regions
→ area/statistics
→ map overlay
```

This is the first hackathon-ready workflow.

## Phase 5 — Language layer

Use Qwen for typed intent parsing and explanation of the structured result.

## Phase 6 — Save monitored location

Persist:

```text
name
AOI
sector
period
baseline
latest observation
```

No complex scheduler is required yet.

## Phase 7 — Urban / land change

Integrate a qualified Open-CD path or the strongest reliable existing change method.

Output:

- before/after
- generic land-change mask
- polygons
- changed area
- conservative explanation

## Phase 8 — Bhoonidhi

Add the ISRO EO provider behind the same provider interface. Start with one usable collection/product path instead of trying to cover the entire archive.

## Phase 9 — Planetary Computer + Bhuvan

- Planetary Computer as secondary global/open provider
- Bhuvan thematic/reference overlays

## Phase 10 — Monitoring automation

Only after the interactive vertical slice works:

```text
saved location
→ search for newer eligible observation
→ if valid and new: analyze
→ otherwise stop
→ significant change: alert/report
```

## Explicitly defer

- flood/disaster
- microservices
- Kubernetes/Kafka
- billing
- multi-tenancy
- custom model training
- full SAR platform
- mobile application

## Hackathon-ready gate

One real AOI must work with real public satellite data from discovery through measured evidence and natural-language explanation.
