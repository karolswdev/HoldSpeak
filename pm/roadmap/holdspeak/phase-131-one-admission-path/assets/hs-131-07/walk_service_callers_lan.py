"""HS-131-07 real-LAN walk: the four census callers through the admitted runner.

Against live llama.cpp at 192.168.1.43:8080, through the REAL service layer:
  1. Rails observer summary — SERVICE principal rails-observer, real summary,
     receipt provenance (service / rails-observer / rails-observer:journal-only),
     receipt-gated journal note.
  2. Decision promotion draft — real domain parent decision.promotion-draft,
     one admitted child, artifact drafted from real model output, parent
     receipt references the child.
  3. Voice reference resolution — voice_reference_resolve parent, one admitted
     child per attempt, resolution grounded on the real model.
  4. Delivery PR review — the real route via TestClient with a stubbed PR
     source (small real diff) and the REAL model; parent
     delivery.pr-review-draft, child receipt, artifact persisted.

Mesh execution is unit-proven (envelope build/validate + frozen-field engine
construction); no live mesh worker is available on this walk.

Run with an isolated HOME. Exits non-zero on any failed assertion.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[6]))

from holdspeak.db import get_database
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind

LAN_URL = "http://192.168.1.43:8080/v1"
LAN_MODEL = "Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf"
OWNER = Principal(PrincipalKind.OWNER, "walk-owner")


def _children(db, parent_id):
    with db._connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM kernel_operations WHERE parent_operation_id=?", (parent_id,)
        ).fetchall()]


async def main() -> int:
    db = get_database()
    db.profiles.upsert(
        profile_id="lan43", name="LAN .43", kind="openAICompatible",
        base_url=LAN_URL, model=LAN_MODEL, requires_key=False,
    )
    broker = _configure(db)

    # ── Leg 1: Rails observer summary ──
    from holdspeak import rails_observer
    service_principal = Principal(
        PrincipalKind.SERVICE, "rails-observer",
        frozenset({("inference.invoke", 1)}), "rails-observer:journal-only",
    )
    summarizer = rails_observer.build_profile_summarizer(
        "lan43", db=db, broker=broker, principal=service_principal,
    )
    events = [{"ts": "t1", "kind": "gate_pass", "detail": "story HS-131-06 shipped"}]
    batch = rails_observer.summarize_batch(events, summarize_fn=summarizer)
    assert not batch.get("degraded"), f"real summary expected: {batch}"
    assert batch.get("summary"), batch
    note = rails_observer.record_journal_entry(db, batch, title="Walk rails journal")
    with db._connection() as conn:
        op = conn.execute(
            "SELECT operation_id FROM kernel_operations WHERE native_id LIKE 'rails_%' ORDER BY created_at DESC LIMIT 1"
        ).fetchone()[0]
    receipt = broker.store.receipt(op)
    assert (receipt["actor_kind"], receipt["actor_identity"], receipt["authority_basis"]) == (
        "service", "rails-observer", "rails-observer:journal-only",
    ), receipt
    assert receipt["outcome"] == "succeeded"
    print(f"leg1 rails op={op} summary={batch['summary'][:60]!r} note={note.id}")

    # ── Leg 2: Decision promotion draft ──
    from holdspeak.services.decision_lifecycle_service import DecisionLifecycleService
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, title) VALUES ('walk-meet', '2026-08-10T00:00:00+00:00', 'Walk meeting')"
        )
    db.plugins.record_artifact(
        artifact_id="walk-art", meeting_id="walk-meet", artifact_type="note",
        title="Walk source artifact", body_markdown="source", status="draft",
    )
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO decisions (id, text, rationale, decided_at, date_basis,
               source_artifact_id, source_meeting_id, source_state, lifecycle,
               created_at, updated_at, last_modified, deleted)
               VALUES ('walk-dec', 'Adopt bounded schedule delegation.',
                       'Exact terms, honest receipts.', '2026-08-10T00:00:00+00:00',
                       'meeting_date', 'walk-art', 'walk-meet', 'linked', 'accepted',
                       '2026-08-10T00:00:00+00:00', '2026-08-10T00:00:00+00:00',
                       '2026-08-10T00:00:00+00:00', 0)"""
        )
    lifecycle = DecisionLifecycleService(db, kernel=broker)
    promo = await lifecycle.draft_promoted_with_model(
        OWNER, "walk-dec", "note", {"inference_target_id": "lan43"},
    )
    parent_id = promo["operation_id"]
    kids = _children(db, parent_id)
    assert len(kids) == 1, kids
    child_receipt = broker.store.receipt(kids[0]["operation_id"])
    assert child_receipt["outcome"] == "succeeded", child_receipt
    assert promo["invocation"]["deployment_revision"], promo["invocation"]
    with db._connection() as conn:
        kind = conn.execute(
            "SELECT kind FROM kernel_parent_runs WHERE operation_id=?", (parent_id,)
        ).fetchone()[0]
    assert kind == "decision.promotion-draft", kind
    assert promo["parent_receipt"]["outcome"] == "succeeded"
    print(f"leg2 decision parent={parent_id} child={kids[0]['operation_id']} "
          f"revision={promo['invocation']['deployment_revision']} artifact drafted")

    # ── Leg 3: Voice reference resolution ──
    from holdspeak.services.workbench_service import WorkbenchService
    wb_service = WorkbenchService(db)
    wb_service._kernel = broker
    wb = wb_service.create_workbench(OWNER, name="Walk Voice", resolver_profile_id="lan43")
    db.directories.upsert(directory_id="zone-alpha", name="Alpha")
    db.directories.upsert(directory_id="zone-beta", name="Beta")
    result = wb_service.resolve_voice(OWNER, wb["id"], "file this note in Alpha", "walk-voice-1")
    with db._connection() as conn:
        vparent = conn.execute(
            "SELECT operation_id FROM kernel_parent_runs WHERE kind='voice_reference_resolve' ORDER BY created_at DESC LIMIT 1"
        ).fetchone()[0]
    vkids = _children(db, vparent)
    assert result.get("attempts", 0) >= 1 and len(vkids) == result["attempts"], (result, vkids)
    for kid in vkids:
        r = broker.store.receipt(kid["operation_id"])
        assert r is not None, f"child {kid['operation_id']} lacks a terminal receipt"
    vreceipt = broker.store.receipt(vparent)
    assert vreceipt is not None
    print(f"leg3 voice parent={vparent} attempts={result['attempts']} "
          f"children={len(vkids)} refs={result.get('refs')}")

    # ── Leg 4: Delivery PR review via the real route ──
    from fastapi import FastAPI, Request
    from fastapi.testclient import TestClient
    from holdspeak.web.routes.delivery_prs import build_delivery_prs_router
    from holdspeak.web.context import WebContext
    from holdspeak.services.delivery_service import DeliveryService

    diff = (
        "--- a/holdspeak/example.py\n+++ b/holdspeak/example.py\n"
        "@@ -1,3 +1,4 @@\n def add(a, b):\n-    return a+b\n"
        "+    # no input validation\n+    return a + b\n"
    )

    class StubPrService:
        def action_context(self, source_id, number):
            return {"status": "ok", "row": {"verbs": {"draft_review": {"available": True}}}}
        def review_material(self, source_id, number):
            return {"status": "ok", "diff": diff, "revision": "walk-rev-1", "linked": []}

    ctx = WebContext(get_state=lambda: {}, delivery_service=DeliveryService(db))
    app = FastAPI()

    @app.middleware("http")
    async def principal_mw(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_delivery_prs_router(ctx, service=StubPrService()))
    client = TestClient(app)
    resp = client.post(
        "/api/delivery/prs/walk-src/7/draft-review",
        json={"inference_target_id": "lan43"},
    )
    assert resp.status_code == 200, (resp.status_code, resp.text[:400])
    body = resp.json()
    assert body["artifact_id"] and body["output"], body
    assert body["invocation"]["outcome"] == "succeeded"
    assert body["parent_receipt"]["outcome"] == "succeeded"
    with db._connection() as conn:
        dkind = conn.execute(
            "SELECT kind FROM kernel_parent_runs WHERE operation_id=?",
            (body["operation_id"],),
        ).fetchone()[0]
    assert dkind == "delivery.pr-review-draft", dkind
    print(f"leg4 delivery parent={body['operation_id']} artifact={body['artifact_id']} "
          f"revision={body['invocation']['deployment_revision']} review={body['output'][:60]!r}")

    print("WALK OK: all four census callers ran admitted invocations on real metal — "
          "rails with honest observer provenance, decision and delivery under real "
          "domain parents with linked child receipts and drafted artifacts, voice "
          "with one admitted child per attempt. Mesh envelope unit-proven.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
