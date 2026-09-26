# Evaluation

## Goal

Evaluate whether each prototype workflow is sufficiently reliable for its declared claim scope.

## Agriculture

Evaluate separately:

- NDVI/NDMI computation correctness
- spatial alignment
- threshold/change-mask stability
- area reconstruction
- crop-classification checkpoint only on compatible data

## Urban / land change

Evaluate:

- pair preprocessing
- change-mask quality
- false-change sensitivity to registration/season/cloud
- area measurement
- conservative semantic labeling

## Language layer

Test whether Qwen:

- maps paraphrases to the correct typed intent
- preserves dates/metrics from evidence
- does not invent unsupported values
- explains warnings clearly

## Provider layer

Test:

- AOI/date query correctness
- pagination
- required asset/band presence
- cloud/quality metadata
- provider failure handling

## Product demo gate

A result is demo-ready only when the complete AOI → observation → evidence → explanation path works on real data and known limitations are visible.
