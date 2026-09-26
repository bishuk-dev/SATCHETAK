# SATCHETAK

> **AI-powered land intelligence for agriculture and urban/land development.**

## Run the working prototype

The prototype uses a FastAPI/Pydantic backend, React/TypeScript/Vite frontend, MapLibre map, and SQLite persistence.

For complete provider credentials, Ollama/Qwen, Bhuvan, monitoring, pricing, TLS, and verification instructions, see [Complete setup guide](docs/SETUP_GUIDE.md).

Configure backend integrations once instead of entering variables in every PowerShell session:

```powershell
Copy-Item .env.example .env
notepad .env
```

The backend automatically loads the root `.env`; it is Git-ignored and process-level environment variables override it. Keep `VITE_` browser settings in `frontend/.env.local`.

The primary UI is query-first: define an AOI and ask an observation, vegetation-change, or generic land-change question. The backend returns an inspectable typed plan before searching or analyzing imagery. Ambiguous requests fall back to catalogue discovery instead of manufacturing an analysis intent.

```powershell
# Terminal 1 — backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m satchetak.app

# Terminal 2 — frontend
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. FastAPI documentation is available at `http://127.0.0.1:8000/api/docs`.

The default demo runs the full location → observation selection → NDVI T1/T2 → delta → area/statistics → inspectable evidence flow using deterministic simulated spectral grids. Every simulated field is visibly labelled. Analysis reports show dated T1/T2 true-colour artifacts followed by an exactly aligned threshold overlay; the contextual workspace basemap is kept visually and semantically separate.

For real Sentinel-2 L2A pixel processing, create an OAuth client in the Copernicus Data Space Sentinel Hub dashboard and set its credentials only in the backend process:

```powershell
$env:CDSE_CLIENT_ID = "your-client-id"
$env:CDSE_CLIENT_SECRET = "your-client-secret"
.\.venv\Scripts\python.exe -m satchetak.app
```

Never put the client secret in frontend code or commit it to the repository. Live agriculture analysis requests B02/B03/B04/B08; urban/land analysis additionally requests B11/B12 SWIR plus scene/data masks. The backend computes NDVI, NDBI, and BSI changes, removes undersized isolated regions, categorizes conservative vegetation-to-bare, built-up-like, and other change candidates, and measures them in a local UTM CRS. B04/B03/B02 are rendered as readable true-colour evidence artifacts from the same aligned arrays used by the calculation.

Urban reports use up to two quality-qualified intermediate scenes in addition to the baseline and latest scene. They separate change categories repeated across comparison dates from latest-only candidates, list the exact dates used, and explain the observed surface effect separately from possible causes or development implications.

Completed reports include a structured evidence brief: direct answer, evidence basis, decision relevance, confidence explanation, limitations, and the next verification action. A separate observation-quality section shows candidate/qualified/rejected counts, date-selection rationale, comparison span, and intermediate checks. These statements are generated from verified metrics rather than invented by a language model.

If a managed network performs TLS inspection, install its root CA in the Windows certificate store. Alternatively, point the backend to a trusted PEM bundle:

```powershell
$env:SATCHETAK_CA_BUNDLE = "C:\path\to\organization-ca-bundle.pem"
```

Restart the backend after changing trust configuration. TLS verification is never disabled.

### Optional Qwen explanation

The backend can call a small Qwen model through any OpenAI-compatible chat-completions server. Start the model server separately, then configure:

```powershell
$env:QWEN_BASE_URL = "http://127.0.0.1:11434/v1"
$env:QWEN_MODEL = "qwen2.5:1.5b"
$env:QWEN_API_KEY = "ollama"
```

Qwen receives only the verified interpretation contract. Its output is rejected if it introduces a number not present in that contract, is malformed, or the service is unavailable. The report then uses the deterministic explanation automatically and exposes the language provenance under a collapsed section.

### Additional providers and reference layers

Live catalogue discovery tries Copernicus first, then a compatible configured Bhoonidhi Sentinel-2 collection, then the public Planetary Computer Sentinel-2 STAC catalogue. Provider-specific catalogue searches are also available through `POST /api/v1/providers/bhoonidhi/search` and `POST /api/v1/providers/planetary_computer/search`.

```powershell
$env:BHOONIDHI_USER_ID = "your-user-id"
$env:BHOONIDHI_PASSWORD = "your-password"
$env:BHOONIDHI_COLLECTION = "your-collection-id"
$env:PLANETARY_COMPUTER_ENABLED = "true"
```

Bhoonidhi credentials stay on the backend. Non-Sentinel Bhoonidhi collections can be searched explicitly, but they are not silently passed into the Sentinel-2 Red/NIR/SWIR analysis.

To add a Bhuvan thematic layer to the map, provide a browser-safe, properly attributed WMS/WMTS tile template supported by MapLibre:

```dotenv
VITE_BHUVAN_WMS_TILE_URL=https://your-approved-bhuvan-service.example/.../{bbox-epsg-3857}...
```

The layer is reference context and never becomes analytical evidence unless a future workflow explicitly validates it.

