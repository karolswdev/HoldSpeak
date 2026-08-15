"""HS-131-09 Part A: dictation, wake, and local Whisper are admitted per session.

One desktop hold = one ``dictation.session``; one configured wake capture = one
bounded ``wake.session`` under the narrow ``wake-capture`` service identity; every
nonempty ``Transcriber.transcribe`` = one ``whisper-transcribe`` child of a live
parent; every explicit MLX load = its own ``whisper-preload`` SIBLING child. No
audio and no transcript ever reaches a kernel row.

Only the audio floor and the Whisper backend are faked. The plans, the parents,
the runner, the receipts, the seal, and the refusals are production code.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from holdspeak.config import Config
from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.speech_session import (
    CAPABILITY_WHISPER_PRELOAD,
    CAPABILITY_WHISPER_TRANSCRIBE,
    HOLD_CAPTURE_CEILING_SECONDS,
    HOLD_CHILD_BUDGET,
    HOLD_DRAIN_SECONDS,
    OUTCOME_INDETERMINATE,
    WAKE_CHILD_BUDGET,
    WAKE_DEADLINE_SECONDS,
    SpeechProviderFailure,
    SpeechSessionRefused,
    admit_hold_session,
    admit_wake_session,
    model_config_revision,
    preload_service_admission,
    wake_config_revision,
    whisper_deployment_identity,
)
from holdspeak.speech_session.child import invocation_id
from holdspeak.speech_session.plan import (
    PRELOAD_AUTHORITY_MISMATCHED,
    PRELOAD_AUTHORITY_REQUIRED,
    TRANSCRIPTION_CONTEXT_REQUIRED,
)
from holdspeak.transcribe import Transcriber, TranscriberError, _MlxTranscriber

pytestmark = pytest.mark.timeout(60, method="signal")

AUDIO_SENTINEL = 0.4242424
TEXT_SENTINEL = "PINEAPPLEQUARTERLYSECRET"


# --------------------------------------------------------------------- fakes


class FakeFloor:
    """The shared audio floor arbiter, reduced to its contract."""

    def __init__(self, *, accept: bool = True, audio: Any = None) -> None:
        self.accept = accept
        self.audio = audio
        self.begins = 0
        self.ends = 0
        self.active_owner = None

    def begin(self, recorder: Any, owner: str = "") -> bool:
        self.begins += 1
        return self.accept

    def end(self, owner: str = "") -> Any:
        self.ends += 1
        return self.audio

    def acquire(self, owner: str) -> bool:
        return True

    def release(self, owner: str) -> None:
        return None


class FakeImpl:
    """The Whisper backend seam: the ONE thing that must not run unadmitted."""

    device = "mlx"
    compute_type = "float16"
    loaded = True

    def __init__(self, text: str = TEXT_SENTINEL) -> None:
        self.text = text
        self.calls: list[int] = []
        self.warms: list[Any] = []

    def transcribe(self, audio: Any) -> str:
        self.calls.append(int(np.asarray(audio).size))
        return self.text

    def ensure_loaded(self, admission: Any) -> None:
        self.warms.append(admission)


class _Text:
    def process(self, text: str) -> str:
        return text


class _Host:
    """The runtime surface the capture/wake mixins actually touch."""

    def __init__(self, config: Config, floor: FakeFloor, transcriber: Any) -> None:
        self.config = config
        self.voice_session = floor
        self.transcriber = transcriber
        self.recorder = object()
        self.runtime_stop_event = threading.Event()
        self.state_lock = threading.Lock()
        self.transcription_lock = threading.Lock()
        self.runtime_status: dict[str, Any] = {}
        self.text_processor = _Text()
        self.wake_previews: dict[str, Any] = {}
        self.dictation_previews: dict[str, Any] = {}
        self.typer = None
        self.server = None
        self.activities: list[tuple[str, str]] = []
        self.states: list[str] = []
        self.kicked: list[Any] = []
        self.tails: list[Any] = []

    # runtime seams the mixins call
    def _set_runtime_activity(self, state: str, **kwargs: Any) -> None:
        self.activities.append((state, str(kwargs.get("last_event") or "")))

    def _set_voice_state(self, state: str, **kwargs: Any) -> None:
        self.states.append(state)

    def _ensure_transcriber_loaded(self) -> Any:
        return self.transcriber

    def _mark_first_dictation(self) -> None:
        return None

    def _maybe_run_dictation_pipeline(self, text: str, **kwargs: Any) -> str:
        return text


def _build_host(tmp_path: Path, monkeypatch, **floor_kwargs: Any):
    from holdspeak.runtime.dictation_capture import DictationCaptureMixin
    from holdspeak.runtime.wake_glue import WakeWordGlueMixin

    class Host(_Host, DictationCaptureMixin, WakeWordGlueMixin):
        pass

    db = Database(tmp_path / "speech.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    broker = _configure(db)
    config = Config()
    impl = FakeImpl()
    host = Host(config, FakeFloor(**floor_kwargs), _transcriber(impl))
    return db, broker, host, impl


def _transcriber(impl: Any, *, timeout: float = 0.0) -> Transcriber:
    """A real ``Transcriber`` over a faked backend: the admission path is real."""
    transcriber = Transcriber.__new__(Transcriber)
    transcriber.backend = "mlx"
    transcriber.timeout_seconds = float(timeout)
    transcriber.language = None
    transcriber._impl = impl
    transcriber.model_name = "base"
    transcriber.device = impl.device
    transcriber.compute_type = impl.compute_type
    return transcriber


# ----------------------------------------------------------------- queries


def _parents(db: Database, kind: str = "") -> list[dict[str, Any]]:
    query = "SELECT p.*,o.principal_kind,o.principal_identity,o.authority_basis FROM kernel_parent_runs p JOIN kernel_operations o ON o.operation_id=p.operation_id"
    parameters: tuple[Any, ...] = ()
    if kind:
        query += " WHERE p.kind=?"
        parameters = (kind,)
    with db._connection() as conn:
        return [dict(row) for row in conn.execute(query + " ORDER BY p.created_at", parameters)]


def _operations(db: Database, *, name: str = "") -> list[dict[str, Any]]:
    query = "SELECT * FROM kernel_operations"
    parameters: tuple[Any, ...] = ()
    if name:
        query += " WHERE name=?"
        parameters = (name,)
    with db._connection() as conn:
        return [dict(row) for row in conn.execute(query + " ORDER BY created_at", parameters)]


def _receipt(db: Database, operation_id: str) -> dict[str, Any] | None:
    with db._connection() as conn:
        row = conn.execute(
            "SELECT * FROM kernel_receipts WHERE operation_id=?", (operation_id,)
        ).fetchone()
    return None if row is None else dict(row)


def _whisper_revision(db: Database, config: Config) -> str:
    from holdspeak.deployment_revisions import DeploymentRevision

    return DeploymentRevision.from_identity(whisper_deployment_identity(config.model)).id


# ------------------------------------------------------------- desktop hold


def test_hold_press_admits_exactly_one_dictation_session(tmp_path, monkeypatch):
    db, _broker, host, _impl = _build_host(tmp_path, monkeypatch)

    host._on_hotkey_press()

    parents = _parents(db)
    assert [row["kind"] for row in parents] == ["dictation.session"]
    row = parents[0]
    assert row["state"] == "OPEN"
    assert (row["principal_kind"], row["principal_identity"]) == ("owner", "owner-session")
    assert int(row["child_budget"]) == HOLD_CHILD_BUDGET == 12
    # Admitted with the honest worst case: the capture ceiling PLUS the drain.
    ceiling = HOLD_CAPTURE_CEILING_SECONDS + HOLD_DRAIN_SECONDS
    assert ceiling - 5 < float(row["deadline_at"]) - float(row["created_at"]) <= ceiling
    # No model ran, so no invocation exists yet.
    assert _operations(db, name="inference.invoke") == []


def test_hold_release_seals_the_deadline_to_release_plus_drain(tmp_path, monkeypatch):
    audio = np.zeros(16000, dtype=np.float32)
    db, _broker, host, _impl = _build_host(tmp_path, monkeypatch)
    host._transcribe_and_type = lambda *a, **k: host.tails.append(k.get("session"))

    host._on_hotkey_press()
    admitted = float(_parents(db)[0]["deadline_at"])
    host.voice_session.audio = audio
    host._on_hotkey_release()

    sealed = float(_parents(db)[0]["deadline_at"])
    assert sealed < admitted
    created = float(_parents(db)[0]["created_at"])
    # The sealed fence is release + 90s, not press + 30m + 90s.
    assert HOLD_DRAIN_SECONDS - 5 < sealed - created <= HOLD_DRAIN_SECONDS + 5


def test_release_before_admission_completes_cancels_the_parent(tmp_path, monkeypatch):
    """Sol Amendment 1: the release wins, the parent is cancelled, audio is discarded."""
    audio = np.zeros(16000, dtype=np.float32)
    db, _broker, host, impl = _build_host(tmp_path, monkeypatch)
    host.voice_session.audio = audio
    host._transcribe_and_type = lambda *a, **k: host.tails.append(k.get("session"))

    from holdspeak.runtime import dictation_session as module

    real = module.admit_hold_session
    released: list[bool] = []

    def racing(**kwargs: Any):
        # The release lands BEFORE this admission returns, in one deterministic
        # sequence: exactly the race Amendment 1 names.
        if not released:
            released.append(True)
            host._on_hotkey_release()
        return real(**kwargs)

    monkeypatch.setattr(module, "admit_hold_session", racing)
    host._on_hotkey_press()

    parents = _parents(db)
    assert [row["kind"] for row in parents] == ["dictation.session"]
    assert parents[0]["state"] == "CANCELLED"
    assert (_receipt(db, parents[0]["operation_id"]) or {}).get("outcome") == "cancelled"
    # The audio was discarded: no tail ran, and no model was ever reached.
    assert host.tails == []
    assert impl.calls == []
    assert _operations(db, name="inference.invoke") == []


def test_refused_press_tears_the_capture_down(tmp_path, monkeypatch):
    db, _broker, host, _impl = _build_host(tmp_path, monkeypatch)

    from holdspeak.runtime import dictation_session as module

    def refuse(**kwargs: Any):
        raise SpeechSessionRefused("speech_session_not_admitted")

    monkeypatch.setattr(module, "admit_hold_session", refuse)
    host._on_hotkey_press()

    assert _parents(db) == []
    assert host.voice_session.ends == 1  # the floor was released, not held open
    assert ("error", "dictation_session_refused") in host.activities


# ---------------------------------------------------------------- wake


def test_wake_capture_admits_one_bounded_wake_session(tmp_path, monkeypatch):
    db, _broker, host, impl = _build_host(tmp_path, monkeypatch)
    host.config.wake_word.enabled = True
    audio = np.full(16000, AUDIO_SENTINEL, dtype=np.float32)

    host._transcribe_wake(audio)

    parents = _parents(db)
    assert [row["kind"] for row in parents] == ["wake.session"]
    row = parents[0]
    assert (row["principal_kind"], row["principal_identity"]) == ("service", "wake-capture")
    assert str(row["authority_basis"]) == (
        f"configured-wake:{wake_config_revision(host.config.wake_word)}"
    )
    assert int(row["child_budget"]) == WAKE_CHILD_BUDGET == 12
    assert (
        WAKE_DEADLINE_SECONDS - 5
        < float(row["deadline_at"]) - float(row["created_at"])
        <= WAKE_DEADLINE_SECONDS
    )
    # One transcription child of THAT parent, and no new effect operation.
    children = _operations(db, name="inference.invoke")
    assert len(children) == 1
    assert children[0]["parent_operation_id"] == row["operation_id"]
    assert _operations(db, name="desktop.type_text") == []
    assert impl.calls == [16000]
    assert row["state"] == "SUCCEEDED"


def test_disabled_wake_configuration_admits_nothing(tmp_path, monkeypatch):
    db, _broker, host, impl = _build_host(tmp_path, monkeypatch)
    host.config.wake_word.enabled = False

    host._transcribe_wake(np.zeros(16000, dtype=np.float32))

    assert _parents(db) == []
    assert impl.calls == []
    assert ("error", "wake_session_refused") in host.activities


def test_wake_authority_revision_tracks_the_configured_fields():
    base = Config().wake_word
    first = wake_config_revision(base)
    assert first == wake_config_revision(Config().wake_word)  # deterministic

    changed = Config().wake_word
    changed.action = "type"
    assert wake_config_revision(changed) != first

    window = Config().wake_word
    window.armed_window_seconds = 12.0
    assert wake_config_revision(window) != first


# ------------------------------------------------------------ transcriber


def test_transcribe_runs_one_child_naming_the_frozen_revision(tmp_path, monkeypatch):
    db, _broker, _host, _impl = _build_host(tmp_path, monkeypatch)
    config = Config()
    session = admit_hold_session(config_snapshot=config)
    impl = FakeImpl()
    transcriber = _transcriber(impl)

    text = transcriber.transcribe(
        np.full(8000, AUDIO_SENTINEL, dtype=np.float32), admission=session.transcription()
    )

    assert text == TEXT_SENTINEL
    children = _operations(db, name="inference.invoke")
    assert len(children) == 1
    revision = _whisper_revision(db, config)
    assert children[0]["target_ref"] == f"deployment-revision:{revision}"
    assert children[0]["parent_operation_id"] == session.operation_id
    assert (_receipt(db, children[0]["operation_id"]) or {})["outcome"] == "succeeded"
    assert session.plan.primary(CAPABILITY_WHISPER_TRANSCRIBE) == revision


def test_empty_audio_creates_no_child(tmp_path, monkeypatch):
    db, _broker, _host, _impl = _build_host(tmp_path, monkeypatch)
    session = admit_hold_session(config_snapshot=Config())
    impl = FakeImpl()

    assert _transcriber(impl).transcribe(
        np.zeros(0, dtype=np.float32), admission=session.transcription()
    ) == ""

    assert impl.calls == []
    assert _operations(db, name="inference.invoke") == []


def test_transcribe_without_a_live_context_refuses_before_the_backend(tmp_path, monkeypatch):
    db, _broker, _host, _impl = _build_host(tmp_path, monkeypatch)
    impl = FakeImpl()

    with pytest.raises(SpeechSessionRefused) as excinfo:
        _transcriber(impl).transcribe(np.full(8000, AUDIO_SENTINEL, dtype=np.float32))

    assert excinfo.value.reason == TRANSCRIPTION_CONTEXT_REQUIRED
    assert impl.calls == []  # no MLX / faster-whisper call happened
    assert impl.warms == []
    assert _operations(db, name="inference.invoke") == []


# -------------------------------------------------------------- MLX preload


class _Mlx(_MlxTranscriber):
    """The real ``ensure_loaded`` walk over faked MLX dispatches."""

    device = "mlx"
    compute_type = "float16"

    def __init__(self, *, holder_ok: bool, silent_ok: bool = True) -> None:
        self._candidates = ("mlx-community/whisper-base-mlx",)
        self._path_or_hf_repo = None
        self.model_name = "base"
        self.language = None
        self._holder_ok = holder_ok
        self._silent_ok = silent_ok
        self.dispatches: list[str] = []
        self.transcribes = 0

    def _model_holder_get(self, path_or_hf_repo: str) -> str:
        self.dispatches.append("model-holder")
        if not self._holder_ok:
            raise RuntimeError("ModelHolder hook missing")
        return "model-holder"

    def _silent_audio_load(self, path_or_hf_repo: str) -> str:
        self.dispatches.append("silent-audio")
        if not self._silent_ok:
            raise RuntimeError("weights unavailable")
        return "silent-audio"

    def transcribe(self, audio_array: Any) -> str:  # type: ignore[override]
        self.transcribes += 1
        return TEXT_SENTINEL


def _child_created_at(db: Database, native_id: str) -> float:
    with db._connection() as conn:
        row = conn.execute(
            "SELECT created_at FROM kernel_operations WHERE native_id=?", (native_id,)
        ).fetchone()
    assert row is not None, f"no invocation for {native_id}"
    return float(row["created_at"])


def test_explicit_get_model_is_one_preload_sibling_before_the_transcribe_child(
    tmp_path, monkeypatch
):
    db, _broker, _host, _impl = _build_host(tmp_path, monkeypatch)
    session = admit_hold_session(config_snapshot=Config())
    impl = _Mlx(holder_ok=True)
    transcriber = _transcriber(impl)

    transcriber.transcribe(
        np.full(8000, AUDIO_SENTINEL, dtype=np.float32), admission=session.transcription()
    )

    assert impl.dispatches == ["model-holder"]  # no fallback dispatch happened
    children = _operations(db, name="inference.invoke")
    assert len(children) == 2
    assert {row["parent_operation_id"] for row in children} == {session.operation_id}
    preload = invocation_id(
        session.plan.session_id,
        CAPABILITY_WHISPER_PRELOAD,
        ("model-holder", "mlx-community/whisper-base-mlx"),
        1,
    )
    assert _child_created_at(db, preload) <= children[-1]["created_at"]
    assert children[0]["native_id"] == preload
    for row in children:
        assert (_receipt(db, row["operation_id"]) or {})["outcome"] == "succeeded"


def test_failed_get_model_then_silent_fallback_are_two_preload_children(tmp_path, monkeypatch):
    db, _broker, _host, _impl = _build_host(tmp_path, monkeypatch)
    session = admit_hold_session(config_snapshot=Config())
    impl = _Mlx(holder_ok=False)
    transcriber = _transcriber(impl)

    transcriber.transcribe(
        np.full(8000, AUDIO_SENTINEL, dtype=np.float32), admission=session.transcription()
    )

    assert impl.dispatches == ["model-holder", "silent-audio"]
    children = _operations(db, name="inference.invoke")
    assert len(children) == 3  # two preload siblings, then the transcription
    outcomes = [(_receipt(db, row["operation_id"]) or {})["outcome"] for row in children]
    assert outcomes == ["failed", "succeeded", "succeeded"]


def test_every_preload_candidate_failing_refuses_without_transcribing(tmp_path, monkeypatch):
    db, _broker, _host, _impl = _build_host(tmp_path, monkeypatch)
    session = admit_hold_session(config_snapshot=Config())
    impl = _Mlx(holder_ok=False, silent_ok=False)

    with pytest.raises(TranscriberError):
        _transcriber(impl).transcribe(
            np.full(8000, AUDIO_SENTINEL, dtype=np.float32), admission=session.transcription()
        )

    assert impl.transcribes == 0
    children = _operations(db, name="inference.invoke")
    assert len(children) == 2
    assert [(_receipt(db, row["operation_id"]) or {})["outcome"] for row in children] == [
        "failed",
        "failed",
    ]


def test_pre_session_warm_without_the_authority_knob_defers(tmp_path, monkeypatch):
    db, _broker, _host, _impl = _build_host(tmp_path, monkeypatch)
    config = Config()
    assert config.model.local_model_preload_authority == ""

    with pytest.raises(SpeechSessionRefused) as excinfo:
        preload_service_admission(config_snapshot=config)

    assert excinfo.value.reason == PRELOAD_AUTHORITY_REQUIRED
    assert _operations(db, name="inference.invoke") == []
    assert _parents(db) == []


def test_authorized_pre_session_warm_runs_as_the_preload_service(tmp_path, monkeypatch):
    db, _broker, _host, _impl = _build_host(tmp_path, monkeypatch)
    config = Config()
    # Sol: the knob must NAME this model configuration's revision, not merely be
    # nonblank — an unbound authority string authorized anything forever.
    config.model.local_model_preload_authority = model_config_revision(config.model)
    impl = _Mlx(holder_ok=True)

    _transcriber(impl).warm(preload_service_admission(config_snapshot=config))

    assert impl.dispatches == ["model-holder"]
    children = _operations(db, name="inference.invoke")
    assert len(children) == 1
    row = children[0]
    assert (row["principal_kind"], row["principal_identity"]) == ("service", "local-model-preload")
    assert row["parent_operation_id"] == ""  # no session exists to parent it
    assert (_receipt(db, row["operation_id"]) or {})["outcome"] == "succeeded"
    # The warm removes the preload from the first session's hot path.
    assert impl._path_or_hf_repo == "mlx-community/whisper-base-mlx"


# ------------------------------------------------------------------ privacy


def test_no_audio_or_transcript_reaches_any_kernel_row(tmp_path, monkeypatch):
    db, _broker, host, _impl = _build_host(tmp_path, monkeypatch)
    host.config.wake_word.enabled = True
    session = admit_hold_session(config_snapshot=Config())
    impl = FakeImpl()
    _transcriber(impl).transcribe(
        np.full(4000, AUDIO_SENTINEL, dtype=np.float32), admission=session.transcription()
    )
    session.close("succeeded")
    host._transcribe_wake(np.full(16000, AUDIO_SENTINEL, dtype=np.float32))

    audio_bytes = np.full(4000, AUDIO_SENTINEL, dtype=np.float32).tobytes()
    with db._connection() as conn:
        tables = [
            "kernel_operations", "kernel_receipts", "kernel_journal",
            "kernel_parent_runs", "kernel_projection_stages",
        ]
        for table in tables:
            for row in conn.execute(f"SELECT * FROM {table}"):
                blob = "|".join(str(value) for value in dict(row).values())
                assert TEXT_SENTINEL not in blob, table
                assert str(AUDIO_SENTINEL) not in blob, table
                assert audio_bytes not in blob.encode("utf-8", "replace"), table


# ------------------------------------------------- meeting transcription (A6)


class _SilentMeetingRecorder:
    """Recorder boundary for admission tests that never exercise audio capture."""

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs

    def start(self) -> None:
        return None


class _SilentMeetingJournal:
    """Capture journal boundary; these tests dispatch already-materialized audio."""

    def __init__(self, meeting_id: str) -> None:
        self.meeting_id = meeting_id

    def append(self, source: str, audio: Any) -> None:
        return None


def _silence_meeting_capture(monkeypatch) -> None:
    monkeypatch.setattr(
        "holdspeak.meeting_session.session.MeetingRecorder", _SilentMeetingRecorder
    )
    monkeypatch.setattr(
        "holdspeak.meeting_capture_journal.MeetingCaptureJournal", _SilentMeetingJournal
    )


def test_meeting_transcription_children_join_the_existing_meeting_session(
    tmp_path, monkeypatch
):
    """A transcription interval is a child of the LIVE meeting.session parent."""
    from holdspeak.meeting_session.intel_admission import (
        SESSION_CHILD_BUDGET,
        SESSION_DEADLINE_SECONDS,
    )
    from holdspeak.meeting_session.transcribe_admission import session_child_budget

    def _budget() -> int:
        return session_child_budget(
            transcription=True,
            session_seconds=SESSION_DEADLINE_SECONDS,
            intelligence_budget=SESSION_CHILD_BUDGET,
        )

    db = Database(tmp_path / "meeting.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    _configure(db)
    # HS-131-17 removed the session's provider preflight entirely; this session
    # runs with intelligence disabled anyway, so there is nothing left to stub.
    # Capture is outside this test's boundary and must not open host audio on CI.
    _silence_meeting_capture(monkeypatch)

    from holdspeak.meeting_session import MeetingSession

    impl = FakeImpl()
    session = MeetingSession(
        _transcriber(impl),
        intel_enabled=False,
        principal=Principal(PrincipalKind.OWNER, "meeting-owner"),
    )
    monkeypatch.setattr(session, "_transcribe_loop", lambda: None)
    state = session.start()
    assert state is not None

    parents = _parents(db, "meeting.session")
    assert len(parents) == 1
    # Sol Amendment 6, exactly: 4096 + ceil(12h / 10s) + 2.
    assert int(parents[0]["child_budget"]) == _budget() == 8418

    text = session._transcribe_audio(np.full(16000, AUDIO_SENTINEL, dtype=np.float32))
    assert text == TEXT_SENTINEL

    children = _operations(db, name="inference.invoke")
    assert len(children) == 1
    assert children[0]["parent_operation_id"] == parents[0]["operation_id"]
    assert children[0]["target_ref"] == f"deployment-revision:{_whisper_revision(db, Config())}"
    # No dictation.session was invented for a meeting interval.
    assert _parents(db, "dictation.session") == []


def test_meeting_interval_without_a_live_parent_drops_before_whisper(tmp_path, monkeypatch):
    db = Database(tmp_path / "meeting.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    _configure(db)
    _silence_meeting_capture(monkeypatch)

    from holdspeak.meeting_session import MeetingSession

    impl = FakeImpl()
    # No authenticated principal: nothing is admitted, so nothing transcribes.
    session = MeetingSession(_transcriber(impl), intel_enabled=False, principal=None)
    monkeypatch.setattr(session, "_transcribe_loop", lambda: None)
    state = session.start()
    assert state is not None

    assert session._transcribe_audio(np.full(16000, AUDIO_SENTINEL, dtype=np.float32)) is None
    assert impl.calls == []
    assert _parents(db) == []
    assert _operations(db, name="inference.invoke") == []


# ------------------------------------------------------- plan resolution (OQ4)


def test_the_plan_freezes_ordered_per_capability_revisions(tmp_path, monkeypatch):
    db, _broker, _host, _impl = _build_host(tmp_path, monkeypatch)
    config = Config()
    # Pipeline OFF (the default): no provider-backed stage is planned, so a stage
    # dispatch would refuse by name instead of silently reaching a model.
    plain = admit_hold_session(config_snapshot=config).plan
    assert set(plain.capabilities) == {CAPABILITY_WHISPER_TRANSCRIBE, CAPABILITY_WHISPER_PRELOAD}

    config.dictation.pipeline.enabled = True
    config.dictation.pipeline.stages = ["intent-router", "project-rewriter"]
    staged = admit_hold_session(config_snapshot=config).plan
    assert {"intent-classify", "rewrite"} <= set(staged.capabilities)
    # punctuate is NOT planned: today's punctuation pass is lexical, not a model.
    assert "punctuate" not in staged.capabilities
    for name, revisions in staged.capabilities.items():
        assert revisions and all(str(item).startswith("dep_") for item in revisions)
    # Whisper is its own deployment, never the dictation-LLM leg.
    assert staged.primary(CAPABILITY_WHISPER_TRANSCRIBE) == _whisper_revision(db, config)
    assert staged.primary("intent-classify") != staged.primary(CAPABILITY_WHISPER_TRANSCRIBE)
    # The plan summary the parent carries is content-free.
    assert "insertion_context_sha256" in staged.summary()
    assert staged.config_revision != plain.config_revision


def test_paired_device_capture_admits_its_own_narrow_session(tmp_path, monkeypatch):
    """A remote device press is admitted — but never as a synthesized OWNER."""
    from holdspeak.speech_session import admit_device_session

    db, _broker, _host, _impl = _build_host(tmp_path, monkeypatch)
    session = admit_device_session(device_id="aipi-1", config_snapshot=Config())

    row = _parents(db, "dictation.session")[0]
    assert (row["principal_kind"], row["principal_identity"]) == ("service", "device-capture")
    assert str(row["authority_basis"]) == "paired-device:aipi-1"
    session.close("succeeded")


# ============================================================ Part B: browser


def _browser_principal() -> Principal:
    """The authenticated route identity a browser interval is bound to."""
    return Principal(PrincipalKind.OWNER, "owner-session")


def _sessions():
    from holdspeak.speech_session import browser_mic_sessions

    registry = browser_mic_sessions()
    registry.reset()
    return registry


def test_browser_open_admits_one_parent_for_every_utterance(tmp_path, monkeypatch):
    """One click-to-toggle interval = ONE parent; N utterances = N children."""
    from holdspeak.speech_session import BROWSER_CEILING_SECONDS, BROWSER_CHILD_BUDGET

    db, _broker, host, impl = _build_host(tmp_path, monkeypatch)
    registry = _sessions()
    principal = _browser_principal()
    interval = registry.open(principal, config_snapshot=host.config)

    audio = np.full(16000, AUDIO_SENTINEL, dtype=np.float32)
    for _ in range(3):
        assert host.transcribe_audio(
            audio, principal=principal, mic_handle=interval.handle
        ) == TEXT_SENTINEL

    parents = _parents(db)
    assert [row["kind"] for row in parents] == ["dictation.session"]
    row = parents[0]
    assert row["state"] == "OPEN"
    assert int(row["child_budget"]) == BROWSER_CHILD_BUDGET == 1024
    ceiling = BROWSER_CEILING_SECONDS
    assert ceiling - 5 < float(row["deadline_at"]) - float(row["created_at"]) <= ceiling
    children = _operations(db, name="inference.invoke")
    assert len(children) == 3
    assert {child["parent_operation_id"] for child in children} == {row["operation_id"]}
    assert impl.calls == [16000, 16000, 16000]
    registry.reset()


def test_a_client_supplied_parent_id_is_refused(tmp_path, monkeypatch):
    """The client may name only an opaque handle the server minted."""
    from holdspeak.speech_session import BROWSER_HANDLE_REFUSED

    db, _broker, host, impl = _build_host(tmp_path, monkeypatch)
    registry = _sessions()
    principal = _browser_principal()
    interval = registry.open(principal, config_snapshot=host.config)
    audio = np.full(16000, AUDIO_SENTINEL, dtype=np.float32)

    # The kernel parent id is NOT a handle, and neither is an invented one.
    for supplied in (interval.session.operation_id, "mic_deadbeef"):
        with pytest.raises(SpeechSessionRefused) as raised:
            host.transcribe_audio(audio, principal=principal, mic_handle=supplied)
        assert raised.value.reason == BROWSER_HANDLE_REFUSED
    assert impl.calls == []
    assert _operations(db, name="inference.invoke") == []
    registry.reset()


def test_the_inactivity_lease_refreshes_only_inside_a_real_whisper_claim(
    tmp_path, monkeypatch
):
    """Sol Amendment 8: model work refreshes the lease; nothing else does."""
    _db, _broker, host, impl = _build_host(tmp_path, monkeypatch)
    registry = _sessions()
    principal = _browser_principal()
    interval = registry.open(principal, config_snapshot=host.config)
    opened_lease = interval.lease_until

    # VAD-only/empty activity: no child is claimed, so nothing is refreshed.
    assert host.transcribe_audio(
        np.zeros(0, dtype=np.float32), principal=principal, mic_handle=interval.handle
    ) == ""
    assert interval.refreshes == 0
    assert interval.lease_until == opened_lease
    assert impl.calls == []

    host.transcribe_audio(
        np.full(16000, AUDIO_SENTINEL, dtype=np.float32),
        principal=principal,
        mic_handle=interval.handle,
    )
    assert interval.refreshes == 1
    assert interval.lease_until > opened_lease
    # The refresh is bounded by the 30-minute ceiling, never past it.
    assert interval.lease_until <= interval.ceiling_at
    registry.reset()


def test_a_lapsed_lease_forces_the_interval_closed_by_name(tmp_path, monkeypatch):
    """Any fence closes the parent and names the reason the client honors."""
    from holdspeak.speech_session import BROWSER_INACTIVITY_LAPSED

    db, _broker, host, impl = _build_host(tmp_path, monkeypatch)
    registry = _sessions()
    principal = _browser_principal()
    interval = registry.open(principal, config_snapshot=host.config)
    interval.lease_until = time.time() - 1.0  # the mic sat idle past its lease

    with pytest.raises(SpeechSessionRefused) as raised:
        host.transcribe_audio(
            np.full(16000, AUDIO_SENTINEL, dtype=np.float32),
            principal=principal,
            mic_handle=interval.handle,
        )
    assert raised.value.reason == BROWSER_INACTIVITY_LAPSED
    # The parent is closed, not left holding authority, and nothing reached a model.
    row = _parents(db)[0]
    assert row["state"] == "CANCELLED"
    assert (_receipt(db, row["operation_id"]) or {}).get("outcome") == "cancelled"
    assert impl.calls == []
    # A retry under the same handle cannot revive it: a fresh click is required.
    with pytest.raises(SpeechSessionRefused):
        host.transcribe_audio(
            np.full(16000, AUDIO_SENTINEL, dtype=np.float32),
            principal=principal,
            mic_handle=interval.handle,
        )
    registry.reset()


def test_closing_the_interval_cancels_and_closes_the_parent(tmp_path, monkeypatch):
    db, _broker, host, _impl = _build_host(tmp_path, monkeypatch)
    registry = _sessions()
    principal = _browser_principal()
    interval = registry.open(principal, config_snapshot=host.config)

    assert registry.close(principal, reason="browser_mic_stopped") == interval.handle

    row = _parents(db)[0]
    assert row["state"] == "CANCELLED"
    assert (_receipt(db, row["operation_id"]) or {}).get("outcome") == "cancelled"
    assert registry.live(principal) is None
    registry.reset()


def test_speak_to_fill_joins_an_interval_and_stands_alone_outside_one(
    tmp_path, monkeypatch
):
    """Sol OQ3: inside an interval it joins; outside it admits its own short session."""
    db, _broker, host, _impl = _build_host(tmp_path, monkeypatch)
    registry = _sessions()
    principal = _browser_principal()
    audio = np.full(16000, AUDIO_SENTINEL, dtype=np.float32)

    # Outside any interval: one short session, admitted and CLOSED by the tail.
    assert host.transcribe_audio(audio, principal=principal) == TEXT_SENTINEL
    standalone = _parents(db)
    assert len(standalone) == 1
    assert standalone[0]["state"] == "SUCCEEDED"

    # Inside one: the utterance joins THAT parent — no second parent appears.
    interval = registry.open(principal, config_snapshot=host.config)
    assert host.transcribe_audio(audio, principal=principal) == TEXT_SENTINEL
    parents = _parents(db)
    assert len(parents) == 2
    joined = [row for row in parents if row["operation_id"] == interval.session.operation_id]
    assert len(joined) == 1
    children = _operations(db, name="inference.invoke")
    assert len(children) == 2
    assert children[1]["parent_operation_id"] == interval.session.operation_id
    registry.reset()


# ---------------------------------------------- Part B: the cancellation fence


def test_a_cancelled_hold_discards_text_before_preview_and_delivery(
    tmp_path, monkeypatch
):
    """The fence discards late text; the child receipt stays honest."""
    from holdspeak.speech_session import admit_hold_session as admit

    db, _broker, host, _impl = _build_host(tmp_path, monkeypatch)
    typed: list[str] = []
    monkeypatch.setattr(
        "holdspeak.desktop_typing.type_text_from_owner_gesture",
        lambda text, **kwargs: typed.append(text),
    )
    session = admit(config_snapshot=host.config)

    class CancellingImpl(FakeImpl):
        """The session is cancelled WHILE the model is running."""

        def transcribe(self, audio: Any) -> str:
            session.cancel_and_close()
            return super().transcribe(audio)

    impl = CancellingImpl()
    host.transcriber = _transcriber(impl)

    host._transcribe_and_type(np.full(16000, AUDIO_SENTINEL, dtype=np.float32), session=session)

    # The model really ran and its child is honest...
    assert impl.calls == [16000]
    children = _operations(db, name="inference.invoke")
    assert len(children) == 1
    assert (_receipt(db, children[0]["operation_id"]) or {}).get("outcome") == "succeeded"
    # ...and NOTHING landed: no preview, no typing, no delivery admission.
    assert typed == []
    assert host.dictation_previews == {}
    assert _operations(db, name="desktop.type_text") == []
    assert host.runtime_status.get("last_transcription") in (None, "")


# ============================================ Sol blocking defects (HS-131-09)
#
# Eight defects Sol's review named before this story could ship. Each test below
# drives the REAL mechanism (kernel parents, receipts, fences, the registry's own
# generation token) and asserts the honest outcome, not the code shape.


class _PipelineBackend:
    """A dictation LLM backend reduced to the two calls that reach a model."""

    backend = "openai_compatible"
    base_url = ""
    model = ""

    def __init__(self) -> None:
        self.rewrites: list[str] = []

    def load(self) -> None:
        return None

    def info(self) -> dict[str, Any]:
        return {"backend": self.backend}

    def rewrite(self, prompt: str, **kwargs: Any) -> str:
        self.rewrites.append(str(prompt))
        return "REWRITTEN"


def _endpoint_profile(db: Database, config: Config) -> None:
    """Point the dictation LLM at a real profile, and freeze THAT revision.

    The dispatch seam binds a non-mesh child to its frozen revision, so a fake
    backend must advertise the endpoint the plan froze — the same rule production
    lives under.
    """
    db.profiles.upsert(
        profile_id="prof_browser", name="prof_browser", kind="openAICompatible",
        base_url="http://127.0.0.1:1234/v1", model="qwen-local",
    )
    config.dictation.pipeline.enabled = True
    config.dictation.pipeline.stages = ["project-rewriter"]
    config.dictation.runtime.profile_id = "prof_browser"


def _pipeline_runtime(admission: Any) -> tuple[Any, Any]:
    """The runtime a pipeline stage would hold, wrapped in the live admission."""
    from holdspeak.speech_session import admitted_runtime

    backend = _PipelineBackend()
    backend.base_url = "http://127.0.0.1:1234/v1"
    backend.model = "qwen-local"
    return backend, admitted_runtime(backend, admission)


# ------------------------------------------- 1. stop during the browser open


def test_a_stop_during_the_browser_open_cancels_the_admitted_parent(
    tmp_path, monkeypatch
):
    """Sol defect 1: the open must re-check its token and leave no orphan."""
    from holdspeak.speech_session import BROWSER_STOPPED_DURING_OPEN
    from holdspeak.speech_session import browser_mic as module

    db, _broker, host, _impl = _build_host(tmp_path, monkeypatch)
    registry = _sessions()
    principal = _browser_principal()
    real = module.admit_speech_session
    stopped: list[bool] = []

    def racing(**kwargs: Any):
        session = real(**kwargs)
        # The stop lands AFTER the parent exists and BEFORE the interval is
        # published: exactly the window that used to orphan a live parent.
        if not stopped:
            stopped.append(True)
            registry.close(principal, reason="browser_mic_stopped")
        return session

    monkeypatch.setattr(module, "admit_speech_session", racing)

    with pytest.raises(SpeechSessionRefused) as raised:
        registry.open(principal, config_snapshot=host.config)

    assert raised.value.reason == BROWSER_STOPPED_DURING_OPEN
    # The freshly admitted parent is CANCELLED with an honest receipt...
    parents = _parents(db)
    assert [row["state"] for row in parents] == ["CANCELLED"]
    assert (_receipt(db, parents[0]["operation_id"]) or {}).get("outcome") == "cancelled"
    # ...and no interval is live for this identity, so nothing can reach it.
    assert registry.live(principal) is None
    assert _operations(db, name="inference.invoke") == []
    registry.reset()


# ---------------------------------------------------- 2. no lease resurrection


def test_a_claim_after_the_lease_lapsed_refuses_and_never_dispatches(
    tmp_path, monkeypatch
):
    """Sol defect 2: a delayed claim must not resurrect a lapsed lease."""
    from holdspeak.speech_session import BROWSER_INACTIVITY_LAPSED

    db, _broker, host, impl = _build_host(tmp_path, monkeypatch)
    registry = _sessions()
    principal = _browser_principal()
    interval = registry.open(principal, config_snapshot=host.config)

    # The request passed the fence (its admission was built while live) and only
    # THEN sat in the transcription queue past the inactivity lease.
    admission = interval.transcription()
    interval.lease_until = time.time() - 1.0

    with pytest.raises(SpeechSessionRefused) as raised:
        host.transcriber.transcribe(
            np.full(16000, AUDIO_SENTINEL, dtype=np.float32), admission=admission
        )

    assert raised.value.reason == BROWSER_INACTIVITY_LAPSED
    # The refusal happened INSIDE the claim: no model ran, and the lease was not
    # extended by the very request that arrived too late.
    assert impl.calls == []
    assert interval.refreshes == 0
    assert interval.lease_until < time.time()
    registry.reset()


# ------------------------------- 3. the fence honors the seal and a revocation


def test_a_provider_returning_after_the_seal_publishes_nothing(tmp_path, monkeypatch):
    """Sol defect 3: the sealed deadline fences late text, not the admitted one."""
    from holdspeak.speech_session import admit_hold_session as admit

    db, _broker, host, _impl = _build_host(tmp_path, monkeypatch)
    typed: list[str] = []
    monkeypatch.setattr(
        "holdspeak.desktop_typing.type_text_from_owner_gesture",
        lambda text, **kwargs: typed.append(text),
    )
    session = admit(config_snapshot=host.config)

    class LateImpl(FakeImpl):
        """The provider returns AFTER release + 90s has already passed."""

        def transcribe(self, audio: Any) -> str:
            text = super().transcribe(audio)
            session.seal(time.time() - 1.0)
            return text

    impl = LateImpl()
    host.transcriber = _transcriber(impl)

    host._transcribe_and_type(
        np.full(16000, AUDIO_SENTINEL, dtype=np.float32), session=session
    )

    # The model really ran and its child receipt is honest...
    assert impl.calls == [16000]
    children = _operations(db, name="inference.invoke")
    assert len(children) == 1
    assert (_receipt(db, children[0]["operation_id"]) or {}).get("outcome") == "succeeded"
    # ...and the sealed fence discarded the text: no preview, no typing.
    assert typed == []
    assert host.dictation_previews == {}
    assert _operations(db, name="desktop.type_text") == []
    # The carrier itself now reports the sealed expiry, not "live".
    assert session.fence.reason() == "speech_session_expired"


def test_a_revoked_warrant_fences_the_session_through_the_durable_read(
    tmp_path, monkeypatch
):
    """Sol defect 3: revocation reaches a closure that only holds the carrier."""
    from holdspeak.speech_session import SpeechSessionRefused
    from holdspeak.speech_session import admit_hold_session as admit

    db, broker, host, _impl = _build_host(tmp_path, monkeypatch)
    typed: list[str] = []
    monkeypatch.setattr(
        "holdspeak.desktop_typing.type_text_from_owner_gesture",
        lambda text, **kwargs: typed.append(text),
    )
    session = admit(config_snapshot=host.config)
    fence = session.fence
    assert fence.reason() == ""

    broker.store.revoke_warrant(session.operation_id)

    assert fence.reason() == "speech_session_warrant_revoked"
    assert fence.discarded("dictation publication") is True
    # And the first child preserves that exact safe reason instead of degrading
    # it to raw text or generic parent-not-live.
    with pytest.raises(SpeechSessionRefused) as refusal:
        host._transcribe_and_type(
            np.full(16000, AUDIO_SENTINEL, dtype=np.float32), session=session
        )
    assert refusal.value.reason == "speech_session_warrant_revoked"
    assert typed == []
    assert _operations(db, name="desktop.type_text") == []


# ------------------------------------ 4. every browser pipeline call is a child


def test_the_one_shot_pipeline_runs_as_children_of_its_own_parent(
    tmp_path, monkeypatch
):
    """Sol defect 4: the one-shot parent stays OPEN through the pipeline stage."""
    db, _broker, host, impl = _build_host(tmp_path, monkeypatch)
    _endpoint_profile(db, host.config)
    _sessions()
    principal = _browser_principal()

    handle = host.transcribe_audio_admitted(
        np.full(16000, AUDIO_SENTINEL, dtype=np.float32), principal=principal
    )

    assert handle.text == TEXT_SENTINEL
    assert handle.owns_parent is True
    parent = _parents(db)[0]
    # The parent is still OPEN: the pipeline has not run yet.
    assert parent["state"] == "OPEN"

    backend, runtime = _pipeline_runtime(handle.provider)
    assert runtime.rewrite("polish this", max_tokens=64, temperature=0.1) == "REWRITTEN"
    handle.close("succeeded")

    # Transcription AND the rewrite are children of the SAME one-shot parent.
    children = _operations(db, name="inference.invoke")
    assert len(children) == 2
    assert {row["parent_operation_id"] for row in children} == {parent["operation_id"]}
    assert backend.rewrites == ["polish this"]
    assert _parents(db)[0]["state"] == "SUCCEEDED"


def test_the_http_pipeline_route_threads_the_live_admission(tmp_path, monkeypatch):
    """Sol defect 4: `pipeline=true` never reaches a model unadmitted."""
    import asyncio

    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.system.voice import build_voice_router

    db, _broker, host, _impl = _build_host(tmp_path, monkeypatch)
    _endpoint_profile(db, host.config)
    _sessions()
    principal = _browser_principal()
    seen: list[Any] = []

    async def spy_process_transcript(raw_text: str, source: str, context: Any = None,
                                     **kwargs: Any) -> str:
        # Stand in for the pipeline stages, but reach the model through the
        # admission the route handed us — an unwrapped runtime would record nothing.
        admission = kwargs.get("admission")
        seen.append(admission)
        _backend, runtime = _pipeline_runtime(admission)
        return str(runtime.rewrite(raw_text, max_tokens=64, temperature=0.1))

    monkeypatch.setattr(
        "holdspeak.dictation_runner.process_transcript", spy_process_transcript
    )
    ctx = WebContext(
        get_state=lambda: {},
        on_transcribe=host.transcribe_audio,
        on_transcribe_admitted=host.transcribe_audio_admitted,
    )
    monkeypatch.setattr(
        "holdspeak.web.routes.system.voice._resolve_config", lambda ctx: host.config
    )
    monkeypatch.setattr(
        "holdspeak.web.routes.system.voice._route_principal", lambda request: principal
    )
    endpoint = _endpoint_for(build_voice_router(ctx), "/api/dictation/transcribe")

    response = asyncio.run(endpoint(_FakeRequest(_wav_body(), {"pipeline": "true"})))

    assert response["success"] is True
    assert response["text"] == "REWRITTEN"
    assert len(seen) == 1 and seen[0] is not None
    parent = _parents(db)[0]
    children = _operations(db, name="inference.invoke")
    # The transcription AND the pipeline's rewrite are children of one parent...
    assert len(children) == 2
    assert {row["parent_operation_id"] for row in children} == {parent["operation_id"]}
    # ...and the parent closed once, honestly, after the pipeline drained.
    assert parent["state"] == "SUCCEEDED"
    assert (_receipt(db, parent["operation_id"]) or {}).get("outcome") == "succeeded"


def test_the_http_pipeline_route_closes_the_parent_failed_when_the_pipeline_raises(
    tmp_path, monkeypatch
):
    """Sol defect 8, on the browser path: a raised pipeline is not a success."""
    import asyncio

    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.system.voice import build_voice_router

    db, _broker, host, _impl = _build_host(tmp_path, monkeypatch)
    _endpoint_profile(db, host.config)
    _sessions()

    async def exploding(raw_text: str, source: str, context: Any = None, **kwargs: Any) -> str:
        raise RuntimeError("the pipeline blew up")

    monkeypatch.setattr("holdspeak.dictation_runner.process_transcript", exploding)
    monkeypatch.setattr(
        "holdspeak.web.routes.system.voice._resolve_config", lambda ctx: host.config
    )
    monkeypatch.setattr(
        "holdspeak.web.routes.system.voice._route_principal",
        lambda request: _browser_principal(),
    )
    ctx = WebContext(
        get_state=lambda: {},
        on_transcribe=host.transcribe_audio,
        on_transcribe_admitted=host.transcribe_audio_admitted,
    )
    endpoint = _endpoint_for(build_voice_router(ctx), "/api/dictation/transcribe")

    response = asyncio.run(endpoint(_FakeRequest(_wav_body(), {"pipeline": "true"})))

    # The caller still gets the raw transcript back...
    assert response["text"] == TEXT_SENTINEL
    # ...and the parent's receipt says what actually happened.
    parent = _parents(db)[0]
    assert parent["state"] == "FAILED"
    assert (_receipt(db, parent["operation_id"]) or {}).get("outcome") == "failed"


@pytest.mark.parametrize(
    ("fatal", "status_code", "parent_outcome"),
    [
        pytest.param(
            lambda: SpeechSessionRefused("speech_child_budget_exhausted"),
            422,
            "refused",
            id="session-refusal",
        ),
        pytest.param(
            lambda: SpeechProviderFailure(
                "dictation.rewrite", reason="provider_budget_refused"
            ),
            502,
            "failed",
            id="provider-failure",
        ),
    ],
)
def test_the_http_pipeline_route_never_turns_a_fatal_signal_into_raw_success(
    fatal, status_code, parent_outcome, tmp_path, monkeypatch
):
    """A fatal speech signal closes honestly and publishes no raw transcript."""
    import asyncio
    import json

    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.system.voice import build_voice_router

    db, _broker, host, _impl = _build_host(tmp_path, monkeypatch)
    _endpoint_profile(db, host.config)
    _sessions()

    async def refusing(*_args: Any, **_kwargs: Any) -> str:
        raise fatal()

    monkeypatch.setattr("holdspeak.dictation_runner.process_transcript", refusing)
    monkeypatch.setattr(
        "holdspeak.web.routes.system.voice._resolve_config", lambda ctx: host.config
    )
    monkeypatch.setattr(
        "holdspeak.web.routes.system.voice._route_principal",
        lambda request: _browser_principal(),
    )
    ctx = WebContext(
        get_state=lambda: {},
        on_transcribe=host.transcribe_audio,
        on_transcribe_admitted=host.transcribe_audio_admitted,
    )
    endpoint = _endpoint_for(build_voice_router(ctx), "/api/dictation/transcribe")

    response = asyncio.run(endpoint(_FakeRequest(_wav_body(), {"pipeline": "true"})))
    body = json.loads(response.body)

    assert response.status_code == status_code
    assert body["success"] is False
    assert body["reason"] in {
        "speech_child_budget_exhausted",
        "provider_budget_refused",
    }
    assert "text" not in body and TEXT_SENTINEL not in str(body)
    parent = _parents(db)[0]
    assert (_receipt(db, parent["operation_id"]) or {}).get("outcome") == parent_outcome


@pytest.mark.parametrize("fatal", [False, True], ids=["success", "refusal"])
def test_the_http_pipeline_route_reports_an_indeterminate_parent_close(
    fatal, monkeypatch
):
    """One-shot terminal persistence uncertainty cannot hide behind a clean body."""
    import asyncio
    import json
    from types import SimpleNamespace

    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.system.voice import build_voice_router

    closed_as: list[str] = []

    class UnrecordableTranscription:
        text = TEXT_SENTINEL
        provider = SimpleNamespace(egress_boundary="same_device")

        def close(self, outcome: str) -> str:
            closed_as.append(outcome)
            return OUTCOME_INDETERMINATE

    async def process(*_args: Any, **_kwargs: Any) -> str:
        if fatal:
            raise SpeechSessionRefused("speech_session_revoked")
        return "REWRITTEN"

    monkeypatch.setattr("holdspeak.dictation_runner.process_transcript", process)
    monkeypatch.setattr(
        "holdspeak.web.routes.system.voice._route_principal",
        lambda _request: _browser_principal(),
    )
    monkeypatch.setattr(
        "holdspeak.web.routes.system.voice._resolve_config", lambda _ctx: Config()
    )
    monkeypatch.setattr(
        "holdspeak.web.routes.system.voice._resolve_server", lambda _ctx: None
    )
    ctx = WebContext(
        get_state=lambda: {},
        on_transcribe=lambda *_args, **_kwargs: TEXT_SENTINEL,
        on_transcribe_admitted=lambda *_args, **_kwargs: UnrecordableTranscription(),
    )
    endpoint = _endpoint_for(build_voice_router(ctx), "/api/dictation/transcribe")

    response = asyncio.run(endpoint(_FakeRequest(_wav_body(), {"pipeline": "true"})))
    if fatal:
        body = json.loads(response.body)
        assert response.status_code == 422
        assert body["reason"] == "speech_session_revoked"
        assert body["session_terminal"] == OUTCOME_INDETERMINATE
        assert closed_as == ["refused"]
    else:
        assert response["success"] is True
        assert response["text"] == "REWRITTEN"
        assert response["session_terminal"] == OUTCOME_INDETERMINATE
        assert closed_as == ["succeeded"]


def test_the_ws_final_pass_runs_under_the_intervals_admission(tmp_path, monkeypatch):
    """Sol defect 4: the streaming final pass is a child of the socket's interval."""
    db, _broker, host, _impl = _build_host(tmp_path, monkeypatch)
    _endpoint_profile(db, host.config)
    registry = _sessions()
    principal = _browser_principal()
    interval = registry.open(principal, config_snapshot=host.config)

    # The utterance the socket transcribed...
    assert host.transcribe_audio(
        np.full(16000, AUDIO_SENTINEL, dtype=np.float32),
        principal=principal,
        mic_handle=interval.handle,
    ) == TEXT_SENTINEL
    # ...and the final pass, under the SAME interval admission the route passes.
    backend, runtime = _pipeline_runtime(interval.session.provider())
    assert runtime.rewrite(TEXT_SENTINEL, max_tokens=64, temperature=0.1) == "REWRITTEN"

    children = _operations(db, name="inference.invoke")
    assert len(children) == 2
    assert {row["parent_operation_id"] for row in children} == {
        interval.session.operation_id
    }
    assert backend.rewrites == [TEXT_SENTINEL]
    # The interval still owns its parent; the final pass never closed it.
    assert _parents(db)[0]["state"] == "OPEN"
    registry.reset()


