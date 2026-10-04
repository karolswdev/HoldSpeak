"""The chat guardrail and chat compaction resolve their engine by ROUTE.

``thread_practice._resolve_deployment_revision`` ran
``SELECT ... FROM deployment_revisions WHERE model=<profile id>``: the pattern
HS-200-08 named a bug (a profile id is not a model name). The rig here is a
real profile, deployment, binding and assignment made by the real services,
where the profile id and the model name DIFFER, as they do on a real desk.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.thread_practice import run_compact, run_guardrail

from tests.unit.test_phase143_inference_assignments import _profile, _result_claim

OWNER = Principal(PrincipalKind.OWNER, "practice-route-owner")
PROFILE_ID = "migrated-intel-endpoint"
MODEL_NAME = "qwen3-30b-a3b-instruct"


class _Runner:
    def __init__(self, result: dict[str, Any]) -> None:
        self.requests: list[Any] = []
        self._result = result

    def invoke(self, request: Any, adapter: Any, publish: Any = None) -> Any:
        self.requests.append(request)

        class _Outcome:
            result = self._result
        return _Outcome()


class _Broker:
    def __init__(self, db: Database, runner: _Runner) -> None:
        self.database = db
        self.inference_runner = runner


@pytest.fixture
def desk(tmp_path: Path) -> tuple[Database, str]:
    """A real assignment row for both capabilities; returns (db, bound deployment revision)."""
    from holdspeak.db.reconcile import _backfill_chat_practice_assignments

    db = Database(tmp_path / "practice.db")
    _profile(db, PROFILE_ID, claims=("language", _result_claim("chat.turn")), model=MODEL_NAME)
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": "assign-turn",
        "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "chat.turn"},
        "entries": [{"profile_id": PROFILE_ID, "profile_revision": 1}],
    })
    with db._connection() as conn:
        _backfill_chat_practice_assignments(conn)
        # The premise: the old string match finds NOTHING.
        assert conn.execute(
            "SELECT 1 FROM deployment_revisions WHERE model=?", (PROFILE_ID,),
        ).fetchone() is None
        bound = conn.execute(
            """SELECT b.deployment_revision_id AS rev FROM model_profile_binding_heads h
               JOIN model_profile_binding_revisions b
                 ON b.binding_id=h.binding_id AND b.revision=h.revision
               WHERE h.profile_id=?""", (PROFILE_ID,),
        ).fetchone()
    assert bound is not None
    return db, str(bound["rev"])


def test_compaction_reaches_the_bound_deployment(desk: tuple[Database, str]) -> None:
    db, bound = desk
    runner = _Runner({"summary": "A summary."})

    result = run_compact(_Broker(db, runner), OWNER, "t1", [{"role": "user", "content": "Hello"}])

    assert result == {"summary": "A summary."}
    assert [r.deployment_revision for r in runner.requests] == [bound]


def test_guardrail_reaches_the_bound_deployment(desk: tuple[Database, str]) -> None:
    db, bound = desk
    runner = _Runner({"violations": ["no"], "warnings": []})

    result = run_guardrail(
        _Broker(db, runner), OWNER, "t1", [{"role": "user", "content": "Hello"}],
        [{"name": "people.note.create", "arguments_head": "{}"}],
        {"instruction": "Check effects", "trigger_tools": ["people.*"]},
    )

    assert result == {"violations": ["no"], "warnings": []}
    assert [r.deployment_revision for r in runner.requests] == [bound]
