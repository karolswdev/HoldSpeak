#!/usr/bin/env python3
"""HS-144-06 — cold, failable Dashboard Door walk.

This is deliberately a standalone production walk, not a pytest replacement.
It boots an unseeded MeetingWebServer beneath a new HOME/XDG/TMP tree, takes
cold and populated browser evidence, and removes every private path it made.

Run:
  uv run --python 3.13.11 python scripts/door_walk_hs144.py

The default runs every leg.  ``--only`` is diagnostic and reports itself as a
partial walk.  ``serve`` and ``refresh-calendar`` are child-only commands used
by the parent; neither seeds product data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

REPO = Path(__file__).resolve().parents[1]
ASSETS = REPO / "pm/roadmap/holdspeak/phase-144-the-dashboard-door/assets"
DEFAULT_OUT = ASSETS / "story-06-shots"
DEFAULT_REPORT = ASSETS / "story-06-walk-report.md"
DEFAULT_JSON = ASSETS / "story-06-walk-report.json"
DEFAULT_PAIRS = ASSETS / "story-06-pairs.json"
DEFAULT_PAIRS_MD = ASSETS / "story-06-pairs.md"
TOKEN = "hs144-06-cold-walk-token"
FIXTURE_TEXT = "Typed first value — this remains editable and has note custody."
FIXTURE_PREFIX = "HS144 WALK"
ALL_LEGS = ("cold", "reveal", "completion", "schedule", "calendar", "one-tap", "click-depth", "doorframe", "menus", "thread")


class WalkAssertionError(AssertionError):
    pass


@dataclass
class AssertionRecord:
    label: str
    passed: bool
    detail: str = ""
    assertion_scope: str = ""


@dataclass
class LegResult:
    name: str
    passed: bool = True
    elapsed_ms: float | None = None
    assertions: list[AssertionRecord] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    facts: dict[str, Any] = field(default_factory=dict)


@dataclass
class ClickRow:
    measure: str
    baseline: str
    start_condition: str
    clicks: list[dict[str, Any]]
    final_evidence_selector: str
    result: str


class Reporter:
    def __init__(self) -> None:
        self.legs: dict[str, LegResult] = {}
        self.current: LegResult | None = None
        self.shots: list[dict[str, str]] = []
        self.findings: list[str] = []
        self.click_rows: list[ClickRow] = []
        self.cleanup: list[str] = []
        self.cleanup_ok = True

    def start_leg(self, name: str) -> LegResult:
        leg = LegResult(name=name)
        self.legs[name] = leg
        self.current = leg
        print(f"\n== LEG {name.upper()} ==", flush=True)
        return leg

    def check(self, label: str, condition: bool, detail: str = "", *, scope: str = "") -> None:
        record = AssertionRecord(label, bool(condition), detail, scope)
        if self.current is not None:
            self.current.assertions.append(record)
        text = f"  {'PASS' if condition else 'FAIL'}  {label}"
        if detail:
            text += f" — {detail}"
        if scope:
            text += f" [scope: {scope}]"
        print(text, flush=True)
        if not condition:
            if self.current is not None:
                self.current.passed = False
            raise WalkAssertionError(f"{label}: {detail}" if detail else label)

    def finding(self, message: str) -> None:
        self.findings.append(message)
        if self.current is not None:
            self.current.findings.append(message)
        print(f"  FINDING  {message}", flush=True)

    def shot(self, path: Path, claim: str) -> None:
        self.shots.append({"path": str(path.relative_to(REPO)), "claim": claim})
        print(f"  SHOT  {path.relative_to(REPO)} — {claim}", flush=True)

    def cleanup_line(self, message: str, ok: bool = True) -> None:
        self.cleanup.append(message)
        self.cleanup_ok = self.cleanup_ok and ok
        print(f"  CLEANUP  {'PASS' if ok else 'FAIL'}  {message}", flush=True)

    @property
    def passed(self) -> bool:
        return all(leg.passed for leg in self.legs.values()) and self.cleanup_ok


class ClickLedger:
    """The only click gateway inside the three measured blocks."""

    def __init__(self, reporter: Reporter, measure: str, baseline: str, start_condition: str) -> None:
        self.reporter = reporter
        self.measure = measure
        self.baseline = baseline
        self.start_condition = start_condition
        self.clicks: list[dict[str, Any]] = []

    def click(self, locator: Any, label: str, selector: str) -> None:
        self.clicks.append({"label": label, "selector": selector, "at_monotonic": round(time.monotonic(), 6)})
        locator.click()

    def close(self, final_evidence_selector: str, result: str) -> None:
        self.reporter.click_rows.append(ClickRow(
            measure=self.measure,
            baseline=self.baseline,
            start_condition=self.start_condition,
            clicks=self.clicks,
            final_evidence_selector=final_evidence_selector,
            result=result,
        ))


class Hub:
    """A child MeetingWebServer with no seed and a walk-only environment."""

    def __init__(self, port: int, home: Path, env: dict[str, str], *, tool_engine: bool = False) -> None:
        self.port = port
        self.home = home
        self.env = env
        self.url = f"http://127.0.0.1:{port}"
        self.tool_engine = tool_engine
        self.proc: subprocess.Popen[str] | None = None
        self.log_path: Path | None = None
        self._log_handle: Any = None

    def start(self, out: Path) -> None:
        self.log_path = out / "hub.log"
        self._log_handle = self.log_path.open("w", encoding="utf-8")
        cmd = [sys.executable, str(Path(__file__).resolve()), "serve", "--port", str(self.port), "--token", TOKEN]
        if self.tool_engine:
            cmd.append("--tool-engine")
        self.proc = subprocess.Popen(
            cmd,
            cwd=str(REPO), env=self.env, stdout=self._log_handle, stderr=subprocess.STDOUT, text=True,
        )
        print(f"  HUB  HOME={self.home}", flush=True)
        print(f"  HUB  XDG_CONFIG_HOME={self.env['XDG_CONFIG_HOME']}", flush=True)
        print(f"  HUB  XDG_DATA_HOME={self.env['XDG_DATA_HOME']}", flush=True)
        print(f"  HUB  TMPDIR={self.env['TMPDIR']}", flush=True)
        print(f"  HUB  port={self.port} pid={self.proc.pid} token=hs144-06-…", flush=True)
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(f"hub died on boot; read {self.log_path}")
            try:
                status, _ = self.api("GET", "/health", timeout=2)
                if status == 200:
                    return
            except Exception:
                pass
            time.sleep(0.25)
        raise RuntimeError(f"hub did not become healthy at {self.url}")

    def api(self, method: str, path: str, body: Any = None, timeout: float = 30) -> tuple[int, Any]:
        data = None
        headers = {"X-HoldSpeak-Token": TOKEN}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(self.url + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                status = response.status
                raw = response.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as error:
            status = error.code
            raw = error.read().decode("utf-8", "replace")
        try:
            return status, json.loads(raw)
        except json.JSONDecodeError:
            return status, raw

    def refresh_calendar(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "refresh-calendar"],
            cwd=str(REPO), env=self.env, text=True, capture_output=True, timeout=60,
        )

    def stop(self, reporter: Reporter) -> None:
        if self.proc is None:
            return
        pid = self.proc.pid
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                code = self.proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                code = self.proc.wait(timeout=15)
                reporter.cleanup_line(f"killed hub pid={pid} exit={code}")
            else:
                reporter.cleanup_line(f"stopped hub pid={pid} exit={code}")
        else:
            reporter.cleanup_line(f"hub pid={pid} already exited={self.proc.returncode}")
        if self._log_handle:
            self._log_handle.close()


def free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = int(sock.getsockname()[1])
    sock.close()
    return port


def isolated_environment(root: Path) -> tuple[Path, dict[str, str]]:
    home = root / "home"
    xdg_config = root / "xdg-config"
    xdg_data = root / "xdg-data"
    temp = root / "tmp"
    for path in (home, xdg_config, xdg_data, temp):
        path.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    # Do not let any process spawned by this walk borrow an owner identity,
    # profile, or credentials.  HOME is passed to every hub/conductor child.
    for key in list(env):
        upper = key.upper()
        if (
            "HOLDSPEAK" in upper
            or "OPENAI" in upper
            or "ANTHROPIC" in upper
            or "TOKEN" in upper
            or "API_KEY" in upper
            or "KEYRING" in upper
        ):
            env.pop(key, None)
    env.update({
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(xdg_config),
        "XDG_DATA_HOME": str(xdg_data),
        "TMPDIR": str(temp),
        "HOLDSPEAK_WEB_PORT": "0",
        "PYTHONUNBUFFERED": "1",
    })
    return home, env


class _WalkToolEngine:
    """HS-152-06: fake engine for the thread Hands leg.

    Emits desk.list (evidence_read) or desk.create (effect_proposal)
    depending on the user message text, then answers with text after
    the tool result arrives.
    """

    active_provider = "walk-tool-engine"
    active_model = "walk-tool-model"

    def run_prompt_stream(self, *, messages=None, temperature=None,
                          max_tokens=None, tools=None, **kw):
        from holdspeak.kernel.inference_stream import Delta

        msgs = list(messages or [])
        has_tool_result = any(m.get("role") == "tool" for m in msgs)
        if has_tool_result:
            for w in ("Here", "are", "the", "results."):
                yield Delta(kind="text", text=w + " ")
                time.sleep(0.01)
        else:
            user_text = ""
            for m in reversed(msgs):
                if m.get("role") == "user":
                    content = m.get("content", "")
                    user_text = str(content) if not isinstance(content, list) else str(content)
                    break
            if "create" in user_text.lower():
                yield Delta(kind="tool_calls", meta={"tool_calls": [
                    {"id": "walk-create-1", "name": "desk.create",
                     "arguments": json.dumps({"kind": "notes", "data": {
                         "title": f"{FIXTURE_PREFIX} walk tool note",
                         "body_markdown": "Created by the walk engine."}})},
                ]})
            else:
                yield Delta(kind="tool_calls", meta={"tool_calls": [
                    {"id": "walk-list-1", "name": "desk.list",
                     "arguments": json.dumps({"kind": "notes"})},
                ]})
        yield Delta(kind="usage", meta={"prompt_tokens": 10, "completion_tokens": 5})
        yield Delta(kind="done")

    def run_prompt_messages(self, **kw):
        return "Here are the results."

    def run_prompt(self, **kw):
        return "Here are the results."


def _seed_tool_engine() -> None:
    """Seed a local profile + assignment + fake engine in the serve child."""
    from holdspeak.db import get_database
    from tests.unit.test_phase143_inference_assignments import _profile, _result_claim, OWNER
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from holdspeak.kernel.runtime import _service as _kernel_service

    db = get_database()
    _profile(db, "walk-tool-local", claims=("language", _result_claim("chat.turn")))
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": "walk-tool-assign", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "chat.turn"},
        "entries": [{"profile_id": "walk-tool-local", "profile_revision": 1}],
    })
    engine = _WalkToolEngine()
    _kernel_service().inference_runner._engine_factory = lambda _rev, **_kw: engine
    print("  TOOL-ENGINE  seeded profile + assignment + fake engine", flush=True)


def serve(port: int, token: str, tool_engine: bool = False) -> int:
    """Child entrypoint: unseeded real hub.  No DeskService.seed call exists here."""
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda *_: None, get_state=lambda: {}),
        host="127.0.0.1", port=port, auth_token=token,
    )
    url = server.start()
    if tool_engine:
        _seed_tool_engine()
    print(f"HUB_READY {url}", flush=True)
    stop = False

    def shutdown(_signum: int, _frame: Any) -> None:
        nonlocal stop
        stop = True

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    try:
        while not stop:
            time.sleep(0.25)
    finally:
        server.stop()
    return 0


def refresh_calendar() -> int:
    """Child-only production conductor invocation under the same isolated env."""
    from holdspeak.calendar_ingest_conductor import CalendarIngestConductor

    refreshed = CalendarIngestConductor().refresh()
    print(json.dumps({"calendar_refresh": bool(refreshed)}), flush=True)
    return 0 if refreshed else 1


def page_api(page: Any, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    """A browser-authenticated API read/write, used only for proof checks."""
    result = page.evaluate(
        """async ([method, path, body]) => {
          const response = await fetch(path, {
            method,
            headers: {"X-HoldSpeak-Token": sessionStorage.getItem("hs.web.token") || "",
                      ...(body ? {"content-type": "application/json"} : {})},
            body: body ? JSON.stringify(body) : undefined,
          });
          const text = await response.text();
          let payload; try { payload = JSON.parse(text); } catch { payload = text; }
          return {status: response.status, payload};
        }""",
        [method, path, body],
    )
    if int(result["status"]) >= 300 or not isinstance(result["payload"], dict):
        raise WalkAssertionError(f"browser api {method} {path}: {result}")
    return result["payload"]


def normal_door(page: Any) -> Any:
    """Wait for the real asynchronous FirstWords handoff before Door inspection."""
    chair = page.locator(".chair")
    chair.wait_for(timeout=15000)
    try:
        page.locator(".chair:not(.chair-first-value)").wait_for(timeout=15000)
    except Exception as error:
        raise WalkAssertionError("First Sentence did not hand off to normal Chair") from error
    door = page.locator(".door-board-section")
    door.wait_for(timeout=15000)
    return door


def door_column(page: Any, name: str) -> Any:
    return page.locator(".door-board-column", has=page.get_by_role("heading", name=name, exact=True))


def attach_page_watch(page: Any, errors: list[str], *, allow_conflict: bool = False) -> None:
    page.on("pageerror", lambda error: errors.append(f"pageerror: {error}"))

    def on_console(message: Any) -> None:
        if message.type != "error":
            return
        text = str(message.text)
        expected_409 = "server responded with a status of 409 (Conflict)" in text
        if allow_conflict and expected_409:
            return
        errors.append(f"console.{message.type}: {text}")

    page.on("console", on_console)


def assert_clean(reporter: Reporter, page: Any, errors: list[str], where: str, *, allow_board_scroll: bool = False) -> None:
    reporter.check(f"{where}: no page errors", not errors, repr(errors[:3]), scope="current browser document")
    reporter.check(
        f"{where}: document has no horizontal overflow",
        bool(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")),
        scope="document root; Door board viewport is not exempt",
    )
    reporter.check(
        f"{where}: body has no horizontal overflow",
        bool(page.evaluate("document.body.scrollWidth <= window.innerWidth")),
        scope="body; Door board viewport is not exempt",
    )
    if allow_board_scroll:
        board = page.locator(".door-board-viewport")
        reporter.check(
            f"{where}: narrow Door board owns its intentional scroll",
            bool(board.evaluate("element => element.scrollWidth > element.clientWidth")),
            scope=".door-board-viewport only",
        )


def capture(reporter: Reporter, page: Any, out: Path, name: str, claim: str) -> Path:
    path = out / name
    page.screenshot(path=str(path), full_page=False)
    reporter.shot(path, claim)
    return path


def browser_context(browser: Any, width: int, height: int, *, scale: float = 1) -> tuple[Any, Any, list[str]]:
    context = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=scale)
    page = context.new_page()
    page.emulate_media(reduced_motion="reduce")
    errors: list[str] = []
    attach_page_watch(page, errors, allow_conflict=True)
    return context, page, errors


def go(page: Any, hub: Hub, route: str = "/") -> None:
    glue = "&" if "?" in route else "?"
    page.goto(f"{hub.url}{route}{glue}token={TOKEN}", wait_until="load", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    page.wait_for_timeout(600)


def api_expect(reporter: Reporter, hub: Hub, method: str, path: str, body: Any, expected: int, label: str) -> Any:
    status, payload = hub.api(method, path, body)
    reporter.check(label, status == expected, f"status={status} payload={str(payload)[:220]}", scope=f"production HTTP authority {method} {path}")
    return payload


def seed_populated_truth(reporter: Reporter, hub: Hub) -> dict[str, str]:
    """Create all non-first-value truth via production HTTP authorities only."""
    now = datetime.now(timezone.utc)
    today = date.today()
    meeting_id = "hs144-walk-source-meeting"
    actions = [
        ("hs144-walk-overdue", f"{FIXTURE_PREFIX} unblock overdue Door", "Ada", today - timedelta(days=1)),
        ("hs144-walk-now", f"{FIXTURE_PREFIX} review Door today", "Bea", today),
        ("hs144-walk-waiting", f"{FIXTURE_PREFIX} prepare next review", "Cy", today + timedelta(days=5)),
        ("hs144-walk-unassigned", f"{FIXTURE_PREFIX} name an owner", None, None),
    ]
    sync_payload = {"meetings": [{
        "meta": {"id": meeting_id, "kind": "meeting", "last_modified": now.isoformat(), "deleted": False},
        "value": {
            "id": meeting_id, "started_at": (now - timedelta(minutes=30)).isoformat(), "ended_at": now.isoformat(),
            "title": "HS144 Walk fixture source", "tags": [], "segments": [], "bookmarks": [],
            "capture_status": "finalized", "transcription_status": "active", "provenance": "native",
            "intel": {"timestamp": now.timestamp(), "topics": ["Door walk"], "summary": "HTTP fixture truth.",
                      "action_items": [{"id": item_id, "task": task, "owner": owner,
                                        "due": due.isoformat() if due else None, "status": "pending",
                                        "review_state": "accepted", "created_at": now.isoformat()}
                                       for item_id, task, owner, due in actions]},
        },
    }]}
    pushed = api_expect(reporter, hub, "POST", "/api/sync/push", sync_payload, 200, "fixture sync ingestion accepted")
    reporter.check("fixture sync reports one source meeting", pushed.get("received", {}).get("meetings") == 1,
                   str(pushed.get("received")), scope="POST /api/sync/push response")
    api_expect(reporter, hub, "POST", "/api/desk/seed", None, 200, "Desk seed authority is preservation-safe")
    created = api_expect(reporter, hub, "POST", "/api/thoughts", {
        "request_id": str(uuid.uuid4()), "raw_text": f"{FIXTURE_PREFIX} active thought stays honest.",
        "source": {"kind": "typed"}, "initial_note": {
            "title": f"{FIXTURE_PREFIX} active thought", "body_markdown": "HTTP custody route created this thought.", "tags": [],
        },
    }, 201, "fixture Thought enters custody authority")
    thought = created.get("thought", created)
    thought_id = str(thought.get("id", ""))
    reporter.check("fixture Thought returned a stable id", bool(thought_id), repr(thought), scope="POST /api/thoughts response")
    schedule = api_expect(reporter, hub, "POST", "/api/scheduled-recordings", {
        "title": f"{FIXTURE_PREFIX} baseline recording", "cron_expr": "0 9 * * *", "tz": "UTC",
        "one_shot": False, "duration_minutes": 30, "enabled": True,
    }, 201, "fixture schedule enters production authority")
    reporter.check("fixture schedule title is authoritative", schedule.get("schedule", {}).get("title") == f"{FIXTURE_PREFIX} baseline recording",
                   repr(schedule), scope="POST /api/scheduled-recordings response")
    return {"thought_id": thought_id, "overdue_id": "hs144-walk-overdue", "now_id": "hs144-walk-now"}


def websocket_unavailable(page: Any) -> dict[str, Any]:
    """Exercise the real browser WebSocket protocol without inventing speech."""
    return page.evaluate(
        """async () => {
          const token = sessionStorage.getItem("hs.web.token") || "";
          const encoded = btoa(String.fromCharCode(...new TextEncoder().encode(token)))
            .replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/, "");
          return await new Promise((resolve, reject) => {
            const ws = new WebSocket(`${location.origin.replace(/^http/, "ws")}/ws/dictation/stream`,
              ["holdspeak.v1", `holdspeak.auth.v1.${encoded}`]);
            const timer = setTimeout(() => { ws.close(); reject(new Error("named unavailable socket timed out")); }, 5000);
            ws.onmessage = (event) => { clearTimeout(timer); try { resolve(JSON.parse(event.data)); } catch { reject(new Error(event.data)); } };
            ws.onerror = () => { clearTimeout(timer); reject(new Error("named unavailable socket errored")); };
          });
        }"""
    )


def leg_cold(reporter: Reporter, browser: Any, hub: Hub, out: Path) -> None:
    """Fresh First Sentence, named model-less refusal, typed custody/handoff."""
    context, page, errors = browser_context(browser, 1440, 900)
    try:
        go(page, hub)
        first = page.get_by_test_id("chair-first-value")
        reporter.check("cold starts at First Sentence", first.is_visible(), scope='[data-testid="chair-first-value"]')
        reporter.check("cold First Sentence heading is one job", first.get_by_role("heading", name="Dictate one sentence", exact=True).is_visible(), scope="First Sentence container")
        reporter.check("cold First Sentence has editable pad", first.get_by_role("textbox", name="Your dictated text", exact=True).is_visible(), scope="First Sentence container")
        reporter.check("cold First Sentence has Click to speak", first.get_by_role("button", name="Click to dictate", exact=True).is_visible(), scope="First Sentence container")
        reporter.check("cold First Sentence has continue verb", first.get_by_role("button", name="Continue later", exact=True).is_visible(), scope="First Sentence container")
        reporter.check("cold has no Door before first value", page.locator(".door-board-section").count() == 0, scope="whole document absence check")
        reporter.check("cold has no Desk chrome before first value", page.locator(".desk-menubar").count() == 0, scope="whole document absence check")
        reporter.check("cold has no fake transcript state", not first.get_by_text("Transcription unavailable.", exact=True).count(), scope="First Sentence container")
        capture(reporter, page, out, "cold-first-value-1440.png", "untouched First Sentence at desktop")
        assert_clean(reporter, page, errors, "cold 1440")

        unavailable = websocket_unavailable(page)
        reporter.check("model-less speech returns named unavailability", unavailable.get("reason") == "transcription_unavailable" and unavailable.get("failure_category") == "transcription_unavailable",
                       repr(unavailable), scope="real /ws/dictation/stream browser protocol")
        reporter.current.facts["speech_unavailable"] = unavailable  # type: ignore[union-attr]

        start = float(page.evaluate("performance.now()"))
        pad = first.get_by_role("textbox", name="Your dictated text", exact=True)
        pad.fill(FIXTURE_TEXT)
        reporter.check("typed first value visibly remains editable", pad.input_value() == FIXTURE_TEXT, scope="First Sentence editable pad")
        # The named typed-state verb is the actual FirstWords custody handoff:
        # it writes the note, records onboarding disposition, and opens the
        # Desk. Going through Keep as Note first then asking the same widget to
        # create a second copy is not a stronger custody proof.
        first.get_by_role("button", name="Save draft & continue", exact=True).click()
        normal_door(page)
        end = float(page.evaluate("performance.now()"))
        elapsed = end - start
        reporter.current.elapsed_ms = elapsed  # type: ignore[union-attr]
        reporter.current.facts.update({"first_value_mode": "typed_fallback", "first_value_ms": round(elapsed, 3)})  # type: ignore[union-attr]
        reporter.check("typed first value reaches visible Desk result and custody within 3 minutes", elapsed <= 180000,
                       f"first_value_mode=typed_fallback elapsed_ms={elapsed:.3f}", scope="First Sentence real Continue later handoff")
        notes = page_api(page, "GET", "/api/notes")
        reporter.check("typed first value has authoritative note custody", any(note.get("body_markdown") == FIXTURE_TEXT for note in notes.get("notes", [])),
                       f"notes={len(notes.get('notes', []))}", scope="GET /api/notes after visible Desk handoff")
        reporter.check("typed handoff reveals normal Door state", page.locator(".chair:not(.chair-first-value)").count() == 1,
                       scope="normal Chair after First Sentence handoff")
        assert_clean(reporter, page, errors, "typed first-value handoff")
    finally:
        context.close()

    context, page, errors = browser_context(browser, 393, 852)
    try:
        # A fresh document cannot recreate First Sentence after the deliberate
        # real handoff, so this screenshot is taken before the 1440 custody path
        # only when cold is the isolated first leg.  The initial cold screenshot
        # at narrow is captured in a separate completely fresh server context by
        # the caller before custody (see run_walk).
        go(page, hub)
        normal_door(page)
        assert_clean(reporter, page, errors, "post-handoff 393")
    finally:
        context.close()


def capture_cold_narrow(reporter: Reporter, browser: Any, hub: Hub, out: Path) -> None:
    """This must run before typed custody changes onboarding state."""
    context, page, errors = browser_context(browser, 393, 852)
    try:
        go(page, hub)
        first = page.get_by_test_id("chair-first-value")
        reporter.check("cold narrow starts at First Sentence", first.is_visible(), scope='[data-testid="chair-first-value"]')
        reporter.check("cold narrow has editable pad and Continue later", first.get_by_role("textbox", name="Your dictated text", exact=True).is_visible() and first.get_by_role("button", name="Continue later", exact=True).is_visible(), scope="First Sentence container")
        reporter.check("cold narrow has no Door", page.locator(".door-board-section").count() == 0, scope="whole document absence check")
        capture(reporter, page, out, "cold-first-value-393.png", "untouched First Sentence at narrow width")
        assert_clean(reporter, page, errors, "cold 393")
    finally:
        context.close()


def assert_reveal(reporter: Reporter, page: Any, hub: Hub, ids: dict[str, str], *, narrow: bool = False) -> Any:
    door = normal_door(page)
    api_door = page_api(page, "GET", "/api/door")
    expected = {
        "Overdue": ("overdue", f"{FIXTURE_PREFIX} unblock overdue Door", "hs144-walk-overdue"),
        "Now": ("now", f"{FIXTURE_PREFIX} review Door today", "hs144-walk-now"),
        "Waiting": ("waiting", f"{FIXTURE_PREFIX} prepare next review", "hs144-walk-waiting"),
        "Active": ("active", f"{FIXTURE_PREFIX} active thought", ids["thought_id"]),
    }
    reporter.check("Door owns its summary", door.locator(".door-board-summary").count() == 1, scope=".door-board-section")
    reporter.check("Door owns upcoming rail", door.locator(".door-upcoming-rail").count() == 1, scope=".door-board-section")
    for label, (key, title, source_id) in expected.items():
        column = door_column(page, label)
        reporter.check(f"{label} column exists inside Door", column.count() == 1, scope=f".door-board-section > .door-board-column heading {label}")
        card = column.locator(".door-card", has_text=title)
        reporter.check(f"{label} owns its labelled source card", card.count() == 1, scope=f"{label} Door column")
        reporter.check(f"{label} count label agrees with aggregate", column.get_by_label(f"1 {label.lower()} items", exact=True).is_visible(), scope=f"{label} column count label")
        api_cards = api_door.get("board", {}).get(key, [])
        reporter.check(f"{label} API source id and title agree", any(str(card_value.get("id")) == source_id and title in str(card_value.get("title") or card_value.get("text") or "") for card_value in api_cards),
                       f"api cards={api_cards}", scope=f"GET /api/door board.{key}")
    unassigned = door_column(page, "Unassigned")
    reporter.check("Unassigned owns source card without invented count", unassigned.locator(".door-card", has_text=f"{FIXTURE_PREFIX} name an owner").count() == 1 and unassigned.locator("[aria-label$='unassigned items']").count() == 0,
                   scope="Unassigned Door column")
    rail = door.locator(".door-upcoming-rail")
    reporter.check("rail owns baseline schedule", rail.get_by_text(f"{FIXTURE_PREFIX} baseline recording", exact=True).is_visible(), scope=".door-upcoming-rail")
    reporter.check("schedule does not duplicate into retained Meetings lane", page.locator('[data-lane="meetings"]').get_by_text(f"{FIXTURE_PREFIX} baseline recording", exact=True).count() == 0,
                   scope="retained Meetings lane absence check")
    counts = api_door.get("counts", {})
    reporter.check("Door aggregate counts are exact fixture truth", all(counts.get(key) == 1 for key in ("overdue", "now", "waiting", "active")),
                   repr(counts), scope="GET /api/door counts")
    if narrow:
        reporter.check("narrow board scroll belongs to board viewport", bool(door.locator(".door-board-viewport").evaluate("element => element.scrollWidth > element.clientWidth")), scope=".door-board-viewport")
    return door


def leg_reveal(reporter: Reporter, browser: Any, hub: Hub, out: Path, ids: dict[str, str]) -> None:
    for width, height, name in ((1440, 900, "after-chair-home-1440.png"), (393, 852, "after-chair-home-393.png")):
        context, page, errors = browser_context(browser, width, height)
        try:
            go(page, hub)
            assert_reveal(reporter, page, hub, ids, narrow=width == 393)
            capture(reporter, page, out, name, f"populated Door board and rail at {width}px")
            assert_clean(reporter, page, errors, f"reveal {width}", allow_board_scroll=width == 393)
        finally:
            context.close()
    context, page, errors = browser_context(browser, 720, 450, scale=2)
    try:
        go(page, hub)
        door = assert_reveal(reporter, page, hub, ids, narrow=True)
        now_card = door_column(page, "Now").locator(".door-card", has_text=f"{FIXTURE_PREFIX} review Door today")
        done = now_card.get_by_role("button", name="Done", exact=True)
        done.focus()
        reporter.check("200% Door card action has visible keyboard focus", bool(done.evaluate("el => document.activeElement === el && el.matches(':focus-visible')")), scope="Now Door card at DSF 2")
        capture(reporter, page, out, "door-populated-zoom200.png", "200% populated Door accessibility evidence")
        capture(reporter, page, out, "door-focus-zoom200.png", "200% keyboard focus evidence on Door action")
        assert_clean(reporter, page, errors, "reveal 200%", allow_board_scroll=True)
    finally:
        context.close()


def leg_completion(reporter: Reporter, browser: Any, hub: Hub, out: Path, ids: dict[str, str]) -> None:
    context, page, errors = browser_context(browser, 1440, 900)
    try:
        go(page, hub)
        door = normal_door(page)
        api_door = page_api(page, "GET", "/api/door")
        overdue_api = next((card for card in api_door.get("board", {}).get("overdue", []) if card.get("id") == ids["overdue_id"]), {})
        reporter.check("completion target exposes production Done descriptor", any(verb.get("name") == "follow_through.complete" and verb.get("arguments", {}).get("verb") == "done" for verb in overdue_api.get("lawful_verbs", [])),
                       repr(overdue_api.get("lawful_verbs")), scope="GET /api/door board.overdue descriptor")
        overdue = door_column(page, "Overdue")
        card = overdue.locator(".door-card", has_text=f"{FIXTURE_PREFIX} unblock overdue Door")
        done = card.get_by_role("button", name="Done", exact=True)
        reporter.check("completion button belongs to named Overdue card", done.count() == 1, scope="Overdue Door column -> fixture card")
        start = float(page.evaluate("performance.now()"))
        done.click()
        card.wait_for(state="detached", timeout=15000)
        end = float(page.evaluate("performance.now()"))
        elapsed = end - start
        reporter.current.elapsed_ms = elapsed  # type: ignore[union-attr]
        reporter.current.facts["completion_ms"] = round(elapsed, 3)  # type: ignore[union-attr]
        landed = page_api(page, "GET", "/api/door")
        reporter.check("Done changes the authoritative Door aggregate", not any(card_value.get("id") == ids["overdue_id"] for card_value in landed.get("board", {}).get("overdue", [])), scope="GET /api/door after Door action")
        reporter.check("Done changes its owning Overdue column within 500ms", elapsed <= 500, f"completion_ms={elapsed:.3f}", scope="Overdue Door card detachment measured by page performance.now()")
        capture(reporter, page, out, "door-completion-1440.png", "quiet success: authoritative Door board changed")

        # The settled receipt grammar is failure-only.  Drift the active Thought
        # through its real custody authority, then click the old descriptor.
        current = api_expect(reporter, hub, "GET", f"/api/thoughts/{ids['thought_id']}", None, 200, "read active Thought for stale-refusal setup").get("thought", {})
        api_expect(reporter, hub, "PATCH", f"/api/thoughts/{ids['thought_id']}/working", {
            "expected_aggregate_revision": current["aggregate_revision"], "expected_working_revision": current["working_revision"],
            "title": f"{FIXTURE_PREFIX} active thought revised", "body_markdown": "Real stale cursor refusal belongs beside Door.", "tags": [],
        }, 200, "drift active Thought through custody authority")
        active_card = door_column(page, "Active").locator(".door-card", has_text=f"{FIXTURE_PREFIX} active thought")
        active_card.get_by_role("button", name="Complete", exact=True).click()
        receipt = door.locator(".door-board-receipt [role=status]")
        receipt.get_by_text("COMPLETE FAILED · HTTP 409", exact=True).wait_for(timeout=15000)
        reporter.check("stale 409 receipt stays in Door", receipt.get_by_role("button", name="Retry", exact=True).is_visible(), scope=".door-board-section .door-board-receipt")
        reporter.check("stale refusal opens no dialog", page.get_by_role("dialog").count() == 0, scope="whole document dialog absence")
        capture(reporter, page, out, "door-stale-refusal-1440.png", "named stale 409 refusal receipt beside Door")
        assert_clean(reporter, page, errors, "completion and stale receipt")
    finally:
        context.close()


def leg_schedule(reporter: Reporter, browser: Any, hub: Hub, out: Path) -> None:
    title = f"{FIXTURE_PREFIX} in-world recording"
    context, page, errors = browser_context(browser, 1440, 900)
    try:
        go(page, hub)
        rail = normal_door(page).locator(".door-upcoming-rail")
        rail.get_by_role("button", name="Schedule recording", exact=True).click()
        form = page.locator("#schedule\\:__create__")
        form.wait_for(timeout=15000)
        reporter.check("Door schedule form is in-world", form.is_visible(), scope="#schedule\\:__create__ opened from .door-upcoming-rail")
        reporter.check("Door schedule form has voice-enabled title", form.get_by_role("button", name="Speak Title", exact=True).is_visible(), scope="Door schedule form")
        form.get_by_role("textbox", name="Title", exact=True).fill(title)
        capture(reporter, page, out, "after-cadence-surface-1440.png", "schedule creation begins in-world from Door rail")
        form.get_by_test_id("schedule-create-submit").click()
        form.wait_for(state="detached", timeout=15000)
        rail.get_by_text(title, exact=True).wait_for(timeout=15000)
        schedules = page_api(page, "GET", "/api/scheduled-recordings")
        reporter.check("in-world schedule is authoritative and visible on Door rail", any(schedule.get("title") == title for schedule in schedules.get("schedules", [])) and rail.get_by_text(title, exact=True).is_visible(),
                       scope="production schedule list AND owning Door rail")
        capture(reporter, page, out, "door-schedule-created-1440.png", "created schedule visible on Door rail")
        assert_clean(reporter, page, errors, "schedule 1440")
    finally:
        context.close()
    context, page, errors = browser_context(browser, 393, 852)
    try:
        go(page, hub)
        rail = normal_door(page).locator(".door-upcoming-rail")
        rail.get_by_role("button", name="Schedule recording", exact=True).click()
        form = page.locator("#schedule\\:__create__")
        form.wait_for(timeout=15000)
        reporter.check("narrow Door schedule form is in-world", form.is_visible(), scope="#schedule\\:__create__ opened from narrow .door-upcoming-rail")
        capture(reporter, page, out, "after-cadence-surface-393.png", "narrow schedule creation begins in-world from Door rail")
        form.get_by_role("button", name="Cancel", exact=True).click()
        form.wait_for(state="detached", timeout=15000)
        assert_clean(reporter, page, errors, "schedule 393", allow_board_scroll=True)
    finally:
        context.close()


def open_meetings_settings(page: Any) -> Any:
    chrome = page.locator(".desk-menubar")
    chrome.get_by_role("button", name="Go", exact=True).click()
    menu = page.get_by_role("menu", name="Go menu")
    # The registry labels this as a Settings verb (for example, "Configure
    # Settings"); substring matching remains scoped to the already-open Go menu.
    menu.get_by_role("menuitem", name="Settings").click()
    settings = page.locator("#surface-settings")
    settings.wait_for(timeout=15000)
    settings.locator("button.prefs-tile", has_text="MEETINGS").click()
    # TODO(HS-146-05): story 03 replaces the single textbox with a GadgetTable
    # list editor.  Wait for the Settings Meetings module to render, but do not
    # assert any specific calendar control glass.
    settings.wait_for(timeout=15000)
    return settings


def _write_calendar_sources_api(page: Any, hub: Hub, sources: list[dict[str, Any]]) -> dict[str, Any]:
    """HS-146-04: configure calendar via the settings API (sources wire), not the UI."""
    status, payload = hub.api("PUT", "/api/settings", {"calendar": {"sources": sources}})
    if status >= 300:
        raise WalkAssertionError(f"settings PUT {status}: {payload}")
    return payload


def leg_calendar(reporter: Reporter, browser: Any, hub: Hub, out: Path, fixture_dir: Path) -> None:
    starts = datetime.now(timezone.utc).replace(second=0, microsecond=0) + timedelta(hours=2)
    ends = starts + timedelta(minutes=45)
    fixture = fixture_dir / "hs144-door-calendar.ics"
    fixture.write_text("\r\n".join([
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//HoldSpeak//HS144 Walk//EN", "BEGIN:VEVENT",
        "UID:hs144-walk-calendar-fixture", f"DTSTART:{starts.strftime('%Y%m%dT%H%M%SZ')}",
        f"DTEND:{ends.strftime('%Y%m%dT%H%M%SZ')}", f"SUMMARY:{FIXTURE_PREFIX} calendar fixture",
        "LOCATION:Walk Room 4", "URL:https://meet.example.test/hs144-walk", "END:VEVENT", "END:VCALENDAR", "",
    ]), encoding="utf-8")
    reporter.current.facts["ics_fixture"] = str(fixture)  # type: ignore[union-attr]

    # HS-146-04: seed repair — configure via the sources-wire API, not the UI textbox.
    context, page, errors = browser_context(browser, 1440, 900)
    try:
        go(page, hub)
        saved = _write_calendar_sources_api(page, hub, [
            {"id": "walk-file", "label": "Walk File", "url": str(fixture), "enabled": True},
        ])
        sources_fact = saved.get("settings", saved).get("_calendar_sources", [])
        reporter.check("Settings saves local fixture through sources-wire API",
                       len(sources_fact) == 1 and sources_fact[0].get("kind") == "file" and sources_fact[0].get("egress") is False,
                       repr(sources_fact), scope="PUT /api/settings calendar.sources AND _calendar_sources fact")
        refreshed = hub.refresh_calendar()
        reporter.check("real CalendarIngestConductor refresh succeeds", refreshed.returncode == 0 and '"calendar_refresh": true' in refreshed.stdout,
                       f"exit={refreshed.returncode} stdout={refreshed.stdout.strip()} stderr={refreshed.stderr.strip()}", scope="isolated child CalendarIngestConductor.refresh()")
        # A fresh Door document is the only honest frame for the rail claim
        # and forces a real aggregate revalidation after the conductor refresh.
        rail_context, rail_page, rail_errors = browser_context(browser, 1440, 900)
        try:
            go(rail_page, hub)
            door = normal_door(rail_page)
            rail = door.locator(".door-upcoming-rail")
            title = f"{FIXTURE_PREFIX} calendar fixture"
            calendar_row = rail.locator('[data-upcoming-source="calendar_event"]', has_text=title)
            scheduled_row = rail.locator(
                '[data-upcoming-source="scheduled_recording"]',
                has_text=f"{FIXTURE_PREFIX} baseline recording",
            )
            reporter.check("fixture event is source-labelled inside Door rail", calendar_row.count() == 1 and calendar_row.get_by_text("EVENT", exact=True).is_visible(), scope=".door-upcoming-rail calendar_event row")
            reporter.check("calendar evidence also shows scheduled-recording rail row", scheduled_row.count() == 1 and scheduled_row.get_by_text("SCHEDULED RECORDING", exact=True).is_visible(), scope=".door-upcoming-rail scheduled_recording row")
            reporter.check("fixture rail row owns location and meeting link", calendar_row.get_by_text("Walk Room 4", exact=True).is_visible() and calendar_row.get_by_role("link", name="Meeting link", exact=True).is_visible(), scope="calendar_event row in .door-upcoming-rail")
            door_api = page_api(rail_page, "GET", "/api/door")
            reporter.check("Door aggregate contains actual fixture calendar source", any(item.get("source") == "calendar_event" and item.get("title") == title for item in door_api.get("upcoming", [])),
                           repr(door_api.get("upcoming")), scope="GET /api/door upcoming")
            reporter.check("calendar evidence capture has no Settings window", rail_page.locator("#surface-settings").count() == 0, scope="fresh Door capture document")
            capture(reporter, rail_page, out, "door-calendar-rail-1440.png", "fresh Door rail with ICS EVENT and scheduled-recording rows")
            assert_clean(reporter, rail_page, rail_errors, "calendar fixture rail")
        finally:
            rail_context.close()
    finally:
        context.close()

    # HS-146-04: HTTPS egress fact via the sources-wire API.
    context, page, errors = browser_context(browser, 1440, 900)
    try:
        go(page, hub)
        https_saved = _write_calendar_sources_api(page, hub, [
            {"id": "walk-https", "label": "", "url": "https://calendar.example.test/team.ics", "enabled": True},
        ])
        https_fact = https_saved.get("settings", https_saved).get("_calendar_sources", [])
        reporter.check("HTTPS sources-wire egress fact is true",
                       len(https_fact) == 1 and https_fact[0] == {
                           "id": "walk-https", "label": "", "kind": "https",
                           "host": "calendar.example.test", "refresh_seconds": 900,
                           "egress": True, "enabled": True,
                       },
                       repr(https_fact), scope="PUT /api/settings calendar.sources derived _calendar_sources fact")
        # TODO(HS-146-05): once story 03's list editor lands, assert the egress
        # chip glass on the Settings surface here.
        capture(reporter, page, out, "settings-calendar-egress-1440.png", "HTTPS transport egress fact via sources-wire API")
        # Restore the file source before cleanup.
        restored = _write_calendar_sources_api(page, hub, [
            {"id": "walk-file", "label": "Walk File", "url": str(fixture), "enabled": True},
        ])
        restored_fact = restored.get("settings", restored).get("_calendar_sources", [])
        reporter.check("Settings restores local fixture before cleanup",
                       len(restored_fact) == 1 and restored_fact[0].get("egress") is False,
                       scope="PUT /api/settings calendar.sources restore")
        assert_clean(reporter, page, errors, "calendar egress fact")
    finally:
        context.close()


def leg_one_tap(reporter: Reporter, browser: Any, hub: Hub, out: Path, fixture_dir: Path) -> None:
    """HS-147: see the meeting on the rail, tap once, trust the arm.

    The stub walk hub deliberately has no meeting runtime (no
    ``_start_meeting`` on its callbacks), so the FIRE cannot honestly
    produce a live meeting here; the fire → meeting → provenance chain is
    proven by the story-01 real-conductor lifecycle test and the story-04
    glue test. This leg proves the OWNER's journey on real glass — tap,
    ARMED, cancel, the honest stale-row refusal — and the origin line on a
    linked meeting delivered through the production sync authority.
    """
    starts_a = datetime.now(timezone.utc).replace(second=0, microsecond=0) + timedelta(hours=2)
    starts_b = starts_a + timedelta(hours=1)
    fixture = fixture_dir / "hs147-one-tap.ics"
    lines: list[str] = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//HoldSpeak//HS147 Walk//EN"]
    for uid, starts, title in (
        ("hs147-walk-a", starts_a, f"{FIXTURE_PREFIX} one-tap standup"),
        ("hs147-walk-b", starts_b, f"{FIXTURE_PREFIX} one-tap review"),
    ):
        ends = starts + timedelta(minutes=45)
        lines += ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTART:{starts.strftime('%Y%m%dT%H%M%SZ')}",
                  f"DTEND:{ends.strftime('%Y%m%dT%H%M%SZ')}", f"SUMMARY:{title}", "END:VEVENT"]
    lines += ["END:VCALENDAR", ""]
    fixture.write_text("\r\n".join(lines), encoding="utf-8")

    context, page, errors = browser_context(browser, 1440, 900)
    try:
        go(page, hub)
        # Append beside the existing sources; later legs (click-depth) assert
        # on the calendar leg's fixture, so this leg must never orphan it.
        settings_payload = page_api(page, "GET", "/api/settings")
        raw_calendar = settings_payload.get("settings", settings_payload).get("calendar", {}) or {}
        prior_sources = [
            {"id": s["id"], "label": s.get("label", ""), "url": s.get("url", ""), "enabled": bool(s.get("enabled"))}
            for s in (raw_calendar.get("sources") or []) if s.get("url")
        ]
        _write_calendar_sources_api(page, hub, prior_sources + [
            {"id": "walk-one-tap", "label": "Walk Tap", "url": str(fixture), "enabled": True},
        ])
        refreshed = hub.refresh_calendar()
        reporter.check("one-tap fixture refresh succeeds", refreshed.returncode == 0,
                       f"exit={refreshed.returncode}", scope="isolated child CalendarIngestConductor.refresh()")
        door_api = page_api(page, "GET", "/api/door")
        ids_by_title = {i["title"]: i["id"] for i in door_api.get("upcoming", []) if i.get("source") == "calendar_event"}
        title_a = f"{FIXTURE_PREFIX} one-tap standup"
        title_b = f"{FIXTURE_PREFIX} one-tap review"
        reporter.check("both one-tap events reach the aggregate", title_a in ids_by_title and title_b in ids_by_title,
                       repr(sorted(ids_by_title)), scope="GET /api/door upcoming")

        tap_context, tap_page, tap_errors = browser_context(browser, 1440, 900)
        try:
            go(tap_page, hub)
            door = normal_door(tap_page)
            rail = door.locator(".door-upcoming-rail")
            row_a = rail.locator('[data-upcoming-source="calendar_event"]', has_text=title_a)
            row_b = rail.locator('[data-upcoming-source="calendar_event"]', has_text=title_b)
            row_a.get_by_test_id("door-record-this").wait_for(timeout=15000)
            reporter.check("every event row offers RECORD THIS", row_b.get_by_test_id("door-record-this").is_visible(),
                           scope='[data-upcoming-source="calendar_event"] door-record-this')
            capture(reporter, tap_page, out, "one-tap-unarmed-1440.png", "populated rail, RECORD THIS on every event row")

            # ONE TAP.
            row_a.get_by_test_id("door-record-this").click()
            row_a.get_by_test_id("door-armed-chip").wait_for(timeout=15000)
            schedules = page_api(tap_page, "GET", "/api/scheduled-recordings").get("schedules", [])
            linked = [s for s in schedules if s.get("calendar_event_id") == ids_by_title[title_a]]
            reporter.check("one tap arms a linked enabled one-shot",
                           len(linked) == 1 and linked[0]["one_shot"] is True and linked[0]["enabled"] is True
                           and linked[0]["title"] == title_a,
                           repr(linked), scope="POST via door-record-this + GET /api/scheduled-recordings")
            expected_fire = (starts_a - timedelta(seconds=60)).timestamp()
            raw_fire = str(linked[0].get("next_fire_at") or "")
            actual_fire = datetime.fromisoformat(raw_fire.replace("Z", "+00:00")).timestamp()
            reporter.check("armed fire time carries the 60s lead", abs(actual_fire - expected_fire) < 1.0,
                           f"next_fire_at={raw_fire} expected_epoch={expected_fire}", scope="60s-lead ruling (D4)")
            door_after = page_api(tap_page, "GET", "/api/door")
            reporter.check("one intent renders one row (linked schedule suppressed)",
                           not [i for i in door_after.get("upcoming", []) if i.get("source") == "scheduled_recording" and i.get("id") == linked[0]["id"]],
                           scope="GET /api/door upcoming suppression ruling")
            capture(reporter, tap_page, out, "one-tap-armed-1440.png", "ARMED chip + Cancel? on the tapped row; no duplicate schedule row")

            # Two-beat cancel returns the row.
            row_a.get_by_test_id("door-cancel-prompt").click()
            row_a.get_by_test_id("door-cancel-confirm").wait_for(timeout=15000)
            row_a.get_by_test_id("door-cancel-confirm").click()
            row_a.get_by_test_id("door-record-this").wait_for(timeout=15000)
            schedules = page_api(tap_page, "GET", "/api/scheduled-recordings").get("schedules", [])
            reporter.check("two-beat cancel disarms server-side",
                           not [s for s in schedules if s.get("calendar_event_id") == ids_by_title[title_a]],
                           scope="DELETE via door-cancel-confirm + GET /api/scheduled-recordings")

            # The honest refusal: arm row B out-of-band, tap its stale button.
            page_api(tap_page, "POST", "/api/scheduled-recordings", {"calendar_event_id": ids_by_title[title_b]})
            row_b.get_by_test_id("door-record-this").click()
            refusal = row_b.get_by_test_id("door-arm-refusal")
            refusal.wait_for(timeout=15000)
            reporter.check("stale tap refuses in-flow by name", refusal.inner_text() == "ALREADY ARMED",
                           refusal.inner_text(), scope="door-arm-refusal on the stale row (live L1 guard)")
            capture(reporter, tap_page, out, "one-tap-refusal-1440.png", "ALREADY ARMED renders in-flow on the stale row")
            assert_clean(reporter, tap_page, tap_errors, "one-tap 1440")
        finally:
            tap_context.close()

        # The origin line, through the production sync authority: a linked
        # meeting arrives exactly as a peer device would deliver it.
        now = datetime.now(timezone.utc)
        meeting_id = "hs147-walk-linked-meeting"
        page_api(page, "POST", "/api/sync/push", {"meetings": [{
            "meta": {"id": meeting_id, "kind": "meeting", "last_modified": now.isoformat(), "deleted": False},
            "value": {
                "id": meeting_id,
                "started_at": (now - timedelta(hours=1)).isoformat(),
                "ended_at": (now - timedelta(minutes=15)).isoformat(),
                "title": title_b, "tags": [], "segments": [], "bookmarks": [],
                "capture_status": "finalized", "transcription_status": "active",
                "provenance": "native",
                "calendar_event_id": ids_by_title[title_b],
            },
        }]})
        meetings = page_api(page, "GET", "/api/meetings").get("meetings", [])
        linked_meeting = [m for m in meetings if m.get("id") == meeting_id]
        reporter.check("synced linked meeting keeps calendar_event_id (round-trip law)",
                       bool(linked_meeting) and linked_meeting[0].get("calendar_event_id") == ids_by_title[title_b],
                       repr(linked_meeting[:1]), scope="POST /api/sync/push + GET /api/meetings")
        origin_context, origin_page, origin_errors = browser_context(browser, 1440, 900)
        try:
            go(origin_page, hub)
            normal_door(origin_page)
            origin_page.get_by_role("button", name="Meetings", exact=True).first.click()
            origin = origin_page.locator('[data-meeting-origin="calendar-event"]')
            origin.first.wait_for(timeout=15000)
            reporter.check("Meetings surface wears the origin line",
                           title_b.upper() in origin.first.inner_text().upper() and "WALK TAP" in origin.first.inner_text().upper(),
                           origin.first.inner_text(), scope='[data-meeting-origin="calendar-event"] on the Meetings surface')
            capture(reporter, origin_page, out, "one-tap-origin-1440.png", "linked meeting wears FROM <SOURCE> · <EVENT>")
            assert_clean(reporter, origin_page, origin_errors, "one-tap origin line")
        finally:
            origin_context.close()

        # Narrow leg in a fresh context (walk law): armed state at 393.
        narrow_context, narrow_page, narrow_errors = browser_context(browser, 393, 852)
        try:
            go(narrow_page, hub)
            ndoor = normal_door(narrow_page)
            nrail = ndoor.locator(".door-upcoming-rail")
            nrow_b = nrail.locator('[data-upcoming-source="calendar_event"]', has_text=title_b)
            nrow_b.get_by_test_id("door-armed-chip").wait_for(timeout=15000)
            capture(reporter, narrow_page, out, "one-tap-armed-393.png", "ARMED chip clean at 393")
            assert_clean(reporter, narrow_page, narrow_errors, "one-tap 393")
        finally:
            narrow_context.close()
    finally:
        context.close()


def leg_menus(reporter: Reporter, browser: Any, hub: Hub, out: Path) -> None:
    """HS-148: the menu grammar on real glass — glyph lane, keycap wells,
    stipple + majority-collapse ghosting, the D3 keyboard repair, the
    registry-derived head menu, and list-view context reachability (the
    148 close-counsel ledger item the audit walk could not trigger)."""
    context, page, errors = browser_context(browser, 1440, 900)
    try:
        go(page, hub)
        normal_door(page)
        # Go menu under the shipped default (launcher): lane + wells + D3.
        page.get_by_role("button", name="Go", exact=True).first.click()
        menu = page.locator('nav[role="menu"]').last
        menu.wait_for(timeout=15000)
        reporter.check("Go menu declares launcher context", menu.get_attribute("data-menu-context") == "launcher",
                       scope='nav[role=menu] data-menu-context')
        reporter.check("Go menu wears the glyph lane", menu.locator(".desk-menu-glyph").count() >= 13,
                       f"glyph spans={menu.locator('.desk-menu-glyph').count()}", scope=".desk-menu-glyph lane law")
        reporter.check("keycaps render as drawn wells", menu.locator(".desk-menu-well").count() >= 5,
                       scope=".desk-menu-well keycap wells")
        try:
            page.wait_for_function(
                "document.activeElement && document.activeElement.getAttribute('role') === 'menuitem'",
                timeout=3000,
            )
            focused_role = "menuitem"
        except Exception:  # noqa: BLE001 — the honest fail path
            focused_role = page.evaluate("document.activeElement && document.activeElement.getAttribute('role')")
        reporter.check("D3 repair: click-open focuses the first item", focused_role == "menuitem",
                       f"activeElement role={focused_role}", scope="autoFocus on intentional bar open (3s poll)")
        capture(reporter, page, out, "menus-go-after-1440.png", "the Go launcher: glyph lane + keycap wells + separator")
        page.keyboard.press("Escape")

        # Object menu (all ghosted): stipple + majority-collapse + visible keycaps.
        page.get_by_role("button", name="Object", exact=True).first.click()
        omenu = page.locator('nav[role="menu"]').last
        omenu.wait_for(timeout=15000)
        reporter.check("ghosted rows carry the stipple class", omenu.locator(".is-ghost").count() >= 8,
                       f"is-ghost={omenu.locator('.is-ghost').count()}", scope=".is-ghost stipple law")
        hint = omenu.locator(".desk-menu-ghost-hint")
        reporter.check("majority ghost reason collapses to one footer",
                       hint.count() == 1 and "Select an object" in hint.inner_text(),
                       scope=".desk-menu-ghost-hint majority-collapse")
        reporter.check("minority reason stays inline once",
                       omenu.get_by_text("Select a Project", exact=False).count() == 1,
                       scope="inline minority ghost reason")
        reporter.check("keycaps stay visible when ghosted", omenu.locator(".is-ghost .desk-menu-well").count() >= 1,
                       scope="ghosted keycap wells")
        capture(reporter, page, out, "menus-object-after-1440.png", "stippled ghosts, one footer hint, wells alive")
        page.keyboard.press("Escape")

        # The registry-derived head menu on a real window.
        page.get_by_role("button", name="Meetings", exact=True).first.click()
        head = page.locator(".desk-pullout-head").first
        head.wait_for(timeout=15000)
        head.click(button="right")
        hmenu = page.locator(".desk-head-menu, nav[role='menu']").last
        hmenu.wait_for(timeout=15000)
        reporter.check("head menu carries registry labels + keycaps",
                       hmenu.get_by_text("Close window", exact=True).count() == 1
                       and hmenu.locator(".desk-menu-well").count() >= 2,
                       scope="registry-derived head menu (AA graduation)")
        capture(reporter, page, out, "menus-head-after-1440.png", "the head menu from the one registry, wells included")
        page.keyboard.press("Escape")
    finally:
        context.close()

    # List-view context reachability (counsel ledger item).
    lv_context, lv_page, lv_errors = browser_context(browser, 1440, 900)
    try:
        go(lv_page, hub)
        normal_door(lv_page)
        lv_page.get_by_role("button", name="Floor", exact=True).first.click()
        row = lv_page.locator(".desk-list-face tbody tr").first
        if row.count() == 0:
            # Spatial view default: flip to list via the Desk menu.
            lv_page.get_by_role("button", name="Desk", exact=True).first.click()
            lv_page.locator('nav[role="menu"]').last.get_by_text("List view", exact=True).click()
            row = lv_page.locator(".desk-list-face tbody tr").first
        row.wait_for(timeout=15000)
        # Zone rows do not wire the context menu; target the seeded Thought's
        # OBJECT row by title (product truth, not a rig convenience).
        obj_row = lv_page.locator(".desk-list-face tbody tr", has_text=f"{FIXTURE_PREFIX} active thought").first
        obj_row.wait_for(timeout=15000)
        obj_row.click(button="right")
        cmenu = lv_page.locator('nav[role="menu"]').last
        cmenu.wait_for(timeout=15000)
        reporter.check("list-view context menu is reachable (ledger item closed)",
                       cmenu.get_by_text("Get Info", exact=False).count() >= 1,
                       scope="list-view row contextmenu")
        capture(reporter, lv_page, out, "menus-listctx-after-1440.png", "list-view object context menu, reachable")
        assert_clean(reporter, lv_page, lv_errors, "menus list-view leg")
    finally:
        lv_context.close()

    # 393: the lone narrow menu wears the grammar.
    n_context, n_page, n_errors = browser_context(browser, 393, 852)
    try:
        go(n_page, hub)
        normal_door(n_page)
        n_page.get_by_role("button", name="Go", exact=True).first.click()
        nmenu = n_page.locator('nav[role="menu"]').last
        nmenu.wait_for(timeout=15000)
        reporter.check("393 Go wears lane + wells", nmenu.locator(".desk-menu-glyph").count() >= 13
                       and nmenu.locator(".desk-menu-well").count() >= 5,
                       scope="393 Go grammar")
        capture(reporter, n_page, out, "menus-go-after-393.png", "the narrow launcher with the full grammar")
        assert_clean(reporter, n_page, n_errors, "menus 393 leg")
    finally:
        n_context.close()


def _wait_tool_row_state(page: Any, state: str, timeout: float = 20000) -> bool:
    """Poll until at least one tool row reaches the given data-tool-state."""
    try:
        page.locator(f'[data-testid="tool-row"][data-tool-state="{state}"]').first.wait_for(timeout=timeout)
        return True
    except Exception:
        return False


def _wait_turn_done_api(hub: Hub, tid: str, aid: str, timeout: float = 30.0) -> dict[str, Any]:
    """Poll the thread detail API until the assistant message stops streaming."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        _, detail = hub.api("GET", f"/api/threads/{tid}")
        for m in detail.get("messages", []):
            if m.get("id") == aid and not m.get("streaming"):
                return detail
        time.sleep(0.3)
    return {}