def test_the_ws_final_pass_sends_an_error_not_raw_text_for_a_fatal_signal(
    tmp_path, monkeypatch
):
    """A fatal final-pass refusal cannot become a normal WebSocket final event."""
    import asyncio
    import json

    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.system.voice import build_voice_router

    _db, _broker, host, _impl = _build_host(tmp_path, monkeypatch)
    _endpoint_profile(_db, host.config)
    _sessions()
    host.config.meeting.web_auth_token = "ws-fatal-owner-token"
    monkeypatch.setattr(Config, "load", classmethod(lambda _cls: host.config))

    async def refusing(*_args: Any, **_kwargs: Any) -> str:
        raise SpeechSessionRefused("speech_child_budget_exhausted")

    monkeypatch.setattr("holdspeak.dictation_runner.process_transcript", refusing)

    class Socket:
        def __init__(self) -> None:
            self.headers = {
                "authorization": "Bearer ws-fatal-owner-token",
                "sec-websocket-protocol": "",
            }
            self.sent: list[dict[str, Any]] = []
            self.messages = [
                {"bytes": np.zeros(1600, dtype=np.int16).tobytes()},
                {"text": json.dumps({"type": "end"})},
            ]
            self.closed = False

        async def accept(self, **_kwargs: Any) -> None:
            return None

        async def receive(self) -> dict[str, Any]:
            return self.messages.pop(0)

        async def send_json(self, payload: dict[str, Any]) -> None:
            self.sent.append(dict(payload))

        async def close(self, **_kwargs: Any) -> None:
            self.closed = True

    ctx = WebContext(
        get_state=lambda: {},
        on_transcribe=lambda _audio, **_kwargs: TEXT_SENTINEL,
        web_auth_token="ws-fatal-owner-token",
    )
    endpoint = _endpoint_for(build_voice_router(ctx), "/ws/dictation/stream")
    socket = Socket()

    asyncio.run(endpoint(socket))

    assert any(
        event.get("type") == "error"
        and event.get("reason") == "speech_child_budget_exhausted"
        for event in socket.sent
    )
    assert not [event for event in socket.sent if event.get("type") == "final"]
    assert TEXT_SENTINEL not in str(
        [event for event in socket.sent if event.get("type") != "partial"]
    )


