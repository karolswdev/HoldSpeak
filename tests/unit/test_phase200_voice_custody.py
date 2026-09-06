"""HS-200-05 — physical voice capture, correction and custody (seam level).

The story's five acceptance criteria split in two. The physical beats — a real
microphone, the macOS hotkey, a denied permission dialog, a replay and a hub
restart on the attested platform — are the owner's attended walk
(`tests/e2e/live200_voice_walk.py`). Everything a test can carry honestly is
here and in `tests/integration/test_phase200_voice_custody.py`.

What is substituted, and why:

* **the transcriber** — a runner has no microphone and no model file, so the
  speech engine is the one adapter stubbed at the runtime seam
  (`_ensure_transcriber_loaded` / `_frozen_session_transcriber`);
* **the typing adapter** — a test never types into the machine's focused
  window, so `holdspeak.desktop_typing.type_text_from_owner_gesture` is
  replaced by a recorder that captures exactly what the delivery asked for.

Everything between those two ends is the real product: the capture tail
(`runtime/dictation_capture.py`), the voice-command dispatch, the pipeline
delegate, `dictation_runner.process_transcript`, the durable journal recorder
and the correction store's own matcher.
"""

from __future__ import annotations

import threading
from types import SimpleNamespace
from typing import Any, Optional

import numpy as np
import pytest

from holdspeak.config import Config
from holdspeak.db import Database, reset_database
from holdspeak.desktop_typing import DesktopTypeRefused
from holdspeak.plugins.dictation.corrections import (
    Correction,
    CorrectionStore,
    apply_text_corrections,
)
from holdspeak.plugins.dictation.journal import DictationJournalRecorder
from holdspeak.runtime import dictation_capture as capture_module
from holdspeak.runtime.dictation_capture import DictationCaptureMixin

AUDIO = np.zeros(16000, dtype=np.float32)
HEARD = "the postgress migration lands on friday"
SAID = "the postgres migration lands on friday"


# ── the rig: the real hotkey tail with two adapters substituted ──────────────


class _HotkeyRig(DictationCaptureMixin):
    """A runtime ``self`` that runs the REAL hotkey tail end to end.

    Only `_ensure_transcriber_loaded`, `_try_tmux_agent_reply`,
    `_mark_first_dictation`, `_set_runtime_activity` and `_set_voice_state` are
    substituted; `_paste_target_profile`, `_maybe_dispatch_voice_command` and
    `_maybe_run_dictation_pipeline` are the shipped methods.
    """

    def __init__(self, *, journal: Any, transcribe: Any) -> None:
        self.config = Config()
        # The passthrough lane: the REAL `run_pipeline_corrections_only` runs
        # and journals, and nothing reaches a model or a LAN endpoint.
        self.config.dictation.pipeline.enabled = False
        self.transcription_lock = threading.Lock()
        self.state_lock = threading.Lock()
        self.runtime_status: dict[str, Any] = {}
        self.activity: list[dict[str, Any]] = []
        self.first_marked = 0
        self.typer = SimpleNamespace(type_text=lambda *a, **k: None)
        self.text_processor = SimpleNamespace(process=lambda t: t)
        self.dictation_previews: dict[str, Any] = {}
        self._transcribe = transcribe
        self.server = SimpleNamespace(
            dictation_journal=journal,
            dictation_corrections=None,
            dictation_telemetry=None,
            broadcast=lambda *a, **k: None,
        )

    # ── substituted adapters ──
    def _ensure_transcriber_loaded(self) -> Any:
        return SimpleNamespace(transcribe=lambda audio, **kw: self._transcribe())

    def _set_runtime_activity(self, state: str, **kw: Any) -> None:
        self.activity.append({"state": state, **kw})

    def _try_tmux_agent_reply(self, text: str, session: Any) -> bool:
        return False  # no tmux pane on a runner

    def _mark_first_dictation(self) -> None:
        self.first_marked += 1

    def _set_voice_state(self, state: str, **kw: Any) -> None:
        return None

    # ── what the test reads ──
    @property
    def events(self) -> list[str]:
        return [str(a.get("last_event") or "") for a in self.activity]

    @property
    def last_error(self) -> str:
        return str(self.runtime_status.get("last_error") or "")


