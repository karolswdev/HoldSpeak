"""Build morning-brief.html (shots inlined, no fetch) and shoot it at 1440 and 393.
Run from the canvas folder: python harness/page.py"""
import base64
from pathlib import Path
from playwright.sync_api import sync_playwright

D = Path(__file__).resolve().parent.parent
HEAD = '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">\n<title>Morning Brief Canvas</title>\n<style>\n/* Tokens from web/src/styles/tokens.css (--bg, --surface-1, --border, --text, --text-muted, --text-faint, --font-mono). The shots are the REAL library species (SurfaceSection, SurfaceLedger, SurfaceLedgerRow, Button, BriefEgress) with the real CSS, composed in the BRIEF section\'s own markup (harness/main.tsx). */\n:root { color-scheme: dark; --bg:#0e0f13; --surface-1:#15171d; --border:#2a2e3e; --text:#f2f3f5; --text-muted:#9ba2b0; --text-faint:#8b93a3;\n  --font-mono:"JetBrains Mono","SFMono-Regular","SF Mono",Consolas,monospace; }\n:root[data-theme="light"] { color-scheme: dark; }\nbody { margin:0; background:var(--bg); color:var(--text); font-family:var(--font-mono); padding:24px 16px; }\nh1 { font-size:14px; letter-spacing:.08em; color:var(--text-muted); margin:0 0 20px; font-weight:600; }\n.state { border-top:1px solid var(--border); padding:16px 0 24px; }\nh2 { font-size:13px; letter-spacing:.06em; margin:0 0 4px; }\n.note { font-size:12px; color:var(--text-faint); margin:0 0 12px; }\n.pair { display:grid; grid-template-columns: minmax(0,3fr) minmax(0,1fr); gap:16px; align-items:start; }\nfigure { margin:0; background:var(--surface-1); border:1px solid var(--border); padding:10px; min-width:0; }\nfigcaption { font-size:12px; color:var(--text-faint); margin-bottom:6px; }\nimg { display:block; width:100%; height:auto; }\n.w393 img { max-width:369px; }\n@media (max-width: 720px) { .pair { grid-template-columns: minmax(0,1fr); } }\n</style></head><body>\n'
H1 = "<h1>PHILO-4-01 · THE BRIEF SECTION · GENERATE ALWAYS REACHABLE · WITH PHILO-4-02 ROW ORDER · ROUND SIX</h1>\n"
BOARDS = [
 ("0-today", "0 · TODAY (REFERENCE)", "the face on main, 12 px library · no Generate while a row is untriaged · rows in the producer's order · the decision is row 5 of 6, behind 3 more"),
 ("1-generate-reachable", "1 · GENERATE IS REACHABLE", "proposed · THIS DEVICE + Generate in the head · the decision row leads · 3 more = 6 − 3 · at 393 the label wraps, the verb keeps its width"),
 ("2a-generating", "2A · GENERATING", "proposed · Generate disabled · GENERATING… in the status slot"),
 ("2b-reading", "2B · READING", "proposed · Generate disabled while the read is open · READING… (PHILO-3-03 state 2)"),
 ("3a-did-not-generate", "3A · DID NOT GENERATE", "proposed · danger line, no Retry · the enabled Generate repeats the POST · day-one rows and caption untouched"),
 ("3b-did-not-load", "3B · DID NOT LOAD", "PHILO-3-03 state 3 + the head verbs · Retry reads again (GET)"),
 ("3c-generate-after-load-failure", "3C · GENERATE AFTER A LOAD FAILURE", "proposed · Generate pressed from 3b · GENERATING… takes the status slot · the failure line and Retry go"),
 ("4-next-day-one-decision", "4 · NEXT DAY, ONE GENERATE", "proposed · the new decision is row 1 · decisions newest first (SEP 24 07:58 · SEP 22 11:30 · SEP 21 10:15) · o1 u1 l1 d2 c1 carry from day one, m1 does not · 4 more = 7 − 3"),
 ("5-next-day-several-decisions", "5 · NEXT DAY, SEVERAL DECISIONS", "proposed · newest first (illustrated created_at SEP 24 07:58 · SEP 24 07:31 · SEP 23 18:05 · then SEP 22 11:30 · SEP 21 10:15) · 6 more = 9 − 3"),
 ("6-null-brief", "6 · NO BRIEF YET", "proposed · No brief yet (A3) + Generate in the head · busy as 3c · failure 6b · result as 4"),
 ("6b-null-brief-did-not-generate", "6B · NO BRIEF YET, DID NOT GENERATE", "proposed · the failure line takes the place of No brief yet · Generate enabled · no Retry"),
 ("7a-empty-brief", "7A · EMPTY BRIEF (ZERO ITEMS)", "proposed · No changes in place of the producer sentence Nothing material changed. · the build changes the producer string and its fences together, or the owner keeps the sentence"),
 ("7b-fully-triaged", "7B · FULLY TRIAGED", "a populated brief, every row Ack or Defer · the rows leave the Arrival · head BRIEF · the stored headline, from the real _compose: 1 thing changed, 3 things waiting, 2 decisions waiting. · it still counts the six items (story 04) · Generate (today: Generate again)"),
 ("8a-quiet-generating", "8A · QUIET BRANCH, GENERATING", "proposed · 7a/7b branch · Generate disabled · GENERATING… under the caption"),
 ("8b-quiet-did-not-generate", "8B · QUIET BRANCH, DID NOT GENERATE", "proposed · 7a/7b branch · danger line under the caption · Generate enabled · no Retry"),
 ("9-empty-success-receipt", "9 · EMPTY BRIEF, RECEIPT", "proposed · a successful Generate that made zero items · Brief ready · 8:02 AM · no counter of zero"),
]
LIBS = [
 ("lib-directory-393", "LIBRARY · DIRECTORY HEAD AT 393", "the real DirectoryPullout · a long one-word name wraps inside the label · 123 members stays on one line · no horizontal overflow"),
 ("lib-jira-chip-393", "LIBRARY · JIRA CHIP AT 393", "the real ConnectionsPane Jira row · only the host chip truncates (opt-in, the row label shows the full host; title = the full host) · Recheck keeps its width and its word"),
 ("lib-route-fallback-393", "LIBRARY · ROUTE FALLBACK AT 393", "the real RouteDisclosure · a route chip keeps its full text: + FALLBACK API.ANTHROPIC.COM · its title is that full text · no horizontal overflow"),
]

