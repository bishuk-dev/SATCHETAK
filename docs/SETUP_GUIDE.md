# Complete local and API setup

This guide configures the complete SATCHETAK prototype without putting secrets in frontend code.

## 1. Install and run the application

Requirements: Python 3.11+, Node.js/npm, and Git.

```powershell
cd C:\Users\Dell\Documents\Github\SATCHETAK
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"

cd frontend
npm install
cd ..
```

Use two terminals after configuring the environment:

```powershell
# Terminal 1
.\.venv\Scripts\python.exe -m satchetak.app

# Terminal 2
cd frontend
npm run dev
```

Open `http://127.0.0.1:5173`. API documentation is at `http://127.0.0.1:8000/api/docs`, and the effective integration state is at `http://127.0.0.1:8000/api/v1/capabilities`.

### Configure once with `.env` (recommended)

You do not need to enter every variable in PowerShell. From the repository root, create a private local configuration once:

```powershell
Copy-Item .env.example .env
notepad .env
```

Fill only the providers you use, save the file, and start the backend normally. SATCHETAK automatically reads the root `.env` file. The file is ignored by Git, and variables explicitly set by Windows or PowerShell take priority over it.

This workspace already has a local `.env` with Ollama configured; add your Copernicus and optional Bhoonidhi credentials there. Keep browser-visible Vite options in `frontend/.env.local`, because every `VITE_` value is exposed to frontend code.

To use a configuration stored elsewhere, set only one variable:

```powershell
$env:SATCHETAK_ENV_FILE = "C:\secure\satchetak.env"
.\.venv\Scripts\python.exe -m satchetak.app
```

## 2. Ollama and Qwen

Ollama is installed at:

```text
C:\Users\Dell\AppData\Local\Programs\Ollama\ollama.exe
```

Add that directory to the user `Path`, or use the full path:

```powershell
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" serve
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" pull qwen2.5:1.5b
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" list
```

Usually the desktop Ollama application already runs the server, so `serve` may report that port `11434` is in use; that is harmless. Verify it:

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

The recommended root `.env` already contains these settings. For a temporary override in one terminal, use:

```powershell
$env:QWEN_BASE_URL = "http://127.0.0.1:11434/v1"
$env:QWEN_MODEL = "qwen2.5:1.5b"
$env:QWEN_API_KEY = "ollama"
.\.venv\Scripts\python.exe -m satchetak.app
```

The backend sends Qwen verified structured evidence only. Any response that introduces a new numerical value, changes the verified final action, has an invalid response structure, or fails to return is rejected. The deterministic explanation remains available automatically. Check the collapsed **Explanation provenance** section in a newly generated report.

### Ollama TLS failure while pulling

If `ollama pull` reports `x509: certificate signed by unknown authority`, first open the network's captive-portal sign-in page and authenticate if one is present. If the connection is still TLS-inspected, ask the network administrator to install the organization root/intermediate CA through Windows policy, or use a trusted network. Do not disable TLS verification or permanently trust a certificate captured from an unauthenticated portal. `SATCHETAK_CA_BUNDLE` controls Python API calls; it does not change the separate Ollama process trust store.

## 3. Copernicus Data Space

Copernicus is the primary live catalogue and pixel-processing provider.

1. Create/sign in to a Copernicus Data Space account.
2. Open the Sentinel Hub dashboard and create an OAuth client.
3. Copy the client ID and secret into the root `.env` file:

```dotenv
CDSE_CLIENT_ID=your-client-id
CDSE_CLIENT_SECRET=your-client-secret
```

Restart the backend after changing credentials. Never place this secret in `frontend/.env.local`. Live processing acquires aligned Sentinel-2 L2A arrays and SCL/data masks. Catalogue scene-cloud percentage is not substituted for the AOI valid-pixel mask.

Official resources:

- <https://dataspace.copernicus.eu/>
- <https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Overview/Authentication.html>

## 4. Bhoonidhi

Bhoonidhi requires an account and API credentials. Add them to the root `.env`:

