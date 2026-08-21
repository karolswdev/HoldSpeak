from __future__ import annotations

import json
import hashlib
import threading
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database
from holdspeak.db.refinement_thoughts import RefinementThoughtRepository
from holdspeak.mcp import server
from holdspeak.mcp.families import thought as thought_family
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ConflictError, ValidationError
from holdspeak.services.refinement_application_service import RefinementApplicationService
from holdspeak.services.refinement_context_service import RefinementContextService
from holdspeak.services.refinement_thought_service import INBOX_DIRECTORY_ID
from holdspeak.services.sync_service import SyncService
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_primitives_router


OWNER = Principal(PrincipalKind.OWNER, "default-context-owner")
NODE = Principal(PrincipalKind.NODE, "paired-node")


def _assert_no_model_rows(db: Database) -> None:
    with db._connection() as conn:
        for table in ("refinement_invocations", "ask_results", "kernel_operations"):
            assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


@pytest.fixture
def default_rig(tmp_path):
    db = Database(tmp_path / "default-context.db")
    db.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    db.notes.upsert(note_id="alpha", title="Alpha", body_markdown="Alpha body")
    db.notes.upsert(note_id="beta", title="Beta", body_markdown="Beta body")
    return db, RefinementApplicationService(db, coordinator=None)


def test_empty_policy_application_is_mandatory_restart_and_replay_safe(default_rig) -> None:
    db, app = default_rig
    first = app.create_thought(
        OWNER, request_id="empty-create", raw_text="rough", source={"kind": "typed"}
    )
    thought, receipt = first["thought"], first["default_context_receipt"]
    empty_hash = RefinementThoughtRepository.empty_attachment_hash(thought["id"])
    assert receipt == {
        "id": receipt["id"], "action": "apply_default_context",
        "scope": "this_thought", "thought_id": thought["id"],
        "default_revision": 0,
        "default_configuration_sha256": "4e04806a2695b3ac90e3ed39b69cb2ffa41f94f7af6cc55d262764c240c6a778",
        "status": "empty", "attachment_zero_sha256": empty_hash,
        "attachment_revision": 0, "attachment_sha256": empty_hash,
        "attachments": [], "failure": None,
    }
    replay = RefinementApplicationService(db, coordinator=None).create_thought(
        OWNER, request_id="empty-create", raw_text="rough", source={"kind": "typed"}
    )
    assert replay == first
    with db._connection() as conn:
        row = conn.execute(
            "SELECT * FROM refinement_default_context_applications WHERE thought_id=?",
            (thought["id"],),
        ).fetchone()
        assert row["status"] == "empty"
        assert row["attachment_zero_sha256"] == row["attachment_sha256"] == empty_hash
        tampered = json.loads(row["receipt_json"])
        tampered["attachment_sha256"] = "0" * 64
        conn.execute(
            "UPDATE refinement_default_context_applications SET receipt_json=? WHERE thought_id=?",
            (json.dumps(tampered), thought["id"]),
        )
    with pytest.raises(ConflictError) as invalid:
        RefinementApplicationService(db, coordinator=None).create_thought(
            OWNER, request_id="empty-create", raw_text="rough", source={"kind": "typed"}
        )
    assert invalid.value.code == "default_context_application_proof_invalid"


