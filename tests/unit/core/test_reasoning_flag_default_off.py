from __future__ import annotations

import inspect
import importlib


def _find_settings_like_class(mod):
    # Find the config/settings class by the presence of our feature flags.
    # This avoids hardcoding the class name (Settings/AppConfig/etc.)
    candidates = []
    for _, obj in vars(mod).items():
        if not inspect.isclass(obj):
            continue
        ann = getattr(obj, "__annotations__", {}) or {}
        if "feature_graphrag" in ann and "feature_reasoning" in ann:
            candidates.append(obj)
    if not candidates:
        raise AssertionError(
            "Could not find config/settings class with "
            "'feature_graphrag' and 'feature_reasoning' annotations in src.core.config"
        )
    # Prefer the first match (should be unique in this codebase).
    return candidates[0]


def test_reasoning_flag_default_off():
    cfg = importlib.import_module("src.core.config")
    SettingsCls = _find_settings_like_class(cfg)
    s = SettingsCls()

    assert s.feature_reasoning is False
