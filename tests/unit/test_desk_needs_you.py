"""Needs you (the Chair's arrival app), against the real hub (the test diet, 2026-10-11).

The successors of the Needs-you browser tests: the hub facts each of them read
through the page, asserted here through the real routes on an isolated hub
(``MeetingWebServer`` + ``TestClient``; no port, no browser). The faces' half
of each browser test is ``web/src/desk/__tests__/needsYou.app.test.tsx``.

Each test names the browser test it replaces (``replaces:``). The seeds are
the browser tests' own seeds (the same producer calls and SQL).
"""
from __future__ import annotations

import json
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub  # noqa: E402

TOKEN = "desk-needs-you"


def _boot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, gh_runner: Any = None) -> Hub:
    """The real hub on an isolated HOME and database, with the glass rig's switches."""
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
    from starlette.testclient import TestClient

    home = tmp_path
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("HOLDSPEAK_MACOS_CALENDAR", "0")
    monkeypatch.setenv("HOLDSPEAK_AGENT_STATE", "off")
    monkeypatch.setenv("HOLDSPEAK_ACTIVE_TARGET", "off")
    monkeypatch.setenv("HOLDSPEAK_DESKTOP_NOTIFY", "0")
    monkeypatch.setenv("HOLDSPEAK_TEST_NO_REAL_CLI", "1")
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GH_CONFIG_DIR", str(home / ".config" / "gh"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("HOLDSPEAK_CHANNEL_KEYSTORE_FILE", str(home / "channel-keys.json"))
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(home / "people.key"))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home / ".claude"))
    monkeypatch.setenv("CODEX_HOME", str(home / ".codex"))
    monkeypatch.setenv("PI_CODING_AGENT_DIR", str(home / ".pi" / "agent"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "hub.db")
    reset_database()
    kwargs: dict[str, Any] = {}
    if gh_runner is not None:
        kwargs["gh_runner"] = gh_runner
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(),
                            get_state=MagicMock(return_value={})),
        auth_token=TOKEN,
        **kwargs,
    )
    frames: list[tuple[str, Any]] = []
    server.broadcast = lambda message_type, data: frames.append((message_type, data))
    client = TestClient(server.app, client=("127.0.0.1", 50000))
    client.headers.update({"Authorization": f"Bearer {TOKEN}"})
    hub = Hub(server, composition.installed(), client, frames)
    assert Path(str(hub.db.db_path)).parent == tmp_path, "the hub is not on the isolated database"
    return hub


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _ok(response: Any, status: int = 200) -> dict[str, Any]:
    assert response.status_code == status, response.text
    return response.json()


def _needs(hub: Hub) -> dict[str, Any]:
    return _ok(hub.client.get("/api/desk/needs-you?fresh=1"))


# ── Name an owner / Review on a meeting's action items ────────────────────

OWNED = "Draft the migration runbook"
UNOWNED = "Book the dry run"


def _seed_planning(hub: Hub, *, unowned: bool = True) -> None:
    """The browser tests' seed: a meeting's action items, saved by the real producer."""
    from holdspeak.intel.models import ActionItem
    from holdspeak.meeting_session.models import IntelSnapshot, MeetingState

    items = [ActionItem(task=OWNED, owner="Priya")]
    if unowned:
        items.append(ActionItem(task=UNOWNED))
    start = datetime.now().replace(microsecond=0) - timedelta(hours=2)
    hub.db.meetings.save_meeting(MeetingState(
        id="m-owner-verb", started_at=start, ended_at=start + timedelta(minutes=30), title="Planning",
        intel=IntelSnapshot(timestamp=0.0, summary="Planned.", action_items=items), intel_status="completed"))


def test_name_an_owner_saves_the_owner_and_the_item_stays_to_review(hub: Hub) -> None:
    """replaces: tests/e2e/test_chair_owner_verb_glass.py::test_owner_verb_only_where_no_owner_exists
    (the hub half: the Door's lane facts before and after the owner well's Save)."""
    _seed_planning(hub)
    board = _ok(hub.client.get("/api/door"))["board"]
    # Both are born review_state=pending, so both sit in `unassigned`; one is owned.
    assert {card["text"]: card.get("owner") for card in board["unassigned"]} == {OWNED: "Priya", UNOWNED: None}
    rows = {row["title"]: row for row in _needs(hub)["items"]}
    assert rows[OWNED]["why"] == "TO REVIEW" and rows[UNOWNED]["why"] == "UNASSIGNED"

    unowned_id = next(card["id"] for card in board["unassigned"] if card["text"] == UNOWNED)
    # The owner well's Save: the Door card's delegate verb (NeedsDrawer CommitWell).
    _ok(hub.client.post("/api/follow-through/complete", json={
        "card_id": unowned_id, "verb": "delegate", "payload": {"to": "Avery"}}))

    after = _ok(hub.client.get("/api/door"))["board"]
    # Not reviewed yet: the item stays in the same lane, now with its owner.
    assert {card["text"]: card.get("owner") for card in after["unassigned"]} == {OWNED: "Priya", UNOWNED: "Avery"}
    rows = {row["title"]: row for row in _needs(hub)["items"]}
    assert rows[UNOWNED]["why"] == "TO REVIEW", rows[UNOWNED]
    assert rows[UNOWNED]["_isUnassigned"] is False


def test_the_producer_card_names_itself_in_target_ref_and_has_no_open_ref(hub: Hub) -> None:
    """replaces: tests/e2e/test_chair_review_verb_glass.py::test_review_opens_the_card_in_follow_through
    (the hub half: Review needs `target_ref`, the producer's card has no `open_ref`; the
    Follow-through board holds the same card under the same id, so the focus lands)."""
    _seed_planning(hub, unowned=False)
    card = _ok(hub.client.get("/api/door"))["board"]["unassigned"][0]
    assert card["text"] == OWNED and card["owner"] == "Priya"
    assert card["target_ref"] == f"action_item:{card['id']}"
    assert not card.get("open_ref")
    board = _ok(hub.client.get("/api/follow-through/board"))
    assert [c["id"] for c in board["unassigned"]] == [card["id"]]
    assert board["unassigned"][0]["text"] == OWNED


# ── The oracle week: the head counts what needs him; Waiting lists the rest ──


def test_the_count_is_what_needs_him_and_waiting_lists_the_rest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """replaces: tests/e2e/test_needs_you_means_you_glass.py::TestNeedsYouMeansYou::test_the_head_counts_what_needs_him_and_waiting_lists_the_rest
    (the hub half: 6 with A3 waiting; A4 named -> 5 and two waiting; the decision accepted -> 4)."""
    from holdspeak.db import reset_database
    from scripts.philo13_needs_you_fixture import A3_ID, A4_ID, DECISION_ID, seed_week

    monkeypatch.setenv("HOME", str(tmp_path))
    week = seed_week(tmp_path / "hub.db", home=tmp_path)
    hub = _boot(tmp_path, monkeypatch)
    try:
        before = _needs(hub)
        members = {m["ref"] for m in before["members"]}
        assert before["count"] == 6 and before["waitingCount"] == 1, (before["count"], before["waitingCount"])
        assert len(before["members"]) == 6 and sorted(members) == sorted(week["expectedRefs"])
        rows = {str(r.get("ref")): r for r in before["items"]}
        assert rows[A3_ID]["why"] == "WAITING ON PRIYA" and rows[A3_ID]["waiting"] is True
        assert A3_ID not in members and A4_ID in members
        # The decision row is a member; Review opens the decision by its ref.
        decision_ref = f"decision:{DECISION_ID}"
        assert decision_ref in members
        assert rows[decision_ref]["openRef"] == decision_ref

        # Name an owner on A4 (the Door card's delegate verb): 5, and two wait.
        _ok(hub.client.post("/api/follow-through/complete", json={
            "card_id": A4_ID, "verb": "delegate", "payload": {"to": "Dana"}}))
        named = _needs(hub)
        assert named["count"] == 5 and named["waitingCount"] == 2, (named["count"], named["waitingCount"])
        rows = {str(r.get("ref")): r for r in named["items"]}
        assert rows[A4_ID]["why"] == "WAITING ON DANA" and rows[A4_ID]["waiting"] is True
        assert A4_ID not in {m["ref"] for m in named["members"]}

        # Accept the decision: 4, and it is no member.
        _ok(hub.client.put(f"/api/decisions/{DECISION_ID}/status", json={"status": "accepted"}))
        decided = _needs(hub)
        assert decided["count"] == 4 and decided["waitingCount"] == 2
        assert decision_ref not in {m["ref"] for m in decided["members"]}
    finally:
        reset_database()
        composition.install(composition.bare(label="pytest"))


# ── Confirm / Defer a proposal from a meeting in no Project ───────────────

UNFILED = "m-philo15-08"
ACTION = "Add the named failure fence before ship"
DECISION = "Use a recorded provider reply for isolated rig tests"


