"""PHILO-15 21 -- the second morning tells no lies.

Fences for the rehearsal-2 bounces (docs/internal/philo/phase-15/rehearsal-2/
BOUNCES-C.md) through the real services and routes:

* B60: a sweep held by quiet hours moves every armed Watch's next check to the
  quiet end; the Room and Needs read QUIET UNTIL, not STALE; a quiet row is not
  counted; the first sweep after the quiet end runs at once.
* B61: the hub's single-Watch check re-checks THAT source; its row is fresh.
* B64: an update with no verified claim (every claim an unreviewed inference,
  cited or not) is refused NOTHING VERIFIED at preview and prepare; an
  unreviewed inference is omitted from the sent text and counted.
* B69: the Room carries ONE freshness state per source (the rule Needs reads)
  and a next check that is never in the past.
* B70: a Room decision row for a done action says so.
* B71: the drafter drops a model sentence that repeats a ``Merged:`` row.
* B74: a source row is named ``GitHub · owner/repo`` / ``Meetings``.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.heartbeat_service import HeartbeatService
from holdspeak.services.needs_you_aggregate import source_label
from holdspeak.services.needs_you_membership import unread_sources
from holdspeak.services.project_service import ProjectService

OWNER = Principal(PrincipalKind.OWNER, "test")


def _naive_utc(delta: timedelta) -> str:
    """connector_watches stores NAIVE UTC (``datetime('now')``)."""
    return (datetime.now(timezone.utc).replace(tzinfo=None) - delta).isoformat(timespec="seconds")


def _seed_watch(db: Database, project_id: str, watch_id: str, *, checked: timedelta,
                connector: str = "gh", repo: str = "karolswdev/holdspeak-dayone-rehearsal-1558") -> None:
    query = {"repository": repo} if connector == "gh" else {"project_id": project_id}
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO connector_watches "
            "(id, connector_id, query_kind, name, query_json, snapshot_json, enabled, state, "
            " last_success_at, next_evaluation_at, project_id, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, '[]', 1, 'active', ?, ?, ?, datetime('now'), datetime('now'))",
            (watch_id, connector, "pull_requests" if connector == "gh" else "meetings",
             f"{connector} watch", json.dumps(query), _naive_utc(checked),
             # Due one sweep ago: the night's sweeps never ran it.
             (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(timespec="seconds"),
             project_id),
        )


def _quiet_now(db: Database) -> HeartbeatService:
    """Quiet hours that hold NOW: began 8 hours ago, end in 1-2 hours (local).

    The rehearsal's shape on any clock: a source checked 10 hours ago was fresh
    when quiet hours began; one checked 20 hours ago was already stale."""
    hour = datetime.now().astimezone().hour
    hb = HeartbeatService(db)
    hb.update_settings({"quiet_hours": {"start": (hour - 8) % 24, "end": (hour + 2) % 24}})
    return hb


def _rig(tmp_path: Path) -> tuple[Database, ProjectService]:
    db = Database(tmp_path / "morning.db")
    db.projects.create_project(project_id="prj-hygiene", name="Rehearsal repo hygiene")
    return db, ProjectService(db)


# ── B60: the held sweep and the rows it yields ──────────────────────


def test_a_held_sweep_moves_every_source_to_the_quiet_end(tmp_path) -> None:
    db, _ps = _rig(tmp_path)
    _seed_watch(db, "prj-hygiene", "w-gh", checked=timedelta(hours=10))
    hb = _quiet_now(db)
    receipt = hb.run_sweep(OWNER)
    assert receipt["held"] is True, receipt
    until = receipt["quiet_hold"]["until"]
    assert receipt["quiet_hold"]["sources"] == 1, receipt
    assert datetime.fromisoformat(until) > datetime.now(timezone.utc)
    with db._connection() as conn:
        row = conn.execute("SELECT next_evaluation_at FROM connector_watches WHERE id='w-gh'").fetchone()
    assert row["next_evaluation_at"] == until
    # The next sweep is the quiet end, so 08:00 sweeps at once.
    assert hb.get_settings()["next_sweep_at"] == until


def test_quiet_rows_read_quiet_until_and_are_not_counted(tmp_path) -> None:
    db, ps = _rig(tmp_path)
    _seed_watch(db, "prj-hygiene", "w-gh", checked=timedelta(hours=10))
    hb = _quiet_now(db)
    hb.run_sweep(OWNER)
    answer = ps.needs_you(OWNER)
    rows = [r for r in answer["coverage"] if r["kind"] == "watch"]
    assert [r["state"] for r in rows] == ["quiet"], rows
    row = rows[0]
    end = hb.quiet_until().astimezone()
    assert row["repair"]["token"] == f"QUIET UNTIL {end:%H:%M}", row
    assert row["label"] == "GitHub · karolswdev/holdspeak-dayone-rehearsal-1558"
    assert row["watch_ids"] == ["w-gh"]
    assert row not in unread_sources(answer["coverage"])
    assert not any(r["state"] == "quiet" for r in unread_sources(answer["coverage"]))
    assert answer["complete"] is True or any(
        r["state"] not in ("available", "quiet") for r in answer["coverage"]), answer["coverage"]
    # Not counted: the number is the number of a desk whose source is fresh.
    quiet_count = answer["count"]
    with db._connection() as conn:
        conn.execute("UPDATE connector_watches SET last_success_at=? WHERE id='w-gh'",
                     (_naive_utc(timedelta(minutes=1)),))
    fresh = ps.needs_you(OWNER)
    assert [r["state"] for r in fresh["coverage"] if r["kind"] == "watch"] == ["available"]
    assert fresh["count"] == quiet_count
    with db._connection() as conn:
        conn.execute("UPDATE connector_watches SET last_success_at=? WHERE id='w-gh'",
                     (_naive_utc(timedelta(hours=10)),))
    # The Room says the same, from the same read: one state per source.
    sources = ps.room(OWNER, "prj-hygiene")["sources"]
    item = sources["items"][0]
    assert item["freshness"] == "quiet", item
    assert item["nextCheckAt"] == sources["quietUntil"] == item["quietUntil"]
    assert datetime.fromisoformat(sources["nextCheckAt"]) > datetime.now(timezone.utc)


def test_a_source_stale_before_quiet_hours_stays_stale(tmp_path) -> None:
    """Honest: quiet hours explain only what went late while they held."""
    db, ps = _rig(tmp_path)
    _seed_watch(db, "prj-hygiene", "w-old", checked=timedelta(hours=20))
    _quiet_now(db)
    rows = [r for r in ps.needs_you(OWNER)["coverage"] if r["kind"] == "watch"]
    assert [r["state"] for r in rows] == ["stale"], rows
    assert rows[0] in unread_sources(rows)


def test_outside_quiet_hours_a_late_source_is_stale_and_its_next_check_is_ahead(tmp_path) -> None:
    db, ps = _rig(tmp_path)
    _seed_watch(db, "prj-hygiene", "w-gh", checked=timedelta(hours=10))
    HeartbeatService(db).update_settings({"quiet_hours": {"start": 0, "end": 0}})  # never quiet
    rows = [r for r in ps.needs_you(OWNER)["coverage"] if r["kind"] == "watch"]
    assert [r["state"] for r in rows] == ["stale"]
    room = ps.room(OWNER, "prj-hygiene")
    item = room["sources"]["items"][0]
    assert item["freshness"] == "stale"
    # B69: the Watch's own time (5 min ago) is past: the next check is ahead.
    assert datetime.fromisoformat(item["nextCheckAt"]) > datetime.now(timezone.utc)
    assert room["sources"].get("quietUntil") is None


def test_the_first_sweep_after_the_quiet_end_runs_at_once(tmp_path) -> None:
    db = Database(tmp_path / "clock.db")
    mountain = timezone(timedelta(hours=-6))
    # 07:05 local, quiet hours 22-08: the sweep is held and stores 08:00.
    at = datetime(2026, 10, 8, 13, 5, tzinfo=timezone.utc)
    hb = HeartbeatService(db, clock=lambda: at, local_zone=mountain)
    receipt = hb.run_sweep(OWNER)
    assert receipt["held"] is True
    assert hb.get_settings()["next_sweep_at"] == "2026-10-08T14:00:00+00:00"
    # A held sweep at 07:50 (the interval would say 08:05) still waits for 08:00.
    late = datetime(2026, 10, 8, 13, 50, tzinfo=timezone.utc)
    HeartbeatService(db, clock=lambda: late, local_zone=mountain).run_sweep(OWNER)
    assert not hb.sweep_due(datetime(2026, 10, 8, 13, 59, tzinfo=timezone.utc))
    assert hb.sweep_due(datetime(2026, 10, 8, 14, 0, tzinfo=timezone.utc))
    # 08:00 sweeps (not held) and stores the plain interval again.
    eight = datetime(2026, 10, 8, 14, 0, tzinfo=timezone.utc)
    after = HeartbeatService(db, clock=lambda: eight, local_zone=mountain).run_sweep(OWNER)
    assert after["held"] is False and "quiet_hold" not in after
    assert hb.get_settings()["next_sweep_at"] == "2026-10-08T14:15:00+00:00"


# ── B74: names, never ids ───────────────────────────────────────────


def test_source_rows_are_named_for_a_person() -> None:
    assert source_label({"provider": "github", "scope": "karolswdev/x"}) == "GitHub · karolswdev/x"
    assert source_label({"provider": "meeting", "scope": "MEETINGS"}) == "Meetings"
    assert source_label({"provider": "jira", "scope": "HS"}) == "Jira · HS"


# ── B61: Retry re-checks THAT source, through the hub's route ───────


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_philo5_the_loop import _boot  # noqa: E402

    from holdspeak.db import reset_database
    from holdspeak.runtime import composition

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def test_retry_rechecks_the_source_through_the_single_watch_route(hub) -> None:
    c = hub.client
    HeartbeatService(hub.db).update_settings({"quiet_hours": {"start": 0, "end": 0}})
    pid = c.post("/api/projects", json={"name": "Rehearsal repo hygiene"}).json()["project"]["id"]
    # The rehearsal's "meeting MEETINGS · STALE" row: a meeting Watch, checked
    # last night (it reads local records; no egress in the fence).
    watch_id = "w-meetings"
    _seed_watch(hub.db, pid, watch_id, checked=timedelta(hours=10), connector="meeting")
    before = c.get("/api/desk/needs-you?fresh=1").json()
    stale = [r for r in before["coverage"] if r.get("source_id") == f"watch:{watch_id}"]
    assert stale and stale[0]["state"] == "stale", before["coverage"]
    assert stale[0]["label"] == "Meetings"
    assert stale[0]["watch_ids"] == [watch_id]
    resp = c.post(f"/api/watches/{watch_id}/evaluate")
    assert resp.status_code == 200, resp.text
    # The face's Retry reads the number again with ?fresh=1 (needsYou.ts).
    after = c.get("/api/desk/needs-you?fresh=1").json()
    rows = [r for r in after["coverage"] if r.get("source_id") == f"watch:{watch_id}"]
    assert rows and rows[0]["state"] == "available", (rows, resp.json())
    assert after["count"] == before["count"] - 1
    # The next morning: the same source, nothing new since its last check
    # (an identical snapshot is a no-op evaluation). Retry still checks it.
    assert c.post(f"/api/watches/{watch_id}/evaluate").status_code == 200  # a real diff row
    with hub.db._connection() as conn:
        conn.execute("UPDATE connector_watches SET last_success_at=? WHERE id=?",
                     (_naive_utc(timedelta(hours=10)), watch_id))
    again = c.post(f"/api/watches/{watch_id}/evaluate")
    assert again.status_code == 200 and again.json()["state"] == "no_op", again.text
    rows = [r for r in c.get("/api/desk/needs-you?fresh=1").json()["coverage"]
            if r.get("source_id") == f"watch:{watch_id}"]
    assert rows[0]["state"] == "available", rows


# ── B64: NOTHING VERIFIED reads the claims, not only the model's tag ──


ALL_INFERENCE = json.dumps({"sections": [
    {"key": "progress", "sentences": [
        {"text": "The repo hygiene meeting assigned Carol to add the CODEOWNERS file.",
         "cited_refs": ["item:hygiene"]}]},
    {"key": "next_actions", "sentences": [
        {"text": "Carol is to add a CODEOWNERS file by Friday.", "cited_refs": ["item:hygiene"]}]},
]})


def _model_boundary(monkeypatch, raw: str) -> None:
    """The model at its boundary: ``raw`` through the REAL parser, every
    citation valid (each claim an INFERENCE, SOURCE LINKED, UNREVIEWED)."""
    from holdspeak.services import project_update_service as pus

    def model(self, principal, det_claims, det_sections, det_body_md, known_names=(), memory=None):
        refs = frozenset(r for c in det_claims for r in c.refs) | {"item:hygiene"}
        sections, claims = pus._parse_model_output(raw, refs)
        return (pus._assemble_body(sections), json.dumps([c.to_dict() for c in claims]),
                "model:ia_0488064ec64348ab8679b509e8952a60", "192.168.1.43:8080", "qwen3.8-27b")

    monkeypatch.setattr(pus.ProjectUpdateService, "_draft_with_model", model)


def _published_model_update(hub) -> str:
    c = hub.client
    pid = c.post("/api/projects", json={"name": "Rehearsal repo hygiene"}).json()["project"]["id"]
    draft = c.post(f"/api/projects/{pid}/updates/draft", json={"generator": "model"})
    assert draft.status_code == 200, draft.text
    update = draft.json()["update"]
    claims = json.loads(update.get("claims_json") or "[]")
    assert claims and all(cl["kind"] == "inference" and cl["acceptance"] == "unreviewed"
                          and cl["support"] == "source_linked" for cl in claims), claims
    assert "[UNVERIFIED]" not in update["body_md"], "no model tag: the old rule let this out"
    assert c.post(f"/api/updates/{update['id']}/publish", json={}).status_code == 200
    return update["id"]


def test_an_all_inference_update_is_refused_at_preview_and_prepare(hub, tmp_path, monkeypatch) -> None:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _philo10_send import destination

    _model_boundary(monkeypatch, ALL_INFERENCE)
    update = _published_model_update(hub)
    dest = destination(hub, tmp_path / "sent")
    ref = f"project_update:{update}"
    preview = hub.client.post("/api/channels/preview", json={"document_ref": ref, "destination_id": dest})
    assert preview.status_code == 400, preview.text
    assert preview.json()["code"] == "nothing_verified", preview.text
    sent = hub.client.post("/api/channels/sends", json={"document_ref": ref, "destination_id": dest})
    assert sent.status_code >= 400 and "nothing_verified" in sent.text, sent.text
    assert not list((tmp_path / "sent").glob("*.md")), "nothing was written"
    stored = hub.db.project_updates.get_update(update)["body_md"]
    assert "Carol is to add a CODEOWNERS file by Friday." in stored, "the desk keeps the claims"


def test_a_reviewed_inference_is_sent_and_an_unreviewed_one_is_counted(hub, tmp_path, monkeypatch) -> None:
    from holdspeak.services.channel_contract import render_update

    _model_boundary(monkeypatch, ALL_INFERENCE)
    c = hub.client
    pid = c.post("/api/projects", json={"name": "Rehearsal repo hygiene"}).json()["project"]["id"]
    update = c.post(f"/api/projects/{pid}/updates/draft", json={"generator": "model"}).json()["update"]
    progress = next(cl for cl in json.loads(update["claims_json"]) if cl["section"] == "progress")
    # The owner reviews ONE claim (the editor's Accept).
    hub.root.project_update_service.review_claim(
        OWNER, update["id"], progress["span_id"], acceptance="accepted")
    assert c.post(f"/api/updates/{update['id']}/publish", json={}).status_code == 200
    body = render_update(hub.db, update["id"]).body_md
    assert "assigned Carol to add the CODEOWNERS file" in body
    assert "Carol is to add a CODEOWNERS file by Friday." not in body
    assert body.rstrip().endswith("1 claim not checked, kept on the desk."), body
    copied = c.get(f"/api/updates/{update['id']}/markdown").text
    assert "Carol is to add a CODEOWNERS file by Friday." not in copied


# ── B71: a merge is said once ───────────────────────────────────────


def test_the_drafter_drops_prose_that_repeats_a_merged_row() -> None:
    from holdspeak.services.project_update_service import _drop_repeated_merges

    row = ("- Merged: Add CODEOWNERS naming Kiraal Swedeva as owner of every file (PR #4) "
           "https://github.com/karolswdev/holdspeak-dayone-rehearsal-1558/pull/4")
    body = (
        "## Progress\n\n"
        f"{row}\n"
        "- A pull request adding a CODEOWNERS file was merged (PR #4).\n"
        "- The CODEOWNERS action is now complete with the merge of PR #4.\n"
        "- The team agreed on squash merges.\n\n"
        "## Decisions\n\n- See karolswdev/holdspeak-dayone-rehearsal-1558/pull/4 for the merge.\n\n"
        "## Risks & Blockers\n\n- Blocked on owner/other-repo/pull/4.\n"
    )
    claims = json.dumps([
        {"text": "A pull request adding a CODEOWNERS file was merged (PR #4).", "span_id": "a"},
        {"text": "The CODEOWNERS action is now complete with the merge of PR #4.", "span_id": "b"},
        {"text": "The team agreed on squash merges.", "span_id": "c"},
        {"text": "See karolswdev/holdspeak-dayone-rehearsal-1558/pull/4 for the merge.", "span_id": "d"},
        {"text": "Blocked on owner/other-repo/pull/4.", "span_id": "e"},
    ])
    out, kept = _drop_repeated_merges(body, claims, [row])
    assert out.count("(PR #4)") == 1, out
    assert row in out and "The team agreed on squash merges." in out
    assert "## Decisions\n\nNo decisions in this window." in out, out
    # Astra r1 P2-5: another repository's PR #4 is another PR: kept, with its claim.
    assert "Blocked on owner/other-repo/pull/4." in out
    assert "No risks or blockers in this window." not in out
    assert [c["span_id"] for c in json.loads(kept)] == ["c", "e"]
    # PR #40 is another PR.
    other = "## Progress\n\n" + row + "\n- PR #40 is still open.\n"
    assert _drop_repeated_merges(other, "[]", [row])[0] == other


# ── B64 (Astra r1): the CLAIMS SET decides; the owner's review is a verb ──


def _model_draft(hub, raw_body: str, claims: list[dict[str, Any]], monkeypatch) -> tuple[str, str]:
    """A model draft whose body and claims are exactly these (the boundary)."""
    from holdspeak.services import project_update_service as pus

    def model(self, principal, det_claims, det_sections, det_body_md, known_names=(), memory=None):
        return raw_body, json.dumps(claims), "model:ia_1", "192.168.1.43:8080", "qwen3.8-27b"

    monkeypatch.setattr(pus.ProjectUpdateService, "_draft_with_model", model)
    c = hub.client
    pid = c.post("/api/projects", json={"name": "Rehearsal repo hygiene"}).json()["project"]["id"]
    update = c.post(f"/api/projects/{pid}/updates/draft", json={"generator": "model"}).json()["update"]
    return pid, update["id"]


def _inference(span: str, text: str, *, section: str = "progress", verified: bool = True) -> dict[str, Any]:
    out = {"span_id": span, "text": text, "refs": ["item:hygiene"] if verified else [], "section": section,
           "kind": "inference", "support": "source_linked" if verified else "unknown",
           "acceptance": "unreviewed"}
    if not verified:
        out["verified"] = False
    return out


def _preview(hub, update: str, tmp_path) -> Any:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _philo10_send import destination

    assert hub.client.post(f"/api/updates/{update}/publish", json={}).status_code == 200
    dest = destination(hub, tmp_path / "sent")
    return hub.client.post("/api/channels/preview", json={
        "document_ref": f"project_update:{update}", "destination_id": dest})


def test_a_claim_without_its_bullet_is_still_omitted(hub, tmp_path, monkeypatch) -> None:
    """Astra r1 P1-1 case 1: formatting never decides. The inference's line
    with its bullet removed by the owner's edit stays an unreviewed claim."""
    body = ("## Progress\n\n- The ledger moved to staging.\n\n"
            "## Next Actions\n\n- Carol is to add a CODEOWNERS file by Friday.\n")
    _pid, update = _model_draft(hub, body, [
        _inference("s_progress_0", "The ledger moved to staging."),
        _inference("s_next_actions_0", "Carol is to add a CODEOWNERS file by Friday.", section="next_actions"),
    ], monkeypatch)
    c = hub.client
    assert c.post(f"/api/updates/{update}/claims/s_progress_0/review",
                  json={"acceptance": "accepted"}).status_code == 200
    unbulleted = body.replace("- Carol is to add", "Carol is to add")
    assert c.put(f"/api/updates/{update}", json={"body_md": unbulleted}).status_code == 200
    preview = _preview(hub, update, tmp_path)
    assert preview.status_code == 200, preview.text
    text = json.dumps(preview.json()["preview"])
    assert "The ledger moved to staging." in text
    assert "CODEOWNERS" not in text, text
    assert "1 claim not checked, kept on the desk." in text


