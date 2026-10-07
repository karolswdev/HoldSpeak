"""Conductor R7: the BUILT Settings › People face beside its ratified board K7a.

The canvas method (board.py's runner and fences, unchanged) against the PRODUCT as built
(CANVAS_MODE=today: no seat, no shim), on a real hub with an isolated HOME (removed at the end).

Boards, at 1440 and 393:
  K7a-built-setting  the strip as the hub reads it (SOURCE · SETTING: the hub saved its default)
  K7a-built-off      after a press on OFF: AGENTS · OFF and the operation's receipt
  K7a-built-env      a second hub started with HOLDSPEAK_MCP_PEOPLE_ACCESS=off: the strip disabled,
                     SOURCE · HOLDSPEAK_MCP_PEOPLE_ACCESS
  K7a-built-read-failed  the read fails (Astra on #919): READ FAILED · <code> and Retry. Stand-in: the
                     browser answers the one GET /api/settings/people-access with 503 (page.route);
                     every other request reaches the real hub. Retry is pressed after the route is
                     lifted, and the strip returns.

Usage (from the worktree root):
  PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \\
    .venv/bin/python docs/internal/conductor-canvas/harness/shoot_built_k7.py
Shots: docs/internal/conductor-canvas/shots/K7a-built-*.png; facts: shots/K7-built-facts.json.
"""
from __future__ import annotations

import json
import os
import sys

sys.dont_write_bytecode = True
from pathlib import Path

os.environ.setdefault("NO_WARMUP", "1")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import board  # noqa: E402
import rig  # noqa: E402

ENV_VAR = "HOLDSPEAK_MCP_PEOPLE_ACCESS"
FRONT = "Settings · People"
OWN44 = r"""() => [...document.querySelectorAll('[data-testid=people-access] button')]
  .map((t) => (t.getAttribute('aria-label') || t.innerText || '').toString().trim().replace(/\s+/g, ' ').slice(0, 32))"""


class TodayStack(rig.Stack):
    """The product as built: no seat, no shim."""

    def __init__(self, mode: str = "today", shims: str = "k"):
        super().__init__("today", shims)


rig.Stack = TodayStack
LEG = {"env": False}


def _read(r: board.Runner) -> dict:
    return r.ev("""() => ({
      tokens: [...document.querySelectorAll('[data-testid=people-access] [aria-pressed]')]
        .map((b) => [b.innerText.trim(), b.getAttribute('aria-pressed'), b.disabled]),
      menu: (document.querySelector('[data-testid=people-access] [data-testid=surface-strip-menu]') || {}).disabled ?? null,
      agents: (document.querySelector('[data-testid=people-access-agents]') || {}).innerText || null,
      source: (document.querySelector('[data-testid=people-access-source]') || {}).innerText || null,
      receipt: (document.querySelector('[data-testid=people-access-receipt]') || {}).innerText || null,
    })""")


def _all_disabled(f: dict) -> bool:
    return (bool(f["tokens"]) and all(t[2] for t in f["tokens"])) or f["menu"] is True


