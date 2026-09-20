#!/usr/bin/env python3
"""HS-202 — THE MEASURED WALK: a surface inventory of every face HoldSpeak has.

Boots the real product twice (a COLD desk and a RICH seeded desk), opens every
surface it can reach at 1440x900 and 393x852, and measures each one against
section B of docs/internal/surface-inventory-2026-09-20/00-rulebook.md, plus the
section-A rules a script can honestly count (U1/U2/U3/U4/A7).

Run (never the owner's HOME, never the microphone):

    HOME=$(mktemp -d) \
    PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \
    uv run python scripts/surface_census_walk.py

Options:
    --desk cold|rich|both     which desk(s) to walk (default both)
    --widths 1440,393         viewport widths
    --only <id> [--only ...]  walk a subset of surface ids
    --out <dir>               output root (default docs/internal/surface-inventory-2026-09-20)
    --no-shots                skip screenshots (measure only)

Writes:
    <out>/01-measured-walk.md   the report
    <out>/census.json           the machine census
    <out>/assets/NN-<surface>-<desk>-<width>.png

Honesty contract: a surface that could not be opened is recorded UNOPENED with
the reason; a measure this rig cannot take is recorded null (NOT ASSESSED),
never 0.
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO / "docs" / "internal" / "surface-inventory-2026-09-20"
MEASURE_JS = (REPO / "scripts" / "surface_census_measure.js").read_text()
TOKEN = "hs-202-surface-census"
WIDTHS = (1440, 393)
HEIGHTS = {1440: 900, 393: 852}


# ─────────────────────────────────────────────────────────── the hub


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class Hub:
    """A real hub in its own process with an isolated HOME."""

    def __init__(self, home: Path, token: str = TOKEN) -> None:
        self.port = _free_port()
        self.token = token
        self.home = home
        self.url = f"http://127.0.0.1:{self.port}"
        self.proc: subprocess.Popen[str] | None = None

    def start(self, timeout: float = 120.0) -> "Hub":
        # This rig serves its OWN hub (the `serve` subcommand below) and never
        # `scripts/walk_working_desk.py serve` — that one calls
        # `DeskService.seed()` + `_populate()` on the way up
        # (walk_working_desk.py:237), so a "cold" desk booted through it would
        # arrive already furnished and the cold column would be a lie.
        env = dict(os.environ)
        env["HOME"] = str(self.home)
        env["HOLDSPEAK_WEB_PORT"] = str(self.port)
        env.setdefault("PYTHONUNBUFFERED", "1")
        self.proc = subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "serve",
                "--port", str(self.port),
                "--token", self.token,
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
        import urllib.request

        try:
            with socket.create_connection(("127.0.0.1", self.port), timeout=timeout):
                pass
        except OSError:
            return False
        try:
            req = urllib.request.Request(
                f"{self.url}/health", headers={"X-HoldSpeak-Token": self.token}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def stop(self) -> None:
        if self.proc is None or self.proc.poll() is not None:
            return
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=10)


def serve_forever(port: int, token: str) -> int:
    """Boot ONE real hub against the ambient HOME and block. Nothing is seeded.

    This is the cold desk's honest boot: `MeetingWebServer` exactly as the
    product starts it, and not one row written.
    """
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}),
        auth_token=token,
        port=port,
    )
    url = server.start()
    print(f"SERVING {url} (unseeded)", flush=True)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        return 0


# ─────────────────────────────────────────── the web bundle (163 law)


def ensure_build() -> None:
    """Build the bundle if any web source is newer than the oldest built chunk.

    The 163 stale-pixels law, copied from tests/e2e/glass_infra.py:_ensure_build.
    """
    built_marker = REPO / "holdspeak" / "static" / "_built" / "index.html"
    assets = built_marker.parent / "assets"
    newest_src = 0.0
    web = REPO / "web"
    for name in ("package.json", "vite.config.ts", "tsconfig.json", "index.html"):
        f = web / name
        if f.exists():
            newest_src = max(newest_src, f.stat().st_mtime)
    for d in ("src", "public"):
        root = web / d
        if root.exists():
            for f in root.rglob("*"):
                if f.is_file():
                    newest_src = max(newest_src, f.stat().st_mtime)
    chunks = [f.stat().st_mtime for f in assets.glob("*.js")] if assets.exists() else []
    built = min(chunks) if (chunks and built_marker.exists()) else 0.0
    if built >= newest_src:
        print("  bundle fresh", flush=True)
        return
    print("  building the web bundle …", flush=True)
    started = time.monotonic()
    result = subprocess.run(
        ["npm", "--prefix", str(web), "run", "build"], capture_output=True, text=True, timeout=600
    )
    if result.returncode != 0:
        raise RuntimeError(f"web build failed:\n{result.stderr[-4000:]}")
    print(f"  bundle rebuilt in {time.monotonic() - started:.1f}s", flush=True)


# ─────────────────────────────────────────────────── browser-side API

_FETCH_JS = """async ([method, path, body, token]) => {
  const response = await fetch(path, {
    method,
    headers: {
      authorization: `Bearer ${token}`,
      ...(body ? {"content-type": "application/json"} : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("json") ? await response.json() : await response.text();
  return {status: response.status, payload};
}"""


class Api:
    """Browser-side fetch through the real hub — the product's own front door."""

    def __init__(self, page: Any, token: str) -> None:
        self.page = page
        self.token = token
        self.failures: list[str] = []

    def call(self, method: str, path: str, body: dict | None = None) -> tuple[int, Any]:
        result = self.page.evaluate(_FETCH_JS, [method, path, body, self.token])
        return result["status"], result["payload"]

    def ok(self, method: str, path: str, body: dict | None = None, *, why: str = "") -> Any:
        status, payload = self.call(method, path, body)
        if status >= 300:
            self.failures.append(f"{method} {path} -> {status} ({why}): {str(payload)[:300]}")
            return None
        return payload


# ─────────────────────────────────────────────────────── the surfaces


@dataclass
class Surface:
    """One face, and the move that opens it."""

    id: str
    name: str
    family: str          # application | pullout | state | chrome | settings
    opener: str          # go:<label> | route:<path> | pullout:<ref-key> | chair | custom:<name>
    root: str | None     # CSS selector of the surface's own element
    door: str            # the stranger's move, or "NO DOOR" (C3)
    needs: str = ""      # what the rich desk must hold for this to be real
    cold: bool = True    # walk it on the cold desk too


# The application manifest is web/src/desk/applications.ts (22 entries).
# `go:` surfaces carry group:"app"|"tool" and so appear in the Go menu
# (web/src/desk/tools.ts:4); the rest have no Go row — a C3 finding recorded
# in `door`, opened here by their demoted route (web/src/routes.tsx:41) or by
# the Desk-menu verb that is their only door.
APPLICATIONS: list[Surface] = [
    Surface("app-chair", "The Chair (home)", "application", "chair", ".chair", "arrival"),
    Surface("app-floor", "The Floor", "application", "custom:floor", ".desk-next", "Dock ▧ / Desk menu"),
    Surface("app-places", "Change places", "application", "go:Change places", "#surface-places", "Go > Change places"),
    Surface("app-speak", "Speak (dictation)", "application", "go:Speak", "#surface-dictation", "Dock ⌁ / Go > Speak"),
    Surface("app-meetings", "Meetings", "application", "go:Meetings", "#surface-meetings", "Dock ▣ / Go > Meetings"),
    Surface("app-agents", "Agents", "application", "go:Agents", "#surface-companion", "Dock / Go > Agents"),
    Surface("app-settings", "Settings", "application", "go:Settings", "#surface-settings", "Dock / Go > Settings"),
    Surface("app-rhythm", "Rhythm (cadence)", "application", "go:Rhythm", "#surface-cadence", "Go > Rhythm"),
    Surface("app-context", "Context", "application", "go:Context", "#surface-constitutional-context", "Go > Context"),
    Surface("app-workbenches", "Workbenches", "application", "go:Workbenches", "#surface-workbenches", "Go > Workbenches"),
    Surface("app-activity", "Activity", "application", "go:Activity", "#surface-activity", "Go > Activity"),
    Surface("app-desk-memory", "Desk memory", "application", "go:Desk memory", "#surface-project-memory", "Go > Desk memory"),
    Surface("app-processes", "Processes", "application", "go:Processes", "#surface-processes", "Go > Processes"),
    Surface("app-commands", "Commands", "application", "go:Commands", "#surface-commands", "Go > Commands"),
    Surface("app-models", "Models (Concierge)", "application", "go:Models", "#surface-concierge", "Go > Models"),
    Surface("app-connections", "Connections", "application", "go:Connections", "#surface-settings", "Go > Connections"),
    Surface("app-ask", "Ask AI", "application", "go:Ask AI", ".desk-ask", "Dock / Go > Ask AI"),
    Surface("app-intelligence", "Intelligence", "application", "custom:intelligence", ".desk-pullout", "Dock ◈"),
    # ── no Go row (C3): opened here by route or by a Desk-menu verb ──
    Surface("app-live", "Live meeting", "application", "route:/live", "#surface-live",
            "NO DOOR: no Go row; reached only from a Record verb (RecordOrb.tsx:69)"),
    Surface("app-new-project", "New Project", "application", "route:/setup", "#surface-project-setup",
            "NO DOOR: no Go row; reached from the Chair's start actions"),
    Surface("app-people", "People", "application", "palette:Open People", "#surface-people",
            "NO DOOR: no Go row; Desk menu > Open People (verbRegistry.ts:336)"),
    Surface("app-components", "Components", "application", "route:/design/components", "#surface-components",
            "NO DOOR: no Go row; a designer's route"),
    Surface("app-runtime-docs", "Runtime docs (an alias onto Settings' Guide wing)", "application",
            "route:/docs/dictation-runtime", "#surface-settings",
            "NO DOOR: no Go row; /docs/dictation-runtime is an alias of configure-settings "
            "scoped to the Guide wing (applications.ts:162), so it draws the Settings window"),
    Surface("app-calendar-snapshot", "Calendar snapshot", "application", "unopenable", "#surface-calendar-snapshot",
            "NO DOOR: opened only by dropping an .ics on the desk (GlassDropLayer.tsx:68); "
            "it needs a dropped-file payload as its scope, which this rig does not forge"),
]

# The pullout kinds are web/src/desk/pullouts/registry.ts (20 kinds, 14 distinct
# components). Each is opened on a seeded object through the product's own
# arrival path, `/?open=<kind>:<id>` (DeskApp.tsx:99).
# Not every PrimitiveKind draws a pull-out. `lib/primitives.ts` gives each kind
# a `surface`: some open a WINDOW, and three open nothing at all
# (`surface: {type:"none"}` -> `compositorSlice.ts:169` breaks). The walk must
# wait for the right container or it records a false UNOPENED.
KIND_TARGET: dict[str, str] = {
    "meeting": ".desk-pullout",
    "note": ".desk-pullout",
    "thread": ".desk-pullout",
    "kb": ".desk-pullout",
    "decision": ".desk-pullout",
    "recipe": ".desk-pullout",
    "workflow": ".desk-pullout",
    "chain": ".desk-pullout",
    "artifact": ".desk-pullout",
    "intelligence": ".desk-pullout",
    "coder": ".desk-pullout",
    "project": "#surface-project-memory",
    "people": "#surface-people",
    "repository": '[id^="repository:"]',
    "roadmap": '[id^="roadmap:"]',
    "workbench": '[id^="workbench:"]',
    "directory": ".desk-zone-window",
    "game": "",
    "story": "",
    "layout": "",
}

SEEDABLE = "one seeded object of this kind"
PULLOUT_KINDS: list[tuple[str, str, str]] = [
    ("meeting", "Meeting pullout", SEEDABLE),
    ("note", "Note pullout", SEEDABLE),
    ("thread", "Thread pullout", SEEDABLE),
    ("kb", "Knowledge pullout", SEEDABLE),
    ("decision", "Decision pullout", SEEDABLE),
    ("recipe", "Agent (recipe) pullout", SEEDABLE),
    ("workflow", "Workflow pullout", SEEDABLE),
    ("chain", "Chain pullout", SEEDABLE),
    ("directory", "Zone (directory) pullout", SEEDABLE),
    ("artifact", "Artifact pullout", "seeded through POST /api/sync/push (no REST create)"),
    ("people", "People pullout", "the singleton people:people (web/src/desk/api.ts:154)"),
    ("intelligence", "Intelligence pullout", "the singleton intelligence:desk (api.ts:151)"),
    ("project", "Project pullout (FallbackPullout)", SEEDABLE),
    ("workbench", "Workbench pullout (FallbackPullout)", SEEDABLE),
    ("repository", "Repository pullout (FallbackPullout)", SEEDABLE),
    ("roadmap", "Roadmap pullout (FallbackPullout)", "read-only, derived from pm/roadmap/ (roadmaps.py:179)"),
    ("coder", "Coder pullout", "NOT SEEDABLE: read from the companion process (/api/coders/status)"),
    ("story", "Story pullout (FallbackPullout)", "NOT SEEDABLE: no wire endpoint (web/src/desk/api.ts:522)"),
    ("game", "Game pullout (FallbackPullout)", "NOT SEEDABLE: SyncClass local (web/src/lib/primitives.ts:26)"),
    ("layout", "Layout pullout (FallbackPullout)", "NOT SEEDABLE: SyncClass local (web/src/lib/primitives.ts:26)"),
]


def pullout_surfaces() -> list[Surface]:
    return [
        Surface(
            f"pullout-{kind}",
            name,
            "pullout",
            f"pullout:{kind}",
            ".desk-pullout",
            "double-click the object on the Floor",
            needs=needs,
            cold=False,
        )
        for kind, name, needs in PULLOUT_KINDS
    ]


# Windows and states that are not their own application.
STATES: list[Surface] = [
    Surface("state-first-sentence", "The First Sentence gate", "state", "custom:first-sentence",
            ".chair-first-value", "arrival on a cold desk", cold=True),
    Surface("state-meetings-queued", "Meetings — a queued meeting", "state", "custom:meetings",
            "#surface-meetings", "Go > Meetings", needs="a queued meeting", cold=False),
    Surface("state-thought", "Thought window", "state", "custom:thought",
            ".thought-workspace, .desk-pullout", "Speak > a thought", needs="a seeded thought", cold=False),
    Surface("state-trust", "Trust window (Data boundaries)", "state", "custom:trust", "#trust",
            "the egress badge in the desk chrome (DeskChrome.tsx:259)", cold=True),
    Surface("state-interview", "The Interview", "state", "custom:interview", ".interview-panel, .desk-pullout",
            "a Project Room > Interview", needs="a project", cold=False),
    Surface("state-room", "Project Room", "state", "custom:room", "#surface-project-memory",
            "Go > Desk memory (scoped to a project)", needs="a project", cold=True),
    Surface("state-delivery", "Delivery / RAILS board", "state", "custom:delivery",
            ".desk-dlv-board, .desk-window", "the dock's Delivery verb", cold=True),
    Surface("state-terminal", "Panes (the session picker)", "state", "custom:terminal",
            ".desk-panepicker.is-open", "the dock's Panes verb", cold=True),
    Surface("state-go-menu", "The Go menu", "chrome", "custom:go-menu", '[role="menu"]',
            "the menu bar", cold=True),
    Surface("state-palette", "The ⌘K palette", "chrome", "custom:palette",
            '[role="region"][aria-label="Tools and Desk search"]', "⌘K", cold=True),
    Surface("state-create-menu", "The ＋Create menu (empty Floor only)", "chrome", "custom:create-menu",
            '[role="menu"]',
            "the Floor's ＋Create verb — it renders ONLY inside EmptyDesk "
            "(web/src/desk/components/EmptyDesk.tsx:37), so a furnished Floor has no Create face",
            cold=True),
    Surface("state-desk-menu", "The Desk menu", "chrome", "custom:bar-menu:Desk", '[role="menu"]',
            "the menu bar", cold=True),
    Surface("state-object-menu", "The Object menu", "chrome", "custom:bar-menu:Object", '[role="menu"]',
            "the menu bar", cold=True),
    Surface("state-window-menu", "The Window menu", "chrome", "custom:bar-menu:Window", '[role="menu"]',
            "the menu bar", cold=True),
]

SETTINGS_SECTIONS: list[Surface] = [
    Surface("settings-settings", "Settings — Settings wing", "settings", "custom:settings-wing:Settings",
            "#surface-settings", "Go > Settings", cold=True),
    Surface("settings-guide", "Settings — Guide wing", "settings", "custom:settings-wing:Guide",
            "#surface-settings", "Go > Settings > Guide", cold=True),
]


# ── the faces INSIDE a window: wings, gear doors, modules, views ──────
#
# A window is not one face. Settings alone carries nine module bodies behind
# a hub ledger (`web/src/pages/cores/settingsPrefs.tsx:40`), and five cores
# carry wings and a gear door (`useCoreWings`). Each is measured on its own.

SETTINGS_MODULES = [
    ("voice", "Voice"),
    ("sounds", "Sounds & Presence"),
    ("wallpaper", "Wallpaper"),
    ("meetings", "Meetings"),
    ("rhythm", "Rhythm"),
    ("models", "Models"),
    ("assignments", "Assignments"),
    ("integrations", "Connections"),
    ("system", "System"),
]

WINGED_CORES = [
    # (surface id prefix, Go label, window id, wings, gear door label)
    ("speak", "Speak", "#surface-dictation",
     ["Speak", "Journal", "Blocks", "Learned"], "Configure dictation"),
    ("meetings", "Meetings", "#surface-meetings",
     ["Outcomes", "Review", "Record", "Artifacts"], "Meeting plumbing"),
    ("activity", "Activity", "#surface-activity",
     ["Records", "Rules"], "Candidates and connectors"),
    ("agents", "Agents", "#surface-companion",
     ["Roster", "Delivery"], "How it connects"),
]

INTELLIGENCE_VIEWS = ["Brief", "Follow-through", "Decisions"]


def inner_surfaces() -> list[Surface]:
    out: list[Surface] = []
    for module_id, label in SETTINGS_MODULES:
        out.append(
            Surface(
                f"settings-module-{module_id}",
                f"Settings module — {label}",
                "settings",
                f"custom:settings-module:{label}",
                "#surface-settings",
                f"Go > Settings > the hub ledger row '{label}' > Open "
                "(web/src/pages/cores/settingsPrefs.tsx:430)",
                cold=True,
            )
        )
    for prefix, go_label, window_id, wings, door in WINGED_CORES:
        for wing in wings:
            out.append(
                Surface(
                    f"wing-{prefix}-{wing.lower().replace(' ', '-')}",
                    f"{go_label} — {wing} wing",
                    "wing",
                    f"custom:wing:{go_label}|{window_id}|{wing}",
                    window_id,
                    f"Go > {go_label} > the '{wing}' wing",
                    cold=True,
                )
            )
        out.append(
            Surface(
                f"door-{prefix}",
                f"{go_label} — the gear door ({door})",
                "wing",
                f"custom:door:{go_label}|{window_id}|{door}",
                window_id,
                f"Go > {go_label} > the gear door '{door}'",
                cold=True,
            )
        )
    for view in INTELLIGENCE_VIEWS:
        out.append(
            Surface(
                f"intel-{view.lower().replace('-', '')}",
                f"Intelligence — {view}",
                "wing",
                f"custom:intel-view:{view}",
                ".desk-pullout",
                f"the dock's Intelligence verb > the '{view}' segment "
                "(web/src/desk/pullouts/IntelligencePullout.tsx:12)",
                cold=True,
            )
        )
    return out


# ── windows this rig had missed entirely ──────────────────────────────
EXTRA_SURFACES: list[Surface] = [
    Surface("win-system-shade", "The System shade (Missed)", "state", "custom:shade",
            ".desk-shade", "the dock's 'Desk memory' launcher "
            "(web/src/desk/components/AttentionDrawer.tsx:73)", cold=True),
    Surface("win-schedule-create", "Schedule a meeting", "state", "custom:schedule",
            '[id="schedule:__create__"]',
            "the Chair's 'Schedule' verb (web/src/desk/chair/ChairHome.tsx:2293)", cold=True),
    Surface("win-new-workbench", "New Workbench chooser", "state", "custom:new-workbench",
            '[id="workbench:__new__"]',
            "Desk menu > New Workbench (createPrimitive('workbench') never persists — "
            "web/src/desk/store/dataSlice.ts:182)", cold=True),
    Surface("win-workbench", "Workbench window", "state", "pullout:workbench",
            '[id^="workbench:"]', "Workbenches > a row", needs="a seeded workbench", cold=False),
    Surface("win-repository", "Repository window", "state", "pullout:repository",
            '[id^="repository:"]', "a repository row on the Floor", needs="a seeded repository", cold=False),
    Surface("win-roadmap", "Roadmap window", "state", "pullout:roadmap",
            '[id^="roadmap:"]', "a roadmap row on the Floor", needs="a roadmap under pm/roadmap/", cold=False),
    Surface("win-thought-workspace", "Thought workspace window", "state", "custom:thought-workspace",
            ".thought-workspace-window, .desk-pullout",
            "a Note pullout > 'Develop this thought' (web/src/desk/pullouts/NotePullout.tsx:483)",
            needs="a seeded note", cold=False),
    Surface("win-list-view", "The Floor as a list", "application", "custom:list-view",
            ".desk-list-view, .desk-next",
            "the Floor at a narrow width, or the list view toggle", cold=True),
    Surface("page-welcome", "The Welcome arrival page (/welcome)", "application", "route:/welcome",
            ".welcome-shell, .welcome-card",
            "NO DOOR: nothing in web/src links to /welcome outside routes.tsx:22 — "
            "its own header calls it a compatibility arrival route", cold=True),
    Surface("page-presence", "The Presence HUD (/presence)", "application", "route:/presence",
            ".presence-body, .presence-card",
            "NO DOOR in the browser: the native desktop overlay loads it "
            "(holdspeak/desktop_presence_cocoa.py:341)", cold=True),
    Surface("win-expose", "Exposé (all windows)", "state", "custom:expose",
            ".desk-expose, [role=\"dialog\"]", "the Window menu / its keybinding", cold=True),
    Surface("win-switcher", "The window switcher (⌃`)", "state", "custom:switcher",
            ".desk-switcher", "⌃` (web/src/desk/keymap.ts)", cold=True),
]


def all_surfaces() -> list[Surface]:
    return (
        APPLICATIONS
        + SETTINGS_SECTIONS
        + inner_surfaces()
        + STATES
        + EXTRA_SURFACES
        + pullout_surfaces()
    )


# ───────────────────────────────────────────────────────── the seeder

LONG_TITLE = (
    "Quarterly platform architecture review — migration, custody, and the "
    "roadmap for the çalışma group (ünïcode) 2026"
)
assert len(LONG_TITLE) >= 110, len(LONG_TITLE)

LONG_PROJECT = "Platform Modernisation — Ingest, Custody and the Long Memory (Wave 3)"
NOTE_WORDS = 2000


def _note_body(words: int) -> str:
    stock = (
        "The ingest path writes one row per utterance. The custody ledger holds "
        "the owner lock. A receipt names the engine, the host and the cost. "
    ).split()
    out = []
    while len(out) < words:
        out.extend(stock)
    return " ".join(out[:words])


@dataclass
class Seed:
    """What the rich desk holds, and the refs the walk opens."""

    refs: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)


def _iso(delta_hours: float = 0.0) -> str:
    from datetime import datetime, timedelta, timezone

    return (datetime.now(tz=timezone.utc) + timedelta(hours=delta_hours)).isoformat()


def seed_rich(api: Api, seed: Seed) -> None:
    """Seed a rich desk through the product's own HTTP API.

    Every call here is the same request the browser makes. What the API
    refuses is recorded in `seed.failures` and printed in the report — the
    rich desk is whatever actually landed, never what was asked for.
    """
    import uuid

    # ── 0. cross the arrival gate; this also furnishes the desk ───────
    #     (setup_service.apply_seed runs inside it — holdspeak/services/setup_service.py:40)
    api.ok("PUT", "/api/setup/onboarding", {"disposition": "completed"}, why="cross the arrival gate")
    api.ok("POST", "/api/desk/seed", {}, why="furnish the desk")

    # ── 1. calendar OFF ───────────────────────────────────────────────
    settings = api.ok("GET", "/api/settings", why="read settings revision")
    revision = settings.get("_revision") if isinstance(settings, dict) else None
    body: dict[str, Any] = {"calendar": {"sources": []}}
    if revision is not None:
        body["_revision"] = revision
    api.ok("PUT", "/api/settings", body, why="calendar off")
    seed.notes.append("calendar: sources cleared (PUT /api/settings)")

    # ── 2. a LAN engine, the lawful way ───────────────────────────────
    #     One call mints profile + artifact + deployment + probe + binding
    #     (holdspeak/web/routes/model_library.py:113).
    engine = api.ok(
        "POST",
        "/api/inference/model-library/define-endpoint",
        {
            "draft": {
                "request_id": f"hs202-endpoint-{uuid.uuid4().hex[:8]}",
                "profile_id": "hs202-lan-engine",
                "expected_profile_revision": 0,
                "label": "LAN llama.cpp (.43)",
                "provider_family": "openai_compatible",
                "model": "qwen2.5-7b-instruct",
                "endpoint": "http://192.168.1.43:8080/v1",
                "requires_key": False,
            },
            "secret": None,
        },
        why="define the LAN endpoint",
    )
    if isinstance(engine, dict):
        provider = engine.get("provider") or {}
        seed.notes.append(
            f"engine: profile={provider.get('profile_id')} rev={provider.get('profile_revision')} "
            f"binding={provider.get('binding_id')}"
        )
        # summary selection at capability scope: read the base revision, then set
        editor = api.ok(
            "POST",
            "/api/inference/assignments/editor",
            {
                "scope": {"kind": "capability", "capability_id": "meeting.deferred_analysis"},
                "capability_id": "meeting.deferred_analysis",
            },
            why="read the assignment base revision",
        )
        base = (editor or {}).get("draft_base_revision", 0) if isinstance(editor, dict) else 0
        assigned = api.ok(
            "POST",
            "/api/inference/assignments/set",
            {
                "command_id": f"hs202-assign-{uuid.uuid4().hex[:8]}",
                "expected_revision": base,
                "scope": {"kind": "capability", "capability_id": "meeting.deferred_analysis"},
                "entries": [
                    {
                        "profile_id": provider.get("profile_id", "hs202-lan-engine"),
                        "profile_revision": provider.get("profile_revision", 1),
                    }
                ],
            },
            why="assign the summary capability",
        )
        seed.counts["engine_assigned"] = 1 if assigned else 0
        # `speech.transcribe` declares boundaries=("local",) and a LAN address
        # classifies as private_network (holdspeak/inference_capabilities.py:1063),
        # so the dictation half of the path stays unassigned here — honestly.
        seed.notes.append(
            "speech.transcribe deliberately NOT assigned: the capability admits only "
            "`local` boundaries, so a LAN endpoint is refused by the product "
            "(holdspeak/inference_capabilities.py:1063) — the Speak face is measured "
            "with a real unassigned half."
        )

    # ── 3. projects — one with 30+ sources through the Door ───────────
    door = api.ok(
        "POST",
        "/api/projects/door",
        {
            "outcome": LONG_PROJECT,
            "sources": [
                {
                    "provider": "github",
                    "scope": f"acme-platform/service-{i:02d}",
                    "watches": ["open_prs", "ci"],
                }
                for i in range(30)
            ]
            + [
                {"provider": "jira", "scope": "PLAT", "watches": ["overdue", "blocked"]},
                {"provider": "jira", "scope": "KUR", "watches": ["due_7_days"]},
            ],
        },
        why="project door with 32 sources",
    )
    project_ids: list[str] = []
    if isinstance(door, dict) and isinstance(door.get("projectId"), str):
        project_ids.append(door["projectId"])
        seed.counts["sources"] = 32
    for name in (
        "Küresel Müşteri Portalı — discovery",
        "Kernel: the ledger, the receipts, and the undo",
    ):
        created = api.ok(
            "POST",
            "/api/projects",
            {"name": name, "command_id": f"hs202-proj-{uuid.uuid4().hex[:8]}"},
            why="project",
        )
        pid = _id_of(created, "project")
        if pid:
            project_ids.append(pid)
    seed.counts["projects"] = len(project_ids)
    if project_ids:
        seed.refs["project"] = f"project:{project_ids[0]}"
        api.ok(
            "PATCH",
            f"/api/projects/{project_ids[0]}",
            {
                "purpose": "One ingest path, one custody ledger, one receipt per write.",
                "outcome_text": LONG_PROJECT,
                "lifecycle": "active",
            },
            why="give the room a purpose",
        )
        for item_type, title, details in (
            ("milestone", "Wave 3 cut-over", {}),
            ("risk", "Dual writers on the live DB", {"likelihood": "medium", "impact": "high"}),
            ("workstream", "Ingest", {}),
        ):
            api.ok(
                "POST",
                f"/api/projects/{project_ids[0]}/items",
                {
                    "item_type": item_type,
                    "title": title,
                    "details": details,
                    "command_id": f"hs202-item-{uuid.uuid4().hex[:8]}",
                },
                why=f"project item {item_type}",
            )

    # ── 4. people (the relationship IS the person) ────────────────────
    api.ok("POST", "/api/people/setup", {}, why="people sidecar")
    people = 0
    for name, kind in (
        ("Aleksandra Wiśniewska-Kowalczyk", "direct_report"),
        ("Jean-Baptiste de la Rochefoucauld-Liancourt", "direct_report"),
        ("Şeyma Öztürk", "peer"),
        ("Priyadarshini Venkataraghavan", "direct_report"),
    ):
        created = api.ok(
            "POST",
            "/api/people/relationships",
            {"display_name": name, "relationship_kind": kind},
            why="relationship",
        )
        if created is not None:
            people += 1
    seed.counts["people"] = people
    seed.refs["people"] = "people:people"          # the singleton (web/src/desk/api.ts:154)
    seed.refs["intelligence"] = "intelligence:desk"  # the singleton (api.ts:151)

    # ── 5. twelve meetings, every state the catalog draws ─────────────
    seed.counts["meetings"] = seed_meetings(api, seed)

    # ── 6. a 2000-word note ───────────────────────────────────────────
    note = api.ok(
        "POST",
        "/api/notes",
        {
            "title": "The long note — ingest, custody, receipts",
            "body_markdown": _note_body(NOTE_WORDS),
            "tags": [],
        },
        why="2000-word note",
    )
    nid = _id_of(note, "note")
    if nid:
        seed.refs["note"] = f"note:{nid}"
        seed.counts["note_words"] = NOTE_WORDS

    # ── 7. one object of each creatable pullout kind ──────────────────
    creators: list[tuple[str, str, dict]] = [
        ("kb", "/api/kbs", {"name": "Custody — what the ledger holds", "member_ids": []}),
        ("decision", "/api/decisions", {"title": "We keep the owner lock on one writer", "status": "proposed"}),
        ("recipe", "/api/recipes", {"name": "The reviewer — an agent with a deliberately long name"}),
        ("chain", "/api/chains", {"name": "Ingest → enrich → file", "steps": []}),
        ("workflow", "/api/workflows", {"name": "Nightly ingest", "prompt": "run the ingest", "graph_json": {}}),
        ("directory", "/api/directories", {"name": "Platform — çalışma zone", "parent_id": None}),
        ("workbench", "/api/workbenches", {"name": "The platform workbench"}),
        ("thread", "/api/threads", {"title": "The platform thread"}),
    ]
    for kind, path, payload in creators:
        created = api.ok("POST", path, payload, why=f"create {kind}")
        cid = _id_of(created, kind)
        if cid:
            seed.refs[kind] = f"{kind}:{cid}"

    # an artifact has no REST create — the sync bucket is its door
    art_id = f"hs202-artifact-{uuid.uuid4().hex[:8]}"
    pushed = api.ok(
        "POST",
        "/api/sync/push",
        {
            "artifacts": [
                {
                    "meta": {"id": art_id, "kind": "artifact", "last_modified": _iso(), "deleted": False},
                    "value": {
                        "id": art_id,
                        "title": "Ingest cut-over plan (v3) — çalışma",
                        "body": _note_body(300),
                        "kind": "artifact",
                    },
                }
            ]
        },
        why="artifact via sync push",
    )
    if pushed is not None:
        seed.refs["artifact"] = f"artifact:{art_id}"

    # ── 8. five thoughts ──────────────────────────────────────────────
    thoughts = 0
    for i in range(5):
        created = api.ok(
            "POST",
            "/api/thoughts",
            {
                "request_id": str(uuid.uuid4()),
                "raw_text": f"Thought {i + 1} — the shape of the ingest path and who owns the lock.",
                "source": {"kind": "typed"},
                "initial_note": {
                    "title": f"Thought {i + 1} — the shape of the ingest path",
                    "body_markdown": _note_body(120),
                    "tags": [],
                },
            },
            why="thought",
        )
        if created is not None:
            thoughts += 1
            thought = created.get("thought") if isinstance(created, dict) else None
            if isinstance(thought, dict):
                wn = thought.get("working_note")
                if isinstance(wn, dict) and isinstance(wn.get("id"), str) and "thought_note" not in seed.refs:
                    seed.refs["thought_note"] = f"note:{wn['id']}"
    seed.counts["thoughts"] = thoughts

    # ── 9. a repository (so Delivery/RAILS has a subject) ─────────────
    repo = api.ok("POST", "/api/repositories", {"path": str(REPO)}, why="repository")
    rid = _id_of(repo, "repository")
    if rid:
        seed.refs["repository"] = f"repository:{rid}"

    # ── 10. whatever the desk actually holds now fills the rest ───────
    harvest_refs(api, seed)


MEETING_RECIPES: list[tuple[str, str, dict]] = [
    # (title, face the catalog draws, the fields that make it so)
    (LONG_TITLE, "RAN (2 h)", {"hours": 2.0, "capture_status": "finalized", "intel": "ready"}),
    ("Kickoff — Küresel Müşteri Portalı", "REC (live)", {"live": True}),
    ("Incident review — ingest stall", "CAPTURE FAILED", {"capture_status": "capture_failed"}),
    ("Roadmap triage", "SUMMARY QUEUED", {"capture_status": "finalized", "intel": "queued"}),
    ("Vendor call — custody", "SUMMARY RUNNING", {"capture_status": "finalized", "intel": "running"}),
    ("Security review", "SUMMARY FAILED", {"capture_status": "finalized", "intel": "error"}),
    ("1:1 — Aleksandra Wiśniewska-Kowalczyk", "RAN", {"capture_status": "finalized", "intel": "ready"}),
    ("Architecture guild", "RAN", {"capture_status": "finalized", "intel": "ready"}),
    ("Platform sync", "SAVED", {"capture_status": "finalized", "intel": None}),
    ("Hiring loop debrief", "OFF", {"capture_status": "finalized", "intel": "disabled"}),
    ("Quarterly planning", "RECOVERABLE", {"capture_status": "recoverable"}),
    ("Retro", "INTERRUPTED", {"capture_status": "recording", "stale": True}),
]


def seed_meetings(api: Api, seed: Seed) -> int:
    """Twelve meetings across every state the Meetings catalog draws.

    The state recipes are `web/src/pages/cores/history/helpers.ts:68`
    (`stateToken`) read back into the sync payload the hub accepts
    (`holdspeak/web/routes/sync.py:45`).
    """
    rows = []
    for index, (title, face, spec) in enumerate(MEETING_RECIPES):
        mid = f"hs202-meeting-{index:02d}"
        hours = float(spec.get("hours", 0.75))
        started = _iso(-(2.0 + index * 3) - hours)
        if spec.get("live"):
            started = _iso(-0.4)
            value: dict[str, Any] = {
                "id": mid,
                "title": title,
                "started_at": started,
                "ended_at": None,
                "capture_status": "recording",
                "segments": _segments(6),
            }
        elif spec.get("stale"):
            value = {
                "id": mid,
                "title": title,
                "started_at": _iso(-30),
                "ended_at": None,
                "capture_status": "recording",
                "segments": _segments(3),
            }
        else:
            from datetime import datetime, timedelta, timezone

            start_dt = datetime.now(tz=timezone.utc) - timedelta(hours=2.0 + index * 3 + hours)
            value = {
                "id": mid,
                "title": title,
                "started_at": start_dt.isoformat(),
                "ended_at": (start_dt + timedelta(hours=hours)).isoformat(),
                "capture_status": spec.get("capture_status", "finalized"),
                "segments": _segments(24 if hours >= 2 else 8),
            }
        intel_state = spec.get("intel")
        if intel_state:
            value["intel_status"] = {
                "state": intel_state,
                "requested_at": _iso(-2),
                "completed_at": _iso(-1) if intel_state in ("ready", "complete") else None,
            }
            if intel_state in ("ready", "complete"):
                value["intel"] = {
                    "timestamp": 0,
                    "topics": ["custody", "ingest", "receipts"],
                    "summary": (
                        "One writer holds the owner lock. Ingest writes one row per "
                        "utterance. Every write returns a receipt naming the engine."
                    ),
                    "action_items": [
                        {"text": "Land the write-receipt channel", "owner": "Karol"},
                        {"text": "Close the second-writer gap", "owner": "Aleksandra"},
                    ],
                }
        rows.append(
            {
                "meta": {"id": mid, "kind": "meeting", "last_modified": _iso(), "deleted": False},
                "value": value,
            }
        )
        if index == 0:
            seed.refs["meeting"] = f"meeting:{mid}"
    pushed = api.ok("POST", "/api/sync/push", {"meetings": rows}, why="12 meetings via sync push")
    if pushed is None:
        return 0
    seed.notes.append(
        "meeting states seeded: " + ", ".join(f"{t[:28]}→{face}" for t, face, _ in MEETING_RECIPES)
    )
    received = pushed.get("received") if isinstance(pushed, dict) else None
    if isinstance(received, dict) and isinstance(received.get("meetings"), int):
        return int(received["meetings"])
    return len(rows)


def _segments(count: int) -> list[dict]:
    lines = [
        "Karol: the desk has to show intelligence arriving, not after the fact.",
        "Aleksandra: the ledger holds the lock; the sidecar must not write.",
        "Karol: if a write fails, the receipt names it. No silent no-ops.",
        "Şeyma: the Room needs the sources before the interview.",
    ]
    out = []
    for i in range(count):
        text = lines[i % len(lines)]
        out.append(
            {
                "text": text,
                "speaker": text.split(":", 1)[0],
                "start_time": float(i * 12),
                "end_time": float(i * 12 + 11),
            }
        )
    return out


def _id_of(payload: Any, kind: str) -> str | None:
    """Pull an id out of whatever shape a create route returned."""
    if not isinstance(payload, dict):
        return None
    for key in ("id", f"{kind}_id", "item_id", "projectId"):
        if isinstance(payload.get(key), str):
            return payload[key]
    for key in (kind, "item", "created", "project", "meeting", "note", "thought", "relationship", "thread"):
        inner = payload.get(key)
        if isinstance(inner, dict):
            for idkey in ("id", f"{kind}_id", "project_id"):
                if isinstance(inner.get(idkey), str):
                    return inner[idkey]
    return None


# The desk's inventory is one fetch per kind (web/src/desk/api.ts:560).
HARVEST_ROUTES: list[tuple[str, str, str]] = [
    ("meeting", "/api/meetings?limit=24", "meetings"),
    ("note", "/api/notes", "notes"),
    ("decision", "/api/decisions", "decisions"),
    ("recipe", "/api/recipes", "recipes"),
    ("kb", "/api/kbs", "kbs"),
    ("directory", "/api/directories", "directories"),
    ("chain", "/api/chains", "chains"),
    ("workflow", "/api/workflows", "workflows"),
    ("workbench", "/api/workbenches", "workbenches"),
    ("project", "/api/projects", "projects"),
    ("thread", "/api/threads", "threads"),
    ("repository", "/api/repositories", "repositories"),
    ("roadmap", "/api/roadmaps", "roadmaps"),
    ("coder", "/api/coders/status", "coders"),
]


def harvest_refs(api: Api, seed: Seed) -> None:
    """Ask each kind's own route what it holds, and take one ref of each."""
    inventory: dict[str, int] = {}
    for kind, path, key in HARVEST_ROUTES:
        status, payload = api.call("GET", path)
        if status >= 300:
            inventory[kind] = -1  # the route refused; NOT a count of zero
            seed.failures.append(f"GET {path} -> {status} (harvest {kind})")
            continue
        items: list[Any] = []
        if isinstance(payload, list):
            items = payload
        elif isinstance(payload, dict):
            for candidate in (key, "items", "results", kind + "s"):
                if isinstance(payload.get(candidate), list):
                    items = payload[candidate]
                    break
        inventory[kind] = len(items)
        for item in items:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                seed.refs.setdefault(kind, f"{kind}:{item['id']}")
                break
    seed.notes.append(
        "desk inventory (per-kind routes; -1 = the route refused, NOT a zero): "
        + json.dumps(inventory, sort_keys=True)
    )
    seed.notes.append("refs opened by the walk: " + json.dumps(seed.refs, sort_keys=True))


# ────────────────────────────────────────────────────────── the walk


class Walker:
    """One page at one width, walking one desk."""

    def __init__(self, page: Any, hub: Hub, width: int, desk: str, shots: Path, take_shots: bool) -> None:
        self.page = page
        self.hub = hub
        self.width = width
        self.desk = desk
        self.shots = shots
        self.take_shots = take_shots
        self.console: list[str] = []
        self.responses: list[str] = []
        page.on("pageerror", lambda e: self.console.append(f"pageerror: {e}"))
        page.on(
            "console",
            lambda m: self.console.append(f"console.{m.type}: {m.text}") if m.type == "error" else None,
        )
        page.on("response", self._on_response)

    def _on_response(self, response: Any) -> None:
        try:
            if response.status >= 400:
                self.responses.append(f"{response.status} {response.url}")
        except Exception:
            pass

    # ── navigation primitives ────────────────────────────────────────
    def goto(self, route: str = "/") -> None:
        sep = "&" if "?" in route else "?"
        self.page.goto(
            f"{self.hub.url}{route}{sep}token={self.hub.token}", wait_until="domcontentloaded"
        )
        try:
            self.page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        self.page.wait_for_timeout(900)

    def pass_gate(self) -> bool:
        """Cross the First Sentence gate if it is up. True if it was."""
        try:
            chair = self.page.locator(".chair")
            chair.wait_for(timeout=15000)
        except Exception:
            return False
        try:
            gated = chair.evaluate("el => el.classList.contains('chair-first-value')")
        except Exception:
            return False
        if not gated:
            return False
        for label in ("Continue later", "Skip", "Not now"):
            btn = self.page.get_by_role("button", name=label, exact=True)
            if btn.count():
                btn.first.click()
                break
        try:
            self.page.locator(".chair:not(.chair-first-value)").wait_for(timeout=10000)
        except Exception:
            pass
        return True

    def close_windows(self) -> None:
        """Leave no window standing so the next surface is measured alone."""
        try:
            self.page.keyboard.press("Escape")
            self.page.evaluate(
                """() => {
                    document.querySelectorAll('.desk-window-close, [aria-label="Close window"]')
                        .forEach(b => b.click());
                }"""
            )
        except Exception:
            pass
        self.page.wait_for_timeout(200)

    def open_go(self, label: str) -> None:
        go = self.page.get_by_role("button", name="Go", exact=True)
        go.wait_for(timeout=15000)
        go.click()
        menu = self.page.get_by_role("menu", name="Go menu")
        item = menu.get_by_role("menuitem", name=label, exact=False)
        item.first.wait_for(timeout=10000)
        item.first.click()

    def open_palette(self, label: str) -> None:
        self.page.keyboard.press("Meta+k")
        box = self.page.get_by_placeholder("Search tools and Desk items")
        box.wait_for(timeout=10000)
        box.fill(label)
        self.page.wait_for_timeout(400)
        option = self.page.get_by_role("option").first
        option.wait_for(timeout=8000)
        option.click()

    def _what_opened(self) -> str:
        """Name the window the palette actually drew — a fuzzy door must confess."""
        try:
            titles = self.page.evaluate(
                """() => Array.from(document.querySelectorAll('.desk-window, .desk-pullout'))
                    .map(w => (w.querySelector('.desk-window-title')?.textContent || w.id || '').trim())
                    .filter(Boolean)"""
            )
        except Exception:
            return "could not read the open windows"
        return "windows open: " + (", ".join(titles) if titles else "none")

    def settle(self) -> None:
        try:
            self.page.evaluate(
                """() => {
                    const anims = document.getAnimations();
                    if (!anims.length) return;
                    return Promise.race([
                        Promise.all(anims.map(a => a.finished.catch(() => null))),
                        new Promise(r => setTimeout(r, 2000)),
                    ]);
                }"""
            )
        except Exception:
            pass
        self.page.wait_for_timeout(200)

    # ── the measured open ────────────────────────────────────────────
    def measure(self, surface: Surface, seed: Seed | None, index: int) -> dict:
        self.console.clear()
        self.responses.clear()
        record: dict[str, Any] = {
            "id": surface.id,
            "name": surface.name,
            "family": surface.family,
            "desk": self.desk,
            "width": self.width,
            "door": surface.door,
            "opener": surface.opener,
            "status": "UNOPENED",
            "reason": None,
            "shot": None,
        }
        t0 = time.monotonic()
        try:
            opened, root_used, note = self.open_surface(surface, seed)
        except Exception as exc:  # a door that refuses is a finding, not a crash
            record["reason"] = f"{type(exc).__name__}: {str(exc)[:240]}"
            record["console"] = list(self.console)
            record["responses"] = list(self.responses)
            return record
        if not opened:
            record["reason"] = note
            record["console"] = list(self.console)
            record["responses"] = list(self.responses)
            return record
        self.settle()
        t_open = (time.monotonic() - t0) * 1000.0
        record["status"] = "MEASURED"
        record["note"] = note
        record["root"] = root_used
        # M13 — the browser's own clock for paint and interactive.
        try:
            record["M13"] = self.page.evaluate(
                """() => {
                    const nav = performance.getEntriesByType('navigation')[0] || {};
                    const paints = {};
                    for (const p of performance.getEntriesByType('paint')) paints[p.name] = Math.round(p.startTime);
                    return {
                        firstPaintMs: paints['first-paint'] ?? null,
                        firstContentfulPaintMs: paints['first-contentful-paint'] ?? null,
                        domInteractiveMs: nav.domInteractive != null ? Math.round(nav.domInteractive) : null,
                        loadEventMs: nav.loadEventEnd != null ? Math.round(nav.loadEventEnd) : null,
                    };
                }"""
            )
        except Exception:
            record["M13"] = None
        record["M13"] = dict(record.get("M13") or {}, openToSettledMs=round(t_open))
        try:
            measured = self.page.evaluate(MEASURE_JS, [root_used, self.width, {}])
        except Exception as exc:
            record["status"] = "UNMEASURED"
            record["reason"] = f"measure failed: {type(exc).__name__}: {str(exc)[:200]}"
            return record
        record.update(measured)
        record["M9"] = {
            "consoleErrors": [e for e in self.console if not _ignorable(e)],
            "httpErrors": list(dict.fromkeys(self.responses)),
        }
        if self.take_shots:
            name = f"{index:02d}-{surface.id}-{self.desk}-{self.width}.png"
            self.shots.mkdir(parents=True, exist_ok=True)
            try:
                self.page.screenshot(path=str(self.shots / name), full_page=False)
                record["shot"] = name
            except Exception as exc:
                record["shot"] = None
                record["reason"] = f"shot failed: {exc}"
        return record

    # ── the openers ──────────────────────────────────────────────────
    def open_surface(self, surface: Surface, seed: Seed | None) -> tuple[bool, str | None, str | None]:
        kind, _, arg = surface.opener.partition(":")
        if kind == "unopenable":
            return False, None, surface.door
        if kind == "chair":
            self.goto("/")
            self.pass_gate()
            return True, ".chair", None
        if kind == "route":
            self.goto(arg)
            self.pass_gate()
            if surface.root:
                try:
                    self.page.locator(surface.root).first.wait_for(timeout=12000)
                except Exception:
                    return False, None, f"route {arg} did not open {surface.root} within 12s"
            return True, surface.root, None
        if kind == "go":
            self.goto("/")
            self.pass_gate()
            self.close_windows()
            self.open_go(arg)
            if surface.root:
                try:
                    self.page.locator(surface.root).first.wait_for(timeout=12000)
                except Exception:
                    return False, None, f"Go > {arg} did not open {surface.root} within 12s"
            return True, surface.root, None
        if kind == "palette":
            self.goto("/")
            self.pass_gate()
            self.close_windows()
            self.open_palette(arg)
            if surface.root:
                try:
                    self.page.locator(surface.root).first.wait_for(timeout=12000)
                except Exception:
                    return False, None, f"palette '{arg}' did not open {surface.root} within 12s"
            return True, surface.root, None
        if kind == "pullout":
            if seed is None:
                return False, None, "pullouts are measured on the rich desk only"
            ref = seed.refs.get(arg)
            if not ref:
                return False, None, f"no seeded {arg} — {surface.needs}"
            target = KIND_TARGET.get(arg, ".desk-pullout")
            if not target:
                return False, None, (
                    f"the `{arg}` kind declares `surface: {{type: \"none\"}}` in "
                    "web/src/lib/primitives.ts, so `openPullout` breaks without drawing "
                    "anything (web/src/desk/store/compositorSlice.ts:169). This registry "
                    "entry has no face at all."
                )
            self.goto(f"/?open={ref}")
            self.pass_gate()
            try:
                self.page.locator(target).first.wait_for(timeout=12000)
            except Exception:
                # ZoneWindow and InfoWindow mount only on the world stage
                # (web/src/desk/gl/WorldStage.tsx:295), so try the Floor once.
                opened, _, _ = self.open_custom("floor", surface, seed)
                if opened:
                    try:
                        self.page.evaluate(
                            "(r) => import('/assets/desk.js').catch(() => null) && null", ref
                        )
                    except Exception:
                        pass
                    self.goto(f"/?open={ref}")
                    self.pass_gate()
                    try:
                        self.page.locator(target).first.wait_for(timeout=8000)
                        return True, target, f"ref={ref} (via the Floor)"
                    except Exception:
                        pass
                return False, None, (
                    f"?open={ref} drew no `{target}` within 12s "
                    "(the ref resolves against the LOADED desk store — "
                    "web/src/desk/store/compositorSlice.ts:137 warns `unknown id` otherwise)"
                )
            return True, target, f"ref={ref}"
        if kind == "custom":
            return self.open_custom(arg, surface, seed)
        return False, None, f"unknown opener {surface.opener}"

    def open_custom(self, what: str, surface: Surface, seed: Seed | None) -> tuple[bool, str | None, str | None]:
        page = self.page
        if what == "first-sentence":
            self.goto("/")
            try:
                page.locator(".chair").wait_for(timeout=15000)
            except Exception:
                return False, None, "no chair"
            gated = page.locator(".chair").evaluate(
                "el => el.classList.contains('chair-first-value')"
            )
            if not gated:
                return False, None, "the gate was not up on this desk (it is a cold-arrival face only)"
            return True, ".chair", None
        if what == "floor":
            self.goto("/")
            self.pass_gate()
            # The Floor is the Chair's other face: the Dock's floor verb.
            for name in ("Floor", "Show the floor", "Desk floor"):
                btn = page.get_by_role("button", name=name, exact=False)
                if btn.count():
                    btn.first.click()
                    page.wait_for_timeout(700)
                    return True, ".desk-next", f"via '{name}'"
            return False, None, "no Floor verb found in the chrome at this width"
        if what == "intelligence":
            self.goto("/")
            self.pass_gate()
            self.close_windows()
            try:
                self.open_palette("Show today's brief")
            except Exception:
                return False, None, "the palette would not run 'Show today's brief'"
            try:
                page.locator(".desk-pullout, #intelligence-desk").first.wait_for(timeout=12000)
            except Exception:
                return False, None, "the Intelligence verb drew no window within 12s"
            return True, ".desk-pullout", None
        if what.startswith("settings-module:"):
            label = what.split(":", 1)[1]
            self.goto("/")
            self.pass_gate()
            self.close_windows()
            self.open_go("Settings")
            page.locator("#surface-settings").wait_for(timeout=12000)
            page.locator("#surface-settings .prefs-hub").wait_for(timeout=12000)
            page.wait_for_timeout(600)
            result = page.evaluate(
                """(label) => {
                    const hub = document.querySelector('#surface-settings .prefs-hub');
                    if (!hub) return 'no-hub';
                    const opens = Array.from(hub.querySelectorAll('button'))
                        .filter(b => (b.textContent || '').trim() === 'Open');
                    if (!opens.length) return 'no-open-verbs';
                    // Walk UP until an ancestor carries the row's own label:
                    // `closest('[class*="ledger"]')` stops at the trailing
                    // span, which holds only the word "Open".
                    for (const b of opens) {
                        let n = b.parentElement;
                        for (let i = 0; i < 6 && n; i++, n = n.parentElement) {
                            if ((n.textContent || '').includes(label)) { b.click(); return 'ok'; }
                        }
                    }
                    const rows = opens.map(b => {
                        let n = b.parentElement;
                        for (let i = 0; i < 6 && n; i++, n = n.parentElement) {
                            const t = (n.textContent || '').trim();
                            if (t && t !== 'Open') return t.slice(0, 40);
                        }
                        return '?';
                    });
                    return 'no-row (' + opens.length + ' rows: ' + rows.join(' | ') + ')';
                }""",
                label,
            )
            if result != "ok":
                return False, None, (
                    f"the Settings hub has no '{label}' row with an Open verb (probe: {result}; "
                    "the module roster is web/src/pages/cores/settingsPrefs.tsx:40)"
                )
            page.wait_for_timeout(1400)
            return True, "#surface-settings", f"module '{label}'"
        if what.startswith("wing:") or what.startswith("door:"):
            kind, _, rest = what.partition(":")
            go_label, window_id, target = rest.split("|")
            self.goto("/")
            self.pass_gate()
            self.close_windows()
            self.open_go(go_label)
            page.locator(window_id).wait_for(timeout=15000)
            page.wait_for_timeout(1500)   # the core lazy-loads after the frame
            # Wings are role="tab" inside the window's own strip
            # (web/src/desk/surface/wings.tsx:88); the gear door is a
            # role="button" beside it, aria-labelled with its title (:127).
            window = page.locator(window_id)
            if kind == "wing":
                verb = window.get_by_role("tab", name=target, exact=True)
                if not verb.count():
                    verb = page.locator('[role="tablist"][aria-label="Window faces"]').get_by_role(
                        "tab", name=target, exact=True
                    )
            else:
                verb = window.get_by_role("button", name=target, exact=True)
                if not verb.count():
                    verb = page.locator(f'button.desk-wing-door[aria-label="{target}"]')
            if not verb.count():
                return False, None, (
                    f"no '{target}' {'wing' if kind == 'wing' else 'gear door'} on "
                    f"{go_label} at this width"
                )
            verb.first.click()
            page.wait_for_timeout(1400)
            return True, window_id, f"{kind} '{target}'"
        if what.startswith("intel-view:"):
            view = what.split(":", 1)[1]
            opened, root, note = self.open_custom("intelligence", surface, seed)
            if not opened:
                return False, None, note
            verb = page.get_by_role("button", name=view, exact=True)
            if not verb.count():
                return False, None, f"no '{view}' segment on the Intelligence face"
            verb.first.click()
            page.wait_for_timeout(1000)
            return True, ".desk-pullout", f"segment '{view}'"
        if what == "shade":
            self.goto("/")
            self.pass_gate()
            self.close_windows()
            btn = page.get_by_role("button", name="Desk memory", exact=True)
            if not btn.count():
                return False, None, "no 'Desk memory' launcher in the dock at this width"
            btn.first.click()
            page.wait_for_timeout(1000)
            if not page.locator(".desk-shade").count():
                return False, None, "the 'Desk memory' launcher drew no shade"
            return True, ".desk-shade", None
        if what == "schedule":
            self.goto("/")
            self.pass_gate()
            btn = page.locator('[data-testid="arrival-schedule"]')
            if not btn.count():
                btn = page.get_by_role("button", name="Schedule", exact=True)
            if not btn.count():
                return False, None, "no 'Schedule' verb on the Chair at this width"
            btn.first.click()
            try:
                page.locator('[id="schedule:__create__"]').wait_for(timeout=10000)
            except Exception:
                return False, None, "the Schedule verb drew no window within 10s"
            return True, '[id="schedule:__create__"]', None
        if what == "new-workbench":
            self.goto("/")
            self.pass_gate()
            self.close_windows()
            try:
                self.open_palette("New Workbench")
            except Exception:
                return False, None, "the ⌘K palette has no 'New Workbench' row"
            try:
                page.locator('[id="workbench:__new__"]').wait_for(timeout=10000)
            except Exception:
                return False, None, f"'New Workbench' drew no chooser ({self._what_opened()})"
            return True, '[id="workbench:__new__"]', None
        if what == "thought-workspace":
            if seed is None or "note" not in seed.refs:
                return False, None, "no seeded note"
            self.goto(f"/?open={seed.refs['note']}")
            self.pass_gate()
            try:
                page.locator(".desk-pullout").first.wait_for(timeout=12000)
            except Exception:
                return False, None, "the note pullout did not open"
            verb = page.get_by_role("button", name="Develop this thought", exact=False)
            if not verb.count():
                return False, None, (
                    "no 'Develop this thought' verb on the note pullout "
                    "(web/src/desk/pullouts/NotePullout.tsx:483)"
                )
            verb.first.click()
            page.wait_for_timeout(2000)
            if page.locator(".thought-workspace-window").count():
                return True, ".thought-workspace-window", None
            return True, ".desk-pullout", "the verb ran but drew no .thought-workspace-window"
        if what == "list-view":
            opened, _, note = self.open_custom("floor", surface, seed)
            if not opened:
                return False, None, f"could not reach the Floor: {note}"
            if page.locator(".desk-list-view").count():
                return True, ".desk-list-view", None
            toggle = page.get_by_role("button", name="List", exact=False)
            if toggle.count():
                toggle.first.click()
                page.wait_for_timeout(800)
                if page.locator(".desk-list-view").count():
                    return True, ".desk-list-view", "via the List toggle"
            return False, None, (
                "the Floor drew no .desk-list-view and no List toggle was found — "
                "list view is automatic only at <=720px (web/src/desk/DeskApp.tsx:190)"
            )
        if what == "expose":
            self.goto("/")
            self.pass_gate()
            self.open_go("Meetings")
            page.wait_for_timeout(800)
            self.open_go("Settings")
            page.wait_for_timeout(800)
            btn = page.get_by_role("button", name="Window", exact=True)
            if btn.count():
                btn.first.click()
                page.wait_for_timeout(400)
                item = page.get_by_role("menuitem", name="Expose", exact=False)
                if item.count():
                    item.first.click()
                    page.wait_for_timeout(900)
                    if page.locator(".desk-expose").count():
                        return True, ".desk-expose", "Window menu > Expose"
            return False, None, (
                "no Expose verb found in the Window menu at this width "
                f"({self._what_opened()})"
            )
        if what == "switcher":
            self.goto("/")
            self.pass_gate()
            self.open_go("Meetings")
            page.wait_for_timeout(600)
            self.open_go("Settings")
            page.wait_for_timeout(600)
            page.keyboard.press("Control+`")
            page.wait_for_timeout(700)
            if not page.locator(".desk-switcher").count():
                return False, None, "⌃` drew no .desk-switcher"
            return True, ".desk-switcher", None
        if what.startswith("bar-menu:"):
            label = what.split(":", 1)[1]
            self.goto("/")
            self.pass_gate()
            btn = page.get_by_role("button", name=label, exact=True)
            if not btn.count():
                return False, None, f"no '{label}' title in the menu bar at this width"
            btn.first.click()
            try:
                page.get_by_role("menu", name=f"{label} menu").wait_for(timeout=8000)
            except Exception:
                return False, None, f"the '{label}' title opened no menu"
            return True, '[role="menu"]', None
        if what == "go-menu":
            self.goto("/")
            self.pass_gate()
            go = page.get_by_role("button", name="Go", exact=True)
            go.wait_for(timeout=15000)
            go.click()
            page.get_by_role("menu", name="Go menu").wait_for(timeout=8000)
            return True, '[role="menu"]', None
        if what == "palette":
            self.goto("/")
            self.pass_gate()
            page.keyboard.press("Meta+k")
            try:
                page.get_by_placeholder("Search tools and Desk items").wait_for(timeout=8000)
            except Exception:
                return False, None, "⌘K opened no palette"
            return True, '[role="region"][aria-label="Tools and Desk search"]', None
        if what == "create-menu":
            # The Create verb lives in DeskStartActions, which is on the FLOOR,
            # not the Chair (web/src/desk/components/DeskStartActions.tsx:44).
            opened, _, note = self.open_custom("floor", surface, seed)
            if not opened:
                return False, None, f"could not reach the Floor: {note}"
            btn = page.get_by_role("button", name="Create", exact=False)
            if not btn.count():
                empty = page.locator(".desk-empty").count()
                return False, None, (
                    "no ＋Create verb: it lives only inside EmptyDesk "
                    "(web/src/components/EmptyDesk.tsx:37) and the Floor is never empty — "
                    f"the product furnishes zones on first boot (.desk-empty present={empty}). "
                    "So this face has NO DOOR on any real desk."
                )
            btn.first.click()
            page.wait_for_timeout(500)
            menu = page.get_by_role("menu", name="Create a Desk item")
            if not menu.count():
                return False, None, "the Create verb opened no menu"
            return True, '[role="menu"]', None
        if what.startswith("settings-wing:"):
            wing = what.split(":", 1)[1]
            self.goto("/")
            self.pass_gate()
            self.close_windows()
            self.open_go("Settings")
            page.locator("#surface-settings").wait_for(timeout=12000)
            tab = page.locator("#surface-settings").get_by_role("button", name=wing, exact=True)
            if tab.count():
                tab.first.click()
                page.wait_for_timeout(600)
                return True, "#surface-settings", f"wing '{wing}'"
            return True, "#surface-settings", f"wing '{wing}' NOT FOUND — measured the default wing"
        if what == "meetings":
            self.goto("/")
            self.pass_gate()
            self.close_windows()
            self.open_go("Meetings")
            page.locator("#surface-meetings").wait_for(timeout=12000)
            return True, "#surface-meetings", None
        if what == "thought":
            if seed is None or "thought_note" not in seed.refs:
                return False, None, "no seeded thought (the thoughts API refused; see the seeding ledger)"
            self.goto(f"/?open={seed.refs['thought_note']}")
            self.pass_gate()
            try:
                page.locator(".desk-pullout, .thought-workspace").first.wait_for(timeout=12000)
            except Exception:
                return False, None, "the thought's working note drew no window"
            return True, ".desk-pullout", f"ref={seed.refs['thought_note']}"
        if what == "trust":
            self.goto("/")
            self.pass_gate()
            self.close_windows()
            badge = page.locator('[aria-label^="Privacy and trust"]')
            if not badge.count():
                return False, None, "no egress badge in the chrome at this width — no door to Trust"
            badge.first.click()
            try:
                page.locator("#trust").wait_for(timeout=10000)
            except Exception:
                return False, None, "the egress badge opened no #trust window within 10s"
            return True, "#trust", None
        if what == "interview":
            if seed is None or "project" not in seed.refs:
                return False, None, "no seeded project"
            self.goto("/")
            self.pass_gate()
            self.close_windows()
            self.open_go("Desk memory")
            try:
                page.locator("#surface-project-memory").wait_for(timeout=12000)
            except Exception:
                return False, None, "Desk memory did not open"
            btn = page.get_by_role("button", name="Interview", exact=False)
            if not btn.count():
                return False, None, "no Interview verb on the Room at this width"
            btn.first.click()
            page.wait_for_timeout(900)
            return True, ".interview-panel, #surface-project-memory", None
        if what == "room":
            self.goto("/")
            self.pass_gate()
            self.close_windows()
            self.open_go("Desk memory")
            try:
                page.locator("#surface-project-memory").wait_for(timeout=12000)
            except Exception:
                return False, None, "Desk memory did not open within 12s"
            return True, "#surface-project-memory", None
        if what == "delivery":
            self.goto("/")
            self.pass_gate()
            self.close_windows()
            btn = page.get_by_role("button", name="Delivery", exact=True)
            if not btn.count():
                return False, None, "no Delivery verb in the dock at this width"
            btn.first.click()
            page.wait_for_timeout(1200)
            return True, ".desk-dlv-board, .desk-window", self._what_opened()
        if what == "terminal":
            self.goto("/")
            self.pass_gate()
            self.close_windows()
            btn = page.get_by_role("button", name="Panes", exact=True)
            if not btn.count():
                return False, None, "no Panes verb in the dock at this width"
            btn.first.click()
            page.wait_for_timeout(1200)
            # The Panes launcher is a transient list, not a window
            # (web/src/desk/components/SessionPullout.tsx:253).
            picker = page.locator(".desk-panepicker.is-open")
            if not picker.count():
                return False, None, f"the dock's Panes verb drew nothing ({self._what_opened()})"
            return True, ".desk-panepicker.is-open", self._what_opened()
        return False, None, f"no custom opener '{what}'"


def _ignorable(text: str) -> bool:
    lowered = text.lower()
    return any(
        token in lowered
        for token in ("resizeobserver", "err_connection_refused", "websocket", "favicon")
    )


# ─────────────────────────────────────────────────────── the scoring


def failing_rules(record: dict) -> list[str]:
    """The rule ids this surface fails, from its own numbers."""
    if record.get("status") != "MEASURED":
        return []
    fails: list[str] = []
    m1 = record.get("M1") or {}
    # The root's raw overflow is the 3px resize-handle affordance on every
    # window (window-chrome.css:42); `contentOverflow` is the honest number.
    if (m1.get("document") or {}).get("overflow", 0) > 0 or (m1.get("root") or {}).get("contentOverflow", 0) > 0:
        fails.append("M1")
    if m1.get("inner"):
        fails.append("M1")
    if record.get("M2"):
        fails.append("M2")
    if record.get("M3"):
        fails.append("M3")
    m4 = record.get("M4") or {}
    if [f for f in (m4.get("folds") or []) if not f.get("open")]:
        fails.append("M4")
    if record.get("M5"):
        fails.append("M5")
    if record.get("M6"):
        fails.append("M6")
    m7 = record.get("M7") or {}
    if m7.get("smallText"):
        fails.append("M7")
    if m7.get("smallTargets"):
        fails.append("M7")
    if (record.get("M8") or {}).get("fails"):
        fails.append("M8")
    m9 = record.get("M9") or {}
    if m9.get("consoleErrors") or m9.get("httpErrors"):
        fails.append("M9")
    if len(record.get("M10") or []) > 2:
        fails.append("M10")
    if (record.get("U1") or {}).get("rawVisible", 0) > 0:
        fails.append("U1")
    if record.get("U2"):
        fails.append("U2")
    if record.get("U3"):
        fails.append("U3")
    if len(record.get("U4") or []) > 1:
        fails.append("U4")
    if record.get("A7"):
        fails.append("A7")
    if str(record.get("door", "")).startswith("NO DOOR"):
        fails.append("C3")
    return sorted(set(fails))


# ────────────────────────────────────────────────────────── the report


def write_report(out: Path, census: dict) -> Path:
    rows = census["surfaces"]
    by_surface: dict[str, list[dict]] = {}
    for r in rows:
        by_surface.setdefault(r["id"], []).append(r)

    # rank by the count of distinct failing rules across every leg
    ranked = []
    for sid, legs in by_surface.items():
        rules: set[str] = set()
        for leg in legs:
            rules.update(leg.get("fails") or [])
        measured = [l for l in legs if l.get("status") == "MEASURED"]
        ranked.append(
            {
                "id": sid,
                "name": legs[0]["name"],
                "family": legs[0]["family"],
                "rules": sorted(rules),
                "count": len(rules),
                "measured": len(measured),
                "legs": len(legs),
            }
        )
    ranked.sort(key=lambda r: (-r["count"], r["id"]))

    lines: list[str] = []
    w = lines.append
    w("# The measured walk — every face, with numbers (2026-09-20)")
    w("")
    w(f"Rig: `scripts/surface_census_walk.py`. Run at {census['ran_at']}.")
    w(f"Repo HEAD `{census['head']}`, branch `{census['branch']}`.")
    w("")
    w(
        "Every number here is read from the live product by the browser: "
        "`scripts/surface_census_measure.js` runs inside the page against the "
        "surface's own element. Rules are "
        "`docs/internal/surface-inventory-2026-09-20/00-rulebook.md` section B, "
        "plus the section-A counts a script can take honestly (U1/U2/U3/U4/A7) "
        "and the door check C3."
    )
    w("")
    w("**Honesty.** A face this rig could not open is `UNOPENED` with the reason. "
      "A measure it cannot take is `NOT ASSESSED` (`null`), never `0`. "
      "M11 (spacing rhythm) and M12 (motion) are NOT ASSESSED by this rig — "
      "see §6.")
    w("")

    # ── 1. what was walked
    w("## 1. What was walked")
    w("")
    w("| | |")
    w("|---|---|")
    w(f"| Desks | {', '.join(census['desks'])} |")
    w(f"| Widths | {', '.join(str(x) for x in census['widths'])} |")
    w(f"| Surfaces in the inventory | {len(by_surface)} |")
    w(f"| Legs walked (surface x desk x width) | {len(rows)} |")
    w(f"| Legs MEASURED | {sum(1 for r in rows if r['status'] == 'MEASURED')} |")
    w(f"| Legs UNOPENED | {sum(1 for r in rows if r['status'] == 'UNOPENED')} |")
    w(f"| Shots | {census['shots']} |")
    w("")
    for desk, s in census.get("seed", {}).items():
        w(f"**{desk} desk seed** — counts: `{json.dumps(s.get('counts', {}), sort_keys=True)}`")
        w("")
        if s.get("failures"):
            w(f"Seeding calls the API refused ({len(s['failures'])}) — the rich desk is "
              "poorer than the brief asked, and every face below was measured on what "
              "actually landed:")
            w("")
            for f in s["failures"][:40]:
                w(f"- `{f}`")
            w("")
        if s.get("notes"):
            for n in s["notes"]:
                w(f"- {n}")
            w("")

    # ── 2. the table, per surface
    w("## 2. Every surface, both widths, both desks")
    w("")
    w("`ovf` = M1 horizontal overflow px (document, or content past its window — the "
      "3px resize-handle affordance every window carries is subtracted; see §4). `cut` = M2 elements with "
      "text cut. `out` = M3 verbs outside the window or viewport. `folds` = M4 "
      "closed folds. `empty` = M5. `dup` = M6 strings shown twice. `<12px` / "
      "`<44px` = M7. `contrast` = M8 failures / assessed. `err` = M9 console + "
      "HTTP. `fonts` = M10 distinct stacks. `raw` = U1 raw buttons. `prim` = U4 "
      "filled primaries. `0-ctr` = U3. `prose` = A7 sentences. `ms` = M13 open→settled.")
    w("")
    for sid in sorted(by_surface):
        legs = by_surface[sid]
        head = legs[0]
        w(f"### {head['name']}  <sub>`{sid}`</sub>")
        w("")
        w(f"- Family: {head['family']} · Door: {head['door']}")
        w(f"- Opened by the rig via: `{head['opener']}`")
        w("")
        w("| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |")
        w("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for leg in sorted(legs, key=lambda l: (l["desk"], -l["width"])):
            w("| " + " | ".join(_row_cells(leg)) + " |")
        w("")
        # the evidence worth reading
        for leg in sorted(legs, key=lambda l: (l["desk"], -l["width"])):
            bits = _evidence(leg)
            if bits:
                w(f"<details><summary>{leg['desk']} @{leg['width']} — evidence</summary>")
                w("")
                for b in bits:
                    w(b)
                w("")
                w("</details>")
                w("")

    # ── 3. ranked worst
    w("## 3. The worst surfaces, ranked by failing rules")
    w("")
    w("| # | surface | family | rules failed | ids |")
    w("|---|---|---|---|---|")
    for i, r in enumerate(ranked[:30], 1):
        w(f"| {i} | {r['name']} | {r['family']} | {r['count']} | {', '.join(r['rules']) or '—'} |")
    w("")

    # ── 4. top findings
    w("## 4. Top findings")
    w("")
    for line in census.get("findings", []):
        w(f"- {line}")
    w("")

    # ── 5. unopened
    w("## 5. What could not be opened")
    w("")
    unopened = [r for r in rows if r["status"] != "MEASURED"]
    if not unopened:
        w("Nothing: every surface in the inventory opened on every leg.")
    else:
        w("| surface | desk | w | why |")
        w("|---|---|---|---|")
        for r in sorted(unopened, key=lambda r: (r["id"], r["desk"], -r["width"])):
            why = str(r.get("reason") or "").replace("|", "/")
            w(f"| {r['name']} | {r['desk']} | {r['width']} | {why} |")
    w("")

    # ── 6. not assessed
    w("## 6. What this rig does NOT measure")
    w("")
    w("- **M11 (spacing on the 4/8 rhythm)** — NOT ASSESSED. Computed gaps are "
      "resolved pixels; a token-derived 6px and a hand-typed 6px are "
      "indistinguishable to the DOM, so a count here would be a guess.")
    w("- **M12 (reduced motion, animation ≤ 400 ms)** — NOT ASSESSED. This walk "
      "settles animations before it shoots, which is the opposite of measuring "
      "them; a separate pass with `prefers-reduced-motion` toggled is the honest way.")
    w("- **D1/D2 (raw hex, raw px, the type scale)** — NOT ASSESSED at runtime: "
      "computed styles have already resolved the tokens. This is a source audit.")
    w("- **M4's 'not signalled' half** — this rig counts folds, tab bars and "
      "scroll containers and says what each hides. Whether the surface *signals* "
      "the hidden content is a reading, made in §4 from the counts, not a number.")
    w("- **M8 over an image or gradient** — text painted over a wallpaper or "
      "gradient is skipped and counted in `skippedOverImage`, never scored 0.")
    w("- **U3 in accessible names** — the rig counts zero-counters in VISIBLE text "
      "only. Names read by assistive tech are not scanned, and at least one zero "
      "counter lives there: the Floor's zone rows render "
      "`\u0060${row.count} items\u0060` unconditionally "
      "(`web/src/desk/components/DeskListView.tsx:214`), so an empty zone announces "
      "\u201c<name> zone, 0 items\u201d.")
    w("- **C1/C2/C4/C5** — the coherence rules are a reading across faces, not a "
      "per-surface number; they belong to the inventory's other lanes.")
    w("")
    path = out / "01-measured-walk.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def _n(value: Any) -> str:
    return "—" if value is None else str(value)


def _row_cells(leg: dict) -> list[str]:
    if leg.get("status") != "MEASURED":
        return [
            leg["desk"], str(leg["width"]), leg.get("status", "?"),
            *["—"] * 15, "C3" if "C3" in (leg.get("fails") or []) else "—",
        ]
    m1 = leg["M1"]
    ovf = max(m1["document"]["overflow"], m1["root"].get("contentOverflow", 0))
    m4 = leg["M4"]
    m7 = leg["M7"]
    m8 = leg["M8"]
    m9 = leg["M9"]
    m13 = leg.get("M13") or {}
    return [
        leg["desk"],
        str(leg["width"]),
        "ok",
        str(ovf) + (f"+{len(m1['inner'])}in" if m1["inner"] else ""),
        str(len(leg["M2"])),
        str(len(leg["M3"])),
        str(len([f for f in m4["folds"] if not f["open"]])) + f"/{len(m4['folds'])}",
        str(len(leg["M5"])),
        str(len(leg["M6"])),
        str(len(m7["smallText"])),
        "n/a" if m7["smallTargets"] is None else str(len(m7["smallTargets"])),
        f"{len(m8['fails'])}/{m8['assessed']}",
        str(len(m9["consoleErrors"]) + len(m9["httpErrors"])),
        str(len(leg["M10"])),
        str(leg["U1"]["rawVisible"]),
        str(len(leg["U4"])),
        str(len(leg["U3"])),
        str(len(leg["A7"])),
        _n(m13.get("openToSettledMs")),
        ", ".join(leg.get("fails") or []) or "—",
    ]


def _evidence(leg: dict) -> list[str]:
    if leg.get("status") != "MEASURED":
        return []
    out: list[str] = []
    m1 = leg["M1"]
    if m1["document"]["overflow"]:
        out.append(
            f"- **M1** the document scrolls sideways: {m1['document']['scrollWidth']}px in "
            f"{m1['document']['innerWidth']}px"
        )
    if m1["root"].get("contentOverflow"):
        widest = m1["root"].get("widest") or {}
        out.append(
            f"- **M1** content overflows its window by {m1['root']['contentOverflow']}px — "
            f"widest child `{widest.get('path','?')}` “{widest.get('text','')}”"
        )
    for inner in m1["inner"][:4]:
        out.append(f"- **M1 (inner)** `{inner['path']}` overflows by {inner['by']}px — “{inner['text']}”")
    for cut in leg["M2"][:6]:
        out.append(f"- **M2** `{cut['path']}` hides {cut['hiddenPx']}px on {cut['axis']} — “{cut['text']}”")
    for v in leg["M3"][:6]:
        where = "viewport" if v["outViewport"] else "window"
        out.append(f"- **M3** verb “{v['label']}” is outside its {where} — `{v['path']}`")
    for f in [f for f in leg["M4"]["folds"] if not f["open"]][:5]:
        out.append(f"- **M4** fold “{f['title']}” is closed over: “{f['hides']}”")
    for t in leg["M4"]["tablists"][:3]:
        labels = ", ".join(x["label"] for x in t["tabs"] if x["label"])
        if labels:
            out.append(f"- **M4** tab bar `{t['path']}`: {labels}")
    for e in leg["M5"][:6]:
        out.append(f"- **M5** {e['kind']} `{e['path']}`" + (f" — “{e.get('label','')}”" if e.get("label") else ""))
    for d in leg["M6"][:6]:
        out.append(f"- **M6** “{d['text']}” appears {d['count']}x")
    for s in leg["M7"]["smallText"][:6]:
        out.append(f"- **M7** {s['px']}px — “{s['text']}” `{s['path']}`")
    if leg["M7"]["smallTargets"]:
        for t in leg["M7"]["smallTargets"][:6]:
            out.append(f"- **M7** target {t['w']}x{t['h']}px — “{t['label']}”")
    for c in leg["M8"]["fails"][:8]:
        out.append(
            f"- **M8** {c['ratio']}:1 (needs {c['need']}) {c['fg']} on {c['bg']} at {c['px']}px — “{c['text']}”"
        )
    if leg["M8"]["skippedOverImage"]:
        out.append(
            f"- **M8** {leg['M8']['skippedOverImage']} text leaves NOT ASSESSED (painted over an image or gradient)"
        )
    for e in leg["M9"]["consoleErrors"][:6]:
        out.append(f"- **M9** console: `{e[:200]}`")
    for e in leg["M9"]["httpErrors"][:6]:
        out.append(f"- **M9** http: `{e[:200]}`")
    if len(leg["M10"]) > 2:
        out.append("- **M10** " + "; ".join(f"{f['family']} ({f['count']})" for f in leg["M10"]))
    if leg["U1"]["rawVisible"]:
        out.append(
            f"- **U1** {leg['U1']['rawVisible']} raw buttons vs {leg['U1']['libraryVisible']} library — "
            + json.dumps(leg["U1"]["byFirstClass"])
        )
    if len(leg["U4"]) > 1:
        out.append("- **U4** filled primaries: " + ", ".join(f"“{p['label']}”" for p in leg["U4"]))
    for z in leg["U3"][:6]:
        out.append(f"- **U3** “{z['text']}” `{z['path']}`")
    for p in leg["A7"][:6]:
        out.append(f"- **A7** {p['words']} words — “{p['text']}”")
    for u in leg["U2"][:3]:
        out.append(f"- **U2** dialog present — “{u['label']}”")
    return out


# Where a rule's finding usually lands in the source. Kept here so the
# generated report points at a seam instead of only a count.
FINDING_SEAMS: dict[str, str] = {
    "U1": "the library Button is `web/src/components/signal/Signal.tsx:36` "
          "(it stamps `btn btn--<variant>`); every visible `button` without `.btn` is a bounce",
    "M1": "window furniture: `.desk-window-edge-r { right: -3px }` "
          "`web/src/desk/components/window-chrome.css:42` (subtracted); the dock is "
          "`web/src/desk/components/window/Dock.tsx`",
    "M7": "the interior type scale lives in `web/src/styles/tokens.css`; "
          "menu keycaps are `.desk-menu-well` (`web/src/desk/components/DeskMenu.tsx:242`)",
    "M4": "folds are `FoldGadget` (`web/src/desk/surface/gadgets.tsx:417`); "
          "Settings' wings are `SETTINGS_WINGS` (`web/src/pages/cores/SettingsCore.tsx:233`)",
    "U3": "zone rows carry their count in the aria-label even at zero "
          "(the Floor's zone buttons)",
    "A7": "the empty Floor's prose line is `web/src/desk/components/EmptyDesk.tsx` "
          "(\u201cor right-click for more options\u201d)",
    "C3": "the Go shelf is a projection of `group` in the application manifest "
          "(`web/src/desk/tools.ts:4`); an application with no `group` has no Go row",
}


def build_findings(census: dict) -> list[str]:
    """The headline findings, each one a count this walk actually took."""
    rows = [r for r in census["surfaces"] if r.get("status") == "MEASURED"]
    out: list[str] = []
    if not rows:
        return ["No leg was measured — the walk opened nothing. Read §5."]

    def total(fn: Callable[[dict], int]) -> int:
        return sum(fn(r) for r in rows)

    raw = total(lambda r: r["U1"]["rawVisible"])
    lib = total(lambda r: r["U1"]["libraryVisible"])
    out.append(
        f"**U1** — {raw} raw `<button>` renders against {lib} library Buttons across {len(rows)} "
        f"measured legs. Every raw one is a bounce by UX-CANON A.1 "
        f"(the library Button is `web/src/components/signal/Signal.tsx:36`, which stamps `btn btn--<variant>`)."
    )
    dup_legs = [r for r in rows if r["M6"]]
    out.append(
        f"**M6** — {len(dup_legs)} of {len(rows)} legs state something twice on one screen; "
        f"{total(lambda r: len(r['M6']))} duplicate strings in all."
    )
    c8 = total(lambda r: len(r["M8"]["fails"]))
    assessed = total(lambda r: r["M8"]["assessed"])
    skipped = total(lambda r: r["M8"]["skippedOverImage"])
    out.append(
        f"**M8** — {c8} text elements below WCAG AA out of {assessed} assessed; "
        f"{skipped} more NOT ASSESSED (painted over a wallpaper or gradient)."
    )
    small = total(lambda r: len(r["M7"]["smallText"]))
    out.append(f"**M7** — {small} text elements render below 12px.")
    narrow = [r for r in rows if r["width"] <= 500 and r["M7"]["smallTargets"]]
    out.append(
        f"**M7 (touch)** — at 393, {sum(len(r['M7']['smallTargets']) for r in narrow)} verbs are "
        f"under 44px across {len(narrow)} legs."
    )
    ovf = [r for r in rows if r["M1"]["document"]["overflow"] or r["M1"]["root"].get("contentOverflow") or r["M1"]["inner"]]
    out.append(f"**M1** — {len(ovf)} legs overflow horizontally (document, window, or an inner clip).")
    cut = total(lambda r: len(r["M2"]))
    out.append(f"**M2** — {cut} elements show text that is cut off.")
    zeros = total(lambda r: len(r["U3"]))
    out.append(f"**U3** — {zeros} counters of zero rendered (UX-CANON A.8 forbids them).")
    prose = total(lambda r: len(r["A7"]))
    out.append(f"**A7** — {prose} sentences over 12 words outside note/transcript content.")
    many_primary = [r for r in rows if len(r["U4"]) > 1]
    out.append(f"**U4** — {len(many_primary)} legs draw more than one filled primary.")
    errs = [r for r in rows if r["M9"]["consoleErrors"] or r["M9"]["httpErrors"]]
    out.append(f"**M9** — {len(errs)} legs carry a console error or a 4xx/5xx.")
    fonts = [r for r in rows if len(r["M10"]) > 2]
    out.append(f"**M10** — {len(fonts)} legs render more than two font stacks.")
    nodoor = sorted({r["name"] for r in census["surfaces"] if str(r.get("door", "")).startswith("NO DOOR")})
    if nodoor:
        out.append(f"**C3** — {len(nodoor)} surfaces have no door a stranger can find: {', '.join(nodoor)}.")
    # attach the seam to each finding whose rule we know
    seamed = []
    for line in out:
        rule = line.split("**")[1] if "**" in line else ""
        rule = rule.split(" ")[0]
        seam = FINDING_SEAMS.get(rule)
        seamed.append(line + (f" Seam: {seam}." if seam else ""))
    return seamed


# ───────────────────────────────────────────────────────────── driver


GATE_SURFACE = next(s for s in STATES if s.id == "state-first-sentence")


def walk_gate(widths: list[int], out: Path, take_shots: bool) -> list[dict]:
    """The First Sentence gate gets a FRESH hub per width.

    The gate is up only while `arrival_required` holds
    (holdspeak/setup_status.py:306): first run AND no disposition. Crossing it
    once writes a disposition, so a second width on the same HOME would find
    the desk already through it. One hub per width is the only honest shot.
    """
    import tempfile

    from playwright.sync_api import sync_playwright

    records: list[dict] = []
    for width in widths:
        home = Path(tempfile.mkdtemp(prefix=f"hs202-gate-{width}-"))
        (home / ".holdspeak").mkdir(parents=True, exist_ok=True)
        hub = Hub(home).start()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                try:
                    page = browser.new_page(viewport={"width": width, "height": HEIGHTS.get(width, 900)})
                    page.emulate_media(reduced_motion="reduce")
                    walker = Walker(page, hub, width, "cold", out / "assets", take_shots)
                    record = walker.measure(GATE_SURFACE, None, 0)
                    record["fails"] = failing_rules(record)
                    records.append(record)
                    print(f"  {record['status']:9} {GATE_SURFACE.id:28} @{width} "
                          f"{', '.join(record['fails'])}", flush=True)
                    if record["status"] != "MEASURED":
                        print(f"            why: {record.get('reason')}", flush=True)
                    page.close()
                finally:
                    browser.close()
        finally:
            hub.stop()
    return records


def walk_desk(desk: str, widths: list[int], out: Path, only: list[str] | None, take_shots: bool) -> tuple[list[dict], dict]:
    import tempfile

    from playwright.sync_api import sync_playwright

    home = Path(tempfile.mkdtemp(prefix=f"hs202-{desk}-"))
    (home / ".holdspeak").mkdir(parents=True, exist_ok=True)
    hub = Hub(home).start()
    seed = Seed()
    records: list[dict] = []
    # the gate has its own hub per width (walk_gate); never walk it here
    surfaces = [s for s in all_surfaces() if (desk == "rich" or s.cold) and s.id != GATE_SURFACE.id]
    if only:
        surfaces = [s for s in surfaces if s.id in only]
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                if desk == "rich":
                    print("  seeding the rich desk …", flush=True)
                    page = browser.new_page(viewport={"width": 1440, "height": 900})
                    page.goto(f"{hub.url}/?token={hub.token}", wait_until="domcontentloaded")
                    api = Api(page, hub.token)
                    seed_rich(api, seed)
                    seed.failures.extend(api.failures)
                    print(f"  seeded: {json.dumps(seed.counts, sort_keys=True)}", flush=True)
                    if seed.failures:
                        print(f"  seeding refusals: {len(seed.failures)}", flush=True)
                    page.close()
                for width in widths:
                    print(f"\n== {desk} desk @{width} ==", flush=True)
                    page = browser.new_page(
                        viewport={"width": width, "height": HEIGHTS.get(width, 900)}
                    )
                    page.emulate_media(reduced_motion="reduce")
                    walker = Walker(page, hub, width, desk, out / "assets", take_shots)
                    for index, surface in enumerate(surfaces, 1):
                        record = walker.measure(surface, seed if desk == "rich" else None, index)
                        record["fails"] = failing_rules(record)
                        records.append(record)
                        mark = record["status"]
                        extra = ", ".join(record["fails"]) if record["fails"] else ""
                        print(f"  {mark:9} {surface.id:28} {extra}", flush=True)
                        if record["status"] != "MEASURED":
                            print(f"            why: {record.get('reason')}", flush=True)
                    page.close()
            finally:
                browser.close()
    finally:
        hub.stop()
    return records, {
        "counts": seed.counts,
        "failures": seed.failures,
        "notes": seed.notes,
        "refs": seed.refs,
        "home": str(home),
    }


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    if raw and raw[0] == "serve":
        sp = argparse.ArgumentParser(prog="surface_census_walk.py serve")
        sp.add_argument("--port", type=int, required=True)
        sp.add_argument("--token", required=True)
        sargs = sp.parse_args(raw[1:])
        return serve_forever(sargs.port, sargs.token)

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--desk", choices=("cold", "rich", "both"), default="both")
    ap.add_argument("--widths", default="1440,393")
    ap.add_argument("--only", action="append", default=None)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--no-shots", action="store_true")
    ap.add_argument("--no-build", action="store_true")
    ap.add_argument(
        "--report-only",
        action="store_true",
        help="re-render 01-measured-walk.md from an existing census.json (no walk)",
    )
    args = ap.parse_args(argv)

    if Path(os.environ.get("HOME", "")) == Path.home() and os.environ.get("HS202_ALLOW_REAL_HOME") != "1":
        pass  # HOME is read per-hub from a fresh mkdtemp; the owner's DB is never touched.

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    widths = [int(x) for x in args.widths.split(",") if x.strip()]
    desks = ["cold", "rich"] if args.desk == "both" else [args.desk]

    if args.report_only:
        census = json.loads((out / "census.json").read_text())
        census["findings"] = build_findings(census)
        (out / "census.json").write_text(json.dumps(census, indent=2))
        report = write_report(out, census)
        print(f"report   {report}")
        return 0

    if not args.no_build:
        ensure_build()

    head = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True
    ).stdout.strip()
    branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=REPO, capture_output=True, text=True
    ).stdout.strip()

    surfaces: list[dict] = []
    seeds: dict[str, dict] = {}
    if "cold" in desks and (not args.only or GATE_SURFACE.id in args.only):
        print("\n######## THE FIRST SENTENCE GATE (a fresh hub per width) ########", flush=True)
        try:
            surfaces.extend(walk_gate(widths, out, not args.no_shots))
        except Exception:
            traceback.print_exc()
    for desk in desks:
        print(f"\n######## {desk.upper()} DESK ########", flush=True)
        try:
            records, seed_info = walk_desk(desk, widths, out, args.only, not args.no_shots)
        except Exception:
            traceback.print_exc()
            records, seed_info = [], {"counts": {}, "failures": ["the walk itself crashed — see stderr"], "notes": []}
        surfaces.extend(records)
        seeds[desk] = seed_info

    census = {
        "ran_at": time.strftime("%Y-%m-%d %H:%M:%S %z"),
        "head": head,
        "branch": branch,
        "rulebook": "docs/internal/surface-inventory-2026-09-20/00-rulebook.md",
        "desks": desks,
        "widths": widths,
        "shots": sum(1 for r in surfaces if r.get("shot")),
        "seed": seeds,
        "surfaces": surfaces,
        "not_assessed": ["M11", "M12", "D1", "D2", "C1", "C2", "C4", "C5"],
    }
    census["findings"] = build_findings(census)
    (out / "census.json").write_text(json.dumps(census, indent=2, sort_keys=False))
    report = write_report(out, census)

    measured = sum(1 for r in surfaces if r["status"] == "MEASURED")
    print(f"\nreport   {report}")
    print(f"census   {out / 'census.json'}")
    print(f"shots    {census['shots']}")
    print(f"measured {measured}/{len(surfaces)} legs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
