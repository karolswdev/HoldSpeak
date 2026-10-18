"""Betterment E4: Add an engine, by kind (hub half, units).

The named service tiles and their catalog presets (``service_tiles``), and
Anthropic through its OpenAI-compatible endpoint (DECISIONS #9): its
``/models`` read sends the key the way Anthropic reads it, and a hosted
connect is let in only when that read answers. No real API is called: every
wire is a stub ``http_get`` or a stubbed ``discover_endpoint_models``.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from holdspeak.inference_setup_catalog import packaged_catalog_envelope_json, verify_catalog_envelope
from holdspeak.services.concierge_service import STATE_READY, probe, service_tiles
from holdspeak.services.errors import ServiceError
from holdspeak.setup_runtime import discover_endpoint_models
from tests.unit.test_model_library_providers import OWNER, _draft, _library, _row


def _entries() -> list:
    from datetime import datetime, timezone

    return verify_catalog_envelope(packaged_catalog_envelope_json(), now=datetime.now(timezone.utc))["entries"]


def test_the_four_services_carry_their_address_and_openrouter_its_presets() -> None:
    tiles = service_tiles(_entries())
    assert [(t["id"], t["name"], t["host"]) for t in tiles] == [
        ("openrouter", "OpenRouter", "openrouter.ai"),
        ("openai", "OpenAI", "api.openai.com"),
        ("anthropic", "Anthropic", "api.anthropic.com"),
        ("gemini", "Gemini", "generativelanguage.googleapis.com"),
    ]
    openrouter = tiles[0]
    assert [p["model"] for p in openrouter["presets"]] == [
        "qwen/qwen3-8b", "qwen/qwen3.5-35b-a3b", "qwen/qwen3.8-27b",
        "qwen/qwen3.7-flash", "google/gemma-4-26b-a4b-it", "qwen/qwen3-coder-next",
    ]
    assert all(p["label"].startswith("OpenRouter · ") for p in openrouter["presets"])
    assert all(not t["presets"] for t in tiles[1:])


def _capture(rows: list[dict]):
    seen: list[tuple[str, dict]] = []

    def http_get(url: str, *, headers: dict, timeout: float):
        seen.append((url, dict(headers)))
        return 200, json.dumps({"data": rows}).encode()

    return seen, http_get


def test_anthropic_models_read_sends_the_key_as_anthropic_reads_it() -> None:
    seen, http_get = _capture([{"id": "claude-x", "type": "model", "display_name": "Claude X"}])
    answer = discover_endpoint_models("https://api.anthropic.com/v1", api_key="sk-ant-stub", http_get=http_get)
    assert answer["ok"] is True and answer["models"] == ["claude-x"], answer
    ((url, headers),) = seen
    assert url == "https://api.anthropic.com/v1/models?limit=1000"
    assert headers["x-api-key"] == "sk-ant-stub"
    assert headers["anthropic-version"] == "2023-06-01"
    assert headers["Authorization"] == "Bearer sk-ant-stub"


def test_another_host_gets_only_the_bearer_key() -> None:
    seen, http_get = _capture([{"id": "m"}])
    discover_endpoint_models("https://openrouter.ai/api/v1", api_key="sk-or", http_get=http_get)
    ((url, headers),) = seen
    assert url == "https://openrouter.ai/api/v1/models"
    assert headers == {"Accept": "application/json", "Authorization": "Bearer sk-or"}


def test_the_anthropic_probe_is_a_cloud_key_check_not_a_dead_end() -> None:
    engine = {"id": "cloud:anthropic", "kind": "cloud", "host": "api.anthropic.com", "keySet": True}
    assert probe(engine=engine, generate=False)["state"] == STATE_READY


def test_anthropic_connects_only_when_its_models_answer(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    asked: list[tuple[str, str | None]] = []

    def models(base_url: str, *, api_key: str | None = None, **_kw):
        asked.append((base_url, api_key))
        return {"ok": api_key == "good-key", "models": ["claude-x"] if api_key == "good-key" else []}

    monkeypatch.setattr("holdspeak.setup_runtime.discover_endpoint_models", models)
    service = _library(tmp_path)
    before = service.get_library(OWNER)["rows"]
    with pytest.raises(ServiceError) as refused:
        service.connect_hosted_model(
            OWNER, _draft(request_id="anthropic-bad", profile_id="anthropic-bad", provider_family="anthropic"),
            {"value": "bad-key"},
        )
    assert refused.value.code == "anthropic_models_check_failed" and refused.value.context["status"] == 422
    assert "bad-key" not in str(refused.value) and "bad-key" not in json.dumps(refused.value.context)
    assert service.get_library(OWNER)["rows"] == before

    service.connect_hosted_model(
        OWNER, _draft(request_id="anthropic-good", profile_id="anthropic-good", provider_family="anthropic"),
        {"value": "good-key"},
    )
    assert asked[0] == ("https://api.anthropic.com/v1", "bad-key")
    assert ("https://api.anthropic.com/v1", "good-key") in asked
    row = _row(service, "anthropic-good")
    assert row["selected_action"] == "Ready" and row["status"] != "not_supported", row