def test_a_draft_with_no_claims_is_refused(hub, tmp_path, monkeypatch) -> None:
    """Astra r1 P1-1 case 2: zero claims is zero verified claims."""
    _pid, update = _model_draft(hub, "## Progress\n\n- The rollout is complete.\n", [], monkeypatch)
    preview = _preview(hub, update, tmp_path)
    assert preview.status_code == 400 and preview.json()["code"] == "nothing_verified", preview.text
    dest = hub.client.get("/api/channels/destinations").json()["destinations"][0]["id"]
    sent = hub.client.post("/api/channels/sends", json={
        "document_ref": f"project_update:{update}", "destination_id": dest})
    assert sent.status_code >= 400 and "nothing_verified" in sent.text, sent.text


def test_the_current_review_wins_over_the_old_flag_and_mark(hub, tmp_path, monkeypatch) -> None:
    """Astra r1 P1-3: a claim the model marked unverified (``verified: false``,
    the desk mark) that the owner ACCEPTED is sent."""
    from holdspeak.services.project_update_service import UNVERIFIED_MARKER

    body = f"## Progress\n\n- {UNVERIFIED_MARKER} We ship Friday.\n"
    _pid, update = _model_draft(hub, body, [_inference("s_progress_0", "We ship Friday.", verified=False)],
                                monkeypatch)
    r = hub.client.post(f"/api/updates/{update}/claims/s_progress_0/review", json={"acceptance": "accepted"})
    assert r.status_code == 200 and r.json()["reviewed_at"], r.text
    preview = _preview(hub, update, tmp_path)
    assert preview.status_code == 200, preview.text
    text = json.dumps(preview.json()["preview"])
    assert "We ship Friday." in text and "UNVERIFIED" not in text


