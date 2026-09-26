# Architectural Decision Log

## ADR-001 — Focus on Land Intelligence

**Accepted.** Commercial MVP supports Agriculture Monitoring and Urban/Land Development Monitoring only.

## ADR-002 — Remove flood/disaster from hackathon MVP

**Accepted.** Disaster workflows create a weaker recurring commercial story and introduce latency/SAR complexity. They are not part of the current implementation scope.

## ADR-003 — Location/AOI-first product

**Accepted.** The normal user journey begins with a monitored location/AOI, not image upload.

## ADR-004 — Observation as a Service

**Accepted.** The core entity is `MonitoredLocation`; new suitable observations update its history and analyses.

## ADR-005 — Provider abstraction

**Accepted.** Analytics do not depend directly on a specific imagery portal.

## ADR-006 — Provider priority

**Accepted.** Copernicus first, Bhoonidhi second, Planetary Computer third; Bhuvan supplies thematic/reference layers.

## ADR-007 — No training initially

**Accepted.** Use qualified pretrained models plus deterministic GIS/spectral analysis.

## ADR-008 — Qwen is language only

**Accepted.** It interprets and explains; it does not manufacture evidence or measurements.

## ADR-009 — Agriculture first demo

**Accepted.** NDVI/vegetation change is the first polished end-to-end vertical slice.

## ADR-010 — Urban claims remain resolution-aware

**Accepted.** Sentinel-2 supports large-area land/development monitoring, not individual-building or parcel-level surveillance.

## ADR-011 — Modular monolith

**Accepted.** One FastAPI app; no microservices by default.

## ADR-012 — Prototype storage stays simple

**Accepted.** Filesystem and SQLite are sufficient until concurrency/history requirements prove otherwise.

## ADR-013 — SatSure is a market reference, not a blueprint

**Accepted.** Learn the outcome/decision-intelligence framing; differentiate with self-service monitored locations, natural-language exploration and visible evidence.
