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
    hold_gesture_principal,
    preload_service_admission,
    wake_config_revision,
    whisper_deployment_identity,
)
from holdspeak.speech_session.child import invocation_id
from holdspeak.speech_session.plan import (
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

    def _ensure_transcriber_loaded(self, **kwargs: Any) -> Any:
        self.transcriber_arguments = dict(kwargs)
        return self.transcriber

    def _mark_first_dictation(self) -> None:
        return None

    def _maybe_run_dictation_pipeline(self, text: str, **kwargs: Any) -> str:
        return text


def _build_host(
    tmp_path: Path,
    monkeypatch,
    *,
    legacy: bool | None = True,
    backend: str = "auto",
    **floor_kwargs: Any,
):
    from holdspeak.runtime.dictation_capture import DictationCaptureMixin
    from holdspeak.runtime.wake_glue import WakeWordGlueMixin

    class Host(_Host, DictationCaptureMixin, WakeWordGlueMixin):
        pass

    db = Database(tmp_path / "speech.db")
    config = Config()
    config.model.backend = backend
    # Startup owns the real speech migration.  The test supplies its saved
    # configuration before startup rather than repairing the resulting route.
    monkeypatch.setattr("holdspeak.config.Config.load", lambda: config)
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    broker = _configure(db)
    # These inherited HS-131 proofs reconstruct v1 parents.  Phase-D tests use
    # the production migration API to activate BOTH coupled markers; no test
    # writes a marker directly.
    if legacy is True:
        with db._connection() as conn:
            conn.execute(
                "DELETE FROM inference_assignment_migrations "
                "WHERE family='speech-recognition-route-assignments'"
            )
            conn.commit()
    elif legacy is False:
        from tests.unit.test_phase143_inference_assignments import _profile, _result_claim

        provider_capabilities = (
            "thought.interview", "ask.answer", "speech.intent_classify", "speech.rewrite"
        )
        _profile(
            db,
            "phase-d-coupled-profile",
            claims=(
                "language",
                "structured_output",
                *(_result_claim(capability) for capability in provider_capabilities),
            ),
        )
        config.thoughts.inference_target_id = "phase-d-coupled-profile"
        config.dictation.runtime.profile_id = "phase-d-coupled-profile"
        migrated = broker.inference_adoption_service.migrate_legacy_config(
            hold_gesture_principal(), config
        )
        assert migrated["status"] == "migrated"
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


def _install_historical_nonlocal_speech_assignment(db: Database, boundary: str) -> None:
    """Persist one pre-Amendment legacy assignment, never a route plan.

    V1 profile rows are retained migration history. They are the only truthful
    way to present an already-saved nonlocal speech selection to the current
    local-only planner: creating it through today's assignment API would (and
    should) reject it before route admission. The current planner must still
    reject the old row before it can mint a parent or construct a transcriber.
    """
    from holdspeak.services.inference_assignment_service import (
        ASSIGNMENT_SCHEMA,
        InferenceAssignmentService,
        _canonical,
        _sha256,
    )

    if boundary == "mesh":
        profile_id = "historical-mesh-speech"
        db.profiles.upsert(
            profile_id=profile_id,
            name="Historical mesh speech",
            kind="meshNode",
            node="historical-mesh-node",
            model="speech-mesh-model",
        )
    elif boundary == "private_network":
        profile_id = "historical-private-speech"
        db.profiles.upsert(
            profile_id=profile_id,
            name="Historical private speech",
            kind="openAICompatible",
            base_url="http://192.168.1.70:8080/v1",
            model="speech-private-model",
        )
    else:  # pragma: no cover - fixed parametrization below
        raise AssertionError(boundary)

    assignments = InferenceAssignmentService(db)
    scope = assignments._scope({"kind": "capability", "capability_id": "speech.transcribe"})
    created_at = "2026-08-24T00:00:00Z"
    assignment_id = f"ia_historical_{boundary}_speech"
    entry = {
        "ordinal": 1,
        "profile_id": f"legacy-{profile_id}",
        "profile_revision": 1,
        "profile_schema_version": 1,
    }
    with db._connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            head = conn.execute(
                "SELECT revision FROM inference_assignment_heads WHERE assignment_key=?",
                (scope["assignment_key"],),
            ).fetchone()
            revision = 1 if head is None else int(head["revision"]) + 1
            material = {
                "schema": ASSIGNMENT_SCHEMA,
                "id": assignment_id,
                "scope": assignments._public_scope(scope),
                "entries": [entry],
                "retry_policy_id": None,
                "revision": revision,
                "created_at": created_at,
            }
            conn.execute(
                """INSERT INTO inference_assignment_revisions
                   (assignment_id,revision,assignment_key,scope_kind,scope_id,
                    subject_kind,selector_kind,capability_id,group_id,retry_policy_id,
                    payload_json,sha256,created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    assignment_id, revision, scope["assignment_key"], "global", "", "",
                    "capability", "speech.transcribe", "", None,
                    _canonical(material), _sha256(material), created_at,
                ),
            )
            conn.execute(
                """INSERT INTO inference_assignment_heads
                   (assignment_key,assignment_id,revision,cleared,updated_at)
                   VALUES (?,?,?,?,?)
                   ON CONFLICT(assignment_key) DO UPDATE SET
                     assignment_id=excluded.assignment_id,revision=excluded.revision,
                     cleared=excluded.cleared,updated_at=excluded.updated_at""",
                (scope["assignment_key"], assignment_id, revision, 0, created_at),
            )
            conn.execute(
                """INSERT INTO inference_assignments
                   (id,assignment_id,assignment_revision,profile_id,profile_revision,
                    profile_schema_version,ordinal)
                   VALUES (?,?,?,?,?,?,?)""",
                (
                    f"{assignment_id}:{revision}:1", assignment_id, revision,
                    entry["profile_id"], 1, 1, 1,
                ),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise


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
    assert str(row["authority_basis"]) == "wake-capture:configured-capture"
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


def _production_cold_mlx_transcriber(monkeypatch):
    """Construct HoldSpeak's real MLX transcriber; bound calls are external only."""
    from mlx_whisper.transcribe import ModelHolder

    physical_loads: list[tuple[Any, ...]] = []

    def external_model_holder(*args: Any, **kwargs: Any) -> object:
        physical_loads.append(tuple(args))
        return object()

    # These two monkeypatches are the mlx-whisper library physical boundary, not
    # a HoldSpeak object or admission/controller substitute.
    monkeypatch.setattr(ModelHolder, "get_model", external_model_holder)
    transcriber = Transcriber(model_name="base", backend="mlx", language="auto")
    assert isinstance(transcriber._impl, _MlxTranscriber)
    monkeypatch.setattr(
        transcriber._impl._mlx_whisper,
        "transcribe",
        lambda *_args, **_kwargs: {"text": TEXT_SENTINEL},
    )
    assert transcriber.loaded is False
    return transcriber, physical_loads


def test_phase_d_cold_wake_derives_one_preload_from_its_frozen_service_route(
    tmp_path, monkeypatch
):
    """R2: a cold normal wake owns one local preload, then one transcript."""
    db, _broker, host, _unused = _build_host(tmp_path, monkeypatch, legacy=False)
    host.config.wake_word.enabled = True
    # This ordinary wake configuration has no configured provider-backed tail:
    # wake-capture@1 is intentionally closed to its two speech capabilities.
    host.config.dictation.pipeline.enabled = False
    transcriber, physical_loads = _production_cold_mlx_transcriber(monkeypatch)
    host.transcriber = transcriber

    host._transcribe_wake(np.full(16000, AUDIO_SENTINEL, dtype=np.float32))

    parent = _parents(db, "wake.session")[0]
    assert (parent["principal_kind"], parent["principal_identity"]) == (
        "service", "wake-capture"
    )
    assert parent["authority_basis"] == "wake-capture:configured-capture"
    assert "wake_capture_revision" in str(parent["input_json"])
    assert transcriber.loaded is True
    assert len(physical_loads) == 1
    with db._connection() as conn:
        members = list(conn.execute(
            "SELECT capability_id FROM inference_parent_route_bundle_members "
            "WHERE bundle_id=(SELECT id FROM inference_parent_route_bundles "
            "WHERE parent_operation_id=?) ORDER BY ordinal",
            (parent["operation_id"],),
        ))
        executions = list(conn.execute(
            """SELECT p.capability_id,e.terminal_outcome
                 FROM inference_route_executions e
                 JOIN inference_route_plans p ON p.id=e.route_plan_id
                 JOIN inference_route_attempts a ON a.execution_id=e.id
                 JOIN kernel_operations o ON o.operation_id=a.child_operation_id
                 WHERE o.parent_operation_id=? ORDER BY e.rowid""",
            (parent["operation_id"],),
        ))
        preload_assignments = conn.execute(
            "SELECT COUNT(*) FROM inference_assignment_heads WHERE assignment_key=?",
            ("capability:speech.preload",),
        ).fetchone()[0]
    assert [row["capability_id"] for row in members] == [
        "speech.transcribe", "speech.preload"
    ]
    assert [tuple(row) for row in executions] == [
        ("speech.preload", "succeeded"), ("speech.transcribe", "succeeded")
    ]
    assert preload_assignments == 0
    assert not [row for row in _parents(db) if row["principal_kind"] == "owner"]
    children = _operations(db, name="inference.invoke")
    assert len(children) == 2
    assert {row["parent_operation_id"] for row in children} == {parent["operation_id"]}
    assert all((_receipt(db, row["operation_id"]) or {})["outcome"] == "succeeded" for row in children)


def test_phase_d_faster_whisper_constructs_after_frozen_local_route_then_transcribes(
    tmp_path, monkeypatch
):
    """R5: construction is the ratified library boundary, not an execution."""
    import sys
    from types import ModuleType, SimpleNamespace

    from holdspeak.runtime.transcriber_state import TranscriberStateMixin
    from holdspeak.speech_session import admit_one_shot_session

    constructed: list[tuple[str, str, str]] = []
    audio_calls: list[int] = []
    external = ModuleType("faster_whisper")

    class WhisperModel:
        def __init__(self, model_name: str, *, device: str, compute_type: str) -> None:
            constructed.append((model_name, device, compute_type))

        def transcribe(self, audio: Any, **_kwargs: Any) -> tuple[list[Any], Any]:
            audio_calls.append(int(np.asarray(audio).size))
            return [SimpleNamespace(text=TEXT_SENTINEL)], SimpleNamespace()

    external.WhisperModel = WhisperModel
    monkeypatch.setitem(sys.modules, "faster_whisper", external)
    real_available = __import__("holdspeak.transcribe", fromlist=["_module_available"])._module_available
    monkeypatch.setattr(
        "holdspeak.transcribe._module_available",
        lambda module: True if module == "faster_whisper" else real_available(module),
    )

    db, _broker, host, _impl = _build_host(
        tmp_path, monkeypatch, legacy=False, backend="faster-whisper"
    )
    session = admit_one_shot_session(
        principal=hold_gesture_principal(), config_snapshot=host.config
    )
    frozen = session.frozen_transcriber_arguments()
    assert {key: frozen[key] for key in ("model_name", "backend", "language")} == {
        "model_name": "base", "backend": "faster-whisper", "language": "auto"
    }
    assert str(frozen["deployment_revision_id"]).startswith("dep2_")
    assert constructed == []
    assert _operations(db, name="inference.invoke") == []

    class Runtime(TranscriberStateMixin):
        def __init__(self) -> None:
            self.config = host.config
            self.state_lock = threading.RLock()
            self.runtime_status: dict[str, Any] = {}
            self._transcriber_init_lock = threading.RLock()
            self.transcriber = None

        def _set_runtime_activity(self, *_args: Any, **_kwargs: Any) -> None:
            return None

    runtime = Runtime()
    transcriber = runtime._ensure_transcriber_loaded(**frozen)
    assert constructed == [("base", "cpu", "int8")]
    assert _operations(db, name="inference.invoke") == []

    assert transcriber.transcribe(
        np.full(8000, AUDIO_SENTINEL, dtype=np.float32), admission=session.transcription()
    ) == TEXT_SENTINEL
    assert audio_calls == [8000]
    children = _operations(db, name="inference.invoke")
    assert len(children) == 1
    assert children[0]["parent_operation_id"] == session.operation_id
    assert (_receipt(db, children[0]["operation_id"]) or {})["outcome"] == "succeeded"
    with db._connection() as conn:
        boundary = conn.execute(
            """SELECT a.boundary FROM inference_route_attempts a
                 JOIN kernel_operations o ON o.operation_id=a.child_operation_id
                 WHERE o.operation_id=?""",
            (children[0]["operation_id"],),
        ).fetchone()[0]
    assert boundary == "local"
    session.close("succeeded")


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


def test_phase_d_wake_revision_is_parent_evidence_not_principal_schema_drift(
    tmp_path, monkeypatch
):
    """R3: two configured wake admissions retain distinct immutable revisions."""
    import json

    db, broker, host, _impl = _build_host(tmp_path, monkeypatch, legacy=False)
    host.config.wake_word.enabled = True
    host.config.dictation.pipeline.enabled = False

    first_revision = wake_config_revision(host.config.wake_word)
    first = admit_wake_session(wake_config=host.config.wake_word, config_snapshot=host.config)
    first_parent = _parents(db, "wake.session")[0]
    host.config.wake_word.action = "type"
    second_revision = wake_config_revision(host.config.wake_word)
    second = admit_wake_session(wake_config=host.config.wake_word, config_snapshot=host.config)
    parents = _parents(db, "wake.session")
    second_parent = parents[1]

    first_snapshot = json.loads(first_parent["input_json"])
    second_snapshot = json.loads(second_parent["input_json"])
    assert first_snapshot["wake_capture_revision"] == first_revision
    assert second_snapshot["wake_capture_revision"] == second_revision
    assert first_snapshot["wake_capture_revision"] != second_snapshot["wake_capture_revision"]

    with db._connection() as conn:
        route_ids = [
            row["route_plan_id"]
            for parent in (first_parent, second_parent)
            for row in conn.execute(
                """SELECT route_plan_id FROM inference_parent_route_bundle_members
                     WHERE bundle_id=(SELECT id FROM inference_parent_route_bundles
                                      WHERE parent_operation_id=?)
                       AND capability_id='speech.transcribe'""",
                (parent["operation_id"],),
            )
        ]
        reconstructed = [
            broker.inference_adoption_service.plans._route_from_row(
                conn,
                conn.execute("SELECT * FROM inference_route_plans WHERE id=?", (route_id,)).fetchone(),
            )
            for route_id in route_ids
        ]
        evidence = [
            json.loads(conn.execute(
                "SELECT payload_json FROM inference_route_plan_principal_evidence WHERE plan_id=?",
                (route_id,),
            ).fetchone()[0])
            for route_id in route_ids
        ]
    assert all(route["capability"]["id"] == "speech.transcribe" for route in reconstructed)
    for policy in evidence:
        assert policy["schema"] == "InferenceFeaturePrincipalPolicyEvidence@1"
        assert policy["policy_id"] == "wake-capture@1"
        assert policy["policy_revision"] == 1
        assert policy["principal_identity"] == "wake-capture"
        assert policy["authority_basis"] == "wake-capture:configured-capture"
        assert policy["parent_kind"] == "wake.session"
        assert "wake_capture_revision" not in policy
    first.close("succeeded")
    second.close("succeeded")


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


def test_phase_d_day_one_standalone_speak_to_fill_uses_the_migrated_route(
    tmp_path, monkeypatch
):
    """Amendment 5: fresh startup needs no profile/assignment/readiness repair.

    This drives the real startup migration, one real short ``dictation.session``,
    its atomic bundle, the controller-owned P=1 preload, and the routed semantic
    transcript adapter.  Only the MLX physical floor is faked.
    """
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from holdspeak.transcribe import _resolve_backend

    db, broker, host, _unused = _build_host(tmp_path, monkeypatch, legacy=False)
    assert host.config.model.backend == "auto"
    assignments = InferenceAssignmentService(db).list_assignments(
        hold_gesture_principal()
    )["assignments"]
    scopes = [item["scope"].get("capability_id") for item in assignments]
    assert scopes.count("speech.transcribe") == 1
    assert "speech.preload" not in scopes

    impl = _Mlx(holder_ok=True)
    impl._candidates = (
        "mlx-community/whisper-base-mlx", "mlx-community/whisper-base"
    )
    host.transcriber = _transcriber(impl)
    text = host.transcribe_audio(np.full(8000, AUDIO_SENTINEL, dtype=np.float32))

    assert text == TEXT_SENTINEL
    assert {key: host.transcriber_arguments[key] for key in ("model_name", "backend", "language")} == {
        "model_name": "base",
        "backend": _resolve_backend("auto"),
        "language": "auto",
    }
    assert str(host.transcriber_arguments["deployment_revision_id"]).startswith("dep2_")
    parent = _parents(db, "dictation.session")[0]
    assert parent["state"] == "SUCCEEDED"
    with db._connection() as conn:
        members = list(conn.execute(
            "SELECT capability_id FROM inference_parent_route_bundle_members "
            "WHERE bundle_id=(SELECT id FROM inference_parent_route_bundles "
            "WHERE parent_operation_id=?) ORDER BY ordinal",
            (parent["operation_id"],),
        ))
        outcomes = list(conn.execute(
            """SELECT p.capability_id,e.terminal_outcome
                 FROM inference_route_executions e
                 JOIN inference_route_plans p ON p.id=e.route_plan_id
                ORDER BY e.rowid"""
        ))
        readiness = conn.execute(
            """SELECT o.state,o.reason_code
                 FROM model_profile_binding_heads h
                 JOIN model_profile_binding_revisions b
                   ON b.binding_id=h.binding_id AND b.revision=h.revision
                 JOIN model_profile_readiness_observations o
                   ON o.observation_id=b.readiness_observation_id
                WHERE b.profile_id LIKE 'speech-migrated-%'"""
        ).fetchone()
    assert [row["capability_id"] for row in members] == [
        "speech.transcribe", "speech.intent_classify", "speech.preload"
    ]
    assert [tuple(row) for row in outcomes] == [
        ("speech.preload", "succeeded"), ("speech.transcribe", "succeeded")
    ]
    assert tuple(readiness) == ("ready", "loaded_under_speech_preload")


def test_phase_d_couples_speech_and_writing_markers_for_one_complete_pipeline(
    tmp_path, monkeypatch
):
    """R4: partial migration stays v1; both markers produce one all-routed parent."""
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from holdspeak.speech_session import admit_one_shot_session
    from holdspeak.speech_session.plan import pipeline_provider_capabilities

    def configured_rewrite(session: Any) -> str:
        runtime = _PipelineBackend()
        # The test backend is the physical provider boundary. Legacy resolution
        # freezes the configured 127.0.0.1 profile; the migrated assignment
        # freezes the production on-device profile created by ``_build_host``.
        if session._route_bundle is None:
            runtime.base_url = "http://127.0.0.1:1234/v1"
            runtime.model = "qwen-local"
        else:
            runtime.backend = "local"
            runtime.model = ""
        return session.provider().rewrite(runtime, "rewrite this", max_tokens=32, temperature=0.0)

    # Startup's real speech migration with no writing marker remains wholly
    # legacy. ``legacy=None`` retains that production startup state unchanged.
    db, _broker, host, _unused = _build_host(tmp_path, monkeypatch, legacy=None)
    db.profiles.upsert(
        profile_id="phase-d-legacy-pipeline",
        name="Phase D legacy pipeline",
        kind="openAICompatible",
        base_url="http://127.0.0.1:1234/v1",
        model="qwen-local",
    )
    host.config.dictation.pipeline.enabled = True
    host.config.dictation.pipeline.stages = ["project-rewriter"]
    host.config.dictation.runtime.profile_id = "phase-d-legacy-pipeline"
    assert InferenceAssignmentService(db).migration_marker(
        hold_gesture_principal(), family="thoughts-writing-route-assignments"
    ) is None
    assert pipeline_provider_capabilities(host.config) == ("rewrite",)
    legacy = admit_one_shot_session(
        principal=hold_gesture_principal(), config_snapshot=host.config
    )
    assert legacy._route_bundle is None
    assert legacy.plan.has("rewrite"), legacy.plan.summary()
    assert _transcriber(FakeImpl()).transcribe(
        np.full(8000, AUDIO_SENTINEL, dtype=np.float32), admission=legacy.transcription()
    ) == TEXT_SENTINEL
    assert configured_rewrite(legacy) == "REWRITTEN"
    legacy_children = _operations(db, name="inference.invoke")
    assert len(legacy_children) == 2
    assert {row["parent_operation_id"] for row in legacy_children} == {legacy.operation_id}
    legacy.close("succeeded")

    # The same normal pipeline after both production migrations freezes all of
    # its configured routes in one parent bundle and never emits a plain child.
    routed_tmp = tmp_path / "routed"
    routed_tmp.mkdir()
    db, _broker, host, _unused = _build_host(routed_tmp, monkeypatch, legacy=False)
    host.config.dictation.pipeline.enabled = True
    host.config.dictation.pipeline.stages = ["project-rewriter"]
    routed = admit_one_shot_session(
        principal=hold_gesture_principal(), config_snapshot=host.config
    )
    assert routed._route_bundle is not None
    assert _transcriber(FakeImpl()).transcribe(
        np.full(8000, AUDIO_SENTINEL, dtype=np.float32), admission=routed.transcription()
    ) == TEXT_SENTINEL

    class RoutedEngine:
        active_provider = "fixture"
        active_model = "phase-d-coupled-profile"

        @staticmethod
        def run_prompt(**_kwargs: Any) -> str:
            return "REWRITTEN"

    # Only the physical configured-model edge is bounded. The production route
    # admission, controller, bundle, attempt, and receipt still execute intact.
    _broker.inference_runner._engine_factory = lambda _revision, **_kwargs: RoutedEngine()
    assert configured_rewrite(routed) == "REWRITTEN"
    members = [item["capability_id"] for item in routed._route_bundle["members"]]
    assert members == ["speech.transcribe", "speech.rewrite", "speech.preload"]
    routed_children = _operations(db, name="inference.invoke")
    assert len(routed_children) == 2
    with db._connection() as conn:
        routed_child_ids = {row["operation_id"] for row in routed_children}
        route_child_ids = {
            row["child_operation_id"]
            for row in conn.execute(
                "SELECT child_operation_id FROM inference_route_attempts "
                "WHERE child_operation_id IS NOT NULL"
            )
        }
    assert routed_child_ids == route_child_ids
    routed.close("succeeded")


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


def test_pre_session_warm_uses_the_assigned_speech_route_not_the_legacy_knob(tmp_path, monkeypatch):
    db, _broker, _host, _impl = _build_host(tmp_path, monkeypatch, legacy=False)
    config = Config()
    assert config.model.local_model_preload_authority == ""

    admission = preload_service_admission(config_snapshot=config)

    assert admission.principal.authority_basis == "local-model-preload:assigned-speech-route"
    assert admission.source_route["source"]["inherited_from"] == "capability"
    assert admission.preload_route["capability"]["id"] == "speech.preload"
    assert _operations(db, name="inference.invoke") == []
    assert _parents(db) == []


def test_authorized_pre_session_warm_runs_as_the_preload_service(tmp_path, monkeypatch):
    db, _broker, _host, _impl = _build_host(tmp_path, monkeypatch, legacy=False)
    config = Config()
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
    # A Phase-B meeting parent freezes its live+speech route bundle before an
    # interval can become an admitted transcription child.
    from tests.unit.test_meeting_session_admission import _assign_bundle_routes

    _assign_bundle_routes(db)
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
    # Phase B reserves the complete frozen live bundle: intelligence (4096),
    # speech preload (1), and its routed transcription allocation (17,286).
    # Keep the legacy helper's 8,418 calculation visible as historical-reader
    # coverage, but the new parent must carry the aggregate bundle budget.
    assert _budget() == 8418
    assert int(parents[0]["child_budget"]) == 21_383

    text = session._transcribe_audio(np.full(16000, AUDIO_SENTINEL, dtype=np.float32))
    assert text == TEXT_SENTINEL

    children = _operations(db, name="inference.invoke")
    assert len(children) == 1
    assert children[0]["parent_operation_id"] == parents[0]["operation_id"]
    # The child names the bundle's profile-backed immutable deployment (`dep2`),
    # not the mutable Config-derived startup speech revision (`dep`).
    assert str(children[0]["target_ref"]).startswith("deployment-revision:dep2_")
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
    # Pipeline explicitly OFF (HS-139-02 flipped the default to True): no
    # provider-backed stage is planned, so a stage dispatch would refuse by
    # name instead of silently reaching a model.
    config.dictation.pipeline.enabled = False
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

    db, _broker, _host, _impl = _build_host(tmp_path, monkeypatch, legacy=False)
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


def test_phase_d_browser_interval_keeps_its_full_capture_budget(tmp_path, monkeypatch):
    """A routed browser parent must not be limited to its one route declaration."""
    from holdspeak.speech_session import BROWSER_CHILD_BUDGET

    db, _broker, host, impl = _build_host(tmp_path, monkeypatch, legacy=False)
    registry = _sessions()
    principal = _browser_principal()
    interval = registry.open(principal, config_snapshot=host.config)
    audio = np.full(16000, AUDIO_SENTINEL, dtype=np.float32)

    for _ in range(4):
        assert host.transcribe_audio(audio, principal=principal, mic_handle=interval.handle) == TEXT_SENTINEL

    parent = _parents(db, "dictation.session")[0]
    assert int(parent["child_budget"]) == BROWSER_CHILD_BUDGET
    assert impl.calls == [16000] * 4
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

    # The model really ran, once...
    assert impl.calls == [16000]
    children = _operations(db, name="inference.invoke")
    assert len(children) == 1

    # ...and its child carries the terminal the CANCEL SIGNAL actually earned.
    #
    # HS-132-12: this pair is a race the kernel deliberately leaves unordered.
    # Cancelling the parent hands the in-flight child to a daemon thread
    # (`kernel/parent_terminal.py` — "do not let a provider's in-flight dispatch
    # hold the cancelling request hostage") and then closes the parent itself.
    # Whichever commits first decides the child: the signal reaching the adapter
    # cancels the dispatch; the parent closing first leaves the signal refused
    # `parent_operation_not_live` and the child closes on its own success. Both
    # are honest, so the test pins BOTH sides and the correlation between them
    # rather than one thread's win — pinning `succeeded` alone made this test
    # flake under `pytest -n auto`, where the daemon thread often gets there
    # first. The signal is asynchronous by design, so wait for its terminal
    # receipt instead of racing it.
    deadline = time.time() + 10.0
    signal_receipt: dict[str, Any] = {}
    while time.time() < deadline:
        signals = _operations(db, name="inference.cancel")
        if signals:
            signal_receipt = _receipt(db, signals[0]["operation_id"]) or {}
            if signal_receipt.get("outcome"):
                break
        time.sleep(0.01)
    assert signal_receipt.get("outcome"), "the cancel signal never reached a receipt"
    child_outcome = (_receipt(db, children[0]["operation_id"]) or {}).get("outcome")
    if signal_receipt["outcome"] == "succeeded":
        # Admitted: the signal names this child's invocation and cancelled it.
        assert str(signal_receipt.get("result_ref") or "").startswith("invocation:")
        assert child_outcome == "cancelled"
    else:
        # Refused: the parent closed first, so nothing ever touched the adapter.
        assert signal_receipt["outcome"] == "parent_operation_not_live"
        assert child_outcome == "succeeded"

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


# ----------------------------------- 6. legacy preload knobs have no authority


def test_mutable_preload_knobs_cannot_change_the_frozen_parentless_source(tmp_path, monkeypatch):
    """Warm authority is the persisted capability row, never ModelConfig bytes."""
    db, _broker, _host, _impl = _build_host(tmp_path, monkeypatch, legacy=False)
    config = Config()
    config.model.local_model_preload_authority = "yes-please"
    first = preload_service_admission(config_snapshot=config)
    config.model.name = "large"
    config.model.local_model_preload_authority = "another-unrelated-config-hash"
    second = preload_service_admission(config_snapshot=config)

    assert first.principal.authority_basis == second.principal.authority_basis == (
        "local-model-preload:assigned-speech-route"
    )
    assert first.source_route["source"] == second.source_route["source"]
    assert first.evidence["deployment_revision_id"] == second.evidence["deployment_revision_id"]
    assert _operations(db, name="inference.invoke") == []
    assert _parents(db) == []


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


def test_phase_d_local_transcription_route_reports_local_egress(tmp_path, monkeypatch):
    """Amendment 7: the ordinary migrated speech route remains local."""
    from holdspeak.speech_session import admit_one_shot_session

    _db, _broker, host, _impl = _build_host(tmp_path, monkeypatch, legacy=False)
    session = admit_one_shot_session(
        principal=_browser_principal(), config_snapshot=host.config
    )
    assert session._route_bundle is not None
    assert session.provider().egress_boundary == "local"
    session.close("succeeded")


@pytest.mark.parametrize("boundary", ["mesh", "private_network"])
def test_phase_d_nonlocal_historical_speech_refuses_before_construction_or_dispatch(
    tmp_path, monkeypatch, boundary
):
    """Amendment 7: current route admission refuses old nonlocal speech authority."""
    from holdspeak.speech_session import admit_one_shot_session

    db, _broker, host, _impl = _build_host(tmp_path, monkeypatch, legacy=False)
    _install_historical_nonlocal_speech_assignment(db, boundary)
    constructions: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    original_init = Transcriber.__init__

    def observed_init(self, *args: Any, **kwargs: Any) -> None:
        constructions.append((args, kwargs))
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(Transcriber, "__init__", observed_init)
    with pytest.raises(SpeechSessionRefused) as raised:
        admit_one_shot_session(
            principal=hold_gesture_principal(), config_snapshot=host.config
        )

    # The planner read the persisted historical assignment under the current
    # capability registry and refused its nonlocal boundary. No parent, frozen
    # plan, controller dispatch, construction, or receipt was possible first.
    assert raised.value.reason in {
        "inference_route_assignment_unavailable",
        "inference_route_boundary_unsupported",
        "no_compatible_assignment",
    }
    assert constructions == []
    assert _parents(db) == []
    assert _operations(db, name="inference.invoke") == []
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_route_plans").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM inference_route_attempts").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM kernel_receipts").fetchone()[0] == 0


def test_phase_d_egress_refuses_a_missing_frozen_transcription_entry(
    tmp_path, monkeypatch
):
    """A broken bundle cannot relabel an unknown transcription route ``local``."""
    from holdspeak.speech_session import admit_one_shot_session
    from holdspeak.speech_session.provider import ROUTED_EGRESS_ROUTE_MISSING

    db, _broker, host, _impl = _build_host(tmp_path, monkeypatch, legacy=False)
    session = admit_one_shot_session(
        principal=_browser_principal(), config_snapshot=host.config
    )
    assert session._route_bundle is not None
    route_id = next(
        str(item["route_plan_id"])
        for item in session._route_bundle["members"]
        if item["capability_id"] == "speech.transcribe"
    )
    with db._connection() as conn:
        conn.execute("DELETE FROM inference_route_plan_entries WHERE plan_id=?", (route_id,))
        conn.commit()

    with pytest.raises(SpeechSessionRefused) as excinfo:
        _ = session.provider().egress_boundary
    assert excinfo.value.reason == ROUTED_EGRESS_ROUTE_MISSING
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