# --------------------------------------------- 6. the preload knob is bound


def test_an_unbound_preload_knob_refuses_and_names_the_revision(tmp_path, monkeypatch):
    """Sol defect 6: any nonblank string used to authorize any warm forever."""
    from holdspeak.speech_session import model_config_revision, preload_service_admission

    db, _broker, _host, _impl = _build_host(tmp_path, monkeypatch)
    config = Config()
    config.model.local_model_preload_authority = "yes-please"

    with pytest.raises(SpeechSessionRefused) as raised:
        preload_service_admission(config_snapshot=config)

    assert raised.value.reason == PRELOAD_AUTHORITY_MISMATCHED
    # The refusal carries what the owner must set — content-free, actionable.
    assert raised.value.detail == model_config_revision(config.model)
    assert _operations(db, name="inference.invoke") == []
    assert _parents(db) == []


def test_a_preload_knob_for_another_model_configuration_refuses(tmp_path, monkeypatch):
    """The authority is for ONE configuration; changing the model revokes it."""
    from holdspeak.speech_session import model_config_revision, preload_service_admission

    _db, _broker, _host, _impl = _build_host(tmp_path, monkeypatch)
    config = Config()
    config.model.local_model_preload_authority = model_config_revision(config.model)
    # Authorized for THIS configuration...
    assert preload_service_admission(config_snapshot=config) is not None
    # ...and not for a different model.
    config.model.name = "large"
    with pytest.raises(SpeechSessionRefused) as raised:
        preload_service_admission(config_snapshot=config)
    assert raised.value.reason == PRELOAD_AUTHORITY_MISMATCHED


