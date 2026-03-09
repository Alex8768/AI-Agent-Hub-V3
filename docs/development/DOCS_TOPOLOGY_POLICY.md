# Docs Topology Policy (A2.32)

## Purpose

Define a deterministic migration policy for moving root-level operational docs
into structured documentation folders.

This policy follows a phased migration:

- compatibility-first during transition patches;
- canonical-only topology after closure.

## Target Topology

- `docs/architecture/` - architecture and platform contracts
- `docs/development/` - workflow, status, and contributor process docs

## Root-to-Target Map (Canonical)

- `PROJECT_ANCHOR.md` -> `docs/development/PROJECT_ANCHOR.md`
- `STATUS.md` -> `docs/development/STATUS.md`
- `PROJECT_CHECKLIST.md` -> `docs/development/PROJECT_CHECKLIST.md`
- `PLATFORM_FEATURES.md` -> `docs/architecture/PLATFORM_FEATURES.md`

## Migration Policy

During migration patches (Patch 1-4):

1. Keep root files present as compatibility stubs.
2. Root stubs must point to canonical target docs.
3. Canonical content lives only in target files after move.
4. Existing scripts/workflows that read root paths must continue to work.

Compatibility stubs should stay minimal and deterministic to avoid drift.

Final state (after Patch 5):

- canonical docs remain in target paths only;
- root compatibility stubs are removed;
- quality gate enforces canonical-only topology.

## Patch Discipline for A2.32

- Patch 1: topology map + policy (this document)
- Patch 2: move docs + create root stubs
- Patch 3: update references to canonical paths
- Patch 4: add deterministic docs topology quality gate
- Patch 5: finalize docs policy closure
