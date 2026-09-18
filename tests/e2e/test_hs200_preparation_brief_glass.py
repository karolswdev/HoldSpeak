"""HS-200-11 — the browser proof of the preparation brief (posture 3).

Everything below runs against a REAL booted hub under an isolated HOME.  The
Project is created through ``POST /api/projects``; the brief is prepared,
kept and re-read through the product's own routes
(``/api/projects/{id}/briefs/manifest``, ``.../briefs/route``,
``.../briefs/prepare``, ``.../briefs/stop``, ``/api/briefs/{id}``,
``/api/briefs/{id}/keep``).

What is seeded below the routes, and why, named honestly:

- The four Watches (GitHub read, Jira stale, Confluence credential-failed,
  the meeting Watch) are written through ``db.automations`` with their
  recorded ``last_success_at`` / ``last_error`` facts, because a source's
  coverage STATE is a recorded fact of its Watch row and no route sets
  ``last_error`` by hand.  The Room's own projection (`_read_room_sources`)
  reads them; nothing is faked above that seam.
- The decision records (one current, one superseded, the successor linked)
  are rows sourced from a meeting linked to the Project -- the join the
  Room itself uses.
- The MODEL is a fake OpenAI-compatible HTTP server on 127.0.0.1 (counsel's
  probe pattern): the endpoint is defined through the product's own
  model-library and assignment services, the hub's route resolves to it, the
  kernel admits and dispatches the request over the real wire, and the
  server answers whatever the leg needs.  So the `LAN`/host chip, the invoke
  receipt and every kernel operation are REAL; only the words are canned.
- The REFUSED legs are real end to end: a closed port (nothing answers), a
  hosted endpoint whose key the owner removed, a server that answers prose.

Shots land in ``…/assets/story-11-shots`` ONLY with
``HOLDSPEAK_WRITE_SHOTS=1`` (tracked evidence is never rewritten by a
plain run).
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    _api,
    _api_allow_error,
    _assert_clean,
    _boot,
    _ensure_build,
    _normal_chair,
    _settle,
)

pytest.importorskip("playwright.sync_api", reason="Preparation brief glass needs Playwright")

REPO = Path(__file__).resolve().parents[2]
SHOTS = REPO / "pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-11-shots"
WRITE_SHOTS = os.environ.get("HOLDSPEAK_WRITE_SHOTS") == "1"
TOKEN = "hs200-11-glass"
PURPOSE = "Architecture review, cut-over sequencing"

pytestmark = [pytest.mark.e2e]


# ── the desk, the Room, the shot ─────────────────────────────────────


def _init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)


def _create_project(page: Any, name: str, command_id: str) -> str:
    created = _api(page, "POST", "/api/projects", {
        "name": name,
        "description": "Seeded for the HS-200-11 browser proof.",
        "command_id": command_id,
    }, token=TOKEN)
    return created["project"]["id"]


def _open_room(page: Any, project_id: str) -> None:
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


def _room_window(page: Any) -> Any:
    return page.locator(".desk-surface-window").filter(
        has=page.locator('[data-testid="room-body"]')
    ).first


def _unclip(page: Any) -> None:
    """Let the Room window grow to its content for the shot: every scrolling
    ancestor of the body is opened to its scrollHeight, the previous inline
    sizes remembered so `_reclip` can hand them back."""
    page.evaluate(
        """() => {
          let el = document.querySelector('[data-testid="room-body"]');
          while (el) {
            const cs = getComputedStyle(el);
            const remember = () => {
              if (el.hasAttribute('data-hs-prev')) return;
              el.setAttribute('data-hs-prev', JSON.stringify({
                height: [el.style.getPropertyValue('height'), el.style.getPropertyPriority('height')],
                maxHeight: [el.style.getPropertyValue('max-height'), el.style.getPropertyPriority('max-height')],
                overflow: [el.style.getPropertyValue('overflow'), el.style.getPropertyPriority('overflow')],
              }));
            };
            if (/(auto|scroll)/.test(cs.overflowY) || /(auto|scroll)/.test(cs.overflow)) {
              remember();
              el.style.setProperty('height', el.scrollHeight + 'px', 'important');
              el.style.setProperty('max-height', 'none', 'important');
              el.style.setProperty('overflow', 'visible', 'important');
            }
            if (el.classList && el.classList.contains('desk-surface-window')) {
              remember();
              el.style.setProperty('height', 'auto', 'important');
              el.style.setProperty('max-height', 'none', 'important');
            }
            el = el.parentElement;
          }
        }"""
    )


def _reclip(page: Any) -> None:
    page.evaluate(
        """() => {
          for (const el of document.querySelectorAll('[data-hs-prev]')) {
            const prev = JSON.parse(el.getAttribute('data-hs-prev'));
            for (const [prop, key] of [['height', 'height'], ['max-height', 'maxHeight'], ['overflow', 'overflow']]) {
              const [value, priority] = prev[key];
              if (value) el.style.setProperty(prop, value, priority);
              else el.style.removeProperty(prop);
            }
            el.removeAttribute('data-hs-prev');
          }
        }"""
    )


def _shot_room(page: Any, name: str) -> Path | None:
    """Shoot the Room window at a tall viewport so nothing is clipped -- only
    when the flag says the tracked evidence may be rewritten."""
    if not WRITE_SHOTS:
        return None
    _settle(page)
    old = page.viewport_size
    page.set_viewport_size({"width": old["width"], "height": 2400})
    _unclip(page)
    _settle(page)
    page.wait_for_timeout(150)
    SHOTS.mkdir(parents=True, exist_ok=True)
    path = SHOTS / f"{name}.png"
    _room_window(page).screenshot(path=str(path))
    assert path.stat().st_size > 1_000, f"Shot {name} too small"
    _reclip(page)
    page.set_viewport_size(old)
    _settle(page)
    return path


# ── the seeds (recorded facts below the routes) ──────────────────────


def _seed_watch(
    project_id: str, connector: str, query_kind: str, query: dict[str, Any], *,
    snapshot: dict[str, Any] | None = None, last_success_at: str | None = None,
    next_evaluation_at: str | None = None, last_error: str | None = None,
) -> str:
    from holdspeak.db import get_database

    db = get_database()
    watch_id = f"w_{connector}_{uuid.uuid4().hex[:10]}"
    now_iso = datetime.now().isoformat(timespec="seconds")
    with db._connection() as conn:
        db.automations.create_watch_in_transaction(
            conn,
            watch_id=watch_id,
            connector_id=connector,
            query_kind=query_kind,
            name=f"{connector} {query_kind}",
            query_json=json.dumps(query, sort_keys=True),
            enabled=True,
            schema_version="WatchSpec@1",
            project_id=project_id,
            intent="Track",
            subject_kind=query_kind,
            trigger_kind="poll",
            trigger_json="{}",
            mode="yolo",
            state="active",
            revision=1,
            baseline_state="",
            test_state="",
            created_at=now_iso,
            updated_at=now_iso,
        )
        conn.execute(
            """UPDATE connector_watches
               SET snapshot_json = ?, last_success_at = ?, next_evaluation_at = ?, last_error = ?
               WHERE id = ?""",
            (
                json.dumps(snapshot) if snapshot is not None else None,
                last_success_at, next_evaluation_at, last_error, watch_id,
            ),
        )
    return watch_id


def _seed_sources(project_id: str) -> None:
    """GitHub read · Jira stale · Confluence credential-failed · meeting read."""
    from holdspeak.db import get_database
    from holdspeak.services.watch_service import ensure_meeting_watch

    # The store's stamps are naive UTC (`aware_iso` reads them as such, C8):
    # a local-clock seed reads hours off and a fresh row looks stale.
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    fresh = (now - timedelta(minutes=2)).isoformat(timespec="seconds")
    _seed_watch(
        project_id, "gh", "pull_requests", {"repository": "karolswdev/HoldSpeak"},
        snapshot={"entities": {
            "pr_1": {"state": "open", "title": "Cut-over runbook"},
            "pr_2": {"state": "open", "title": "Replica failover"},
        }},
        last_success_at=fresh,
        next_evaluation_at=(now + timedelta(hours=1)).isoformat(timespec="seconds"),
    )
    _seed_watch(
        project_id, "jira", "issues",
        {"projects": ["KAN"], "connection_ref": "acme.atlassian.net|me@acme.com"},
        snapshot={"entities": {}},
        last_success_at=(now - timedelta(hours=6)).isoformat(timespec="seconds"),
        next_evaluation_at=(now - timedelta(hours=5)).isoformat(timespec="seconds"),
    )
    _seed_watch(
        project_id, "confluence", "pages", {"connection_ref": "acme.atlassian.net|me@acme.com"},
        last_success_at=(now - timedelta(hours=1)).isoformat(timespec="seconds"),
        last_error="Confluence rejected the token (401)",
    )
    db = get_database()
    meeting_watch = ensure_meeting_watch(db, project_id)
    if meeting_watch and meeting_watch.get("id"):
        with db._connection() as conn:
            conn.execute(
                """UPDATE connector_watches
                   SET last_success_at = ?, snapshot_json = ?, next_evaluation_at = ?, last_error = NULL
                   WHERE id = ?""",
                (
                    fresh, json.dumps({"entities": {}}),
                    (now + timedelta(hours=1)).isoformat(timespec="seconds"),
                    meeting_watch["id"],
                ),
            )


def _seed_decisions(project_id: str) -> None:
    from holdspeak.db import get_database

    db = get_database()
    meeting_id = f"mtg_{uuid.uuid4().hex[:10]}"
    now_iso = datetime.now().isoformat(timespec="seconds")
    current = f"decrec_cur_{uuid.uuid4().hex[:8]}"
    old = f"decrec_old_{uuid.uuid4().hex[:8]}"
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, title, started_at, ended_at, created_at) VALUES (?, ?, ?, ?, ?)",
            (meeting_id, "Cut-over sync", now_iso, now_iso, now_iso),
        )
        conn.execute(
            "INSERT OR IGNORE INTO meeting_projects (meeting_id, project_id) VALUES (?, ?)",
            (meeting_id, project_id),
        )
        for rid, text, lifecycle in (
            (current, "Cut-over runs on the read replica first", "active"),
            (old, "Cut-over runs under a full freeze", "superseded"),
        ):
            conn.execute(
                """INSERT INTO decision_records
                   (id, decision_text, lifecycle, source_type, source_id, created_at, updated_at)
                   VALUES (?, ?, ?, 'meeting', ?, ?, ?)""",
                (rid, text, lifecycle, meeting_id, now_iso, now_iso),
            )
            conn.execute(
                """INSERT INTO decision_record_sources (id, record_id, source_type, source_ref, created_at)
                   VALUES (?, ?, 'meeting', ?, ?)""",
                (f"src_{rid}", rid, meeting_id, now_iso),
            )
        # The successor lineage the supersede verb writes.
        conn.execute(
            """INSERT INTO decision_record_revisions (id, record_id, field_name, old_value, new_value, created_at)
               VALUES (?, ?, 'successor_id', NULL, ?, ?)""",
            (f"rev_{old}", old, current, now_iso),
        )


def _seed_project_room(page: Any, command_id: str) -> str:
    project_id = _create_project(page, "Q4 platform", command_id)
    # The meeting link first: the meeting Watch exists only for a Room with
    # a linked meeting (`ensure_meeting_watch`, HS-175 C7).
    _seed_decisions(project_id)
    _seed_sources(project_id)
    return project_id


# ── the fake OpenAI-compatible server (counsel's probe pattern) ──────


class FakeLLM:
    """Answers any POST with an OpenAI chat completion carrying `self.reply`
    (a callable gets the request body), and logs every request it gets."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.reply: Any = "{}"
        self.delay_s = 0.0
        self.status = 200
        probe = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a: Any) -> None:
                pass

            def _send(self, body: dict[str, Any], status: int = 200) -> None:
                raw = json.dumps(body).encode()
                self.send_response(status)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_GET(self) -> None:
                probe.requests.append({"method": "GET", "path": self.path})
                self._send({"data": [{"id": "qwen3-35b", "object": "model"}], "object": "list"})

            def do_POST(self) -> None:
                n = int(self.headers.get("content-length") or 0)
                body = self.rfile.read(n).decode("utf-8", "replace") if n else ""
                probe.requests.append({"method": "POST", "path": self.path, "body": body})
                if probe.delay_s:
                    time.sleep(probe.delay_s)
                if probe.status != 200:
                    self._send({"error": {"message": "server exploded"}}, probe.status)
                    return
                text = probe.reply(body) if callable(probe.reply) else str(probe.reply)
                self._send({
                    "id": "cmpl-1", "object": "chat.completion", "model": "qwen3-35b",
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
                    "content": text,
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                })

        self.server = HTTPServer(("127.0.0.1", 0), H)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    @property
    def endpoint(self) -> str:
        return f"http://127.0.0.1:{self.port}/v1"

    @property
    def posts(self) -> list[dict[str, Any]]:
        """The completions calls -- the only requests that carry the purpose.
        (The hub's engine also GETs `/v1/models` to discover the endpoint;
        that is a reachability read with no payload.)"""
        return [r for r in self.requests if r["method"] == "POST"]

    def stop(self) -> None:
        self.server.shutdown()


