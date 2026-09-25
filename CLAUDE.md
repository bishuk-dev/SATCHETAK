# CLAUDE.md

Read and follow [`AGENTS.md`](AGENTS.md). It is the authoritative repository-wide AI instruction file.

Also read, in this order:

1. [`docs/DECISIONS.md`](docs/DECISIONS.md)
2. [`docs/DEVELOPMENT_PLAN.md`](docs/DEVELOPMENT_PLAN.md)
3. the workflow/model/input document relevant to the current task.

## Claude-specific working protocol

Before code generation:

- summarize the current phase in one sentence;
- name the files you intend to modify;
- identify the input/output contract being changed;
- identify how the change will be tested.

During implementation:

- keep the patch bounded to one vertical slice;
- do not silently introduce training/fine-tuning;
- do not broaden model support;
- do not substitute a generic VLM when a specialist rejects an input;
- do not invent confidence values or benchmark results.

After implementation:

- run the relevant tests;
- inspect generated masks/overlays when applicable;
- report verified facts separately from assumptions and future work.

If uncertain about remote-sensing physics, a model input contract, or a checkpoint's preprocessing, stop and research the primary source rather than guessing.