# ------------------------------------------------ 7. wake stop cancels in-flight


def test_stopping_the_wake_listener_cancels_the_in_flight_capture(
    tmp_path, monkeypatch
):
    """Sol defect 7: the stop must REACH the capture that is already running."""
    db, _broker, host, _impl = _build_host(tmp_path, monkeypatch)
    host.config.wake_word.enabled = True
    host._wake_listener = None
    host._wake_stream = None
    host._wake_queue = None
    typed: list[str] = []
    monkeypatch.setattr(
        "holdspeak.desktop_typing.type_text_from_owner_gesture",
        lambda text, **kwargs: typed.append(text),
    )

    class StoppingImpl(FakeImpl):
        """The listener is stopped WHILE the wake transcription is in the model."""

        def transcribe(self, audio: Any) -> str:
            text = super().transcribe(audio)
            host._stop_wake_listener()
            return text

    impl = StoppingImpl()
    host.transcriber = _transcriber(impl)
    host.config.wake_word.action = "type"

    host._transcribe_wake(np.full(16000, AUDIO_SENTINEL, dtype=np.float32))

    # The model ran and its child is honest...
    assert impl.calls == [16000]
    parents = _parents(db, "wake.session")
    assert len(parents) == 1
    assert parents[0]["state"] == "CANCELLED"
    assert (_receipt(db, parents[0]["operation_id"]) or {}).get("outcome") == "cancelled"
    # ...and NOTHING was typed and no preview was issued after the stop.
    assert typed == []
    assert host.wake_previews == {}
    assert _operations(db, name="desktop.type_text") == []
    # The slot is empty again: a stop cannot cancel a session twice.
    assert host._cancel_wake_session() == ""


