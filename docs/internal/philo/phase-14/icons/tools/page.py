import json
I="/Users/karol/dev/tools/HoldSpeak/wt-p14-a0-icons/docs/internal/philo/phase-14/icons"
ids=json.load(open("ids.json"))
K=[("project-drawer","Project drawer"),("smart-drawer","Smart drawer (Needs you, Today)"),("conductor-drawer","Conductor drawer"),("parked-drawer","Parked drawer"),("meeting","Meeting (a recording)"),("note","Note"),("decision","Decision"),("action-item","Action item"),("artifact","Artifact"),("pull-request","Pull request"),("repository","Repository"),("person","Person"),("people-ledger","People ledger"),("agent-claude-code","Agent: Claude Code"),("agent-codex","Agent: Codex"),("thread","Thread"),("memory","Memory")]
CUR={"project-drawer":"drawer","smart-drawer":"drawer (no own sprite)","conductor-drawer":"drawer + automaton badge","parked-drawer":"drawer_stale","meeting":"cassette","note":"note","decision":"note family","action-item":"note family","artifact":"paper","pull-request":"paper (no own sprite)","repository":"drawer (shared)","person":"people-ledger (no own sprite)","people-ledger":"people-ledger","agent-claude-code":"automaton","agent-codex":"automaton2","thread":None,"memory":"tome"}
FLAG={("D2","people-ledger"):"weak: reads as a binder; the tabs carry it",
("D2","memory"):"weak: a logic chip; needs its label",
("D3","memory"):"a jar of fireflies; needs its label",
("D3","action-item"):"weak at 32: the ticket lines blur",
("D3","note"):"the scribble is noise at 32",
("D3","person"):"reads; dark fill at 32",
("D2","pull-request"):"dark page: off the D2 white-page rule",
("D1","conductor-drawer"):"the head sits on the cabinet",
("D3","project-drawer"):"a wide cabinet; the smart and Conductor drawers are narrow",
}
rows=[]
for k,name in K:
    cells=[]
    cur=CUR[k]
    if cur is None:
        cells.append('<td class="c"><div class="none">none</div><div class="cap">no sprite today</div></td>')
    else:
        cells.append(f'<td class="c"><div class="dk"><img src="current/{k}.png" width="64" height="64" alt=""></div><div class="st"><img class="s" src="current/{k}.png" width="32" height="32" alt=""></div><div class="cap">{cur}</div></td>')
    for D in ("D1","D2","D3"):
        f=FLAG.get((D,k),"")
        cells.append(f'<td><div class="dk"><img src="candidates/{D}/{k}-64.png" width="64" height="64" alt="{D} {name}"></div><div class="st"><img src="candidates/{D}/{k}-32.png" width="32" height="32" alt=""></div><div class="cap"><code>{ids[D][k][:8]}</code>{(" · "+f) if f else ""}</div></td>')
    rows.append(f'<tr><th scope="row">{name}</th>{"".join(cells)}</tr>')
html=open("page.tpl").read().replace("{{ROWS}}","\n".join(rows))
open(f"{I}/sheet.html","w").write(html)