def _seed_unfiled(hub: Hub) -> dict[str, str]:
    """The browser test's seed: a finished summary of an unfiled meeting, bridged by the real bridge."""
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db = hub.db
    now = datetime.now()
    # A due a week out: Priya's item then sits in the Door's waiting column on
    # every weekday. A spoken "Friday" fell inside the two-day "now" window
    # (follow_through_service._lane) from Wednesday to Friday, and the row
    # read DUE TODAY instead of WAITING ON PRIYA SHAH (a calendar red).
    due = (now + timedelta(days=7)).date().isoformat()
    action_id = "action_philo15_08_priya"
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, ended_at, title, duration_seconds, "
            " intel_status, intel_completed_at, capture_status, provenance) "
            "VALUES (?, ?, ?, ?, 35.0, 'complete', ?, 'finalized', 'desktop')",
            (UNFILED, (now - timedelta(minutes=20)).isoformat(),
             (now - timedelta(minutes=19)).isoformat(), "philo3_architect_meeting",
             (now - timedelta(minutes=18)).isoformat()),
        )
        for start, end, text in (
            (0.0, 26.0, "Decision three: use a recorded provider reply for isolated rig tests."),
            (26.0, 35.0, "Action: Priya Shah will add the named failure fence before ship."),
        ):
            conn.execute(
                "INSERT INTO segments (meeting_id, text, speaker, start_time, end_time) "
                "VALUES (?, ?, 'Speaker', ?, ?)",
                (UNFILED, text, start, end),
            )
        conn.execute(
            "INSERT INTO action_items (id, meeting_id, task, owner, due, status, review_state, created_at) "
            "VALUES (?, ?, ?, 'Priya Shah', ?, 'pending', 'pending', ?)",
            (action_id, UNFILED, ACTION, due, now.isoformat()),
        )
        conn.execute(
            "INSERT INTO artifacts (id, meeting_id, origin, artifact_type, title, structured_json, "
            " confidence, status, plugin_id, plugin_version) "
            "VALUES (?, ?, 'meeting', 'summary_items', 'Decisions and action items', ?, 1.0, "
            " 'draft', 'meeting_summary', '1')",
            (f"summary-items-{UNFILED}", UNFILED, json.dumps({
                "decisions": [{"decision": DECISION, "rationale": None}],
                "action_items": [{"task": ACTION, "owner": "Priya Shah", "due": due,
                                  "action_item_id": action_id}],
            })),
        )
        conn.commit()
    created = ProposalBridgeService(db).bridge_meeting_artifacts(UNFILED)
    assert {p.kind for p in created} == {"decision", "action"}, created
    return {"action_item_id": action_id, "proposal_id": next(p.id for p in created if p.kind == "action")}


def _rows_titled(answer: dict[str, Any], title: str) -> list[dict[str, Any]]:
    return [row for row in answer["items"] if str(row.get("title") or "") == title]


def test_confirm_an_unfiled_meetings_action_from_its_one_needs_row(hub: Hub) -> None:
    """replaces: tests/e2e/test_philo15_08_confirm_unfiled_glass.py::TestConfirmFromAnUnfiledMeeting::test_confirm_an_action_item_from_its_needs_row
    (the hub half: one row for the obligation, a proposal; Confirm through the route the
    row's verb posts; the proposal is confirmed and the summary's action row accepted)."""
    ids = _seed_unfiled(hub)
    before = _needs(hub)
    rows = _rows_titled(before, ACTION)
    # The summary's own To review card of the same action is not a second row.
    assert len(rows) == 1, rows
    assert rows[0]["proposalId"] == ids["proposal_id"] and rows[0]["proposalKind"] == "action", rows[0]
    assert rows[0]["proposalActionItemId"] == ids["action_item_id"]
    assert rows[0]["meetingTitle"] == "philo3_architect_meeting"

    _ok(hub.client.post(f"/api/proposals/{ids['proposal_id']}/confirm"))

    # The row leaves Needs: what is left of the obligation names its owner,
    # Priya Shah, so it waits on her (listed under Waiting, never counted).
    after = _needs(hub)
    left = _rows_titled(after, ACTION)
    assert all(row.get("waiting") is True for row in left), left
    assert not [m for m in after["members"] if m["ref"] in {str(r.get("ref")) for r in left}]
    wire = _ok(hub.client.get(f"/api/meetings/{UNFILED}/follow-through-proposals"))
    assert {p["id"]: p["state"] for p in wire["proposals"]}[ids["proposal_id"]] == "confirmed"
    with hub.db._connection() as conn:
        actions = conn.execute(
            "SELECT id, review_state FROM action_items WHERE meeting_id=?", (UNFILED,)).fetchall()
    assert [(r["id"], r["review_state"]) for r in actions] == [(ids["action_item_id"], "accepted")]


def test_defer_holds_back_the_whole_obligation(hub: Hub) -> None:
    """replaces: tests/e2e/test_philo15_08_confirm_unfiled_glass.py::TestConfirmFromAnUnfiledMeeting::test_defer_holds_back_the_whole_obligation
    (Defer takes the action off Needs, its To review card included; the proposal stays
    `proposed` with `deferred_until`, and the meeting's Review wing still lists it)."""
    ids = _seed_unfiled(hub)
    assert len(_rows_titled(_needs(hub), ACTION)) == 1

    _ok(hub.client.post(f"/api/proposals/{ids['proposal_id']}/defer", json={}))

    after = _needs(hub)
    assert _rows_titled(after, ACTION) == []
    # The decision of the same meeting is still there (a fresh read draws it).
    assert len(_rows_titled(after, DECISION)) == 1
    assert not [c for c in after.get("coverage") or [] if ACTION in str(c.get("label") or "")]
    review = _ok(hub.client.get(f"/api/meetings/{UNFILED}/outcome-review"))
    held = [p for p in review["proposals"] if p["text"] == ACTION]
    assert held and held[0]["state"] == "proposed" and held[0]["deferred_until"], held


# ── Sources of one cause are one row (PHILO-17) ───────────────────────────

SIGNED_OUT = "To get started with GitHub CLI, please run:  gh auth login"