def test_replace_default_applies_as_second_v2_command_and_marks_projection(default_rig) -> None:
    db, app = default_rig
    configured = app.replace_default_context(
        OWNER, request_id="set-alpha", expected_revision=0,
        refs=["note:alpha", "note:alpha"],
    )
    assert configured["default_context"]["refs"] == ["note:alpha"]
    assert configured["receipt"]["scope"] == "future_thoughts"
    assert configured["receipt"]["existing_thoughts_changed"] == 0

    born = app.create_thought(
        OWNER, request_id="born-with-alpha", raw_text="new thought"
    )
    thought, receipt = born["thought"], born["default_context_receipt"]
    assert (thought["aggregate_revision"], thought["attachment_revision"]) == (2, 1)
    assert receipt["status"] == "applied"
    assert receipt["attachments"] == [{"ref": "note:alpha", "title": "Alpha", "leaf_count": 1}]
    assert receipt["attachment_zero_sha256"] != receipt["attachment_sha256"]
    commands = db.refinement_thoughts.commands(thought["id"])
    assert [(row["aggregate_revision"], row["command_kind"], row["canonical_version"],
             row["prior_attachment_revision"], row["next_attachment_revision"])
            for row in commands] == [
        (1, "create", 2, 0, 0),
        (2, "replace_attachments", 2, 0, 1),
    ]
    listed = app.list_context(OWNER, thought_id=thought["id"])
    assert listed["attachments"][0]["is_default"] is True
    alpha_candidate = next(item for item in listed["results"]
                           if item["ref"] == "note:alpha") if listed["results"] else None
    assert alpha_candidate is None  # compact listing does not manufacture Browse rows
    assert listed["default_context"]["selections"][0]["title"] == "Alpha"
    _assert_no_model_rows(db)

    detached = app.mutate_context(
        OWNER, action="detach", thought_id=thought["id"], ref="note:alpha",
        request_id="detach-born", expected_aggregate_revision=2,
        expected_working_revision=1, expected_attachment_revision=1,
    )
    assert detached["receipt"]["scope"] == "this_thought"
    assert detached["receipt"]["default_context_changed"] is False
    assert app.get_default_context(OWNER)["default_context"]["refs"] == ["note:alpha"]


def test_invalid_multi_default_fails_open_as_one_named_empty_result(default_rig) -> None:
    db, app = default_rig
    app.replace_default_context(
        OWNER, request_id="set-two", expected_revision=0,
        refs=["note:alpha", "note:beta"],
    )
    assert db.notes.delete("beta") is True
    born = app.create_thought(
        OWNER, request_id="invalid-default-birth", raw_text="must survive"
    )
    thought, receipt = born["thought"], born["default_context_receipt"]
    assert (thought["aggregate_revision"], thought["attachment_revision"], thought["attachments"]) == (1, 0, [])
    assert receipt["status"] == "not_applied"
    assert receipt["failure"]["code"] == "default_context_missing"
    assert receipt["failure"]["selections"] == [
        {"kind": "note", "leaf_count": 1, "ref": "note:beta", "title": "Beta"}
    ]
    assert db.refinement_thoughts.commands(thought["id"])[0]["command_kind"] == "create"
    assert len(db.refinement_thoughts.commands(thought["id"])) == 1
    with db._connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM refinement_attachment_revisions WHERE thought_id=?",
            (thought["id"],),
        ).fetchone()[0] == 0
    current = app.get_default_context(OWNER)["default_context"]
    assert current["refs"] == ["note:alpha", "note:beta"]
    assert [item["state"] for item in current["selections"]] == ["current", "missing"]
    _assert_no_model_rows(db)


def test_adopt_self_default_fails_open_without_losing_custody(default_rig) -> None:
    db, app = default_rig
    app.replace_default_context(
        OWNER, request_id="set-adopted-note", expected_revision=0, refs=["note:alpha"]
    )
    note = db.notes.get("alpha")
    assert note is not None
    content_hash = RefinementThoughtRepository.content_hash(
        note.title, note.body_markdown, note.tags
    )
    result = app.adopt_note(
        OWNER, request_id="adopt-alpha", note_id="alpha",
        expected_source_content_sha256=content_hash,
        expected_source_last_modified=note.last_modified,
    )
    assert result["thought"]["working_note"]["id"] == "alpha"
    assert result["thought"]["attachments"] == []
    assert result["default_context_receipt"]["status"] == "not_applied"
    assert result["default_context_receipt"]["failure"]["code"] == "default_context_self_reference"


