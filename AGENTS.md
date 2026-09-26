# AGENTS.md

Repository-wide instructions for AI coding agents working on SATCHETAK.

## Mission

Build the fastest credible **location-first land-intelligence prototype** for two verticals only:

```text
Agriculture Monitoring
Urban / Land Development Monitoring
```

Do not reintroduce flood/disaster workflows into the hackathon MVP.

## Product invariant

The normal user journey is:

```text
MonitoredLocation / AOI
→ observation discovery
→ quality filtering
→ T1/T2 selection
→ analysis
→ GIS measurement
→ evidence
→ Qwen explanation
```

Manual image upload is secondary.

## Prime scientific rule

> A language model may interpret a request and explain verified evidence. It may not manufacture evidence, geometry, dates, bands, masks, measurements, or confidence.

## Prototype priority

Prefer:

```text
working vertical slice
> simple maintainable architecture
> extra providers
> production infrastructure
```

Never sacrifice scientific validity for speed.

## Provider order

Implement in this order:

1. Copernicus Data Space
2. Bhoonidhi
3. Planetary Computer
4. Bhuvan thematic overlays

Correct ISRO mental model:

```text
Bhoonidhi → EO discovery/download
Bhuvan    → thematic/reference layers
```

## First end-to-end workflow

Agriculture should be the first polished demo:

```text
Sentinel-2 L2A
→ Red + NIR
→ NDVI T1 / T2
→ ΔNDVI
→ change mask / polygons
→ area + statistics
→ map evidence
→ Qwen explanation
```

Then add urban/land change using the strongest qualified change workflow.

## Claim discipline

Allowed examples:

- vegetation decline/increase;
- anomalous field regions;
- land-cover change;
- green-cover loss;
- large-area development expansion;
- changed area.

Do not claim without validated evidence:

- disease;
- nutrient deficiency;
- yield loss;
- exact construction type;
- individual-house appearance;
- parcel-level encroachment from 10 m imagery.

## No-training rule

Initial prototype uses pretrained models and deterministic geospatial tools. Do not add training, LoRA, PEFT, or dataset pipelines unless explicitly approved.

## Simplicity rules

Use a modular monolith. Prefer SQLite/filesystem for prototype persistence. Do not introduce Postgres/PostGIS, Redis, S3, Kafka, Kubernetes, microservices, or multi-agent systems before the main vertical slice works.

## Completion definition

A capability is complete only when it is reachable from the location-first product flow and its evidence can be inspected in the UI.