def test_the_owners_own_words_are_reviewed_with_provenance_kept(hub, tmp_path, monkeypatch) -> None:
    """Astra r1 P1-3: a saved owner-authored replacement counts as reviewed
    for its exact new words; the model's claim stays with its provenance."""
    body = "## Progress\n\n- Carol was assigned the CODEOWNERS file.\n"
    _pid, update = _model_draft(hub, body, [_inference("s_progress_0", "Carol was assigned the CODEOWNERS file.")],
                                monkeypatch)
    mine = "## Progress\n\n- Karol added the CODEOWNERS file; PR #4 merged.\n"
    saved = hub.client.put(f"/api/updates/{update}", json={"body_md": mine})
    assert saved.status_code == 200, saved.text
    claims = json.loads(saved.json()["update"]["claims_json"])
    assert [cl["text"] for cl in claims] == [
        "Carol was assigned the CODEOWNERS file.", "Karol added the CODEOWNERS file; PR #4 merged."]
    owner = claims[1]
    assert owner["acceptance"] == "accepted" and owner["support_record"]["method"] == "reviewer"
    assert owner["support_record"]["fields"] == ["owner_text"]
    preview = _preview(hub, update, tmp_path)
    assert preview.status_code == 200, preview.text
    assert "Karol added the CODEOWNERS file" in json.dumps(preview.json()["preview"])