def test_default_policy_is_owner_only_idempotent_and_absent_from_sync(default_rig) -> None:
    db, app = default_rig
    first = app.replace_default_context(
        OWNER, request_id="stable-set", expected_revision=0, refs=["note:alpha"]
    )
    assert app.replace_default_context(
        OWNER, request_id="stable-set", expected_revision=0, refs=["note:alpha"]
    ) == first
    no_op = app.replace_default_context(
        OWNER, request_id="stable-noop", expected_revision=1, refs=["note:alpha"]
    )
    assert no_op["receipt"]["no_op"] is True
    with pytest.raises(ConflictError) as stale:
        app.replace_default_context(
            OWNER, request_id="stale-set", expected_revision=0, refs=[]
        )
    assert stale.value.code == "default_context_revision_conflict"
    with pytest.raises(Exception) as denied:
        app.get_default_context(NODE)
    assert getattr(denied.value, "code", "") == "thought_owner_required"
    pulled = SyncService(db).pull(NODE)
    assert "refinement_default_context" not in json.dumps(pulled)


def test_corrupt_policy_or_unexpected_resolution_fault_rolls_back_birth(default_rig, monkeypatch) -> None:
    db, app = default_rig
    with db._connection() as conn:
        conn.execute(
            "UPDATE refinement_default_context_current SET configuration_sha256='broken' WHERE id=1"
        )
    with pytest.raises(ConflictError) as corrupt:
        app.create_thought(OWNER, request_id="corrupt-birth", raw_text="must rollback")
    assert corrupt.value.code == "default_context_ledger_invalid"
    with db._connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM refinement_thoughts WHERE create_request_id='corrupt-birth'"
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM notes WHERE body_markdown='must rollback'"
        ).fetchone()[0] == 0

    with db._connection() as conn:
        conn.execute(
            "UPDATE refinement_default_context_current SET configuration_sha256=? WHERE id=1",
            ("4e04806a2695b3ac90e3ed39b69cb2ffa41f94f7af6cc55d262764c240c6a778",),
        )
    app.replace_default_context(
        OWNER, request_id="set-before-fault", expected_revision=0, refs=["note:alpha"]
    )

    def explode(*_args, **_kwargs):
        raise RuntimeError("unexpected resolver fault")

    monkeypatch.setattr(RefinementContextService, "_resolve_manifest", explode)
    with pytest.raises(RuntimeError, match="unexpected resolver fault"):
        app.create_thought(OWNER, request_id="fault-birth", raw_text="also rollback")
    with db._connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM refinement_thoughts WHERE create_request_id='fault-birth'"
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM refinement_default_context_applications WHERE create_request_id='fault-birth'"
        ).fetchone()[0] == 0


@pytest.mark.parametrize("corruption", [
    "missing_history", "bad_rev0", "noncanonical_labels", "missing_transition",
    "forged_action_receipt", "illegal_ref",
])
def test_full_policy_ledger_corruption_hard_rolls_back_birth(default_rig, corruption) -> None:
    db, app = default_rig
    app.replace_default_context(
        OWNER, request_id=f"ledger-{corruption}", expected_revision=0,
        refs=["note:alpha"],
    )
    with db._connection() as conn:
        if corruption == "missing_history":
            conn.execute("PRAGMA foreign_keys=OFF")
            conn.execute("DELETE FROM refinement_default_context_revisions WHERE revision=0")
        elif corruption == "bad_rev0":
            conn.execute("UPDATE refinement_default_context_revisions SET labels_json='[{}]' WHERE revision=0")
        elif corruption == "noncanonical_labels":
            conn.execute("UPDATE refinement_default_context_revisions SET labels_json=? WHERE revision=1",
                         ('[{"title":"Alpha","ref":"note:alpha","kind":"note","leaf_count":1}]',))
        elif corruption == "missing_transition":
            conn.execute("DELETE FROM refinement_default_context_actions")
        elif corruption == "forged_action_receipt":
            row = conn.execute("SELECT action_id,receipt_json FROM refinement_default_context_actions").fetchone()
            receipt = json.loads(row["receipt_json"])
            receipt["existing_thoughts_changed"] = 1
            conn.execute("UPDATE refinement_default_context_actions SET receipt_json=? WHERE action_id=?",
                         (json.dumps(receipt), row["action_id"]))
        else:
            refs = ["knowledge:forged"]
            digest = RefinementContextService._default_hash(1, refs)
            conn.execute("UPDATE refinement_default_context_revisions SET refs_json=?,configuration_sha256=? WHERE revision=1",
                         (json.dumps(refs), digest))
            conn.execute("UPDATE refinement_default_context_current SET refs_json=?,configuration_sha256=?",
                         (json.dumps(refs), digest))
    with pytest.raises(ConflictError) as refused:
        app.create_thought(
            OWNER, request_id=f"birth-after-{corruption}", raw_text="roll back"
        )
    assert refused.value.code == "default_context_ledger_invalid"
    with db._connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM refinement_thoughts WHERE create_request_id=?",
            (f"birth-after-{corruption}",),
        ).fetchone()[0] == 0


