"""The Room app, AS RENDERED: what only a real browser proves of the Room.

Owner, 2026-10-12 (push 2 of the test diet): a browser test only for drag,
focus, keys, touch, hover or an exact geometry relation.

PHILO-13-18 (C8) -- the library DeskEditor wraps long lines, at every width
(an exact geometry relation: each line's last words inside the editor box).

Astra's B5 check (#739) found the Room's Update draft cut its summary, decision
and action lines at the right edge at 393 (assets/story-10-week/week-393/
after.png): the owners and due dates were not on the glass. Through the real
hub on an isolated HOME, a project's Update draft whose lines are the B5 week
(tests/fixtures/philo13_b5_week_summary_reply.json: the summary, the decision,
two actions with owner and due date) is opened at 393 touch and 1440 mouse:

  W1 the editor reader (glass_infra._rendered_text_faults, on_glass) finds no
     clipped text and no overlap in the editor;
  W2 nothing in the editor scrolls sideways;
  W3 every line's last words (the owner and the due date) are inside the
     editor's visible box.

Shots go to assets/story-18-shots/ (``.tmp/evidence-shots/`` unless
HOLDSPEAK_EVIDENCE_WRITE=1).

Also here (lane e2e-high-1):

The Project Room in a real browser: only what needs one.

Kept by the test diet (push 2, 2026-10-12), one file for the Room app. Each
check needs a real browser:

* the review loop decided from the keyboard (HS-160-07, keys and focus);
* the wings stay inside the head and the window under a 70-character
  Project name (HS-168-05, an exact geometry relation, 1440 and 393);
* closing People puts focus back on the Room's People verb (HS-200-14,
  return-to-task; focus), on the full ready -> Resolve -> People -> locked walk;
* the unfinished asks (HS-200-41): the `@container surface (max-width:
  420px)` rule, rendered (computed grid areas at 393); the rows rove from
  the keyboard on a list that mounted empty; five rows leave the Room
  standing (geometry).

Was tests/e2e/test_hs160_delta_glass.py, test_hs168_window_wings_glass.py,
test_hs200_people_preparation_glass.py and test_hs200_task_resume_glass.py
(parked whole). Their other legs: the frozen review, its repeat and its
degraded coverage are tests/unit/test_frozen_review.py; the People section's
words are web/src/features/project-room/__tests__/roomPeople200.test.tsx and
the hub's tests/unit/test_people_*.py; the unfinished rows, the refusal
words, the restart, the claim and the one Tab stop are
web/src/desk/surface/__tests__/taskResume.test.tsx,
web/src/features/project-room/__tests__/room200TaskResume.test.tsx and
tests/unit/test_phase200_task_resume.py; fit at 393 is the desk sweep's.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _rendered_text_faults, _settle
from tests._evidence import evidence_dir
import os
import uuid
from datetime import timedelta
from .glass_infra import _assert_clean
from .glass_infra import people_key_file

pytest.importorskip("playwright.sync_api", reason="the Room glass needs Playwright")

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(300, method="thread")]

TOKEN = "room-glass"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-18-shots")
SIZES = {1440: 900, 393: 852}
# The B5 week, as the drafted update writes it (one line per fact).
LINES = [
    "Summary: The ledger cutover is ready for the controlled migration, and the rollback path is tested end to end.",
    "Decision: Use the controlled migration window because the rollback path is tested (Ledger cutover sync).",
    "Action: Confirm the migration window with the payments team. Owner: Avery. Due: 2026-10-06.",
    "Action: Send the rollback checklist to every service owner on the ledger. Owner: Morgan. Due: 2026-10-07.",
]
ENDS = ["end to end.", "cutover sync).", "Due: 2026-10-06.", "Due: 2026-10-07."]


def _seed_draft(project_id: str) -> None:
    from holdspeak.db import get_database

    body = "## This week\n\n" + "\n\n".join(LINES) + "\n"
    now = datetime.now().isoformat()
    with get_database()._connection() as conn:
        conn.execute(
            """INSERT INTO project_updates
               (id, project_id, project_revision, review_id, lifecycle, draft_revision,
                body_md, claims_json, source_manifest_json, generator, created_at, updated_at)
               VALUES (?, ?, 0, NULL, 'draft', 1, ?, '[]', '{}', 'deterministic', ?, ?)""",
            ("pupd_p1318_wrap", project_id, body, now, now),
        )


_ENDS_JS = """(ends) => {
  const ed = document.querySelector('[data-testid="update-body-editor"] .cm-editor');
  const box = ed.getBoundingClientRect();
  const out = {box: [box.left, box.right].map(Math.round), missing: [], sideways: []};
  for (const end of ends) {
    const line = [...ed.querySelectorAll('.cm-line')].find((l) => l.textContent.includes(end));
    if (!line) { out.missing.push(end + ' (no line)'); continue; }
    const walker = document.createTreeWalker(line, NodeFilter.SHOW_TEXT);
    let hit = null;
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      const i = n.textContent.indexOf(end.slice(-6));
      if (i >= 0) { const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + 6); hit = r.getBoundingClientRect(); }
    }
    if (!hit || hit.right > box.right + 1 || hit.left < box.left - 1)
      out.missing.push(end + ' at ' + (hit ? Math.round(hit.right) : 'none'));
  }
  for (const e of [ed, ...ed.querySelectorAll('*')])
    if (e.scrollWidth > e.clientWidth + 1 && ['auto', 'scroll'].includes(getComputedStyle(e).overflowX))
      out.sideways.push((e.className || e.tagName).toString().slice(0, 40) + ' ' + e.scrollWidth + '>' + e.clientWidth);
  return out;
}"""


@pytest.mark.parametrize("width", list(SIZES))
def test_the_update_draft_wraps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    """replaces: tests/e2e/test_philo13_18_editor_wrap_glass.py::test_the_update_draft_wraps"""
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                      has_touch=width < 720, is_mobile=False)
            page = ctx.new_page()
            page.set_default_timeout(20_000)
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            pid = _api(page, "POST", "/api/projects", {"name": "Payments ledger cutover",
                       "description": "B5 week", "command_id": "p1318-wrap"}, token=TOKEN)["project"]["id"]
            _seed_draft(pid)
            page.evaluate("""([k, s]) => sessionStorage.setItem('hs.desk.staged-surface-open',
                JSON.stringify({key: k, scope: s}))""", ["open-project-memory", f"project:{pid}"])
            page.reload(wait_until="load")
            _normal_chair(page)

            def press(loc: Any) -> None:
                loc.scroll_into_view_if_needed()
                if width < 720:
                    b = loc.bounding_box()
                    page.touchscreen.tap(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
                else:
                    loc.click()

            press(page.locator('[data-testid="updates-verb"]').first)
            page.locator('[data-testid="update-list-item"]').first.wait_for()
            press(page.locator('[data-testid="update-list-item"]').first)
            editor = page.locator('[data-testid="update-body-editor"] .cm-editor')
            editor.wait_for()
            editor.scroll_into_view_if_needed()
            _settle(page)
            assert "Owner: Morgan" in editor.inner_text(), "the seeded draft is not in the editor"
            faults = _rendered_text_faults(page, '[data-testid="update-body-editor"]', on_glass=True)
            ends = page.evaluate(_ENDS_JS, ENDS)
            page.screenshot(path=str(SHOTS / f"update-editor-wrap-{width}.png"))
            (SHOTS / f"update-editor-wrap-{width}.json").write_text(
                json.dumps({"faults": faults, "ends": ends}, indent=1) + "\n")
            browser.close()
    finally:
        server.stop()

    assert faults["scopes"], "no visible update editor"
    assert not faults["clipped"] and not faults["overlaps"], f"W1 at {width}: {faults}"
    assert not ends["sideways"], f"W2 at {width}: the editor scrolls sideways: {ends['sideways']}"
    assert not ends["missing"], f"W3 at {width}: line ends off the editor ({ends['box']}): {ends['missing']}"


# ══ lane e2e-high-1 ════════════════════════════════════════

DELTA_TOKEN = "hs160-delta-glass"

DELTA_SHOTS = evidence_dir("pm/roadmap/holdspeak/phase-160-the-delta/assets/story-07-shots")

def _delta_init_desk(page: Any, url: str) -> None:
    """Navigate to the hub root so relative fetch paths work, then seed."""
    page.goto(f"{url}/?token={DELTA_TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=DELTA_TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=DELTA_TOKEN)

def _delta_open_project_room(page: Any, url: str, project_id: str) -> None:
    """Navigate the desk to the Project Room for *project_id*."""
    page.evaluate(
        """([key, scope]) => {
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key, scope})
          );
        }""",
        ["open-project-memory", f"project:{project_id}"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)

def _create_project_api(page: Any) -> str:
    """Create a project through the real HTTP route (fast path for API legs)."""
    created = _api(page, "POST", "/api/projects", {
        "name": "Delta Glass API Project",
        "description": "Created via POST /api/projects for delta glass leg.",
        "command_id": "hs160-delta-glass-api",
    }, token=DELTA_TOKEN)
    return created["project"]["id"]

def _seed_post_creation_facts(project_id: str) -> None:
    """Seed meetings, decisions, and overdue action items for the review.

    Creates 3 proposal-producing facts:
    - 2 overdue action items (via meeting association) -> 2 risk_attention proposals
    - 1 accepted decision -> 1 review_flag proposal
    Total: 3 proposals for A/L/X keyboard decisions.

    All three are DB-layer gaps: no HTTP POST route exists for creating
    meetings, decisions, or raw action items. Each gap is noted.
    """
    from holdspeak.db import get_database
    from holdspeak.meeting_session.models import MeetingState

    db = get_database()
    now_iso = datetime.now().isoformat()
    past_due_14d = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    past_due_7d = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    # 1. Meeting + associate with project (DB gap: no POST /api/meetings)
    db.meetings.save_meeting(MeetingState(
        id="m-delta-001",
        started_at=datetime(2026, 8, 25, 10, 0),
        title="Sprint 8 Planning",
        capture_status="finalized",
    ))
    with db._connection() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO meeting_projects
               (meeting_id, project_id, source, confidence)
               VALUES (?, ?, 'manual', 1.0)""",
            ("m-delta-001", project_id),
        )

    # 2. Second meeting for the second action item
    db.meetings.save_meeting(MeetingState(
        id="m-delta-002",
        started_at=datetime(2026, 8, 22, 14, 0),
        title="Sprint 7 Retro",
        capture_status="finalized",
    ))
    with db._connection() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO meeting_projects
               (meeting_id, project_id, source, confidence)
               VALUES (?, ?, 'manual', 1.0)""",
            ("m-delta-002", project_id),
        )

    # 3. Accepted decision (DB gap: no POST /api/decisions)
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO decisions (
                   id, text, rationale, decided_at, date_basis,
                   source_timestamp, provenance_label,
                   source_artifact_id, source_meeting_id,
                   source_state, project_key, lifecycle,
                   superseded_by, created_at, updated_at, last_modified, deleted
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "dec-delta-001",
                "Adopt event sourcing for the payment ledger",
                "Reduces audit risk and enables real-time settlement views",
                "2026-08-20T14:30:00",
                "meeting_date",
                None,
                "reported",
                "",
                "m-delta-001",
                "linked",
                None,
                "accepted",
                None,
                now_iso, now_iso, now_iso, 0,
            ),
        )

    # 4. First overdue action item (DB gap: no POST /api/door)
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO action_items (
                   id, meeting_id, task, owner, due, status,
                   review_state, created_at, source_type, source_ref
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "ai-delta-001",
                "m-delta-001",
                "Update PCI compliance docs for new gateway",
                "karol",
                past_due_14d,
                "pending",
                "accepted",
                now_iso,
                "meeting",
                "",
            ),
        )

    # 5. Second overdue action item (different meeting, different due)
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO action_items (
                   id, meeting_id, task, owner, due, status,
                   review_state, created_at, source_type, source_ref
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "ai-delta-002",
                "m-delta-002",
                "Schedule Black Friday load test with infrastructure",
                "alice",
                past_due_7d,
                "pending",
                "accepted",
                now_iso,
                "meeting",
                "",
            ),
        )

@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_delta_review_loop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """THE LOOP: create Project via Blank interview, seed facts, open
    review, keyboard-decide all proposals, finish, verify room state.

    Wide (1440): shots of grouped queue + ledger, completion summary,
    room after review.
    Narrow (393): shot of one-card + footer verbs.
    """
    _ensure_build()
    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    server, url = _boot(tmp_path, monkeypatch, token=DELTA_TOKEN)
    DELTA_SHOTS.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": width, "height": 900 if width == 1440 else 852},
            )
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))

            _delta_init_desk(page, url)

            # -- Create project via API (HS-169: interview surface retired;
            #    seed through the project route as test_hs169_room_glass.py does) --
            project_id = _create_project_api(page)
            assert project_id, "Project ID should be non-empty"

            # -- Seed post-creation facts --
            _seed_post_creation_facts(project_id)

            # -- Open review via API (triggers evidence collection) --
            review = _api(
                page, "POST", f"/api/projects/{project_id}/reviews",
            token=DELTA_TOKEN,
            )
            review_id = review["review_id"]
            assert review_id.startswith("prev_"), f"Unexpected review_id: {review_id}"
            proposals = review["proposals"]
            proposal_count = len(proposals)
            assert proposal_count >= 3, (
                f"Expected >=3 proposals (2 risk_attention + 1 review_flag), "
                f"got {proposal_count}: "
                f"{[p['proposal_kind'] for p in proposals]}"
            )

            # -- Reload the Room: verb should appear --
            _delta_open_project_room(page, url, project_id)

            # HS-169: the identity band is gone; room-body is the new anchor.
            page.get_by_test_id("room-body").wait_for(timeout=15000)

            # The review verb appears in NEEDS YOU caption because pending_count > 0
            review_verb = page.get_by_test_id("review-verb")
            review_verb.wait_for(timeout=10000)
            assert review_verb.is_visible()
            # HS-169: verb text is now "Review N" (count), not "Review changes"
            review_text = review_verb.inner_text()
            assert review_text.startswith("Review"), f"Review verb text: {review_text}"

            # -- Click the review verb: posture swaps IN PLACE --
            review_verb.click()

            posture = page.get_by_test_id("review-posture")
            posture.wait_for(timeout=15000)
            assert posture.get_attribute("data-phase") == "reviewing"

            # No navigation happened -- assert no modal/dialog overlay
            assert page.locator("dialog[open]").count() == 0, (
                "Review opened a modal -- expected in-place posture swap"
            )

            # -- Layout-dependent assertions --
            # Wide (>=560px container): queue visible, inline verbs
            # Narrow (<560px): queue hidden (CSS display:none), footer verbs,
            #   one card at a time

            if width == 1440:
                # Queue renders GROUPED with count chips
                queue = page.get_by_test_id("review-queue")
                queue.wait_for(timeout=5000)

                kind_groups = page.get_by_test_id("review-kind-group")
                kind_groups.first.wait_for(timeout=5000)
                assert kind_groups.count() >= 1, "No kind groups in the queue"

                count_chips = page.get_by_test_id("review-kind-count")
                count_chips.first.wait_for(timeout=3000)
                assert count_chips.count() >= 1

                queue_items = page.get_by_test_id("review-queue-item")
                queue_items.first.wait_for(timeout=5000)
                rendered_count = queue_items.count()
                assert rendered_count >= 3, (
                    f"Expected >=3 queue items, got {rendered_count}"
                )
            else:
                # Narrow: queue is CSS-hidden; verify the detail card instead
                detail = page.get_by_test_id("review-detail")
                detail.wait_for(timeout=5000)
                assert detail.is_visible()

            # Ledger comparison visible at both widths
            comparison = page.get_by_test_id("review-comparison")
            comparison.wait_for(timeout=5000)
            assert comparison.is_visible()

            # Position indicator shows "1 / N" -- always visible
            position = page.get_by_test_id("review-position")
            position.wait_for(timeout=3000)
            pos_text = position.inner_text()
            # Extract rendered count from position indicator
            rendered_count = int(pos_text.strip().split("/")[-1].strip())
            assert rendered_count >= 3, (
                f"Expected >=3 proposals in position, got: {pos_text}"
            )

            # -- Focus the posture for keyboard --
            posture.focus()

            # -- J/K navigation proof --
            posture.press("j")
            page.wait_for_function(
                """() => {
                    const el = document.querySelector('[data-testid="review-position"]');
                    return el && el.textContent.trim().startsWith('2');
                }""",
                timeout=5000,
            )
            posture.press("k")
            page.wait_for_function(
                """() => {
                    const el = document.querySelector('[data-testid="review-position"]');
                    return el && el.textContent.trim().startsWith('1');
                }""",
                timeout=5000,
            )

            # -- SHOT: grouped queue + ledger (1440) or one-card + footer (393) --
            if width == 1440:
                shot = DELTA_SHOTS / "review-queue-1440.png"
                page.screenshot(path=str(shot), full_page=False)
                assert shot.exists() and shot.stat().st_size > 20_000, (
                    f"Shot too small: {shot.stat().st_size} bytes"
                )

            if width == 393:
                shot = DELTA_SHOTS / "review-card-393.png"
                page.screenshot(path=str(shot), full_page=False)
                assert shot.exists() and shot.stat().st_size > 20_000, (
                    f"Shot too small: {shot.stat().st_size} bytes"
                )

            # -- Keyboard decisions: A on one, L on one, X on one --

            # Accept the first proposal (A)
            posture.press("a")
            remaining_after_a = rendered_count - 1
            page.wait_for_function(
                f"""() => {{
                    const el = document.querySelector('[data-testid="review-position"]');
                    return el && el.textContent.includes('/ {remaining_after_a}');
                }}""",
                timeout=10000,
            )

            # Defer the next proposal (L)
            posture.press("l")
            remaining_after_l = remaining_after_a - 1
            page.wait_for_function(
                f"""() => {{
                    const el = document.querySelector('[data-testid="review-position"]');
                    return el && el.textContent.includes('/ {remaining_after_l}');
                }}""",
                timeout=10000,
            )

            # Dismiss the next (X) -- undo notice should appear
            posture.press("x")
            # After the last proposal is dismissed, the phase goes to exhausted
            # and the undo notice appears in the exhausted view
            page.wait_for_function(
                """() => {
                    const undo = document.querySelector('[data-testid="review-undo-notice"]');
                    const posture = document.querySelector('[data-testid="review-posture"]');
                    return (undo !== null) ||
                           (posture && posture.getAttribute('data-phase') === 'exhausted');
                }""",
                timeout=10000,
            )

            # Decide any remaining proposals with A (if more than 3)
            for _ in range(max(0, rendered_count - 3)):
                posture.press("a")
                page.wait_for_timeout(1000)

            # -- Exhausted: completion summary --
            page.wait_for_function(
                """() => {
                    const el = document.querySelector('[data-testid="review-posture"]');
                    return el && el.getAttribute('data-phase') === 'exhausted';
                }""",
                timeout=10000,
            )

            summary = page.get_by_test_id("review-summary")
            summary.wait_for(timeout=5000)
            assert summary.is_visible()

            # Verify summary has at least the accepted count
            accepted_badge = page.get_by_test_id("summary-accepted")
            if accepted_badge.count() > 0:
                assert accepted_badge.is_visible()

            deferred_badge = page.get_by_test_id("summary-deferred")
            if deferred_badge.count() > 0:
                assert deferred_badge.is_visible()

            dismissed_badge = page.get_by_test_id("summary-dismissed")
            if dismissed_badge.count() > 0:
                assert dismissed_badge.is_visible()

            # -- SHOT: completion summary --
            if width == 1440:
                shot = DELTA_SHOTS / "review-summary-1440.png"
                page.screenshot(path=str(shot), full_page=False)
                assert shot.exists() and shot.stat().st_size > 20_000

            # -- Finish review: Cmd/Ctrl+Enter --
            modifier = "Meta" if os.uname().sysname == "Darwin" else "Control"
            posture_el = page.get_by_test_id("review-posture")
            posture_el.focus()
            posture_el.press(f"{modifier}+Enter")

            # Wait for checkpointed state (review-accepted-notice)
            page.wait_for_function(
                """() => {
                    return document.querySelector('[data-testid="review-accepted-notice"]') !== null;
                }""",
                timeout=15000,
            )

            # -- Exit the review posture (Escape) --
            posture_el = page.get_by_test_id("review-posture")
            posture_el.focus()
            posture_el.press("Escape")

            # Wait for posture to disappear (back to room)
            page.wait_for_function(
                """() => {
                    return document.querySelector('[data-testid="review-posture"]') === null;
                }""",
                timeout=10000,
            )

            # -- Room: pending 0, review verb gone --
            # HS-169: the identity band is gone; room-body is the new anchor.
            page.get_by_test_id("room-body").wait_for(timeout=10000)

            # Review verb should NOT appear (pending_count = 0)
            page.wait_for_timeout(1000)  # let the refresh settle
            assert page.get_by_test_id("review-verb").count() == 0, (
                "Review verb should not appear after review acceptance"
            )

            _assert_clean(page, errors)

            # -- SHOT: room after review --
            if width == 1440:
                shot = DELTA_SHOTS / "room-after-review-1440.png"
                page.screenshot(path=str(shot), full_page=False)
                assert shot.exists() and shot.stat().st_size > 20_000

            # -- API verification: pending_count = 0, last_accepted_at set --
            room = _api(page, "GET", f"/api/projects/{project_id}/room", token=DELTA_TOKEN)
            review_section = room["review"]
            assert review_section["pending_count"] == 0
            assert review_section["open_review_id"] is None
            assert review_section["last_accepted_at"] is not None

            # -- Zero false ledger events: one review.accepted, no phantoms --
            from holdspeak.db import get_database

            db = get_database()
            with db._connection() as conn:
                events = conn.execute(
                    "SELECT * FROM service_events WHERE event_type LIKE '%review%' "
                    "ORDER BY created_at",
                ).fetchall()
            review_events = [dict(e) for e in events]
            accepted_events = [
                e for e in review_events
                if "accepted" in (e.get("event_type") or "")
            ]
            assert len(accepted_events) == 1, (
                f"Expected 1 review.accepted event, got {len(accepted_events)}: "
                f"{[e['event_type'] for e in review_events]}"
            )

            browser.close()
    finally:
        server.stop()
        reset_database()

WINGS_TOKEN = "hs168-wings-glass"

WINGS_SHOTS = evidence_dir("pm/roadmap/holdspeak/phase-168-the-connections-door/assets/story-05-shots")

# A project name longer than any reasonable head can show without ellipsis.
WINGS_LONG_NAME = "A Very Long Project Name That Should Trigger Ellipsis On The Title Bar Here"

assert len(WINGS_LONG_NAME) >= 70, f"Name is only {len(WINGS_LONG_NAME)} chars"

def _wings_init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={WINGS_TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=WINGS_TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=WINGS_TOKEN)

def _wings_create_project(page: Any) -> str:
    result = _api(page, "POST", "/api/projects", {
        "name": WINGS_LONG_NAME,
        "description": "Glass test project for HS-168-05 wings layout.",
        "command_id": "hs168-wings-glass",
    }, token=WINGS_TOKEN)
    return result["project"]["id"]

def _wings_open_project_room(page: Any, url: str, project_id: str) -> None:
    page.evaluate(
        """([key, scope]) => {
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key, scope})
          );
        }""",
        ["open-project-memory", f"project:{project_id}"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)

@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_wings_inside_head(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    width: int,
) -> None:
    """Wings bounding box lies inside the head and window at both widths."""
    _ensure_build()
    from playwright.sync_api import sync_playwright

    server, url = _boot(tmp_path, monkeypatch, token=WINGS_TOKEN)
    errors: list[str] = []

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(str(error)))

            _wings_init_desk(page, url)
            project_id = _wings_create_project(page)
            _wings_open_project_room(page, url, project_id)

            # Wait for the 169 Room body to appear (the 169 Room has
            # no project-room-name test-id; room-body is the anchor).
            room_body = page.get_by_test_id("room-body")
            room_body.wait_for(timeout=15000)

            _settle(page)

            # Locate the elements
            head = page.locator(".desk-pullout-head.has-wings")
            title = head.locator(".desk-pullout-title")
            wings_loc = head.locator(".desk-wings")
            window = page.locator(".desk-window-shell")

            head.wait_for(timeout=5000)

            head_box = head.bounding_box()
            title_box = title.bounding_box()
            window_box = window.first.bounding_box()

            # PHILO-13-11 (C1, owner-ratified 2026-10-02): at 393 the head is
            # ONE 44 px row (close + wings); the window's name moves to the
            # SCREEN title bar, which names the front window. The long name
            # is fenced there (below) instead of in the head.
            phone = width < 720
            screen_name = page.locator("[data-testid=desk-screen-title] .desk-screen-name")
            name_el = screen_name if phone else title

            assert head_box is not None, "head bounding box is null"
            if phone:
                assert title_box is None, "the head repeats the title at 393 (the screen bar names the window)"
                assert screen_name.bounding_box() is not None, "the screen title bar does not name the window"
            else:
                assert title_box is not None, "title bounding box is null"
            assert window_box is not None, "window bounding box is null"

            # At 393, wings may not be visible (compact mode may hide them).
            wings_visible = wings_loc.is_visible()
            wings_box = wings_loc.bounding_box() if wings_visible else None

            # Shoot the window element
            WINGS_SHOTS.mkdir(parents=True, exist_ok=True)
            shot_path = WINGS_SHOTS / f"wings-{width}.png"
            window.first.screenshot(path=str(shot_path))

            if wings_box is not None:
                # Wings right edge must be inside the head right edge
                wings_right = wings_box["x"] + wings_box["width"]
                head_right = head_box["x"] + head_box["width"]
                window_right = window_box["x"] + window_box["width"]

                assert wings_right <= head_right + 1, (
                    f"Wings right edge ({wings_right:.0f}) exceeds head right edge "
                    f"({head_right:.0f}) -- wings pushed off the window"
                )
                assert wings_right <= window_right + 1, (
                    f"Wings right edge ({wings_right:.0f}) exceeds window right edge "
                    f"({window_right:.0f})"
                )

                # Wings left edge must be inside the head
                assert wings_box["x"] >= head_box["x"] - 1, (
                    f"Wings left edge ({wings_box['x']:.0f}) is before head left edge "
                    f"({head_box['x']:.0f})"
                )

            # HS-169-07: with only ROOM + HISTORY wings (2 instead of 4),
            # the title may fit without truncation at 1440. The primary
            # invariant (wings inside head/window) is asserted above.
            # Truncation is a secondary signal that the name is long
            # enough to matter -- assert it only at 393 where the head
            # is narrow enough to force it.
            if phone:
                assert screen_name.text_content().strip() == WINGS_LONG_NAME, screen_name.text_content()
            title_scroll = name_el.evaluate("el => el.scrollWidth")
            title_client = name_el.evaluate("el => el.clientWidth")
            if width < 560:
                assert title_scroll > title_client, (
                    f"Title not truncated at {width}: scrollWidth={title_scroll}, "
                    f"clientWidth={title_client} -- ellipsis did not fire"
                )

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()

PEOPLE_SHOTS = evidence_dir("pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-14-shots")

PEOPLE_WRITE_SHOTS = os.environ.get("HOLDSPEAK_WRITE_SHOTS") == "1"

PEOPLE_TOKEN = "hs200-people"

PEOPLE_OWNER_LOGIN = "karolswdev"

def _people_create_project(page: Any, name: str) -> str:
    created = _api(page, "POST", "/api/projects", {
        "name": name,
        "description": "Seeded for the HS-200-14 browser proof.",
        "command_id": f"hs200-14-{uuid.uuid4().hex[:8]}",
    }, token=PEOPLE_TOKEN)
    return created["project"]["id"]

def _seed_gh_connection() -> None:
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO watch_provider_connections "
            "(id, provider_id, external_connection_ref, state, "
            " last_connected_at, created_at, updated_at) "
            "VALUES ('wpc-gh', 'github', ?, 'connected', "
            " datetime('now'), datetime('now'), datetime('now'))",
            (PEOPLE_OWNER_LOGIN,),
        )

def _seed_watch(project_id: str, *, watch_id: str, name: str, snapshot: list[dict[str, Any]], state: str = "active") -> None:
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO connector_watches "
            "(id, connector_id, query_kind, name, query_json, snapshot_json, "
            " enabled, last_success_at, last_error, project_id, state, created_at, updated_at) "
            "VALUES (?, 'gh', 'pull_requests', ?, ?, ?, 1, datetime('now'), NULL, ?, ?, "
            " datetime('now'), datetime('now'))",
            (watch_id, name, json.dumps({"repository": name}, sort_keys=True),
             json.dumps(snapshot), project_id, state),
        )

def _seed_meeting_with_proposals(project_id: str, proposals: list[tuple[str, str]]) -> list[str]:
    """A finalized meeting linked to the Project and one PROPOSED action per
    (owner, text); returns the proposal ids for the real confirm route."""
    from holdspeak.db import get_database
    db = get_database()
    now = datetime.now()
    ids: list[str] = []
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings "
            "(id, started_at, ended_at, title, duration_seconds, intel_status, capture_status, provenance) "
            "VALUES ('m-review', ?, ?, 'Architecture review', 1800.0, 'complete', 'finalized', 'desktop')",
            ((now - timedelta(hours=2)).isoformat(), (now - timedelta(hours=1, minutes=30)).isoformat()),
        )
        conn.execute(
            "INSERT OR IGNORE INTO meeting_projects (meeting_id, project_id, source, confidence) "
            "VALUES ('m-review', ?, 'manual', 1.0)",
            (project_id,),
        )
        for index, (owner, text) in enumerate(proposals):
            pid = f"prop-{uuid.uuid4().hex[:12]}"
            conn.execute(
                "INSERT INTO follow_through_proposals "
                "(id, meeting_id, project_id, kind, text, owner_hint, due_hint, source_plugin, "
                " fingerprint, state, model_host, created_at, segment_index, span_start, span_end) "
                "VALUES (?, 'm-review', ?, 'action', ?, ?, NULL, 'decision_capture', ?, 'proposed', "
                " '192.168.1.43', ?, ?, ?, ?)",
                (pid, project_id, text, owner, f"fp-{uuid.uuid4().hex[:12]}", now.isoformat(),
                 2 + index, 10.0 + index * 5, 14.0 + index * 5),
            )
            ids.append(pid)
    return ids

def _person(page: Any, name: str, *, aliases: tuple[str, ...] = (), project_id: str | None = None) -> str:
    created = _api(page, "POST", "/api/people/relationships", {"display_name": name}, token=PEOPLE_TOKEN)
    rid = str(created["relationship"]["id"])
    for alias in aliases:
        _api(page, "POST", f"/api/people/relationships/{rid}/owner-aliases", {"alias": alias}, token=PEOPLE_TOKEN)
    if project_id:
        _api(page, "POST", f"/api/people/relationships/{rid}/projects/{project_id}", {}, token=PEOPLE_TOKEN)
    return rid

def _seed_ready_desk(page: Any) -> dict[str, str]:
    """His desk, with the ledger set up: Priya Sharma + Priya Nair (a shared
    first name), Marek Kubiak linked to the Project by `project_refs` and
    to his GitHub login by an owner alias; a review meeting whose two
    actions name `Priya` and `marek-k`; a PR waiting on `marek-k`."""
    _seed_gh_connection()
    project_id = _people_create_project(page, "Q4 platform")
    _api(page, "POST", "/api/people/setup", {}, token=PEOPLE_TOKEN)
    sharma = _person(page, "Priya Sharma")
    nair = _person(page, "Priya Nair")
    marek = _person(page, "Marek Kubiak", aliases=("marek-k",), project_id=project_id)
    proposals = _seed_meeting_with_proposals(project_id, [
        ("Priya", "Confirm the freeze window"),
        ("marek-k", "Own the PostgreSQL migration"),
    ])
    for pid in proposals:
        confirmed = _api(page, "POST", f"/api/proposals/{pid}/confirm", {}, token=PEOPLE_TOKEN)
        assert "error" not in confirmed, confirmed
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    _seed_watch(project_id, watch_id="w-prs", name="karolswdev/HoldSpeak", snapshot=[
        {"number": 612, "title": "Rig settles animations", "state": "OPEN",
         "reviewRequests": ["marek-k"], "updatedAt": yesterday},
        {"number": 613, "title": "Fix token alignment", "state": "OPEN",
         "reviewRequests": ["marek-k", PEOPLE_OWNER_LOGIN], "updatedAt": yesterday},
    ])
    # A revoked source (counsel P2-v): paused, so its PR names Marek but
    # contributes no count -- the row must say `PAUSED · OMITTED`.
    _seed_watch(project_id, watch_id="w-paused", name="karolswdev/Paused", state="paused", snapshot=[
        {"number": 700, "title": "Old work", "state": "OPEN",
         "reviewRequests": ["marek-k"], "updatedAt": yesterday},
    ])
    return {"project_id": project_id, "sharma": sharma, "nair": nair, "marek": marek}

def _arrive(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={PEOPLE_TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=PEOPLE_TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=PEOPLE_TOKEN)

def _people_open_room(page: Any, project_id: str) -> None:
    page.evaluate(
        """([key, scope]) => {
          sessionStorage.setItem("hs.desk.staged-surface-open", JSON.stringify({key, scope}));
        }""",
        ["open-project-memory", f"project:{project_id}"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)
    # PHILO-17 refit (room): People is a fold in the Room; open it.
    fold = page.locator("[data-testid=room-fold-people] details").first
    fold.wait_for(state="attached", timeout=15000)
    if fold.get_attribute("open") is None:
        page.locator("[data-testid=room-fold-people] summary").first.click()
    page.get_by_test_id("room-people-head-verb").wait_for(timeout=15000)
    _settle(page)

def _people_section(page: Any) -> Any:
    return page.locator("section.surface-section").filter(has=page.get_by_test_id("room-people-head-verb")).first

def _scroll_people_into_view(page: Any) -> None:
    """Put the section HEAD at the top of the body: the ask well is sticky
    at the foot at every width (Room condition 7), so a row merely
    "in view" can still sit underneath the composer (the 41 scar)."""
    _people_section(page).evaluate("el => el.scrollIntoView({block: 'start'})")
    _settle(page)

def _shot(page: Any, name: str, width: int) -> Path | None:
    """Take a shot with the pointer parked off every row (no hover state)."""
    if not PEOPLE_WRITE_SHOTS:
        return None
    PEOPLE_SHOTS.mkdir(parents=True, exist_ok=True)
    page.mouse.move(2, 2)
    _settle(page)
    path = PEOPLE_SHOTS / f"{name}-{width}.png"
    page.screenshot(path=str(path), full_page=False)
    assert path.stat().st_size > 2_000, f"Shot {name} too small ({path.stat().st_size})"
    return path

def _people_room_window(page: Any) -> Any:
    return page.locator(".desk-surface-window").filter(has=page.get_by_test_id("room-people-head-verb")).first

def _primaries(page: Any) -> list[str]:
    """Every filled primary on the FACE (the Room window; the desk behind it
    is another face with its own one): at most one."""
    return _people_room_window(page).evaluate("""(win) => [...win.querySelectorAll('.btn--primary')]
        .filter(b => b.getBoundingClientRect().width > 0)
        .map(b => (b.className + ' :: ' + (b.textContent || '').trim()))""")

def _overflowing(page: Any, width: int) -> list[str]:
    """Every interactive element whose right edge passes the viewport."""
    return page.evaluate("""(width) => {
        const out = [];
        const chair = document.querySelector('.chair') || document;
        const sel = 'button, a, [role="button"], [role="group"], .surface-disclosure-trigger';
        for (const el of chair.querySelectorAll(sel)) {
            const r = el.getBoundingClientRect();
            if (r.width === 0 && r.height === 0) continue;
            if (r.right > width + 0.5) out.push((el.className || el.tagName) + ' :: ' + (el.textContent || '').trim().slice(0, 40) + ' right=' + r.right.toFixed(1));
        }
        return out;
    }""", width)

def _raw_buttons(page: Any) -> list[str]:
    """Every <button> in the PEOPLE section that is not the library Button,
    the mic, a ledger line, or a library Disclosure trigger."""
    return _people_section(page).evaluate("""(section) => {
        const raw = [];
        for (const btn of section.querySelectorAll('button')) {
            const cls = btn.className || '';
            if (!cls.includes('btn') && !cls.includes('desk-mic') &&
                !cls.includes('surface-ledger-line') &&
                !cls.includes('surface-disclosure-trigger')) raw.push(cls + ' :: ' + (btn.textContent || '').trim());
        }
        return raw;
    }""")

def _zero_counters(page: Any) -> list[str]:
    """Any `0 <NOUN>` or `0 OF` token on the section (A.8) -- except the
    typed partial `PEOPLE 0 OF N`, which is a coverage fraction, not a
    counter."""
    text = _people_section(page).inner_text()
    return [
        line.strip() for line in text.split("\n")
        if line.strip().startswith("0 ") and not line.strip().startswith("0 OF")
        or " 0 " in f" {line.strip()} " and "0 OF" not in line
    ]

def _people_body_check(page: Any, width: int) -> None:
    assert _raw_buttons(page) == [], "every verb is the library Button (A.1)"
    assert _zero_counters(page) == [], "no counters of zero (A.8)"
    assert len(_primaries(page)) <= 1, f"one filled primary per face: {_primaries(page)}"
    if width <= 480:
        assert page.evaluate("document.documentElement.scrollWidth") <= width
        over = _overflowing(page, width)
        assert over == [], f"elements past the viewport at {width}: {over}"

def _run_ready_resolve_and_people(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    _ensure_build()
    # The key file the hub reads: `_boot` sets HOLDSPEAK_PEOPLE_KEYSTORE_FILE
    # to it, inside the isolated HOME.
    key_file = people_key_file(tmp_path)
    server, url = _boot(tmp_path, monkeypatch, token=PEOPLE_TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 1000})
            page.on("pageerror", lambda e: errors.append(str(e)))
            _arrive(page, url)
            seeds = _seed_ready_desk(page)
            project_id = seeds["project_id"]

            # ── ready: the typed partial and the ambiguous owner ──
            _people_open_room(page, project_id)
            _scroll_people_into_view(page)
            section = _people_section(page)
            assert section.locator("h3").inner_text().strip() == "PEOPLE 1 OF 2"
            assert page.get_by_test_id("room-people-gaps").inner_text().strip() == "1 AMBIGUOUS"
            owner_tokens = [t.strip() for t in page.get_by_test_id("room-people-owner-token").all_inner_texts()]
            assert owner_tokens == ["OWNER · AMBIGUOUS · 2 MATCHES"], owner_tokens
            body = section.inner_text()
            assert "Priya Sharma" not in body and "Priya Nair" not in body, "an ambiguous owner was attributed"
            assert "marek-k" not in body, "a raw login crossed onto the face"
            assert "Marek Kubiak" in body
            marek_row = page.get_by_test_id("room-people-row").filter(has_text="Marek Kubiak").first
            marek_li = marek_row.locator("xpath=ancestor::li[1]")
            assert "1 OPEN COMMITMENT" in marek_li.inner_text()
            commitment = marek_li.get_by_test_id("room-people-commitment").first
            assert "Own the PostgreSQL migration" in commitment.inner_text()
            # Tokens are CSS-uppercased on the face; compare the rendered case.
            assert "MEETING · ARCHITECTURE REVIEW · SEGMENT 4" in commitment.inner_text().upper()
            assert commitment.get_by_test_id("room-people-open-source").count() == 1
            fact = marek_li.get_by_test_id("room-people-fact").first
            assert "karolswdev/HoldSpeak" in fact.inner_text() and "2 PRS WAITING" in fact.inner_text()
            assert marek_li.get_by_test_id("room-people-fact").count() == 1, "a paused Watch contributed a count"
            omitted = marek_li.get_by_test_id("room-people-omitted").first
            assert "karolswdev/Paused" in omitted.inner_text()
            assert omitted.get_by_test_id("room-people-omitted-token").inner_text().strip().upper() == "PAUSED · OMITTED"
            priya_li = page.get_by_test_id("room-people-unresolved-row").first.locator("xpath=ancestor::li[1]")
            assert "Confirm the freeze window" in priya_li.inner_text()
            assert page.get_by_test_id("room-people-head-verb").inner_text().strip() == "People"
            _people_body_check(page, width)
            _shot(page, "people-ready", width)

            # ── resolve: candidates under the row, no modal, the ledger's own write ──
            resolve = page.get_by_test_id("room-people-resolve-verb")
            assert resolve.get_attribute("aria-label") == "Resolve: Priya"
            resolve.click()
            page.get_by_test_id("room-people-resolve").wait_for(timeout=5000)
            _settle(page)
            assert page.locator("[role='dialog']").count() == 0, "no modals (A.4)"
            well = page.get_by_test_id("room-people-resolve")
            names = [t.strip() for t in well.get_by_test_id("room-people-candidate").all_inner_texts()]
            assert sorted(names) == ["Priya Nair", "Priya Sharma"], names
            _people_body_check(page, width)
            _shot(page, "people-resolve", width)
            well.get_by_test_id("room-people-candidate").filter(has_text="Priya Sharma").click()
            # PHILO-17 refit (room): inside its fold the section's own caption
            # is not drawn (the fold's title names it); it still counts 2.
            page.locator("section.surface-section h3", has_text="PEOPLE 2").first.wait_for(state="attached", timeout=10000)
            _settle(page)
            assert page.get_by_test_id("room-people-gaps").count() == 0, "no gap tokens once complete"
            assert page.get_by_test_id("room-people-unresolved-row").count() == 0
            sharma_body = page.get_by_test_id("room-people-row").filter(has_text="Priya Sharma").first.locator("xpath=ancestor::li[1]").inner_text()
            assert "Confirm the freeze window" in sharma_body, "the commitment moved onto the resolved person"
            detail = _api(page, "GET", f"/api/people/relationships/{seeds['sharma']}", token=PEOPLE_TOKEN)
            assert "Priya" in (detail["relationship"].get("owner_aliases") or []), "the alias landed in the ledger"
            _people_body_check(page, width)
            _shot(page, "people-resolved", width)

            # ── People: scoped to the Project, and the way back ──
            verb = page.get_by_test_id("room-people-head-verb")
            verb.focus()
            verb.click()
            page.get_by_test_id("people-roster-everyone").wait_for(timeout=15000)
            people_window = page.locator(".desk-surface-window").filter(
                has=page.get_by_test_id("people-roster-everyone"),
            ).first
            _settle(page)
            roster = people_window.inner_text()
            assert "1 ON THIS PROJECT" in roster and "Marek Kubiak" in roster
            assert "2 MORE · Everyone" in roster
            assert "Priya Nair" not in roster
            if width <= 480:
                over = _overflowing(page, width)
                assert over == [], f"elements past the viewport at {width}: {over}"
            _shot(page, "people-core-project", width)
            # The window's own traffic light (the dock carries a second `Close
            # People`; the window region is the one being closed).
            page.get_by_role("region", name="People").get_by_label("Close People").click()
            page.wait_for_function(
                "() => document.activeElement && document.activeElement.dataset.testid === 'room-people-head-verb'",
                timeout=5000,
            )
            _settle(page)

            # ── locked: the key file turns unreadable ──
            key_file.write_text("{not json", encoding="utf-8")
            readiness = _api(page, "GET", "/api/people/readiness", token=PEOPLE_TOKEN)
            assert readiness["state"] == "locked", readiness
            _people_open_room(page, project_id)
            _scroll_people_into_view(page)
            section = _people_section(page)
            assert section.locator("h3").inner_text().strip() == "PEOPLE 0 OF 2"
            assert page.get_by_test_id("room-people-gaps").inner_text().strip() == "LOCKED"
            assert page.get_by_test_id("room-people-head-verb").inner_text().strip() == "Unlock"
            owner_tokens = sorted(t.strip() for t in page.get_by_test_id("room-people-owner-token").all_inner_texts())
            assert owner_tokens == ["OWNER · LOCKED", "OWNER · LOCKED"], owner_tokens
            assert page.get_by_test_id("room-people-resolve-verb").count() == 0, "no dead verb under a lock"
            body = section.inner_text()
            assert "Priya Sharma" not in body and "Marek Kubiak" not in body, "a locked store named nobody"
            assert "marek-k" in body or "Priya" in body
            _people_body_check(page, width)
            _shot(page, "people-locked", width)

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()

class TestPeoplePreparationGlass:
    @pytest.mark.timeout(240)
    def test_ready_resolve_people_locked_1440(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _run_ready_resolve_and_people(tmp_path, monkeypatch, 1440)

TASK_SHOTS = evidence_dir("pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-41-shots")

TASK_TOKEN = "hs200-41-glass"

def _task_init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TASK_TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TASK_TOKEN)
    _api(page, "PUT", "/api/setup/onboarding",
         {"disposition": "completed"}, token=TASK_TOKEN)

def _task_create_project(page: Any, name: str, command_id: str) -> str:
    created = _api(page, "POST", "/api/projects", {
        "name": name,
        "description": "Seeded for the HS-200-41 browser proof.",
        "command_id": command_id,
    }, token=TASK_TOKEN)
    return created["project"]["id"]

def _task_open_room(page: Any, project_id: str) -> None:
    page.evaluate(
        """([key, scope]) => {
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key, scope})
          );
        }""",
        ["open-project-memory", f"project:{project_id}"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)
    page.get_by_test_id("room-body").wait_for(timeout=20000)
    _settle(page)

def _task_room_window(page: Any) -> Any:
    return page.locator(".desk-surface-window").filter(
        has=page.locator('[data-testid="room-body"]')
    ).first

def _shot_element(page: Any, locator: Any, name: str, *, pad: int = 0) -> Path:
    """Shoot one element (optionally with padding around it).

    The element is scrolled into view first. Without that the clip is taken at
    whatever scroll position the previous leg left, and the Room's STICKY ask
    foot — which floats over the body by design — lands in the middle of the
    specimen. The block shots at 1440 and 393 were showing the composer sitting
    across the row they were meant to show.
    """
    try:
        locator.scroll_into_view_if_needed(timeout=5000)
    except Exception:
        pass  # a shot is never worth failing a leg over
    page.wait_for_timeout(150)
    _settle(page)
    TASK_SHOTS.mkdir(parents=True, exist_ok=True)
    path = TASK_SHOTS / f"{name}.png"
    if pad:
        box = locator.bounding_box()
        assert box, f"{name}: element has no box"
        view = page.viewport_size
        clip = {
            "x": max(0.0, box["x"] - pad),
            "y": max(0.0, box["y"] - pad),
            "width": min(view["width"] - max(0.0, box["x"] - pad), box["width"] + 2 * pad),
            "height": min(view["height"] - max(0.0, box["y"] - pad), box["height"] + 2 * pad),
        }
        page.screenshot(path=str(path), clip=clip)
    else:
        locator.screenshot(path=str(path))
    assert path.stat().st_size > 1_000, f"Shot {name} too small"
    return path

def _shot_room(page: Any, name: str) -> Path:
    """Shoot the Room window (tall viewport so nothing is clipped)."""
    _settle(page)
    old = page.viewport_size
    page.set_viewport_size({"width": old["width"], "height": 1600})
    _settle(page)
    path = _shot_element(page, _task_room_window(page), name)
    page.set_viewport_size(old)
    return path

def _save_ask(page: Any, project_id: str, purpose: str, **extra: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"purpose": purpose, "lens": "Project", **extra}
    return _api(
        page, "POST", f"/api/projects/{project_id}/ask-tasks", body, token=TASK_TOKEN,
    )["task"]

def _rows(page: Any) -> Any:
    return page.locator('[data-testid="room-unfinished"] .surface-task-resume')

@pytest.mark.timeout(300)
def test_narrow_container_rule_at_393(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The `@container surface (max-width: 420px)` rule, rendered.

    Two rows — one saved, one failed with a long quoted reason — so the
    fold, the wrapping token row and the row rhythm are all legible.
    """
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TASK_TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 393, "height": 852})
            page.on("pageerror", lambda e: errors.append(str(e)))

            _task_init_desk(page, url)
            project_id = _task_create_project(page, "Q4 platform", "hs200-41-narrow")
            _save_ask(
                page, project_id,
                "Whether the Q4 platform migration can land before the freeze",
                recipe_key="risk-review",
            )
            _task_open_room(page, project_id)

            # A second ask, refused for real, so the narrow row carries a
            # long quoted reason as well as the short one.
            well = page.locator('[data-testid="room-ask-input-well"] input')
            well.wait_for(timeout=10000)
            well.fill("Draft the migration risk note for the platform review")
            well.press("Enter")
            page.wait_for_function(
                """() => document.querySelectorAll(
                     '[data-testid="room-unfinished"] .surface-task-resume').length === 2""",
                timeout=25000,
            )
            _settle(page)

            geometry = page.evaluate(
                """() => Array.from(document.querySelectorAll(
                     '[data-testid="room-unfinished"] .surface-task-resume')).map(row => {
                     const cs = getComputedStyle(row);
                     const purpose = row.querySelector('.surface-task-resume-purpose');
                     const verbs = row.querySelector('.surface-task-resume-verbs');
                     const tokens = row.querySelector('.surface-task-resume-tokens');
                     return {
                       state: row.dataset.state,
                       areas: cs.gridTemplateAreas,
                       rowWidth: Math.round(row.getBoundingClientRect().width),
                       purposeWraps:
                         getComputedStyle(purpose).whiteSpace === 'normal',
                       purposeHeight: Math.round(purpose.getBoundingClientRect().height),
                       tokensBottom: Math.round(tokens.getBoundingClientRect().bottom),
                       verbsTop: Math.round(verbs.getBoundingClientRect().top),
                       clientWidth: row.clientWidth,
                       scrollWidth: row.scrollWidth,
                       overflowPx: row.scrollWidth - row.clientWidth,
                       widest: Array.from(row.querySelectorAll('*'))
                         .map(el => ({
                           cls: el.className && el.className.baseVal === undefined
                             ? String(el.className) : '',
                           w: Math.round(el.getBoundingClientRect().width),
                           text: (el.textContent || '').trim().slice(0, 70),
                         }))
                         .sort((a, b) => b.w - a.w)[0],
                     };
                   })"""
            )
            print(f"[hs200-41] narrow geometry: {json.dumps(geometry, indent=2)}")
            assert len(geometry) == 2
            for g in geometry:
                # F3 added the `reason` line: four areas, eight quotes.
                assert g["areas"].count('"') == 8, g
                assert g["purposeWraps"], "the narrow rule must let the purpose wrap"
                assert g["verbsTop"] >= g["tokensBottom"] - 1, (
                    f"the verbs must fall UNDER the tokens at 393: {g}"
                )
            # The saved row — the ratified `UNFINISHED 1` — fits its container.
            saved_row = [g for g in geometry if g["state"] == "saved"][0]
            assert saved_row["overflowPx"] <= 1, saved_row

            # F3, FIXED: a FAILED row whose quoted reason is a long
            # unbreakable string (`model file not found: /very/long/path.gguf`)
            # used to push its own state chip past the row box at 393 — the
            # chip does not wrap and the row does not scroll, so the tail of
            # the hub's own words was simply not on the glass. The chip now
            # says `FAILED` and the quoted words have their own wrapping row,
            # so the failed row fits like every other one.
            failed_row = [g for g in geometry if g["state"] == "failed"][0]
            print(f"[hs200-41] narrow failed row: {json.dumps(failed_row)}")
            assert failed_row["overflowPx"] <= 1, (
                "the engine's quoted words must wrap, never run off-glass: "
                f"{failed_row}"
            )

            _shot_room(page, "taskresume-narrow-393")
            _shot_element(
                page, page.locator('[data-testid="room-unfinished"]'),
                "taskresume-narrow-rows-393",
            )
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()