def test_reject_omits_and_accept_sends_through_the_route(hub, tmp_path, monkeypatch) -> None:
    from holdspeak.services.channel_contract import render_update

    body = "## Progress\n\n- The ledger moved to staging.\n- We ship Friday.\n"
    _pid, update = _model_draft(hub, body, [
        _inference("s_progress_0", "The ledger moved to staging."),
        _inference("s_progress_1", "We ship Friday."),
    ], monkeypatch)
    c = hub.client
    assert c.post(f"/api/updates/{update}/claims/s_progress_0/review", json={"acceptance": "accepted"}).status_code == 200
    rejected = c.post(f"/api/updates/{update}/claims/s_progress_1/review", json={"acceptance": "rejected"})
    assert rejected.status_code == 200
    states = {cl["span_id"]: cl["acceptance"] for cl in json.loads(rejected.json()["update"]["claims_json"])}
    assert states == {"s_progress_0": "accepted", "s_progress_1": "rejected"}
    assert c.post(f"/api/updates/{update}/claims/s_progress_1/review", json={"acceptance": "maybe"}).status_code == 400
    assert c.post(f"/api/updates/{update}/claims/nope/review", json={"acceptance": "accepted"}).status_code == 404
    assert c.post(f"/api/updates/{update}/publish", json={}).status_code == 200
    sent = render_update(hub.db, update).body_md
    assert "The ledger moved to staging." in sent and "We ship Friday." not in sent