@pytest.mark.parametrize("target", [
    "receipt_extra", "policy_hash", "empty_status", "attachment_projection",
    "attachment_manifest", "failure_shape",
])
def test_application_replay_reconstructs_every_durable_proof(default_rig, target) -> None:
    db, app = default_rig
    app.replace_default_context(
        OWNER, request_id=f"proof-policy-{target}", expected_revision=0,
        refs=["note:alpha"],
    )
    first = app.create_thought(
        OWNER, request_id=f"proof-birth-{target}", raw_text="proof"
    )
    thought_id = first["thought"]["id"]
    with db._connection() as conn:
        row = conn.execute(
            "SELECT * FROM refinement_default_context_applications WHERE thought_id=?",
            (thought_id,),
        ).fetchone()
        receipt = json.loads(row["receipt_json"])
        if target == "receipt_extra":
            receipt["body"] = "forged"
            conn.execute("UPDATE refinement_default_context_applications SET receipt_json=? WHERE thought_id=?",
                         (json.dumps(receipt), thought_id))
        elif target == "policy_hash":
            conn.execute("UPDATE refinement_default_context_applications SET default_configuration_sha256='forged' WHERE thought_id=?",
                         (thought_id,))
        elif target == "empty_status":
            receipt["status"] = "empty"
            conn.execute("UPDATE refinement_default_context_applications SET status='empty',receipt_json=? WHERE thought_id=?",
                         (json.dumps(receipt), thought_id))
        elif target == "attachment_projection":
            receipt["attachments"][0]["title"] = "Forged"
            conn.execute("UPDATE refinement_default_context_applications SET receipt_json=? WHERE thought_id=?",
                         (json.dumps(receipt), thought_id))
        elif target == "attachment_manifest":
            conn.execute("UPDATE refinement_attachment_visible SET visible_title='Forged' WHERE thought_id=?",
                         (thought_id,))
        else:
            receipt["failure"] = {"code": "default_context_missing", "selections": [], "body": "leak"}
            conn.execute("UPDATE refinement_default_context_applications SET error_code='default_context_missing',receipt_json=? WHERE thought_id=?",
                         (json.dumps(receipt), thought_id))
    with pytest.raises(ConflictError) as refused:
        app.create_thought(
            OWNER, request_id=f"proof-birth-{target}", raw_text="proof"
        )
    assert refused.value.code == "default_context_application_proof_invalid"


@pytest.mark.parametrize("forgery", ["other_valid_default", "unrelated_leaf"])
def test_not_applied_replay_uses_independent_failure_attribution(default_rig, forgery) -> None:
    db, app = default_rig
    app.replace_default_context(
        OWNER, request_id=f"failure-proof-policy-{forgery}", expected_revision=0,
        refs=["note:alpha", "note:beta"],
    )
    db.notes.delete("beta")
    first = app.create_thought(
        OWNER, request_id=f"failure-proof-birth-{forgery}", raw_text="proof"
    )
    assert first["default_context_receipt"]["failure"]["selections"][0]["ref"] == "note:beta"
    thought_id = first["thought"]["id"]
    with db._connection() as conn:
        row = conn.execute(
            "SELECT * FROM refinement_default_context_applications WHERE thought_id=?",
            (thought_id,),
        ).fetchone()
        attribution = json.loads(row["failure_json"])
        assert row["failure_sha256"] == hashlib.sha256(
            row["failure_json"].encode("utf-8")
        ).hexdigest()
        assert attribution == {
            "affected": [{"ref": "note:beta", "title": "Beta"}],
            "code": "default_context_missing",
            "leaf": {"visible_ref": "note:beta", "ref": "note:beta", "title": "Beta"},
        }
        receipt = json.loads(row["receipt_json"])
        if forgery == "other_valid_default":
            receipt["failure"]["selections"] = [{
                "ref": "note:alpha", "kind": "note", "title": "Alpha", "leaf_count": 1,
            }]
        else:
            receipt["failure"]["leaf"] = {"ref": "note:alpha", "title": "Alpha"}
        conn.execute(
            "UPDATE refinement_default_context_applications SET receipt_json=? WHERE thought_id=?",
            (json.dumps(receipt), thought_id),
        )
    with pytest.raises(ConflictError) as refused:
        app.create_thought(
            OWNER, request_id=f"failure-proof-birth-{forgery}", raw_text="proof"
        )
    assert refused.value.code == "default_context_application_proof_invalid"


