"""Build the owner's review page (../index.html): every board, both widths,
both word sets. The shots are linked by relative path (no base64)."""
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANVAS = HERE.parent
OUT = CANVAS / "index.html"
SUMMARY = json.loads((CANVAS / "shots/facts.json").read_text())["summary"]

BOARDS = [
    ("1-never", "1 · No project grant", "sweep-runner open: one line per project, each with the Allow verb; no chip. desk-agent reads DESK and has no project lines (a DESK credential holds no project tool)."),
    ("2-live", "2 · Granted on one project (the row closed)", "The row names what is allowed and where: the ALLOWED chip + PAYMENTS LEDGER CUTOVER. Footer receipt ALLOWED."),
    ("3-live-open", "3 · Granted on one project (the row open)", "Payments ledger cutover: ALLOWED + Stop. Hiring loop: no chip + Allow. Each project is its own grant."),
    ("4-stopped", "4 · Stopped", "Stored REVOKED: the STOPPED chip and the Allow verb. Footer receipt STOPPED."),
    ("5-expired", "5 · Expired", "Stored LIVE with expires_at one hour ago; the projection gives EXPIRED: the STOPPED chip, the Allow verb, no receipt (expiry is not an owner act)."),
    ("6-orphan", "6 · Grant live, no credential (Remote Access ON)", "sweep-runner's credential is gone; its grant row stays: ALLOWED, the project, NO CREDENTIAL, the Stop verb."),
    ("7-orphan-off", "7 · Grant live, no credential (Remote Access OFF)", "The ledger still shows the grant and its Stop verb, whatever the switch says."),
    ("7b-off-credential", "7b · Remote Access OFF, credential kept, grant live", "The credential row stays because it carries live authority; its project lines keep Stop."),
    ("8-refused", "8 · Stop refused", "Another owner request stopped the grant first: CANNOT STOP · NO GRANT on the project line; the reread shows STOPPED; the footer receipt REFUSED and its well (rendered open)."),
    ("9-two-projects", "9 · Granted on two projects", "The closed row counts the live projects: ALLOWED + 2 PROJECTS."),
]


def pair(folder: str, name: str, label: str) -> str:
    return (
        '<div class="pair">'
        f'<figure><img src="shots/{folder}/{name}-1440.png" alt="{html.escape(label)} at 1440" loading="lazy"><figcaption>1440 × 900</figcaption></figure>'
        f'<figure><img src="shots/{folder}/{name}-393.png" alt="{html.escape(label)} at 393" loading="lazy"><figcaption>393 × 852</figcaption></figure>'
        "</div>"
    )


sections = ['<section class="board"><h2>0 · Today</h2><p class="note">The real module on the real wire: the Phase 7 desk grant only; desk-agent reads ALL (the defect); no project grant.</p>'
            + pair("today", "0-today", "Today") + "</section>"]
for key, title, note in BOARDS:
    sections.append(
        f'<section class="board"><h2>{html.escape(title)}</h2><p class="note">{html.escape(note)}</p>'
        f'<div class="set set-a">{pair("a", f"{key}-a", title + " set A")}</div>'
        f'<div class="set set-b">{pair("b", f"{key}-b", title + " set B")}</div></section>'
    )