@pytest.mark.timeout(300)
def test_the_rows_rove_on_a_list_that_mounted_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The ratified keyboard law (design D2(f): "Up/Down rove rows"), FIXED.

    This was a live defect the glass caught and no unit test could: the Room's
    list always starts empty and is filled by `loadUnfinished`, and
    `TaskResumeList` renders `null` while it has no children (A.8), so
    `useRovingRows`'s listener effect saw a null ref on mount — and with deps
    `[ref, selector, rowSelector]`, all stable, it NEVER ran again once the
    rows arrived. Up/Down/Left/Right/Home/End and type-ahead were all dead,
    while the dep-less stamping effect still set the tabindexes so the list
    LOOKED like one Tab stop. Every vitest specimen renders its rows on mount,
    which is why they were green and the browser was not.

    The hook now mirrors the ref into state, so the listener effect re-runs the
    moment the element exists. That is a fix in `roving.ts`, not in this face:
    every list that mounts empty and fills from a fetch was equally dead, which
    is most of them.

    A CDP listener census is the proof, plus the keys actually moving.
    """
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TASK_TOKEN)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            _task_init_desk(page, url)
            project_id = _task_create_project(page, "Q4 platform", "hs200-41-rove")
            _save_ask(page, project_id, "The first unfinished ask")
            _save_ask(page, project_id, "The second unfinished ask")
            _task_open_room(page, project_id)
            page.get_by_test_id("room-unfinished").wait_for(timeout=15000)
            assert _rows(page).count() == 2

            cdp = page.context.new_cdp_session(page)

            def listeners(selector: str) -> list[str]:
                found = cdp.send("Runtime.evaluate", {
                    "expression": f"document.querySelector({selector!r})",
                })["result"]
                if not found.get("objectId"):
                    return ["(element absent)"]
                got = cdp.send(
                    "DOMDebugger.getEventListeners",
                    {"objectId": found["objectId"]},
                )
                return sorted(entry["type"] for entry in got["listeners"])

            unfinished = listeners(".surface-task-resume-list")
            ledger = listeners(".surface-ledger")
            print(f"[hs200-41] listeners on .surface-task-resume-list: {unfinished}")
            print(f"[hs200-41] listeners on .surface-ledger (mounts full):  {ledger}")
            assert unfinished == ["focusin", "keydown"], (
                f"the keyboard law must be BOUND on a list that mounted empty: {unfinished}"
            )
            assert ledger == ["focusin", "keydown"], (
                f"the comparison list changed shape: {ledger}"
            )

            def focused() -> str:
                return page.evaluate(
                    """() => {
                        const el = document.activeElement;
                        if (!el) return '';
                        return (el.getAttribute('aria-label') || el.textContent || '').trim();
                    }"""
                )

            page.eval_on_selector(
                '[data-testid="room-unfinished"] .surface-task-resume '
                'button[tabindex="0"]', "el => el.focus()",
            )
            entry = focused()
            assert entry.startswith("Resume: "), entry

            # Down walks to the OTHER row's verb.
            page.keyboard.press("ArrowDown")
            page.wait_for_timeout(90)
            down = focused()
            assert down.startswith("Resume: ") and down != entry, (
                f"ArrowDown must walk to the next row: {entry!r} -> {down!r}"
            )
            # Up comes back.
            page.keyboard.press("ArrowUp")
            page.wait_for_timeout(90)
            assert focused() == entry, "ArrowUp must walk back"
            # Right walks this row's OWN controls (the MORE fold is one).
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(90)
            right = focused()
            assert right != entry, f"ArrowRight must walk the row's controls: {right!r}"
            # End/Home reach the ends.
            page.keyboard.press("End")
            page.wait_for_timeout(90)
            assert focused() == down, f"End must reach the last row: {focused()!r}"
            page.keyboard.press("Home")
            page.wait_for_timeout(90)
            assert focused() == entry, f"Home must reach the first row: {focused()!r}"

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()

@pytest.mark.timeout(300)
def test_a_full_unfinished_list_leaves_the_room_standing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Five rows must not eat the Room (F5, FIXED).

    The list used to render inside `.room-ask-container`, which is
    `position: sticky; bottom: 0` with an opaque backdrop
    (`web/src/features/project-room/project-room.css:306-313`), against a
    `.room-body` that reserves `padding-bottom: 96px` on an assumption that
    predates this story ("the well ~52px + padding + gap",
    `project-room.css:11-13`).  With the five rows the Room fetches, the
    sticky block covered every other section: no NEEDS YOU, no SOURCES, no
    RECEIPTS — a wall of unfinished asks over dead space.

    A ledger does not belong in a composer's foot.  The list is now a Room
    SECTION beside the other four, where the design's posture-6 grammar puts
    it, and the sticky foot is the well alone.
    """
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TASK_TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))
            _task_init_desk(page, url)
            project_id = _task_create_project(page, "Q4 platform", "hs200-41-sticky")
            for index in range(5):
                _save_ask(
                    page, project_id,
                    f"Unfinished ask number {index + 1} kept for the sticky measurement",
                )
            _task_open_room(page, project_id)
            page.get_by_test_id("room-unfinished").wait_for(timeout=15000)
            assert _rows(page).count() == 5
            # PHILO-17 sources (#1068, U10): a Room with no source opens Add
            # source at once, and the well goes into the flow while it is
            # open. This leg measures the Room in use: close it first.
            cancel = page.get_by_test_id("room-add-sources-cancel")
            if cancel.count():
                cancel.click()
                page.get_by_test_id("room-add-sources").wait_for(state="detached", timeout=10000)

            page.evaluate(
                """() => { const b = document.querySelector('.desk-surface-body');
                           b.scrollTop = b.scrollHeight; }"""
            )
            page.wait_for_timeout(400)
            _settle(page)
            measured = page.evaluate(
                """() => {
                    const body = document.querySelector('.desk-surface-body');
                    const container = document.querySelector('.room-ask-container');
                    const roomBody = document.querySelector('.room-body');
                    const cs = getComputedStyle(container);
                    return {
                      position: cs.position,
                      backdrop: cs.backgroundColor,
                      containerHeight: Math.round(
                        container.getBoundingClientRect().height),
                      bodyClientHeight: body.clientHeight,
                      reservedByRoomBody: getComputedStyle(roomBody).paddingBottom,
                    };
                }"""
            )
            share = round(
                100 * measured["containerHeight"] / measured["bodyClientHeight"]
            )
            print(
                f"[hs200-41] FINDING sticky foot with 5 rows: "
                f"{json.dumps(measured)} -> {share}% of the readable Room"
            )
            # PHILO-17 refit: the ask is in the flow (no sticky foot); the
            # rest of this leg still holds: five rows never grow the well.
            assert measured["position"] == "static", measured
            # The sticky foot is the WELL, and only the well: five rows must
            # not grow it. It stays inside the 96px `.room-body` reserves.
            assert measured["containerHeight"] <= 96, (
                f"the sticky foot must be the well alone: {measured}"
            )
            assert share <= 20, (
                f"the sticky foot must not eat the Room: {share}% of it"
            )
            # And the Room is still THERE behind it: its own sections are on
            # the glass with five unfinished rows present.
            standing = page.evaluate(
                """() => Array.from(
                     document.querySelectorAll('.room-body .surface-section-head h3'))
                   .map(el => el.textContent.trim())"""
            )
            print(f"[hs200-41] sections standing with 5 rows: {standing}")
            assert any(s.startswith("UNFINISHED") for s in standing), standing
            # The Room's OWN sections, not covered by a wall of asks. (Which
            # sections a Room draws depends on what it has; these two are what
            # this fixture's Room holds — RECEIPTS is absent because there are
            # none, which is A.8 doing its job.)
            assert "OPEN HERE" in standing, standing
            assert "SOURCES" in standing, standing

            # The sticky foot FLOATS over the body by design, so it can cover
            # the section nearest the bottom mid-scroll — as it always has for
            # whichever section was last. What must hold is that AT FULL
            # SCROLL nothing is left underneath it: `.room-body` reserves
            # `padding-bottom: 96px` for exactly that. Measured, not assumed.
            covered = page.evaluate(
                """() => {
                    const well = document.querySelector('.room-ask-container')
                      .getBoundingClientRect();
                    return Array.from(document.querySelectorAll(
                      '[data-testid="room-unfinished"] .surface-task-resume'))
                      .filter(row => {
                        const r = row.getBoundingClientRect();
                        return r.bottom > well.top + 1 && r.top < well.bottom - 1;
                      }).length;
                }"""
            )
            assert covered == 0, (
                f"{covered} unfinished row(s) still under the sticky foot at full scroll"
            )
            _shot_room(page, "taskresume-five-rows-sticky-1440")
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