# ── B61 (Astra r1 P1-4): no answer is not an answer ──────────────────


def test_a_blank_answer_is_a_failed_check_and_an_empty_list_is_a_read(tmp_path) -> None:
    import subprocess

    from holdspeak.services.errors import ServiceError
    from holdspeak.services.watch_service import WatchService
    from holdspeak.services.watch_sources import default_snapshot_fetcher

    db, _ps = _rig(tmp_path)
    _seed_watch(db, "prj-hygiene", "w-gh", checked=timedelta(hours=10))
    answer = {"stdout": ""}

    def gh(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout=answer["stdout"], stderr="")

    svc = WatchService(db, snapshot_fetcher=default_snapshot_fetcher(github_runner=gh))

    def last_success() -> str:
        with db._connection() as conn:
            return conn.execute("SELECT last_success_at FROM connector_watches WHERE id='w-gh'").fetchone()[0]

    before = last_success()
    with pytest.raises(ServiceError) as failed:
        svc.evaluate_once(OWNER, "w-gh")
    assert failed.value.code == "connector_no_answer" and failed.value.detail == "no answer"
    assert last_success() == before, "no answer never reads as a check"
    answer["stdout"] = "[]"
    assert svc.evaluate_once(OWNER, "w-gh")["state"] in ("baselined", "completed", "no_op")
    assert last_success() != before