```dotenv
BHOONIDHI_USER_ID=your-user-id
BHOONIDHI_PASSWORD=your-password
BHOONIDHI_COLLECTION=collection-id-from-bhoonidhi
```

Restart the backend. Test a provider-specific search from FastAPI docs using:

```text
POST /api/v1/providers/bhoonidhi/search
```

The endpoint performs `/auth/token` authentication and STAC-style `/data/search`. Any configured collection can be searched explicitly. Only a Sentinel-2-compatible collection can participate in the automatic Red/NIR/SWIR analysis fallback; an unrelated Cartosat, SAR, DEM, or ocean product is never silently treated as Sentinel-2.

Official API specification: <https://bhoonidhi.nrsc.gov.in/bhoonidhi-api/>

## 5. Planetary Computer

The public Planetary Computer Sentinel-2 STAC catalogue needs no API key in this prototype. It is enabled by default:

```powershell
$env:PLANETARY_COMPUTER_ENABLED = "true"
```

Test it through:

```text
POST /api/v1/providers/planetary_computer/search
```

It is used only after earlier configured catalogue providers return no candidates. Pixel processing remains provenance-labelled and uses the Copernicus processing credentials.

Official STAC API: <https://planetarycomputer.microsoft.com/api/stac/v1/docs>

## 6. Bhuvan thematic/reference layers

Bhuvan is a contextual OGC WMS/WMTS layer, not the raw-image analysis provider. Obtain the approved layer/service URL from the Bhuvan catalogue. Create `frontend/.env.local`:

```dotenv
VITE_BHUVAN_WMS_TILE_URL=https://approved-service.example/wms?service=WMS&request=GetMap&version=1.1.1&layers=approved_layer&styles=&format=image/png&transparent=true&srs=EPSG:3857&width=256&height=256&bbox={bbox-epsg-3857}
```

Restart Vite. A **Bhuvan layer** option appears only when this variable exists. Do not use a sample state-specific layer outside its published extent, and keep NRSC/ISRO attribution.

Official guidance: <https://bhuvan.nrsc.gov.in/wiki/index.php/How_to_use_WMS_services>

## 7. Context basemaps

The default contextual basemaps are OpenStreetMap streets and Esri World Imagery. To use another licensed satellite tile source, create `frontend/.env.local`:

```dotenv
VITE_SATELLITE_TILE_URL=https://provider.example/{z}/{x}/{y}.jpg
VITE_SATELLITE_ATTRIBUTION=Required provider attribution
```

These tiles are visual context only. Dated evidence images always come from the aligned analysis arrays.

## 8. Monitoring

Open a completed saved report and select **Check for newer imagery**. The action calls:

```text
POST /api/v1/locations/{location_id}/monitor/check
```

It searches from the last analyzed T2 date to today and records the check. If a newer eligible observation exists, rerun the analysis. This prototype does not claim an always-running cloud scheduler; deploy an external scheduled HTTP job later if unattended checks are required.

## 9. Land-price evidence

Expand **Market-price evidence** in a report and enter a dated, traceable transaction or asking-price comparable. SATCHETAK calculates price per hectare, median, observed range, and first-to-latest percentage change.

```text
POST /api/v1/locations/{location_id}/price-comparables
GET  /api/v1/locations/{location_id}/price-summary
```

No price is inferred from satellite imagery. Mixed currencies are rejected rather than silently converted. For production, connect a licensed registry/listing source to the same comparable contract.

## 10. TLS-inspected networks

Export the organization root and intermediate certificates as a PEM chain and configure:

```powershell
$env:SATCHETAK_CA_BUNDLE = "C:\path\to\organization-ca-chain.pem"
```

Restart the backend. Never add an option that disables certificate verification.

## 11. Final verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q

cd frontend
npm run lint
npm run build
npm run test:e2e
```

Then run one new live report and verify:

- `/api/v1/capabilities` shows the expected configured services;
- the report says `SENTINEL-2 PIXELS`, not simulated pixels;
- observation dates and audit trail are visible;
- Qwen provenance says its paraphrase was validated;
- before/after/overlay images load;
- numbered regions, monitoring check, JSON export, PDF print, and market evidence work.
