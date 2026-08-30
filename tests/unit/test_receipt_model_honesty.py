"""HS-132-09 — the receipt names what LOADED (the executable honesty fence).

The last surviving instance of the issue-#450 defect class: with
``intel_provider='cloud'`` and a local realtime model, an Ask on ``this_machine``
executed the local GGUF while the receipt, the Ask footer, and the hub's
advertised manifest all printed the cloud model id. The chain had four links and
every one of them is fenced here:

1. ``MeetingIntel`` defined neither ``active_model`` nor ``model``, so the
   canonical prompt adapter's executed-model report was ALWAYS ``''``.
2. With nothing reported, Ask and Recipe chat fell back to ``_hub_model_name`` —
   a describer of the CONFIGURED MEETING placement, which answers a different
   question from "what does the destination this run resolved to load".
3. The no-retarget refusal compared the user's ``model`` against that same
   foreign name, so naming the model the device genuinely runs was REFUSED.
4. The manifest row advertised to paired devices came from the same describer.

So this module asserts ONE equality per destination kind:

    readiness-model == executed-model == receipt-model == advertised-model

* **readiness-model** — the deployment identity readiness checked
  (``target.deployment.model``), and the immutable revision admission froze.
* **executed-model** — what the engine the ADMITTED path built reports having
  loaded (``active_model``), through the real factory and a doubled SDK seam.
* **receipt-model** — ``result["model"]`` and ``actual_placement["model"]`` from
  a REAL ``AskService.ask`` turn.
* **advertised-model** — the public picker row (``GET /api/models``) for that
  destination, and the hub manifest row for the hub-default cloud leg.

The physical leaves are doubled at the lowest possible seam (``holdspeak.intel``'s
``Llama``/``OpenAI`` import head, and the mesh relay's queue-and-wait verb), so
everything ABOVE them — placement, admission, the frozen revision, the engine
factory, the adapter, the projection, the receipt — is the production body.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, NamedTuple

import pytest

import holdspeak.db as hsdb
import holdspeak.intel as intel_pkg
from holdspeak.db import Database, reset_database
from holdspeak.deployment_revisions import capture_deployment_revision
from holdspeak.inference_targets import (
    build_intel_for_revision,
    hub_default_cloud_deployment,
    paired_device_target,
    resolve_inference_target,
)
from holdspeak.intel.models import (
    DEFAULT_INTEL_CLOUD_API_KEY_ENV,
    DEFAULT_INTEL_CLOUD_MODEL,
)
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.ask_service import AskService
from holdspeak.services.errors import ValidationError
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.sync_service import _hub_model_name
from tests.unit.admitted_context import admitted_context

OWNER = Principal(PrincipalKind.OWNER, "owner")
ANSWER = "PRINTED"

#: Every model name the doubled SDK seams were actually asked to run. The wire
#: is the last word on what executed, so the fence compares receipts against it.
WIRE: list[str] = []


class _FakeLlama:
    """The llama.cpp seam: it knows ONLY the path it was handed."""

    def __init__(self, *, model_path: str, **_kw: Any) -> None:
        self.model_path = model_path
        WIRE.append(Path(model_path).stem)

    def create_chat_completion(self, **_kw: Any) -> dict[str, Any]:
        return {"choices": [{"message": {"content": ANSWER}}]}


class _FakeOpenAI:
    """The OpenAI-compatible seam: it records the model each request names."""

    def __init__(self, **_kw: Any) -> None:
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    @staticmethod
    def _create(**kwargs: Any) -> Any:
        WIRE.append(str(kwargs.get("model") or ""))
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=ANSWER))]
        )


class Leg(NamedTuple):
    """One destination kind: how to build it, and the ONE model it must name."""

    id: str
    setup: Callable[..., tuple[str, str]]  # (db, tmp_path, monkeypatch) -> (target_id, model)


def _hub_local(db: Any, tmp_path: Path, monkeypatch: Any) -> tuple[str, str]:
    model = tmp_path / "Hub-Local-8B.gguf"
    model.touch()
    _pin_local_meeting_model(monkeypatch, model)
    return "this_machine", "Hub-Local-8B"


def _on_device(db: Any, tmp_path: Path, monkeypatch: Any) -> tuple[str, str]:
    profile_model = tmp_path / "Studio-4B.gguf"
    profile_model.touch()
    # The GLOBAL meeting model is a different file: a run that re-reads live
    # config instead of its frozen revision loads THIS one and is caught.
    other = tmp_path / "Global-Other-9B.gguf"
    other.touch()
    _pin_local_meeting_model(monkeypatch, other)
    db.profiles.upsert(
        profile_id="studio", name="Studio", kind="onDevice",
        model_file=str(profile_model),
    )
    return "studio", "Studio-4B"


def _openai_compatible(db: Any, tmp_path: Path, monkeypatch: Any) -> tuple[str, str]:
    db.profiles.upsert(
        profile_id="lan", name="LAN box", kind="openAICompatible",
        base_url="http://192.168.1.43:8080/v1", model="Qwen3.5-9B-Q6_K",
    )
    return "lan", "Qwen3.5-9B-Q6_K"


def _mesh_node(db: Any, tmp_path: Path, monkeypatch: Any) -> tuple[str, str]:
    db.profiles.upsert(
        profile_id="edge", name="Walk edge", kind="meshNode",
        node="walk-edge", model="qwen3.5-4b",
    )
    db.mesh_relay.touch_worker("walk-edge")
    # The relay's queue-and-wait verb is the physical leaf (a node, a pairing,
    # and a polling worker live past it). Everything the fence measures —
    # placement, revision, `active_model`, the receipt — is above it.
    monkeypatch.setattr(
        "holdspeak.intel.mesh_relay.MeshRelayIntel.run_prompt",
        lambda self, **_kw: WIRE.append(self.active_model) or ANSWER,
    )
    return "edge", "qwen3.5-4b"


LEGS: tuple[Leg, ...] = (
    Leg("this_machine", _hub_local),
    Leg("onDevice", _on_device),
    Leg("openAICompatible", _openai_compatible),
    Leg("meshNode", _mesh_node),
)


def _pin_local_meeting_model(monkeypatch: Any, model: Path) -> None:
    """Configure the hub's local meeting model — the ONE seam every describer reads."""
    monkeypatch.setattr(
        "holdspeak.intel.providers.configured_local_meeting_model_path",
        lambda: str(model),
    )