# ---------------------------------------- 8. a failed session closes failed


def test_a_hold_whose_tail_raised_closes_the_parent_failed(tmp_path, monkeypatch):
    """Sol defect 8: the inner swallow must not launder a failure into success."""
    db, _broker, host, _impl = _build_host(tmp_path, monkeypatch)
    session = admit_hold_session(config_snapshot=host.config)

    class ExplodingImpl(FakeImpl):
        def transcribe(self, audio: Any) -> str:
            raise RuntimeError("the model blew up")

    host.transcriber = _transcriber(ExplodingImpl())

    outcome = host._transcribe_and_type(
        np.full(16000, AUDIO_SENTINEL, dtype=np.float32), session=session
    )
    assert outcome == "failed"
    session.close(outcome)

    parent = _parents(db)[0]
    assert parent["state"] == "FAILED"
    assert (_receipt(db, parent["operation_id"]) or {}).get("outcome") == "failed"


def test_the_kick_off_thread_closes_the_parent_with_the_tails_outcome(
    tmp_path, monkeypatch
):
    """The threaded tail carries the honest outcome to the parent's close."""
    db, _broker, host, _impl = _build_host(tmp_path, monkeypatch)
    session = admit_hold_session(config_snapshot=host.config)
    host._transcribe_and_type = lambda *a, **k: "failed"

    host._kick_off_transcribe(
        np.full(16000, AUDIO_SENTINEL, dtype=np.float32), session=session
    )
    for _ in range(200):
        if _parents(db)[0]["state"] != "OPEN":
            break
        time.sleep(0.01)

    assert _parents(db)[0]["state"] == "FAILED"


