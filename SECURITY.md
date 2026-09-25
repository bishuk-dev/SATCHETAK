# Security Policy

SATCHETAK processes complex raster formats and loads third-party model code/weights. Both are security boundaries.

## Untrusted raster uploads

Validate before decoding/processing:

- allowlisted format/driver;
- file size;
- width and height;
- band count;
- total pixel count;
- dtype;
- decompressed-memory estimate;
- archive paths when archives are ever accepted.

Initial allowlist:

```text
GeoTIFF / TIFF
PNG
JPEG
```

Do not accept arbitrary VRT/XML-driven raster graphs in the MVP.

## Filesystem

- Each analysis receives an isolated runtime directory.
- Normalize and validate paths.
- Never allow `..` traversal outside the analysis root.
- Do not expose raw server filesystem paths to clients.
- Generated filenames come from server IDs, not user input.

## Model supply chain

For every checkpoint:

- prefer official publisher/model card;
- pin revision/commit;
- record SHA-256 where practical;
- prefer safetensors over pickle when available;
- review any repository requiring `trust_remote_code=True`;
- never execute remote code from an unpinned branch;
- do not commit model weights.

## Process isolation

Do not add containers merely for architecture aesthetics.

Use a separate runner/container when:

- a model needs incompatible Python/CUDA/framework versions;
- a model requires reviewed remote custom code;
- memory isolation is necessary;
- a failure in the model runtime could destabilize the API process.

## Query safety

Natural-language queries can select from a bounded registry of workflows and parameters only.

The model must never receive permission to:

- execute shell commands;
- import arbitrary packages;
- read arbitrary host files;
- make arbitrary network requests;
- write outside the runtime artifact directory.

## Secrets

Never commit:

- `.env`;
- API tokens;
- Hugging Face write tokens;
- cloud credentials;
- SSH keys;
- private dataset URLs.

## Reporting

If a security issue is discovered, do not publish exploit details in a public issue before remediation. Use a private disclosure channel configured for the repository.
