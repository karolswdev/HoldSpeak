"""Conductor F2: the BUILT faces on the real glass, each beside its ratified board.

The canvas method (shoot.py) with no seat and no shim: vite serves the product as on this branch
(rig.Stack mode `today`) against a real hub on a scratch HOME (`/tmp/kcanvas-*`, removed at the end).
seed_db.py writes the canvas seed; seed_f2.py then writes what K2 and K4 write (the launch ledger
with `origin_ref`, the Work attempts bound to the sessions, PR #412 open) and gives each session a
`cat` pane on a tmux server of its own (TMUX_TMPDIR under /tmp/kcanvas-tmux-*, killed at the end).
The K6 step runs `seed_f2.py merge` (PR #413 merged, the follow-through closed, the action item
completed through FollowThroughService). Chromium gets a fake microphone, so the Speak answer mic
records for real.

The fences are board.py's (C1's JS_LIB, CONTRAST_ALL, CLIP, OVERLAP, TARGETS44 and C5's laws),
unchanged. Shots and facts go to .tmp/evidence-shots/conductor-f2/ (never into the tree).

Usage (from the worktree root):
  PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \\
    .venv/bin/python docs/internal/conductor-canvas/harness/shoot_built.py
ONLY_WIDTH=393 limits the run. Exit 2 on a failed fence.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import board  # noqa: E402
import rig  # noqa: E402

B = board.B
REPO = HERE.parents[3]
OUT = REPO / ".tmp/evidence-shots/conductor-f2"
RUNBOOK = "Write the rollback runbook"
RECON = "Shard the reconciliation job"
FLAG = "Add the ledger freeze flag"
ROOM = "surface-project-memory"

# The board each built shot answers to (docs/internal/conductor-canvas/shots/<board>-<w>.png).
BOARDS = {
    "K4a-door-row-in-flight": "K4a-door-row-in-flight",
    "K4b-room-in-flight": "K4b-room-in-flight",
    "K4c-agents-session-pin": "K4c-agents-session-pin",
    "K5a-needs-you-coder-row": "K5a-needs-you-coder-row",
    "K5b-speak-answer-recording": "K5b-speak-answer-recording",
    "K5c-enter-sends": "K5c-enter-sends",
    "K6-follow-through-receipt": "K6-follow-through-receipt",
}

# This lane's own targets at 393: the fence fails on these; any other small target is main's.
OWN44 = r"""() => [...document.querySelectorAll(
  '[data-testid=flight-session], [data-testid=flight-open-pr], [data-testid=arrival-coder-row] button, '
  + '[data-testid=arrival-agents] button, [data-testid=session-answer-well] button, [data-testid=session-answer-well] textarea')]
  .map((t) => (t.getAttribute('aria-label') || t.innerText || t.getAttribute('placeholder') || t.className || '').toString().trim().replace(/\s+/g, ' ').slice(0, 32))"""


class BuiltStack(rig.Stack):
    """rig.Stack in mode `today` (no seat, no shim), plus seed_f2.py and a tmux server of its own."""

    def __init__(self, mode: str = "today", shims: str = "k"):
        super().__init__("today", shims)

    def __enter__(self):
        self.tmux = tempfile.mkdtemp(prefix="kcanvas-tmux-", dir="/tmp")
        os.environ["TMUX_TMPDIR"] = self.tmux       # the hub's steering reads this socket too
        super().__enter__()
        out = self.f2("seed")
        self.seed["f2"] = out
        return self

    def f2(self, *argv: str) -> dict:
        env = {**os.environ, "HOME": self.home, "PYTHONPATH": str(REPO), "TMUX_TMPDIR": self.tmux}
        done = subprocess.run([rig.PY, str(HERE / "seed_f2.py"), *argv], cwd=REPO, env=env,
                              capture_output=True, text=True, timeout=120)
        if done.returncode:
            raise RuntimeError(f"seed_f2 {argv} failed: {done.stderr[-2000:]}")
        return json.loads(done.stdout.strip().splitlines()[-1])

    def __exit__(self, *exc):
        try:
            subprocess.run(["tmux", "kill-server"], env={**os.environ, "TMUX_TMPDIR": self.tmux},
                           capture_output=True, timeout=10)
        finally:
            shutil.rmtree(self.tmux, ignore_errors=True)
            os.environ.pop("TMUX_TMPDIR", None)
        return super().__exit__(*exc)


STACK: list[BuiltStack] = []


def _stack(mode: str = "today", shims: str = "k") -> BuiltStack:
    st = BuiltStack(mode, shims)
    STACK.append(st)
    return st


rig.Stack = _stack  # board.Runner.run builds its stack through rig.Stack


class _FakeMicLaunch:
    """Chromium with a fake microphone (the rig grants it): the Speak answer mic records for real."""

    def __init__(self, cm):
        self._cm = cm

    def __enter__(self):
        pw = self._cm.__enter__()
        real = pw.chromium.launch

        def launch(**kw):
            kw.setdefault("args", [])
            kw["args"] += ["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"]
            return real(**kw)

        pw.chromium.launch = launch
        return pw

    def __exit__(self, *exc):
        return self._cm.__exit__(*exc)


_real_sp = board.sync_playwright
board.sync_playwright = lambda: _FakeMicLaunch(_real_sp())


def show_all(r) -> None:
    more = r.page.locator("[data-testid=arrival-needs-you] button:has-text('Show all')").first
    if more.count():
        r.tap(more, 900)


def boards(r: board.Runner) -> None:
    ev, settle, page = r.ev, r.settle, r.page
    r.scope44 = OWN44
    r.page.context.grant_permissions(["microphone"])
    st = STACK[-1]

    # ── K4a the Door row in flight ──
    show_all(r)
    row = page.locator(f"[data-testid=arrival-needs-you-row]:has-text('{RUNBOOK}')").first
    row.scroll_into_view_if_needed()
    settle(800)
    chip = row.locator("[data-testid=flight-chip]")
    r.shoot("K4a-door-row-in-flight", "Needs you", whole=[f"[aria-label='Open session: {RUNBOOK}']"],
            checks={"the Door row wears CLAUDE CODE · WAITING": chip.count() == 1 and "CLAUDE CODE · WAITING" in chip.inner_text()})

    # ── K4b the Room in flight ──
    ev("() => window.__cOpen.room('p-ledger')")
    settle(3500)
    ev("(w) => window.__cOpen.focus(w)", ROOM)
    settle(600)
    page.locator(f"[id='{ROOM}'] [data-testid=needs-you-row]").first.scroll_into_view_if_needed()
    settle(400)
    chips = ev(f"() => [...document.querySelectorAll(\"[id='{ROOM}'] [data-testid=flight-chip]\")].map((c) => c.innerText.trim())")
    r.shoot("K4b-room-in-flight", "Payments ledger cutover",
            whole=[f"[id='{ROOM}'] [aria-label='Open PR #412: {FLAG}']"],
            checks={"the Room shows WAITING, WORKING and PR #412 OPEN":
                    all(any(w in c for c in chips) for w in ["CLAUDE CODE · WAITING", "CODEX · WORKING", "PR #412 · OPEN"]),
                    "the PR row names its egress": "GITHUB.COM" in ev(f"() => document.getElementById('{ROOM}').innerText")},
            extra={"chips": chips})
    r.close_all()

    # ── K4c the AGENTS section names each session's item ──
    ev("() => import('/src/desk/chair/chairWindows.ts').then((m) => m.openChairWindow('chair:week'))")
    settle(1500)
    agents = page.locator("[data-testid=arrival-agents]").first
    agents.scroll_into_view_if_needed()
    settle(500)
    origin = ev("() => [...document.querySelectorAll('[data-testid=arrival-agent-origin]')].map((c) => c.innerText.trim())")
    r.shoot("K4c-agents-session-pin", "The week", whole=["[data-testid=arrival-agents] [data-testid=arrival-agent-origin]"],
            checks={"two live sessions, each names its item": len(origin) == 2}, extra={"origins": origin})

    # ── K5a the Needs you coder row ──
    ev("() => import('/src/desk/chair/chairWindows.ts').then((m) => m.openChairWindow('chair:needs'))")
    settle(1200)
    coder = page.locator("[data-testid=arrival-coder-row]").first
    coder.scroll_into_view_if_needed()
    settle(500)
    head = ev("() => (document.querySelector('[data-testid=arrival-display]') || {}).innerText || ''")
    first_primary = ev("() => { const b = document.querySelector('[data-testid=arrival-needs-you-ledger] .btn--primary, [data-testid=arrival-needs-you-ledger] [data-variant=primary]'); return b ? (b.getAttribute('aria-label') || b.innerText) : null; }")
    r.shoot("K5a-needs-you-coder-row", "Needs you",
            whole=["[data-testid=arrival-coder-question]", "[data-testid=arrival-speak-answer]", "[data-testid=arrival-coder-row] [data-testid=arrival-project]"],
            checks={"the coder row reads CLAUDE CODE · WAITING": "CLAUDE CODE · WAITING" in coder.inner_text()},
            extra={"headline": head, "first_primary": first_primary})

    # Control: MAIN's session window for the same session (Open, no answer well), measured, not a
    # board: what its footer does with a live pane and the YOLO posture is main's, not this lane's.
    r.tap(page.locator("[data-testid=arrival-coder-open]").first, 3000)
    page.screenshot(path=str(OUT / f"_control-main-session-window-{r.width}.png"))
    control = {"clip": ev(B.CLIP), "overlap": ev(B.OVERLAP)}
    r.facts[f"_control_main_session_window_{r.width}"] = control
    inherit_clip = {"strips": [x["cls"] for x in control["clip"]["strips"]], "clipped": [x["text"] for x in control["clip"]["clipped"]]}
    inherit_overlap = sorted({str(h.get("a")) for h in control["overlap"]["hits"]})
    ev("() => import('/src/desk/steering.ts').then((m) => m.useSteering.getState().closeSession())")
    settle(800)
    coder.scroll_into_view_if_needed()
    settle(400)

    # ── K5b Speak answer: the session window, the answer well, the mic recording ──
    r.tap(page.locator("[data-testid=arrival-speak-answer]").first, 3000)
    page.locator(".desk-session-question").first.scroll_into_view_if_needed()
    settle(800)
    listening = ev("() => !!document.querySelector('[data-testid=session-answer-well] .desk-mic.is-listening')")
    mic_state = ev("() => (document.querySelector('[data-testid=session-answer-well] .desk-mic') || {}).className || null")
    r.shoot("K5b-speak-answer-recording", "claude", inherit_clip=inherit_clip, inherit_overlap=inherit_overlap,
            whole=[".desk-session-question", "[data-testid=session-answer-well] .desk-mic", "[data-testid=session-answer-well] .desk-steer-input"],
            checks={"the steer mic is recording": listening, "the composer is drawn once": ev("() => document.querySelectorAll('.desk-steer-input').length") == 1},
            extra={"mic_class": mic_state})
    # Stop the recording (click-to-toggle) before typing: the field is the owner's.
    if listening:
        r.tap(page.locator("[data-testid=session-answer-well] .desk-mic").first, 1500)

    # ── K5c Enter sends ──
    inp = page.locator("[data-testid=session-answer-well] .desk-steer-input").first
    inp.fill("Jordan owns the rollback. Avery reviews it.")
    inp.press("Enter")
    settle(2500)
    page.locator("[data-testid=session-answer-well] .desk-steer-sent, [data-testid=session-answer-well] .desk-arm-refusal").first.scroll_into_view_if_needed()
    settle(500)
    sent = ev("() => (document.querySelector('[data-testid=session-answer-well] .desk-steer-sent') || {}).innerText || null")
    refused = ev("() => (document.querySelector('[data-testid=session-answer-well] .desk-arm-refusal') || {}).innerText || null")
    landed = subprocess.run(["tmux", "capture-pane", "-p", "-S", "-", "-t", "hs-runbook"], env={**os.environ, "TMUX_TMPDIR": st.tmux},
                            capture_output=True, text=True).stdout
    r.shoot("K5c-enter-sends", "claude", inherit_clip=inherit_clip, inherit_overlap=inherit_overlap, whole=["[data-testid=session-answer-well] .desk-steer-sent"],
            checks={"Enter sent the steer": bool(sent), "the composer is empty after the send": inp.input_value() == "",
                    "the text landed in the session's pane": "Jordan owns the rollback" in landed},
            extra={"sent": sent, "refused": refused, "pane": landed.strip()[-200:]})
    r.close_all()

    # ── K6 the merge: the commitment closes with the PR as evidence ──
    st.f2("merge")
    ev("() => window.__cOpen.room('p-ledger')")
    settle(4000)
    ev("(w) => window.__cOpen.focus(w)", ROOM)
    settle(800)
    rows = ev(f"() => [...document.querySelectorAll(\"[id='{ROOM}'] [data-testid=needs-you-row]\")].map((c) => c.innerText.replace(/\\s+/g, ' ').trim())")
    agents_after = ev("() => [...document.querySelectorAll('[data-testid=arrival-agent-row]')].map((c) => c.innerText.replace(/\\s+/g, ' ').trim())")
    r.shoot("K6-follow-through-receipt", "Payments ledger cutover", whole=["[data-testid=room-merge-receipt]"],
            checks={"the runbook left OPEN HERE": not any(RUNBOOK in x for x in rows),
                    "the receipt names the runbook and PR #413": "PR #413 MERGED" in (ev("() => (document.querySelector('[data-testid=room-merge-receipt]') || {}).innerText || ''") or "")},
            extra={"open_here": rows, "agents_after_merge": agents_after})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    widths = [w for w in B.ALL_WIDTHS if not os.environ.get("ONLY_WIDTH") or str(w[0]) == os.environ["ONLY_WIDTH"]]
    facts: dict = {}
    fails: list[str] = []
    for width, height in widths:
        rr = board.Runner(OUT, "K", width, height, "k", None)
        rr.first_run = None
        rr.run(boards)
        fails += rr.fails
        facts.update(rr.facts)
    facts["_fails"] = fails
    facts["_boards"] = {k: f"docs/internal/conductor-canvas/shots/{v}" for k, v in BOARDS.items()}
    (OUT / "facts.json").write_text(json.dumps(facts, indent=1, ensure_ascii=False))
    print("\nFAILS:" if fails else "\nALL FENCES HELD", *fails, sep="\n  ")
    return 2 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