def leg_thread(reporter: Reporter, browser: Any, hub: Hub, out: Path) -> None:
    """HS-151 + HS-152: thread creation via context menu, then HS-152 Hands:
    yolo tool call (desk.list -> auto-admit -> receipted with result block + RAW),
    safe-mode tool call (desk.create -> held -> Allow once -> receipted).
    """
    THREAD_SHOTS = REPO / "pm/roadmap/holdspeak/phase-151-the-desk-chat/assets/story-08-walk-shots"
    THREAD_SHOTS.mkdir(parents=True, exist_ok=True)

    # ── Part 1: HS-151 context-menu thread creation (unchanged) ──────
    context, page, errors = browser_context(browser, 1440, 900)
    try:
        go(page, hub)
        normal_door(page)

        note_title = f"{FIXTURE_PREFIX} active thought"
        page.get_by_role("button", name="Floor", exact=True).first.click()
        row = page.locator(".desk-list-face tbody tr").first
        if row.count() == 0:
            page.get_by_role("button", name="Desk", exact=True).first.click()
            page.locator('nav[role="menu"]').last.get_by_text("List view", exact=True).click()
            page.wait_for_timeout(1000)

        obj_row = page.locator(".desk-list-face tbody tr", has_text=note_title).first
        try:
            obj_row.wait_for(timeout=15000)
        except Exception:
            pass
        reporter.check(
            "thread leg: source note row visible in list view",
            obj_row.count() >= 1,
            f"looked for {note_title!r} in .desk-list-face tbody tr",
            scope="list-view object row for context menu",
        )
        capture(reporter, page, THREAD_SHOTS, "thread-list-view-1440.png",
                "list view with the fixture note row visible")

        obj_row.click(button="right")
        cmenu = page.locator('nav[role="menu"]').last
        cmenu.wait_for(timeout=15000)
        capture(reporter, page, THREAD_SHOTS, "thread-context-menu-1440.png",
                "context menu on the fixture note row")

        thread_entry = cmenu.get_by_text("Continue in thread", exact=True)
        reporter.check(
            "thread leg: 'Continue in thread' verb present in context menu",
            thread_entry.count() >= 1,
            scope="list-view object row contextmenu",
        )

        thread_entry.click()
        page.wait_for_timeout(2500)

        thread_head = page.locator(".thread-head")
        reporter.check(
            "thread leg: thread pullout opens after Continue in thread",
            thread_head.count() >= 1,
            scope=".thread-head after Continue in thread verb",
        )
        capture(reporter, page, THREAD_SHOTS, "thread-pullout-opened-1440.png",
                "thread pullout opened from Continue in thread verb")

        composer = page.locator(".thread-composer-input")
        reporter.check(
            "thread leg: composer visible in thread pullout",
            composer.count() >= 1,
            scope=".thread-composer-input in thread pullout",
        )

        threads_status, threads_resp = hub.api("GET", "/api/threads")
        thread_list = threads_resp.get("threads", []) if isinstance(threads_resp, dict) else []
        reporter.check(
            "thread leg: at least one thread exists after verb",
            len(thread_list) >= 1,
            f"thread count={len(thread_list)}",
            scope="GET /api/threads",
        )

        if thread_list:
            newest_tid = thread_list[0].get("id", "")
            detail_status, detail = hub.api("GET", f"/api/threads/{newest_tid}")
            refs = detail.get("refs", [])
            has_seed_ref = any(r.get("ref_kind") in ("note", "seed") for r in refs)
            reporter.check(
                "thread leg: thread carries seed ref from the source note",
                has_seed_ref,
                f"refs={refs}",
                scope=f"GET /api/threads/{newest_tid} refs",
            )

        assert_clean(reporter, page, errors, "thread 1440 (context-menu)")
    finally:
        context.close()

    # ── Part 2: HS-152 Hands — yolo tool call (desk.list) ────────────
    # Default control_mode is yolo; the walk's fake engine emits desk.list
    # which is evidence_read → auto-admitted → receipted.

    for width, height in ((1440, 900), (393, 852)):
        context, page, errors = browser_context(browser, width, height)
        try:
            # Create a fresh thread for the yolo leg.
            create_status, create_resp = hub.api("POST", "/api/threads", {"title": "Walk yolo tool"})
            reporter.check(
                f"thread yolo {width}: thread created",
                create_status == 201 and bool(create_resp.get("id")),
                f"status={create_status}",
                scope="POST /api/threads",
            )
            yolo_tid = create_resp.get("id", "")

            # Seed desk + onboarding, then navigate to the thread.
            hub.api("POST", "/api/desk/seed")
            hub.api("PUT", "/api/setup/onboarding", {"disposition": "completed"})
            go(page, hub, f"/?open=thread:{yolo_tid}")
            page.wait_for_timeout(2000)

            # Send a turn that triggers desk.list.
            yolo_composer = page.locator(".thread-composer-input")
            try:
                yolo_composer.wait_for(timeout=10000)
            except Exception:
                pass
            reporter.check(
                f"thread yolo {width}: composer visible",
                yolo_composer.count() >= 1,
                scope=".thread-composer-input",
            )
            yolo_composer.fill("List my notes")
            page.locator("button.desk-chip", has_text="Send").click()

            # Wait for the tool row to reach receipted (yolo auto-admits desk.list).
            receipted = _wait_tool_row_state(page, "receipted", timeout=25000)
            reporter.check(
                f"thread yolo {width}: tool row reaches DONE (receipted)",
                receipted,
                scope='[data-testid="tool-row"][data-tool-state="receipted"]',
            )

            # Assert the receipt short-id is present.
            receipt_el = page.locator(".thread-tool-receipt")
            reporter.check(
                f"thread yolo {width}: receipt short-id visible",
                receipt_el.count() >= 1,
                scope=".thread-tool-receipt",
            )

            # Assert the result block with note content exists.
            result_block = page.locator('[data-testid="result-block"]')
            reporter.check(
                f"thread yolo {width}: result block rendered",
                result_block.count() >= 1,
                scope='[data-testid="result-block"]',
            )

            # Assert the RAW fold is present.
            raw_fold = page.locator('[data-testid="raw-fold"]')
            reporter.check(
                f"thread yolo {width}: RAW fold present",
                raw_fold.count() >= 1,
                scope='[data-testid="raw-fold"]',
            )

            capture(reporter, page, out, f"thread-yolo-receipted-{width}.png",
                    f"yolo desk.list receipted with result block + RAW at {width}px")

            assert_clean(reporter, page, errors, f"thread yolo {width}")
        finally:
            context.close()

    # ── Part 3: HS-152 Hands — safe-mode tool call (desk.create) ─────
    # Switch control_mode to safe, then drive desk.create (effect_proposal →
    # held → decision box → Allow once → receipted).

    cm_status, cm_resp = hub.api("PUT", "/api/authority/control-mode", {"control_mode": "safe"})
    reporter.check(
        "thread safe: control_mode switched to safe",
        cm_status == 200,
        f"status={cm_status} resp={str(cm_resp)[:200]}",
        scope="PUT /api/authority/control-mode",
    )

    for width, height in ((1440, 900), (393, 852)):
        context, page, errors = browser_context(browser, width, height)
        try:
            create_status, create_resp = hub.api("POST", "/api/threads", {"title": "Walk safe tool"})
            reporter.check(
                f"thread safe {width}: thread created",
                create_status == 201 and bool(create_resp.get("id")),
                f"status={create_status}",
                scope="POST /api/threads",
            )
            safe_tid = create_resp.get("id", "")

            hub.api("POST", "/api/desk/seed")
            hub.api("PUT", "/api/setup/onboarding", {"disposition": "completed"})
            go(page, hub, f"/?open=thread:{safe_tid}")
            page.wait_for_timeout(2000)

            safe_composer = page.locator(".thread-composer-input")
            try:
                safe_composer.wait_for(timeout=10000)
            except Exception:
                pass
            safe_composer.fill("Create a note for me")
            page.locator("button.desk-chip", has_text="Send").click()

            # Wait for the decision box (effect_proposal held in safe mode).
            decision_box = page.locator('[data-testid="decision-box"]')
            box_appeared = False
            try:
                decision_box.wait_for(timeout=25000)
                box_appeared = True
            except Exception:
                pass
            reporter.check(
                f"thread safe {width}: decision box renders",
                box_appeared,
                scope='[data-testid="decision-box"]',
            )
            if box_appeared:
                # Verify all three verbs are present.
                reporter.check(
                    f"thread safe {width}: Allow once verb present",
                    page.locator('[data-testid="allow-once"]').count() >= 1,
                    scope='[data-testid="allow-once"]',
                )
                reporter.check(
                    f"thread safe {width}: Allow always verb present",
                    page.locator('[data-testid="allow-always"]').count() >= 1,
                    scope='[data-testid="allow-always"]',
                )
                reporter.check(
                    f"thread safe {width}: Deny verb present",
                    page.locator('[data-testid="deny"]').count() >= 1,
                    scope='[data-testid="deny"]',
                )
                capture(reporter, page, out, f"thread-safe-held-{width}.png",
                        f"safe desk.create held with decision box at {width}px")

                # Click Allow once.
                page.locator('[data-testid="allow-once"]').click()

                # Wait for receipted.
                receipted = _wait_tool_row_state(page, "receipted", timeout=25000)
                reporter.check(
                    f"thread safe {width}: Allow once -> tool row receipted",
                    receipted,
                    scope='[data-testid="tool-row"][data-tool-state="receipted"]',
                )
                capture(reporter, page, out, f"thread-safe-receipted-{width}.png",
                        f"safe desk.create receipted after Allow once at {width}px")

            assert_clean(reporter, page, errors, f"thread safe {width}")
        finally:
            context.close()

    # Restore control_mode to yolo for any subsequent legs.
    hub.api("PUT", "/api/authority/control-mode", {"control_mode": "yolo"})


