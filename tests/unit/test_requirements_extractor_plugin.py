"""HS-27-04: the real requirements_extractor plugin."""

from __future__ import annotations

from holdspeak.plugins.builtin import register_builtin_plugins
from holdspeak.plugins.builtin.requirements_extractor import (
    RequirementsExtractorPlugin,
    _extract_requirements,
    _normalize_type,
)
from holdspeak.plugins.host import PluginHost

_GOOD_JSON = """```json
{"requirements": [
  {"text": "The system must let users export reports as PDF", "type": "functional"},
  {"text": "Page loads must complete within 200ms", "type": "non-functional"},
  {"text": "Must ship by Q3", "type": "constraint"},
  {"text": "Export passes WCAG AA contrast checks", "type": "acceptance criteria"}
]}
```"""


def _plugin(response):
    return RequirementsExtractorPlugin(intel_call=lambda _m: response)


def test_attributes() -> None:
    p = RequirementsExtractorPlugin()
    assert p.id == "requirements_extractor"
    assert p.kind == "synthesizer"
    assert p.execution_mode == "deferred"
    assert p.required_capabilities == ["llm"]


def test_run_success_extracts_and_classifies() -> None:
    out = _plugin(_GOOD_JSON).run({"transcript": "We discussed requirements."})
    assert out["confidence_hint"] == 1.0
    assert [r["type"] for r in out["requirements"]] == [
        "functional",
        "non_functional",
        "constraint",
        "acceptance",
    ]
    assert out["requirements"][0]["text"] == "The system must let users export reports as PDF"
    assert "4 requirement(s)" in out["summary"]


def test_run_bare_strings_default_to_functional() -> None:
    out = _plugin('{"requirements": ["Support SSO login"]}').run({"transcript": "t"})
    assert out["confidence_hint"] == 1.0
    assert out["requirements"] == [{"text": "Support SSO login", "type": "functional"}]


def test_run_unknown_type_falls_back_to_functional() -> None:
    out = _plugin('{"requirements": [{"text": "Do a thing", "type": "weird"}]}').run({"transcript": "t"})
    assert out["requirements"][0]["type"] == "functional"


def test_run_empty_is_failure() -> None:
    out = _plugin('{"requirements": []}').run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "requirements" not in out


def test_run_unparseable_is_failure() -> None:
    out = _plugin("no json here, just chatter").run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "requirements" not in out


def test_run_no_transcript_is_failure() -> None:
    out = _plugin(_GOOD_JSON).run({"transcript": "  "})
    assert out["confidence_hint"] == 0.0


def test_run_provider_exception_is_caught() -> None:
    def _boom(_m):
        raise RuntimeError("down")

    out = RequirementsExtractorPlugin(intel_call=_boom).run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "intel call failed" in out["summary"]


def test_extract_returns_none_without_recognizable_key() -> None:
    assert _extract_requirements('{"foo": 1}') is None
    assert _extract_requirements("") is None
    assert _extract_requirements("[1,2,3]") is None


def test_normalize_type_synonyms() -> None:
    assert _normalize_type("non-functional") == "non_functional"
    assert _normalize_type("NFR") == "non_functional"
    assert _normalize_type("acceptance criteria") == "acceptance"
    assert _normalize_type("constraints") == "constraint"
    assert _normalize_type(None) == "functional"


def test_registrar_returns_real_plugin() -> None:
    host = PluginHost(default_timeout_seconds=0.5, enabled_capabilities={"llm"})
    register_builtin_plugins(host)
    assert isinstance(host.get_plugin("requirements_extractor"), RequirementsExtractorPlugin)


def test_host_blocks_without_llm_capability() -> None:
    host = PluginHost(default_timeout_seconds=0.5)
    register_builtin_plugins(host)
    result = host.execute(
        "requirements_extractor",
        context={"transcript": "The system must do things."},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="abc",
    )
    assert result.status == "blocked"
    assert result.error == "Missing capabilities: llm"