def _signed_out_gh(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    cmd = args[0] if args else kwargs.get("args", [])
    return subprocess.CompletedProcess(args=cmd, returncode=4, stdout="", stderr=SIGNED_OUT)


def _utc_naive(delta: timedelta = timedelta()) -> str:
    return (datetime.now(timezone.utc).replace(tzinfo=None) + delta).isoformat()


def _insert_watch(hub: Hub, watch_id: str, project_id: str, connector: str, query_kind: str,
                  query: dict[str, Any], *, last_success_at: str | None = None) -> None:
    with hub.db._connection() as conn:
        conn.execute(
            "INSERT INTO connector_watches "
            "(id, connector_id, query_kind, name, query_json, snapshot_json, enabled, last_success_at, "
            " last_error, project_id, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, '[]', 1, ?, NULL, ?, datetime('now'), datetime('now'))",
            (watch_id, connector, query_kind, f"{connector} {query_kind}", json.dumps(query, sort_keys=True),
             last_success_at, project_id),
        )


def test_sources_of_one_cause_are_one_counted_row(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """replaces: tests/e2e/test_philo17_needs_you_grouped_glass.py::test_one_row_per_cause_and_repair_on_the_real_hub
    (the hub half: 30 signed-out GitHub sources minted by the producer are one group with one
    plain cause; the paused source and each Jira site are groups of their own, each Jira with
    its host; the hub's count counts each group once)."""
    from holdspeak.db import reset_database
    from holdspeak.services.needs_you_membership import unread_source_groups

    hub = _boot(tmp_path, monkeypatch, gh_runner=_signed_out_gh)
    try:
        rooms = {}
        for key, name in (("a", "Payments ledger"), ("b", "Staff hiring")):
            created = _ok(hub.client.post("/api/projects", json={
                "name": name, "description": "PHILO-17 grouped sources", "command_id": f"p17-room-{key}"}))
            rooms[key] = created["project"]["id"]
        for n in range(30):
            room = rooms["a"] if n % 2 == 0 else rooms["b"]
            _insert_watch(hub, f"w-gh-{n}", room, "gh", "pull_requests", {"repository": f"acme/repo-{n:02d}"})
            # gh is signed out; the producer (WatchService.baseline) records the error.
            assert hub.client.post(f"/api/watches/w-gh-{n}/baseline", json={}).status_code >= 400
        _insert_watch(hub, "w-gh-paused", rooms["b"], "gh", "pull_requests", {"repository": "acme/paused"},
                      last_success_at=_utc_naive(-timedelta(minutes=5)))
        _ok(hub.client.post("/api/watches/w-gh-paused/pause", json={}))
        for site in ("alpha", "beta"):
            _insert_watch(hub, f"w-jira-{site}", rooms["a"], "jira", "issues",
                          {"projects": [site.upper()], "connection_ref": f"{site}.atlassian.net|me@acme.dev"},
                          last_success_at=_utc_naive(-timedelta(days=2)))

        wire = _needs(hub)
        gh_failed = [c for c in wire["coverage"] if c.get("provider") == "github" and c["state"] == "failed"]
        assert len(gh_failed) == 30, [c.get("reason") for c in wire["coverage"]]
        assert {c["cause"] for c in gh_failed} == {"Not signed in"}

        groups = unread_source_groups(wire["coverage"])
        assert len(groups) == 4, [[r.get("label") for r in g] for g in groups]
        sizes = sorted(len(g) for g in groups)
        assert sizes == [1, 1, 1, 30], sizes
        signed_out = next(g for g in groups if len(g) == 30)
        assert {r["repair"]["verb"] for r in signed_out} == {"Reconnect"}
        paused = [g[0] for g in groups if g[0].get("cause") == "paused"]
        assert [r["label"] for r in paused] == ["GitHub · acme/paused"], paused
        jira = [g[0] for g in groups if g[0].get("provider") == "jira"]
        assert sorted(r["host"] for r in jira) == ["alpha.atlassian.net", "beta.atlassian.net"], jira
        # One number: the hub counts each group once beside the members.
        assert wire["count"] == len(wire["members"]) + len(groups) + len(wire.get("arming") or []), wire["count"]
    finally:
        reset_database()
        composition.install(composition.bare(label="pytest"))


# ── Arrival: proposal rows and their Confirm (HS-172) ─────────────────────


def _seed_hs172(hub: Hub) -> None:
    """The browser test's seed: a Room, a GitHub Watch, a ran meeting with two proposals."""
    now = datetime.now()
    with hub.db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO projects "
            "(id, name, description, keywords_json, team_members_json, "
            "context_json, detection_threshold, is_archived, revision, "
            "target_at, created_at, updated_at) "
            "VALUES ('proj-a', 'Q4 Platform', '', '[]', '[]', '{}', 0.5, 0, 1, NULL, "
            "'2026-09-01T00:00:00', '2026-09-05T10:00:00')",
        )
        conn.execute(
            "INSERT OR IGNORE INTO watch_provider_connections "
            "(id, provider_id, external_connection_ref, state, "
            " last_connected_at, created_at, updated_at) "
            "VALUES ('wpc-gh', 'github', 'karolswdev', 'connected', "
            " datetime('now'), datetime('now'), datetime('now'))",
        )
        conn.execute(
            "INSERT INTO connector_watches "
            "(id, connector_id, query_kind, name, query_json, snapshot_json, "
            " enabled, last_success_at, last_error, project_id, "
            " created_at, updated_at) "
            "VALUES ('w-prs', 'gh', 'pull_requests', 'gh prs', '{}', ?, 1, "
            " datetime('now'), NULL, 'proj-a', datetime('now'), datetime('now'))",
            (json.dumps([{
                "title": "Rig settles animations before every shot", "number": 612, "state": "open",
                "url": "https://github.com/karolswdev/holdspeak/pull/612",
                "reviewRequests": ["karolswdev"],
                "created_at": (now - timedelta(days=3)).isoformat(), "updated_at": now.isoformat(),
            }]),),
        )
        conn.execute(
            "INSERT OR IGNORE INTO meetings "
            "(id, started_at, ended_at, title, duration_seconds, "
            " intel_status, capture_status, provenance) "
            "VALUES ('m-standup', ?, ?, 'Standup', 1800.0, 'complete', 'finalized', 'desktop')",
            ((now - timedelta(hours=1)).isoformat(), (now - timedelta(minutes=30)).isoformat()),
        )
        for i in range(3):
            conn.execute(
                "INSERT INTO segments (meeting_id, text, speaker, start_time, end_time) "
                "VALUES ('m-standup', ?, 'Karol', ?, ?)",
                (f"Topic {i}", float(i * 600), float((i + 1) * 600)),
            )
        conn.execute(
            "INSERT OR IGNORE INTO meeting_projects (meeting_id, project_id) VALUES ('m-standup', 'proj-a')")
        for kind, text, due in (("action", "Marek owns the PostgreSQL migration", "Fri"),
                                ("decision", "cut-over on the 12th", None)):
            conn.execute(
                "INSERT INTO follow_through_proposals "
                "(id, meeting_id, project_id, kind, text, due_hint, "
                " source_plugin, fingerprint, state, model_host, created_at) "
                "VALUES (?, 'm-standup', 'proj-a', ?, ?, ?, 'decision_capture', ?, "
                " 'proposed', '192.168.1.43', ?)",
                (f"prop-{uuid.uuid4().hex[:12]}", kind, text, due, f"fp-{uuid.uuid4().hex[:16]}",
                 now.isoformat()),
            )
        conn.commit()


def _proposal_rows(answer: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in answer["items"] if row.get("source") == "proposal"}


def test_arrival_proposal_rows_carry_their_meeting_kind_and_date(hub: Hub) -> None:
    """replaces: tests/e2e/test_hs172_arrival_glass.py::TestArrivalProposals::test_arrival_proposals
    (the hub half: each proposal is a counted row that names its meeting, its kind and its date)."""
    _seed_hs172(hub)
    answer = _needs(hub)
    rows = _proposal_rows(answer)
    assert sorted((r["proposalKind"], r["title"]) for r in rows.values()) == [
        ("action", "Marek owns the PostgreSQL migration"), ("decision", "cut-over on the 12th")]
    for row in rows.values():
        assert row["meetingTitle"] == "Standup" and row["projectId"] == "proj-a", row
    assert next(r for r in rows.values() if r["proposalKind"] == "action")["proposalDue"] == "Fri"
    # Betterment D1: the decision to make counts; a promise counts once kept.
    members = {m["ref"] for m in answer["members"]}
    counted = {r["proposalKind"]: (r.get("ref") if r.get("ref") is not None else r["id"]) in members
               for r in rows.values()}
    assert counted == {"decision": True, "action": False}, counted


def test_arrival_confirm_removes_exactly_that_proposal_and_files_the_obligation(hub: Hub) -> None:
    """replaces: tests/e2e/test_hs172_arrival_glass.py::TestArrivalProposals::test_arrival_confirm_fires
    (the hub half: Confirm through the route the row's verb posts; exactly that row leaves;
    an action becomes a Room commitment that owns its action item; a decision asks nothing)."""
    from holdspeak.services.needs_you_membership import unread_source_groups

    _seed_hs172(hub)
    seeded = _ok(hub.client.get("/api/projects/proj-a/proposals"))["proposals"]
    by_kind = {p["kind"]: p for p in seeded if p["state"] == "proposed"}
    assert {"action", "decision"} <= set(by_kind), seeded

    for kind in ("action", "decision"):
        proposal = by_kind[kind]
        title = proposal["text"]
        before = _needs(hub)
        assert f"proposal:{proposal['id']}" in _proposal_rows(before)
        _ok(hub.client.post(f"/api/proposals/{proposal['id']}/confirm"))
        after = _needs(hub)
        assert set(_proposal_rows(before)) - set(_proposal_rows(after)) == {f"proposal:{proposal['id']}"}
        assert not set(_proposal_rows(after)) - set(_proposal_rows(before))
        # The headline is the hub's one number: its members, each unread group, each arming.
        assert after["count"] == len(after["members"]) + len(after.get("arming") or []) + len(
            unread_source_groups(after.get("coverage") or []))
        same_title = [r for r in after["items"] if r["title"] == title and r.get("source") != "proposal"]
        if kind == "decision":
            # A confirmed decision asks nobody to do anything: no row, no UNASSIGNED card.
            assert same_title == [], same_title
            continue
        assert len(same_title) == 1, after["items"]
        row = same_title[0]
        assert row["source"] == "commitment" and row.get("actionItemId"), row
        # The commitment owns its action item: no Door card for it.
        assert not [r for r in after["items"] if r.get("_isDoor") and r.get("ref") == row["actionItemId"]]
        # Betterment D1: kept, it is his (no owner named) and due on Friday
        # ("Fri", read against the meeting's day): it counts on that day.
        assert row["direction"] == "mine", row
        members = {m["ref"] for m in after["members"]}
        ref = row.get("ref") if row.get("ref") is not None else row["id"]
        assert (ref in members) == bool(row["counted"]), (row, members)

    confirmed = _ok(hub.client.get("/api/projects/proj-a/proposals?state=confirmed"))["proposals"]
    assert {p["id"] for p in confirmed} >= {by_kind["action"]["id"], by_kind["decision"]["id"]}


# ── honest faces: a Room's meeting action is counted once on the desk ─────


def _seed_honest_faces(hub: Hub) -> None:
    """tests/e2e/test_honest_faces_glass.py::_seed, verbatim (real producers):
    a Project with two meetings, each with one unowned action item; the first
    meeting also records a decision, and its lifecycle row gets a record."""
    from holdspeak.db.decisions import backfill_decisions
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.decision_record_service import DecisionRecordService

    db = hub.db
    owner = Principal(PrincipalKind.OWNER, "karol")
    db.projects.create_project(
        project_id="p-ledger", name="Payments ledger cutover",
        description="Move settlement to the new ledger by Nov 5.",
        keywords=["payments", "ledger", "cutover"],
    )
    now = datetime.now()
    for mid, title, hours_ago, action, decisions in (
        ("m-standup", "Ledger cutover sync", 2, "Write the rollback runbook",
         ["Freeze the old ledger on Nov 5"]),
        ("m-arch", "Architecture review: tracing", 26, "Pilot OTel in billing", []),
    ):
        start = (now - timedelta(hours=hours_ago)).replace(microsecond=0)
        summary = "Dual-write is stable. The team agreed to freeze the old ledger on Nov 5."
        db.meetings.save_meeting(MeetingState(
            id=mid, started_at=start, ended_at=start + timedelta(minutes=30), title=title,
            segments=[TranscriptSegment(text="Dual-write is stable.", speaker="Me",
                                        start_time=1.0, end_time=4.0)],
            intel=IntelSnapshot(timestamp=1.0, topics=["cutover"], summary=summary, action_items=[{
                "id": f"{mid}-a1", "task": action, "owner": None, "due": None,
                "status": "pending", "review_state": "accepted",
                "source_timestamp": None, "created_at": start.isoformat()}]),
            intel_status="completed",
        ))
        db.projects.associate_meeting_project(
            meeting_id=mid, project_id="p-ledger", source="manual", confidence=1.0)
        if decisions:
            db.plugins.record_artifact(
                artifact_id=f"{mid}-decisions", meeting_id=mid, artifact_type="decisions",
                title="Meeting decisions", plugin_id="honest-faces",
                structured_json={"decisions": [
                    {"decision": d, "rationale": "Agreed in the meeting."} for d in decisions]},
            )
    with db._connection() as conn:
        backfill_decisions(conn)
    lifecycle = db.decisions.list(meeting_id="m-standup")[0]
    DecisionRecordService(db).create_from_meeting(owner, lifecycle.id)


def test_a_rooms_meeting_action_is_one_door_card_on_the_desk(hub: Hub) -> None:
    """replaces: tests/e2e/test_honest_faces_glass.py::test_room_actions_are_not_counted_twice_on_the_desk

    After a sweep, the desk's answer holds each meeting action ONE time, as
    its Door card; the Room rows (`roomItems`) carry no action row; no ref
    and no title repeats."""
    _seed_honest_faces(hub)
    _ok(hub.client.post("/api/settings/heartbeat/run-now"))
    aggregate = _needs(hub)
    assert not [row for row in aggregate["roomItems"] if row.get("kind") == "action_item"], aggregate["roomItems"]
    actions = [row for row in aggregate["items"] if row.get("kind") == "action_item"]
    assert sorted(row["title"] for row in actions) == ["Pilot OTel in billing", "Write the rollback runbook"], actions
    assert all(row.get("_isDoor") for row in actions), actions
    refs = [row["ref"] for row in actions]
    assert len(refs) == len(set(refs)), refs
    titles = [row["title"] for row in aggregate["items"]]
    assert len(titles) == len(set(titles)), titles


# ── PHILO-17 (evalerror): a failed Evaluate reaches Needs you ──────────────
# The seed of tests/e2e/test_philo17_evaluate_error_glass.py: a gh runner that
# answers as a signed-out gh does, its stderr carrying synthetic credentials;
# two live, graduated GitHub Watches in one Room.

EVAL_CREDENTIAL_LINES = (
    "token ghp_AAAAbbbbCCCCddddEEEEffffGGGGhhhh1234",
    "Authorization: Basic dXNlcjpodW50ZXIycGFzcw==",
    "fetch https://octo:hunter2pass@github.com/acme/app.git",
    "GET https://api.github.com/x?token=qwertyuiop123",
    "acli ATATT3xFfGF0abcdefghijklmnopqrstuvwxyz0123456789",
)
EVAL_SECRETS = ("ghp_AAAA", "dXNlcjpodW50ZXIycGFzcw", "hunter2pass", "qwertyuiop123", "ATATT3xFfGF0")
EVAL_WATCHES = ("w-eval-a", "w-eval-b")


def _signed_out_gh_with_secrets(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    cmd = args[0] if args else kwargs.get("args", [])
    return subprocess.CompletedProcess(args=cmd, returncode=4, stdout="",
                                       stderr="\n".join((SIGNED_OUT, *EVAL_CREDENTIAL_LINES)))


def seed_eval_error_room(hub: Hub) -> str:
    """The Room and its two live Watches (state active, read five minutes ago, no error)."""
    room = _ok(hub.client.post("/api/projects", json={
        "name": "Payments ledger", "description": "PHILO-17 evaluate error",
        "command_id": "p17-evalerror-room"}))["project"]["id"]
    checked = _utc_naive(-timedelta(minutes=5))
    for n, watch_id in enumerate(EVAL_WATCHES):
        with hub.db._connection() as conn:
            conn.execute(
                "INSERT INTO connector_watches "
                "(id, connector_id, query_kind, name, query_json, snapshot_json, enabled, last_success_at, "
                " last_error, project_id, state, created_at, updated_at) "
                "VALUES (?, 'gh', 'pull_requests', ?, ?, '[]', 1, ?, NULL, ?, 'active', datetime('now'), datetime('now'))",
                (watch_id, f"gh acme/repo-{n}", json.dumps({"repository": f"acme/repo-{n}"}, sort_keys=True),
                 checked, room),
            )
    return room


def evaluate_both(hub: Hub) -> tuple[Any, Any]:
    """The owner's Evaluate on the first Watch (the route), an agent's on the second (MCP)."""
    route = hub.client.post(f"/api/watches/{EVAL_WATCHES[0]}/evaluate", json={})
    mcp = hub.client.post("/api/mcp", json={
        "jsonrpc": "2.0", "id": "evalerror", "method": "tools/call",
        "params": {"name": "project.watch.evaluate", "arguments": {"watch_id": EVAL_WATCHES[1]}}})
    return route, mcp


def _github_failed(hub: Hub) -> list[dict[str, Any]]:
    return [c for c in _needs(hub)["coverage"] if c.get("provider") == "github" and c["state"] == "failed"]


def test_a_failed_evaluate_is_stored_and_reaches_needs_you_without_a_secret(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """replaces: tests/e2e/test_philo17_evaluate_error_glass.py::test_a_failed_evaluate_reaches_needs_you_as_its_grouped_row (hub half)"""
    from holdspeak.db import reset_database

    hub = _boot(tmp_path, monkeypatch, gh_runner=_signed_out_gh_with_secrets)
    try:
        seed_eval_error_room(hub)
        assert _github_failed(hub) == []

        route, mcp = evaluate_both(hub)
        assert route.status_code == 400, route.text
        assert route.json()["code"] == "connector_refresh_failed", route.text
        assert mcp.status_code == 200, mcp.text
        result = mcp.json()["result"]
        assert result["isError"] is True, result
        assert json.loads(result["content"][0]["text"])["code"] == "connector_refresh_failed", result
        assert "gh auth login" in route.text
        assert [x for x in EVAL_SECRETS if x in route.text] == [], route.text
        assert [x for x in EVAL_SECRETS if x in mcp.text] == [], mcp.text

        for watch_id in EVAL_WATCHES:
            stored = hub.db.automations.get_watch(watch_id)["last_error"]
            assert "gh auth login" in stored, stored
            assert [x for x in EVAL_SECRETS if x in stored] == [], stored

        failed = _github_failed(hub)
        assert sorted(c["source_id"] for c in failed) == [f"watch:{w}" for w in EVAL_WATCHES], failed
        assert {c["cause"] for c in failed} == {"Not signed in"}, failed
        assert [x for x in EVAL_SECRETS if x in json.dumps(_needs(hub))] == []
    finally:
        reset_database()
        composition.install(composition.bare(label="pytest"))


# ── HS-144: the Door's action items on the arrival (sync push seed) ───────


def _seed_door_sync(hub: Hub) -> None:
    """The browser test's seed, through the same routes: one synced meeting
    with four accepted action items (overdue, today, next week, no owner),
    then an active thought."""
    from datetime import date

    now = datetime.now(timezone.utc)
    today = date.today()
    rows = [
        ("hs144-overdue", "Unblock the overdue Door proof", "Ada", today - timedelta(days=1)),
        ("hs144-now", "Review the front door today", "Bea", today),
        ("hs144-waiting", "Prepare next week's review", "Cy", today + timedelta(days=5)),
        ("hs144-unassigned", "Name an owner for the glass walk", None, None),
    ]
    meeting_id = "hs144-door-glass-meeting"
    pushed = _ok(hub.client.post("/api/sync/push", json={"meetings": [{
        "meta": {"id": meeting_id, "kind": "meeting", "last_modified": now.isoformat(), "deleted": False},
        "value": {
            "id": meeting_id, "started_at": (now - timedelta(minutes=30)).isoformat(),
            "ended_at": now.isoformat(), "title": "Door glass planning", "tags": [], "segments": [],
            "bookmarks": [], "capture_status": "finalized", "transcription_status": "active",
            "provenance": "native",
            "intel": {
                "timestamp": now.timestamp(), "topics": ["Door board"],
                "summary": "Production sync ingestion for the Door proof.",
                "action_items": [
                    {"id": item_id, "task": task, "owner": owner,
                     "due": due.isoformat() if due else None, "status": "pending",
                     "review_state": "accepted", "created_at": now.isoformat()}
                    for item_id, task, owner, due in rows
                ],
            },
        },
    }]}))
    assert pushed["received"]["meetings"] == 1
    _ok(hub.client.post("/api/desk/seed"))
    created = hub.client.post("/api/thoughts", json={
        "request_id": str(uuid.uuid4()), "raw_text": "Keep the Door board honest on glass.",
        "source": {"kind": "typed"},
        "initial_note": {"title": "Door active thought",
                         "body_markdown": "Keep the Door board honest on glass.", "tags": []},
    })
    assert created.status_code in (200, 201), created.text


def test_the_overdue_door_item_ranks_first_and_an_active_thought_is_no_member(hub: Hub) -> None:
    """replaces: tests/e2e/test_hs144_door_glass.py::test_hs144_door_populated_glass_action_refusal_and_shots
    (the hub half: the overdue item is the first Door row with its OVERDUE why;
    the active thought is no member)."""
    _seed_door_sync(hub)
    answer = _needs(hub)
    door_rows = [row for row in answer["items"] if str(row.get("ref") or "").startswith("hs144-")]
    # The hub ranks overdue, due today, unassigned, then the one that waits
    # (an owned item due next week waits on its owner; the hub's own count).
    assert [row["ref"] for row in door_rows] == ["hs144-overdue", "hs144-now", "hs144-unassigned", "hs144-waiting"]
    assert door_rows[0]["title"] == "Unblock the overdue Door proof"
    # "OVERDUE · <n>D": n counts from the hub's day, so only the word is pinned.
    assert str(door_rows[0]["why"]).startswith("OVERDUE"), door_rows[0]
    assert door_rows[3]["why"] == "WAITING ON CY" and door_rows[3]["waiting"] is True
    # Betterment D1: what Ada and Bea owe is theirs and never counts, late or
    # not; the item nobody owns is his to place.
    members = {m["ref"] for m in answer["members"]}
    assert "hs144-unassigned" in members
    assert not {"hs144-overdue", "hs144-now", "hs144-waiting"} & members
    assert [row["direction"] for row in door_rows] == ["theirs", "theirs", "mine", "theirs"]
    titles = [str(row.get("title") or "") for row in answer["items"]]
    assert not any("active thought" in title.lower() for title in titles), titles
    assert not any(str(m.get("ref") or "").startswith("thought") for m in answer["members"]), answer["members"]


# ── DUE-LABEL: the Door's two-day "now" window says the day, and whose ────


def test_the_now_window_says_the_day_and_theirs_waits(
    hub: Hub, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The Door's ``now`` column holds today, tomorrow and the day after
    (``FollowThroughService._lane``). On the pinned Tuesday (2026-10-20) the
    word says the day; Bea's items wait on Bea; the owner's own stay his and
    count on their day (Betterment D1)."""
    from tests.fixtures.daily_week import WIRE_DAY, pin_wire_day

    pin_wire_day(hub, monkeypatch)
    now = datetime(2026, 10, 20, 10, 0).astimezone()
    rows = [
        (f"due-{who}-{days}", f"{who} item due in {days} days", owner, WIRE_DAY + timedelta(days=days))
        for who, owner in (("mine", "me"), ("theirs", "Bea"))
        for days in (0, 1, 2)
    ]
    meeting_id = "due-label-meeting"
    pushed = _ok(hub.client.post("/api/sync/push", json={"meetings": [{
        "meta": {"id": meeting_id, "kind": "meeting", "last_modified": now.isoformat(), "deleted": False},
        "value": {
            "id": meeting_id, "started_at": (now - timedelta(minutes=30)).isoformat(),
            "ended_at": now.isoformat(), "title": "Due label planning", "tags": [], "segments": [],
            "bookmarks": [], "capture_status": "finalized", "transcription_status": "active",
            "provenance": "native",
            "intel": {
                "timestamp": now.timestamp(), "topics": [], "summary": "Due words.",
                "action_items": [
                    {"id": item_id, "task": task, "owner": owner, "due": due.isoformat(),
                     "status": "pending", "review_state": "accepted", "created_at": now.isoformat()}
                    for item_id, task, owner, due in rows
                ],
            },
        },
    }]}))
    assert pushed["received"]["meetings"] == 1
    board = _ok(hub.client.get("/api/door"))["board"]
    assert {str(card["id"]) for card in board["now"]} >= {row[0] for row in rows}, board["now"]

    answer = _needs(hub)
    got = {str(row.get("ref")): row for row in answer["items"] if str(row.get("ref") or "").startswith("due-")}
    members = {m["ref"] for m in answer["members"]}
    words = {"0": "DUE TODAY", "1": "DUE TOMORROW", "2": "DUE Thu"}
    for days, word in words.items():
        mine, theirs = got[f"due-mine-{days}"], got[f"due-theirs-{days}"]
        # The owner's own: the due word alone, his, never waiting.
        assert (mine["why"], mine["direction"], mine["waiting"]) == (word, "mine", False), mine
        # Bea's: listed under Waiting on Bea with the due word beside it.
        assert (theirs["why"], theirs["direction"], theirs["waiting"], theirs["counted"]) == (
            f"WAITING ON BEA · {word}", "theirs", True, False), theirs
        assert f"due-theirs-{days}" not in members
    assert answer["waitingCount"] >= 3
    # The one count rule: his item counts on its day, not before.
    assert got["due-mine-0"]["counted"] is True and "due-mine-0" in members
    assert got["due-mine-1"]["counted"] is False and got["due-mine-2"]["counted"] is False


# ── HS-201-01: an unreadable roster is its own row, never a clear desk ────


def test_an_unreadable_roster_is_the_unknown_blocker_and_the_answer_is_incomplete(
    hub: Hub, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """replaces: tests/e2e/test_hs201_one_thing_glass.py::TestOneThing::test_unknown_setup_is_its_own_row
    (the hub half; the face half is web/src/desk/chair/arrivalOneThing.test.tsx)."""
    import holdspeak.services.needs_you_membership as membership

    def roster_unreadable(db: Any, principal: Any) -> dict[str, Any]:
        raise RuntimeError("the roster read failed")

    monkeypatch.setattr(membership, "_read_assignments", roster_unreadable)
    answer = _needs(hub)
    assert answer["blockers"] == [
        {"key": "unknown", "label": "Could not read setup", "verb": "Try again", "direction": "setup"}]
    assert {"ref": "blocker:unknown", "kind": "blocker"} in answer["members"]
    assert "assignments" in answer["sourceErrors"]
    assert answer["complete"] is False


# ── honest faces: the Room names its meetings' unowned actions ───────────


def test_a_rooms_meeting_actions_are_its_open_rows_with_owner_unknown(hub: Hub) -> None:
    """replaces: tests/e2e/test_honest_faces_glass.py::test_room_shows_its_meeting_action_as_open (hub half)

    The Room never says "Clear here" while its meetings hold an action with
    no owner: its needs-you answer holds both actions, each OWNER · UNKNOWN,
    each with an `open` verb on its own action item; the count is the rows."""
    _seed_honest_faces(hub)
    needs = _ok(hub.client.get("/api/projects/p-ledger/room"))["needsYou"]
    assert needs["state"] == "ok", needs
    assert needs["count"] == 2 == len(needs["items"]), needs
    rows = {row["title"]: row for row in needs["items"]}
    assert set(rows) == {"Write the rollback runbook", "Pilot OTel in billing"}, rows
    for row in rows.values():
        assert (row["kind"], row["why"], row["verb"], row["owner"]) == (
            "action_item", "OWNER · UNKNOWN", "open", None), row
    assert rows["Write the rollback runbook"]["action_item_id"] == "m-standup-a1"
    assert rows["Pilot OTel in billing"]["action_item_id"] == "m-arch-a1"


# ── Betterment daily D0: every row knows its direction, its person and its date ──


def test_every_row_knows_its_direction_its_person_and_its_date(hub: Hub) -> None:
    """On the recon's week after the nine keeps: mine, theirs and decide come
    apart, each row names its Person, and every said due is a date."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.fixtures.daily_week import seed

    people = seed(hub)
    names = {rid: name for name, rid in people.items()}
    answer = _needs(hub)
    rows = {
        row["title"]: (row["direction"], names.get(row["person_id"], row["person_id"]), row.get("dueAt"))
        for row in answer["items"]
    }
    assert rows == {
        "Draft the rollback runbook": ("theirs", "Mira", "2026-10-20"),
        "Profile the reconciliation job": ("theirs", "Theo", "2026-10-23"),
        "Write up alert rule changes": ("theirs", "Theo", "2026-10-22"),
        "Confirm the vendor freeze dates": ("theirs", "Jun", "2026-10-16"),
        "Load-test the dedupe key path": ("theirs", "Jun", "2026-10-23"),
        "Email Dana about the cutover window": ("mine", "", "2026-10-19"),
        "Review design doc on settlement retries": ("mine", "Theo", "2026-10-19"),
        "Do it": ("decide", "", None),
        "Talk about the staff path in our next one-on-one": ("decide", "", None),
    }
    assert {b["direction"] for b in answer["blockers"]} <= {"setup"}
    # The said words stay beside the date.
    with hub.db._connection() as conn:
        said = dict(conn.execute("SELECT task, due_said FROM action_items").fetchall())
    assert said["Profile the reconciliation job"] == "Friday next week"
    assert said["Confirm the vendor freeze dates"] == "this week"


def test_a_row_stored_with_words_still_gets_a_lane_from_its_meeting_day(hub: Hub) -> None:
    """A row written before D0 (its due still "Monday") is read against its
    meeting's day, so it is due soon instead of waiting forever."""
    start = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0) - timedelta(days=1)
    weekday = (start + timedelta(days=1)).strftime("%A")  # today's name, said yesterday
    with hub.db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, title, intel_status, capture_status, provenance) "
            "VALUES ('m-legacy', ?, 'Legacy', 'complete', 'finalized', 'desktop')", (start.isoformat(),))
        conn.execute(
            "INSERT INTO action_items (id, meeting_id, task, owner, due, status, review_state, created_at) "
            "VALUES ('ai-legacy', 'm-legacy', 'Send the legacy note', 'Me', ?, 'open', 'accepted', ?)",
            (weekday, start.isoformat()))
        conn.commit()
    row = next(r for r in _needs(hub)["items"] if r["title"] == "Send the legacy note")
    assert row["dueAt"] == (start + timedelta(days=1)).date().isoformat(), row
    assert row["why"] == "DUE TODAY" and row["direction"] == "mine", row


# ── Betterment daily D1: one number, true labels ─────────────────────────────


def test_the_one_number_is_mine_due_today_and_to_decide(hub: Hub) -> None:
    """The recon's week with today as its Monday, after the nine keeps, with
    the LAN engine set: the bell, the Dock and the Project icon read 4. Mine
    due today (2) + to decide (2); theirs (5, one of them overdue) never counts."""
    from datetime import date

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.fixtures.daily_week import seed

    seeded = seed(hub, monday=date.today(), engine=True)
    answer = _needs(hub)
    counted = sorted(row["title"] for row in answer["items"] if row["counted"])
    assert counted == [
        "Do it", "Email Dana about the cutover window",
        "Review design doc on settlement retries",
        "Talk about the staff path in our next one-on-one",
    ]
    assert answer["count"] == len(answer["members"]) == 4
    assert answer["blockers"] == []
    # The Project icon reads the same rule filtered to the Project; the Room's
    # own count (9: it counts theirs) is not the badge.
    assert answer["projectCounts"] == {seeded["project"]: 4}
    overdue = next(row for row in answer["items"] if row["title"] == "Confirm the vendor freeze dates")
    assert overdue["direction"] == "theirs" and overdue["why"].startswith("OVERDUE") and not overdue["counted"]
    # The faces' half (web/src/desk/__tests__/bell.app.test.tsx) renders this answer.
    from tests.unit.test_desk_speak import _record

    projects = _ok(hub.client.get("/api/projects"))
    board = _ok(hub.client.get("/api/follow-through/board"))
    # The Project id is minted per run; the stored answer names it one way.
    wire = json.loads(json.dumps({"needsYou": answer, "projects": projects, "followThrough": board})
                      .replace(seeded["project"], "proj-daily-week"))
    _record("needs-you", wire,
            Path(hub.db.db_path).parent,
            "tests/unit/test_desk_needs_you.py::test_the_one_number_is_mine_due_today_and_to_decide",
            folder=Path(__file__).resolve().parents[2] / "web" / "src" / "desk" / "__tests__"
            / "fixtures" / "daily-week")


def test_a_promise_not_kept_yet_does_not_count(hub: Hub) -> None:
    """Before the keeps: the two decisions count; no proposed action does."""
    from datetime import date

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.fixtures.daily_week import seed

    seed(hub, monday=date.today(), engine=True, keep=False)
    answer = _needs(hub)
    assert sorted(row["title"] for row in answer["items"] if row["counted"]) == [
        "Adopt idempotent retries with a dedupe key", "Do it",
        "Freeze ledger writes during the cutover",
        "Talk about the staff path in our next one-on-one",
    ]
    assert answer["count"] == 4


def test_follow_through_due_is_a_date_or_the_whole_words(hub: Hub) -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.fixtures.daily_week import seed

    seed(hub)
    with hub.db._connection() as conn:
        conn.execute("UPDATE action_items SET due = 'after the launch' WHERE task = 'Write up alert rule changes'")
        conn.commit()
    board = _ok(hub.client.get("/api/follow-through/board"))
    dues = {card["text"]: card["due"] for lane in ("now", "waiting", "unassigned", "overdue") for card in board[lane]}
    assert dues["Profile the reconciliation job"] == "2026-10-23"
    assert dues["Write up alert rule changes"] == "after the launch"


# ── Betterment daily D2: the filters of the one list ──────────────────────────


def _titles(answer: dict[str, Any]) -> list[str]:
    return sorted(row["title"] for row in answer["items"])


def test_the_filters_narrow_the_list_and_never_the_number(hub: Hub) -> None:
    """On the recon's week (today its Monday, the nine keeps): They owe me +
    Theo is exactly Theo's two rows; Mine is his two; the count stays 4."""
    from datetime import date

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.fixtures.daily_week import seed

    seeded = seed(hub, monday=date.today(), engine=True)

    def read(query: str) -> dict[str, Any]:
        return _ok(hub.client.get(f"/api/desk/needs-you?{query}"))

    theirs_theo = read("direction=theirs&person=Theo")
    assert _titles(theirs_theo) == ["Profile the reconciliation job", "Write up alert rule changes"]
    assert theirs_theo["count"] == 4 and theirs_theo["shown"] == 2
    assert theirs_theo["filter"] == {"direction": "theirs", "person": "Theo"}
    assert {row["person_name"] for row in theirs_theo["items"]} == {"Theo Park"}
    assert _titles(read("direction=mine")) == [
        "Email Dana about the cutover window", "Review design doc on settlement retries"]
    # Mine + Theo: what I owe Theo. The full name and the id find him too.
    assert _titles(read("direction=mine&person=theo%20park")) == ["Review design doc on settlement retries"]
    assert _titles(read(f"person={seeded['Theo']}")) == [
        "Profile the reconciliation job", "Review design doc on settlement retries",
        "Write up alert rule changes"]
    assert _titles(read("direction=decide")) == ["Do it", "Talk about the staff path in our next one-on-one"]
    # The Project by name or id: every row of the week is in it.
    assert len(read("project=Payments%20ledger%20cutover")["items"]) == 9
    assert len(read(f"project={seeded['project']}")["items"]) == 9
    # This week: due by Sunday, the late row too; the decisions have no date.
    week = _titles(read("week=1"))
    assert "Confirm the vendor freeze dates" in week and "Do it" not in week
    assert hub.client.get("/api/desk/needs-you?direction=nobody").status_code == 400
    # No filter: the answer is the whole list, with no filter keys.
    whole = _needs(hub)
    assert len(whole["items"]) == 9 and "filter" not in whole


def test_desk_needs_you_over_mcp_takes_the_same_filters(hub: Hub) -> None:
    from datetime import date

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.fixtures.daily_week import seed

    seed(hub, monday=date.today(), engine=True)
    is_error, answer = hub.mcp("desk.needs_you", {"direction": "theirs", "person": "Theo"})
    assert not is_error, answer
    assert _titles(answer) == ["Profile the reconciliation job", "Write up alert rule changes"]
    assert answer["count"] == 4
    is_error, answer = hub.mcp("desk.needs_you", {"direction": "mine", "week": True})
    assert not is_error and _titles(answer) == [
        "Email Dana about the cutover window", "Review design doc on settlement retries"]


def test_an_old_rows_said_due_becomes_a_date_on_open(hub: Hub) -> None:
    """The D0 follow-up: a row written before D0 keeps "Monday" as its due
    and no due_said. The next open resolves it once against its meeting's
    day; words that name no day stay words. Every reader then sees a date."""
    from holdspeak.db.reconcile import _resolve_said_dues

    with hub.db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, title, intel_status, capture_status, provenance) "
            "VALUES ('m-old', '2026-10-15T18:00:00', 'Old', 'complete', 'finalized', 'desktop')")
        for action_id, due in (("ai-old", "Friday next week"), ("ai-words", "after the launch"),
                               ("ai-iso", "2026-10-20")):
            conn.execute(
                "INSERT INTO action_items (id, meeting_id, task, owner, due, status, review_state, created_at) "
                "VALUES (?, 'm-old', ?, 'Theo', ?, 'open', 'accepted', '2026-10-15T18:30:00')",
                (action_id, action_id, due))
        conn.commit()
        assert _resolve_said_dues(conn) == 2
        rows = {r[0]: (r[1], r[2]) for r in conn.execute("SELECT id, due, due_said FROM action_items")}
        assert _resolve_said_dues(conn) == 0  # once
    assert rows["ai-old"] == ("2026-10-23", "Friday next week")
    assert rows["ai-words"] == ("after the launch", "after the launch")
    assert rows["ai-iso"] == ("2026-10-20", None)