def measured_tasks(reporter: Reporter, page: Any, ids: dict[str, str]) -> None:
    ledger = ClickLedger(reporter, "Tasks", "1", "settled populated Door after first-value handoff")
    door = normal_door(page)
    overdue = door_column(page, "Overdue")
    reporter.check("click-depth Tasks is direct board evidence", overdue.locator(".door-card", has_text=f"{FIXTURE_PREFIX} unblock overdue Door").count() == 0,
                   "completed fixture is absent; Now remains direct task evidence", scope="Overdue and Now Door columns")
    reporter.check("click-depth Tasks has settled Now card and count", door_column(page, "Now").locator(".door-card", has_text=f"{FIXTURE_PREFIX} review Door today").count() == 1 and door_column(page, "Now").get_by_label("1 now items", exact=True).is_visible(), scope="Now Door column")
    reporter.check("click-depth Tasks uses zero clicks", len(ledger.clicks) == 0, scope="ClickLedger Tasks")
    ledger.close(".door-board-section .door-board-column:has(h4:text-is('Now'))", "PASS")


def measured_upcoming(reporter: Reporter, page: Any) -> None:
    ledger = ClickLedger(reporter, "Upcoming", "1+", "same settled populated Door")
    rail = normal_door(page).locator(".door-upcoming-rail")
    reporter.check("click-depth Upcoming is direct rail evidence", rail.locator('[data-upcoming-source="calendar_event"]', has_text=f"{FIXTURE_PREFIX} calendar fixture").count() == 1,
                   scope=".door-upcoming-rail calendar row")
    reporter.check("click-depth Upcoming uses zero clicks", len(ledger.clicks) == 0, scope="ClickLedger Upcoming")
    ledger.close('.door-upcoming-rail [data-upcoming-source="calendar_event"]', "PASS")


