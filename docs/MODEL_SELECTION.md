# Model Selection

## Goal

Use the smallest set of qualified pretrained models/tools needed for the two commercial verticals.

## Initial stack

### Qwen-family instruct model

Role:

- natural-language intent parsing
- parameter extraction
- explanation of verified results

Not allowed to generate scientific measurements or evidence.

### EarthDial or another qualified remote-sensing VLM

Role:

- bounded single-observation semantic questions
- optional grounding if the selected checkpoint demonstrably supports it

### Open-CD

Role:

- paired-image change detection

A default checkpoint is promoted only after compatibility and local smoke/evaluation tests.

### IBM/NASA Prithvi crop classifier

Role:

- optional agriculture-specific classification

Restriction:

Use only for its exact documented multi-temporal/band input contract. It is not a generic RGB crop classifier.

### Rasterio / GDAL / NumPy

Role:

- NDVI / NDMI
- CRS/alignment
- masks/polygonization
- area/statistics
- deterministic geospatial calculations

## Removed from MVP

- AI4G Flood
- Prithvi flood checkpoint
- flood model adapters
- SAR flood-specific preprocessing

## Qualification rule

A model becomes usable only after:

1. license/source identified;
2. checkpoint/version pinned;
3. input contract implemented exactly;
4. local inference smoke test passes;
5. output normalization is tested;
6. known failure modes are documented.

Strong paper metrics alone do not make a checkpoint a product default.
