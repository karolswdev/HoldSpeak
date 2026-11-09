"""HS-130-06 — the target id selects the placement and a run never silently
hops to another destination by model name. Since the engine door (2026-11-08)
an answer takes no target selector at all; the unrouted Thought
(``thought.interview``) is the one caller that still names a target."""
from __future__ import annotations

import asyncio

import pytest

from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "owner")
from holdspeak.services.ask_service import AskService
from holdspeak.services.errors import ServiceError, ValidationError


class _FakeIntel:
    active_provider = "openai_compatible"

    def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
        return "ok"


@pytest.fixture
def rig(tmp_path, monkeypatch):
    db = Database(tmp_path / "ask_retarget.db")
    # A private-LAN destination (boundary: private_network) advertising model-a.
    db.profiles.upsert(profile_id="prof_a", name="Alpha", kind="openAICompatible",
                       base_url="http://192.168.1.50:8080", model="model-a", requires_key=False)
    # An external-service destination (boundary: cloud) advertising model-b.
    db.profiles.upsert(profile_id="prof_b", name="Beta", kind="openAICompatible",
                       base_url="https://api.example.com/v1", model="model-b", requires_key=False)
    # A second private endpoint serving the SAME model name as prof_a.
    db.profiles.upsert(profile_id="prof_c", name="Gamma", kind="openAICompatible",
                       base_url="http://192.168.1.51:8080", model="model-a", requires_key=False)
    # The admitted runner loads engines from the frozen deployment revision.
    # Targeting is the behavior here, so its runner seam supplies a test engine.
    broker = _configure(db)
    monkeypatch.setattr(broker.inference_runner, "_engine_factory", lambda revision, **_kw: _FakeIntel())
    return AskService(db, hub_model=lambda: "", broker=broker)


def _ask(service, **kw):
    kw.setdefault("operation_capability", "thought.interview")
    return asyncio.run(service.ask(OWNER, "summarize", **kw))



def test_an_answer_takes_no_target_or_model_selector(rig) -> None:
    for selector in ({"inference_target_id": "prof_a"}, {"model": "model-b"}, {"profile_id": "prof_b"}):
        with pytest.raises(ValidationError) as exc:
            _ask(rig, operation_capability="ask.answer", **selector)
        assert exc.value.code == "inference_legacy_selector_retired"



def test_list_models_does_not_dedupe_across_destinations(rig) -> None:
    rows = rig.list_models(OWNER)
    ids = {r["id"] for r in rows}
    assert {"prof_a", "prof_b", "prof_c"} <= ids
    # prof_a and prof_c serve the SAME model name yet BOTH appear, distinct by id.
    same_name = [r for r in rows if r["name"] == "model-a"]
    assert {r["id"] for r in same_name} == {"prof_a", "prof_c"}


def test_hub_row_carries_its_id(tmp_path, monkeypatch) -> None:
    # Listing destinations builds no engine at all — HS-131-13 removed the
    # vestigial `build_intel_for_target` patch this test used to carry (the
    # factory is gone, and listing never reached it in the first place).
    db = Database(tmp_path / "ask_hub.db")
    service = AskService(db, hub_model=lambda: "hub-model")
    rows = service.list_models(OWNER)
    hub = [r for r in rows if r["source"] == "hub"]
    assert len(hub) == 1 and hub[0]["id"] == "this_machine"
