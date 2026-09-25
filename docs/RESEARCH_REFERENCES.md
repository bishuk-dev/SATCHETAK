# Research and Source References

This file records primary/official sources used for architectural choices. It is not a claim that SatQuery reproduces every reported result.


## Language layer

### Qwen open instruction-model family

Primary official sources to consult before freezing a checkpoint:
- Qwen official GitHub organization/repositories
- official Hugging Face model cards for the selected checkpoint

Use:
- intent parsing;
- structured output;
- clarification;
- evidence-grounded explanation.

Important:
SatQuery does not rely on a Qwen checkpoint for remote-sensing perception or physical measurement. The exact model size is selected by our language evaluation, not by marketing benchmark position.

---

## Single-image / multimodal VLM

### EarthDial — CVPR 2025
**EarthDial: Turning Multi-sensory Earth Observations to Interactive Dialogues**

Official repository:
https://github.com/hiyamdebary/EarthDial

Official/publisher-associated model weights:
https://huggingface.co/akshaydudhane/EarthDial_4B_RGB
https://huggingface.co/akshaydudhane/EarthDial_4B_MS

Relevant support:
- EO-specific conversational VLM;
- RGB, multispectral, SAR, multi-resolution and multi-temporal data;
- VQA, classification, visual reasoning and grounding;
- public 4B weights.

Engineering caveat:
The official code pins an older Transformers stack, so dependency compatibility must be tested rather than assumed.

### GeoGround
Official repository:
https://github.com/VisionXLab/GeoGround

Relevant support:
- remote-sensing visual grounding;
- HBB, OBB and mask grounding;
- public weights announced/released.

Use as a specialist candidate only if required.

---

## Change detection

### Open-CD
Official repository:
https://github.com/likyoo/open-cd

Inference documentation:
https://github.com/likyoo/open-cd/blob/main/docs/inference.md

Research:
**Open-CD: A Comprehensive Toolbox for Change Detection**, ACM Multimedia 2025.

Relevant support:
- pretrained model zoo;
- inference API;
- multiple remote-sensing binary-change architectures;
- Apache-2.0.

### ChangeFormer
Official implementation:
https://github.com/wgcban/ChangeFormer

**A Transformer-Based Siamese Network for Change Detection**, IGARSS 2022.

Useful as an alternative checkpoint/reference, but the standalone repository uses an older dependency stack.

---

## Flood

### Microsoft AI4G Flood
Official repository:
https://github.com/microsoft/ai4g-flood

Paper:
**Mapping global floods with 10 years of satellite radar data**
Nature Communications, 2025
https://doi.org/10.1038/s41467-025-60973-1

Relevant support:
- public inference code and trained artifact;
- pre/post Sentinel-1 VV/VH workflow;
- explicit RTC/preprocessing guidance;
- flood extent output.

### Sen1Floods11
Official dataset repository:
https://github.com/cloudtostreet/Sen1Floods11

Paper:
Bonafilia et al., CVPR Workshops 2020.

Relevant support:
- georeferenced flood benchmark;
- Sentinel-1 VV/VH and Sentinel-2 data;
- hand labels.

### IBM/NASA Prithvi EO 2.0 flood checkpoint
https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-300M-TL-Sen1Floods11

Relevant support:
- official IBM/NASA publisher;
- TerraTorch integration;
- documented six-band optical flood inference;
- Apache-2.0 shown on model card.

---

## Agriculture

### IBM/NASA Prithvi multi-temporal crop classification
https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-1.0-100M-multi-temporal-crop-classification

Relevant support:
- official pretrained downstream checkpoint;
- 3-timestamp / 18-band documented input;
- crop/land-class segmentation;
- Apache-2.0 shown on model card.

### Prithvi EO 2.0
Official repository:
https://github.com/NASA-IMPACT/Prithvi-EO-2.0

Relevant support:
- multi-temporal EO foundation model;
- temporal/location-aware variants;
- useful future backbone, but an unadapted backbone is not automatically a crop/flood classifier.

---

## Multimodal EO background

### BigEarthNet.txt
**BigEarthNet.txt: A Large-Scale Multi-Sensor Image-Text Dataset and Benchmark for Earth Observation**

Used as evidence that remote-sensing VLM adaptation and multisensor VQA/grounding are active research areas.

Important: SatQuery v2 does not train on BigEarthNet.txt initially.

### AnySat — CVPR 2025 Highlight
Official repository:
https://github.com/gastruc/anysat

Relevant support:
- heterogeneous EO resolutions/modalities;
- flood mapping, crop classification and change-detection downstream tasks after adaptation/heads.

Important: the released foundation encoder is not treated as an off-the-shelf task head for our MVP.

---

## Agentic / workflow background

### Agentic AI for Remote Sensing: Technical Challenges and Research Directions
Position paper / arXiv, 2026.

Architectural lesson used:
- EO workflows need geospatial state and validity checks;
- tool order matters;
- planner/executor/verifier is safer than unconstrained language-only reasoning.

SatQuery adopts the validity principle but does **not** implement an autonomous multi-agent system.

---

# Evidence hierarchy

When adding future sources, prefer:

1. peer-reviewed paper;
2. official author/research-organization repository;
3. official model card/release;
4. reputable maintained scientific toolbox;
5. community reproduction.

Never base a production model decision only on a blog post or copied benchmark table.
