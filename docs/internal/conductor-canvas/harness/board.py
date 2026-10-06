"""Conductor canvas: the board runner (one stack per width, the fences, the touch hands).

The fences are imported UNCHANGED from the ratified canvas harnesses (pm/roadmap is history:
read, never edited):
  - C1's (story-11-canvas/harness/shoot.py): JS_LIB, CONTRAST_ALL, CLIP, OVERLAP, TARGETS44;
  - C5's runner (story-15-canvas/harness/board.py): the hands, FRONT, BASIC, CONTENT, WHOLE,
    SUBMENU_ADJ and `Runner.shoot` (the laws per board).
Only three things differ here: the stack is this folder's rig (its own seed and seats), the
scratch-path fence names this run's HOME prefix (`kcanvas-`), and the run shoots the first-run
boards before the warm-up dismisses the first run.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import traceback
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.dont_write_bytecode = True   # never write __pycache__ into pm/roadmap (history, read-only)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rig  # noqa: E402  (registered as `rig` first, so the imported runner uses THIS rig)

REPO = HERE.parents[3]
P13 = REPO / "pm/roadmap/holdspeak-philo/phase-13-the-desk/assets"
_spec = importlib.util.spec_from_file_location("c5board", P13 / "story-15-canvas/harness/board.py")
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)
assert B.rig is rig, "the imported runner must use this folder's rig"
# This run's scratch HOME is /tmp/kcanvas-*: the scratch-path fence names it (and still names /tmp).
B.BASIC = B.BASIC.replace("p13c57-", "kcanvas-")

SHOTS = HERE.parent / "shots"


class Runner(B.Runner):
    """C5's runner; `first_run` shoots before the first run is dismissed."""

    first_run = None  # a callable (runner) -> None

    def shoot(self, board: str, front, inherit: list[str] | None = None, inherit_clip: dict | None = None,
              inherit_overlap: list[str] | None = None, **kw):
        """C5's shoot. `inherit` names texts whose low contrast is MAIN's (not this canvas's face):
        they are recorded as `inherited_low_contrast` and do not fail the board. Any other hit fails."""
        key = f"{board}-{self.width}"
        n = len(self.fails)
        f = super().shoot(board, front, **kw)
        if f is not None:
            # MAIN's Dock at 393: a Dock chip under the Dock's own `More` button (no canvas surface);
            # and any pair a board names in `inherit_overlap` (main's surfaces only).
            dock = [h for h in f["overlap"] if "More AppIcons" in (h.get("a"), h.get("b"))
                    or any(str(h.get("a", "")).startswith(p) for p in (inherit_overlap or []))]
            if dock:
                f["inherited_overlap"] = dock
                f["overlap"] = [h for h in f["overlap"] if h not in dock]
                if not f["overlap"]:
                    law = f"{key}: no rendered overlap"
                    self.fails[n:] = [x for x in self.fails[n:] if x != law]
        if f is not None and inherit_clip:
            # A strip or a clipped text that MAIN's own window shows the same (measured on a control).
            st = [x for x in f["clip"]["strips"] if x["cls"] in inherit_clip.get("strips", [])]
            cl = [x for x in f["clip"]["clipped"] if x["text"] in inherit_clip.get("clipped", [])]
            f["inherited_clip"] = {"strips": st, "clipped": cl}
            f["clip"]["strips"] = [x for x in f["clip"]["strips"] if x not in st]
            f["clip"]["clipped"] = [x for x in f["clip"]["clipped"] if x not in cl]
            for law, left in (("no sideways strip", f["clip"]["strips"]), ("no clipped text", f["clip"]["clipped"])):
                if not left:
                    self.fails[n:] = [x for x in self.fails[n:] if x != f"{key}: {law}"]
        if f is not None and inherit:
            inh = [h for h in f["low_contrast"] if h["text"] in inherit]
            f["inherited_low_contrast"] = inh
            if len(inh) == len(f["low_contrast"]):
                law = f"{key}: in-place contrast >= 4.5:1 (3:1 large)"
                self.fails[n:] = [x for x in self.fails[n:] if x != law]
        return f

    def shoot_bare(self, board: str, front, **kw):
        """A face with no desk window (the first run, the Floor list): the law is NO blue title
        bar, not exactly one. Every other law of `shoot` stands."""
        key = f"{board}-{self.width}"
        n = len(self.fails)
        f = self.shoot(board, front, **kw)
        if f is not None:
            law = f"{key}: exactly one blue title bar"
            self.fails[n:] = [x for x in self.fails[n:] if x != law]
            f["windowless"] = True
            if f["front_state"]["blue"]:
                self.fails.append(f"{key}: a windowless face shows a blue title bar")
        return f

    def run(self, boards) -> None:  # noqa: C901 (C5's run, plus the first-run leg)
        stack = None
        try:
            if self.state is None:
                stack = rig.Stack("proposal", self.shims).__enter__()
                self.url, self.seed, guard = stack.url, stack.seed, stack.guard
            else:
                self.url, self.seed, guard = self.state["url"], self.state["seed"], self.state.get("guard")
            self.facts[f"_seat_guard_{self.width}"] = guard
            self.shots.mkdir(parents=True, exist_ok=True)
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                ctx = browser.new_context(viewport={"width": self.width, "height": self.height}, device_scale_factor=2, has_touch=self.phone)

                def page():
                    pg = ctx.new_page()
                    pg.on("pageerror", lambda e: self.errors.append(f"pageerror: {e}"))
                    pg.on("console", lambda m: self.errors.append(f"console: {m.text[:200]}")
                          if m.type == "error" and "status of 4" not in m.text and "Failed to fetch" not in m.text else None)
                    return pg
                try:
                    # THE FIRST-RUN LEG: the first run shows on a fresh HOME only. Load it, let a cold
                    # vite settle (it may reload once), then mark the page and shoot.
                    self.page = page()
                    self.page.goto(self.url, wait_until="load")
                    fr = self.page.locator("[data-testid=firstrun]")
                    try:
                        fr.wait_for(timeout=180_000)
                        self.settle(20_000)
                        fr.wait_for(timeout=60_000)
                        self.ev("() => { window.__cBooted = true; }")
                        if self.first_run:
                            self.first_run(self)
                    except Exception as exc:  # a reused stack has no first run: record, go on
                        self.facts[f"_first_run_{self.width}"] = f"not shot: {str(exc).splitlines()[0][:160]}"
                    self.page.close()
                    # WARM-UP (C5's, no shot, no write): open every window once, then start clean.
                    if not os.environ.get("NO_WARMUP"):
                        self.page = page()
                        try:
                            self.boot()
                            for js in ["window.__cOpen.open('meeting:m-standup')", "window.__cOpen.open('decision:d-freeze')",
                                       "window.__cOpen.room('p-ledger')", "window.__cOpen.brief()",
                                       "window.__cOpen.surface('review-meetings')", "window.__cOpen.surface('open-people')"]:
                                self.ev("() => " + js)
                                self.settle(2500)
                        except Exception as exc:
                            print("warm-up:", str(exc).splitlines()[0][:200], flush=True)
                        self.settle(3000)
                        try:
                            self.close_all()
                        except Exception:
                            pass
                        self.page.close()
                    self.errors.clear()
                    self.page = page()
                    self.boot()
                    boards(self)
                except Exception as exc:
                    traceback.print_exc()
                    self.fails.append(f"CRASH at width {self.width}: {str(exc).splitlines()[0][:300]}")
                    try:
                        self.page.screenshot(path=str(self.shots / f"_crash-{self.width}.png"))
                    except Exception:
                        pass
                browser.close()
        finally:
            if stack is not None:
                stack.__exit__(None, None, None)
            self.facts[f"_browser_errors_{self.width}"] = self.errors
            if self.errors:
                self.fails.append(f"browser errors at {self.width}: {self.errors[:3]}")


def main(boards, first_run) -> int:
    state = json.loads(Path(os.environ["STACK_STATE"]).read_text()) if os.environ.get("STACK_STATE") else None
    widths = [w for w in B.ALL_WIDTHS if not os.environ.get("ONLY_WIDTH") or str(w[0]) == os.environ["ONLY_WIDTH"]]
    facts_path = SHOTS / "facts.json"
    facts: dict = json.loads(facts_path.read_text()) if (os.environ.get("ONLY") or os.environ.get("ONLY_WIDTH")) and facts_path.exists() else {}
    fails: list[str] = []
    for width, height in widths:
        r = Runner(SHOTS, "K", width, height, "k", state)
        r.first_run = first_run
        r.run(boards)
        fails += r.fails
        facts.update(r.facts)
    facts["_fails"] = fails
    facts_path.write_text(json.dumps(facts, indent=1, ensure_ascii=False))
    print("\nFAILS:" if fails else "\nALL FENCES HELD", *fails, sep="\n  ")
    return 2 if fails else 0