def measured_schedule_reachability(reporter: Reporter, page: Any) -> None:
    ledger = ClickLedger(reporter, "Open schedule creation", "2", "same settled populated Door")
    rail = normal_door(page).locator(".door-upcoming-rail")
    button = rail.get_by_role("button", name="Schedule recording", exact=True)
    ledger.click(button, "Door rail → Schedule recording", '.door-upcoming-rail button[name="Schedule recording"]')
    form = page.locator("#schedule\\:__create__")
    form.wait_for(timeout=15000)
    reporter.check("click-depth schedule form opens after one Door click", form.is_visible() and len(ledger.clicks) == 1, scope="ClickLedger Schedule + #schedule\\:__create__")
    ledger.close("#schedule\\:__create__", "PASS")
    form.get_by_role("button", name="Cancel", exact=True).click()
    form.wait_for(state="detached", timeout=15000)


def leg_click_depth(reporter: Reporter, browser: Any, hub: Hub, ids: dict[str, str]) -> None:
    context, page, errors = browser_context(browser, 1440, 900)
    try:
        go(page, hub)
        measured_tasks(reporter, page, ids)
        measured_upcoming(reporter, page)
        measured_schedule_reachability(reporter, page)
        assert_clean(reporter, page, errors, "click-depth")
    finally:
        context.close()