def test_a_wake_session_whose_pipeline_raised_closes_failed(tmp_path, monkeypatch):
    """Sol defect 8, wake side: the swallowed error still reaches the receipt."""
    db, _broker, host, _impl = _build_host(tmp_path, monkeypatch)
    host.config.wake_word.enabled = True

    def exploding_pipeline(text: str, **kwargs: Any) -> str:
        raise RuntimeError("the pipeline blew up")

    host._maybe_run_dictation_pipeline = exploding_pipeline

    host._transcribe_wake(np.full(16000, AUDIO_SENTINEL, dtype=np.float32))

    parents = _parents(db, "wake.session")
    assert len(parents) == 1
    assert parents[0]["state"] == "FAILED"
    assert (_receipt(db, parents[0]["operation_id"]) or {}).get("outcome") == "failed"
    # The transcription child that DID succeed keeps its own honest receipt.
    children = _operations(db, name="inference.invoke")
    assert len(children) == 1
    assert (_receipt(db, children[0]["operation_id"]) or {}).get("outcome") == "succeeded"


# ------------------------------------------------------------------ route rig


class _FakeRequest:
    """The three things `/api/dictation/transcribe` reads from a request."""

    def __init__(self, body: bytes, query: dict[str, str], principal: Any = None) -> None:
        from types import SimpleNamespace

        self._body = body
        self.query_params = query
        # The route derives the identity from request state ONLY; a client never
        # supplies one.
        self.state = SimpleNamespace(principal=principal or _browser_principal())

    async def body(self) -> bytes:
        return self._body