# ── B70: a done action says DONE on the Room's row ─────────────────


def test_a_done_action_reads_done_on_the_room_row(tmp_path, monkeypatch) -> None:
    import tests.unit.test_phase200_meeting_outcomes as rig
    from tests.unit.test_philo15_decisions_day_one import _parse, _proposals
    from holdspeak.services.follow_through_service import FollowThroughService
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db, engine = rig._rig(tmp_path, monkeypatch)
    engine.result = _parse(json.dumps({"summary": "One action.", "topics": [], "action_items": [],
                                       "decisions": []}))
    rig._meeting(db, "m-done")
    rig._drain()
    prop = next(p for p in _proposals(db, "m-done") if p["kind"] == "action")
    kept = ProposalBridgeService(db).confirm_proposal(OWNER, prop["id"])

    def row() -> dict[str, Any]:
        items = ProjectService(db).room(OWNER, "prj-cutover")["decisions"]["items"]
        return next(d for d in items if d["id"] == kept["decision_record_id"])

    assert "done" not in row()
    with db._connection() as conn:
        action_id = conn.execute(
            "SELECT action_item_id FROM decision_commitments WHERE id=?", (kept["commitment_id"],),
        ).fetchone()[0]
    FollowThroughService(db).complete(OWNER, action_id, "done")
    done = row()
    assert done["done"] is True and done["done_at"], done
    assert datetime.fromisoformat(done["done_at"]).tzinfo is not None


