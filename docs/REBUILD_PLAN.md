# Clean Rebuild Plan

## Goal

Start implementation without dragging forward accidental architecture from the previous attempt, while preserving the old work for reference.

## Do not

- delete the old repository/history;
- mass-copy old packages into the rebuild;
- refactor old code until it “looks clean”;
- reuse a component simply because it already exists.

Reuse only after the new workflow contract exists and the old component independently satisfies it.

## Recommended Git strategy

Safest options, in order:

### Option A — new repository

Best isolation.

Keep the old repository read-only and create a fresh repository for v2.

### Option B — clean orphan branch in the same repository

Preserve old history on `main`/tag, create a clean v2 root on a separate branch, review it, then optionally change the default branch later.

Do not rewrite shared history merely to make the repo look clean.

## Archive marker

Before implementation, record the exact final legacy commit/tag, for example:

```text
legacy-sih-2026-attempt
```

The rebuild docs should reference it only as historical context.

## Import policy

Nothing from legacy code is copied automatically.

For each reused module:

1. identify new contract;
2. inspect old implementation;
3. copy the smallest useful logic;
4. rewrite tests against the new contract;
5. remove assumptions no longer valid;
6. record reuse in the PR/commit.

## First clean commit

The first rebuild commit should contain only:

```text
README
AGENTS
CLAUDE
CONTRIBUTING
SECURITY
docs/*
minimal package skeleton
test runner/config
```

No model integration.

The second milestone begins Phase 1 ingestion.

## Why

A clean phase boundary gives AI coding tools less stale context and reduces the chance they “repair” old assumptions instead of implementing the new design.
