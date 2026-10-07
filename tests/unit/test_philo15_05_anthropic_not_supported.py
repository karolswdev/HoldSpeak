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
from tests.unit.test_model_library_providers import OWNER, _draft, _library, _row


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
    service.connect_hosted_model(
        OWNER, _draft(request_id="anthropic-1", profile_id="anthropic-main", provider_family="anthropic"),
        {"value": "anthropic-key"},
    )
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
