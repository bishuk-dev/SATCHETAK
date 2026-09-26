# UI / UX

## AOI selection

The map is the primary spatial input. Activate **Draw rectangle**, press at one corner, drag to the opposite corner, and release. A coordinate tooltip follows the cursor while it moves over the map. The selected rectangle synchronizes directly with the west/south/east/north fields, and editing those fields updates the rectangle.

## Principle

SATCHETAK is **map-first, monitoring-first**. Chat is an interface to the monitoring product, not the product itself.

## Main screen

```text
┌───────────────────────────────────────────────────────────┐
│ Search place / latitude-longitude                         │
├───────────────────────────────┬───────────────────────────┤
│                               │ Sector                    │
│              MAP              │ Agriculture | Urban/Land  │
│                               │                           │
│          [draw AOI]           │ Period                    │
│                               │ 3M | 6M | 1Y              │
│                               │                           │
│                               │ [Analyze]                 │
├───────────────────────────────┴───────────────────────────┤
│ Observation timeline: T1 --------------------------- T2   │
├───────────────────────────────────────────────────────────┤
│ Before | After | Change / NDVI overlay                    │
├───────────────────────────────────────────────────────────┤
│ Metrics | warnings | provenance | Qwen explanation        │
│ [Monitor this location]                                   │
└───────────────────────────────────────────────────────────┘
```

## User journey

1. Search a place or enter coordinates.
2. Draw AOI.
3. Choose Agriculture or Urban/Land.
4. Choose monitoring period.
5. SATCHETAK searches the catalogue.
6. Show candidate count and rejected-scene reasons when useful.
7. Show exact selected T1/T2 dates.
8. Render before/after + evidence overlay.
9. Show metrics and warnings.
10. Allow natural-language questions about the verified result.
11. Save as a monitored location.

## Wording

Use:

- "periodic satellite monitoring"
- "as new observations become available"
- "latest usable observation"
- "vegetation decline"
- "land change"

Avoid unsupported:

- "real-time satellite monitoring"
- "disease detected"
- "yield loss"
- "illegal construction detected"
- building-level precision from Sentinel-2.