def _endpoint_for(router: Any, path: str) -> Any:
    for route in router.routes:
        if getattr(route, "path", "") == path:
            return route.endpoint
    raise AssertionError(f"no route for {path}")


def _wav_body(samples: int = 16000) -> bytes:
    """One valid 16 kHz mono 16-bit WAV the route will accept."""
    import io
    import wave

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(np.zeros(samples, dtype=np.int16).tobytes())
    return buffer.getvalue()


# ==================================== Sol round 2: the last two blockers


def test_the_pipeline_route_admits_no_legacy_browser_pipeline_operation(
    tmp_path, monkeypatch
):
    """Sol round 2, blocker 1: ONE admission per utterance, and it is the session.

    The route used to submit a separate top-level ``inference.run`` for
    ``program:browser-mic-pipeline-v1`` that parented nothing, authorized nothing,
    could refuse a perfectly valid session, and defaulted to "admitted, local"
    whenever the kernel errored. It is gone: the utterance's own speech session is
    the admission, and the egress label comes from the revision it froze.
    """
    import asyncio

    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.system.voice import build_voice_router

    db, _broker, host, _impl = _build_host(tmp_path, monkeypatch)
    _endpoint_profile(db, host.config)
    _sessions()

    async def spy(raw_text: str, source: str, context: Any = None, **kwargs: Any) -> str:
        _backend, runtime = _pipeline_runtime(kwargs.get("admission"))
        return str(runtime.rewrite(raw_text, max_tokens=64, temperature=0.1))

    monkeypatch.setattr("holdspeak.dictation_runner.process_transcript", spy)
    monkeypatch.setattr(
        "holdspeak.web.routes.system.voice._resolve_config", lambda ctx: host.config
    )
    ctx = WebContext(
        get_state=lambda: {},
        on_transcribe=host.transcribe_audio,
        on_transcribe_admitted=host.transcribe_audio_admitted,
    )
    endpoint = _endpoint_for(build_voice_router(ctx), "/api/dictation/transcribe")

    response = asyncio.run(endpoint(_FakeRequest(_wav_body(), {"pipeline": "true"})))

    # No legacy program operation exists, under any name or definition ref.
    assert _operations(db, name="inference.run") == []
    with db._connection() as conn:
        refs = [
            str(dict(row).get("definition_ref") or "")
            for row in conn.execute("SELECT * FROM kernel_operations")
        ]
    assert not [ref for ref in refs if "browser-mic-pipeline" in ref]
    # Every model call is still a receipted child of the ONE utterance parent.
    parent = _parents(db)[0]
    children = _operations(db, name="inference.invoke")
    assert len(children) == 2
    assert {row["parent_operation_id"] for row in children} == {parent["operation_id"]}
    # And the egress label is the FROZEN revision's own boundary, not a default.
    assert response["egress_boundary"] == "local"  # the profile is on 127.0.0.1
    assert response["text"] == "REWRITTEN"


