"""HS-100-02 — three core flows traced end-to-end on the staged spike
build, friction counted honestly: every click, every window, every
concept the UI demands, every dead end. Output: numbered screenshots +
a steps JSON into the phase assets dir."""

from __future__ import annotations

import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://192.168.1.36:8791"
TOKEN = "Z3084LIRjQLOX8MQ7aB5j-njmsRakhoo"
ASSETS = Path(
    "/Users/karol/dev/tools/HoldSpeak/pm/roadmap/holdspeak/"
    "phase-100-the-application-layer/assets/hs-100-02-traces"
)
ASSETS.mkdir(parents=True, exist_ok=True)


class Trace:
    def __init__(self, name: str):
        self.name = name
        self.steps: list[dict] = []
        self.clicks = 0

    def snap(self, page, label: str, *, dead_end: str | None = None):
        n = len(self.steps) + 1
        shot = f"{self.name}-{n:02d}.png"
        page.screenshot(path=str(ASSETS / shot))
        windows = page.locator(".desk-window-shell").count()
        pullouts = page.locator(".desk-pullout").count()
        self.steps.append(
            {
                "n": n,
                "label": label,
                "clicks_so_far": self.clicks,
                "windows_open": windows,
                "pullouts_open": pullouts,
                "dead_end": dead_end,
                "shot": shot,
            }
        )
        print(f"  [{self.name} {n:02d}] {label} "
              f"(clicks={self.clicks} windows={windows} pullouts={pullouts})"
              + (f" DEAD END: {dead_end}" if dead_end else ""))

    def click(self, page, selector_or_xy, label: str):
        self.clicks += 1
        if isinstance(selector_or_xy, tuple):
            page.mouse.click(*selector_or_xy)
        else:
            page.click(selector_or_xy, timeout=8000)
        page.wait_for_timeout(500)


def arrive(page):
    page.goto(BASE + "/?token=" + TOKEN, wait_until="networkidle")
    page.wait_for_selector(".desk-next", timeout=15000)
    page.wait_for_selector(".desk-world, .desk-listmode, .desk-empty",
                           timeout=15000)
    page.wait_for_timeout(1500)


def flow_meeting(p) -> Trace:
    """Flow A (Job 2): 'I just had a meeting' -> 'the actions are filed'."""
    t = Trace("flow-a-meeting")
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    arrive(page)
    t.snap(page, "arrive at the desk")
    t.click(page, ".desk-mark", "open the HoldSpeak room menu")
    t.snap(page, "room menu open")
    t.click(page, "[role=menuitem]:has-text('Meetings')", "choose Meetings")
    page.wait_for_selector("[aria-label='Meetings'].desk-surface-window",
                           timeout=10000)
    page.wait_for_timeout(1500)
    t.snap(page, "Meetings window open (HistoryCore)")
    t.click(page, ".desk-surface-window >> text=Release sync (trace seed)",
            "open the imported meeting")
    page.wait_for_timeout(1500)
    body = page.locator("[aria-label='Meetings'].desk-surface-window").inner_text()
    intel_note = None
    for needle in ("disabled", "Disabled", "No artifacts", "no artifacts"):
        if needle in body:
            idx = body.index(needle)
            intel_note = body[max(0, idx - 80): idx + 120].replace("\n", " / ")
            break
    t.snap(page, "meeting detail — looking for actions/artifacts",
           dead_end=intel_note and f"intel status in body: …{intel_note}…")
    # Where does the UI send you to fix it? Record whatever affordance exists.
    fix = page.locator(".desk-surface-window :text-matches('Settings|Enable', 'i')")
    t.steps.append({
        "n": len(t.steps) + 1,
        "label": "affordances pointing at a fix",
        "fix_affordances": fix.count(),
        "clicks_so_far": t.clicks,
    })
    print(f"  [flow-a] fix affordances visible: {fix.count()}")
    browser.close()
    return t