def img(name):
    return base64.b64encode((D / "shots" / name).read_bytes()).decode()

parts = [HEAD, H1]
for key, title, note in BOARDS:
    parts.append(f'<section class="state"><h2>{title}</h2><p class="note">{note}</p>\n<div class="pair">'
                 f'<figure class="w1440"><figcaption>1440</figcaption><img alt="{key} at 1440" src="data:image/png;base64,{img(key + "-1440.png")}"></figure>\n'
                 f'<figure class="w393"><figcaption>393</figcaption><img alt="{key} at 393" src="data:image/png;base64,{img(key + "-393.png")}"></figure></div></section>')
for key, title, note in LIBS:
    parts.append(f'<section class="state"><h2>{title}</h2><p class="note">{note}</p>\n<div class="pair">'
                 f'<figure class="w393"><figcaption>393</figcaption><img alt="{key}" src="data:image/png;base64,{img(key + ".png")}"></figure></div></section>')
parts.append("\n</body></html>\n")
(D / "morning-brief.html").write_text("".join(parts))

with sync_playwright() as p:
    b = p.chromium.launch()
    for w in (1440, 393):
        pg = b.new_page(viewport={"width": w, "height": 900})
        pg.goto(f"file://{D}/morning-brief.html"); pg.wait_for_timeout(300)
        print(w, "scrollWidth", pg.evaluate("document.documentElement.scrollWidth"))
        pg.screenshot(path=str(D / f"morning-brief{'' if w == 1440 else '-393'}.png"), full_page=True)
    b.close()
