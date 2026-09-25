# Pretrained Model Selection

## Policy

SATCHETAK does not train or fine-tune models in the initial rebuild.

A model is adopted only when:

1. the source is trustworthy;
2. weights are publicly obtainable;
3. license/usage terms are recorded;
4. input preprocessing is documented;
5. output semantics are known;
6. local inference works;
7. negative/input-contract tests work;
8. it provides value over a deterministic baseline.

Model status:

```text
RESEARCHED
DOWNLOADED
SMOKE_TESTED
QUALIFIED
DEFAULT
REJECTED
```


## 0. Language interpretation and explanation

### Preferred first family: Qwen open instruct models

Qwen-family instruction models are the first candidates for the text-only language layer.

Required capabilities:

```text
free-form query → typed intent
parameter extraction
clarification
strict JSON/schema output
evidence-grounded explanation
multilingual/colloquial query handling
```

Selection principle:

> Choose the **smallest** model that passes SATCHETAK's language qualification suite with acceptable latency and memory use.

Do not assume the newest/largest checkpoint is automatically better for this role.

The language layer is replaceable. The production interface must depend on `IntentRequest` and explanation schemas, not Qwen-specific tokenization or tool-call formats.

Qualification must measure:

- intent accuracy;
- JSON/schema validity;
- parameter extraction;
- clarification correctness;
- hallucinated-field rate;
- unsupported-operation rejection;
- latency and memory.

The LLM does not receive authority to bypass workflow/input validation.

---

## 1. Single-image VQA / scene reasoning

### Primary candidate: EarthDial 4B

Source:
- CVPR 2025 paper/repository: `hiyamdebary/EarthDial`
- published 4B weights on Hugging Face under the authors' account.

Why it is relevant:

- remote-sensing-specific conversational VLM;
- published support for RGB, multispectral, SAR, multi-resolution and multi-temporal EO data;
- tasks include VQA, classification, detection/grounding and visual reasoning;
- available 4B checkpoints are substantially smaller than many 7B+ RS VLM alternatives.

Known engineering constraint:

The EarthDial repository pins an older Transformers stack. Do not let that force global dependency downgrades without testing. If dependency conflict becomes real, isolate the adapter.

Checkpoint handling:

- pin exact Hugging Face revision;
- prefer `safetensors`;
- document whether RGB or MS checkpoint is used;
- never route a modality to a checkpoint merely because the code accepts an image.

### Grounding specialist fallback: GeoGround

GeoGround released model weights in 2025 and targets remote-sensing visual grounding across HBB, OBB and segmentation-mask outputs.

It should be evaluated only if EarthDial grounding is inadequate. Do not add it in Phase 2 unless needed.

### Rejected as first choice: generic VLM

InternVL/Qwen can be valuable baselines, but the first production candidate should be remote-sensing adapted because generic VLMs may be fluent while missing sensor/domain semantics.

---

## 2. Generic paired change

### Framework: Open-CD

Open-CD is an Apache-2.0 change-detection toolbox with pretrained models and a direct inference API. Its technical report was accepted at ACM Multimedia 2025.

Reason to use a toolbox adapter instead of vendor-copying one research repo:

- one stable integration surface;
- multiple published pretrained checkpoints;
- easier A/B qualification;
- masks are direct task outputs.

### Initial smoke candidate

`ChangerEx R18` on LEVIR-CD is a reasonable first checkpoint because it is directly shown in the Open-CD inference documentation.

It is **not frozen as DEFAULT** until compared with at least one alternate (for example another LEVIR-CD/S2Looking checkpoint) on our selected test cases.

Limit:

LEVIR-CD-style models are primarily high-resolution optical binary change detectors. They do not automatically generalize to SAR, arbitrary spectral stacks, or agricultural semantics.

---

## 3. Flood

### Primary SAR candidate: Microsoft AI4G Flood

Official source:
- `microsoft/ai4g-flood`
- trained model artifact included by the authors;
- associated peer-reviewed Nature Communications paper (2025).

Model:
- U-Net;
- MobileNetV2 encoder;
- Sentinel-1 VV/VH;
- pre/post pair workflow.

Why selected:

- task-specific;
- official code and artifact;
- paper-backed deployment methodology;
- explicit preprocessing warnings;
- directly produces flood extent rather than relying on VLM description.

Important input limitation:

The official docs emphasize Sentinel-1 RTC-compatible processing. Other SAR sensors/products are out of qualified scope until separately tested.

### Optical fallback candidate: IBM/NASA Prithvi EO 2.0 Sen1Floods11

Model:
`ibm-nasa-geospatial/Prithvi-EO-2.0-300M-TL-Sen1Floods11`

License shown on model card: Apache-2.0.

Input:
six documented optical bands used by the Sen1Floods11 fine-tune.

This is a later path, not required for the first flood milestone.

---

## 4. Agriculture

### Crop-classification candidate

Model:
`ibm-nasa-geospatial/Prithvi-EO-1.0-100M-multi-temporal-crop-classification`

Publisher:
IBM/NASA geospatial model family.

Model card license:
Apache-2.0.

Exact documented input:
- GeoTIFF;
- 18 bands;
- 3 timesteps;
- per timestep: Blue, Green, Red, Narrow NIR, SWIR1, SWIR2.

The strict input contract is a benefit: it prevents us from pretending that arbitrary imagery can produce crop classes.

### Generic vegetation change

No pretrained crop model is required.

Use deterministic NDVI/related index change where band semantics permit.

This is more defensible than applying a crop checkpoint outside its sensor/temporal contract.

---

# Model registry fields

The eventual machine-readable registry must include:

```yaml
id:
status:
publisher:
source_url:
paper_url:
license:
revision:
sha256:
capabilities:
modalities:
sensors:
required_bands:
band_order:
radiometry:
input_size:
normalization:
temporal_requirement:
output_type:
preprocessing_profile:
known_limits:
qualified_on:
```

No model weight is committed to Git.

# Trust hierarchy

Prefer:

```text
peer-reviewed paper + official author repo/model
        >
official research-organization model card
        >
well-maintained scientific toolbox
        >
community checkpoint with reproducible evidence
        >
random tutorial / mirror
```

Community models may be used for experiments, but they are not promoted without stronger validation.
