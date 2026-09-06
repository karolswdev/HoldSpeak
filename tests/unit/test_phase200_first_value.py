"""HS-200-04 — first value is independent of model readiness.

The product's first promise is a sentence you can edit, copy and keep. It must
hold on a machine with no LLM configured and no model file, and it must hold
while the setup verdict says `needs_attention` or `blocked` — those words are
about later work, not about this sentence.

These are the state-level fences. The cold end-to-end journey lives in
`tests/critical/test_journey_first_sentence_cold.py`; the browser-facing half
(the composer, Copy and Keep are never disabled by readiness) lives in the web
suite.
"""

from __future__ import annotations

from typing import Any

import pytest

import holdspeak.config as config_module
from holdspeak import setup_status
from holdspeak.commands.doctor import DoctorCheck
from holdspeak.config import Config


@pytest.fixture
def cold_config(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A default configuration on a fresh machine: nothing configured."""
    monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")


def _Check(name: str, status: str, detail: str = "", fix: str | None = None) -> DoctorCheck:
    return DoctorCheck(name=name, status=status.upper(), detail=detail, fix=fix)


def _status(monkeypatch: pytest.MonkeyPatch, checks: list[DoctorCheck]) -> dict[str, Any]:
    monkeypatch.setattr(
        "holdspeak.commands.doctor.collect_doctor_checks",
        lambda **_kwargs: checks,
    )
    return setup_status.build_setup_status(database=None, config=Config())


def test_a_warning_verdict_does_not_withhold_the_first_sentence(
    cold_config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`needs_attention` is a repair list, never a gate on arrival."""
    status = _status(
        monkeypatch,
        [
            _Check("Runtime profiles", "warn", "requires a key", fix="Set the key"),
            _Check("Microphone", "pass"),
        ],
    )
    assert status["overall"] == "needs_attention"
    # First value is still owed and still offered.
    assert status["first_run"] is True
    assert status["arrival_required"] is True


def test_even_a_blocked_verdict_does_not_withhold_the_first_sentence(
    cold_config, monkeypatch: pytest.MonkeyPatch
) -> None:
    status = _status(
        monkeypatch,
        [_Check("Dictation runtime", "fail", "no model", fix="Choose a model")],
    )
    assert status["overall"] == "blocked"
    assert status["arrival_required"] is True


def test_the_primary_action_names_the_repair_and_not_a_diagnosis(
    cold_config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The single next step is the section's own fix, in its own words."""
    status = _status(
        monkeypatch,
        [
            _Check("Microphone", "pass"),
            _Check("Runtime profiles", "warn", "key unset", fix="Set the key"),
            _Check("Dictation runtime", "fail", "no model", fix="Choose a model"),
        ],
    )
    action = status["primary_action"]
    assert action is not None
    # The FAIL outranks the WARN, and the action is the fix, not the label.
    assert action["label"] == "Choose a model"


def test_a_ready_verdict_offers_the_first_dictation_itself(
    cold_config, monkeypatch: pytest.MonkeyPatch
) -> None:
    status = _status(monkeypatch, [_Check("Microphone", "pass")])
    assert status["overall"] == "ready"
    assert status["primary_action"]["id"] == "first_dictation"


def test_keeping_a_first_sentence_never_resolves_an_inference_target(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The fence, asserted rather than believed.

    Every inference entry point raises for the length of this test. If a future
    change routes the first kept sentence through a model, this fails here
    instead of failing on every machine that has no model file.
    """
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    import holdspeak.inference_targets as inference_targets
    from holdspeak.db import get_database, reset_database

    home = tmp_path / "home"
    (home / ".config" / "holdspeak").mkdir(parents=True)
    (home / ".local" / "share" / "holdspeak").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(
        config_module, "CONFIG_FILE", home / ".config" / "holdspeak" / "config.json"
    )
    monkeypatch.setattr(
        db_core, "DEFAULT_DB_PATH", home / ".local" / "share" / "holdspeak" / "holdspeak.db"
    )

    def _forbidden(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("first value must not resolve an inference target")

    monkeypatch.setattr(inference_targets, "resolve_inference_target", _forbidden)
    monkeypatch.setattr(inference_targets, "this_machine_target", _forbidden)
    monkeypatch.setattr(inference_targets, "list_inference_targets", _forbidden)

    reset_database()
    try:
        db = get_database(home / ".local" / "share" / "holdspeak" / "holdspeak.db")
        entry = db.dictation_journal.record(
            source="dictation",
            transcript="the postgress migration lands on friday",
            final_text="the postgres migration lands on friday",
            total_ms=90.0,
        )
        assert entry.id
        note = db.notes.upsert(
            note_id="note_first_value",
            title="First sentence",
            body_markdown="the postgres migration lands on friday",
        )
        assert note.id == "note_first_value"
        assert db.dictation_journal.count() >= 1
    finally:
        reset_database()
