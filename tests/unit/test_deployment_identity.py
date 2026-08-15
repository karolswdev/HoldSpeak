"""HS-130-03 — One deployment identity: readiness, execution, receipt agree.

Each destination kind resolves ONE deployment identity. Readiness checks whether
THAT deployment loads, execution loads exactly it, and the receipt names exactly
what loaded. These tests pin readiness-model == executed-engine-model ==
receipt-model (and the same destination) for this_machine, a named on-device
profile, and paired_device — and close the on-device A/B split as a regression.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.deployment_revisions import capture_deployment_revision
from holdspeak.inference_targets import (
    build_intel_for_revision,
    paired_device_target,
    resolve_inference_target,
    this_machine_target,
)
from tests.unit.admitted_context import admitted_context


def _admitted_engine(db, target):
    """Build the engine the way an ADMITTED child does (HS-131-13).

    `build_intel_for_target` is gone; the one construction path freezes the
    deployment first and then presents the dispatch context the runner minted for
    that exact revision. Readiness/execution/receipt agreement is therefore now
    asserted against the SAME frozen identity the receipt names.
    """
    revision = capture_deployment_revision(db, target)
    return build_intel_for_revision(revision, context=admitted_context(revision=revision))


def _fake_meeting(model_path: str, *, provider: str = "local") -> SimpleNamespace:
    return SimpleNamespace(
        intel_realtime_model=model_path,
        intel_provider=provider,
        intel_profile_id="",
        intel_cloud_reasoning_effort=None,
        intel_cloud_store=False,
    )


@pytest.fixture
def db(tmp_path, monkeypatch):
    reset_database()
    database = Database(tmp_path / "deploy.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: database)
    yield database
    reset_database()


def test_this_machine_readiness_execution_receipt_name_one_model(
    tmp_path, monkeypatch, db
) -> None:
    model = tmp_path / "hub-intel.gguf"
    model.touch()
    monkeypatch.setattr(
        "holdspeak.config.Config.load",
        lambda: SimpleNamespace(meeting=_fake_meeting(str(model))),
    )

    target = this_machine_target()
    assert target.ready is True

    readiness_path = target.deployment.model_path
    engine = _admitted_engine(db, target)
    executed_path = getattr(engine, "model_path", None)
    receipt = target.placement_receipt(provider="local")

    # readiness-model == executed-engine-model == receipt-model, same destination.
    assert readiness_path == str(model)
    assert executed_path == str(model)
    assert receipt["model"] == model.stem
    assert receipt["target_id"] == target.id == "this_machine"


def test_named_on_device_runs_the_model_that_made_it_ready(
    tmp_path, monkeypatch, db
) -> None:
    """Regression: reports A, runs B, attests A — the on-device A/B split.

    Before HS-130-03 an on-device profile reported ready on its ``model_file``
    but execution fell through the ``this_device`` branch to
    ``build_configured_meeting_intel`` and loaded the GLOBAL meeting model. Now
    execution loads the profile's own model_file — the one readiness checked.
    """
    profile_model = tmp_path / "profile-A.gguf"
    profile_model.touch()
    global_model = tmp_path / "global-B.gguf"
    global_model.touch()
    assert str(profile_model) != str(global_model)

    # Global meeting model is a DIFFERENT file the run must not silently load.
    monkeypatch.setattr(
        "holdspeak.config.Config.load",
        lambda: SimpleNamespace(meeting=_fake_meeting(str(global_model))),
    )
    db.profiles.upsert(
        profile_id="mac", name="This iMac", kind="onDevice",
        model_file=str(profile_model),
    )

    target = resolve_inference_target(db, "mac")
    assert target.ready is True
    assert target.deployment.model_path == str(profile_model)

    engine = _admitted_engine(db, target)
    executed_path = getattr(engine, "model_path", None)
    receipt = target.placement_receipt(provider="local")

    # The run loads the model readiness attested — never the global model.
    assert executed_path == str(profile_model)
    assert executed_path != str(global_model)
    # readiness == execution == receipt, all naming the profile's own model.
    assert target.model == str(profile_model)
    assert receipt["model"] == str(profile_model)
    assert receipt["target_id"] == "mac"


def test_paired_device_cannot_report_ready_when_execution_path_is_unrunnable(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(
        "holdspeak.config.Config.load",
        lambda: SimpleNamespace(meeting=_fake_meeting(str(tmp_path / "gone.gguf"))),
    )
    # The delegated execution path (build_configured_meeting_intel) cannot load.
    monkeypatch.setattr(
        "holdspeak.intel.providers.resolve_intel_provider",
        lambda *a, **k: (None, "Local intel unavailable (no model)"),
    )

    target = paired_device_target()
    assert target.ready is False
    assert "unavailable" in target.readiness_state
    assert target.readiness_reason


def test_paired_device_receipt_names_the_runnable_deployment(
    tmp_path, monkeypatch
) -> None:
    model = tmp_path / "hub.gguf"
    model.touch()
    monkeypatch.setattr(
        "holdspeak.config.Config.load",
        lambda: SimpleNamespace(meeting=_fake_meeting(str(model))),
    )
    monkeypatch.setattr(
        "holdspeak.intel.providers.resolve_intel_provider",
        lambda *a, **k: ("local", None),
    )

    target = paired_device_target()
    assert target.ready is True
    # readiness == execution deployment == receipt, same destination.
    assert target.deployment.model_path == str(model)
    receipt = target.placement_receipt(provider="local")
    assert receipt["model"] == model.stem == target.model
    assert receipt["target_id"] == "paired_device"