def leg_doorframe(reporter: Reporter, browser: Any, hub: Hub, out: Path) -> None:
    context, page, errors = browser_context(browser, 393, 852)
    try:
        go(page, hub)
        normal_door(page)
        chrome = page.locator(".desk-menubar")
        go_button = chrome.get_by_role("button", name="Go", exact=True)
        reporter.check("393 Go is visible Desk chrome control", go_button.is_visible(), scope=".desk-menubar")
        go_button.click()
        menu = page.get_by_role("menu", name="Go menu")
        meetings = menu.get_by_role("menuitem", name="Meetings")
        reporter.check("393 Go owns Meetings registered app", meetings.is_visible(), scope='role=menu[name="Go menu"]')
        capture(reporter, page, out, "go-menu-393.png", "393px Go menu with Meetings entry")
        meetings.click()
        reporter.check("393 Go Meetings opens registered Meetings surface", page.locator("#surface-meetings").is_visible(), scope="#surface-meetings")
        capture(reporter, page, out, "go-meetings-393.png", "393px Go activates Meetings surface")
        assert_clean(reporter, page, errors, "doorframe Go 393", allow_board_scroll=True)
    finally:
        context.close()

    results: list[dict[str, Any]] = []
    for ordinal in range(1, 16):
        context, page, errors = browser_context(browser, 1440, 900)
        try:
            go(page, hub, "/meetings")
            registered = page.locator('[data-surface-registry-state="registered"]')
            registered.wait_for(state="attached", timeout=15000)
            surface = page.locator("#surface-meetings")
            surface.wait_for(timeout=15000)
            visible = surface.is_visible()
            reporter.check(f"deep-link {ordinal:02d}/15 registered Meetings visible", visible, scope=f"fresh desktop document {ordinal} /meetings")
            assert_clean(reporter, page, errors, f"deep-link desktop {ordinal:02d}")
            if ordinal in (1, 15):
                capture(reporter, page, out, f"meetings-deep-link-{ordinal:02d}-1440.png", f"fresh /meetings arrival {ordinal}/15")
            results.append({"ordinal": ordinal, "viewport": "1440x900", "route": "/meetings", "result": "PASS"})
            print(f"  DEEP-LINK  {ordinal:02d}/15 viewport=1440x900 route=/meetings result=PASS", flush=True)
        finally:
            context.close()
    context, page, errors = browser_context(browser, 393, 852)
    try:
        go(page, hub, "/meetings")
        page.locator('[data-surface-registry-state="registered"]').wait_for(state="attached", timeout=15000)
        surface = page.locator("#surface-meetings")
        surface.wait_for(timeout=15000)
        reporter.check("narrow fresh /meetings reaches registered surface", surface.is_visible(), scope="fresh 393px /meetings document")
        capture(reporter, page, out, "meetings-deep-link-393.png", "fresh narrow /meetings registered arrival")
        assert_clean(reporter, page, errors, "deep-link narrow")
        results.append({"ordinal": 1, "viewport": "393x852", "route": "/meetings", "result": "PASS"})
        print("  DEEP-LINK  01/01 viewport=393x852 route=/meetings result=PASS", flush=True)
    finally:
        context.close()
    reporter.current.facts["deep_links"] = results  # type: ignore[union-attr]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_pairs(reporter: Reporter, out: Path, pairs_path: Path, pairs_md_path: Path) -> list[dict[str, Any]]:
    before = ASSETS / "audit-b-shots"
    items = [
        (before / "chair-home-1440.png", out / "after-chair-home-1440.png", "1440×900", "populated Door", "different", "Chair scattered lanes → Door board + upcoming rail"),
        (before / "chair-home-393.png", out / "after-chair-home-393.png", "393×852", "populated Door", "different", "narrow Door board + rail; Go shown separately"),
        (before / "cadence-surface-1440.png", out / "after-cadence-surface-1440.png", "1440×900", "schedule form", "different", "schedule create begins on Door, not Cadence"),
        (before / "cadence-surface-393.png", out / "after-cadence-surface-393.png", "393×852", "schedule form", "different", "narrow schedule create begins on Door, not Cadence"),
        (before / "first-value-capture-1440.png", out / "cold-first-value-1440.png", "1440×900", "First Sentence", "parity", "First Sentence remains one job"),
        (before / "first-value-capture-393.png", out / "cold-first-value-393.png", "393×852", "First Sentence", "parity", "First Sentence remains one job"),
    ]
    rows: list[dict[str, Any]] = []
    for before_path, after_path, viewport, state, relation, claim in items:
        exists = before_path.exists() and after_path.exists()
        before_hash = sha256(before_path) if before_path.exists() else "MISSING"
        after_hash = sha256(after_path) if after_path.exists() else "MISSING"
        identical = exists and before_hash == after_hash
        reporter.check(f"pair assets exist: {after_path.name}", exists, f"before={before_path.exists()} after={after_path.exists()}", scope="before/after pair manifest")
        if relation == "different":
            reporter.check(f"claimed changed pair is not byte-identical: {after_path.name}", not identical,
                           "claimed changed pair is byte-identical; inspect state/paths" if identical else "hashes differ", scope="SHA-256 false-positive tell")
        rows.append({
            "before": str(before_path.relative_to(REPO)), "after": str(after_path.relative_to(REPO)), "viewport": viewport,
            "state": state, "claim": claim, "assertion_ids": ["container-scoped Door assertions", "SHA-256 false-positive tell"],
            "before_sha256": before_hash, "after_sha256": after_hash, "expected_byte_relationship": relation,
            "byte_identical": identical, "owner_review": "pending owner shot review",
        })
    for filename, claim in (("door-populated-zoom200.png", "200% populated Door accessibility evidence"), ("door-focus-zoom200.png", "200% Door keyboard focus evidence"), ("door-calendar-rail-1440.png", "Settings-fed ICS rail")):
        path = out / filename
        rows.append({"before": None, "after": str(path.relative_to(REPO)), "viewport": "720×450 CSS / DSF 2" if "zoom200" in filename else "1440×900",
                     "state": "accessibility evidence" if "zoom200" in filename else "calendar rail", "claim": claim,
                     "assertion_ids": ["container-scoped assertions"], "before_sha256": None,
                     "after_sha256": sha256(path) if path.exists() else "MISSING", "expected_byte_relationship": "no comparable Audit-B before",
                     "byte_identical": None, "owner_review": "pending owner shot review"})
    pairs_path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    lines = ["# HS-144-06 before/after pairs", "", "Owner review is pending. Hash inequality is a false-positive tell only; the container-scoped assertions in `story-06-walk-report.md` establish the factual claim.", "", "| Before | After | Viewport | State | Relation | SHA-256 tell | Owner review |", "|---|---|---|---|---|---|---|"]
    for row in rows:
        before_text = row["before"] or "No comparable Audit-B 200% before"
        hash_tell = "n/a" if row["byte_identical"] is None else ("BYTE-IDENTICAL (FAIL for different)" if row["byte_identical"] else "different bytes")
        lines.append(f"| `{before_text}` | `{row['after']}` | {row['viewport']} | {row['state']} | {row['expected_byte_relationship']} | {hash_tell} | {row['owner_review']} |")
    pairs_md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rows