def _define_route(home: Path, endpoint: str, profile_id: str, rev: int, *, requires_key: bool = False) -> None:
    """A REAL endpoint profile through the product's own model-library and
    assignment services, assigned to the brief capability (no hand-seeded id)."""
    from holdspeak.config import Config
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
    from holdspeak.services.model_library_service import ModelLibraryApplicationService
    from holdspeak.services.preparation_brief_service import PREPARATION_BRIEF_CAPABILITY

    owner = Principal(PrincipalKind.OWNER, "hs200-11-glass")
    db = get_database()
    setup = InferenceSetupApplicationService(db, config_provider=Config, home_provider=lambda: home)
    acquisition = InferenceAcquisitionApplicationService(
        db, setup_service=setup, model_root=home / "models", home_provider=lambda: home,
    )
    ModelLibraryApplicationService(db, setup_service=setup, acquisition_service=acquisition).define_endpoint(
        owner,
        {
            "request_id": f"hs200-11-endpoint-{profile_id}-{rev}",
            "profile_id": profile_id,
            "expected_profile_revision": 0,
            "label": f"Probe {profile_id}",
            "provider_family": "openai_compatible" if requires_key else "private_endpoint",
            "model": "qwen3-35b",
            "endpoint": endpoint,
            "requires_key": requires_key,
        },
        {"value": "sk-glass-key"} if requires_key else None,
    )
    assignments = InferenceAssignmentService(db)
    assignments.set_assignment(owner, {
        "command_id": f"hs200-11-global-{rev}", "expected_revision": rev - 1,
        "scope": {"kind": "global"},
        "entries": [{"profile_id": profile_id, "profile_revision": 1}],
    })
    assignments.set_assignment(owner, {
        "command_id": f"hs200-11-capability-{rev}", "expected_revision": rev - 1,
        "scope": {"kind": "capability", "capability_id": PREPARATION_BRIEF_CAPABILITY},
        "entries": [{"profile_id": profile_id, "profile_revision": 1}],
    })