# ── Betterment daily D3: promises from a meeting are kept on arrival ─────────


def test_a_finished_summary_keeps_its_promises_and_decisions_wait(hub: Hub) -> None:
    """Owner decision 24: on the recon's week, through the hub's own
    post-summary hook, the seven promises with an owner are kept with no
    Confirm press, NEW under their meeting; the four decisions wait for
    Decide. Nothing kept is a proposal row any more."""
    from datetime import date

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.fixtures.daily_week import WEEK, seed

    seeded = seed(hub, monday=date.today(), engine=True, arrival=True)
    answer = _needs(hub)
    rows = {row["title"]: row for row in answer["items"]}
    # The faces' half (web/src/desk/__tests__/needs-you.app.test.tsx) renders this answer.
    from tests.unit.test_desk_speak import _record

    wire = json.loads(json.dumps({"needsYou": answer}).replace(seeded["project"], "proj-daily-week"))
    _record("needs-you-arrival", wire, Path(hub.db.db_path).parent,
            "tests/unit/test_desk_needs_you.py::test_a_finished_summary_keeps_its_promises_and_decisions_wait",
            folder=Path(__file__).resolve().parents[2] / "web" / "src" / "desk" / "__tests__"
            / "fixtures" / "daily-week")
    promises = {a["task"] for m in WEEK["meetings"] for a in m["actions"]}
    decisions = {d["decision"] for m in WEEK["meetings"] for d in m["decisions"]}
    assert len(promises) == 7 and len(decisions) == 4
    for title in promises:
        row = rows[title]
        assert not row.get("proposalId"), row
        assert row["source"] == "commitment" and row["actionItemId"], row
        assert row["arrival"]["meetingTitle"], row
    for title in decisions:
        assert rows[title]["direction"] == "decide" and rows[title]["proposalKind"] == "decision"
    # One group per meeting; its decisions join it.
    titles = {m["id"]: m["title"] for m in WEEK["meetings"]}
    for meeting in WEEK["meetings"]:
        group = sorted(t for t, r in rows.items() if (r.get("arrival") or {}).get("meetingId") == meeting["id"])
        assert group == sorted([a["task"] for a in meeting["actions"]] + [d["decision"] for d in meeting["decisions"]])
        assert all(rows[t]["arrival"]["meetingTitle"] == titles[meeting["id"]] for t in group)
    # The kept rows say who kept them.
    with hub.db._connection() as conn:
        kept_by = {r[0] for r in conn.execute(
            "SELECT DISTINCT principal_identity FROM service_events WHERE event_type = 'proposal.confirmed'")}
    assert kept_by == {"kept-on-arrival"}, kept_by
    # The number: mine due today (2) + to decide (4); theirs never counts.
    assert answer["count"] == 6, sorted(r["title"] for r in answer["items"] if r["counted"])

    # Seen: the group goes; the rows stay.
    _ok(hub.client.post("/api/desk/needs-you/seen", json={"meeting_ids": [m["id"] for m in WEEK["meetings"]]}))
    after = _needs(hub)
    assert not any(row.get("arrival") for row in after["items"])
    assert {row["title"] for row in after["items"]} == set(rows)