### Monitoring and market evidence

Each saved report has a **Check for newer imagery** action backed by `POST /api/v1/locations/{id}/monitor/check`. It records the latest eligible observation without pretending that a desktop prototype is an always-on scheduler.

Market evidence is intentionally separate from satellite evidence. Users can enter traceable transaction or asking-price comparables in the collapsed Market-price evidence panel. The backend reports price-per-hectare range, median, and first-to-latest change through verified records only; it does not invent a valuation or infer price from pixels.

Quality checks:

```powershell
.\.venv\Scripts\python.exe -m pytest
cd frontend
npm run lint
npm run build
```

SATCHETAK is a location-first monitoring product. A user selects land once, and SATCHETAK turns suitable new satellite observations into evidence-grounded change maps, vegetation/land metrics, and natural-language insights.

## Core principle

> **Monitor land → detect change → quantify it → explain it.**

## Product flow

```text
Create monitored location
        ↓
Search place / enter latitude-longitude
        ↓
Draw Area of Interest (AOI)
        ↓
Choose monitoring objective
  ├─ Agriculture
  └─ Urban / Land Development
        ↓
Choose period / baseline
        ↓
Discover suitable satellite observations
        ↓
Filter cloud / invalid scenes
        ↓
Select baseline + latest valid observation
        ↓
Run domain analysis + GIS measurement
        ↓
Map evidence + metrics + evidence-grounded explanation
        ↓
Save location for future observations
```

The user does **not** need to upload imagery for the normal workflow. Manual upload remains a secondary expert/debug path for private or commercial imagery.

## Commercial MVP

### Agriculture monitoring

- NDVI / vegetation state
- NDMI where supported
- vegetation increase/decrease
- temporal trend
- anomaly/change polygons
- optional crop classification only when the exact model input contract is satisfied

Do not claim disease, nutrient deficiency, yield loss, or crop stress causes without validated models and ground truth.

### Urban / land-development monitoring

- generic land change
- built-up expansion where supported
- green-cover loss
- disturbed/cleared land
- change polygons
- changed-area measurements

With free 10 m Sentinel-2 data, SATCHETAK targets **large-area land change**, not individual-house or parcel-level surveillance.

## Observation as a Service

The primary domain objects are:

```text
MonitoredLocation
├─ name
├─ AOI
├─ sector
├─ observation policy
├─ baseline
├─ observation history
└─ analysis history

Observation
├─ provider
├─ satellite / sensor
├─ acquisition time
├─ cloud / quality metadata
├─ bands / CRS
└─ asset references

Analysis
├─ T1
├─ T2
├─ workflow
├─ evidence
├─ metrics
└─ explanation
```

## Data providers

Prototype priority:

```text
1. Copernicus Data Space Ecosystem
   → primary global Sentinel catalogue/data source

2. Bhoonidhi (ISRO)
   → Indian EO discovery/download and future India-specific differentiation

3. Microsoft Planetary Computer
   → secondary STAC/open-data provider

4. Bhuvan (ISRO)
   → thematic/reference layers, not the primary raw-image pipeline
```

Provider access sits behind a small interface so the analytics layer does not depend on a portal.

## Model/tool strategy

| Responsibility | Initial strategy |
|---|---|
| Language interpretation / explanation | Typed deterministic layer now; optional small Qwen-family instruct model behind the same contract later |
| Single-observation semantic questions | EarthDial or another qualified RS-VLM |
| Paired-image change | Open-CD qualified checkpoint |
| Agriculture crop classification | Prithvi crop checkpoint only for its exact compatible input |
| Spectral/GIS analytics | Rasterio / GDAL / NumPy |

No training/fine-tuning is required for the first prototype.

## Prototype success

The first useful build is complete when this works end-to-end:

```text
AOI
→ real satellite search
→ valid T1/T2 selection
→ agriculture OR land-change analysis
→ before/after view
→ evidence overlay
→ measured change
→ evidence-grounded explanation
→ save MonitoredLocation
```

## Product reference

The app now has a separate landing page and a `/#/dashboard` workspace with agricultural and development purchase screens, expanded vegetation statistics, dated analytical imagery, an opacity-controlled categorized change overlay, clickable region explanations, saved report history, print/PDF support, evidence JSON export, and MapLibre satellite/street basemaps. See [land screening and workspace](docs/LAND_SCREENING.md) for supported questions, evidence limits, artifact delivery, basemap configuration, and browser checks.

SatSure is a useful commercial reference because it demonstrates that customers pay for decision-ready Earth intelligence rather than raw imagery. SATCHETAK should not copy SatSure feature-for-feature. Its initial differentiation is a **self-service monitored-location workflow** with natural-language exploration and visible evidence/provenance.

## Non-goals for the hackathon MVP

- flood/disaster-response workflows;
- real-time satellite claims;
- building-level surveillance from 10 m imagery;
- custom model training;
- microservices/Kafka/Kubernetes;
- multi-agent systems;
- billing/enterprise tenancy;
- supporting every satellite/provider.

**SATCHETAK — monitor land, verify change.**