def boards(r: board.Runner) -> None:
    r.scope44 = OWN44
    r.ev("() => window.__cOpen.surface('configure-settings', 'people')")
    r.settle(3500)
    if LEG["env"]:
        f = _read(r)
        r.shoot("K7a-built-env", FRONT, whole=["[data-testid=people-access]", "[data-testid=people-access-source]"],
                checks={"the strip is disabled": _all_disabled(f),
                        "SOURCE · HOLDSPEAK_MCP_PEOPLE_ACCESS": f["source"] == f"SOURCE · {ENV_VAR}",
                        "AGENTS · OFF": f["agents"] == "AGENTS · OFF"}, extra={"read": f})
        return
    f = _read(r)
    r.shoot("K7a-built-setting", FRONT, whole=["[data-testid=people-access]", "[data-testid=people-access-agents]"],
            checks={"WRITE pressed, enabled": any(t[0] == "WRITE" and t[1] == "true" and not t[2] for t in f["tokens"]) or f["menu"] is False,
                    "SOURCE · SETTING": f["source"] == "SOURCE · SETTING",
                    "AGENTS · READ": f["agents"] == "AGENTS · READ"}, extra={"read": f})
    off = r.page.locator("[data-testid=people-access] button", has_text="OFF")
    if off.count():
        r.tap(off.first, 1500)
    else:  # the phone fold: the one menu Button, then its OFF row
        r.tap(r.page.locator("[data-testid=people-access] [data-testid=surface-strip-menu]"), 700)
        r.tap(r.page.locator("[role=menu] [role^=menuitem]", has_text="OFF").first, 1500)
    f = _read(r)
    r.shoot("K7a-built-off", FRONT, whole=["[data-testid=people-access-agents]", "[data-testid=people-access-receipt]"],
            checks={"AGENTS · OFF": f["agents"] == "AGENTS · OFF",
                    "the receipt: SUCCEEDED · ACCESS · OFF": bool(f["receipt"]) and "SUCCEEDED" in f["receipt"] and "ACCESS · OFF" in f["receipt"]},
            extra={"read": f})
    # ── the read failure: the stand-in answers the GET with 503 ──
    url = "**/api/settings/people-access"
    r.page.route(url, lambda route: route.fulfill(status=503, content_type="application/json",
                                                  body='{"code": "unavailable"}')
                 if route.request.method == "GET" else route.continue_())
    r.ev("() => window.__cOpen.closeAll()")
    r.settle(800)
    r.ev("() => window.__cOpen.surface('configure-settings', 'people')")
    r.settle(3500)
    failed = r.ev("() => (document.querySelector('[data-testid=people-access-read-failed]') || {}).innerText || null")
    r.shoot("K7a-built-read-failed", FRONT, whole=["[data-testid=people-access-read-failed]"],
            checks={"READ FAILED · UNAVAILABLE and Retry": bool(failed) and "READ FAILED" in failed and "UNAVAILABLE" in failed and "Retry" in failed,
                    "no strip while the read fails": r.ev("() => !document.querySelector('[data-testid=people-access]')")},
            extra={"failed": failed, "stand_in": "GET /api/settings/people-access answered 503 by page.route"})
    r.page.unroute(url)
    # The stand-in's own 503 is the board's input, not a page fault: recorded, then cleared.
    own = [e for e in r.errors if "status of 503" in e]
    r.facts[f"K7a-built-read-failed-{r.width}"]["stand_in_console"] = own
    r.errors[:] = [e for e in r.errors if e not in own]
    r.tap(r.page.locator("[data-testid=people-access-read-failed] button", has_text="Retry"), 1500)
    back = _read(r)
    r.facts[f"K7a-built-read-failed-retry-{r.width}"] = {"read": back, "strip_back": bool(back["tokens"]) or back["menu"] is not None}
    if not (bool(back["tokens"]) or back["menu"] is not None):
        r.fails.append(f"K7a-built-read-failed-{r.width}: Retry did not bring the strip back")


def main() -> int:
    widths = [w for w in board.B.ALL_WIDTHS if not os.environ.get("ONLY_WIDTH") or str(w[0]) == os.environ["ONLY_WIDTH"]]
    facts: dict = {}
    fails: list[str] = []
    for env in (False, True):
        LEG["env"] = env
        saved = os.environ.get(ENV_VAR)
        if env:
            os.environ[ENV_VAR] = "off"  # the hub inherits it (rig.Stack's env)
        try:
            for width, height in widths:
                r = board.Runner(board.SHOTS, "K", width, height, "k", None)
                r.first_run = None
                r.run(boards)
                fails += r.fails
                facts.update(r.facts)
        finally:
            if saved is None:
                os.environ.pop(ENV_VAR, None)
            else:
                os.environ[ENV_VAR] = saved
    facts["_fails"] = fails
    (board.SHOTS / "K7-built-facts.json").write_text(json.dumps(facts, indent=1, ensure_ascii=False))
    print("\nFAILS:" if fails else "\nALL FENCES HELD", *fails, sep="\n  ")
    return 2 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
