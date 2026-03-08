# pro-v3.1-dev snapshot (2026-02-28)

Commit: `48422b8`
Branch: `pro-v3.1-dev`

## Purpose

This snapshot captures a hardened, CI-green baseline of AI Agent Hub V3 (Base + Pro).

## Verification

```bash
python -m compileall -q src
pytest -q
```

```bash
python scripts/demo_golden_path.py
```

```bash
DEMO_ENABLE_REASONING=1 python scripts/demo_golden_path.py
```
