"""HS-29-01: the real dependency_mapper plugin."""

from __future__ import annotations

from holdspeak.plugins.builtin import register_builtin_plugins
from holdspeak.plugins.builtin.dependency_mapper import (
    DependencyMapperPlugin,
    _extract_dependencies,
)
from holdspeak.plugins.host import PluginHost

_GOOD_JSON = """```json
{"dependencies": [
  {"from": "Billing", "to": "API freeze", "note": "needs the contract locked"},
  {"from": "GA", "to": "Beta", "note": null}
]}
```"""


def _plugin(response):
    return DependencyMapperPlugin(intel_call=lambda _m: response)


def test_attributes() -> None:
    p = DependencyMapperPlugin()
    assert p.id == "dependency_mapper"
    assert p.kind == "synthesizer"
    assert p.execution_mode == "deferred"
    assert p.required_capabilities == ["llm"]


def test_run_success_maps_edges() -> None:
    out = _plugin(_GOOD_JSON).run({"transcript": "We mapped deps."})
    assert out["confidence_hint"] == 1.0
    assert out["dependencies"][0] == {"from": "Billing", "to": "API freeze", "note": "needs the contract locked"}
    assert out["dependencies"][1]["note"] is None
    assert "2 dependency edge(s)" in out["summary"]


def test_run_edge_without_endpoints_dropped() -> None:
    out = _plugin('{"dependencies": [{"from": "X"}]}').run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "dependencies" not in out


def test_run_empty_is_failure() -> None:
    out = _plugin('{"dependencies": []}').run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "dependencies" not in out


def test_run_unparseable_is_failure() -> None:
    out = _plugin("no json").run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0


def test_run_no_transcript_is_failure() -> None:
    out = _plugin(_GOOD_JSON).run({"transcript": "  "})
    assert out["confidence_hint"] == 0.0


def test_run_provider_exception_is_caught() -> None:
    def _boom(_m):
        raise RuntimeError("down")

    out = DependencyMapperPlugin(intel_call=_boom).run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "intel call failed" in out["summary"]


def test_extract_returns_none_without_recognizable_key() -> None:
    assert _extract_dependencies('{"foo": 1}') is None
    assert _extract_dependencies("") is None


def test_registrar_returns_real_plugin() -> None:
    host = PluginHost(default_timeout_seconds=0.5, enabled_capabilities={"llm"})
    register_builtin_plugins(host)
    assert isinstance(host.get_plugin("dependency_mapper"), DependencyMapperPlugin)


def test_host_blocks_without_llm_capability() -> None:
    host = PluginHost(default_timeout_seconds=0.5)
    register_builtin_plugins(host)
    result = host.execute(
        "dependency_mapper",
        context={"transcript": "deps"},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="abc",
    )
    assert result.status == "blocked"
    assert result.error == "Missing capabilities: llm"
