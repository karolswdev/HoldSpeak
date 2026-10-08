"""PHILO-15 10 — the engine setup tells the truth.

B05: READY only for a group the assignment authority serves in full; the
     receipt of "Use these" names LIMITED groups; "Use these" sets the
     Default for AI work once, when none ever existed.
B06: Speech recognition is proposed only from a speech engine.
The WAITING refusal is the server's, read from its own engine list.
The Check asks the server once whether it takes tool calls.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.services import concierge_service as cs
from holdspeak.services.errors import ConflictError
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.setup_runtime import endpoint_tool_support
from tests.unit.test_phase143_inference_assignments import OWNER, _profile, _result_claim

SUMMARY = "meeting.deferred_analysis"


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "engine-truth.db")


def _lan(db: Database, *, enforced: bool = True) -> dict:
    """A LAN chat engine with the claims the Model Library gives it."""
    from holdspeak.services.model_library_service import enforced_result_claims

    claims = ("language", *enforced_result_claims()) if enforced else ("language", _result_claim(SUMMARY))
    _profile(db, "lan-qwen", claims=claims, boundary="private_network")
    return {
        "id": "lan:lan-qwen", "kind": "lan", "name": "Qwen3.8 27B", "host": "192.168.1.43",
        "state": "READY", "profileId": "lan-qwen", "profileRevision": 1,
    }


def _heads(db: Database) -> list[str]:
    with db._connection() as conn:
        return [r["assignment_key"] for r in conn.execute("SELECT assignment_key FROM inference_assignment_heads")]


# ── the authority's read-only fit ────────────────────────────────────────


def test_fit_names_served_and_blocked_work_and_writes_nothing(db: Database) -> None:
    _lan(db, enforced=False)
    svc = InferenceAssignmentService(db)
    answer = svc.fit(OWNER, scope={"kind": "group", "group_id": "thoughts_notes"}, profile_id="lan-qwen")
    assert "chat.turn" in answer["served"] and "ask.answer" in answer["served"]
    assert answer["blocked"] == [
        {"capability_id": "thought.interview", "code": "structured_output_unsupported"}
    ]
    assert answer["saveable"] is True
    assert _heads(db) == []


def test_fit_reads_a_group_with_no_owner_work(db: Database) -> None:
    """Chat (compaction, guardrail) is never written; the fit still answers."""
    _lan(db, enforced=False)
    answer = InferenceAssignmentService(db).fit(
        OWNER, scope={"kind": "group", "group_id": "chat_practice"}, profile_id="lan-qwen",
    )
    assert answer["served"] == []
    assert {b["capability_id"] for b in answer["blocked"]} == {"chat.compact", "chat.guardrail"}


# ── propose: READY means ready; speech is speech ─────────────────────────


def test_propose_reads_ready_where_the_executor_enforces_and_limited_elsewhere(db: Database) -> None:
    """Astra r1 (finding 5): the library engine claims every result schema an
    executor checks, so only works nothing enforces keep a group LIMITED."""
    lan = _lan(db)
    svc = InferenceAssignmentService(db)
    result = cs.propose(engines=[lan], fit=cs.authority_fit(svc, OWNER, db))
    rows = {r["group"]: r for r in result["rows"]}
    assert "chat_practice" not in rows  # internal works are not an owner row
    assert rows["thoughts_notes"]["state"] == "READY"
    assert rows["writing_dictation"]["state"] == "READY"
    assert rows["meetings"]["state"] == "READY"
    assert rows["agents_tools"]["state"] == "LIMITED"
    assert rows["agents_tools"]["blocked"] == ["Agents"]
    assert rows["background"]["state"] == "LIMITED"
    assert rows["background"]["blocked"] == ["Calendar", "Memory"]
    # Every engine the picker offers carries its own answer.
    assert rows["agents_tools"]["fits"][lan["id"]]["state"] == "LIMITED"


def test_a_work_with_its_own_engine_is_not_a_limit(db: Database) -> None:
    lan = _lan(db)
    _profile(db, "embedder", claims=("language", "embedding"), modalities=("language",))
    svc = InferenceAssignmentService(db)
    svc.set_assignment(OWNER, {
        "command_id": "embed-own", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "memory.embed"},
        "entries": [{"profile_id": "embedder", "profile_revision": 1}],
    })
    rows = {r["group"]: r for r in cs.propose(engines=[lan], fit=cs.authority_fit(svc, OWNER, db))["rows"]}
    assert rows["background"]["blocked"] == ["Calendar"]


def _thought_override(db: Database, svc: InferenceAssignmentService, *, ready: bool = True) -> None:
    _profile(db, "thinker", claims=("language", _result_claim("thought.interview")), ready=ready,
             boundary="private_network")
    svc.set_assignment(OWNER, {
        "command_id": "thought-own", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "thought.interview"},
        "entries": [{"profile_id": "thinker", "profile_revision": 1}],
    })


def _thoughts_row(db: Database, svc: InferenceAssignmentService) -> dict:
    lan = _lan(db, enforced=False)  # an older, language-only candidate
    return {r["group"]: r for r in cs.propose(engines=[lan], fit=cs.authority_fit(svc, OWNER, db))["rows"]}[
        "thoughts_notes"]


def test_a_ready_own_assignment_serves_the_work(db: Database) -> None:
    svc = InferenceAssignmentService(db)
    _thought_override(db, svc)
    assert _thoughts_row(db, svc)["state"] == "READY"


def test_an_unbound_own_assignment_serves_nothing(db: Database) -> None:
    """Astra r2 (finding 2): an uncleared head whose profile lost its binding
    does not make the group READY; the group stays LIMITED."""
    svc = InferenceAssignmentService(db)
    _thought_override(db, svc)
    with db._connection() as conn:
        conn.execute("DELETE FROM model_profile_binding_heads WHERE profile_id='thinker'")
    row = _thoughts_row(db, svc)
    assert row["state"] == "LIMITED"
    assert row["blocked"] == ["Thoughts"]


def test_a_not_ready_own_assignment_serves_nothing(db: Database) -> None:
    svc = InferenceAssignmentService(db)
    _thought_override(db, svc, ready=False)
    row = _thoughts_row(db, svc)
    assert row["state"] == "LIMITED"


def test_the_library_profile_claims_what_executors_enforce() -> None:
    from holdspeak.services.model_library_service import enforced_result_claims

    claims = set(enforced_result_claims())
    for capability in ("thought.interview", "speech.intent_classify", "meeting.plugin.decision_capture"):
        assert _result_claim(capability) in claims
    for capability in ("agent.plan", "agent.tool_turn"):
        assert _result_claim(capability) not in claims
    # calendar.snapshot_extract shares a result schema with an enforced work;
    # it stays blocked by its vision requirement (the background fit above).


def test_propose_reads_unknown_when_the_engine_has_no_record(db: Database) -> None:
    engine = {"id": "local:loopback", "kind": "local", "name": "Qwen", "host": "THIS DEVICE", "state": "READY"}
    result = cs.propose(engines=[engine], fit=cs.authority_fit(InferenceAssignmentService(db), OWNER, db))
    rows = {r["group"]: r for r in result["rows"]}
    assert rows["thoughts_notes"]["state"] == "UNKNOWN"


def test_speech_is_never_proposed_from_a_chat_preset() -> None:
    preset = {"id": "preset:qwen", "kind": "preset", "name": "Quick local Qwen", "host": "THIS DEVICE",
              "state": "WAITING", "presetId": "preset_local_qwen35_4b_gguf_q4km"}
    rows = {r["group"]: r for r in cs.propose(engines=[preset])["rows"]}
    assert rows["speech_recognition"]["state"] == "WAITING"
    assert rows["speech_recognition"]["engineId"] is None
    assert "presetId" not in rows["speech_recognition"]


def test_speech_takes_the_device_whisper_and_text_groups_never_do() -> None:
    whisper = {"id": "local:whisper:mlx:base", "kind": "local", "name": "Whisper base", "host": "THIS DEVICE",
               "state": "READY", "audioCapable": True, "supportedModalities": ["audio"]}
    rows = {r["group"]: r for r in cs.propose(engines=[whisper])["rows"]}
    assert rows["speech_recognition"]["engineId"] == "local:whisper:mlx:base"
    assert rows["speech_recognition"]["state"] == "READY"
    assert rows["writing_dictation"]["engineId"] != "local:whisper:mlx:base"
    assert rows["thoughts_notes"]["engineId"] != "local:whisper:mlx:base"


def test_detect_lists_the_device_whisper(db: Database, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import holdspeak.whisper_models as wm

    monkeypatch.setattr(wm, "whisper_on_disk", lambda name, backend, home=None: True)
    row = cs._device_whisper(db, tmp_path)
    assert row is not None
    assert row["name"].startswith("Whisper ")
    assert row["supportedModalities"] == ["audio"]


# ── apply: the server refuses WAITING; the receipt tells LIMITED ─────────


def test_apply_refuses_a_row_that_calls_a_preset_ready(db: Database) -> None:
    preset = {"id": "preset:qwen", "kind": "preset", "state": "WAITING", "presetId": "p"}
    with pytest.raises(ConflictError) as caught:
        cs.apply(
            rows=[{"group": "speech_recognition", "engineId": "preset:qwen", "state": "READY"}],
            engines=[preset], assignment_service=InferenceAssignmentService(db), principal=OWNER, db=db,
        )
    assert caught.value.code == "concierge_waiting_group"
    assert caught.value.detail == "Speech recognition waits for a download."


def test_apply_still_refuses_a_waiting_row(db: Database) -> None:
    with pytest.raises(ConflictError) as caught:
        cs.apply(
            rows=[{"group": "speech_recognition", "engineId": None, "state": "WAITING"}],
            engines=[], assignment_service=InferenceAssignmentService(db), principal=OWNER, db=db,
        )
    assert caught.value.code == "concierge_waiting_group"


def test_apply_reports_limited_and_sets_the_default_once(db: Database) -> None:
    lan = _lan(db)
    svc = InferenceAssignmentService(db)
    result = cs.apply(
        rows=[
            {"group": "thoughts_notes", "engineId": lan["id"], "state": "LIMITED"},
            {"group": "agents_tools", "engineId": lan["id"], "state": "LIMITED"},
        ],
        engines=[lan], assignment_service=svc, principal=OWNER, db=db,
    )
    by_group = {r["group"]: r for r in result["results"]}
    assert by_group["thoughts_notes"]["state"] == "READY"
    assert by_group["agents_tools"]["state"] == "LIMITED"
    assert by_group["agents_tools"]["blocked"] == ["Agents"]
    assert result["summary"]["limited"] == 1
    assert result["summary"]["engine"] == "Qwen3.8 27B"
    assert result["summary"]["default"]["engineId"] == lan["id"]
    assert "global" in _heads(db)
    # A second press never changes the default it set.
    again = cs.apply(
        rows=[{"group": "thoughts_notes", "engineId": lan["id"], "state": "LIMITED"}],
        engines=[lan], assignment_service=svc, principal=OWNER, db=db,
    )
    assert again["summary"]["default"] is None


def test_partial_limits_are_not_repair_rows(db: Database) -> None:
    lan = _lan(db, enforced=False)
    svc = InferenceAssignmentService(db)
    cs.apply(
        rows=[{"group": "thoughts_notes", "engineId": lan["id"], "state": "LIMITED"}],
        engines=[lan], assignment_service=svc, principal=OWNER, db=db,
    )
    rows = cs.repairs(db=db, assignment_service=svc, principal=OWNER)
    # The set row says LIMITED; no repair row says it again. (Speech, with
    # no Whisper on this desk, inherits the text default and IS a repair.)
    assert not [
        r for r in rows
        if r["token"] == "TOOL INCOMPATIBLE" and "thoughts_notes" in r["groups"]
    ], rows


# ── the Check asks the server about tool calls ───────────────────────────


def _props(supports: bool):
    body = json.dumps({"chat_template_caps": {"supports_tools": supports}}).encode()
    return lambda url, headers, timeout: (200, body)


def _no_props(url, headers, timeout):
    return 404, b""


def test_tools_from_llama_cpp_props() -> None:
    assert endpoint_tool_support("http://10.0.0.2:8080/v1", model="m", http_get=_props(True)) == "yes"
    assert endpoint_tool_support("http://10.0.0.2:8080/v1", model="m", http_get=_props(False)) == "no"


def test_tools_from_a_one_token_probe_on_the_lan() -> None:
    sent: list[dict] = []

    def post(url, headers, body, timeout):
        sent.append(json.loads(body))
        return 400, b"tools param requires --jinja flag"

    assert endpoint_tool_support("http://10.0.0.2:8080/v1", model="m", http_get=_no_props, http_post=post) == "no"
    assert sent[0]["max_tokens"] == 1 and sent[0]["tools"]


def test_a_cloud_check_never_spends_a_token() -> None:
    def post(*_a, **_k):  # pragma: no cover - must not be called
        raise AssertionError("cloud probe spent a token")

    assert endpoint_tool_support("https://api.example.com/v1", model="m", lan=False,
                                 http_get=_no_props, http_post=post) == "unknown"


def test_models_capabilities_claim_tools() -> None:
    assert endpoint_tool_support("http://10.0.0.2/v1", model="m", tools_claimed=True) == "yes"


def test_a_written_limited_group_is_an_applied_receipt(db: Database) -> None:
    """Astra r1 (finding 3): LIMITED was written, so the durable outcome is
    succeeded; only a group not written fails it."""
    lan = _lan(db)
    result = cs.apply(
        rows=[{"group": "agents_tools", "engineId": lan["id"], "state": "LIMITED"}],
        engines=[lan], assignment_service=InferenceAssignmentService(db), principal=OWNER, db=db,
    )
    with db._connection() as conn:
        row = conn.execute("SELECT state, outcome FROM kernel_receipts WHERE receipt_id=?", (result["receipt"],)).fetchone()
    assert row["state"] == "succeeded", dict(row)
    assert row["outcome"] == "Applied 1 group(s)"


def test_a_failed_group_carries_its_token(db: Database) -> None:
    engine = {"id": "lan:bare", "kind": "lan", "name": "Bare", "host": "10.0.0.9", "state": "READY"}
    result = cs.apply(
        rows=[{"group": "thoughts_notes", "engineId": "lan:bare", "state": "UNKNOWN"},
              {"group": "background", "engineId": "lan:bare", "state": "UNKNOWN"}],
        engines=[engine], assignment_service=InferenceAssignmentService(db), principal=OWNER, db=db,
    )
    assert [(r["group"], r["token"]) for r in result["results"]] == [
        ("thoughts_notes", "NO MODEL RECORD"), ("background", "NO MODEL RECORD"),
    ]
    with db._connection() as conn:
        row = conn.execute("SELECT state FROM kernel_receipts WHERE receipt_id=?", (result["receipt"],)).fetchone()
    assert row["state"] == "failed"


def test_the_speech_model_downloads_alone(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Astra r2: `{"only": ["whisper"]}` fetches the Whisper files and nothing
    else, sets nothing up after, and needs no llama.cpp runtime."""
    from holdspeak.services import local_ai_setup_service as las
    from holdspeak.services.errors import ServiceError

    svc = las.LocalAISetupService.__new__(las.LocalAISetupService)
    import threading
    svc._lock = threading.Lock()
    svc._thread = None
    svc._cancel = threading.Event()
    svc._error = ""
    svc._home = lambda: tmp_path
    svc._runtime = lambda: {"ready": False}  # no llama.cpp: speech must not need it
    plan = [
        {"key": "whisper", "model": type("M", (), {"size": 10})(), "on_device": False},
        {"key": "embed", "model": type("M", (), {"size": 20})(), "on_device": False},
        {"key": "starter", "model": type("M", (), {"size": 30})(), "on_device": False},
    ]
    svc._plan = lambda: plan
    seen: dict = {}

    def fake_download(principal, plan_, missing, set_up=True):
        seen["missing"] = [item["key"] for item in missing]
        seen["set_up"] = set_up

    svc._download_then_set_up = fake_download
    svc.status = lambda principal=None: {"state": "downloading"}
    las.LocalAISetupService.start(svc, OWNER, only=["whisper"])
    svc._thread.join(5)
    assert seen == {"missing": ["whisper"], "set_up": False}
    with pytest.raises(ServiceError):
        las.LocalAISetupService.start(svc, OWNER, only=["everything"])
    # The full press still checks the runtime first.
    with pytest.raises(ServiceError):
        las.LocalAISetupService.start(svc, OWNER)
