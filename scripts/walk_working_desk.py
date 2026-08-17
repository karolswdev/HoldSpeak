#!/usr/bin/env python3
"""HS-132-14 — The Working Desk walk harness (reusable).

Stands up a REAL hub against an isolated HOME, seeds it, and photographs
every surface Phase 132 repaired at both 1440x900 and 393x852, asserting
zero console errors on every walked path.

Two modes, one file:

    # serve only (the subprocess the walk drives; also usable by hand)
    HOME=$(mktemp -d) uv run python scripts/walk_working_desk.py serve \
        --port 8793 --token walk-owner-token

    # the whole walk: boots its own hub, shoots, reaps
    HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=~/Library/Caches/ms-playwright \
        uv run python scripts/walk_working_desk.py walk --port 8793

Options for ``walk``:

    --hub-url URL   drive an already-running hub instead of booting one
    --token TOKEN   owner token for the hub (default: a fixed walk token)
    --out DIR       screenshot directory (default: this phase's assets)
    --lan URL       include the live-metal ``.43`` receipt-honesty leg
    --only NAME     run one leg by name (repeatable)

Every screenshot is named ``<surface>-<state>-<width>.png``. The harness
exits non-zero on the first failed assertion; console errors are collected
per page and reported as findings with their shot.
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUT = (
    REPO / "pm/roadmap/holdspeak/phase-132-the-working-desk/assets/hs-132-14"
)
DEFAULT_TOKEN = "hs-132-14-walk-owner-token"
VIEWPORTS = ((1440, 900), (393, 852))

# ---------------------------------------------------------------- reporting

FAILS: list[str] = []
FINDINGS: list[str] = []
SHOTS: list[tuple[str, str]] = []
PASSES = 0


def check(label: str, cond: bool, detail: str = "") -> bool:
    global PASSES
    if cond:
        PASSES += 1
        print(f"  PASS  {label}" + (f" — {detail}" if detail else ""), flush=True)
    else:
        FAILS.append(f"{label} — {detail}" if detail else label)
        print(f"  FAIL  {label}" + (f" — {detail}" if detail else ""), flush=True)
    return bool(cond)


def finding(text: str) -> None:
    FINDINGS.append(text)
    print(f"  FINDING  {text}", flush=True)


def section(title: str) -> None:
    print(f"\n== {title} ==", flush=True)


# ------------------------------------------------------------------- serving


def _populate(db: Any, principal: Any) -> None:
    """Give the walk something true to photograph.

    Everything here goes through the product's OWN services and repositories
    — the same code paths the MCP tools and the capture pipeline call. It is
    real data in the real schema, not a DOM fixture. Two things have no HTTP
    mint route at all (a decision record, a recorded meeting's action items),
    which is exactly why they are written here rather than over the wire.
    """
    from datetime import datetime, timedelta

    from holdspeak.services.decision_record_service import DecisionRecordService

    # --- a recorded meeting with commitments: Follow-through's four lanes ---
    try:
        from holdspeak.meeting_session.models import IntelSnapshot, MeetingState
    except Exception:  # pragma: no cover - layout drift
        from holdspeak.models import IntelSnapshot, MeetingState  # type: ignore

    now = datetime.now()
    overdue_due = (now - timedelta(days=6)).date().isoformat()
    soon_due = (now + timedelta(days=3)).date().isoformat()
    db.meetings.save_meeting(
        MeetingState(
            id="walk-meeting-1",
            started_at=now - timedelta(days=2),
            title="Phase 132 desk review",
            intel=IntelSnapshot(
                timestamp=0.0,
                topics=["placement dial", "write receipts"],
                summary="Reviewed the six-pillar audit and split the repairs.",
                action_items=[
                    {
                        "id": "walk-ai-overdue",
                        "task": "Land the write-receipt channel",
                        "owner": "Karol",
                        "due": overdue_due,
                        "status": "pending",
                        "review_state": "accepted",
                        "created_at": (now - timedelta(days=2)).isoformat(),
                    },
                    {
                        "id": "walk-ai-now",
                        "task": "Photograph the placement dial states",
                        "owner": "Karol",
                        "due": soon_due,
                        "status": "pending",
                        "review_state": "accepted",
                        "created_at": (now - timedelta(days=2)).isoformat(),
                    },
                    {
                        "id": "walk-ai-unassigned",
                        "task": "Decide the streaming-partials question",
                        "owner": None,
                        "due": None,
                        "status": "pending",
                        "review_state": "accepted",
                        "created_at": (now - timedelta(days=2)).isoformat(),
                    },
                    {
                        "id": "walk-ai-done",
                        "task": "Fix the meeting stop callback",
                        "owner": "Karol",
                        "due": None,
                        "status": "done",
                        "review_state": "accepted",
                        "created_at": (now - timedelta(days=2)).isoformat(),
                    },
                ],
            ),
        )
    )

    # --- two decision records, one superseding the other -------------------
    records = DecisionRecordService(db)
    first = records.create(
        principal,
        decision_text="Run meetings intelligence on the homelab .43",
        rationale="Private network, no cloud egress, and the box is idle.",
        alternatives="Cloud provider; this device.",
        owner="Karol",
        source_type="desk",
        source_id="walk-decision-1",
    )
    second = records.create(
        principal,
        decision_text="Keep meetings intelligence on the hub default",
        rationale="Latency beat capacity once the desk streamed tokens live.",
        owner="Karol",
        source_type="desk",
        source_id="walk-decision-2",
    )
    records.supersede(
        principal,
        first["id"],
        second["id"],
        reason="Superseded after the streaming walk.",
    )
    # --- an agent question for the Cadence reply pad ----------------------
    # There is no HTTP route that creates a loop: `LoopCollector` projects
    # `agent_question` loops out of the agent-session registry, and a
    # `POST /api/cadence/run-now` tick persists them. The registry file is
    # the product's own contract (`holdspeak/agent_context/models.py:18`).
    from holdspeak.config.core import CONFIG_DIR

    sessions = Path(CONFIG_DIR) / "agent_sessions.json"
    sessions.parent.mkdir(parents=True, exist_ok=True)
    sessions.write_text(
        json.dumps(
            {
                "sessions": {
                    "walk-sess-1": {
                        "agent": "codex",
                        "session_id": "walk-sess-1",
                        "cwd": str(REPO),
                        "updated_at": now.astimezone().isoformat(),
                        "hook_event_name": "Stop",
                        "repo_root": str(REPO),
                        "project_name": "holdspeak",
                        "awaiting_response": True,
                        "last_assistant_text":
                            "Should the walk harness live in scripts/ or tests/e2e/?",
                        "tmux_pane": "walk:0.1",
                        "pinned": True,
                    }
                }
            },
            indent=2,
        )
    )
    # --- a generated brief: populates the Brief lane (HS-135-07) ----------
    try:
        from holdspeak.services.monday_brief_service import MondayBriefService

        brief = MondayBriefService(db).generate(principal)
        print(f"POPULATED brief={brief.id} headline={brief.headline!r}", flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"BRIEF_FAILED {exc!r}", flush=True)

    print(f"POPULATED records={first['id']}->{second['id']} sessions={sessions}",
          flush=True)


def _seed_and_serve(port: int, token: str, host: str = "127.0.0.1") -> None:
    """Boot the real hub on ``port`` with a seeded, populated desk, and block."""
    import threading

    from holdspeak.db import get_database
    from holdspeak.principals import derive_owner
    from holdspeak.services.desk_service import DeskService
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    db = get_database()
    principal = derive_owner(token, token)
    assert principal is not None, "owner principal could not be derived"
    report = DeskService(db).seed(principal)
    print(f"SEEDED {json.dumps(report, default=str)[:400]}", flush=True)
    try:
        _populate(db, principal)
    except Exception as exc:  # noqa: BLE001 — the walk still runs, and says so
        print(f"POPULATE_FAILED {exc!r}", flush=True)

    # ---- the harness's stand-in for the desktop capture runtime ----------
    # A real live meeting needs a microphone and the transcribe/intel loop
    # (`holdspeak/meeting_session/transcribe_loop.py:277` is the only
    # `segment` emitter; `intel_admission.py:456` the only `intel_token`).
    # Headless, the walk plays that role: it starts a REAL meeting row and
    # pushes the REAL frame vocabulary through the REAL server broadcast, so
    # everything downstream of the hub — socket, bus, LiveCore — is the
    # product. Only the audio→text→intel engine is stood in for.
    live: dict[str, Any] = {"active": False, "id": ""}
    server_ref: dict[str, Any] = {}

    def _emit_capture() -> None:
        server = server_ref.get("server")
        if server is None:
            return
        time.sleep(0.8)
        for idx, text in enumerate(
            (
                "Karol: the desk has to show intelligence arriving, not after the fact.",
                "Karol: and a bookmark must confirm on the glass while we are still live.",
                "Karol: if a write fails, the receipt names it. No silent no-ops.",
            )
        ):
            server.broadcast(
                "segment",
                {
                    "id": f"walk-seg-{idx}",
                    "speaker": "Me",
                    "text": text,
                    "timestamp": float(idx * 12),
                    "source": "mic",
                },
            )
            time.sleep(0.35)
        for chunk in (
            "Three commitments so far: ",
            "land the write-receipt channel, ",
            "photograph the placement dial, ",
            "and decide the streaming-partials question.",
        ):
            server.broadcast("intel_token", {"token": chunk})
            time.sleep(0.25)
        server.broadcast(
            "intel_complete",
            {
                "summary": "Three commitments captured; the desk feedback layer is the theme.",
                "topics": ["write receipts", "placement dial", "streaming partials"],
                "action_items": [
                    {"task": "Land the write-receipt channel"},
                    {"task": "Photograph the placement dial"},
                    {"task": "Decide the streaming-partials question"},
                ],
                "final": False,
            },
        )

    def on_start(**_kwargs: Any) -> dict[str, Any]:
        from datetime import datetime as _dt

        live["active"] = True
        live["id"] = f"walk-live-{int(time.time())}"
        live["started"] = time.time()
        threading.Thread(target=_emit_capture, daemon=True).start()
        return {
            "id": live["id"],
            "meeting_id": live["id"],
            "active": True,
            "status": "recording",
            "title": "Walk live meeting",
            "started_at": _dt.now().isoformat(),
            "formatted_duration": "00:00",
        }

    def on_meeting_stop(**_kwargs: Any) -> dict[str, Any]:
        if not live["active"]:
            raise RuntimeError("No active meeting")
        live["active"] = False
        return {"status": "stopped", "id": live["id"]}

    def on_bookmark(label: str = "") -> dict[str, Any]:
        # Shaped exactly like the runtime's own bookmark payload
        # (`holdspeak/runtime/meeting_glue.py:469-489`): a label and the
        # offset in seconds into the meeting.
        return {
            "label": label,
            "timestamp": max(0.0, time.time() - live.get("started", time.time())),
            "meeting_id": live["id"],
        }

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=on_bookmark,
            on_stop=on_meeting_stop,
            on_start=on_start,
            on_meeting_stop=on_meeting_stop,
            get_state=lambda: {
                "active": live["active"],
                "id": live["id"],
                "status": "recording" if live["active"] else "idle",
                "activity": {
                    "state": "recording" if live["active"] else "idle",
                    "source": "runtime",
                },
            },
        ),
        host=host,
        port=port,
        auth_token=token,
    )
    server_ref["server"] = server
    url = server.start()
    print(f"HUB_READY {url}", flush=True)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:  # pragma: no cover - operator interrupt
        pass


class Hub:
    """A real hub in its own process, with its own isolated HOME."""

    def __init__(self, port: int, token: str, home: str | None = None) -> None:
        self.port = port
        self.token = token
        self.home = home or os.environ.get("HOME", "")
        self.url = f"http://127.0.0.1:{port}"
        self.proc: subprocess.Popen[str] | None = None

    def start(self, timeout: float = 90.0) -> "Hub":
        env = dict(os.environ)
        env["HOME"] = self.home
        env["HOLDSPEAK_WEB_PORT"] = str(self.port)
        env.setdefault("PYTHONUNBUFFERED", "1")
        self.proc = subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "serve",
                "--port",
                str(self.port),
                "--token",
                self.token,
            ],
            cwd=str(REPO),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        print(f"  hub pid={self.proc.pid} home={self.home} port={self.port}", flush=True)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                out = self.proc.stdout.read() if self.proc.stdout else ""
                raise RuntimeError(f"hub died on boot:\n{out[-4000:]}")
            if self.healthy():
                return self
            time.sleep(0.4)
        raise RuntimeError(f"hub never became healthy at {self.url}")

    def healthy(self, timeout: float = 1.0) -> bool:
        try:
            with socket.create_connection(("127.0.0.1", self.port), timeout=timeout):
                pass
        except OSError:
            return False
        try:
            self.api("GET", "/health")
            return True
        except Exception:
            return False

    def stop(self) -> None:
        if self.proc is None or self.proc.poll() is not None:
            return
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:  # pragma: no cover
            self.proc.kill()
            self.proc.wait(timeout=10)
        # The port must actually be free again — that is what the
        # write-receipt backstop leg depends on.
        for _ in range(40):
            if not self.healthy(timeout=0.3):
                return
            time.sleep(0.25)

    # --- HTTP -----------------------------------------------------------

    def api(
        self, method: str, path: str, body: Any = None, timeout: float = 30.0
    ) -> tuple[int, Any]:
        data = None
        headers = {"X-HoldSpeak-Token": self.token}
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(
            self.url + path, data=data, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", "replace")
                status = resp.status
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", "replace")
            status = exc.code
        try:
            return status, json.loads(raw)
        except Exception:
            return status, raw


# ------------------------------------------------------------------ browser


class Shooter:
    """A page at one viewport that refuses to hide console errors."""

    def __init__(self, page: Any, width: int, out: Path) -> None:
        self.page = page
        self.width = width
        self.out = out
        self.console_errors: list[str] = []
        page.on("pageerror", lambda e: self.console_errors.append(f"pageerror: {e}"))
        page.on(
            "console",
            lambda m: (
                self.console_errors.append(f"console.{m.type}: {m.text}")
                if m.type == "error"
                else None
            ),
        )

    def shot(self, surface: str, state: str, proves: str = "") -> Path:
        self.out.mkdir(parents=True, exist_ok=True)
        name = f"{surface}-{state}-{self.width}.png"
        path = self.out / name
        self.page.screenshot(path=str(path), full_page=False)
        SHOTS.append((name, proves))
        print(f"  SHOT  {name}" + (f" — {proves}" if proves else ""), flush=True)
        return path

    def assert_clean(self, where: str) -> None:
        noisy = [
            e
            for e in self.console_errors
            if not _ignorable_console(e)
        ]
        if noisy:
            finding(f"console errors on {where} @{self.width}: {noisy[:6]}")
        check(f"zero console errors — {where} @{self.width}", not noisy, str(noisy[:3]))
        self.console_errors.clear()


def _ignorable_console(text: str) -> bool:
    """Network noise the walk itself causes (the hub-stopped leg)."""
    lowered = text.lower()
    return any(
        token in lowered
        for token in (
            "failed to load resource",
            "err_connection_refused",
            "websocket",
            "net::err",
        )
    )


def goto(shooter: Shooter, hub: Hub, route: str = "/") -> None:
    sep = "&" if "?" in route else "?"
    shooter.page.goto(
        f"{hub.url}{route}{sep}token={hub.token}", wait_until="domcontentloaded"
    )
    try:
        shooter.page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    shooter.page.wait_for_timeout(1200)


# --------------------------------------------------------------------- main


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)

    p_serve = sub.add_parser("serve", help="boot a seeded hub and block")
    p_serve.add_argument("--port", type=int, default=0)
    p_serve.add_argument("--token", default=DEFAULT_TOKEN)

    p_walk = sub.add_parser("walk", help="run the screenshot walk")
    p_walk.add_argument("--port", type=int, default=0)
    p_walk.add_argument("--token", default=DEFAULT_TOKEN)
    p_walk.add_argument("--hub-url", default=None)
    p_walk.add_argument("--out", default=str(DEFAULT_OUT))
    p_walk.add_argument("--lan", default=None)
    p_walk.add_argument("--only", action="append", default=None)

    args = parser.parse_args(argv)

    if args.mode == "serve":
        _seed_and_serve(args.port or _free_port(), args.token)
        return 0

    from scripts.walk_working_desk_legs import run_walk  # noqa: PLC0415

    return run_walk(args)


if __name__ == "__main__":
    sys.exit(main())
