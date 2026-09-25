# Contributing

SatQuery is a research-informed engineering project. Correct sensor semantics and reproducible evidence matter more than feature count.

## Before opening a change

Read:

- `docs/PROJECT_SCOPE.md`
- `docs/ARCHITECTURE.md`
- `docs/DECISIONS.md`
- `docs/DEVELOPMENT_PLAN.md`
- the relevant workflow and input-contract sections.

## Change size

Prefer one coherent vertical slice per pull request.

Good:

```text
add GeoTIFF metadata inspector + tests
```

Bad:

```text
replace router + add two models + redesign API + rebuild frontend
```

## Scientific changes

Any change to:

- model checkpoint,
- band order,
- normalization,
- threshold,
- CRS/resampling method,
- mask post-processing,
- confidence/calibration,

must include:

1. source/rationale;
2. tests;
3. expected behavioral change;
4. update to the relevant documentation/decision record.

## Model changes

A model must move through:

```text
RESEARCHED → DOWNLOADED → SMOKE_TESTED → QUALIFIED → DEFAULT
```

Do not skip states.

`QUALIFIED` means the model has passed our declared contract and evaluation suite for the intended workflow. It does not mean the model is universally valid for other sensors.

## Coding style

- Python: typed public interfaces, small pure functions for deterministic geo logic, explicit exceptions.
- TypeScript: keep API schemas generated/shared where practical; do not duplicate scientific logic in the browser.
- Prefer explicit enums and Pydantic models over unstructured dictionaries.
- Use structured logging.
- No catch-all exception that converts every failure into a success response.

## Tests

At minimum:

```bash
python -m pytest tests/path/to/affected_tests.py
git diff --check
```

Before merge, run the broader affected suite.

Model-dependent tests must be clearly tagged so CI can run fast deterministic tests without downloading multi-GB weights.

## Commits

Prefer conventional commits:

```text
feat(ingestion): add GeoTIFF metadata inventory
fix(flood): reject non-RTC Sentinel-1 input
test(change): add non-overlap pair rejection
docs(models): qualify AI4G flood checkpoint
```

## Artifacts

Generated masks, checkpoints, caches, datasets, and temporary rasters do not belong in Git unless a small fixture is explicitly required for deterministic testing.

Keep benchmark result manifests versioned when they are used to justify a model decision.
