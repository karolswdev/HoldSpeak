"""The Conductor canvas, leg K7 (R7, DRAFT for the owner): Settings > People, People MCP access.

Owner, 2026-10-06: "the default should be on, for HOLDSPEAK_MCP_PEOPLE_ACCESS, and I guess there's
an affordance to set it somewhere, right?"

The same rig and fences as shoot.py (board.py: a REAL hub on an isolated HOME, the PRODUCT app
served by vite), with ONLY the Q7 seats (seats.mjs K7, CANVAS_SEATS=k7): the K boards' seats were
drawn on main 8f958800e and their faces are built since. The control reads and presses the REAL
route (GET / PUT /api/settings/people-access, Conductor R7).

Usage (from the worktree root):
  PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \\
    .venv/bin/python docs/internal/conductor-canvas/harness/shoot_k7.py
"""
from __future__ import annotations

import os
import sys
sys.dont_write_bytecode = True   # no __pycache__ in the tree
from pathlib import Path

os.environ["CANVAS_SEATS"] = "k7"
os.environ.setdefault("NO_WARMUP", "1")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import board  # noqa: E402

#: The Settings window's name when the People module is open (the product names it).
PEOPLE_WINDOW = "Settings · People"

OWN44 = r"""() => [...document.querySelectorAll('[data-testid=k-people-access] button, [data-testid=k-people-hub] button')]
  .map((t) => (t.getAttribute('aria-label') || t.innerText || '').toString().trim().replace(/\s+/g, ' ').slice(0, 32))"""


def boards(r: board.Runner) -> None:
    ev, settle, phone = r.ev, r.settle, r.phone
    r.scope44 = OWN44

    # ── K7a (R7, DRAFT): Settings > People: People MCP access, the real route ──
    ev("() => window.__cOpen.surface('configure-settings', 'people')")
    settle(3500)
    tokens = r.ev("() => [...document.querySelectorAll('[data-testid=k-people-access] [aria-pressed]')].map((b) => [b.innerText.trim(), b.getAttribute('aria-pressed')])")
    agents = r.ev("() => (document.querySelector('[data-testid=k-people-agents]') || {}).innerText || null")
    r.shoot("K7a-people-access", PEOPLE_WINDOW, whole=["[data-testid=k-people-access]", "[data-testid=k-people-agents]"],
            checks={"OFF / READ / WRITE, WRITE pressed (the default is on)":
                        [t[0] for t in tokens] == ["OFF", "READ", "WRITE"] and dict(tokens).get("WRITE") == "true"
                        or phone,  # 393 folds the strip to one menu Button (FilterTokens' own law)
                    "AGENTS · READ": agents == "AGENTS · READ"},
            extra={"tokens": tokens, "agents": agents})



def main() -> int:
    """board.main, writing this leg's own facts (shots/K7-facts.json): the ratified K boards'
    facts.json is history and is never rewritten by this leg."""
    import json

    widths = [w for w in board.B.ALL_WIDTHS if not os.environ.get("ONLY_WIDTH") or str(w[0]) == os.environ["ONLY_WIDTH"]]
    facts: dict = {}
    fails: list[str] = []
    for width, height in widths:
        r = board.Runner(board.SHOTS, "K", width, height, "k", None)
        r.first_run = None
        r.run(boards)
        fails += r.fails
        facts.update(r.facts)
    facts["_fails"] = fails
    (board.SHOTS / "K7-facts.json").write_text(json.dumps(facts, indent=1, ensure_ascii=False))
    print("\nFAILS:" if fails else "\nALL FENCES HELD", *fails, sep="\n  ")
    return 2 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
