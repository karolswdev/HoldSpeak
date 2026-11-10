"""Test helper: put a saved (v1) profile on one engine-door job.

The door reads the owner's live assignment chain (``engine_door.chain``). A
speech test that names an endpoint profile assigns it to the job here, the way
a desk migrated from a saved selection carries it: one assignment row whose
entry is ``legacy-<profile_id>``. Nothing else is written.
"""
from __future__ import annotations

from typing import Any


def assign_profile(db: Any, capability_id: str, profile_id: str) -> str:
    """Assign the v1 profile ``profile_id`` to ``capability_id``; returns the
    assignment id. A second call for the same job replaces the first."""
    from holdspeak.services.inference_assignment_service import (
        ASSIGNMENT_SCHEMA,
        InferenceAssignmentService,
        _canonical,
        _sha256,
    )

    assignments = InferenceAssignmentService(db)
    scope = assignments._scope({"kind": "capability", "capability_id": capability_id})
    created_at = "2026-08-24T00:00:00Z"
    assignment_id = "ia_test_" + "".join(c if c.isalnum() else "_" for c in f"{capability_id}_{profile_id}")
    entry = {"ordinal": 1, "profile_id": f"legacy-{profile_id}", "profile_revision": 1,
             "profile_schema_version": 1}
    with db._connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            head = conn.execute(
                "SELECT revision FROM inference_assignment_heads WHERE assignment_key=?",
                (scope["assignment_key"],),
            ).fetchone()
            revision = 1 if head is None else int(head["revision"]) + 1
            material = {
                "schema": ASSIGNMENT_SCHEMA, "id": assignment_id,
                "scope": assignments._public_scope(scope), "entries": [entry],
                "retry_policy_id": None, "revision": revision, "created_at": created_at,
            }
            conn.execute(
                """INSERT INTO inference_assignment_revisions
                   (assignment_id,revision,assignment_key,scope_kind,scope_id,
                    subject_kind,selector_kind,capability_id,group_id,retry_policy_id,
                    payload_json,sha256,created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (assignment_id, revision, scope["assignment_key"], "global", "", "", "capability",
                 capability_id, "", None, _canonical(material), _sha256(material), created_at),
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
                (f"{assignment_id}:{revision}:1", assignment_id, revision, entry["profile_id"], 1, 1, 1),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    return assignment_id


def route_speech_stages_to_runtime(monkeypatch: Any) -> None:
    """Point the dictation provider stages at the pipeline runtime a test stubs.

    A web test that stubs ``assembly.build_runtime`` keeps doing so: this
    assigns ``speech.intent_classify`` and ``speech.rewrite`` to one loopback
    profile and makes the runner's engine for it call the stubbed runtime
    (``classify`` / ``rewrite``), so the door's call lands on the stub. When the
    stub raises, the runtime is unavailable before any call, as in production.
    """
    import json

    from holdspeak.db import get_database
    from holdspeak.kernel.runtime import _service
    from holdspeak.plugins.dictation import assembly

    db = get_database()
    db.profiles.upsert(
        profile_id="door-test-provider", name="door-test-provider", kind="openAICompatible",
        base_url="http://127.0.0.1:1/v1", model="door-test-model",
    )
    for job in ("speech.intent_classify", "speech.rewrite"):
        assign_profile(db, job, "door-test-provider")

    class _Schema:
        def __init__(self, block_ids: list[str]) -> None:
            self.block_ids = tuple(block_ids)
            self.extras_per_block: dict[str, Any] = {}

    class _Engine:
        def run_prompt(self, *, system_prompt: str = "", user_prompt: str, max_tokens: int = 128,
                       temperature: float = 0.0, **_kwargs: Any) -> str:
            runtime = assembly.build_runtime()
            if system_prompt.startswith("Return JSON"):
                allowed = [item.strip() for item in system_prompt.rsplit(":", 1)[-1].split(",") if item.strip()]
                return json.dumps(runtime.classify(user_prompt, _Schema(allowed),
                                                   max_tokens=max_tokens, temperature=temperature))
            return str(runtime.rewrite(user_prompt, max_tokens=max_tokens, temperature=temperature))

    monkeypatch.setattr(_service().inference_runner, "_engine_factory", lambda _revision, **_kw: _Engine())
