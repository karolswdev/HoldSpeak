#!/usr/bin/env python3
"""THE INTERACTION WALK (2026-09-20) -- press every verb, on every surface.

The census lane (`scripts/surface_census_walk.py`) measures what a surface
LOOKS like. This lane measures what it DOES: every visible verb pressed,
every keyboard path walked, every menu enumerated, at 1440x900 and 393x852.

It changes no product code. It boots ONE real hub per run against an
isolated HOME, seeds it through the product's own services and HTTP
routes, and drives it with Playwright.

Run:
    HOME=$(mktemp -d) \
    PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \
        uv run python scripts/surface_interaction_walk.py

Outputs:
    docs/internal/surface-inventory-2026-09-20/interaction.json
    docs/internal/surface-inventory-2026-09-20/assets/interaction/*.png

Laws obeyed:
  * never the owner's HOME (the caller supplies a mktemp HOME; asserted).
  * never the microphone: chromium runs with a FAKE media device and the
    record/dictate verbs are on the no-press list (reported NOT ASSESSED).
  * never a destructive desk-wide verb (reset/wipe) -- it would eat the
    walk's own data; reported NOT ASSESSED with the reason.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "docs/internal/surface-inventory-2026-09-20"
SHOTS_DIR = OUT_DIR / "assets/interaction"
TOKEN = "surface-interaction-walk-token"
VIEWPORTS = ((1440, 900), (393, 852))
if os.environ.get("IW_VIEWPORTS") == "wide":
    VIEWPORTS = ((1440, 900),)
elif os.environ.get("IW_VIEWPORTS") == "narrow":
    VIEWPORTS = ((393, 852),)

# Verbs we refuse to press, and why. Reported NOT ASSESSED, never a pass.
# Class first (the mic species are named in the markup), label second.
# NOTE: the bare label "Speak" is the APPLICATION door and IS pressed; only
# the mic species (`desk-mic`, `desk-orb`, `desk-first-talk`) are refused.
NO_PRESS_CLASS = (
    ("desk-mic", "microphone"),
    ("desk-orb", "microphone"),
    ("desk-first-talk", "microphone"),
    ("gadget-transport-key", "microphone"),
)
NO_PRESS_LABEL_EXACT = {
    "talk": "microphone",
    "record a meeting": "microphone",
    "record meeting": "microphone",
    "record": "microphone",
    "click to speak": "microphone",
    "click to dictate": "microphone",
    "hold to talk": "microphone",
}
NO_PRESS_LABEL_PART = (
    ("speak ", "microphone (a mic gadget on a field)"),
    ("start recording", "microphone"),
    ("stop recording", "microphone"),
    ("reset desk", "destroys the walk's own seed"),
    ("reset layout", "destroys the walk's own window layout mid-walk"),
    ("seed desk", "destroys the walk's own seed"),
    ("wipe", "destroys the walk's own seed"),
    ("quit", "kills the hub"),
    ("shut down", "kills the hub"),
)

RESULT: dict[str, Any] = {
    "walk": "interaction",
    "date": "2026-09-20",
    "viewports": [],
    "notes": [],
}


def note(text: str) -> None:
    RESULT["notes"].append(text)
    print(f"  NOTE  {text}", flush=True)


def section(title: str) -> None:
    print(f"\n== {title} ==", flush=True)


# ─────────────────────────────────────────────────────────── the hub ──

def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class Hub:
    """A real hub in its own process with an isolated HOME."""

    def __init__(self, port: int, token: str, home: str) -> None:
        self.port = port
        self.token = token
        self.home = home
        self.url = f"http://127.0.0.1:{port}"
        self.proc: subprocess.Popen[str] | None = None

    def start(self, timeout: float = 180.0) -> "Hub":
        env = dict(os.environ)
        env["HOME"] = self.home
        env["HOLDSPEAK_WEB_PORT"] = str(self.port)
        env.setdefault("PYTHONUNBUFFERED", "1")
        self.proc = subprocess.Popen(
            [
                sys.executable,
                str(REPO / "scripts" / "walk_working_desk.py"),
                "serve",
                "--port", str(self.port),
                "--token", self.token,
            ],
            cwd=str(REPO), env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        print(f"  hub pid={self.proc.pid} home={self.home} port={self.port}",
              flush=True)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                out = self.proc.stdout.read() if self.proc.stdout else ""
                raise RuntimeError(f"hub died on boot:\n{out[-4000:]}")
            if self.healthy():
                return self
            time.sleep(0.4)
        raise RuntimeError(f"hub never became healthy at {self.url}")

    def healthy(self) -> bool:
        try:
            with socket.create_connection(("127.0.0.1", self.port), timeout=1.0):
                pass
        except OSError:
            return False
        try:
            req = urllib.request.Request(
                f"{self.url}/health", headers={"X-HoldSpeak-Token": self.token})
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def api(self, method: str, path: str, body: Any = None) -> tuple[int, Any]:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            f"{self.url}{path}", data=data, method=method,
            headers={
                "X-HoldSpeak-Token": self.token,
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode()
                try:
                    return resp.status, json.loads(raw)
                except Exception:
                    return resp.status, raw[:400]
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode()[:400]
        except Exception as exc:  # noqa: BLE001
            return 0, repr(exc)

    def stop(self) -> None:
        if self.proc is None or self.proc.poll() is not None:
            return
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=10)


# ──────────────────────────────────────────────────────── extra seed ──

def seed_extra(hub: Hub) -> dict[str, Any]:
    """Add projects, notes, people, thoughts and a LAN engine over HTTP.

    Every call's status is recorded: a route that refuses is a fact about
    the product, not a reason to lie about the desk's richness.
    """
    log: dict[str, Any] = {}

    def call(name: str, method: str, path: str, body: Any = None) -> Any:
        code, payload = hub.api(method, path, body)
        log[name] = {"path": path, "status": code,
                     "reply": payload if isinstance(payload, str)
                     else json.dumps(payload, default=str)[:300]}
        print(f"  seed {name}: {code} {path}", flush=True)
        return payload

    # Projects — the one-screen Door (HS-169-02): outcome + sources.
    call("project_alpha", "POST", "/api/projects/door",
         {"outcome": "Ship the payments platform cutover", "sources": []})
    call("project_beta", "POST", "/api/projects/door",
         {"outcome": "Finish the desk rewrite", "sources": []})
    # Notes (two, so a later search has more than one hit).
    call("note_1", "POST", "/api/notes",
         {"title": "Walk note", "body_markdown":
          "A note the walk can find later. Payments cutover risk."})
    call("note_2", "POST", "/api/notes",
         {"title": "Grammar of the dock", "body_markdown":
          "Second note so Desk search has two hits."})
    # People — NOT SEEDED on purpose. `POST /api/people/setup` is the one
    # gesture that creates the encrypted sidecar, and it goes through the
    # macOS Keychain; a walk must never raise a Keychain prompt on the
    # owner's machine. The People surface is therefore measured EMPTY and
    # its populated states are NOT ASSESSED.
    log["people"] = {"status": "NOT SEEDED",
                     "reply": "people/setup touches the Keychain; a walk never does"}
    # A LAN engine — define-endpoint against a real profile head.
    lib = call("model_library", "GET", "/api/inference/model-library")
    profile_id, revision = None, None
    if isinstance(lib, dict):
        profiles = lib.get("profiles") or lib.get("library", {}).get("profiles") or []
        if isinstance(profiles, list) and profiles:
            profile_id = profiles[0].get("id") or profiles[0].get("profile_id")
            revision = profiles[0].get("revision")
    if profile_id is not None and isinstance(revision, int):
        call("engine", "POST", "/api/inference/model-library/define-endpoint",
             {"draft": {
                 "request_id": "walk-endpoint-1",
                 "profile_id": profile_id,
                 "expected_profile_revision": revision,
                 "label": "Homelab .43",
                 "provider_family": "openai_compatible",
                 "model": "qwen2.5-7b-instruct",
                 "endpoint": "http://192.168.1.43:8080/v1",
                 "requires_key": False,
              }, "secret": None})
    else:
        log["engine"] = {"status": "NOT ASSESSED",
                         "reply": "no profile head to bind an endpoint to"}
        print("  seed engine: NOT ASSESSED (no profile head)", flush=True)
    call("setup", "GET", "/api/setup/status")
    return log


# ───────────────────────────────────────────────────── the probe JS ──

ENUMERATE_JS = r"""
(rootSel) => {
  const root = rootSel ? document.querySelector(rootSel) : document.body;
  if (!root) return [];
  const sel = "button,[role='button'],[role='menuitem'],[role='option'],a[href],summary,[role='tab'],[role='switch'],[role='checkbox']";
  const out = [];
  const nodes = [...root.querySelectorAll(sel)];
  nodes.forEach((el, i) => {
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return;
    const cs = getComputedStyle(el);
    if (cs.visibility === "hidden" || cs.display === "none") return;
    const text = (el.innerText || "").trim().replace(/\s+/g, " ");
    const aria = el.getAttribute("aria-label");
    const title = el.getAttribute("title");
    out.push({
      i,
      tag: el.tagName.toLowerCase(),
      cls: (el.className && el.className.baseVal !== undefined
            ? el.className.baseVal : String(el.className || "")).slice(0, 120),
      text: text.slice(0, 80),
      aria: aria ? aria.slice(0, 80) : null,
      title: title ? title.slice(0, 80) : null,
      role: el.getAttribute("role"),
      disabled: el.hasAttribute("disabled") ||
                el.getAttribute("aria-disabled") === "true",
      rect: {x: Math.round(r.x), y: Math.round(r.y),
             w: Math.round(r.width), h: Math.round(r.height)},
      iconOnly: text.length === 0,
      raw: el.tagName.toLowerCase() === "button" &&
           !/(^| )(btn|desk-btn|surface-btn|desk-light|desk-dock|desk-chip|desk-verbbar|desk-menu|desk-head|desk-window|desk-tool|desk-deck)/.test(
              String(el.className || "")),
    });
  });
  return out;
}
"""

SNAPSHOT_JS = r"""
() => {
  const wins = [...document.querySelectorAll(".desk-window")].map(
    w => (w.getAttribute("aria-label") || "").slice(0, 60));
  const pullouts = [...document.querySelectorAll(".desk-pullout")].map(
    w => (w.getAttribute("aria-label") || "").slice(0, 60));
  const txt = (document.body.innerText || "");
  let h = 0;
  for (let i = 0; i < txt.length; i++) { h = (h * 31 + txt.charCodeAt(i)) | 0; }
  const geom = [...document.querySelectorAll(".desk-window")].map(w => {
    const r = w.getBoundingClientRect();
    return (w.getAttribute("aria-label") || "") + ":" + String(w.className) +
           ":" + Math.round(r.x) + "," + Math.round(r.y) + "," +
           Math.round(r.width) + "," + Math.round(r.height);
  }).join("|");
  return {
    windows: wins, pullouts, geom,
    menus: document.querySelectorAll("[role='menu']").length,
    dialogs: document.querySelectorAll("[role='dialog']").length,
    textLen: txt.length, textHash: h,
    url: location.pathname + location.search,
  };
}
"""

MOTION_JS = r"""
() => {
  const long = [], geo = [];
  const seen = new Set();
  for (const sheet of document.styleSheets) {
    let rules;
    try { rules = sheet.cssRules; } catch (e) { continue; }
    if (!rules) continue;
    const walk = (list) => {
      for (const rule of list) {
        if (rule.cssRules) { walk(rule.cssRules); continue; }
        const st = rule.style; if (!st) continue;
        const sel = (rule.selectorText || "").slice(0, 90);
        const dur = st.transitionDuration || st.animationDuration || "";
        for (const part of dur.split(",")) {
          const t = part.trim();
          if (!t) continue;
          const ms = t.endsWith("ms") ? parseFloat(t)
                   : t.endsWith("s") ? parseFloat(t) * 1000 : 0;
          if (ms > 400) {
            const k = sel + "|" + t;
            if (!seen.has(k)) { seen.add(k); long.push({sel, dur: t, ms}); }
          }
        }
        const props = (st.transitionProperty || "") + " " +
                      (st.getPropertyValue("transition") || "");
        if (/\b(width|height|top|left|right|bottom)\b/.test(props)) {
          const k = "geo|" + sel;
          if (!seen.has(k)) { seen.add(k); geo.push({sel, props: props.trim().slice(0,90)}); }
        }
      }
    };
    walk(rules);
  }
  return {
    longTransitions: long.slice(0, 60),
    geometryTransitions: geo.slice(0, 60),
    running: document.getAnimations().map(a => ({
      dur: (a.effect && a.effect.getTiming) ? a.effect.getTiming().duration : null,
    })).slice(0, 40),
    reducedMotionMatches: matchMedia("(prefers-reduced-motion: reduce)").matches,
  };
}
"""

TOUCH_JS = r"""
() => {
  const sel = "button,[role='button'],a[href],input,select,textarea,[role='menuitem'],[role='option'],[role='tab'],[role='switch']";
  const els = [...document.querySelectorAll(sel)].filter(el => {
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && cs.visibility !== "hidden" &&
           r.top < innerHeight && r.bottom > 0;
  });
  const describe = (el) => {
    const r = el.getBoundingClientRect();
    return {
      label: ((el.innerText || "").trim().replace(/\s+/g," ").slice(0,50)) ||
             el.getAttribute("aria-label") || el.getAttribute("title") || "(no name)",
      cls: String(el.className || "").slice(0, 80),
      w: Math.round(r.width), h: Math.round(r.height),
      x: Math.round(r.x), y: Math.round(r.y),
    };
  };
  const small = els.filter(el => {
    const r = el.getBoundingClientRect();
    return r.width < 44 || r.height < 44;
  }).map(describe);
  // nearest-neighbour gap
  const boxes = els.map(el => ({el, r: el.getBoundingClientRect()}));
  const tight = [];
  for (let i = 0; i < boxes.length; i++) {
    for (let j = i + 1; j < boxes.length; j++) {
      const a = boxes[i].r, b = boxes[j].r;
      if (boxes[i].el.contains(boxes[j].el) || boxes[j].el.contains(boxes[i].el)) continue;
      const dx = Math.max(0, Math.max(a.left, b.left) - Math.min(a.right, b.right));
      const dy = Math.max(0, Math.max(a.top, b.top) - Math.min(a.bottom, b.bottom));
      if (dx === 0 && dy === 0) continue;
      const gap = dx === 0 ? dy : dy === 0 ? dx : Math.hypot(dx, dy);
      if (gap > 0 && gap < 8) tight.push({
        a: describe(boxes[i].el).label, b: describe(boxes[j].el).label,
        gap: Math.round(gap),
      });
    }
  }
  const hoverOnly = els.filter(el =>
    el.hasAttribute("title") && !(el.innerText || "").trim()).map(describe);
  const iconNoName = els.filter(el =>
    !(el.innerText || "").trim() && !el.getAttribute("aria-label") &&
    (el.tagName === "BUTTON" || el.getAttribute("role") === "button")
  ).map(describe);
  return {total: els.length, small, tight: tight.slice(0, 40), hoverOnly,
          iconNoName, docScrollW: document.documentElement.scrollWidth,
          clientW: document.documentElement.clientWidth};
}
"""

FOCUS_JS = r"""
() => {
  const el = document.activeElement;
  if (!el || el === document.body) return null;
  const cs = getComputedStyle(el);
  const r = el.getBoundingClientRect();
  return {
    tag: el.tagName.toLowerCase(),
    cls: String(el.className || "").slice(0, 80),
    label: ((el.innerText || "").trim().replace(/\s+/g," ").slice(0,50)) ||
           el.getAttribute("aria-label") || el.getAttribute("placeholder") || "(no name)",
    outline: cs.outlineStyle + " " + cs.outlineWidth + " " + cs.outlineColor,
    outlineWidth: parseFloat(cs.outlineWidth) || 0,
    boxShadow: (cs.boxShadow || "none").slice(0, 60),
    x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
    visible: r.width > 0 && r.height > 0,
  };
}
"""

SCROLL_JS = r"""
() => {
  const wins = [...document.querySelectorAll(".desk-window")];
  return wins.map(w => {
    const scrollers = [...w.querySelectorAll("*")].filter(el => {
      const cs = getComputedStyle(el);
      return /(auto|scroll)/.test(cs.overflowY) && el.scrollHeight > el.clientHeight + 2;
    });
    const head = w.querySelector(".desk-window-handle, .desk-pullout-head");
    const foot = w.querySelector(".desk-window-foot, .surface-footer, footer");
    const lights = [...w.querySelectorAll(".desk-light")].map(
      l => l.getAttribute("aria-label"));
    const r = w.getBoundingClientRect();
    return {
      name: w.getAttribute("aria-label"),
      title: (w.querySelector(".desk-window-title") || {}).textContent || null,
      sheet: /is-sheet/.test(w.className), max: /is-max/.test(w.className),
      lights, hasHead: !!head, hasFoot: !!foot,
      scrollers: scrollers.length,
      scrollerCls: scrollers.slice(0, 4).map(e => String(e.className || "").slice(0, 60)),
      overflowX: w.scrollWidth - w.clientWidth,
      rect: {x: Math.round(r.x), y: Math.round(r.y),
             w: Math.round(r.width), h: Math.round(r.height)},
      outsideViewport: r.right > innerWidth + 1 || r.bottom > innerHeight + 1 ||
                       r.left < -1 || r.top < -1,
    };
  });
}
"""


# ───────────────────────────────────────────────────────── the driver ──

def _ignorable_console(text: str) -> bool:
    low = text.lower()
    return any(t in low for t in (
        "failed to load resource", "err_connection_refused", "websocket",
        "net::err", "download the react devtools"))


EGRESS_HINT = (
    "/intel", "/summary", "/ask", "/chat", "/draft", "/prepare", "/route",
    "/connector", "/github", "/jira", "/sync", "/models", "/engine",
    "/brief", "/updates", "/reviews", "/run-now", "/dispatch",
)


class Walker:
    def __init__(self, page: Any, width: int, height: int, hub: Hub) -> None:
        self.page = page
        self.width = width
        self.height = height
        self.hub = hub
        self.console: list[str] = []
        self.requests: list[str] = []
        self.gate_seen = 0
        self.gate_shot: str | None = None
        self.gate_html: str | None = None
        self.gate_verbs: list[Any] = []
        self.gate_escaped: bool | None = None
        page.on("pageerror", lambda e: self.console.append(f"pageerror: {e}"))
        page.on("console", lambda m: (
            self.console.append(f"console.error: {m.text}")
            if m.type == "error" else None))
        page.on("request", lambda r: self.requests.append(f"{r.method} {r.url}"))

    # -- helpers ------------------------------------------------------
    def goto_desk(self) -> None:
        """Load the desk. A cold desk answers with the First Words gate:
        the ONE face a fresh install shows, with no menubar, no dock and a
        surface registry in `recovery-only`. The walk records that and then
        presses its only escape ("Continue later") to reach the desk."""
        self.page.goto(f"{self.hub.url}/?token={self.hub.token}",
                       wait_until="domcontentloaded")
        try:
            self.page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        self.page.wait_for_timeout(2500)
        gate = self.page.locator(".desk-first-words")
        if gate.count():
            self.gate_seen += 1
            if self.gate_shot is None:
                self.gate_shot = self.shot("first-words-gate")
                self.gate_html = self.page.evaluate(
                    "() => document.querySelector('.desk-surface-windows')"
                    "?.getAttribute('data-surface-registry-state')")
                self.gate_verbs = self.page.evaluate(ENUMERATE_JS, ".desk-first-words")
            escape = self.page.locator(".desk-first-words .btn--ghost")
            if escape.count():
                try:
                    escape.first.click(timeout=4000)
                    self.page.wait_for_timeout(3800)
                except Exception:
                    pass
            self.gate_escaped = self.page.locator(".desk-first-words").count() == 0

    def shot(self, name: str) -> str:
        SHOTS_DIR.mkdir(parents=True, exist_ok=True)
        fn = f"{name}-{self.width}.png"
        try:
            self.page.screenshot(path=str(SHOTS_DIR / fn), full_page=False)
        except Exception as exc:  # noqa: BLE001
            return f"SHOT-FAILED {exc!r}"
        print(f"  SHOT  {fn}", flush=True)
        return fn

    def snap(self) -> dict[str, Any]:
        try:
            return self.page.evaluate(SNAPSHOT_JS)
        except Exception as exc:  # noqa: BLE001
            return {"error": repr(exc)}

    def api_since(self, mark: int) -> list[str]:
        out = []
        for r in self.requests[mark:]:
            if "/api/" in r or "/mcp" in r:
                out.append(r.split("?")[0].replace(self.hub.url, ""))
        return out

    def press(self, locator: Any, label: str, *, settle: int = 900) -> dict[str, Any]:
        """Press one verb and classify what happened."""
        before = self.snap()
        mark = len(self.requests)
        err_mark = len(self.console)
        result: dict[str, Any] = {"verb": label}
        try:
            locator.click(timeout=4000)
        except Exception as exc:  # noqa: BLE001
            result["effect"] = "CLICK-FAILED"
            result["detail"] = repr(exc)[:160]
            return result
        self.page.wait_for_timeout(settle)
        after = self.snap()
        reqs = self.api_since(mark)
        errs = [e for e in self.console[err_mark:] if not _ignorable_console(e)]
        new_windows = [w for w in after.get("windows", [])
                       if w not in before.get("windows", [])]
        new_pullouts = [p for p in after.get("pullouts", [])
                        if p not in before.get("pullouts", [])]
        changed = (before.get("textHash") != after.get("textHash") or
                   before.get("url") != after.get("url") or
                   before.get("menus") != after.get("menus") or
                   before.get("geom") != after.get("geom"))
        effects = []
        if new_windows:
            effects.append("WINDOW:" + "|".join(new_windows[:2]))
        if new_pullouts:
            effects.append("PULLOUT:" + "|".join(new_pullouts[:2]))
        if reqs:
            effects.append(f"REQUEST:{len(reqs)}")
        if changed and not new_windows and not new_pullouts:
            effects.append("STATE")
        if errs:
            effects.append("ERROR")
        result["effect"] = " ".join(effects) if effects else "NOTHING"
        result["requests"] = reqs[:6]
        result["errors"] = errs[:3]
        result["egress"] = sorted({r for r in reqs
                                   if any(h in r for h in EGRESS_HINT)})
        return result


def no_press_reason(label: str, cls: str = "") -> str | None:
    for token, why in NO_PRESS_CLASS:
        if token in (cls or ""):
            return why
    low = (label or "").strip().lower()
    if low in NO_PRESS_LABEL_EXACT:
        return NO_PRESS_LABEL_EXACT[low]
    for token, why in NO_PRESS_LABEL_PART:
        if token in low:
            return why
    return None


# ───────────────────────────────────────────────────────────── legs ──

def leg_menus(w: Walker) -> dict[str, Any]:
    """The four menus: enumerate, then press every enabled entry."""
    section(f"menus @{w.width}")
    out: dict[str, Any] = {"menus": [], "presses": []}
    w.goto_desk()
    titles = w.page.locator("nav.desk-verbbar .desk-verbbar-title")
    n = titles.count()
    out["menubar_present"] = n > 0
    if n == 0:
        note(f"@{w.width}: no menubar (nav.desk-verbbar) found")
        return out
    names = [titles.nth(i).inner_text().strip() for i in range(n)]
    out["menu_names"] = names
    for i, name in enumerate(names):
        try:
            titles.nth(i).click(timeout=4000)
            w.page.wait_for_timeout(450)
        except Exception as exc:  # noqa: BLE001
            out["menus"].append({"menu": name, "error": repr(exc)[:120]})
            continue
        entries = w.page.evaluate(ENUMERATE_JS, "[role='menu']")
        out["menus"].append({
            "menu": name,
            "count": len(entries),
            "entries": [{"label": e["aria"] or e["text"], "disabled": e["disabled"],
                         "role": e["role"]} for e in entries],
        })
        w.shot(f"menu-{name.lower().replace(' ', '-')}")
        w.page.keyboard.press("Escape")
        w.page.wait_for_timeout(250)

    # press each entry, re-opening its menu each time
    for mi, menu in enumerate(out["menus"]):
        if "entries" not in menu:
            continue
        for ei, entry in enumerate(menu["entries"]):
            label = entry["label"] or "(unnamed)"
            rec = {"menu": menu["menu"], "verb": label}
            why = no_press_reason(label)
            if why:
                rec["effect"] = "NOT ASSESSED"
                rec["detail"] = why
                out["presses"].append(rec)
                continue
            if entry["disabled"]:
                rec["effect"] = "DISABLED"
                out["presses"].append(rec)
                continue
            try:
                w.goto_desk()
                titles = w.page.locator("nav.desk-verbbar .desk-verbbar-title")
                titles.nth(mi).click(timeout=4000)
                w.page.wait_for_timeout(400)
                items = w.page.locator("[role='menu'] [role='menuitem'], "
                                       "[role='menu'] [role='menuitemcheckbox'], "
                                       "[role='menu'] [role='menuitemradio']")
                if ei >= items.count():
                    rec["effect"] = "NOT ASSESSED"
                    rec["detail"] = "menu shape changed between enumerate and press"
                    out["presses"].append(rec)
                    continue
                rec.update(w.press(items.nth(ei), label))
            except Exception as exc:  # noqa: BLE001
                rec["effect"] = "PRESS-ERROR"
                rec["detail"] = repr(exc)[:140]
            out["presses"].append(rec)
            print(f"  {menu['menu']} > {label}: {rec.get('effect')}", flush=True)
    return out


def leg_dock(w: Walker) -> dict[str, Any]:
    section(f"dock @{w.width}")
    out: dict[str, Any] = {"items": [], "presses": []}
    w.goto_desk()
    items = w.page.evaluate(ENUMERATE_JS, ".desk-dock")
    out["present"] = bool(items)
    out["items"] = [{"label": e["aria"] or e["text"], "iconOnly": e["iconOnly"],
                     "cls": e["cls"][:50],
                     "w": e["rect"]["w"], "h": e["rect"]["h"]} for e in items]
    if not items:
        note(f"@{w.width}: no dock (.desk-dock) rendered")
        return out
    w.shot("dock")
    buttons = w.page.locator(".desk-dock button")
    for i in range(min(buttons.count(), 24)):
        label = out["items"][i]["label"] if i < len(out["items"]) else f"#{i}"
        rec: dict[str, Any] = {"verb": label}
        why = no_press_reason(label or "",
                              out["items"][i]["cls"] if i < len(out["items"]) else "")
        if why:
            rec["effect"] = "NOT ASSESSED"
            rec["detail"] = why
            out["presses"].append(rec)
            continue
        try:
            w.goto_desk()
            b = w.page.locator(".desk-dock button")
            if i >= b.count():
                rec["effect"] = "NOT ASSESSED"
                rec["detail"] = "dock shape changed"
                out["presses"].append(rec)
                continue
            rec.update(w.press(b.nth(i), label or f"#{i}"))
        except Exception as exc:  # noqa: BLE001
            rec["effect"] = "PRESS-ERROR"
            rec["detail"] = repr(exc)[:140]
        out["presses"].append(rec)
        print(f"  dock > {label}: {rec.get('effect')}", flush=True)
    return out


def open_shelf(w: Walker) -> bool:
    """Open the ⌘K tool shelf by keyboard alone. True if it opened."""
    w.page.keyboard.press("Meta+k")
    w.page.wait_for_timeout(600)
    if w.page.locator(".desk-tool-shelf").count():
        return True
    w.page.keyboard.press("Control+k")
    w.page.wait_for_timeout(600)
    return bool(w.page.locator(".desk-tool-shelf").count())


def leg_shelf(w: Walker) -> dict[str, Any]:
    section(f"cmd-K shelf @{w.width}")
    out: dict[str, Any] = {}
    w.goto_desk()
    opened = open_shelf(w)
    out["opens_by_keyboard"] = opened
    if not opened:
        note(f"@{w.width}: Cmd+K / Ctrl+K did not open .desk-tool-shelf")
        return out
    w.shot("shelf-open")
    rows = w.page.evaluate(ENUMERATE_JS, ".desk-tool-shelf")
    out["rows"] = [{"label": r["text"] or r["aria"], "role": r["role"]}
                   for r in rows]
    out["row_count"] = len(rows)
    # Escape closes it?
    w.page.keyboard.press("Escape")
    w.page.wait_for_timeout(500)
    out["escape_closes"] = w.page.locator(".desk-tool-shelf").count() == 0
    # Arrow + Enter opens the first row?
    if open_shelf(w):
        before = w.snap()
        w.page.keyboard.press("ArrowDown")
        w.page.wait_for_timeout(200)
        w.page.keyboard.press("Enter")
        w.page.wait_for_timeout(1200)
        after = w.snap()
        out["enter_opens_something"] = (
            after.get("windows") != before.get("windows") or
            after.get("textHash") != before.get("textHash"))
        out["after_enter_windows"] = after.get("windows", [])[:6]
        w.shot("shelf-enter")
    return out


def close_all_windows(w: Walker) -> int:
    """Empty the desk so the next surface opens alone and front.

    The whole window layout lives in ONE browser key --
    `localStorage["hs.desk.workspace.v1"]` (measured) -- and the desk
    rewrites it on every store change, so clearing it from the live page
    is undone before the reload lands. The reset therefore ARMS a flag in
    sessionStorage (which survives the same-tab navigation) and lets the
    context's init script clear the key at document-start, before any app
    code runs. Pressing the close lights one by one does not converge:
    11 windows survived 14 presses in the pilot run.
    """
    try:
        w.page.evaluate("() => sessionStorage.setItem('iw-reset', '1')")
    except Exception:
        return 0
    return 1


# A BARE STATEMENT, not an arrow function: `add_init_script` evaluates the
# source, so `() => {...}` would only produce a function value and never
# run (measured: 12 windows survived the "reset" while this was wrapped).
RESET_INIT_JS = """
try {
  if (sessionStorage.getItem('iw-reset') === '1') {
    sessionStorage.removeItem('iw-reset');
    localStorage.clear();
  }
} catch (e) {}
"""


def close_new_windows(w: Walker, keep: str) -> int:
    """Close every window whose name is not ``keep`` (cheap, in place)."""
    closed = 0
    for _ in range(8):
        names = w.snap().get("windows", [])
        extra = [n for n in names if n != keep]
        if not extra:
            break
        try:
            w.page.locator(
                f'.desk-window[aria-label="{extra[0]}"] .desk-light-close'
            ).first.click(timeout=2000)
            closed += 1
            w.page.wait_for_timeout(250)
        except Exception:
            break
    return closed


def shelf_open_named(w: Walker, query: str, *, keyboard: bool = False,
                     reset: bool = True) -> list[str]:
    """Open a catalog row for ``query`` from an empty desk.

    ``keyboard=True`` is the no-mouse path (type, Enter on the highlighted
    row) used by the owner-job scorecard. The default path clicks the row
    whose label carries the name, so a surface leg measures the surface it
    asked for and not whichever row the highlight happened to sit on.
    """
    if reset:
        close_all_windows(w)
        w.goto_desk()
    if not open_shelf(w):
        return []
    box = w.page.locator(".desk-tool-search input")
    if box.count() == 0:
        return []
    box.first.fill(query)
    w.page.wait_for_timeout(600)
    if keyboard:
        w.page.keyboard.press("Enter")
    else:
        rows = w.page.locator(".desk-tool-shelf [role='option']")
        hit = None
        for i in range(min(rows.count(), 25)):
            if query.lower() in (rows.nth(i).inner_text() or "").lower():
                hit = i
                break
        if hit is None:
            w.page.keyboard.press("Enter")
        else:
            rows.nth(hit).click()
    w.page.wait_for_timeout(1800)
    return w.snap().get("windows", [])


def leg_surface(w: Walker, query: str, cap: int = 18) -> dict[str, Any]:
    """Open one surface by name and press every verb inside its window."""
    section(f"surface '{query}' @{w.width}")
    out: dict[str, Any] = {"query": query}
    windows = shelf_open_named(w, query)
    out["opened_windows"] = windows
    if not windows:
        out["status"] = "DID NOT OPEN"
        note(f"@{w.width}: '{query}' opened no window from the shelf")
        return out
    out["status"] = "open"
    target = next((n for n in windows if query.lower() in (n or "").lower()), None)
    out["title_matches_query"] = target is not None
    # The desk opens windows the walk never asked for (an attention nudge
    # takes the front on arrival), so `is-front` is NOT the surface under
    # test. Scope by the window's own name.
    out["unrequested_windows"] = [n for n in windows if n != target]
    if target is None:
        out["status"] = "OPENED SOMETHING ELSE"
        note(f"@{w.width}: '{query}' opened {windows} -- no window carries the name")
        return out
    # Clear the unrequested windows off the target and raise it, or every
    # verb inside it is unclickable behind another window's glass.
    out["cleared_before_probe"] = close_new_windows(w, target)
    try:
        w.page.locator(f'.desk-window[aria-label="{target}"] '
                       '.desk-window-title').first.click(timeout=2500)
        w.page.wait_for_timeout(300)
    except Exception:
        pass
    slug = query.lower().replace(" ", "-")
    out["shot"] = w.shot(f"surface-{slug}")
    out["window_grammar"] = [g for g in w.page.evaluate(SCROLL_JS)
                             if g.get("name") == target]
    scope = f'.desk-window[aria-label="{target}"]'
    verbs = w.page.evaluate(ENUMERATE_JS, scope)
    out["verb_count"] = len(verbs)
    out["raw_buttons"] = [v["text"] or v["aria"] for v in verbs if v["raw"]][:12]
    out["icon_no_name"] = [v["cls"][:50] for v in verbs
                           if v["iconOnly"] and not v["aria"]][:12]
    out["presses"] = []
    for i, v in enumerate(verbs[:cap]):
        label = v["aria"] or v["text"] or f"({v['cls'][:24]})"
        rec: dict[str, Any] = {"verb": label, "disabled": v["disabled"]}
        why = no_press_reason(label, v["cls"])
        if why:
            rec["effect"] = "NOT ASSESSED"
            rec["detail"] = why
            out["presses"].append(rec)
            continue
        if v["disabled"]:
            rec["effect"] = "DISABLED"
            out["presses"].append(rec)
            continue
        try:
            sel = (f"{scope} button, {scope} [role='button'], "
                   f"{scope} a[href], {scope} [role='tab']")
            live = w.page.locator(sel)
            if i >= live.count():
                # the surface re-rendered smaller; re-open and retry once
                shelf_open_named(w, query)
                live = w.page.locator(sel)
                if i >= live.count():
                    rec["effect"] = "NOT ASSESSED"
                    rec["detail"] = "verb list shrank under the walk"
                    out["presses"].append(rec)
                    continue
            rec.update(w.press(live.nth(i), label))
        except Exception as exc:  # noqa: BLE001
            rec["effect"] = "PRESS-ERROR"
            rec["detail"] = repr(exc)[:140]
        out["presses"].append(rec)
        print(f"  {query} > {label}: {rec.get('effect')}", flush=True)
        # a verb that opened another window: close it in place and keep
        # the surface under test in front (cheap; a full re-open costs ~10s)
        eff = rec.get("effect", "")
        if "WINDOW" in eff or "CLICK-FAILED" in eff:
            rec["cleanup_closed"] = close_new_windows(w, target)
            if w.page.locator(f'.desk-window[aria-label="{target}"]').count() == 0:
                shelf_open_named(w, query)
    out["dead_verbs"] = [p["verb"] for p in out["presses"]
                         if p.get("effect") == "NOTHING"]
    return out


def leg_keyboard(w: Walker) -> dict[str, Any]:
    """Tab through the desk: reach, focus ring, order, Escape."""
    section(f"keyboard @{w.width}")
    out: dict[str, Any] = {}
    w.goto_desk()
    w.page.keyboard.press("Tab")
    stops: list[dict[str, Any]] = []
    seen = set()
    for _ in range(60):
        f = w.page.evaluate(FOCUS_JS)
        if f is None:
            break
        key = (f["tag"], f["label"], f["x"], f["y"])
        if key in seen:
            break
        seen.add(key)
        stops.append(f)
        w.page.keyboard.press("Tab")
        w.page.wait_for_timeout(60)
    out["tab_stops"] = len(stops)
    out["no_focus_ring"] = [s["label"] for s in stops
                            if s["outlineWidth"] < 1 and
                            s["boxShadow"] in ("none", "")][:15]
    out["offscreen_stops"] = [s["label"] for s in stops if not s["visible"]][:10]
    # tab order vs visual order (top-to-bottom, left-to-right)
    visual = sorted(range(len(stops)),
                    key=lambda i: (stops[i]["y"] // 24, stops[i]["x"]))
    inversions = sum(1 for a in range(len(visual))
                     for b in range(a + 1, len(visual)) if visual[a] > visual[b])
    out["order_inversions"] = inversions
    out["order_pairs"] = len(visual) * (len(visual) - 1) // 2
    out["first_ten"] = [s["label"] for s in stops[:10]]
    if stops:
        w.shot("keyboard-focus")
    # Escape closes what Enter opened
    opened = shelf_open_named(w, "Notes")
    if opened:
        w.page.keyboard.press("Escape")
        w.page.wait_for_timeout(600)
        after = w.snap().get("windows", [])
        out["escape_closes_window"] = len(after) < len(opened)
        out["escape_before"] = opened[:4]
        out["escape_after"] = after[:4]
    else:
        out["escape_closes_window"] = None
        out["escape_note"] = "NOT ASSESSED: Notes did not open from the shelf"
    return out


OWNER_JOBS = [
    ("dictate", "Speak"),
    ("record to summary", "Meetings"),
    ("write a thought", "Thoughts"),
    ("find a note later", "Notes"),
    ("set up an engine", "Models"),
]


def leg_owner_jobs(w: Walker) -> dict[str, Any]:
    """Can each of the five owner jobs be STARTED with no mouse?"""
    section(f"owner jobs, keyboard only @{w.width}")
    out: dict[str, Any] = {"jobs": []}
    for job, query in OWNER_JOBS:
        rec: dict[str, Any] = {"job": job, "query": query}
        try:
            windows = shelf_open_named(w, query, keyboard=True)
            rec["reached_by_keyboard"] = bool(windows)
            rec["windows"] = windows[:4]
            if windows:
                rec["shot"] = w.shot(f"job-{query.lower()}")
                # can the first verb inside be reached by Tab?
                w.page.keyboard.press("Tab")
                w.page.wait_for_timeout(120)
                f = w.page.evaluate(FOCUS_JS)
                rec["first_tab_inside"] = f["label"] if f else None
                rec["focus_ring"] = bool(
                    f and (f["outlineWidth"] >= 1 or f["boxShadow"] not in ("none", "")))
            if job == "dictate":
                rec["completion"] = ("NOT ASSESSED: the walk never presses the "
                                     "microphone")
            elif job == "record to summary":
                rec["completion"] = ("NOT ASSESSED: needs a real recording; the "
                                     "walk never presses the microphone")
            else:
                rec["completion"] = "surface reached; verb presses measured separately"
        except Exception as exc:  # noqa: BLE001
            rec["error"] = repr(exc)[:140]
        out["jobs"].append(rec)
        print(f"  job {job}: reached={rec.get('reached_by_keyboard')}", flush=True)
    return out


def leg_touch(w: Walker) -> dict[str, Any]:
    section(f"touch @{w.width}")
    w.goto_desk()
    desk = w.page.evaluate(TOUCH_JS)
    out = {"desk": desk}
    # and inside one opened window
    if shelf_open_named(w, "Meetings"):
        out["meetings_window"] = w.page.evaluate(TOUCH_JS)
        out["shot"] = w.shot("touch-meetings")
    return out


def leg_motion(w: Walker) -> dict[str, Any]:
    section(f"motion @{w.width}")
    w.goto_desk()
    return w.page.evaluate(MOTION_JS)


# ──────────────────────────────────────────────────────────── main ──

def run_viewport(browser: Any, hub: Any, width: int, height: int,
                 reduced: bool = False) -> dict[str, Any]:
    ctx = browser.new_context(
        viewport={"width": width, "height": height},
        device_scale_factor=2,
        reduced_motion="reduce" if reduced else "no-preference",
        permissions=[],
    )
    ctx.add_init_script(RESET_INIT_JS)
    page = ctx.new_page()
    w = Walker(page, width, height, hub)
    data: dict[str, Any] = {"width": width, "height": height,
                            "reduced_motion": reduced}
    legs = [
        ("menus", leg_menus), ("dock", leg_dock), ("shelf", leg_shelf),
        ("keyboard", leg_keyboard), ("owner_jobs", leg_owner_jobs),
        ("touch", leg_touch), ("motion", leg_motion),
    ]
    if reduced:
        legs = [("motion", leg_motion)]
    for name, fn in legs:
        try:
            data[name] = fn(w)
        except Exception as exc:  # noqa: BLE001
            data[name] = {"leg_error": repr(exc)[:300]}
            note(f"@{width} leg {name} failed: {exc!r}")
    if not reduced:
        data["surfaces"] = {}
        for query in SURFACE_QUERIES:
            try:
                data["surfaces"][query] = leg_surface(w, query)
            except Exception as exc:  # noqa: BLE001
                data["surfaces"][query] = {"leg_error": repr(exc)[:300]}
                note(f"@{width} surface {query} failed: {exc!r}")
    data["first_words_gate"] = {
        "seen_on_every_load": w.gate_seen,
        "shot": w.gate_shot,
        "surface_registry_state_behind_it": w.gate_html,
        "verbs_on_the_gate": [
            {"label": v["aria"] or v["text"], "disabled": v["disabled"],
             "cls": v["cls"][:50], "w": v["rect"]["w"], "h": v["rect"]["h"]}
            for v in w.gate_verbs],
        "escaped_by_continue_later": w.gate_escaped,
    }
    data["console_errors"] = [e for e in w.console if not _ignorable_console(e)][:30]
    ctx.close()
    return data


SURFACE_QUERIES: list[str] = []


def main() -> int:
    home = os.environ.get("HOME", "")
    assert home and home != str(Path.home().parent / "karol") and "/karol" not in home, (
        f"refusing to run against the owner's HOME ({home}); "
        "run with HOME=$(mktemp -d)")
    SHOTS_DIR.mkdir(parents=True, exist_ok=True)

    queries = os.environ.get("IW_SURFACES")
    global SURFACE_QUERIES
    # The labels the catalog actually carries (verified against
    # web/src/desk/applications.ts and web/src/desk/tools.ts).
    SURFACE_QUERIES = (queries.split(",") if queries else [
        "Intelligence", "Speak", "Meetings", "Agents", "Settings",
        "Change places", "Rhythm", "Context", "Workbenches", "Activity",
        "Desk memory", "Processes", "Commands", "Models", "Ask AI",
    ])

    hub = Hub(_free_port(), TOKEN, home).start()
    RESULT["seed"] = seed_extra(hub)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(args=[
                "--use-fake-device-for-media-stream",
                "--use-fake-ui-for-media-stream",
            ])
            for (wd, ht) in VIEWPORTS:
                RESULT["viewports"].append(run_viewport(browser, hub, wd, ht))
            RESULT["reduced_motion_pass"] = run_viewport(
                browser, hub, 1440, 900, reduced=True)
            browser.close()
    finally:
        hub.stop()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_name = os.environ.get("IW_OUT", "interaction.json")
    (OUT_DIR / out_name).write_text(
        json.dumps(RESULT, indent=2, default=str))
    print(f"\nWROTE {OUT_DIR / out_name}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