def test_drop_and_undo_on_a_kept_promise_and_a_decision(hub: Hub) -> None:
    """Drop on a kept promise removes it; Undo (reopen) brings it back. Drop on
    "Do it" (a decision) removes it; Undo (restore) brings it back to Decide."""
    from datetime import date

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.fixtures.daily_week import seed

    seed(hub, monday=date.today(), engine=True, arrival=True)
    rows = {row["title"]: row for row in _needs(hub)["items"]}
    action = rows["Write up alert rule changes"]["actionItemId"]
    _ok(hub.client.post("/api/follow-through/complete", json={"card_id": action, "verb": "dismiss", "payload": {}}))
    assert "Write up alert rule changes" not in {r["title"] for r in _needs(hub)["items"]}
    _ok(hub.client.post("/api/follow-through/complete", json={"card_id": action, "verb": "reopen", "payload": {}}))
    assert "Write up alert rule changes" in {r["title"] for r in _needs(hub)["items"]}

    proposal = rows["Do it"]["proposalId"]
    _ok(hub.client.post(f"/api/proposals/{proposal}/dismiss"))
    assert "Do it" not in {r["title"] for r in _needs(hub)["items"]}
    restored = _ok(hub.client.post(f"/api/proposals/{proposal}/restore"))
    assert restored["state"] == "proposed"
    back = next(r for r in _needs(hub)["items"] if r["title"] == "Do it")
    assert back["direction"] == "decide" and back["counted"]
    # A second Undo replays.
    assert _ok(hub.client.post(f"/api/proposals/{proposal}/restore"))["replayed"] is True


