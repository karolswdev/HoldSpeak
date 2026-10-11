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
            "VALUES (?, ?, ?, 'Priya Shah', 'Friday', 'pending', 'pending', ?)",
            (action_id, UNFILED, ACTION, now.isoformat()),
        )
        conn.execute(
            "INSERT INTO artifacts (id, meeting_id, origin, artifact_type, title, structured_json, "
            " confidence, status, plugin_id, plugin_version) "
            "VALUES (?, ?, 'meeting', 'summary_items', 'Decisions and action items', ?, 1.0, "
            " 'draft', 'meeting_summary', '1')",
            (f"summary-items-{UNFILED}", UNFILED, json.dumps({
                "decisions": [{"decision": DECISION, "rationale": None}],
                "action_items": [{"task": ACTION, "owner": "Priya Shah", "due": "Friday",
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
    members = {m["ref"] for m in answer["members"]}
    assert all((r.get("ref") if r.get("ref") is not None else r["id"]) in members for r in rows.values())


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
        members = {m["ref"] for m in after["members"]}
        assert (row.get("ref") if row.get("ref") is not None else row["id"]) in members, (row, members)

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