def flow_dictation(p) -> Trace:
    """Flow B (Job 1): speak -> text lands -> teach a correction."""
    t = Trace("flow-b-dictation")
    # FINDING (recorded in the judgment): on the plain-HTTP LAN origin the
    # owner actually uses, navigator.mediaDevices is undefined and every
    # MicButton silently returns null — the voice product loses its mic
    # with no explanation. The flag below restores it for the trace.
    browser = p.chromium.launch(args=[
        "--use-fake-ui-for-media-stream",
        "--use-fake-device-for-media-stream",
        "--use-file-for-fake-audio-capture=/tmp/hs_dictate.wav",
        f"--unsafely-treat-insecure-origin-as-secure={BASE}",
    ])
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.context.grant_permissions(["microphone"])
    # localhost is a secure context; the LAN origin is not (the finding
    # above stands — traced here so the voice path itself can be measured).
    page.goto("http://localhost:8791/?token=" + TOKEN,
              wait_until="networkidle")
    page.wait_for_selector(".desk-next", timeout=15000)
    page.wait_for_selector(".desk-world, .desk-listmode, .desk-empty",
                           timeout=15000)
    page.wait_for_timeout(1500)
    t.snap(page, "arrive at the desk")
    t.click(page, ".desk-start-action:has-text('Dictate')",
            "the Dictate daily start")
    page.wait_for_selector(".desk-surface-window", timeout=10000)
    page.wait_for_timeout(1200)
    t.snap(page, "Dictation window open")
    t.click(page, ".desk-surface-window button:has-text('Try it')",
            "open the try-it dry run")
    mic = page.locator(".desk-surface-window .desk-mic").first
    mic.wait_for(timeout=10000)
    box = mic.bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.wait_for_timeout(3500)
    page.mouse.up()
    t.clicks += 1  # the hold counts as one interaction
    deadline = time.time() + 30
    text = ""
    while time.time() < deadline:
        text = page.locator(".desk-surface-window textarea").first.input_value()
        if text.strip():
            break
        page.wait_for_timeout(500)
    t.snap(page, f"real Whisper transcript landed: {text!r}")
    assert text.strip(), "transcription never landed"
    # Run it so a result (and the correction disclosure) exists.
    run = page.locator(
        ".desk-surface-window button:has-text('Run dry test')").first
    if run.count():
        t.click(page, ".desk-surface-window button:has-text('Run dry test')",
                "run the dry-run pipeline")
        page.wait_for_timeout(4000)
    t.snap(page, "dry-run result with Right/Wrong verdict pair")
    t.click(page, ".desk-surface-window button:has-text('Wrong')",
            "mark the result Wrong")
    page.wait_for_timeout(800)
    correct = page.locator(".desk-surface-window >> text=Correct this result")
    if correct.count():
        t.snap(page, "correction ritual open in place")
    else:
        t.snap(page, "after Wrong — no correction ritual",
               dead_end="Wrong did not open the correction ritual")
    browser.close()
    return t


def flow_keep_ask(p) -> Trace:
    """Flow C (Job 4): tap a kept note -> pull-out -> lasso -> ask."""
    t = Trace("flow-c-keep-ask")
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    arrive(page)
    t.snap(page, "arrive at the seeded desk")
    objs = page.evaluate("() => window.__hsWorldProbe()")
    assert objs, "no objects on the seeded desk"
    target = None
    for o in objs:
        hit = page.evaluate(
            """(o) => {
              const el = document.elementFromPoint(o.x, o.y);
              return el && (el.classList.contains('desk-world-canvas') ||
                            el.classList.contains('desk-vignette'));
            }""",
            o,
        )
        if hit:
            target = o
            break
    assert target, "no tappable object clear of furniture"
    t.click(page, (target["x"], target["y"]), f"tap {target['ref']}")
    page.wait_for_selector(".desk-pullout", timeout=5000)
    t.snap(page, "pull-out open — the kept object is readable")
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)
    # Lasso around the object to rope a selection.
    page.mouse.move(target["x"] - 160, target["y"] - 160)
    page.mouse.down()
    page.mouse.move(target["x"] + 160, target["y"] + 160, steps=8)
    page.mouse.up()
    t.clicks += 1
    page.wait_for_timeout(600)
    roped = page.locator(".desk-askbar").count()
    t.snap(page, f"lasso roped a selection (askbar={roped})",
           dead_end=None if roped else "lasso produced no ask affordance")
    if roped:
        t.click(page, ".desk-askbar button:has-text('Ask AI')",
                "open the Ask panel from the rope")
        page.wait_for_selector(".desk-pullout textarea, textarea",
                               timeout=5000)
        t.snap(page, "Ask panel open with the roped grounding")
        page.locator("textarea").last.fill(
            "What did I decide about the release?")
        t.click(page, ".desk-pullout-foot button:text-is('Ask')",
                "submit the ask")
        page.wait_for_timeout(12000)
        t.snap(page, "the honest response (or refusal) printed")
    browser.close()
    return t


def main():
    import sys
    only = sys.argv[1] if len(sys.argv) > 1 else None
    flows = [f for f in (flow_meeting, flow_dictation, flow_keep_ask)
             if not only or only in f.__name__]
    traces = []
    with sync_playwright() as p:
        for flow in flows:
            try:
                traces.append(flow(p))
            except Exception as exc:  # record the failure as a finding
                print(f"  !! {flow.__name__} aborted: {exc}")
                traces.append({"flow": flow.__name__, "aborted": str(exc)})
    out = []
    for tr in traces:
        if isinstance(tr, Trace):
            out.append({"flow": tr.name, "clicks": tr.clicks,
                        "steps": tr.steps})
        else:
            out.append(tr)
    if only and (ASSETS / "traces.json").exists():
        prior = json.loads((ASSETS / "traces.json").read_text())
        names = {row.get("flow") for row in out}
        out = [row for row in prior
               if row.get("flow") not in names
               and row.get("flow", "").replace("_", "-") not in
               {n.replace("_", "-") for n in names}] + out
    (ASSETS / "traces.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(
        [{k: v for k, v in row.items() if k != "steps"} for row in out],
        indent=2))


if __name__ == "__main__":
    main()
