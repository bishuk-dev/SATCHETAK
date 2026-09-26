# Security

Prototype security priorities:

- validate AOI geometry and file inputs;
- keep provider credentials server-side;
- do not allow arbitrary server-side URL fetching;
- restrict raster/GDAL resource use;
- do not expose arbitrary shell/Python execution;
- sanitize generated artifact paths;
- apply size/pixel limits to optional user uploads;
- preserve source provenance without leaking secrets/signed URLs.

## TLS trust

All Copernicus catalogue, identity, and processing requests verify TLS certificates. On Windows the backend uses the native certificate store, which supports organization-managed root certificates. If a TLS-inspection proxy uses a root CA that cannot be installed in the system store, set `SATCHETAK_CA_BUNDLE` to the absolute path of a trusted PEM CA bundle and restart the backend.

Do not work around certificate failures by disabling verification (`verify=False`) or by suppressing TLS warnings.
