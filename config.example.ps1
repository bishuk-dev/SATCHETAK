# Copy the variables you need into the PowerShell session that starts SATCHETAK.
# Never commit real credentials.

# Copernicus Data Space: required for live Sentinel-2 pixel processing.
$env:CDSE_CLIENT_ID = "replace-with-oauth-client-id"
$env:CDSE_CLIENT_SECRET = "replace-with-oauth-client-secret"

# Local Ollama Qwen: optional, with verified deterministic fallback.
$env:QWEN_BASE_URL = "http://127.0.0.1:11434/v1"
$env:QWEN_MODEL = "qwen2.5:1.5b"
$env:QWEN_API_KEY = "ollama"

# Bhoonidhi: optional authenticated catalogue integration.
$env:BHOONIDHI_USER_ID = "replace-with-bhoonidhi-user-id"
$env:BHOONIDHI_PASSWORD = "replace-with-bhoonidhi-password"
$env:BHOONIDHI_COLLECTION = "replace-with-collection-id"

# Public Planetary Computer catalogue fallback.
$env:PLANETARY_COMPUTER_ENABLED = "true"

# Optional custom CA bundle for managed networks. Never disable TLS verification.
# $env:SATCHETAK_CA_BUNDLE = "C:\path\to\organization-root-chain.pem"

# Backend browser origins.
$env:SATCHETAK_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"

# Optional frontend values belong in frontend/.env.local, not in this script:
# VITE_BHUVAN_WMS_TILE_URL=...
# VITE_SATELLITE_TILE_URL=...
# VITE_SATELLITE_ATTRIBUTION=...
