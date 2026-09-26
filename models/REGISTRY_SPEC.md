# Model Registry Specification

Each model entry must record:

```text
id
version/checkpoint
source/license
supported workflow
supported modalities
required bands/timestamps
preprocessing profile
output schema
qualification status
known limitations
```

Initial model families:

- Qwen — language interpretation/explanation
- EarthDial / qualified RS-VLM — single-observation semantics
- Open-CD checkpoint — paired land change
- Prithvi crop checkpoint — optional compatible crop classification

Flood-specific models are not part of the current MVP registry.