def _kernel_ops(tmp_path: Path) -> list[tuple[str, str]]:
    conn = sqlite3.connect(str(tmp_path / "holdspeak.db"))
    rows = conn.execute(
        "SELECT name, state FROM kernel_operations WHERE name LIKE 'inference%' ORDER BY created_at"
    ).fetchall()
    conn.close()
    return [(str(r[0]), str(r[1])) for r in rows]


def _board_reply(body: str) -> str:
    """The board's claim mix, cited to the REAL refs the prompt carried:
    the current decision verbatim (DECISION · SUPPORTED · ACCEPTED), the
    superseded decision (goes to the SUPERSEDED ledger), the GitHub source
    (LINKED with typed unknowns), an uncited sentence (NO SOURCE), and two
    priorities over the bound (NOT INCLUDED)."""
    prompt = json.loads(body).get("messages", [{}])[-1].get("content", "") if body.startswith("{") else body
    import re

    refs = re.findall(r"(decision_record:[A-Za-z0-9_]+|source:[A-Za-z0-9_]+)", prompt)
    current = next((r for r in refs if "decrec_cur_" in r), "")
    old = next((r for r in refs if "decrec_old_" in r), "")
    gh = next((r for r in refs if r.startswith("source:w_gh_")), "")
    return json.dumps({
        "priorities": [
            {"text": "Cut-over runs on the read replica first", "cited_refs": [current]},
            {"text": "Cut-over runs under a full freeze", "cited_refs": [old]},
            {"text": "Two open pull requests wait on the runbook", "cited_refs": [gh]},
            {"text": "Rehearse the rollback on the replica", "cited_refs": [gh]},
            {"text": "Extra priority four", "cited_refs": [gh]},
            {"text": "Extra priority five", "cited_refs": [gh]},
        ],
        "questions": [
            {"text": "Priya expects the cut-over at 95% by 2026-12-31", "cited_refs": [gh]},
            {"text": "Sprint velocity improved over the trailing average", "cited_refs": []},
        ],
        "obligations": [],
    })


# ── locators ─────────────────────────────────────────────────────────


def _enter_prepare(page: Any) -> None:
    page.get_by_test_id("room-ask-result").locator("select").select_option("brief")
    page.get_by_test_id("prepare-posture").wait_for(timeout=15000)
    page.get_by_test_id("prepare-coverage").wait_for(timeout=15000)
    _settle(page)


def _purpose(page: Any) -> Any:
    return page.get_by_role("textbox", name="Purpose")


def _chip_words(locator: Any) -> str:
    chip = locator.locator(".surface-state-chip").first
    return (chip.get_attribute("aria-label") or chip.inner_text()).strip()


