from __future__ import annotations

from src.layers.pro.reasoning.contracts import AnswerRequest
from src.services.answer.policy_profiles import resolve_runtime_policy_profile


def test_policy_profiles_default_dev_guided_in_debug() -> None:
    class _S:
        debug = True

    profile = resolve_runtime_policy_profile(req=AnswerRequest(query="x"), settings=_S())
    assert profile.get("profile_name") == "dev_guided"
    assert profile.get("allow_act_read_only") is True


def test_policy_profiles_default_prod_strict_in_non_debug() -> None:
    class _S:
        debug = False

    profile = resolve_runtime_policy_profile(req=AnswerRequest(query="x"), settings=_S())
    assert profile.get("profile_name") == "prod_strict"
    assert profile.get("allow_act_read_only") is False


def test_policy_profiles_applies_override_only_in_debug() -> None:
    class _S:
        debug = True

    req = AnswerRequest(query="x", filters={"runtime_policy_profile": "dev_full"})
    profile = resolve_runtime_policy_profile(req=req, settings=_S())
    assert profile.get("profile_name") == "dev_full"
    assert "runtime_policy_profile_override_applied" in list(profile.get("reason_codes") or [])
