"""HS-34-04: lock the intel public surface after the package split.

The 1,066-line `intel.py` module became an `intel/` package
(models / parsing / providers / engine) with a full re-export `__init__`. This
guards that every name callers/tests rely on is still importable from
`holdspeak.intel`, including the optional-dependency patch targets
(`OpenAI`, `Llama`) that `providers`/`engine` read through the package.
"""

from __future__ import annotations

import holdspeak.intel as intel

_PUBLIC = {
    # models
    "MeetingIntelError",
    "ActionItem",
    "IntelResult",
    "DEFAULT_INTEL_MODEL_PATH",
    "DEFAULT_INTEL_PROVIDER",
    "VALID_INTEL_PROVIDERS",
    # providers
    "resolve_intel_provider",
    "resolve_llm_capability",
    "build_configured_meeting_intel",
    "get_intel_runtime_status",
    "get_local_intel_runtime_status",
    "get_cloud_intel_runtime_status",
    "intel_egress_posture",
    # parsing
    "_extract_json",
    "_coerce_action_items",
    # engine
    "MeetingIntel",
}


def test_public_surface_is_importable() -> None:
    missing = sorted(n for n in _PUBLIC if not hasattr(intel, n))
    assert not missing, f"holdspeak.intel no longer exports: {missing}"


def test_public_names_are_in_dunder_all() -> None:
    not_exported = sorted(n for n in _PUBLIC if n not in intel.__all__)
    assert not not_exported, f"missing from __all__: {not_exported}"


def test_optional_dependency_patch_targets_exist() -> None:
    # test_intel_cloud / test_intel_egress_invariant / test_intel_streaming patch
    # holdspeak.intel.OpenAI and holdspeak.intel.Llama; providers/engine read them
    # via the package, so the package must expose them.
    assert hasattr(intel, "OpenAI")
    assert hasattr(intel, "Llama")


def test_engine_reads_openai_through_the_package(monkeypatch) -> None:
    """A package-level patch of OpenAI must reach the engine (egress contract)."""
    sentinel = object()
    monkeypatch.setattr(intel, "OpenAI", None)
    eng = intel.MeetingIntel(provider="cloud", cloud_base_url="http://127.0.0.1:9/v1")
    # With OpenAI patched to None on the package, the engine's cloud-load guard
    # must raise (it reads intel.OpenAI via the package), not silently succeed.
    import pytest

    with pytest.raises(Exception):
        eng._ensure_openai_client_loaded()
    del sentinel