def _meeting_config(**overrides: Any) -> Any:
    from holdspeak.config import Config, MeetingConfig

    config = Config()
    config.meeting = MeetingConfig(**overrides)
    return config


@pytest.fixture
def rig(tmp_path, monkeypatch):
    reset_database()
    WIRE.clear()
    db = Database(tmp_path / "receipt-honesty.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    # The SDK import head — the LOWEST seam. Both providers load for real above it.
    monkeypatch.setattr(intel_pkg, "Llama", _FakeLlama)
    monkeypatch.setattr(intel_pkg, "OpenAI", _FakeOpenAI)
    broker = _configure(db)
    yield db, broker
    reset_database()


def _ask(db: Any, broker: Any, **kwargs: Any) -> dict[str, Any]:
    """One REAL Ask turn: placement, admission, dispatch, projection, receipt."""
    service = AskService(db, broker=broker)
    return asyncio.run(service.ask(OWNER, "state of play", **kwargs))


def _advertised(db: Any, broker: Any, target_id: str) -> str:
    """What the picker advertises for this destination (GET /api/models)."""
    rows = {row["id"]: row["name"] for row in AskService(db, broker=broker).list_models(OWNER)}
    return rows[target_id]


def _executed_model(engine: Any) -> str:
    """What the engine the ADMITTED path built reports having loaded."""
    load = getattr(engine, "_ensure_model_loaded", None)
    if load is not None:
        load()  # through the doubled SDK seam; nothing physical is warmed
    return str(getattr(engine, "active_model", ""))


def _assert_one_model(db: Any, broker: Any, target_id: str, expected: str) -> None:
    """The fence proper: four independent readings, one model name."""
    target = resolve_inference_target(db, target_id)
    assert target.ready, target.readiness_reason
    readiness = target.deployment.model

    revision = capture_deployment_revision(db, target)
    engine = build_intel_for_revision(
        revision, context=admitted_context(revision=revision)
    )
    executed = _executed_model(engine)

    result = _ask(db, broker, inference_target_id=target_id)
    receipt = result["actual_placement"]

    assert readiness == expected, f"readiness names {readiness!r}"
    assert revision.model == expected, f"the frozen revision names {revision.model!r}"
    assert executed == expected, f"the engine loaded {executed!r}"
    assert result["model"] == expected, f"the result names {result['model']!r}"
    assert receipt["model"] == expected, f"the receipt names {receipt['model']!r}"
    assert _advertised(db, broker, target_id) == expected
    assert WIRE and WIRE[-1] == expected, f"the wire ran {WIRE[-1:]!r}"


@pytest.mark.parametrize("leg", LEGS, ids=[leg.id for leg in LEGS])
def test_readiness_execution_receipt_and_advertisement_name_one_model(
    leg, rig, tmp_path, monkeypatch
) -> None:
    db, broker = rig
    target_id, expected = leg.setup(db, tmp_path, monkeypatch)
    _assert_one_model(db, broker, target_id, expected)


def test_the_fence_fails_on_an_injected_divergence(rig, tmp_path, monkeypatch) -> None:
    """A run that loads something its revision never named FAILS this fence.

    The injection is the pre-HS-131-13 shape of the bug: the same-device factory
    building an engine on a model the frozen revision does not name. The engine
    now REPORTS what it loaded, so the divergence surfaces in the receipt instead
    of hiding behind a hub-side describer.
    """
    db, broker = rig
    target_id, expected = _hub_local(db, tmp_path, monkeypatch)
    _assert_one_model(db, broker, target_id, expected)  # honest first

    imposter = tmp_path / "Imposter-70B.gguf"
    imposter.touch()
    from holdspeak.intel.engine import MeetingIntel

    monkeypatch.setattr(
        "holdspeak.inference_targets._local_pinned_engine",
        lambda model_path=None, *, context=None, revision=None: MeetingIntel(
            provider="local", model_path=str(imposter)
        ),
    )
    with pytest.raises(AssertionError, match=r"the engine loaded 'Imposter-70B'"):
        _assert_one_model(db, broker, target_id, expected)

    # ...and the divergence is VISIBLE, not swallowed: the receipt names the
    # model that actually loaded, which is exactly what makes the fence bite.
    diverged = _ask(db, broker, inference_target_id=target_id)
    assert diverged["model"] == "Imposter-70B" != expected
    assert diverged["actual_placement"]["model"] == "Imposter-70B"


def test_hub_default_cloud_leg_names_one_model(rig, tmp_path, monkeypatch) -> None:
    """The fifth destination: the hub-default cloud leg (HS-131-08).

    It is not Ask-addressable, so its advertised surface is the manifest row a
    paired device reads. Readiness, the frozen revision, the engine, and that row
    still name ONE model.
    """
    db, broker = rig
    local = tmp_path / "Hub-Local-8B.gguf"
    local.touch()
    monkeypatch.setenv(DEFAULT_INTEL_CLOUD_API_KEY_ENV, "sk-fence")
    monkeypatch.setattr(
        "holdspeak.config.Config.load",
        classmethod(lambda cls, path=None: _meeting_config(
            intel_enabled=True, intel_provider="cloud",
            intel_realtime_model=str(local),
        )),
    )

    from holdspeak.intel.providers import effective_intel_cloud

    meeting = _meeting_config(
        intel_enabled=True, intel_provider="cloud", intel_realtime_model=str(local)
    ).meeting
    identity = hub_default_cloud_deployment(effective_intel_cloud(meeting))
    revision = capture_deployment_revision(db, identity)
    engine = build_intel_for_revision(
        revision, context=admitted_context(revision=revision)
    )

    assert identity.model == DEFAULT_INTEL_CLOUD_MODEL
    assert revision.model == DEFAULT_INTEL_CLOUD_MODEL
    assert _executed_model(engine) == DEFAULT_INTEL_CLOUD_MODEL
    # The advertised row (what a paired device is told the desktop loads).
    assert _hub_model_name(None) == DEFAULT_INTEL_CLOUD_MODEL


def test_cloud_provider_with_a_local_model_keeps_this_machine_honest(
    rig, tmp_path, monkeypatch
) -> None:
    """The audit's live reproduction, now fenced.

    ``intel_provider='cloud'`` with a local realtime model. The desktop's
    configured MEETING deployment is the cloud leg — and an Ask on
    ``this_machine`` is pinned LOCAL and must say so, in the receipt, in the
    footer payload, and in the picker row. Before HS-132-09 all three printed the
    cloud model id.
    """
    db, broker = rig
    local = tmp_path / "Hub-Local-8B.gguf"
    local.touch()
    monkeypatch.setenv(DEFAULT_INTEL_CLOUD_API_KEY_ENV, "sk-fence")
    monkeypatch.setattr(
        "holdspeak.config.Config.load",
        classmethod(lambda cls, path=None: _meeting_config(
            intel_enabled=True, intel_provider="cloud",
            intel_realtime_model=str(local),
        )),
    )

    # The hub's own configured placement really is the cloud leg...
    assert _hub_model_name(None) == DEFAULT_INTEL_CLOUD_MODEL
    # ...and `this_machine` still names, runs, and receipts the LOCAL model.
    _assert_one_model(db, broker, "this_machine", "Hub-Local-8B")

    result = _ask(db, broker, inference_target_id="this_machine")
    assert result["model"] != DEFAULT_INTEL_CLOUD_MODEL
    assert result["egress"] == {"scope": "local"}


def test_naming_the_genuinely_loaded_model_is_accepted(rig, tmp_path, monkeypatch) -> None:
    """A user naming the model the destination really runs is ACCEPTED, and the
    refusal for any other name quotes the TRUE model (never a foreign describer)."""
    db, broker = rig
    local = tmp_path / "Hub-Local-8B.gguf"
    local.touch()
    monkeypatch.setenv(DEFAULT_INTEL_CLOUD_API_KEY_ENV, "sk-fence")
    monkeypatch.setattr(
        "holdspeak.config.Config.load",
        classmethod(lambda cls, path=None: _meeting_config(
            intel_enabled=True, intel_provider="cloud",
            intel_realtime_model=str(local),
        )),
    )

    accepted = _ask(db, broker, inference_target_id="this_machine", model="Hub-Local-8B")
    assert accepted["model"] == "Hub-Local-8B"

    with pytest.raises(ValidationError) as exc:
        _ask(db, broker, inference_target_id="this_machine", model=DEFAULT_INTEL_CLOUD_MODEL)
    message = str(exc.value)
    assert "Hub-Local-8B" in message
    assert exc.value.context["available_models"] == ["Hub-Local-8B"]


# HS-150-04: test_recipe_run_and_chat_agree_on_the_model DELETED —
# recipe.chat retired; model honesty is proven by recipe.run alone.


def test_manifest_row_equals_what_the_paired_device_would_load(
    rig, tmp_path, monkeypatch
) -> None:
    """The manifest row a paired device reads == the paired deployment's model,
    in BOTH mismatch directions of the old ``intel_provider``-only describer."""
    db, broker = rig
    local = tmp_path / "Hub-Local-8B.gguf"
    local.touch()

    from holdspeak.db.models import ProfileRecord

    # Direction 1: provider says "local", but an ADOPTED endpoint destination
    # won the placement. The old describer answered the local GGUF stem.
    monkeypatch.setattr(
        "holdspeak.intel.providers._lookup_profile_record",
        lambda pid: ProfileRecord(
            id=pid, name="LAN box", kind="openAICompatible",
            base_url="http://192.168.1.43:8080/v1", model="Qwen3.5-9B-Q6_K",
        ),
    )
    monkeypatch.setattr(
        "holdspeak.config.Config.load",
        classmethod(lambda cls, path=None: _meeting_config(
            intel_enabled=True, intel_provider="local", intel_profile_id="p-lan",
            intel_realtime_model=str(local),
        )),
    )
    assert _hub_model_name(None) == "Qwen3.5-9B-Q6_K" == paired_device_target().model

    # Direction 2: provider says "cloud" with a key, so the desktop really would
    # load the cloud leg — and the row agrees with the paired target, which is
    # what the paired device's own readiness and receipt use.
    monkeypatch.setattr(
        "holdspeak.intel.providers._lookup_profile_record", lambda pid: None
    )
    monkeypatch.setenv(DEFAULT_INTEL_CLOUD_API_KEY_ENV, "sk-fence")
    monkeypatch.setattr(
        "holdspeak.config.Config.load",
        classmethod(lambda cls, path=None: _meeting_config(
            intel_enabled=True, intel_provider="cloud",
            intel_realtime_model=str(local),
        )),
    )
    assert _hub_model_name(None) == DEFAULT_INTEL_CLOUD_MODEL == paired_device_target().model

    # Intelligence off: the hub advertises no model at all.
    monkeypatch.setattr(
        "holdspeak.config.Config.load",
        classmethod(lambda cls, path=None: _meeting_config(intel_enabled=False)),
    )
    assert _hub_model_name(None) == ""


def test_on_device_with_no_model_file_refuses_by_name(rig, tmp_path) -> None:
    """The latent sibling (HS-131-13's shape): a blank ``model_file`` used to
    fall back to the GLOBAL meeting model — an admitted child loading a model its
    revision never named. It refuses BY NAME instead."""
    from holdspeak.inference_targets import LOCAL_DEPLOYMENT_MODEL_UNKNOWN
    from holdspeak.intel.providers import build_meeting_intel_for_profile
    from holdspeak.kernel.model import KernelRefused

    db, _broker = rig
    revision = SimpleNamespace(id="dep_blank", destination_id="blank")
    with pytest.raises(KernelRefused) as exc:
        build_meeting_intel_for_profile(
            kind="onDevice", base_url=None, model="", profile_id="blank",
            model_file="", deployment_revision=revision,
            context=admitted_context(revision=revision),
        )
    assert LOCAL_DEPLOYMENT_MODEL_UNKNOWN in str(exc.value)