def _texts(page: Any, testid: str) -> list[str]:
    return [t.strip() for t in page.get_by_test_id(testid).all_inner_texts()]


def _section_captions(page: Any) -> list[str]:
    return page.evaluate(
        """() => Array.from(document.querySelectorAll(
             '[data-testid="prepare-posture"] .surface-section-head h3')).map(el => el.textContent.trim())"""
    )


def _button_names(page: Any) -> list[dict[str, str]]:
    return page.evaluate(
        """() => Array.from(document.querySelectorAll('[data-testid="prepare-posture"] button')).map(b => ({
              name: (b.getAttribute('aria-label') || b.textContent || '').trim(),
              cls: b.className,
            }))"""
    )


def _assert_refused_drawing(page: Any, testid: str) -> None:
    verb = page.get_by_test_id(testid)
    assert verb.is_disabled(), f"{testid} must be native disabled"
    assert verb.get_attribute("aria-disabled") == "true"
    style = verb.evaluate("el => { const s = getComputedStyle(el); return {border: s.borderTopStyle, cursor: s.cursor}; }")
    assert style["border"] == "dashed", f"a refused primary is drawn dashed, got {style}"
    assert style["cursor"] == "not-allowed", style


def _wait_refused(page: Any, timeout: int = 120000) -> None:
    page.locator('[data-testid="prepare-posture"][data-posture="refused"]').wait_for(timeout=timeout)
    _settle(page)


# ── leg 1: the prepare face — a purpose, no calendar, coverage first ─