def test_default_failure_names_exact_visible_selection_and_leaf(default_rig) -> None:
    db, app = default_rig
    app.replace_default_context(
        OWNER, request_id="precise-direct-policy", expected_revision=0,
        refs=["note:alpha", "note:beta"],
    )
    alpha = db.notes.get("alpha")
    assert alpha is not None
    adopted = app.adopt_note(
        OWNER, request_id="precise-direct-adopt", note_id="alpha",
        expected_source_content_sha256=RefinementThoughtRepository.content_hash(
            alpha.title, alpha.body_markdown, alpha.tags),
        expected_source_last_modified=alpha.last_modified,
    )["default_context_receipt"]
    assert adopted["failure"] == {
        "code": "default_context_self_reference",
        "selections": [{"ref": "note:alpha", "kind": "note", "title": "Alpha", "leaf_count": 1}],
        "leaf": {"ref": "note:alpha", "title": "Alpha"},
    }


@pytest.mark.parametrize("mode", ["member_self", "missing_member", "oversized_leaf"])
def test_default_failure_attributes_container_leaf_exactly(default_rig, mode) -> None:
    db, app = default_rig
    everyday_id = "hs-seed-everyday-context"
    db.kbs.upsert(kb_id=everyday_id, name="Everyday context",
                  member_ids=["note:alpha", "note:beta"])
    app.replace_default_context(
        OWNER, request_id=f"container-policy-{mode}", expected_revision=0,
        refs=[f"knowledge:{everyday_id}"],
    )
    if mode == "member_self":
        alpha = db.notes.get("alpha")
        assert alpha is not None
        receipt = app.adopt_note(
            OWNER, request_id="container-self", note_id="alpha",
            expected_source_content_sha256=RefinementThoughtRepository.content_hash(
                alpha.title, alpha.body_markdown, alpha.tags),
            expected_source_last_modified=alpha.last_modified,
        )["default_context_receipt"]
        leaf = {"ref": "note:alpha", "title": "Alpha"}
    else:
        if mode == "missing_member":
            db.notes.delete("beta")
        else:
            db.notes.upsert(note_id="beta", title="Beta", body_markdown="x" * 13_000)
        receipt = app.create_thought(
            OWNER, request_id=f"container-{mode}", raw_text="birth"
        )["default_context_receipt"]
        leaf = {"ref": "note:beta", "title": "Beta"}
    assert receipt["status"] == "not_applied"
    assert receipt["failure"]["selections"] == [{
        "ref": f"knowledge:{everyday_id}", "kind": "knowledge",
        "title": "Everyday context", "leaf_count": 2,
    }]
    assert receipt["failure"]["leaf"] == leaf


