"""Build the owner's review page: every board, both widths, both word sets,
the shots embedded as data URIs so the page is self-contained."""
import base64
import html
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHOTS = HERE.parent / "shots"
REPO = HERE.parents[6]
OUT = REPO / "docs/internal/philo/phase-7/grant-canvas/index.html"

BOARDS = [
    ("1-never", "1 · No grant ever", "No chip. The Allow verb beside Revoke."),
    ("2-live", "2 · Grant live", "Chip ALLOWED. The Stop verb. The receipt in the foot."),
    ("3-revoked", "3 · Grant stopped", "Chip STOPPED. The Allow verb. The receipt in the foot."),
    ("4-expired", "4 · Expired by clock, credential active", "Credential ● active, chip STOPPED: two independent columns."),
    ("5-orphan", "5 · Grant live, no credential (remote ON)", "The row stays: idle ●, NO CREDENTIAL, ALLOWED, the Stop verb only."),
    ("5b-orphan-off", "5b · Grant live, no credential (remote OFF)", "The ledger renders whatever the switch says."),
    ("5c-orphan-expired", "5c · No credential, grant past expiry", "Chip STOPPED from the time-aware rule; no verb."),
    ("6-refused", "6 · Refused", "The named refusal on its row: CAN'T STOP · NO GRANT; CAN'T ALLOW · OWNER ONLY."),
    ("7-empty", "7 · Last row gone", "No ledger. The foot receipt's ℹ opens the receipt well."),
]


def img(path: Path, alt: str) -> str:
    data = base64.b64encode(path.read_bytes()).decode()
    return f'<img src="data:image/png;base64,{data}" alt="{html.escape(alt)}" loading="lazy">'


def pair(prefix: Path, name: str, label: str) -> str:
    return (
        '<div class="pair">'
        f'<figure class="w1440">{img(prefix / f"{name}-1440.png", label + " at 1440")}<figcaption>1440</figcaption></figure>'
        f'<figure class="w393">{img(prefix / f"{name}-393.png", label + " at 393")}<figcaption>393</figcaption></figure>'
        "</div>"
    )


sections = [
    '<section class="board"><h2>0 · Today</h2><p class="note">The real module, the real producer\'s wire. Caption CREDENTIALS; Revoke only.</p>'
    + pair(SHOTS / "today", "0-today", "Today")
    + "</section>"
]
for key, title, note in BOARDS:
    sections.append(
        f'<section class="board"><h2>{html.escape(title)}</h2><p class="note">{html.escape(note)}</p>'
        f'<div class="set set-a">{pair(SHOTS / "a", f"{key}-a", title + " set A")}</div>'
        f'<div class="set set-b">{pair(SHOTS / "b", f"{key}-b", title + " set B")}</div>'
        "</section>"
    )