def test_a_model_draft_says_each_merge_once(tmp_path, monkeypatch) -> None:
    """B71 through the real drafter: the model's prose repeats the merge the
    carried ``Merged:`` row already says; the draft keeps the row only."""
    from tests.unit import test_philo15_17_merge_reaches_update as m17
    from tests.unit.test_conductor_k4_follow_through import _seed, _updates

    db = Database(tmp_path / "hub.db")
    _seed(db)
    m17._model_from(monkeypatch, json.dumps({"sections": [
        {"key": "progress", "sentences": [
            {"text": "A pull request adding CONTRIBUTING.md with three rules was merged (PR #1).",
             "cited_refs": []},
            {"text": "The team chose squash merges.", "cited_refs": []}]},
    ]}))
    rig = m17._merged(tmp_path, db, monkeypatch)
    try:
        _delta, updates = _updates(db)
        draft = updates.draft_update(m17.OWNER, m17.PROJECT, generator="model")
        body = draft["body_md"]
        assert m17.ROW in body
        assert body.count("PR #1") == 1, body
        assert "The team chose squash merges." in body
        texts = [c["text"] for c in json.loads(draft["claims_json"])]
        assert not any("was merged (PR #1)" in t for t in texts), texts
    finally:
        rig.tmux.ended = True


# ── B64 (Astra r2): formatting never sends a sentence, nor reviews it ──