class _TypingRecorder:
    """Stands in for `type_text_from_owner_gesture`; records, never types."""

    def __init__(self, *, raises: Optional[BaseException] = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self._raises = raises

    def __call__(self, text: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append({"text": text, **kwargs})
        if self._raises is not None:
            raise self._raises
        return {
            "operation_id": f"op-{len(self.calls)}",
            "state": "succeeded",
            "outcome": "succeeded",
            "target_ref": "desktop-input:focus-1-abcd",
        }


@pytest.fixture
def journal(tmp_path):
    """A REAL durable journal recorder on an isolated database file."""
    reset_database()
    database = Database(tmp_path / "custody.db")
    yield DictationJournalRecorder(database.dictation_journal), database
    reset_database()


@pytest.fixture
def typing(monkeypatch):
    """Replace the typing adapter at its module seam and hand back the recorder."""

    def _install(recorder: _TypingRecorder) -> _TypingRecorder:
        import holdspeak.desktop_typing as desktop_typing

        monkeypatch.setattr(
            desktop_typing, "type_text_from_owner_gesture", recorder
        )
        return recorder

    return _install


# ── AC1: a hotkey dictation leaves its actual receipt ────────────────────────


def test_a_hotkey_dictation_journals_its_own_row_and_types_the_landed_text_once(
    journal, typing
) -> None:
    """The receipt is real: one journal row tagged `hotkey`, one typing handoff.

    The row is what the product wrote — not a fixture — so the source tag, the
    transcript and the landed text are the shipped values.
    """
    recorder, database = journal
    typed = typing(_TypingRecorder())
    rig = _HotkeyRig(journal=recorder, transcribe=lambda: HEARD)

    assert rig._transcribe_and_type(AUDIO) is None  # the parent closes succeeded

    rows = database.dictation_journal.recent()
    assert len(rows) == 1, rows
    row = rows[0]
    assert row.source == "hotkey"
    assert row.transcript == HEARD
    assert row.final_text == HEARD

    assert len(typed.calls) == 1, typed.calls
    call = typed.calls[0]
    assert call["text"] == HEARD
    assert call["gesture"] == "hold_release"
    assert call["requested_target"] == "focused"
    assert call["delivery_method"] == "desktop_fallback"
    assert call["submit"] is False

    assert "dictation_typed" in rig.events
    assert rig.last_error == ""
    assert rig.first_marked == 1


def test_a_hotkey_dictation_reaches_the_agent_target_when_one_is_aimed(
    journal, typing
) -> None:
    """The aimed target rides into the delivery: an agent reply is not `focused`."""
    recorder, _database = journal
    typed = typing(_TypingRecorder())
    rig = _HotkeyRig(journal=recorder, transcribe=lambda: HEARD)
    agent = SimpleNamespace(session_id="s-1", cwd=None, awaiting_response=True)

    rig._transcribe_and_type(AUDIO, agent_reply_session=agent)

    assert len(typed.calls) == 1
    assert typed.calls[0]["requested_target"] == "agent_fallback"


# ── AC5 (second half): an uncertain delivery never types twice ───────────────


def test_a_typing_adapter_that_raises_is_never_retried_and_keeps_the_words(
    journal, typing
) -> None:
    """A driver that raised AFTER the text may have landed is ambiguous.

    The capture tail makes exactly ONE handoff, names the failure on the
    runtime, and leaves the journal row standing — the words are recoverable
    from the journal even though the delivery is unknown.
    """
    recorder, database = journal
    typed = typing(
        _TypingRecorder(raises=DesktopTypeRefused("desktop_type_driver_failed"))
    )
    rig = _HotkeyRig(journal=recorder, transcribe=lambda: HEARD)

    rig._transcribe_and_type(AUDIO)

    assert len(typed.calls) == 1, "one uncertain handoff is never replayed"
    assert "dictation_typing_failed" in rig.events
    assert "desktop_type_driver_failed" in rig.last_error
    assert rig.runtime_status.get("text_injection_enabled") is False
    rows = database.dictation_journal.recent()
    assert len(rows) == 1 and rows[0].transcript == HEARD, (
        "a failed delivery must not lose the words it captured"
    )
    assert rig.first_marked == 0, "an uncertain delivery is not a first dictation"


# ── AC3: silence, failed transcription, interruption ────────────────────────


def test_silence_journals_nothing_types_nothing_and_names_no_speech(
    journal, typing
) -> None:
    """An empty transcription is not a failure and not a row — it is named."""
    recorder, database = journal
    typed = typing(_TypingRecorder())
    rig = _HotkeyRig(journal=recorder, transcribe=lambda: "")

    assert rig._transcribe_and_type(AUDIO) is None

    assert typed.calls == []
    assert database.dictation_journal.recent() == []
    assert "dictation_no_speech" in rig.events
    assert rig.last_error == "", "silence is not an error"


def test_a_failed_transcription_names_itself_and_writes_no_row(
    journal, typing
) -> None:
    """The engine raised: nothing is typed, nothing is journaled, the parent
    closes `failed`, and the reason is on the runtime for the face to read."""
    recorder, database = journal
    typed = typing(_TypingRecorder())

    def _boom() -> str:
        raise ValueError("whisper decode blew up")

    rig = _HotkeyRig(journal=recorder, transcribe=_boom)

    assert rig._transcribe_and_type(AUDIO) == "failed"

    assert typed.calls == []
    assert database.dictation_journal.recent() == []
    assert "dictation_transcription_failed" in rig.events
    assert "whisper decode blew up" in rig.last_error


class _RefusingFence:
    """A cancellation election nobody wins: the utterance was interrupted."""

    def __init__(self) -> None:
        self.stages: list[str] = []

    def publish(self, stage: str, _publication: Any) -> tuple[bool, Any]:
        self.stages.append(stage)
        return False, None

    def discarded(self, _stage: str) -> bool:
        return False

    def reason(self, **_kw: Any) -> str:
        return "speech_session_cancelled"


class _InterruptedSession:
    def __init__(self) -> None:
        self.fence = _RefusingFence()
        self.closes: list[str] = []

    def transcription(self, **_kw: Any) -> Any:
        return None

    def provider(self) -> Any:
        return None

    def close(self, outcome: str = "succeeded") -> str:
        self.closes.append(outcome)
        return outcome


def test_an_interruption_mid_utterance_types_nothing_and_journals_nothing(
    journal, typing, monkeypatch
) -> None:
    """A session cancelled while the model was working publishes NOTHING.

    The words were heard, so the transcription happened; the delivery election
    is lost, so no keystroke and no receipt follow it.
    """
    recorder, database = journal
    typed = typing(_TypingRecorder())
    rig = _HotkeyRig(journal=recorder, transcribe=lambda: HEARD)
    monkeypatch.setattr(
        capture_module,
        "_frozen_session_transcriber",
        lambda _self, _session: SimpleNamespace(
            transcribe=lambda audio, **kw: HEARD
        ),
    )
    session = _InterruptedSession()

    rig._transcribe_and_type(AUDIO, session=session)

    assert typed.calls == [], "a cancelled utterance may never type"
    assert database.dictation_journal.recent() == []
    assert "dictation voice-command dispatch" in session.fence.stages


# ── AC4: the correction the matcher actually applies ─────────────────────────


def test_one_taught_text_rule_fires_on_a_later_utterance_and_names_its_id(
    tmp_path,
) -> None:
    """The stored rule is the one the pipeline's matcher applies, by durable id."""
    reset_database()
    database = Database(tmp_path / "corrections.db")
    store = CorrectionStore(repository=database.dictation_corrections)

    outcome = store.record("text", "postgress", "PostgreSQL")
    assert bool(outcome) is True
    assert outcome.correction_id is not None

    landed, applied = apply_text_corrections(HEARD, store.snapshot())
    assert landed == "the PostgreSQL migration lands on friday"
    assert applied == (outcome.correction_id,)
    reset_database()


def test_a_rule_that_changes_nothing_names_no_id(tmp_path) -> None:
    """The matcher reports what it CHANGED. An utterance the rule never
    matched contributes no id, so the journal cannot claim a firing."""
    reset_database()
    database = Database(tmp_path / "corrections-quiet.db")
    store = CorrectionStore(repository=database.dictation_corrections)
    store.record("text", "postgress", "PostgreSQL")

    landed, applied = apply_text_corrections("nothing to fix here", store.snapshot())
    assert landed == "nothing to fix here"
    assert applied == ()
    reset_database()


# ── AC5 (first half): the rules survive a restart ────────────────────────────


def test_correction_rows_outlive_the_process_that_taught_them(tmp_path) -> None:
    """The ring is process memory; the rows are not.

    A second store built over the SAME database file — the shape of a hub
    restart — hydrates the rule and the matcher fires it with the same durable
    id, so nothing about the correction lived only in the first process.
    """
    reset_database()
    path = tmp_path / "restart.db"
    first = Database(path)
    taught = CorrectionStore(repository=first.dictation_corrections).record(
        "text", "postgress", "PostgreSQL"
    )
    assert taught.correction_id is not None
    reset_database()

    second = Database(path)
    reopened = CorrectionStore(repository=second.dictation_corrections)
    rules = [c for c in reopened.snapshot() if c.kind == "text"]
    assert [(r.key, r.value) for r in rules] == [("postgress", "PostgreSQL")]

    landed, applied = apply_text_corrections(HEARD, reopened.snapshot())
    assert landed == "the PostgreSQL migration lands on friday"
    assert applied == (taught.correction_id,)
    reset_database()


def test_a_ring_only_rule_fires_but_fabricates_no_id() -> None:
    """No repository, no durable id — and the matcher invents none."""
    ring = [Correction(kind="text", key="postgress", value="PostgreSQL", sequence=1)]
    landed, applied = apply_text_corrections(HEARD, ring)
    assert landed == "the PostgreSQL migration lands on friday"
    assert applied == ()
