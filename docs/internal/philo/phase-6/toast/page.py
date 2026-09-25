"""Build the self-contained PHILO-6-03 placement review page.

The PNG board captures are produced by the real-species Vite canvas and then inlined
so the owner can review every board without a running server or network fetch.
"""
from base64 import b64encode
from pathlib import Path


ROOT = Path(__file__).parent
SHOTS = ROOT / "shots"
BOARDS = ("today", "proposed", "summary-open", "capture", "meetings", "floor")


def image_data(name: str) -> str:
    return b64encode((SHOTS / name).read_bytes()).decode("ascii")


HEAD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PHILO-6-03 · Toast placement canvas</title>
<style>
:root { color-scheme: dark; --bg:#0e0f13; --surface:#15171d; --border:#2a2e3e; --text:#f2f3f5; --muted:#9ba2b0; --mono:"JetBrains Mono","SFMono-Regular",Consolas,monospace; }
* { box-sizing:border-box; }
body { margin:0; padding:24px 16px 48px; background:var(--bg); color:var(--text); font-family:var(--mono); }
h1 { margin:0 0 12px; font-size:14px; letter-spacing:.08em; color:var(--muted); }
.status { margin:0 0 24px; max-width:100ch; font-size:12px; line-height:1.5; color:var(--muted); }
.board { margin:0 0 28px; }
.board h2 { margin:0 0 10px; font-size:13px; letter-spacing:.06em; }
.pair { display:grid; grid-template-columns:minmax(0,3fr) minmax(0,1fr); gap:16px; align-items:start; }
figure { margin:0; padding:10px; background:var(--surface); border:1px solid var(--border); min-width:0; }
figcaption { margin:0 0 8px; font-size:12px; color:var(--muted); }
img { display:block; width:100%; height:auto; }
.facts { margin-top:24px; padding-top:16px; border-top:1px solid var(--border); }
.facts h2 { margin:0 0 8px; font-size:12px; letter-spacing:.06em; }
.facts p { margin:6px 0; max-width:100ch; font-size:12px; line-height:1.5; color:var(--muted); }
@media (max-width:720px) { .pair { grid-template-columns:minmax(0,1fr); } }
</style></head><body>
<h1>PHILO-6-03 · CANVAS ONLY · PROPOSED · OWNER RATIFICATION PENDING</h1>
<p class="status">The today board preserves the current fixed aftercare defect as a comparison. The proposed, summary-open, and capture boards show the existing card in a normal-flow slot immediately before the existing capture bar. The meetings board shows a real Meetings window open: its flow slot is inside the active window body below the production titlebar and before the Meetings content. The floor board shows the card in the Floor shell above the production DeskListView work area. The card keeps its existing words, species and two verbs. At 393 the production capture bar is sticky: a flow card can pass under it at an intermediate scroll, so the phone no-overlap figures hold at the measured scroll or end-of-scroll clearance. The capture board is distinct because its bar shows the existing pressed-mic visual as a canvas-only fixture with no microphone or backend call.</p>
__BOARDS__
<section class="facts">
<h2>GEOMETRY AND FENCE</h2>
<p>The canvas fence measures the card, Arrival sections, complete summary well, readable summary text and capture bar at 1440 × 900 and 393 × 852. It asserts no card intersection with those regions on every flow board at the recorded scroll, no horizontal overflow and exactly two card Button verbs. Browser errors are recorded in shots/browser-errors.json.</p>
<h2>OWNER ASKS</h2>
<p>1. Ratify the Arrival slot before CaptureBar, plus top-of-current-surface flow slots off Arrival: inside an active Meetings window body below its titlebar and before content; in Floor above the work area.</p>
<p>2. Ratify auto-scroll to the measured Arrival phone slot. This MOVES the owner's reading position and scrolls the Arrival head off the phone. At another scroll position the sticky CaptureBar can cover the flow card.</p>
<h2>PROVENANCE</h2>
<p>Canvas source: canvas/harness/main.tsx and main.css. It imports the production DeskChrome, Dock, RuntimeBusProvider, Chair, DeskWindowFrame, DeskListView, SurfaceSection, SurfaceRows, SurfaceRow, SurfaceLedger, SurfaceLedgerRow, MeetingSummarySlab, Button, MicButton and BriefEgress, plus production web/src CSS. The Floor board seeds three local fixture primitives for the production Floor list species; it makes no hub request or write. The capture board pressed-mic visual uses the production listening sprite and Button styling only; it does not invoke microphone capture or a backend. The harness follows the Phase 4 methods in pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-01-canvas/ and story-04-canvas/. The retained phase-5 defect was inspected at pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/final/20260925T001407Z-his-words-real/shots/summary/393-after.png.</p>
<p>Review artifact only. No product placement file or ChairHome.tsx was edited. The seam proposal is in chairhome.patch and is explicitly not applied. Zero-count implementation and focused proof are in zero/.</p>
</section>
</body></html>
"""


board_markup = []
for board in BOARDS:
    board_markup.append(
        f'<section class="board"><h2>{board.upper()}</h2><div class="pair">'
        f'<figure><figcaption>1440 × 900 · real shell</figcaption>'
        f'<img alt="{board} board at 1440" src="data:image/png;base64,{image_data(board + "-1440.png")}"></figure>'
        f'<figure><figcaption>393 × 852 · real shell</figcaption>'
        f'<img alt="{board} board at 393" src="data:image/png;base64,{image_data(board + "-393.png")}"></figure>'
        "</div></section>"
    )

(ROOT / "toast-placement.html").write_text(HEAD.replace("__BOARDS__", "\n".join(board_markup)))
print(ROOT / "toast-placement.html")
