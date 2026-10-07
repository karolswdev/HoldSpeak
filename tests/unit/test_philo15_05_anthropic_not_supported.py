"""PHILO-15 lane 05, ruling 3 (inventory gap 5, honesty): an Anthropic key
does nothing today, so no face may read it as if it worked.

There is no Anthropic execution adapter. The Model Library's readiness for
the family is ``not_supported`` (was ``anthropic_runtime_missing``), its row
reads NOT SUPPORTED YET as a state (not a repair, not "broken"), and the
Concierge's api.anthropic.com row reads NOT_SUPPORTED, never READY, even with
a key held. The adapter is a queued Phase 15 item.

Real producers: the real Model Library service over a real database with
real key custody; the real Concierge ``probe``.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.services.concierge_service import STATE_NOT_SUPPORTED, probe
from holdspeak.services.model_library_service import (
    NOT_SUPPORTED,
    NOT_SUPPORTED_LABEL,
    ModelLibraryApplicationService,
)
from holdspeak.services.errors import ServiceError
from tests.unit.test_model_library_providers import OWNER, _draft, _library, _row, store_stored_anthropic


def test_readiness_for_anthropic_is_not_supported() -> None:
    reason = ModelLibraryApplicationService._provider_readiness_reason
    assert reason("anthropic") == NOT_SUPPORTED == "not_supported"
    assert reason("openrouter") is None and reason("openai_compatible") is None


def test_an_anthropic_row_reads_not_supported_yet_even_with_a_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "holdspeak.setup_runtime.discover_endpoint_models",
        lambda *_args, **_kwargs: {"ok": True, "models": ["fixture"]},
    )
    service = _library(tmp_path, store_path=tmp_path / "keys.json")
    # A profile an older desk stored before the service refused the family.
    store_stored_anthropic(service, monkeypatch, request_id="anthropic-1", profile_id="anthropic-main")
    row = _row(service, "anthropic-main")
    assert row["status"] == "not_supported"
    assert row["selected_action"] == NOT_SUPPORTED_LABEL == "NOT SUPPORTED YET"
    assert row["repair"] is None  # nothing to repair until an adapter exists
    with service._db._connection() as conn:
        reasons = {r["reason_code"] for r in conn.execute(
            "SELECT reason_code FROM model_profile_readiness_observations"
        ).fetchall()}
    assert "not_supported" in reasons and "anthropic_runtime_missing" not in reasons


@pytest.mark.parametrize("key_set", [True, False])
def test_the_concierge_anthropic_row_is_never_ready(key_set: bool) -> None:
    calls: list[str] = []
    engine = {"id": "cloud:anthropic", "kind": "cloud", "host": "api.anthropic.com", "keySet": key_set}
    for generate in (False, True):
        result = probe(
            engine=engine, generate=generate,
            http_get=lambda *_a, **_k: (calls.append("net"), (200, b"{}"))[1],
        )
        assert result["state"] == STATE_NOT_SUPPORTED == "NOT_SUPPORTED"
    assert calls == []  # no spend, no request


def test_connecting_anthropic_is_refused_and_stores_nothing(tmp_path: Path) -> None:
    """Astra r1 (#975): HTTP and MCP get the form's honest answer."""
    keys = tmp_path / "keys.json"
    service = _library(tmp_path, store_path=keys)
    before = service.get_library(OWNER)
    with pytest.raises(ServiceError) as refused:
        service.connect_hosted_model(
            OWNER, _draft(request_id="anthropic-refused", profile_id="anthropic-refused", provider_family="anthropic"),
            {"value": "anthropic-key-sentinel"},
        )
    assert refused.value.code == "not_supported"
    assert refused.value.context["status"] == 422
    assert "anthropic-key-sentinel" not in str(refused.value)
    # Nothing stored: no profile row, no key, no command reservation.
    assert service.get_library(OWNER)["rows"] == before["rows"]
    assert not keys.exists() or "anthropic-key-sentinel" not in keys.read_text()
    with service._db._connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM model_library_provider_commands WHERE request_id=?", ("anthropic-refused",)
        ).fetchone()[0] == 0


def test_a_library_with_nothing_ready_does_not_say_ready(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """Astra r1 (#975) P2: an unsupported-only library said Ready."""
    service = _library(tmp_path, store_path=tmp_path / "keys.json")
    store_stored_anthropic(service, monkeypatch, request_id="anthropic-only", profile_id="anthropic-only")
    stored = [r for r in service.get_library(OWNER)["rows"] if r["source"] != "catalog"]
    monkeypatch.setattr(service, "_rows", lambda *_: stored)
    summary = service.get_library(OWNER)["summary"]
    assert summary == {
        "state": "none_ready", "label": "NOT SUPPORTED YET", "ready_count": 0, "attention_count": 0,
    }
    # Catalog rows only (nothing added yet): not Ready either.
    monkeypatch.setattr(service, "_rows", lambda *_: [
        {"id": "catalog:x", "source": "catalog", "label": "X", "status": "available",
         "detail": {}, "repair": None, "selected_action": "Download"},
    ])
    assert service.get_library(OWNER)["summary"]["state"] == "none_ready"
    assert service.get_library(OWNER)["summary"]["label"] == "Add model"