PAGE = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Delegation grant canvas</title>
<style>
:root {{ --bg:#f6f6f4; --fg:#1b1d22; --muted:#5b6070; --line:#d8d9dd; --card:#ffffff; --accent:#1f7a55; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#111317; --fg:#e7e8ec; --muted:#9ba2b0; --line:#2a2e3e; --card:#181b22; --accent:#4fd29a; }} }}
:root[data-theme="dark"] {{ --bg:#111317; --fg:#e7e8ec; --muted:#9ba2b0; --line:#2a2e3e; --card:#181b22; --accent:#4fd29a; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:15px/1.45 system-ui, -apple-system, sans-serif; }}
main {{ max-width:1500px; margin:0 auto; padding:24px 16px 64px; }}
h1 {{ font-size:26px; margin:0 0 4px; }}
.sub {{ color:var(--muted); margin:0 0 16px; font-size:13px; }}
.status {{ display:inline-block; font:600 12px ui-monospace, monospace; letter-spacing:.06em; border:1px solid var(--line); padding:2px 8px; margin-bottom:16px; }}
.switch {{ display:flex; gap:8px; align-items:center; flex-wrap:wrap; position:sticky; top:0; background:var(--bg); padding:8px 0; z-index:2; border-bottom:1px solid var(--line); }}
.switch label {{ font:600 12px ui-monospace, monospace; border:1px solid var(--line); padding:6px 10px; cursor:pointer; background:var(--card); }}
.switch input {{ position:absolute; opacity:0; }}
.switch input:checked + span {{ color:var(--accent); }}
table {{ border-collapse:collapse; width:100%; margin:12px 0 24px; font-size:13px; background:var(--card); }}
th, td {{ border:1px solid var(--line); padding:6px 8px; text-align:left; vertical-align:top; }}
code {{ font:12px ui-monospace, monospace; }}
.board {{ margin:28px 0; }}
.board h2 {{ font-size:17px; margin:0 0 2px; }}
.note {{ color:var(--muted); margin:0 0 8px; font-size:13px; }}
.pair {{ display:grid; grid-template-columns:minmax(0,1fr) 220px; gap:12px; align-items:start; }}
figure {{ margin:0; background:var(--card); border:1px solid var(--line); padding:6px; }}
figure img {{ width:100%; height:auto; display:block; }}
figcaption {{ font:12px ui-monospace, monospace; color:var(--muted); padding-top:4px; }}
.set-b {{ display:none; }}
body:has(#words-b:checked) .set-a {{ display:none; }}
body:has(#words-b:checked) .set-b {{ display:block; }}
ol.q li {{ margin:4px 0; }}
@media (max-width: 720px) {{ .pair {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<main>
<h1>Delegation grant canvas</h1>
<p class="sub">PHILO-7-02 · the grant on the Remote Access ledger in Settings · rendered from the library species in the production window</p>
<span class="status">PROPOSED · THE OWNER RATIFIES</span>
<div class="switch" role="radiogroup" aria-label="Word set">
  <label><input type="radio" name="words" id="words-a" checked><span>SET A · Allow filing / FILING ALLOWED</span></label>
  <label><input type="radio" name="words" id="words-b"><span>SET B · Allow filing and decisions / FILING AND DECISIONS ALLOWED (recommended)</span></label>
</div>
<table>
<tr><th>Slot</th><th>Set A</th><th>Set B (recommended)</th></tr>
<tr><td>Verb, no live grant</td><td><code>Allow filing</code></td><td><code>Allow filing and decisions</code></td></tr>
<tr><td>Verb, live grant</td><td><code>Stop filing</code></td><td><code>Stop filing and decisions</code></td></tr>
<tr><td>Chip, live</td><td><code>FILING ALLOWED</code></td><td><code>FILING AND DECISIONS ALLOWED</code></td></tr>
<tr><td>Chip, stopped or expired</td><td><code>FILING STOPPED</code></td><td><code>FILING AND DECISIONS STOPPED</code></td></tr>
<tr><td>Chip, never granted</td><td colspan="2">none</td></tr>
<tr><td>Refusal</td><td colspan="2"><code>CAN'T ALLOW</code> / <code>CAN'T STOP</code> + <code>OWNER ONLY</code>, <code>NO GRANT</code>, <code>GRANT STOPPED</code>, <code>GRANT EXPIRED</code>, <code>BAD REQUEST</code></td></tr>
<tr><td>Caption</td><td colspan="2"><code>AGENTS</code> (today <code>CREDENTIALS</code>)</td></tr>
<tr><td>Order</td><td colspan="2">credential ● lead · grant chip first cell · credential facts · grant verb, then <code>Revoke</code></td></tr>
</table>
<p class="sub">Credential rows: the real <code>GET /api/settings/remote</code> from the real hub on an isolated database. Grant rows: the lifecycle beat's decided shape; the grant producer is unbuilt. Board 0 is the real module.</p>
{''.join(sections)}
<section class="board">
<h2>Three questions</h2>
<ol class="q">
<li>Words: set A or set B? Recommended: B, because R5 put decision delete in the grant.</li>
<li>Caption: <code>AGENTS</code> in place of <code>CREDENTIALS</code>, always? Recommended: yes.</li>
<li>Order: credential ● lead, grant chip first, grant verb before <code>Revoke</code>? Recommended: yes.</li>
</ol>
</section>
</main>
</body>
</html>
"""
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(PAGE)
print(OUT, OUT.stat().st_size)