def test_a_promise_with_no_owner_waits_and_asks_whose(hub: Hub) -> None:
    """A promise with no owner is not kept; its row offers the meeting's
    speakers. Confirm with one of them keeps it with that owner."""
    from holdspeak.intel.models import ActionItem
    from holdspeak.intel_queue import _on_intel_complete
    from holdspeak.kernel.summary_items_projection import write_summary_items
    from holdspeak.meeting_session.models import IntelSnapshot, MeetingState, TranscriptSegment

    start = datetime.now().replace(microsecond=0) - timedelta(hours=1)
    items = [ActionItem(task="Book the dry run", owner=None), ActionItem(task="Send the notes", owner="Me")]
    hub.db.meetings.save_meeting(MeetingState(
        id="m-whose", started_at=start, ended_at=start + timedelta(minutes=20), title="Dry run sync",
        segments=[TranscriptSegment(text="Someone books the dry run.", speaker="Mira", start_time=0, end_time=5),
                  TranscriptSegment(text="I send the notes.", speaker="Me", start_time=5, end_time=9)],
        intel=IntelSnapshot(timestamp=9.0, summary="Dry run.", action_items=items), intel_status="complete"))
    with hub.db._connection() as conn:
        write_summary_items(conn, {"job_id": "job-whose", "decisions": []}, "m-whose",
                            [{"task": i.task, "owner": i.owner, "due": None, "id": i.id} for i in items])
    _on_intel_complete(hub.db, "m-whose")
    rows = {row["title"]: row for row in _needs(hub)["items"]}
    assert rows["Book the dry run"]["proposalId"] and rows["Book the dry run"]["whose"] == ["Mira", "Me"]
    assert not rows["Send the notes"].get("proposalId")  # kept: it had an owner
    pid = rows["Book the dry run"]["proposalId"]
    kept = _ok(hub.client.post(f"/api/proposals/{pid}/confirm", json={"owner": "Mira"}))
    assert kept["action_item_id"]
    row = next(r for r in _needs(hub)["items"] if r["title"] == "Book the dry run")
    assert row["owner"] == "Mira" and row["direction"] == "theirs"


