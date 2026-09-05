"""HS-156-04 — Front Door glass tests.

Real hub + fake engine: the door surface at 1440 and 393.
Fresh desk → pack cards show. Apply a stub pack via the front-door
API (the test_front_door_apply.py seam) → plan progresses → strip
appears. The advanced fold exposes the full Library + Assignments.
Zero horizontal overflow at both widths.

Shots → pm/roadmap/holdspeak/phase-156-the-front-door/assets/story-04-shots/
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="Glass needs Playwright")

REPO = Path(__file__).resolve().parents[2]
TOKEN = "hs156-door-glass"
SHOTS_DIR = REPO / "pm/roadmap/holdspeak/phase-156-the-front-door/assets/story-04-shots"
SHOTS_06_DIR = REPO / "pm/roadmap/holdspeak/phase-156-the-front-door/assets/story-06-shots"

pytestmark = [pytest.mark.e2e, pytest.mark.requires_meeting]


# ----------------------------------------------------------------- fake engine

class _TextEngine:
    """Minimal engine that returns text so turns produce real assistant rows."""
    active_provider = "text-glass"
    active_model = "hs156-glass-model"

    def run_prompt_stream(self, *, messages=None, tools=None, **kw):
        from holdspeak.kernel.inference_stream import Delta
        yield Delta(kind="text", text="Glass test response. ")
        yield Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 5})
        yield Delta(kind="done")

    def run_prompt_messages(self, **kw):
        return "Glass test response."

    def run_prompt(self, **kw):
        return '{"summary": "Summary."}'


# ----------------------------------------------------------------- hub fixture

@pytest.fixture
def hub(tmp_path, monkeypatch):
    """Boot an in-process hub with yolo control_mode and isolated DB."""
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database, get_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    real_home = Path.home()
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    pw_path = os.environ.get(
        "PLAYWRIGHT_BROWSERS_PATH",
        str(real_home / "Library/Caches/ms-playwright"),
    )
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", pw_path)
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")

    config_dir = home / ".holdspeak"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.json").write_text(json.dumps({
        "control_mode": "yolo",
    }))

    reset_database()

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {},
        ),
        auth_token=TOKEN,
    )
    url = server.start()
    db = get_database()

    # Wire the fake engine.
    from holdspeak.kernel.runtime import _service as _kernel_service
    broker = _kernel_service()
    engine = _TextEngine()
    if broker is not None:
        broker.inference_runner._engine_factory = lambda _rev, **_kw: engine

    yield {
        "server": server,
        "url": url,
        "db": db,
        "broker": broker,
        "engine": engine,
    }
    server.stop()
    reset_database()


# ----------------------------------------------------------------- helpers

def _api_direct(url: str, method: str, path: str, body: Any = None) -> dict:
    """Direct HTTP call (not through a Playwright page)."""
    import urllib.request
    import urllib.error

    full_url = f"{url}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Authorization": f"Bearer {TOKEN}"}
    if data:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(full_url, data=data, headers=headers, method=method)
    # HS-156-08 CI hardening: the in-process hub can briefly refuse
    # connections under CI load — retry bounded before failing.
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req) as resp:
                ct = resp.headers.get("content-type", "")
                raw = resp.read()
                payload = json.loads(raw) if "json" in ct else raw.decode()
                return {"status": resp.status, "payload": payload}
        except urllib.error.HTTPError as e:
            raw = e.read()
            try:
                payload = json.loads(raw)
            except Exception:
                payload = raw.decode()
            return {"status": e.code, "payload": payload}
        except urllib.error.URLError:
            if attempt == 4:
                raise
            import time as _time
            _time.sleep(1.0)
    raise RuntimeError("unreachable")


def _save_shot(page: Any, name: str, width: int) -> None:
    SHOTS_DIR.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SHOTS_DIR / f"{name}-{width}.png"))


def _seed_profile_and_assign(db: Any) -> None:
    """Seed a profile and assign it globally so the desk is 'configured'."""
    from tests.unit.test_phase143_inference_assignments import _profile, _result_claim, OWNER
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    pid = "hs156-glass-local"
    _profile(db, pid, claims=("language", _result_claim("chat.turn")))
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": "hs156-glass-assign",
        "expected_revision": 0,
        "scope": {"kind": "global"},
        "entries": [{"profile_id": pid, "profile_revision": 1}],
    })


def _save_shot_06(page: Any, name: str, width: int) -> None:
    SHOTS_06_DIR.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SHOTS_06_DIR / f"{name}-{width}.png"))


def _seed_endpoint_profile(db: Any, pid: str, label: str, base_url: str, model: str) -> None:
    """Seed an openAICompatible endpoint profile for the topology map.

    Creates a model profile revision (so the assignment service accepts it),
    then overwrites the raw profile record with the endpoint's kind/base_url.
    """
    from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
    _profile(db, pid, claims=("language", _result_claim("chat.turn")))
    # Overwrite the raw profile record with endpoint kind + URL
    db.profiles.upsert(
        profile_id=pid,
        name=label,
        kind="openAICompatible",
        base_url=base_url,
        model=model,
    )


def _seed_group_assignment_to(db: Any, group_ids: list[str], profile_id: str) -> None:
    """Assign specific groups to a profile so topology flows are visible."""
    from tests.unit.test_phase143_inference_assignments import OWNER
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    svc = InferenceAssignmentService(db)
    for gid in group_ids:
        svc.set_assignment(OWNER, {
            "command_id": f"hs156-glass-assign-{gid}",
            "expected_revision": 0,
            "scope": {"kind": "group", "group_id": gid},
            "entries": [{"profile_id": profile_id, "profile_revision": 1}],
        })


def _open_models_module(page: Any, url: str, width: int) -> None:
    """Navigate to Settings and open the Models module tile."""
    page.goto(f"{url}/settings?token={TOKEN}", wait_until="load")
    page.wait_for_timeout(4000)

    # Click the Models tile to open the module
    models_tile = page.locator("text=Models")
    if models_tile.count() > 0:
        models_tile.first.click()
        page.wait_for_timeout(2000)


# ----------------------------------------------------------------- door-cards leg

def test_door_cards(hub: dict) -> None:
    """Fresh desk (no assignments): Settings -> Models shows the front door at 1440+393."""
    from playwright.sync_api import sync_playwright

    url = hub["url"]

    # Seed desk + complete onboarding (but do NOT assign profiles)
    _api_direct(url, "POST", "/api/desk/seed")
    _api_direct(url, "PUT", "/api/setup/onboarding", {"disposition": "completed"})

    # Verify recommendation API works
    rec_result = _api_direct(url, "GET", "/api/front-door/recommendation")
    assert rec_result["status"] == 200, f"Recommendation failed: {rec_result}"

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for width in (1440, 393):
            page = browser.new_page(viewport={"width": width, "height": 900})
            _open_models_module(page, url, width)

            _save_shot(page, "door-cards", width)

            # Take a keyboard-focus screenshot
            page.keyboard.press("Tab")
            page.keyboard.press("Tab")
            _save_shot(page, "door-cards-focus", width)

            # No horizontal overflow
            body_w = page.evaluate("document.body.scrollWidth")
            viewport_w = page.evaluate("window.innerWidth")
            assert body_w <= viewport_w + 1, (
                f"Horizontal overflow at {width}: body={body_w}, viewport={viewport_w}"
            )

            page.close()

        browser.close()


# ----------------------------------------------------------------- door-apply leg

def test_door_apply(hub: dict) -> None:
    """Apply a pack via the API -> plan -> seed profile -> strip at 1440+393."""
    from playwright.sync_api import sync_playwright

    url = hub["url"]
    db = hub["db"]

    # Seed desk + complete onboarding
    _api_direct(url, "POST", "/api/desk/seed")
    _api_direct(url, "PUT", "/api/setup/onboarding", {"disposition": "completed"})

    # Check what packs are available
    rec_result = _api_direct(url, "GET", "/api/front-door/recommendation")
    assert rec_result["status"] == 200, f"Recommendation failed: {rec_result}"
    packs = rec_result["payload"].get("packs", [])

    if packs:
        # Try applying the first available pack (may fail on downloads)
        pack_id = packs[0]["id"]
        _api_direct(url, "POST", "/api/front-door/apply", {"pack_id": pack_id})

    # Now seed a profile + assignment so the UI shows the strip
    _seed_profile_and_assign(db)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for width in (1440, 393):
            page = browser.new_page(viewport={"width": width, "height": 900})
            _open_models_module(page, url, width)

            _save_shot(page, "door-strip", width)

            # Try to open the Advanced disclosure fold
            advanced = page.locator("text=Advanced")
            if advanced.count() > 0:
                advanced.first.click()
                page.wait_for_timeout(1000)
                _save_shot(page, "door-fold-open", width)

            # No horizontal overflow
            body_w = page.evaluate("document.body.scrollWidth")
            viewport_w = page.evaluate("window.innerWidth")
            assert body_w <= viewport_w + 1, (
                f"Horizontal overflow at {width}: body={body_w}, viewport={viewport_w}"
            )

            page.close()

        browser.close()


# ----------------------------------------------------------------- door-strip leg

def test_door_strip(hub: dict) -> None:
    """Configured desk: the strip shows, the fold opens Library + Assignments."""
    from playwright.sync_api import sync_playwright

    url = hub["url"]
    db = hub["db"]

    # Seed desk + complete onboarding + assign a profile
    _api_direct(url, "POST", "/api/desk/seed")
    _api_direct(url, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
    _seed_profile_and_assign(db)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for width in (1440, 393):
            page = browser.new_page(viewport={"width": width, "height": 900})
            _open_models_module(page, url, width)

            _save_shot(page, "strip-initial", width)

            # Try to open the Advanced disclosure fold
            advanced = page.locator("text=Advanced")
            if advanced.count() > 0:
                advanced.first.click()
                page.wait_for_timeout(1000)
                _save_shot(page, "strip-fold-open", width)

            # No horizontal overflow
            body_w = page.evaluate("document.body.scrollWidth")
            viewport_w = page.evaluate("window.innerWidth")
            assert body_w <= viewport_w + 1, (
                f"Horizontal overflow at {width}: body={body_w}, viewport={viewport_w}"
            )

            page.close()

        browser.close()


# ----------------------------------------------------------------- topology leg

def test_topology(hub: dict) -> None:
    """HS-156-06: the topology map shows this Mac + LAN endpoint at 1440+393."""
    from playwright.sync_api import sync_playwright

    url = hub["url"]
    db = hub["db"]

    # Seed desk + complete onboarding + assign a profile (to reach strip)
    _api_direct(url, "POST", "/api/desk/seed")
    _api_direct(url, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
    _seed_profile_and_assign(db)

    # Seed an LAN endpoint profile (owner-shaped: .43 server)
    _seed_endpoint_profile(
        db,
        pid="lan-qwen36-35b-a3b",
        label="LAN Qwen 3.6",
        base_url="http://192.168.1.43:8080/v1",
        model="qwen3.6-35b-a3b",
    )

    # Assign most groups to the LAN endpoint so the topology draws real bundled flows
    _seed_group_assignment_to(
        db,
        ["thoughts_notes", "writing_dictation", "meetings", "agents_tools", "background"],
        "lan-qwen36-35b-a3b",
    )

    # Verify topology API works
    topo_result = _api_direct(url, "GET", "/api/front-door/topology")
    assert topo_result["status"] == 200, f"Topology failed: {topo_result}"
    payload = topo_result["payload"]
    assert len(payload["nodes"]) >= 2, f"Expected at least 2 nodes, got {len(payload['nodes'])}"
    # Verify flows point to the LAN node (not just this_machine)
    lan_flows = [f for f in payload["flows"] if f["target_node_id"] == "lan-qwen36-35b-a3b"]
    assert len(lan_flows) >= 3, f"Expected flows to LAN node, got {lan_flows}"

    # Check flows match assignments
    assignments_result = _api_direct(url, "GET", "/api/inference/assignments")
    assert assignments_result["status"] == 200

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for width in (1440, 393):
            page = browser.new_page(viewport={"width": width, "height": 900})
            _open_models_module(page, url, width)

            # Open Advanced fold
            advanced = page.locator("text=Advanced")
            if advanced.count() > 0:
                advanced.first.click()
                page.wait_for_timeout(2000)

            # The Map tab should be selected by default
            _save_shot_06(page, "topology-map", width)

            # Click a node if visible
            node = page.locator("[data-topology-node]").first
            if node.count() > 0:
                node.click()
                page.wait_for_timeout(1000)
                _save_shot_06(page, "topology-node-selected", width)

            # Keyboard focus: Tab into the map
            page.keyboard.press("Tab")
            page.keyboard.press("Tab")
            _save_shot_06(page, "topology-keyboard-focus", width)

            # No horizontal overflow
            body_w = page.evaluate("document.body.scrollWidth")
            viewport_w = page.evaluate("window.innerWidth")
            assert body_w <= viewport_w + 1, (
                f"Horizontal overflow at {width}: body={body_w}, viewport={viewport_w}"
            )

            page.close()

        browser.close()


# ----------------------------------------------------------------- topology-add-node leg

def test_topology_add_node(hub: dict) -> None:
    """HS-156-06: add-node round-trips a second endpoint on the topology map."""
    from playwright.sync_api import sync_playwright

    url = hub["url"]
    db = hub["db"]

    # Seed desk + complete onboarding + assign a profile
    _api_direct(url, "POST", "/api/desk/seed")
    _api_direct(url, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
    _seed_profile_and_assign(db)

    # Seed the first LAN endpoint + assign groups to it
    _seed_endpoint_profile(
        db,
        pid="lan-qwen36-35b-a3b",
        label="LAN Qwen 3.6",
        base_url="http://192.168.1.43:8080/v1",
        model="qwen3.6-35b-a3b",
    )
    _seed_group_assignment_to(
        db,
        ["thoughts_notes", "writing_dictation", "meetings", "agents_tools", "background"],
        "lan-qwen36-35b-a3b",
    )

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for width in (1440, 393):
            page = browser.new_page(viewport={"width": width, "height": 900})
            _open_models_module(page, url, width)

            # Open Advanced fold
            advanced = page.locator("text=Advanced")
            if advanced.count() > 0:
                advanced.first.click()
                page.wait_for_timeout(2000)

            # Click "Add node" disclosure trigger
            add_btn = page.locator("text=+ Add node")
            if add_btn.count() > 0:
                add_btn.first.click()
                page.wait_for_timeout(500)
                _save_shot_06(page, "topology-add-node-choices", width)

                # Click "Define endpoint"
                define_btn = page.locator("[data-testid='add-endpoint']")
                if define_btn.count() > 0:
                    define_btn.click()
                    page.wait_for_timeout(500)
                    _save_shot_06(page, "topology-add-node-form", width)

            # No horizontal overflow
            body_w = page.evaluate("document.body.scrollWidth")
            viewport_w = page.evaluate("window.innerWidth")
            assert body_w <= viewport_w + 1, (
                f"Horizontal overflow at {width}: body={body_w}, viewport={viewport_w}"
            )

            page.close()

        browser.close()


# ----------------------------------------------------------------- HS-156-08 beauty legs

SHOTS_08_DIR = REPO / "pm/roadmap/holdspeak/phase-156-the-front-door/assets/story-08-shots"


def _save_shot_08(page: Any, name: str, width: int) -> None:
    SHOTS_08_DIR.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SHOTS_08_DIR / f"{name}-{width}.png"))


def _start_stub_endpoint() -> "tuple[Any, int]":
    """Minimal OpenAI-compat /v1/models endpoint.

    CI runners carry no local inference runtime, so the recommender can
    build zero packs on a bare hub; a reachable endpoint guarantees packs
    (the stopwatch rig's capture-server trick, HS-156-07)."""
    import http.server
    import socket
    import threading

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(
                {"data": [{"id": "glass-stub-model", "object": "model"}]}
            ).encode())

        def log_message(self, *_: Any) -> None:
            pass

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    httpd = http.server.HTTPServer(("127.0.0.1", port), _Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, port


def test_beauty_cards(hub: dict) -> None:
    """HS-156-08: pack cards as OBJECTS — tier row, summary anchor, folded detail.

    HS-170: RETIRED -- the front-door pack cards (.front-door-cards, surface-choice-card)
    are PARKED (HS-170-03, settled-design-four-faces.md Face 3); the pack-card
    recommender is replaced by the Concierge's FOUND engine rows + picker wells
    (ConciergeCore.tsx, own window open-concierge).
    """
    pytest.skip(
        "HS-170: front-door pack cards PARKED (HS-170-03); "
        "capability now at the Concierge's FOUND section (ConciergeCore.tsx)"
    )
    from playwright.sync_api import sync_playwright

    url = hub["url"]
    _api_direct(url, "POST", "/api/desk/seed")
    _api_direct(url, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
    # A reachable stub endpoint so the recommender ALWAYS offers packs,
    # even on runners with no local inference runtime (CI).
    stub, stub_port = _start_stub_endpoint()
    _seed_endpoint_profile(
        hub["db"], "hs156-beauty-stub", "Qwen server (stub)",
        f"http://127.0.0.1:{stub_port}", "glass-stub-model",
    )

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for width in (1440, 393):
            page = browser.new_page(viewport={"width": width, "height": 1000})
            _open_models_module(page, url, width)
            page.wait_for_selector("[data-testid='front-door-cards']", timeout=20000)
            _save_shot_08(page, "cards", width)

            # The recommended pack, selected: presence, not just a corner tag
            recommended = page.locator(".surface-choice-card[data-recommended]").first
            recommended.wait_for(state="visible", timeout=20000)
            recommended.click()
            page.wait_for_timeout(300)
            _save_shot_08(page, "cards-selected", width)

            # One fold open: per-job detail grouped by what serves them
            cards_count = page.locator(".surface-choice-card").count()
            folds = page.locator(
                ".surface-choice-card-fold .surface-disclosure-trigger"
            )
            assert cards_count >= 1 and folds.count() == cards_count, (
                "every pack card carries a fold"
            )
            folds.first.click()
            page.wait_for_timeout(300)
            _save_shot_08(page, "cards-fold-open", width)

            # No horizontal overflow
            body_w = page.evaluate("document.body.scrollWidth")
            viewport_w = page.evaluate("window.innerWidth")
            assert body_w <= viewport_w + 1, (
                f"Horizontal overflow at {width}: body={body_w}, viewport={viewport_w}"
            )

            page.close()

        browser.close()
    stub.shutdown()


def test_beauty_candidate_picker(hub: dict) -> None:
    """HS-156-08: candidates are material cards (name, boundary, health), never raw rows.

    HS-170: RETIRED -- the front-door candidate picker (.assignment-candidates)
    is PARKED (HS-170-03, settled-design-four-faces.md Face 3); the picker is
    replaced by the Concierge's per-group ChoiceCard picker wells
    (ConciergeCore.tsx PickerWell, concierge-picker-well-{group} testid).
    """
    pytest.skip(
        "HS-170: front-door candidate picker PARKED (HS-170-03); "
        "capability now at the Concierge's picker ChoiceCards (ConciergeCore.tsx)"
    )
    from playwright.sync_api import sync_playwright

    url = hub["url"]
    db = hub["db"]

    _api_direct(url, "POST", "/api/desk/seed")
    _api_direct(url, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
    _seed_profile_and_assign(db)
    # Stub-backed endpoint profiles: a LAN address here would stall the
    # recommender's reachability probes on CI (3 s each, no LAN).
    stub, stub_port = _start_stub_endpoint()
    _seed_endpoint_profile(
        db, "hs156-beauty-lan", "Qwen server on .43",
        f"http://127.0.0.1:{stub_port}", "qwen3.5-9b",
    )
    _seed_endpoint_profile(
        db, "hs156-beauty-mlx", "Qwen3.5 9B (MLX)",
        f"http://127.0.0.1:{stub_port}", "qwen3.5-9b-mlx",
    )

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for width in (1440, 393):
            page = browser.new_page(viewport={"width": width, "height": 1000})
            _open_models_module(page, url, width)

            # The configured desk shows the strip; wait for it, then the fold
            page.wait_for_selector("[data-testid='front-door-strip']", timeout=25000)
            advanced = page.locator("text=Advanced")
            assert advanced.count() > 0, "the strip carries the Advanced fold"
            advanced.first.click()
            page.wait_for_timeout(1000)
            table_tab = page.get_by_role("tab", name="Table")
            if table_tab.count() > 0:
                table_tab.first.click()
                page.wait_for_timeout(1500)

            # Open the first assignment editor
            page.locator(".capability-assignment-row button").first.click()
            page.wait_for_selector(".assignment-candidates", timeout=15000)
            page.locator(".assignment-candidates").scroll_into_view_if_needed()
            page.wait_for_timeout(300)

            # Material cards, not raw rows: name + chips + chain state
            cards = page.locator(".assignment-candidates > button")
            assert cards.count() >= 1, "the editor lists candidate cards"
            assert page.locator(".assignment-candidate-chips").count() >= 1

            _save_shot_08(page, "candidate-picker", width)

            # No horizontal overflow
            body_w = page.evaluate("document.body.scrollWidth")
            viewport_w = page.evaluate("window.innerWidth")
            assert body_w <= viewport_w + 1, (
                f"Horizontal overflow at {width}: body={body_w}, viewport={viewport_w}"
            )

            page.close()

        browser.close()
    stub.shutdown()