def test_empty_nonempty_birth_races_bind_wholly_before_or_after(tmp_path, monkeypatch) -> None:
    def make(name: str, *, configured: bool) -> tuple[Database, RefinementApplicationService]:
        db = Database(tmp_path / f"{name}.db")
        db.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
        db.notes.upsert(note_id="alpha", title="Alpha", body_markdown="Alpha body")
        app = RefinementApplicationService(db, coordinator=None)
        if configured:
            app.replace_default_context(
                OWNER, request_id=f"{name}-seed", expected_revision=0,
                refs=["note:alpha"],
            )
        return db, app

    # Mutation wins first: birth observes the complete new head in both directions.
    _db, app = make("set-first", configured=False)
    app.replace_default_context(
        OWNER, request_id="set-first-action", expected_revision=0, refs=["note:alpha"]
    )
    assert app.create_thought(OWNER, request_id="set-first-birth", raw_text="x")[
        "default_context_receipt"
    ]["status"] == "applied"
    _db, app = make("clear-first", configured=True)
    app.replace_default_context(
        OWNER, request_id="clear-first-action", expected_revision=1, refs=[]
    )
    assert app.create_thought(OWNER, request_id="clear-first-birth", raw_text="x")[
        "default_context_receipt"
    ]["status"] == "empty"

    def birth_wins(name: str, *, configured: bool, mutation_refs: list[str],
                   expected_revision: int, expected_status: str) -> None:
        _db, app = make(name, configured=configured)
        entered, release = threading.Event(), threading.Event()
        original = RefinementContextService._verified_default

        def gated(self, conn):
            value = original(self, conn)
            if threading.current_thread().name == f"{name}-birth":
                entered.set()
                assert release.wait(5)
            return value

        results: dict[str, object] = {}
        errors: list[BaseException] = []

        def create() -> None:
            try:
                results["birth"] = app.create_thought(
                    OWNER, request_id=f"{name}-birth-request", raw_text="x"
                )
            except BaseException as exc:  # pragma: no cover - assertion reports it
                errors.append(exc)

        def mutate() -> None:
            try:
                results["mutation"] = app.replace_default_context(
                    OWNER, request_id=f"{name}-mutation", expected_revision=expected_revision,
                    refs=mutation_refs,
                )
            except BaseException as exc:  # pragma: no cover - assertion reports it
                errors.append(exc)

        with monkeypatch.context() as scoped:
            scoped.setattr(RefinementContextService, "_verified_default", gated)
            birth = threading.Thread(target=create, name=f"{name}-birth")
            mutation = threading.Thread(target=mutate, name=f"{name}-mutation")
            birth.start()
            assert entered.wait(5)
            mutation.start()
            assert mutation.is_alive()  # blocked behind birth's BEGIN IMMEDIATE
            release.set()
            birth.join(5)
            mutation.join(5)
        assert not errors
        assert not birth.is_alive() and not mutation.is_alive()
        receipt = results["birth"]["default_context_receipt"]  # type: ignore[index]
        assert receipt["status"] == expected_status
        assert receipt["default_revision"] == expected_revision

    # Birth wins first: it binds the complete old head before the blocked mutation.
    birth_wins("empty-before-set", configured=False, mutation_refs=["note:alpha"],
               expected_revision=0, expected_status="empty")
    birth_wins("nonempty-before-clear", configured=True, mutation_refs=[],
               expected_revision=1, expected_status="applied")


def test_two_default_replacements_have_one_cas_winner(default_rig) -> None:
    _db, app = default_rig
    barrier = threading.Barrier(3)
    successes: list[dict] = []
    failures: list[BaseException] = []

    def replace(name: str, ref: str) -> None:
        barrier.wait()
        try:
            successes.append(app.replace_default_context(
                OWNER, request_id=f"race-{name}", expected_revision=0, refs=[ref]
            ))
        except BaseException as exc:  # pragma: no cover - assertion reports it
            failures.append(exc)

    first = threading.Thread(target=replace, args=("alpha", "note:alpha"))
    second = threading.Thread(target=replace, args=("beta", "note:beta"))
    first.start()
    second.start()
    barrier.wait()
    first.join(5)
    second.join(5)
    assert not first.is_alive() and not second.is_alive()
    assert len(successes) == len(failures) == 1
    assert isinstance(failures[0], ConflictError)
    assert failures[0].code == "default_context_revision_conflict"  # type: ignore[attr-defined]
    assert successes[0]["default_context"]["revision"] == 1