def test_a_plugins_promise_is_kept_only_when_it_stands_for_a_said_thing(hub: Hub) -> None:
    """C4's note: plugin promises reach Needs you. One that stands for the
    summary's own row, or whose words are in the transcript, is kept; an
    unsupported one waits for Confirm (no flood)."""
    from holdspeak.db.proposals import Proposal
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    def proposal(**kw: Any) -> Proposal:
        base = dict(id="p", meeting_id="m", project_id=None, kind="action", text="t", owner_hint="Mira",
                    due_hint=None, source_artifact_id=None, source_plugin="action_owner_enforcer",
                    segment_timestamp=None, speaker_label=None, model_host=None, fingerprint="f",
                    state="proposed", original_text=None, decision_record_id=None, commitment_id=None,
                    created_at="2026-10-18T00:00:00Z", decided_at=None)
        base.update(kw)
        return Proposal(**base)

    keeps = ProposalBridgeService.arrival_keeps
    assert keeps(proposal(source_plugin="meeting_summary"))
    assert keeps(proposal(action_item_id="ai-1"))
    assert keeps(proposal(support="supported"))
    assert not keeps(proposal())  # a plugin's unsupported sentence
    assert not keeps(proposal(owner_hint=None, source_plugin="meeting_summary"))  # Whose?
    assert not keeps(proposal(kind="decision", source_plugin="meeting_summary"))  # Decide


def test_a_re_summary_never_brings_back_a_dropped_promise(hub: Hub) -> None:
    """He drops a kept promise; the same meeting is summarised again (a new
    transcript revision, new rows). The dropped promise is not kept again and
    is not shown again; the promise he kept is kept again."""
    from holdspeak.intel.models import ActionItem
    from holdspeak.intel_queue import _on_intel_complete
    from holdspeak.kernel.summary_items_projection import write_summary_items
    from holdspeak.meeting_session.models import IntelSnapshot, MeetingState, TranscriptSegment

    start = datetime.now().replace(microsecond=0) - timedelta(hours=1)

    def summarise(job: str, extra: list[TranscriptSegment], alert: str = "Write up the alert rule changes") -> None:
        items = [ActionItem(task=alert, owner="Theo"),
                 ActionItem(task="Send the notes", owner="Me")]
        hub.db.meetings.save_meeting(MeetingState(
            id="m-resum", started_at=start, ended_at=start + timedelta(minutes=20), title="Alert sync",
            segments=[TranscriptSegment(text="Theo writes up the alert rules.", speaker="Theo", start_time=0, end_time=5),
                      *extra],
            intel=IntelSnapshot(timestamp=9.0, summary="Alerts.", action_items=items), intel_status="complete"))
        with hub.db._connection() as conn:
            write_summary_items(conn, {"job_id": job, "decisions": []}, "m-resum",
                                [{"task": i.task, "owner": i.owner, "due": None, "id": i.id} for i in items])
        _on_intel_complete(hub.db, "m-resum")

    summarise("job-1", [])
    assert "Write up the alert rule changes" in [r["title"] for r in _needs(hub)["items"]]
    with hub.db._connection() as conn:
        dropped = conn.execute(
            "SELECT id FROM action_items WHERE meeting_id='m-resum' AND task LIKE 'Write up%' "
            "AND status = 'open'").fetchone()[0]
    _ok(hub.client.post("/api/follow-through/complete", json={"card_id": dropped, "verb": "dismiss", "payload": {}}))

    # The engine words it a little differently this time (the exact text is
    # already refused by the proposal fingerprint; the normalized title is not).
    summarise("job-2", [TranscriptSegment(text="And I send the notes.", speaker="Me", start_time=5, end_time=9)],
              alert="Write up alert rule changes")
    titles = [r["title"] for r in _needs(hub)["items"]]
    assert not any(t.startswith("Write up") for t in titles), titles
    assert "Send the notes" in titles
    with hub.db._connection() as conn:
        live = conn.execute(
            "SELECT COUNT(*) FROM action_items WHERE meeting_id='m-resum' AND task LIKE 'Write up%' "
            "AND status NOT IN ('dismissed', 'done')").fetchone()[0]
        states = [r[0] for r in conn.execute(
            "SELECT state FROM follow_through_proposals WHERE meeting_id='m-resum' AND text LIKE 'Write up%'")]
    assert live == 0 and "proposed" not in states, (live, states)


