# CLAUDE.md

## Project

SATCHETAK is a location-first **Land Intelligence** product for:

- Agriculture Monitoring
- Urban / Land Development Monitoring

Core principle:

> **Monitor land → detect change → quantify it → explain it.**

## Fast prototype path

```text
AOI
→ Copernicus satellite search
→ valid T1/T2
→ NDVI or land-change workflow
→ evidence + area metrics
→ Qwen explanation
→ save monitored location
```

## Architecture

Keep one FastAPI modular monolith and a map-first frontend.

Primary domain objects:

```text
MonitoredLocation
Observation
Analysis
```

## Providers

- Copernicus Data Space: first global provider
- Bhoonidhi: ISRO EO catalogue/data provider
- Planetary Computer: secondary global provider
- Bhuvan: thematic/reference overlays

Do not confuse Bhuvan with the raw EO acquisition role of Bhoonidhi.

## Scientific rules

1. Change requires valid temporal observations.
2. NDVI requires Red + NIR.
3. Physical area requires valid geospatial metadata.
4. Qwen explains structured results; it does not invent them.
5. Exact source acquisition dates remain visible.
6. Cloud/quality failures are explicit.
7. Sentinel-based monitoring is periodic/as-new-observations-arrive, not guaranteed real-time.
8. 10 m imagery is not individual-building surveillance.

## Build order

1. AOI/map
2. Copernicus discovery
3. T1/T2 selection
4. vegetation change
5. evidence UI
6. save monitored location
7. urban/land change
8. Bhoonidhi
9. Planetary Computer/Bhuvan

Do not over-engineer before step 6 works.
