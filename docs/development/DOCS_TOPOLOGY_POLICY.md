# Docs Topology Policy (A2.32)

## Purpose

Define a deterministic migration policy for moving root-level operational docs
into structured documentation folders.

This policy is intentionally compatibility-first: migration must not break
existing workflows that still read root-level paths.

## Target Topology

- `docs/architecture/` - architecture and platform contracts
- `docs/development/` - workflow, status, and contributor process docs

## Root-to-Target Map (Canonical)

- `PROJECT_ANCHOR.md` -> `docs/development/PROJECT_ANCHOR.md`
- `STATUS.md` -> `docs/development/STATUS.md`
- `PROJECT_CHECKLIST.md` -> `docs/development/PROJECT_CHECKLIST.md`
- `PLATFORM_FEATURES.md` -> `docs/architecture/PLATFORM_FEATURES.md`

## Compatibility Policy

During migration patches:

1. Keep root files present as compatibility stubs.
2. Root stubs must point to canonical target docs.
3. Canonical content lives only in target files after move.
4. Existing scripts/workflows that read root paths must continue to work.

Compatibility stubs should stay minimal and deterministic to avoid drift.

Current state (after Patch 2):

- canonical docs are already moved to target paths;
- root files are temporary compatibility stubs;
- stubs are removed only in Patch 5 after reference and quality-gate alignment.

## Patch Discipline for A2.32

- Patch 1: topology map + policy (this document)
- Patch 2: move docs + create root stubs
- Patch 3: update references to canonical paths
- Patch 4: add deterministic docs topology quality gate
- Patch 5: finalize docs policy closure