def test_the_egress_label_follows_the_frozen_revision_off_this_machine(
    tmp_path, monkeypatch
):
    """The label is derived, never defaulted: a LAN endpoint is not "local"."""
    from holdspeak.speech_session import admit_one_shot_session

    db, _broker, host, _impl = _build_host(tmp_path, monkeypatch)
    db.profiles.upsert(
        profile_id="prof_lan", name="prof_lan", kind="openAICompatible",
        base_url="http://192.168.1.43:8080/v1", model="qwen-lan",
    )
    host.config.dictation.pipeline.enabled = True
    host.config.dictation.pipeline.stages = ["project-rewriter"]
    host.config.dictation.runtime.profile_id = "prof_lan"

    session = admit_one_shot_session(
        principal=_browser_principal(), config_snapshot=host.config
    )
    assert session.provider().egress_boundary == "private_network"
    session.close("succeeded")


def test_a_classify_only_pipeline_reports_the_classify_revisions_boundary(
    tmp_path, monkeypatch
):
    """Sol round 3: rewrite being unplanned must not launder classify to "local".

    A pipeline with only the intent router still freezes intent-classify on the
    remote revision; the combined no-argument label reports THAT boundary, not a
    rewrite-shaped default.
    """
    from holdspeak.speech_session import admit_one_shot_session

    db, _broker, host, _impl = _build_host(tmp_path, monkeypatch)
    db.profiles.upsert(
        profile_id="prof_lan_c", name="prof_lan_c", kind="openAICompatible",
        base_url="http://192.168.1.43:8080/v1", model="qwen-lan",
    )
    host.config.dictation.pipeline.enabled = True
    host.config.dictation.pipeline.stages = ["intent-router"]  # no rewriter
    host.config.dictation.runtime.profile_id = "prof_lan_c"

    session = admit_one_shot_session(
        principal=_browser_principal(), config_snapshot=host.config
    )
    plan = session.plan
    assert plan.has("intent-classify") and not plan.has("rewrite")
    assert session.provider().egress_boundary == "private_network"
    session.close("succeeded")


def test_a_stop_between_wake_admission_and_registration_cancels_the_parent(
    tmp_path, monkeypatch
):
    """Sol round 2, blocker 2: a session admitted across the stop boundary loses.

    The stop lands in the exact window between ``admit_wake_session`` returning and
    the session being published in the slot — where the slot was still empty and
    the capture used to survive.
    """
    db, _broker, host, impl = _build_host(tmp_path, monkeypatch)
    host.config.wake_word.enabled = True
    host._wake_listener = None
    host._wake_stream = None
    host._wake_queue = None
    typed: list[str] = []
    monkeypatch.setattr(
        "holdspeak.desktop_typing.type_text_from_owner_gesture",
        lambda text, **kwargs: typed.append(text),
    )

    real = host._admit_wake_session
    stopped: list[bool] = []

    def racing(cfg: Any):
        session = real(cfg)
        if not stopped:
            stopped.append(True)
            host._stop_wake_listener()  # the slot is still EMPTY here
        return session

    host._admit_wake_session = racing

    host._transcribe_wake(np.full(16000, AUDIO_SENTINEL, dtype=np.float32))

    parents = _parents(db, "wake.session")
    assert [row["state"] for row in parents] == ["CANCELLED"]
    assert (_receipt(db, parents[0]["operation_id"]) or {}).get("outcome") == "cancelled"
    # The audio was discarded: no Whisper dispatch, no child, no typing, no preview.
    assert impl.calls == []
    assert _operations(db, name="inference.invoke") == []
    assert typed == []
    assert host.wake_previews == {}
    # The slot is empty and a further stop has nothing to cancel.
    assert host._wake_session is None
    assert host._cancel_wake_session() == ""
    assert ("complete", "wake_session_stopped") in host.activities