def write_report(reporter: Reporter, out: Path, report_path: Path, json_path: Path, pairs_path: Path, pairs_md_path: Path, partial: bool) -> None:
    payload = {
        "story": "HS-144-06", "mode": "partial" if partial else "full", "result": "PASS" if reporter.passed else "FAIL",
        "legs": {name: asdict(leg) for name, leg in reporter.legs.items()},
        "click_depth": [asdict(row) for row in reporter.click_rows], "shots": reporter.shots,
        "findings": reporter.findings, "cleanup": reporter.cleanup, "cleanup_ok": reporter.cleanup_ok,
        "paths": {"shots": str(out.relative_to(REPO)), "pairs_json": str(pairs_path.relative_to(REPO)), "pairs_md": str(pairs_md_path.relative_to(REPO))},
    }
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = ["# The cold Door walk report (born HS-144-06; nine legs as of HS-148)", "", f"**Mode:** {'partial diagnostic walk' if partial else 'full cold walk'}", f"**Result:** {'PASS' if reporter.passed else 'FAIL'}", "", "## Leg results", "", "| Leg | Result | Timing / fact | Assertion scope |", "|---|---|---|---|"]
    for name in ALL_LEGS:
        leg = reporter.legs.get(name)
        if leg is None:
            lines.append(f"| {name} | NOT RUN | — | partial diagnostic walk |")
            continue
        timing = ""
        if leg.elapsed_ms is not None:
            timing = f"{leg.elapsed_ms:.3f} ms"
        elif leg.facts:
            timing = "; ".join(f"{key}={value}" for key, value in leg.facts.items() if key in {"first_value_mode", "completion_ms"})
        scopes = sorted({record.assertion_scope for record in leg.assertions if record.assertion_scope})
        lines.append(f"| {name} | {'PASS' if leg.passed else 'FAIL'} | {timing or '—'} | {'; '.join(scopes[:2]) or 'see assertions'} |")
    lines.extend(["", "## First-value truth", "", "- `first_value_mode=typed_fallback`: this cold fresh HOME had no transcription callback/model. The walk verifies the real WebSocket named refusal `transcription_unavailable`; it never supplies or calls a fake transcript.", "- The timer begins immediately before typing into the actual First Sentence pad and stops only once the actual Save draft & continue handoff visibly reaches the normal Desk. The report separately proves the resulting note custody through `GET /api/notes`.", "", "## Completion semantics", "", "- Quiet success is the authoritative Door card disappearing. `completion_ms` is same-page `performance.now()` click-to-card-detachment, followed by `GET /api/door` confirmation. No success toast was added or claimed.", "- The named in-place receipt is separately proven on a real stale Thought `HTTP 409` refusal.", "", "## Click-depth ledger", "", "| Measure | Audit-B before | After | Recorded browser clicks | Final evidence selector | Result |", "|---|---:|---:|---|---|---|"])
    for row in reporter.click_rows:
        labels = ", ".join(click["label"] for click in row.clicks) or "none"
        lines.append(f"| {row.measure} | {row.baseline} | {len(row.clicks)} | {labels} | `{row.final_evidence_selector}` | {row.result} |")
    lines.extend(["", "## Assertion details", ""])
    for leg in reporter.legs.values():
        lines.append(f"### {leg.name} — {'PASS' if leg.passed else 'FAIL'}")
        for record in leg.assertions:
            lines.append(f"- {'PASS' if record.passed else 'FAIL'} — **{record.label}**. Scope: {record.assertion_scope or 'not recorded'}. {record.detail}".rstrip())
        for finding in leg.findings:
            lines.append(f"- FINDING — {finding}")
        lines.append("")
    lines.extend(["## Evidence", "", f"- Shots: `{out.relative_to(REPO)}/`", f"- Machine JSON: `{json_path.relative_to(REPO)}`", f"- Pair manifest: `{pairs_path.relative_to(REPO)}` and `{pairs_md_path.relative_to(REPO)}`", "- Owner review / beauty verdict / Tuesday answer: pending owner shot review; this worker does not fabricate an owner nod.", "", "## Cleanup", ""])
    lines.extend(f"- {item}" for item in reporter.cleanup)
    lines.append(f"- cleanup={'pass' if reporter.cleanup_ok else 'fail'}")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def remove_path(reporter: Reporter, path: Path, label: str) -> None:
    try:
        if path.exists():
            shutil.rmtree(path)
            reporter.cleanup_line(f"deleted {label}: {path}")
        else:
            reporter.cleanup_line(f"already absent {label}: {path}")
    except Exception as error:  # noqa: BLE001
        reporter.cleanup_line(f"could not delete {label}: {path}: {error}", ok=False)


