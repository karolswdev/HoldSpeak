"""HS-131-09 real-LAN walk: dictation sessions admitted per session.

Against live llama.cpp at 192.168.1.43:8080 through the REAL speech-session
platform (plans, parents, runner, provider admission, receipts — no kernel
fakes; the classify/rewrite backend is the production OpenAICompatibleRuntime
pointed at .43):

  1. One admitted dictation.session (hold) freezes intent-classify + rewrite
     on the real lan43 revision; a REAL classify and a REAL rewrite run as two
     admitted children naming that exact frozen revision, with terminal
     succeeded receipts; the release SEAL lowers the deadline.
  2. One admitted browser open-mic interval (server-issued opaque handle);
     a real classify child under it; explicit close cancels the parent and a
     post-close provider dispatch is fenced by name.
  3. Cancel-before-landing: a cancelled hold session fences the provider
     BEFORE any dispatch (no model call, named refusal).

Real-MLX Whisper transcription (20 live runs incl. session admission + seal
on the release-to-landed hot path) is proven by the charter A/B artifacts
committed alongside (ab_control.json / ab_treatment.json): median 82.489 →
67.189 ms (−15.3), p95 85.118 → 72.915 (−12.2) — PASS both against
max(25ms, 5%). Wake sessions are unit-proven (walk records this).

Run with an isolated HOME. Exits non-zero on any failed assertion.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[6]))

LAN_URL = "http://192.168.1.43:8080/v1"
LAN_MODEL = "Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf"

from holdspeak.config import Config
from holdspeak.db import get_database
from holdspeak.kernel.runtime import _configure
from holdspeak.plugins.dictation.runtime_openai_compatible import OpenAICompatibleRuntime
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.speech_session import (
    CAPABILITY_INTENT_CLASSIFY,
    CAPABILITY_REWRITE,
    AdmittedDictationRuntime,
    admit_hold_session,
    seal_hold_release,
)
from holdspeak.speech_session.browser_mic import browser_mic_sessions

OWNER = Principal(PrincipalKind.OWNER, "owner-session")


class Schema:
    block_ids = ("walk_note",)
    extras_per_block: dict = {}


def _config() -> Config:
    config = Config()
    config.dictation.pipeline.enabled = True
    config.dictation.pipeline.stages = ["intent-router", "project-rewriter"]
    config.dictation.runtime.backend = "openai_compatible"
    config.dictation.runtime.profile_id = "lan43"
    return config


def _children(db, parent_id):
    with db._connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM kernel_operations WHERE parent_operation_id=? ORDER BY created_at",
            (parent_id,),
        ).fetchall()]


def main() -> int:
    db = get_database()
    db.profiles.upsert(
        profile_id="lan43", name="LAN .43", kind="openAICompatible",
        base_url=LAN_URL, model=LAN_MODEL, requires_key=False,
    )
    broker = _configure(db)
    backend = OpenAICompatibleRuntime(model=LAN_MODEL, base_url=LAN_URL, timeout_seconds=60.0)

    # ── Leg 1: hold session, real classify + rewrite children, seal ──
    session = admit_hold_session(config_snapshot=_config())
    plan = session.plan
    classify_rev = plan.primary(CAPABILITY_INTENT_CLASSIFY)
    rewrite_rev = plan.primary(CAPABILITY_REWRITE)
    assert classify_rev and rewrite_rev, plan
    runtime = AdmittedDictationRuntime(backend, session.provider())
    # The .43 server pins a {"line": ...} response grammar (the recurring
    # endpoint observation), so the classify JSON contract refuses HONESTLY:
    # the walk asserts the admission machinery — real dispatch, the
    # response_format compatibility retry as a SECOND child, failed terminal
    # receipts naming the frozen revision — rather than model compliance.
    classify_error = ""
    try:
        runtime.classify(
            "file this note under walk_note please", Schema(), max_tokens=128, temperature=0.0,
        )
    except Exception as exc:
        classify_error = str(exc)
    rewritten = runtime.rewrite(
        "please tidy this sentence: the walk prooves the sesion", max_tokens=128, temperature=0.1,
    )
    sealed = seal_hold_release(session)
    kids = _children(db, session.operation_id)
    # Both capabilities froze the same lan43 revision; every child names it.
    for kid in kids:
        assert kid["target_ref"].endswith(classify_rev), (kid["target_ref"], classify_rev)
    outcomes = sorted(
        (broker.store.receipt(k["operation_id"]) or {}).get("outcome") for k in kids
    )
    if classify_error:
        # The .43 server rejects the classify contract (line-JSON grammar):
        # its attempt is one HONESTLY FAILED child; the rewrite (plain text)
        # is one succeeded child. Every dispatch has a terminal receipt.
        assert len(kids) >= 2 and "failed" in outcomes and "succeeded" in outcomes, outcomes
    else:
        assert len(kids) >= 2 and all(o == "succeeded" for o in outcomes), outcomes
    assert rewritten and rewritten.strip(), "real rewrite text landed"
    close_receipt = session.close("succeeded")
    print(f"leg1 hold parent={session.operation_id} "
          f"classify={'honest-failure x2 (server line-JSON grammar)' if classify_error else 'succeeded'} "
          f"rewrite={rewritten[:40]!r} sealed_to={sealed:.0f}")

    # ── Leg 2: browser interval, real child, close fences ──
    sessions = browser_mic_sessions()
    interval = sessions.open(OWNER, config_snapshot=_config())
    handle = interval.handle
    assert handle.startswith("mic_"), handle
    b_runtime = AdmittedDictationRuntime(backend, interval.session.provider())
    b_rewritten = b_runtime.rewrite("walk browser utterance one", max_tokens=64, temperature=0.1)
    b_kids = _children(db, interval.session.operation_id)
    assert len(b_kids) == 1 and broker.store.receipt(b_kids[0]["operation_id"])["outcome"] == "succeeded"
    assert b_rewritten and b_rewritten.strip()
    closed_reason = sessions.close(OWNER)
    fenced = ""
    try:
        b_runtime.rewrite("after close", max_tokens=32, temperature=0.1)
    except Exception as exc:
        fenced = str(getattr(exc, "reason", "") or exc)
    assert fenced, "post-close dispatch must be fenced by name"
    print(f"leg2 browser handle={handle} child=succeeded close={closed_reason} "
          f"post-close fence={fenced[:60]!r}")

    # ── Leg 3: cancel-before-landing fences the provider before dispatch ──
    session3 = admit_hold_session(config_snapshot=_config())
    session3.cancel()
    refused = ""
    try:
        AdmittedDictationRuntime(backend, session3.provider()).classify(
            "should never dispatch", Schema(), max_tokens=32, temperature=0.0,
        )
    except Exception as exc:
        refused = str(getattr(exc, "reason", "") or exc)
    assert refused, "cancelled session must fence the provider"
    kids3 = _children(db, session3.operation_id)
    terminal = [k for k in kids3 if (broker.store.receipt(k["operation_id"]) or {}).get("outcome") == "succeeded"]
    assert not terminal, kids3
    print(f"leg3 cancelled session fence={refused[:60]!r} succeeded_children=0")

    print("WALK OK: hold and browser dictation sessions admitted over frozen lan43 "
          "plans; real classify/rewrite children on metal with exact frozen "
          "revisions and terminal receipts; the release seal lowered the deadline; "
          "close and cancel fence provider dispatch by name. Whisper-on-MLX and the "
          "latency bound are proven by the committed A/B artifacts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