# ── Send S3: one real channel row, one Needs-you member ────────────────


def _send_rows(answer: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in answer.get("items", []) if row.get("kind") == "send"]


def test_an_agent_prepare_is_owner_needs_membership_and_real_folder_send(
    hub: Hub, tmp_path: Path,
) -> None:
    """S3's producer and owner press share the channel row and its count.

    The agent reaches ``channel.prepare`` through its issued project
    credential.  The owner then reads the same row, presses Send through the
    owner route, and the file channel writes the frozen payload to the saved
    folder.  The pre-send answer is recorded as the whole producer response
    for the Needs-you app test; it is never typed into a fixture.
    """
    from _philo10_send import destination, room
    from test_philo9_steward_admission import _agent, _tool
    from tests.unit.test_desk_speak import _record

    _pid, update = room(hub, name="S3 private delivery")
    folder = tmp_path / "private-team-folder"
    dest = destination(hub, folder, name="Private team folder")
    agent = _agent(hub, palette="ALL", identity="claude-code")
    is_error, prepared = _tool(agent, "channel.prepare", {
        "document_ref": f"project_update:{update}", "destination_id": dest,
    })
    assert is_error is False, prepared
    send = prepared["send"]
    assert send["state"] == "prepared"
    assert send["prepared_by"] == {"kind": "agent", "identity": "claude-code"}
    assert list(folder.iterdir()) == []

    owner_answer = _needs(hub)
    rows = _send_rows(owner_answer)
    assert len(rows) == 1, rows
    row = rows[0]
    assert row["id"] == f"send:{send['id']}", row
    assert (row["documentLabel"], row["documentTitle"], row["destinationName"], row["preparedBy"]) == (
        "REV 1", send["document_json"]["title"], "Private team folder", "Claude Code",
    ), row
    assert owner_answer["count"] == len(owner_answer["members"]) and row["ref"] in {
        member["ref"] for member in owner_answer["members"]
    }
    assert any(c["kind"] == "send" and c["state"] == "available" for c in owner_answer["coverage"])

    # The source fixture is the actual complete owner response, including all
    # ordinary Needs-you rows and the frozen channel row.
    recorded_answer = json.loads(json.dumps({"needsYou": owner_answer}).replace(_pid, "proj-send-needs"))
    _record("needs-send", recorded_answer, Path(hub.db.db_path).parent,
            "tests/unit/test_desk_needs_you.py::test_an_agent_prepare_is_owner_needs_membership_and_real_folder_send",
            folder=Path(__file__).resolve().parents[2] / "web" / "src" / "desk" / "__tests__"
            / "fixtures" / "send-needs")

    # The same MCP tool is safe for an admitted agent: it has the coverage
    # source, but no private send row, title, destination, or frozen payload.
    is_error, agent_answer = _tool(agent, "desk.needs_you", {})
    assert is_error is False, agent_answer
    assert not _send_rows(agent_answer), agent_answer
    assert agent_answer.get("coverage") and not any(
        "S3 private delivery" in json.dumps(item) for item in agent_answer.get("items", [])
    )

    sent_response = _ok(hub.client.post("/api/channels/send", json={"send_id": send["id"],
                                                                      "command_id": "s3-owner-send"}))
    assert sent_response["outcome"] == "sent", sent_response
    sent = sent_response["send"]
    path = Path(sent["proof"]["path"])
    assert path.parent.resolve() == folder.resolve()
    assert path.read_bytes() == bytes(hub.db.channel_sends.get(send["id"])["payload"])
    assert len(list(folder.iterdir())) == 1
    after = _needs(hub)
    assert not _send_rows(after), after
    assert hub.db.channel_sends.get(send["id"])["state"] == "sent"
    with hub.db._connection() as conn:
        receipt = conn.execute(
            "SELECT state, result_ref FROM kernel_receipts WHERE operation_id = "
            "(SELECT send_operation_id FROM channel_sends WHERE id=?)", (send["id"],)
        ).fetchone()
    assert receipt and tuple(receipt) == ("succeeded", f"channel_send:{send['id']}")


def test_send_needs_membership_leaves_once_for_discard_failed_and_unknown_replay(
    hub: Hub, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every terminal channel state has one durable Needs-you consequence."""
    from _philo10_send import destination, room
    from holdspeak.services.channel_contract import FileChannel, Outcome
    from tests.unit.test_desk_speak import _record

    _pid, update = room(hub, name="S3 state transitions")
    folder = tmp_path / "state-transitions"
    dest = destination(hub, folder)
    ref = f"project_update:{update}"

    # Discard is an owner decision, and its row leaves after one refresh.
    discarded = _ok(hub.client.post("/api/channels/sends", json={"document_ref": ref,
                                                                   "destination_id": dest}))
    discarded_id = discarded["send"]["id"]
    assert len(_send_rows(_needs(hub))) == 1
    _ok(hub.client.post(f"/api/channels/sends/{discarded_id}/discard", json={"command_id": "s3-discard"}))
    assert not _send_rows(_needs(hub))
    assert hub.db.channel_sends.get(discarded_id)["state"] == "discarded"

    # A provider leaf may answer FAILED.  Routing, persistence and the
    # aggregate remain the real hub paths.
    real_dispatch = FileChannel.dispatch
    monkeypatch.setattr(FileChannel, "dispatch", lambda *_args, **_kwargs: Outcome("failed", "permission_denied"))
    failed = _ok(hub.client.post("/api/channels/sends", json={"document_ref": ref,
                                                                "destination_id": dest}))
    failed_id = failed["send"]["id"]
    failed_press = _ok(hub.client.post("/api/channels/send", json={"send_id": failed_id,
                                                                      "command_id": "s3-failed"}))
    assert failed_press["outcome"] == "failed"
    failed_rows = _send_rows(_needs(hub))
    assert len(failed_rows) == 1 and failed_rows[0]["sendId"] == failed_id
    assert failed_rows[0]["why"] == "NOT SENT"

    # A fresh prepare can share the failed row's second. Its dispatch_seq is
    # still NULL, so membership must use the durable channel row order.
    prepared_retry = _ok(hub.client.post("/api/channels/sends", json={"document_ref": ref,
                                                                         "destination_id": dest}))
    prepared_retry_id = prepared_retry["send"]["id"]
    prepared_rows = _send_rows(_needs(hub))
    assert len(prepared_rows) == 1 and prepared_rows[0]["sendId"] == prepared_retry_id
    _ok(hub.client.post(f"/api/channels/sends/{prepared_retry_id}/discard", json={"command_id": "s3-discard-retry"}))

    # UNKNOWN is a settled no-answer. Replaying the same command id returns
    # the existing operation and never calls the provider a second time.
    calls = 0

    def unknown_dispatch(*_args: Any, **_kwargs: Any) -> Outcome:
        nonlocal calls
        calls += 1
        return Outcome("unknown", "timeout")

    monkeypatch.setattr(FileChannel, "dispatch", unknown_dispatch)
    unknown = _ok(hub.client.post("/api/channels/sends", json={"document_ref": ref,
                                                                 "destination_id": dest}))
    unknown_id = unknown["send"]["id"]
    first = _ok(hub.client.post("/api/channels/send", json={"send_id": unknown_id,
                                                              "command_id": "s3-unknown"}))
    second = _ok(hub.client.post("/api/channels/send", json={"send_id": unknown_id,
                                                               "command_id": "s3-unknown"}))
    assert first["outcome"] == second["outcome"] == "unknown"
    assert first["operation_id"] == second["operation_id"]
    assert calls == 1
    unknown_rows = _send_rows(_needs(hub))
    assert len(unknown_rows) == 1 and unknown_rows[0]["sendId"] == unknown_id
    assert unknown_rows[0]["why"] == "NO ANSWER"
    assert unknown_rows[0]["send"]["retry_command"] == {
        "command_id": "s3-unknown", "send_id": unknown_id,
    }
    assert list(folder.iterdir()) == []
    unknown_answer = _needs(hub)
    _record(
        "needs-send-unknown",
        json.loads(json.dumps({"needsYou": unknown_answer}).replace(_pid, "proj-send-needs-unknown")),
        Path(hub.db.db_path).parent,
        "tests/unit/test_desk_needs_you.py::test_send_needs_membership_leaves_once_for_discard_failed_and_unknown_replay",
        folder=Path(__file__).resolve().parents[2] / "web" / "src" / "desk" / "__tests__"
        / "fixtures" / "send-needs",
    )
    monkeypatch.setattr(FileChannel, "dispatch", real_dispatch)
