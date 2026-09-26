# Land screening and workspace

The root page is the product landing page. `/#/dashboard` opens the location-first workspace. Both routes work with Vite and the backend static-file server without a server-side routing fallback.

## Supported questions

- “Is this land worth buying for agricultural use?” runs Red/NIR vegetation change and an agricultural purchase screen.
- “Assess this land purchase for commercial development” runs visible/NIR/SWIR change categorization and a development purchase screen.
- “Analyze vegetation condition and change in this field” runs vegetation measurements.
- “Show urban development change and cleared land” screens connected regions as vegetation-to-bare/disturbed, built-up-like, or other surface-change candidates.

Purchase queries return the existing qualified analysis workflow plus `assessment_purpose` (`agriculture_purchase` or `development_purchase`). Pass that field to `POST /api/v1/analyses`. The result includes a persisted `assessment` with measured findings, missing checks, and next steps. A purpose/workflow mismatch returns 422.

The report does not assign a purchase score or a suitability classification. Demo results have `demo_only` status; live results have `insufficient_evidence` for a purchase decision. Soil, water, terrain, climate, title, permissions, and economics are not inferred from satellite signals. These are explicit evidence gaps. This scope follows [FAO land evaluation guidance](https://www.fao.org/4/T0715E/t0715e06.htm).

## Urban/land category screen

Urban analysis uses B02/B03/B04/B08/B11/B12 to calculate NDVI, NDBI, and BSI at both dates. Deterministic rules identify conservative candidate categories, then an eight-connected region pass removes regions below approximately 0.10 ha at 10 m output sampling. The report shows area by category, region count, largest connected region, and a colour-coded overlay on the latest observation.

Up to two quality-qualified intermediate observations are also compared with the same baseline. The report separates area whose category recurs in at least two comparison observations from area that appears only in the latest comparison. It lists every date used and assigns the same temporal status to each connected region. Repetition increases temporal support but does not prove permanence or cause; latest-only change may be real and recent, but needs a later clear observation for confirmation.

`vegetation_to_bare_candidate` means vegetation decreased while bare-soil signals increased. `built_up_like_candidate` means SWIR/NIR signals shifted toward built or hardened surfaces without meeting the clearing rule. `other_surface_change` passed the magnitude and minimum-region rules but not either semantic rule. All three remain screening evidence. B11/B12 are native 20 m bands, so output sampled at 10 m does not provide 10 m SWIR detail.

## Additional agriculture measurements

NDVI P10, median, P90, standard deviation, and decline/increase/within-threshold shares are computed from the same mutually valid pixels as the change analysis. Shares use the configured change thresholds, not crop-specific productivity assumptions. Cloud values shown on observation cards are catalogue scene-level values, not AOI cloud coverage. Demo area remains a bounding-box estimate; live valid overlap is not the total parcel area.

These additions summarize existing Red/NIR data. Soil, weather, irrigation, elevation, multi-season history, and cadastral datasets are not integrated yet. Qwen is not used to manufacture or fill missing evidence; reports use deterministic templates.

## Dated evidence artifacts

Each completed analysis creates three immutable presentation artifacts from the same aligned arrays used by the metrics:

- T1 B04/B03/B02 true-colour visualization;
- T2 B04/B03/B02 true-colour visualization;
- a transparent threshold overlay aligned pixel-for-pixel with T1/T2.

The report shows before, after, and the categorized overlay before the technical index grids, which are collapsed by default. Overlay opacity is adjustable. Artifact descriptors include their dates, dimensions, WGS84 corner coordinates, source mode, legend, and API URL so future evidence layers can use the same contract. Demo artifacts are always marked simulated. Live artifacts are individually contrast-stretched visualizations of the actual Sentinel-2 arrays so both dates remain readable; stretching affects display only, not calculations.

Up to eight largest connected regions receive numbered markers on the latest-image overlay. Selecting a marker shows its category, measured area, relative location in the AOI, and a plain-language explanation. Completed analyses are persisted under their monitored location and can be reopened from Recent locations. Reports support browser print/save-to-PDF and structured JSON export.

For each non-zero category, the buyer summary separates the directly observed surface effect from its decision relevance. For example, vegetation-to-bare affects observed surface/green cover; it may be associated with clearing, harvest, grading, excavation, or seasonal exposure, so the software does not choose one cause without reference or field evidence.

The report begins with an evidence brief instead of a generic paragraph. It directly answers what changed, shows why the evidence supports that answer, explains what it may mean for the decision, states how confidence should be read, exposes what the analysis does not prove, and recommends the next verification. Observation-quality panels explain why T1/T2 were selected and how intermediate dates contributed.

## MapLibre and basemaps

MapLibre GL renders the map. The Satellite toggle uses Esri World Imagery; Streets uses OpenStreetMap. Neither basemap supplies the dated analytical pixels. Basemap acquisition dates and resolution vary by location.

For a different licensed tile service, set these public build-time values in `frontend/.env.local`:

```dotenv
VITE_SATELLITE_TILE_URL=https://your-provider.example/tiles/{z}/{x}/{y}.jpg
VITE_SATELLITE_ATTRIBUTION=Your provider attribution
```

Use only browser-safe tokens with origin restrictions in `VITE_` values. Keep Copernicus client secrets on the backend. Configure a tile subscription appropriate to a commercial deployment and retain the provider attribution; see [Esri attribution guidance](https://support.esri.com/en-us/knowledge-base/what-is-the-correct-way-to-cite-an-arcgis-online-basema-000012040).

The active rectangle appears in an SVG overlay above the map throughout dragging. After release, the committed geometry stays in the MapLibre GeoJSON layer and updates the location form. Basemap switching preserves the AOI.

## Validation

Run `.venv/Scripts/python.exe -m pytest` on Windows, or `.venv/bin/python -m pytest` on Unix. Run `npm run build`, `npm run lint`, and `npm run test:e2e` from `frontend`.

Browser tests use installed Chrome and an isolated backend on port 8001 with a frontend on 5174. Tile responses are deterministic test images. Purchase-report tests exercise the actual demo API; live Copernicus processing requires configured credentials and is not covered by these offline checks.