def _web_client(db: Database, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    app = FastAPI()

    @app.middleware("http")
    async def owner(request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    return TestClient(app)


def test_http_and_mcp_default_create_contracts_are_closed_and_reciprocal(default_rig, monkeypatch) -> None:
    db, _app = default_rig
    client = _web_client(db, monkeypatch)
    assert client.get("/api/thoughts/default-context").json()["default_context"]["refs"] == []
    extra = client.put("/api/thoughts/default-context", json={
        "request_id": "bad", "expected_revision": 0, "refs": [], "body": "forbidden",
    })
    assert extra.status_code == 422 and extra.json()["error"] == "default_context_request_invalid"
    configured = client.put("/api/thoughts/default-context", json={
        "request_id": "http-set", "expected_revision": 0, "refs": ["note:alpha"],
    })
    assert configured.status_code == 200
    created = client.post("/api/thoughts", json={
        "request_id": "http-create", "raw_text": "HTTP thought",
    })
    assert created.status_code == 201
    assert created.json()["default_context_receipt"]["status"] == "applied"
    assert client.post("/api/thoughts", json={
        "request_id": "bad-create", "raw_text": "x", "context": "copied",
    }).status_code == 422

    monkeypatch.setattr(thought_family, "get_database", lambda: db)
    monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))
    tools = {item["name"]: item for item in thought_family.TOOLS}
    for name in ("thought.create", "thought.adopt_note", "thought.get_default_context",
                 "thought.replace_default_context"):
        assert tools[name]["inputSchema"]["additionalProperties"] is False
    def mcp_call(name: str, arguments: dict) -> tuple[bool, dict]:
        response = server.handle_message({
            "jsonrpc": "2.0", "id": name, "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        })
        assert response is not None
        result = response["result"]
        return result["isError"], json.loads(result["content"][0]["text"])

    malformed_create = [
        {"request_id": "bad-source-kind", "raw_text": "x", "source": {"ref": None}},
        {"request_id": "bad-source-ref", "raw_text": "x", "source": {"kind": "note", "ref": 7}},
        {"request_id": "bad-note-tags", "raw_text": "x", "initial_note": {"tags": ["ok", 7]}},
        {"request_id": "bad-note-extra", "raw_text": "x", "initial_note": {"body": "forbidden"}},
    ]
    for payload in malformed_create:
        http = client.post("/api/thoughts", json=payload)
        error, mcp = mcp_call("thought.create", payload)
        assert http.status_code == 422 and error
        assert http.json()["error"] == mcp["code"] == "thought_create_request_invalid"
    malformed_adopt = {
        "request_id": "bad-adopt", "note_id": 7,
        "expected_source_content_sha256": False,
        "expected_source_last_modified": ["not", "a", "date"],
    }
    http = client.post("/api/thoughts/adopt", json=malformed_adopt)
    error, mcp = mcp_call("thought.adopt_note", malformed_adopt)
    assert http.status_code == 422 and error
    assert http.json()["error"] == mcp["code"] == "note_adoption_precondition_required"
    with db._connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM refinement_thoughts WHERE create_request_id LIKE 'bad-%'"
        ).fetchone()[0] == 0

    error, default_result = mcp_call("thought.get_default_context", {})
    assert not error
    assert default_result == client.get("/api/thoughts/default-context").json()
    error, refused = mcp_call("thought.replace_default_context", {
        "request_id": "mcp-extra", "expected_revision": 1,
        "refs": ["note:alpha"], "body_markdown": "forbidden",
    })
    assert error and refused["code"] == "mcp_invalid_params"
    error, mcp_created = mcp_call("thought.create", {
        "request_id": "mcp-create", "raw_text": "MCP thought",
    })
    assert not error
    assert mcp_created["default_context_receipt"]["status"] == "applied"
    assert "Alpha body" not in json.dumps(mcp_created)

    db.notes.upsert(note_id="gamma", title="Gamma", body_markdown="Gamma body")
    gamma = db.notes.get("gamma")
    assert gamma is not None
    gamma_hash = RefinementThoughtRepository.content_hash(
        gamma.title, gamma.body_markdown, gamma.tags
    )
    error, adopted = mcp_call("thought.adopt_note", {
        "request_id": "mcp-adopt", "note_id": "gamma",
        "expected_source_content_sha256": gamma_hash,
        "expected_source_last_modified": gamma.last_modified,
    })
    assert not error
    assert adopted["thought"]["working_note"]["id"] == "gamma"
    assert adopted["default_context_receipt"]["status"] == "applied"