def test_a_sentence_made_a_heading_is_not_sent(hub, tmp_path, monkeypatch) -> None:
    """Astra r2 probe 1: with one accepted claim present, an unreviewed
    sentence turned into ``## <sentence>`` is omitted (only the drafter's own
    section headings are structure)."""
    body = "## Progress\n\n- The ledger moved to staging.\n- Carol is to add a CODEOWNERS file by Friday.\n"
    _pid, update = _model_draft(hub, body, [
        _inference("s_progress_0", "The ledger moved to staging."),
        _inference("s_progress_1", "Carol is to add a CODEOWNERS file by Friday."),
    ], monkeypatch)
    c = hub.client
    assert c.post(f"/api/updates/{update}/claims/s_progress_0/review",
                  json={"acceptance": "accepted"}).status_code == 200
    headed = body.replace("- Carol is to add", "## Carol is to add")
    saved = c.put(f"/api/updates/{update}", json={"body_md": headed})
    assert saved.status_code == 200
    assert not any(cl["span_id"].startswith("s_owner_") for cl in json.loads(saved.json()["update"]["claims_json"]))
    preview = _preview(hub, update, tmp_path)
    assert preview.status_code == 200, preview.text
    text = json.dumps(preview.json()["preview"])
    assert "The ledger moved to staging." in text and "CODEOWNERS" not in text, text


@pytest.mark.parametrize("reformat", [
    lambda s: f"**{s}**",                       # bold
    lambda s: f"1. {s}",                        # a numbered list
    lambda s: f"> {s}",                         # a quote
    lambda s: f"- [UNVERIFIED] {s}",            # the desk mark, unbolded
], ids=["bold", "numbered", "quote", "unbolded-mark"])
def test_reformatting_the_models_sentence_is_not_review(hub, tmp_path, monkeypatch, reformat) -> None:
    """Astra r2 probe 2 (her four cases, the real producer): re-styling the
    model's sentence creates no owner claim; the update stays NOTHING VERIFIED."""
    from holdspeak.services.project_update_service import UNVERIFIED_MARKER

    sentence = "We ship Friday."
    body = f"## Progress\n\n- {UNVERIFIED_MARKER} {sentence}\n"
    _pid, update = _model_draft(hub, body, [_inference("s_progress_0", sentence, verified=False)], monkeypatch)
    restyled = f"## Progress\n\n{reformat(sentence)}\n"
    saved = hub.client.put(f"/api/updates/{update}", json={"body_md": restyled})
    assert saved.status_code == 200, saved.text
    claims = json.loads(saved.json()["update"]["claims_json"])
    assert [cl["span_id"] for cl in claims] == ["s_progress_0"], claims
    preview = _preview(hub, update, tmp_path)
    assert preview.status_code == 400 and preview.json()["code"] == "nothing_verified", preview.text


# ── B64 (Astra r2 P2 ruling): NOTHING TO REPORT ──────────────────────


def test_nothing_to_report_waits_for_accept_then_sends(hub, tmp_path) -> None:
    c = hub.client
    pid = c.post("/api/projects", json={"name": "Quiet Project"}).json()["project"]["id"]
    update = c.post(f"/api/projects/{pid}/updates/draft", json={}).json()["update"]
    claims = json.loads(update["claims_json"])
    assert [(cl["span_id"], cl["text"], cl["acceptance"]) for cl in claims] == [
        ("s_nothing_0", "Nothing to report.", "unreviewed")]
    assert update["body_md"] == "Nothing to report.\n"
    # Unreviewed: refused, no filler needed.
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _philo10_send import destination

    dest = destination(hub, tmp_path / "sent")
    ref = {"document_ref": f"project_update:{update['id']}", "destination_id": dest}
    assert c.post(f"/api/updates/{update['id']}/claims/s_nothing_0/review",
                  json={"acceptance": "accepted"}).status_code == 200
    assert c.post(f"/api/updates/{update['id']}/publish", json={}).status_code == 200
    preview = c.post("/api/channels/preview", json=ref)
    assert preview.status_code == 200, preview.text
    assert preview.json()["preview"]["text"].endswith("\n\nNothing to report.\n"), preview.json()


def test_nothing_to_report_unaccepted_is_refused(hub, tmp_path) -> None:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _philo10_send import destination

    c = hub.client
    pid = c.post("/api/projects", json={"name": "Quiet Project"}).json()["project"]["id"]
    update = c.post(f"/api/projects/{pid}/updates/draft", json={}).json()["update"]["id"]
    assert c.post(f"/api/updates/{update}/publish", json={}).status_code == 200
    dest = destination(hub, tmp_path / "sent")
    preview = c.post("/api/channels/preview", json={"document_ref": f"project_update:{update}",
                                                     "destination_id": dest})
    assert preview.status_code == 400 and preview.json()["code"] == "nothing_verified", preview.text