def run_walk(args: argparse.Namespace) -> int:
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    report_path = Path(args.report).resolve()
    json_path = Path(args.report_json).resolve()
    pairs_path = Path(args.pairs).resolve()
    pairs_md_path = Path(args.pairs_md).resolve()
    for path in (report_path, json_path, pairs_path, pairs_md_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    selected = tuple(args.only) if args.only else ALL_LEGS
    invalid = sorted(set(selected) - set(ALL_LEGS))
    if invalid:
        raise SystemExit(f"unknown --only leg(s): {', '.join(invalid)}")
    partial = set(selected) != set(ALL_LEGS)
    reporter = Reporter()
    root = Path(tempfile.mkdtemp(prefix="hs144-door-walk-", dir=args.tmp_root or None))
    home, env = isolated_environment(root)
    fixture_dir = root / "fixtures"
    fixture_dir.mkdir()
    hub = Hub(free_port(), home, env, tool_engine="thread" in selected)
    browser: Any = None
    ids: dict[str, str] = {}
    try:
        hub.start(out)
        from playwright.sync_api import sync_playwright
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=not args.headed)

        # Cold narrow must happen before the actual typed custody handoff changes
        # onboarding in the only truthful fresh database.
        if "cold" in selected:
            reporter.start_leg("cold")
            capture_cold_narrow(reporter, browser, hub, out)
            leg_cold(reporter, browser, hub, out)

        # Seeding never occurs until the actual first-value handoff has occurred.
        needs_populated = any(leg in selected for leg in ("reveal", "completion", "schedule", "calendar", "one-tap", "click-depth", "doorframe", "menus", "thread"))
        if needs_populated:
            if "cold" not in selected:
                reporter.finding("partial walk bypassed cold first-value handoff; populated legs are diagnostic only")
                # A partial populated diagnosis still opens the normal Chair through
                # the product's real Continue later action, never direct onboarding.
                context, page, _errors = browser_context(browser, 1440, 900)
                try:
                    go(page, hub)
                    first = page.get_by_test_id("chair-first-value")
                    first.get_by_role("button", name="Continue later", exact=True).click()
                    normal_door(page)
                finally:
                    context.close()
            reporter.current = None
            ids = seed_populated_truth(reporter, hub)

        def call(name: str, fn: Callable[[], None]) -> None:
            reporter.start_leg(name)
            try:
                fn()
            except Exception as error:  # noqa: BLE001 — keep later independent legs diagnosable
                reporter.current.passed = False  # type: ignore[union-attr]
                reporter.finding(f"{type(error).__name__}: {error}")
                print(f"  LEG-FAIL  {name}: {type(error).__name__}: {error}", flush=True)

        if "reveal" in selected:
            call("reveal", lambda: leg_reveal(reporter, browser, hub, out, ids))
        if "completion" in selected:
            call("completion", lambda: leg_completion(reporter, browser, hub, out, ids))
        if "schedule" in selected:
            call("schedule", lambda: leg_schedule(reporter, browser, hub, out))
        if "calendar" in selected:
            call("calendar", lambda: leg_calendar(reporter, browser, hub, out, fixture_dir))
        if "one-tap" in selected:
            call("one-tap", lambda: leg_one_tap(reporter, browser, hub, out, fixture_dir))
        if "click-depth" in selected:
            call("click-depth", lambda: leg_click_depth(reporter, browser, hub, ids))
        if "doorframe" in selected:
            call("doorframe", lambda: leg_doorframe(reporter, browser, hub, out))
        if "menus" in selected:
            call("menus", lambda: leg_menus(reporter, browser, hub, out))
        if "thread" in selected:
            call("thread", lambda: leg_thread(reporter, browser, hub, out))
    except Exception as error:  # noqa: BLE001
        name = reporter.current.name if reporter.current else "bootstrap"
        if reporter.current is None:
            reporter.start_leg(name)
        reporter.current.passed = False  # type: ignore[union-attr]
        reporter.finding(f"fatal {type(error).__name__}: {error}")
        print(f"  FATAL  {type(error).__name__}: {error}", flush=True)
    finally:
        if browser is not None:
            try:
                browser.close()
                reporter.cleanup_line("closed Playwright browser")
            except Exception as error:  # noqa: BLE001
                reporter.cleanup_line(f"could not close Playwright browser: {error}", ok=False)
        hub.stop(reporter)
        # Durable reports must survive a failed run, but all private state and
        # local ICS fixture live under this root and are deleted visibly.
        remove_path(reporter, fixture_dir, "ICS fixture tree")
        remove_path(reporter, root, "walk HOME/XDG/TMP tree")
        try:
            build_pairs(reporter, out, pairs_path, pairs_md_path)
        except Exception as error:  # noqa: BLE001
            reporter.start_leg("pair-manifest")
            reporter.current.passed = False  # type: ignore[union-attr]
            reporter.finding(f"pair manifest failure: {error}")
        write_report(reporter, out, report_path, json_path, pairs_path, pairs_md_path, partial)

    print("\n== WALK RESULT ==", flush=True)
    for name in ALL_LEGS:
        leg = reporter.legs.get(name)
        if leg is None:
            print(f"  {name:12} NOT RUN", flush=True)
        else:
            timing = f" elapsed_ms={leg.elapsed_ms:.3f}" if leg.elapsed_ms is not None else ""
            print(f"  {name:12} {'PASS' if leg.passed else 'FAIL'}{timing}", flush=True)
    print("\n== CLICK DEPTH ==", flush=True)
    for row in reporter.click_rows:
        print(f"  {row.measure}: before={row.baseline} after={len(row.clicks)} clicks={[click['label'] for click in row.clicks] or ['none']}", flush=True)
    print("\n== ARTIFACTS ==", flush=True)
    print(f"  shots={out}", flush=True)
    print(f"  report={report_path}", flush=True)
    print(f"  report_json={json_path}", flush=True)
    print(f"  pairs={pairs_path}", flush=True)
    print(f"  cleanup={'pass' if reporter.cleanup_ok else 'fail'}", flush=True)
    return 0 if reporter.passed else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HS-144-06 cold Door walk")
    subparsers = parser.add_subparsers(dest="mode")
    serve_parser = subparsers.add_parser("serve", help="child: start unseeded isolated hub")
    serve_parser.add_argument("--port", type=int, required=True)
    serve_parser.add_argument("--token", required=True)
    serve_parser.add_argument("--tool-engine", action="store_true", help="seed a fake tool engine for the thread Hands leg")
    subparsers.add_parser("refresh-calendar", help="child: run production CalendarIngestConductor.refresh")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="durable screenshot directory")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="machine-written Markdown report")
    parser.add_argument("--report-json", default=str(DEFAULT_JSON), help="machine-written JSON report")
    parser.add_argument("--pairs", default=str(DEFAULT_PAIRS), help="before/after pair JSON")
    parser.add_argument("--pairs-md", default=str(DEFAULT_PAIRS_MD), help="before/after pair Markdown")
    parser.add_argument("--tmp-root", default="", help="parent directory for disposable walk state")
    parser.add_argument("--only", action="append", choices=ALL_LEGS, help="diagnostic leg only; repeatable")
    parser.add_argument("--headed", action="store_true", help="show Chromium for attended diagnosis")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.mode == "serve":
        return serve(args.port, args.token, tool_engine=args.tool_engine)
    if args.mode == "refresh-calendar":
        return refresh_calendar()
    return run_walk(args)


if __name__ == "__main__":
    raise SystemExit(main())