@pytest.mark.timeout(300)
@pytest.mark.parametrize("width", [1440, 393])
def test_prepare_face_states_coverage_before_the_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """P3Prepare: `COVERAGE · 2 OF 4` in the head, ONE `SOURCES 4` ledger
    with both gaps marked and their repair verbs (a 401 reads CREDENTIAL
    EXPIRED · CONFLUENCE), `CARRIED FORWARD`, the route READY with the
    profile's own model label and host, and a purpose that needs no
    calendar (AC1, AC2's pre-run half, P1-1, P2 i, P2 iv)."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    llm = FakeLLM()
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width >= 1440 else 852})
            page.on("pageerror", lambda e: errors.append(str(e)))
            _init_desk(page, url)
            project_id = _seed_project_room(page, f"hs200-11-prepare-{width}")
            _define_route(tmp_path / "home", llm.endpoint, "probe-llm", 1)
            _open_room(page, project_id)

            # The Room's well cycles Result → Preparation brief; no calendar is asked for.
            _enter_prepare(page)
            assert page.get_by_test_id("prepare-head-name").inner_text().strip() == "Prepare a brief"
            assert _chip_words(page.get_by_test_id("prepare-coverage")) == "COVERAGE · 2 OF 4"
            assert page.get_by_test_id("prepare-coverage").get_attribute("data-complete") == "false"
            assert page.get_by_test_id("prepare-purpose-by-hand").inner_text().strip() == "PURPOSE SET BY HAND"
            assert page.get_by_test_id("prepare-no-calendar").inner_text().strip() == "NO CALENDAR"
            # P1-1: the route beside the verb reads the leg's own revisions --
            # the profile's model label, never the engine kind.
            assert page.get_by_test_id("prepare-route").get_attribute("data-state") == "ready"
            assert page.get_by_test_id("prepare-route-model").inner_text().strip() == "QWEN3 35B"
            assert "127.0.0.1" in page.get_by_test_id("prepare-route").inner_text()
            assert llm.posts == [], "the route probe sends nothing"

            captions = _section_captions(page)
            assert captions[0] == "SOURCES 4", captions
            assert "CARRIED FORWARD 1" in captions, captions
            states = [
                (el.get_attribute("data-state") or "")
                for el in page.get_by_test_id("prepare-source-state").all()
            ]
            assert sorted(states) == ["available", "available", "failed", "stale"], states
            repairs = _texts(page, "prepare-source-repair")
            assert sorted(repairs) == ["Reconnect", "Retry"], repairs
            # P2 i: one failure class, one token, one verb.
            chips = [_chip_words(el) for el in page.get_by_test_id("prepare-source-state").all()]
            assert "CREDENTIAL EXPIRED · CONFLUENCE" in chips, chips
            observed = _texts(page, "prepare-source-observed")
            assert len(observed) == 4 and all(t.startswith("OBSERVED ") for t in observed), observed

            # An empty purpose: `Prepare` is drawn refused, not merely dimmed.
            _assert_refused_drawing(page, "prepare-verb")
            _shot_room(page, f"prepare-empty-{width}")

            long_purpose = (
                "Architecture review, cut-over sequencing, rollback rehearsal, DNS plan, "
                "and the Saturday window with Finance and Payments stakeholders"
            )
            _purpose(page).fill(long_purpose)
            assert not page.get_by_test_id("prepare-verb").is_disabled()
            # P2 iv: the purpose WRAPS -- a textarea that grew, nothing clipped.
            field = _purpose(page).evaluate("el => ({tag: el.tagName, sw: el.scrollWidth, cw: el.clientWidth, sh: el.scrollHeight, ch: el.clientHeight})")
            assert field["tag"] == "TEXTAREA", field
            assert field["sw"] <= field["cw"] + 1, f"the purpose clips horizontally: {field}"
            assert field["sh"] <= field["ch"] + 2, f"the purpose clips vertically: {field}"
            # The purpose persists (sessionStorage) before anything is sent.
            stored = page.evaluate("() => sessionStorage.getItem('hs.room.prepareDrafts')")
            assert stored and "rollback rehearsal" in stored, stored

            # No page-level overflow at this width; every verb is named.
            _assert_clean(page, errors)
            unnamed = [b for b in _button_names(page) if not b["name"]]
            assert not unnamed, unnamed
            browser.close()
    finally:
        llm.stop()
        server.stop()


# ── leg 2: running, then the kept brief with its claims, over the REAL wire ─


@pytest.mark.timeout(300)
@pytest.mark.parametrize("width", [1440, 393])
def test_running_then_kept_brief_with_claims_and_not_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """P3Brief / P3BriefPhone over a REAL dispatch to the fake server: the
    document, `CLAIMS` on three axes with typed unknowns, `NO SOURCE` +
    `Find support`, `SUPERSEDED 1` with its successor (P1-2), `NOT INCLUDED
    2` (P1-3), `NOT READ 2` carrying the state chip and the repair, the
    LAN egress and receipt from the wire, `Keep` -- then the kept brief
    re-read by id with its manifest (AC2, AC3, AC4)."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    llm = FakeLLM()
    llm.reply = _board_reply
    llm.delay_s = 6.0
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width >= 1440 else 852})
            page.on("pageerror", lambda e: errors.append(str(e)))
            _init_desk(page, url)
            project_id = _seed_project_room(page, f"hs200-11-brief-{width}")
            _define_route(tmp_path / "home", llm.endpoint, "probe-llm", 1)
            _open_room(page, project_id)
            _enter_prepare(page)
            _purpose(page).fill(PURPOSE)
            page.get_by_test_id("prepare-verb").click()

            # The run: a real plan with `Stop` kept, the egress beside it.
            page.get_by_test_id("prepare-running").wait_for(timeout=10000)
            assert page.get_by_role("button", name="Stop", exact=True).count() == 1
            _shot_room(page, f"prepare-running-{width}")

            page.get_by_test_id("prepare-document").wait_for(timeout=60000)
            _settle(page)
            assert len(llm.posts) == 1, llm.requests
            assert "read replica" in llm.posts[0]["body"], "the decision travelled in the prompt"
            assert page.get_by_test_id("prepare-head-name").inner_text().strip() == "Brief ready"
            assert _chip_words(page.get_by_test_id("prepare-lifecycle")) == "DRAFT"
            assert page.get_by_test_id("prepare-manifest-token").inner_text().strip() == "MANIFEST · REV 1"
            assert _chip_words(page.get_by_test_id("prepare-coverage")) == "COVERAGE · 2 OF 4"
            assert page.get_by_test_id("prepare-prepared").inner_text().strip().startswith("PREPARED ")

            # The document is the bounded outline, in caption-step headings;
            # the superseded decision is NOT a line of it (P1-2).
            doc = page.get_by_test_id("prepare-document").inner_text()
            assert "DECIDE TODAY" in doc and "ASK THEM" in doc, doc
            assert "Sprint velocity improved" in doc
            assert "full freeze" not in doc, doc
            assert "Extra priority" not in doc, doc

            captions = _section_captions(page)
            assert "CLAIMS 5" in captions and "SUPERSEDED 1" in captions and "NOT READ 2" in captions, captions

            # The carried decision keeps its axes; the model's own prose is
            # LINKED at best; the uncited sentence is UNSUPPORTED (C2).
            kinds = _texts(page, "prepare-claim-kind")
            assert kinds == ["DECISION", "INFERENCE", "INFERENCE", "INFERENCE", "INFERENCE"], kinds
            support = [_chip_words(el) for el in page.get_by_test_id("prepare-claim-support").all()]
            assert support == ["SUPPORTED", "LINKED", "LINKED", "LINKED", "UNSUPPORTED"], support
            acceptance = [_chip_words(el) for el in page.get_by_test_id("prepare-claim-acceptance").all()]
            assert acceptance == ["ACCEPTED", "UNREVIEWED", "UNREVIEWED", "UNREVIEWED", "UNREVIEWED"], acceptance
            unknowns = [_chip_words(el) for el in page.get_by_test_id("prepare-claim-unknown").all()]
            assert "DEADLINE 2026-12-31 · NO SOURCE" in unknowns, unknowns
            assert "NUMBER 95% · NO SOURCE" in unknowns, unknowns
            # The NAME rule: no known person on this desk, no false NAME chip.
            assert not [u for u in unknowns if u.startswith("NAME ")], unknowns
            # No raw id on the face (162's law): the ref chip names the source.
            ref_chips = _texts(page, "prepare-claim-ref")
            assert ref_chips[0].startswith("DEC "), ref_chips
            assert ref_chips[1].lower() == "karolswdev/holdspeak", ref_chips
            assert not any("decrec" in r.lower() or "w_gh" in r.lower() for r in ref_chips), ref_chips
            # No source, no source chip: `NO SOURCE` + `Find support`, and no
            # `Open source` that opens nothing.
            assert page.get_by_test_id("prepare-claim-no-source").count() == 1
            assert page.get_by_test_id("prepare-claim-find").count() == 1
            assert page.get_by_test_id("prepare-claim-open").count() == 4
            assert page.get_by_role("button", name="Write it myself").count() == 0

            # P1-2: the superseded citation, its successor linked.
            assert page.get_by_test_id("prepare-superseded-row").count() == 1
            assert _chip_words(page.get_by_test_id("prepare-superseded-chip")).startswith("SUPERSEDED BY DEC ")
            assert page.get_by_test_id("prepare-superseded-open").count() == 1

            # P1-3: what the bound left out is named, with why.
            page.get_by_role("button", name="NOT INCLUDED 2").click()
            page.get_by_test_id("prepare-not-included").wait_for(timeout=5000)
            whys = _texts(page, "prepare-not-included-why")
            assert whys and all(w.startswith("OVER THE BOUND OF 3") for w in whys), whys
            assert _texts(page, "prepare-not-included-token") == ["OVER THE BOUND"]

            # NOT READ names each omitted source with its state and its repair.
            not_read = page.get_by_test_id("prepare-not-read-row")
            assert not_read.count() == 2
            not_read_states = sorted(
                (el.get_attribute("data-state") or "")
                for el in page.locator('[data-testid="prepare-not-read"] [data-testid="prepare-source-state"]').all()
            )
            assert not_read_states == ["failed", "stale"], not_read_states
            reasons = page.locator('[data-testid="prepare-not-read"] [data-testid="prepare-source-reason"]').all_inner_texts()
            assert all(r.endswith("· OMITTED") for r in reasons), reasons

            # P2 ii: the MANIFEST disclosure lists what was READ and what was
            # carried -- and draws no NOT READ row a second time.
            page.get_by_test_id("prepare-open-sources").click()
            page.get_by_test_id("prepare-manifest-sources").wait_for(timeout=5000)
            read_states = [
                (el.get_attribute("data-state") or "")
                for el in page.locator('[data-testid="prepare-manifest-sources"] [data-testid="prepare-source-state"]').all()
            ]
            assert read_states == ["available", "available"], read_states
            assert page.get_by_test_id("prepare-manifest-decision").count() == 2
            assert page.get_by_test_id("prepare-not-read-row").count() == 2, "omitted rows drawn once"
            page.get_by_test_id("prepare-open-sources").click()

            # Egress where egress happened -- from the WIRE; the receipt names the model.
            egress = page.get_by_test_id("prepare-footer-egress").inner_text().strip()
            assert egress == "127.0.0.1", egress
            receipt = page.get_by_test_id("prepare-footer-receipt").inner_text().strip()
            assert receipt.startswith("QWEN3 35B"), receipt
            assert _kernel_ops(tmp_path)[-1] == ("inference.invoke", "succeeded"), _kernel_ops(tmp_path)

            # P2 v: Discard exists on a draft (ConfirmVerb, in place).
            assert page.get_by_test_id("prepare-discard").count() == 1

            # Keep: focus stays on Keep, the head token becomes KEPT, Keep is drawn refused.
            keep = page.get_by_test_id("prepare-keep")
            keep.click()
            page.locator('[data-testid="prepare-lifecycle"] .surface-state-chip[aria-label="KEPT"]').wait_for(timeout=10000)
            _settle(page)
            assert page.get_by_test_id("prepare-head-name").inner_text().strip() == "Brief ready"
            assert keep.get_attribute("aria-disabled") == "true"
            assert keep.evaluate("el => getComputedStyle(el).borderTopStyle") == "dashed"
            assert page.evaluate("() => document.activeElement && document.activeElement.dataset.testid") == "prepare-keep"
            assert page.get_by_test_id("prepare-discard").count() == 0, "a kept brief is not discarded"
            before = _api(page, "GET", f"/api/projects/{project_id}/briefs?lifecycle=kept", token=TOKEN)["briefs"]
            keep.dispatch_event("click")  # a second press writes nothing
            assert _api(page, "GET", f"/api/projects/{project_id}/briefs?lifecycle=kept", token=TOKEN)["briefs"] == before
            _shot_room(page, f"brief-kept-{width}")

            # The kept brief, re-read by id, carries its manifest and its freeze.
            kept = _api(page, "GET", f"/api/briefs/{before[0]['id']}", token=TOKEN)["brief"]
            assert kept["lifecycle"] == "kept" and kept["integrity"] == "verified"
            assert kept["project_id"] == project_id
            manifest = kept["manifest"]
            assert manifest["coverage"] == {"expected": 4, "available": 2, "complete": False}
            assert sorted(o["state"] for o in manifest["omitted"]) == ["failed", "stale"]
            assert sorted(d["lifecycle"] for d in manifest["decisions"]) == ["current", "superseded"]
            assert next(d for d in manifest["decisions"] if d["lifecycle"] == "superseded")["successor_ref"]
            assert len(manifest["not_included"]) == 2
            assert manifest["calendar"] == {"present": False}
            assert kept["generator_host"] == "127.0.0.1"

            # The way back: the Project button returns to the Room, and the
            # Room lists the kept brief with `Open` (AC4).
            page.get_by_test_id("prepare-project-button").click()
            page.get_by_test_id("room-briefs").wait_for(timeout=15000)
            page.get_by_test_id("room-brief-open").click()
            page.get_by_test_id("prepare-document").wait_for(timeout=15000)
            assert _chip_words(page.get_by_test_id("prepare-lifecycle")) == "KEPT"

            # P1-5: `Find support` opens Desk memory WITH the sentence, searched.
            page.get_by_test_id("prepare-claim-find").first.click()
            page.get_by_test_id("desk-memory-body").wait_for(timeout=15000)
            _settle(page)
            filled = page.evaluate(
                """() => Array.from(document.querySelectorAll('[data-testid="desk-memory-body"] input'))
                       .map(i => i.value).filter(Boolean)"""
            )
            assert filled and "Sprint velocity" in filled[0], filled

            _assert_clean(page, errors)
            unnamed = [b for b in _button_names(page) if not b["name"]]
            assert not unnamed, unnamed
            browser.close()
    finally:
        llm.stop()
        server.stop()