m = SUMMARY
PAGE = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Project grant canvas</title>
<style>
/* The product's dark field tokens (web/src/styles/tokens.css) for the page. */
:root {{ --bg:#15171d; --fg:#e7e8ec; --muted:#9ba2b0; --line:#2a2e3e; --card:#1b1e26; --accent:#4fd29a; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:15px/1.45 system-ui, -apple-system, sans-serif; }}
main {{ max-width:1500px; margin:0 auto; padding:24px 16px 64px; }}
h1 {{ font-size:24px; margin:0 0 4px; }}
.sub {{ color:var(--muted); margin:0 0 12px; font-size:13px; }}
.status {{ display:inline-block; font:600 12px ui-monospace, monospace; letter-spacing:.06em; border:1px solid var(--line); padding:2px 8px; margin-bottom:12px; }}
.switch {{ display:flex; gap:8px; flex-wrap:wrap; position:sticky; top:0; background:var(--bg); padding:8px 0; z-index:2; border-bottom:1px solid var(--line); }}
.switch label {{ font:600 12px ui-monospace, monospace; border:1px solid var(--line); padding:6px 10px; cursor:pointer; background:var(--card); }}
.switch input {{ position:absolute; opacity:0; }}
.switch input:checked + span {{ color:var(--accent); }}
table {{ border-collapse:collapse; width:100%; margin:12px 0 20px; font-size:13px; background:var(--card); }}
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
@media (max-width: 720px) {{ .pair {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<main>
<h1>Project grant canvas</h1>
<p class="sub">PHILO-9-07 · the project delegation grant on the Remote Access ledger · library species in the production Settings window</p>
<span class="status">DRAFT · FOR THE OWNER'S RATIFICATION</span>
<div class="switch" role="radiogroup" aria-label="Word set">
  <label><input type="radio" name="words" id="words-a" checked><span>SET A · Allow run and publish (recommended)</span></label>
  <label><input type="radio" name="words" id="words-b"><span>SET B · Allow project work</span></label>
</div>
<table>
<tr><th>Slot</th><th>Set A (recommended)</th><th>Set B</th></tr>
<tr><td>Verb, not live</td><td><code>Allow run and publish</code></td><td><code>Allow project work</code></td></tr>
<tr><td>Verb, live</td><td><code>Stop run and publish</code></td><td><code>Stop project work</code></td></tr>
<tr><td>Chip, live</td><td><code>RUN AND PUBLISH ALLOWED</code></td><td><code>PROJECT WORK ALLOWED</code></td></tr>
<tr><td>Chip, stopped or expired</td><td><code>RUN AND PUBLISH STOPPED</code></td><td><code>PROJECT WORK STOPPED</code></td></tr>
<tr><td>Closed row</td><td colspan="2">the live chip + the project name (one) or <code>N PROJECTS</code> (more); nothing when no project grant is live</td></tr>
<tr><td>Refusal</td><td colspan="2"><code>CANNOT ALLOW</code> / <code>CANNOT STOP</code> + <code>NO GRANT</code>, <code>GRANT STOPPED</code>, <code>GRANT EXPIRED</code>, <code>OWNER ONLY</code>, <code>BAD REQUEST</code></td></tr>
<tr><td>Palette</td><td colspan="2">the issued name: desk-agent reads <code>DESK</code> (today <code>ALL</code>)</td></tr>
</table>
<p class="sub">Measured on {m['renders']} renders: text under 12 px {len(m['small_text'])}; raw buttons {len(m['raw_buttons'])}; horizontal overflow {len(m['overflow'])}; chips and tokens {m['chips_measured']}, lowest contrast {m['contrast_min']}:1; Buttons {m['buttons_probed']}, points {m['points_probed']}, not owned {len(m['not_owned'])}.</p>
{''.join(sections)}
<section class="board">
<h2>Three questions</h2>
<ol>
<li>Words: set A (<code>Allow run and publish</code>) or set B (<code>Allow project work</code>)? Recommended: A. It names your ruling ("Run, stop, publish") and what the agent can do.</li>
<li>The pick: the PROJECT credential's row opens in place with one line per project, each with its own verb (no popover, no modal)? Recommended: yes.</li>
<li>Project lines only on credentials whose palette holds the project tools (PROJECT, ALL); a DESK credential gets none? Recommended: yes.</li>
</ol>
</section>
<section class="board">
<h2>Limits</h2>
<ul>
<li>The project grant producer does not exist. Credential rows are the real <code>GET /api/settings/remote</code> of a real hub on an isolated HOME; project grant rows are stored rows plus a clock, projected by the canvas's rule (README, "The wire contract").</li>
<li>The DESK palette name is the canvas's statement of the repair: the real wire says ALL (board 0).</li>
<li>Refusals, operation ids and receipt times are fixture values. The boards are static states; the receipt well on board 8 is rendered open.</li>
</ul>
</section>
</main>
</body>
</html>
"""
OUT.write_text(PAGE)
print(OUT, OUT.stat().st_size)
