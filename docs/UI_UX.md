# UI / UX Specification

## Product principle

The viewer is the product. Chat text is secondary.

A user should be able to answer:

1. What input did SATCHETAK use?
2. What region is the answer about?
3. What changed/detected?
4. How was the number computed?
5. What limitations/warnings apply?

without opening developer logs.

## Main layout

Desktop:

```text
┌───────────────────────────────────────────────────────────┐
│ project / input status / workflow                         │
├──────────────┬─────────────────────────────┬──────────────┤
│ Inputs       │ Map / image viewer          │ Answer       │
│ metadata     │ overlays                    │ evidence     │
│ bands/time   │ before/after controls       │ metrics      │
│ warnings     │                             │ provenance   │
└──────────────┴─────────────────────────────┴──────────────┘
│ Query bar                                                 │
└───────────────────────────────────────────────────────────┘
```

## Single image

Display:

- image;
- box/mask overlays;
- toggle overlay visibility;
- answer;
- input metadata summary.

## Change

Must have:

- side-by-side or swipe T1/T2;
- change-mask toggle;
- opacity slider;
- changed-area metric when valid.

## Flood

Must show:

- pre/post SAR visualization or derived view;
- flood mask;
- permanent-water-filter status;
- valid/nodata areas;
- area metric.

Do not color nodata as “not flooded”.

## Agriculture

Display:

- T1/T2 optical composite;
- NDVI T1;
- NDVI T2;
- ΔNDVI;
- crop class maps only when crop workflow is valid.

Use neutral wording such as “vegetation decrease” unless the model/data supports a stronger agricultural interpretation.

## Warning design

Warnings are not hidden in tooltips.

Examples:

```text
CRS unavailable — physical area is disabled.
Input SAR radiometry does not match the qualified flood model.
Crop classifier not used — input is not an HLS 3-timestamp stack.
```

## Confidence

Do not show a circular “AI confidence 94%” meter until system confidence is calibrated.

Allowed initially:

- model score distribution;
- warning badges;
- evidence availability;
- outcome status.

## Trace

User-facing trace should be concise:

```text
Input inspected
→ paired as Sentinel-1 pre/post
→ AI4G flood model
→ permanent-water filter: not applied
→ mask polygonized
→ area computed in EPSG:xxxx
```

No internal chain-of-thought.