# ── leg 3: the refusal keeps the purpose; the receipt tells the truth ─


@pytest.mark.timeout(300)
@pytest.mark.parametrize("width", [1440, 393])
def test_unavailable_model_refuses_and_keeps_the_purpose(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """P3PrepareNoModel, REAL: an endpoint at a closed port.  `Cannot draft`,
    `ENDPOINT UNREACHABLE`, `PURPOSE KEPT`, the invoke receipt (a kernel
    operation exists, so the face says SENT, not NOTHING SENT -- P0),
    `Prepare` drawn refused, `Set up model`, no `Write it myself`, the
    coverage token and both marked rows kept -- and no brief row written;
    then return-to-task lands focus on Prepare (P2 iii)."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width >= 1440 else 852})
            page.on("pageerror", lambda e: errors.append(str(e)))
            _init_desk(page, url)
            project_id = _seed_project_room(page, f"hs200-11-refused-{width}")
            _define_route(tmp_path / "home", "http://127.0.0.1:1/v1", "closed-port", 1)

            route = _api(page, "GET", f"/api/projects/{project_id}/briefs/route", token=TOKEN)["route"]
            assert route["state"] == "ready", route  # the probe reads the route; it sends nothing
            assert route["host"] == "127.0.0.1" and route["model"] == "QWEN3 35B", route
            assert route["boundary"] == "private_network", route

            _open_room(page, project_id)
            _enter_prepare(page)
            _purpose(page).fill(PURPOSE)
            started = time.monotonic()
            page.get_by_test_id("prepare-verb").click()
            _wait_refused(page)
            print(f"[hs200-11] closed-port dispatch refused in {time.monotonic() - started:.1f}s")

            assert page.get_by_test_id("prepare-head-name").inner_text().strip() == "Cannot draft"
            assert page.get_by_test_id("prepare-purpose-kept").inner_text().strip() == "PURPOSE KEPT"
            # P0: an inference.invoke operation exists (the kernel dispatched),
            # so the head, the footer and the receipt all say SENT.
            ops = _kernel_ops(tmp_path)
            assert ops and ops[-1][0] == "inference.invoke", ops
            sent = page.get_by_test_id("prepare-sent-token").inner_text().strip()
            assert sent == "SENT · 127.0.0.1 · NOT ANSWERED", sent
            assert page.get_by_test_id("prepare-footer-egress").inner_text().strip() == "127.0.0.1"
            assert page.get_by_test_id("prepare-footer-receipt").inner_text().strip() == sent
            assert page.get_by_test_id("prepare-route").get_attribute("data-state") == "unreachable"
            assert _chip_words(page.get_by_test_id("prepare-route")) == "ENDPOINT UNREACHABLE"
            assert page.get_by_test_id("prepare-route-detail").inner_text().strip() == "QWEN3 35B · 127.0.0.1"
            # The purpose is still in the field, and still in session custody.
            assert _purpose(page).input_value() == PURPOSE
            stored = page.evaluate("() => sessionStorage.getItem('hs.room.prepareDrafts')")
            assert stored and PURPOSE in stored
            # The repair is the existing setup path; `Write it myself` is dropped.
            assert page.get_by_test_id("prepare-set-up-model").inner_text().strip() == "Set up model"
            assert page.get_by_role("button", name="Write it myself").count() == 0
            _assert_refused_drawing(page, "prepare-verb")
            # A failed face may not clear a known gap by omission.
            assert _chip_words(page.get_by_test_id("prepare-coverage")) == "COVERAGE · 2 OF 4"
            assert sorted(_texts(page, "prepare-source-repair")) == ["Reconnect", "Retry"]
            _shot_room(page, f"prepare-refused-{width}")

            # Nothing was written for a refused run.
            assert _api(page, "GET", f"/api/projects/{project_id}/briefs", token=TOKEN)["briefs"] == []

            # P2 iii: `Set up model` remembers Prepare although it is
            # native-disabled; the return-to-task signal re-reads the route
            # and lands focus on Prepare once it is enabled.
            page.get_by_test_id("prepare-set-up-model").click()
            page.wait_for_timeout(800)
            page.evaluate("() => window.dispatchEvent(new Event('holdspeak:settings-updated'))")
            page.locator('[data-testid="prepare-posture"][data-posture="prepare"]').wait_for(timeout=10000)
            page.wait_for_timeout(500)
            assert page.evaluate(
                "() => document.activeElement && document.activeElement.getAttribute('data-testid')"
            ) == "prepare-verb"

            # A reload keeps the purpose: the Room reopens, Result → brief finds his words.
            page.reload(wait_until="load")
            _normal_chair(page)
            page.get_by_test_id("room-body").wait_for(timeout=20000)
            _enter_prepare(page)
            assert _purpose(page).input_value() == PURPOSE

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


# ── leg 4: a request that WAS sent and answered prose (counsel's probe E) ─


@pytest.mark.timeout(300)
def test_a_sent_and_answered_request_is_never_reported_as_nothing_sent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """P0, the fence: the fake server answers prose.  The kernel operation
    SUCCEEDED, so the face says `SENT · 127.0.0.1 · NOTHING USABLE RECEIVED`
    in the head and the receipt, and the footer carries the target's egress
    chip.  `NOTHING SENT` appears nowhere."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    llm = FakeLLM()
    llm.reply = "Sure! Here is a brief in prose: decide the cut-over window today."
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            _init_desk(page, url)
            project_id = _seed_project_room(page, "hs200-11-sent")
            _define_route(tmp_path / "home", llm.endpoint, "probe-llm", 1)
            _open_room(page, project_id)
            _enter_prepare(page)
            _purpose(page).fill(PURPOSE)
            page.get_by_test_id("prepare-verb").click()
            _wait_refused(page, timeout=60000)
            assert len(llm.posts) == 1, llm.requests
            assert _kernel_ops(tmp_path)[-1] == ("inference.invoke", "succeeded"), _kernel_ops(tmp_path)
            head = page.get_by_test_id("prepare-head").inner_text()
            assert "NOTHING SENT" not in head, head
            assert page.get_by_test_id("prepare-sent-token").inner_text().strip() == "SENT · 127.0.0.1 · NOTHING USABLE RECEIVED"
            assert page.get_by_test_id("prepare-footer-egress").inner_text().strip() == "127.0.0.1"
            assert page.get_by_test_id("prepare-footer-receipt").inner_text().strip() == "SENT · 127.0.0.1 · NOTHING USABLE RECEIVED"
            assert _chip_words(page.get_by_test_id("prepare-route")) == "OUTPUT UNUSABLE"
            assert _api(page, "GET", f"/api/projects/{project_id}/briefs", token=TOKEN)["briefs"] == []

            # An HTTP 500 from the target: still SENT, still not answered.
            llm.status = 500
            page.get_by_test_id("prepare-set-up-model").click()
            page.evaluate("() => window.dispatchEvent(new Event('holdspeak:settings-updated'))")
            page.locator('[data-testid="prepare-posture"][data-posture="prepare"]').wait_for(timeout=10000)
            page.get_by_test_id("prepare-verb").click()
            _wait_refused(page, timeout=90000)
            assert page.get_by_test_id("prepare-sent-token").inner_text().strip() == "SENT · 127.0.0.1 · NOT ANSWERED"
            assert page.get_by_test_id("prepare-footer-egress").inner_text().strip() == "127.0.0.1"
            browser.close()
    finally:
        llm.stop()
        server.stop()


# ── leg 5: KEY NOT SET through the real ids ─────────────────────────


@pytest.mark.timeout(300)
def test_a_hosted_endpoint_without_its_key_is_key_not_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """P1-1: a REAL hosted endpoint defined through the product's services;
    the owner removes its key; the route reads KEY NOT SET before a byte
    leaves, `Prepare` is drawn refused, and nothing is written."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            _init_desk(page, url)
            project_id = _seed_project_room(page, "hs200-11-key")
            _define_route(tmp_path / "home", "https://api.example.test/v1", "hosted-llm", 1, requires_key=True)
            assert _api(page, "GET", f"/api/projects/{project_id}/briefs/route", token=TOKEN)["route"]["state"] == "ready"
            # The owner removes the key from the SAME slot the runner reads.
            from holdspeak.profile_key_store import _default_profile_key_store

            conn = sqlite3.connect(str(tmp_path / "holdspeak.db"))
            slot = conn.execute(
                "SELECT secret_slot FROM deployment_revisions WHERE secret_slot != '' ORDER BY rowid DESC LIMIT 1"
            ).fetchone()[0]
            conn.close()
            _default_profile_key_store().delete(slot)
            route = _api(page, "GET", f"/api/projects/{project_id}/briefs/route", token=TOKEN)["route"]
            assert route["state"] == "key_missing" and route["token"] == "KEY NOT SET", route
            assert route["host"] == "api.example.test" and route["model"] == "QWEN3 35B", route

            _open_room(page, project_id)
            _enter_prepare(page)
            _purpose(page).fill(PURPOSE)
            assert _chip_words(page.get_by_test_id("prepare-route")) == "KEY NOT SET"
            _assert_refused_drawing(page, "prepare-verb")
            assert page.get_by_test_id("prepare-set-up-model").count() == 1
            status, _payload = _api_allow_error(
                page, "POST", f"/api/projects/{project_id}/briefs/prepare", {"purpose": PURPOSE}, token=TOKEN,
            )
            assert status == 409
            assert _kernel_ops(tmp_path) == [], "no request may leave without the key"
            browser.close()
    finally:
        server.stop()


# ── leg 6: Stop stops — no orphan draft ─────────────────────────────


@pytest.mark.timeout(300)
def test_stop_leaves_no_orphan_draft(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """P1-4: the fake server takes 8 s; the owner presses Stop at 1 s.  The
    hub cancels the operation under the attempt; if the run still completes,
    it writes NO draft, and the face says the request had left."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    llm = FakeLLM()
    llm.reply = _board_reply
    llm.delay_s = 8.0
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            _init_desk(page, url)
            project_id = _seed_project_room(page, "hs200-11-stop")
            _define_route(tmp_path / "home", llm.endpoint, "probe-llm", 1)
            _open_room(page, project_id)
            _enter_prepare(page)
            _purpose(page).fill(PURPOSE)
            page.get_by_test_id("prepare-verb").click()
            page.get_by_test_id("prepare-running").wait_for(timeout=10000)
            page.wait_for_timeout(1000)
            page.get_by_role("button", name="Stop", exact=True).click()
            page.locator('[data-testid="prepare-posture"][data-posture="prepare"]').wait_for(timeout=5000)
            page.get_by_test_id("prepare-stopped").wait_for(timeout=10000)
            token = page.get_by_test_id("prepare-stopped").inner_text().strip()
            assert token.startswith("STOPPED · REQUEST HAD LEFT"), token
            time.sleep(10)  # let the hub's run complete after the stop
            listed = _api(page, "GET", f"/api/projects/{project_id}/briefs", token=TOKEN)["briefs"]
            assert listed == [], [(b["id"], b["lifecycle"]) for b in listed]
            # The purpose is still his.
            assert _purpose(page).input_value() == PURPOSE
            browser.close()
    finally:
        llm.stop()
        server.stop()


# ── kept for counsel's probes (`/tmp/muaddib-xx/counsel11/probe_hub.py`) ──
#
# No leg above uses it: the kept-brief legs dispatch over the REAL wire to
# `FakeLLM`.  Counsel's probe C imports this monkeypatch helper; it stays so
# the probe can run before and after a fix.


def _install_fake_model(monkeypatch: pytest.MonkeyPatch, *, delay_s: float = 0.0) -> None:
    from holdspeak.services import preparation_brief_service as svc

    def fake_route_state(self: Any) -> dict[str, Any]:
        return {
            "state": svc.ROUTE_READY, "token": "READY", "host": "192.168.1.43",
            "model": "QWEN3 35B", "boundary": "private_network", "reason": "",
            "repair": "Set up model", "invoke": svc.empty_invoke_receipt(),
        }

    def fake_draft(self: Any, principal: Any, purpose: str, inventory: list[Any], manifest: dict[str, Any], route: dict[str, Any], **kw: Any):
        if delay_s:
            time.sleep(delay_s)
        current = next(d["ref"] for d in manifest["decisions"] if d["lifecycle"] == "current")
        gh = next(s for s in manifest["sources"] if s["kind"] == "github")
        gh_ref = f"source:{gh['source_id']}"
        canned = json.dumps({
            "priorities": [
                {"text": "Cut-over runs on the read replica first", "cited_refs": [current]},
                {"text": "Two open pull requests wait on the runbook", "cited_refs": [gh_ref]},
            ],
            "questions": [
                {"text": "Priya expects the cut-over at 95% by 2026-12-31", "cited_refs": [gh_ref]},
                {"text": "Sprint velocity improved over the trailing average", "cited_refs": []},
            ],
            "obligations": [],
        })
        parsed = svc.parse_model_output(
            canned, frozenset({current, gh_ref}),
            {current: "Cut-over runs on the read replica first", gh_ref: " ".join([gh["label"], *gh["tokens"]])},
            inventory, manifest,
        )
        assert parsed is not None
        return parsed, "model:fake-assignment", "192.168.1.43", "QWEN3 35B"

    monkeypatch.setattr(svc.PreparationBriefService, "_route_state", fake_route_state)
    monkeypatch.setattr(svc.PreparationBriefService, "_draft_with_model", fake_draft)
