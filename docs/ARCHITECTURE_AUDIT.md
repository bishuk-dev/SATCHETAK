# Architecture Audit — Current Direction

## Resolved inconsistencies

The documentation is now aligned around one product:

```text
SATCHETAK Land Intelligence
├─ Agriculture Monitoring
└─ Urban / Land Development Monitoring
```

The old flood/disaster branch has been removed from the hackathon MVP.

The primary interaction has changed from image upload to:

```text
location/AOI → observation discovery → analysis → recurring monitoring
```

ISRO integration is split correctly:

```text
Bhoonidhi → EO data discovery/download
Bhuvan    → thematic/reference layers
```

## Remaining implementation risks

- exact Copernicus/Bhoonidhi auth and asset-access contracts must be validated during implementation;
- AOI-specific cloud/valid-pixel screening may need more than catalogue-level cloud percentage;
- generic change models can confuse seasonal/registration differences with real land change;
- Sentinel-2 resolution limits urban claim granularity;
- crop classification requires strict input compatibility.

## Prototype recommendation

Do not solve all risks at once. Prove Agriculture NDVI change end-to-end first, then add Urban/Land change, then additional providers.
