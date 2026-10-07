/* PHILO-14 canvas: The Desk Is Objects. Three alternatives of the desk's SHAPE, drawn on the REAL
 * product (the screen bar, the Dock, the window frame, the library species) against a real hub on
 * an isolated HOME. Loaded only in CANVAS_MODE=proposal. One seat (seats.mjs) lets an alternative
 * take the Chair's place; with no alternative chosen the product renders exactly as on main (the
 * CONTROL boards are shot in CANVAS_MODE=today, with no seat and no shim at all).
 *
 * THE ALTERNATIVES (the same five moments each, 1440 and 393):
 *   A "Workbench": a screen of icons (drawers, objects, the Conductor drawer, Needs you, Parked);
 *     windows you open and stack; Get Info is its own window.
 *   B "Bench": a Shelf of drawers on the left, windows stacked on the bench, the Conductor as a
 *     Pit of agent bays along the bottom; a drawer opens as a tray with one row per kind.
 *   C "Stage": the Floor as places: each Project is a zone, agents (automatons) stand at the item
 *     they work, a trail back to the Conductor's garage; a drawer opens by entering its place.
 * Moments: 1 the Floor; 2 a Project drawer open (icons at 1440, the list at 393, Get Info);
 *   3 drop to hand (the YOLO confirm line, the brief one press away); 4 the agent's lane;
 *   5 Needs you as a smart drawer.
 *
 * STAND-INS (named; no board claims more than it shows):
 *   S1 the drawers' contents are composed here from the seeded records' names (the build reads a
 *      Project's members from the hub); the action item "Write the cutover comms" is a canvas item.
 *   S2 the agents, their states and their lamps (ASKS, WORKS, PR #412) are this file's; the hub
 *      holds the same two hook-reported sessions and three launches (seed_db.py, seed_f2.py).
 *   S3 the lane's timeline (tool calls, the agent's words, commit a1c9e02, PR #413, the held call,
 *      the files changed) is canvas data: the hub keeps most of it today and serves none of it
 *      (PROPOSAL §2; lane C0 builds the route).
 *   S4 the drafted answer "Jordan owns it. Avery reviews." is canvas text (the hub drafts one and
 *      no face shows it).
 *   S5 the drag is drawn (a ghost sprite at the target, the target lit); no drop handler runs.
 *      Hand, Answer, Approve, Deny, Stop, Re-brief and Open PR do nothing: nothing leaves the
 *      machine; no agent starts.
 *   S6 the Needs you rows are composed here from the seeded records and S2/S3.
 *   S7 sprites: the mold has no sprite for an action item (the note family is drawn), a PR (paper),
 *      a person (the one people-ledger), a smart drawer or the Conductor drawer (the drawer with a
 *      badge); a project and a repository share the drawer. Named in ../README.md.
 */
import { useLayoutEffect, useSyncExternalStore, type ReactNode } from "react";
import "./p14.css";
import { Button } from "@w/components/signal/Signal";
import {
  EgressChip,
  FilterTokens,
  LampGadget,
  StringGadget,
  SurfaceFooter,
  SurfaceSection,
} from "@w/desk/surface";
import { DeskWindowFrame } from "@w/desk/components/DeskWindow";
import { useDesk } from "@w/desk/store";
import { SPRITE_BASE, spriteUrl } from "@w/desk/sprites";
import { useCompactViewport } from "@w/desk/useCompactViewport";

const G = globalThis as any;

/* ── the shim's store ─────────────────────────────────────────────────── */

type Alt = "A" | "B" | "C";
const P = {
  tick: 0,
  subs: new Set<() => void>(),
  alt: null as Alt | null,
  moment: 1,
  view: "icons" as "icons" | "list",
  sel: null as string | null,
  answer: "",
};
const bump = () => { P.tick++; P.subs.forEach((f) => f()); };
const useP = () => useSyncExternalStore((f) => { P.subs.add(f); return () => P.subs.delete(f); }, () => P.tick);

/* ── the objects (S1, S2) ─────────────────────────────────────────────── */

type Kind = "project" | "meeting" | "decision" | "action" | "note" | "artifact" | "repository" | "agent" | "pr" | "person" | "conductor" | "smart" | "parked";
type Tone = "ask" | "work" | "ok" | "held" | "due";
type Obj = { id: string; name: string; kind: Kind; when: string; where: string; tone?: Tone; word?: string; count?: number; badge?: string };

const KIND_WORD: Record<Kind, string> = {
  project: "PROJECT", meeting: "MEETING", decision: "DECISION", action: "ACTION ITEM", note: "NOTE", artifact: "ARTIFACT",
  repository: "REPOSITORY", agent: "AGENT", pr: "PULL REQUEST", person: "PERSON", conductor: "DRAWER", smart: "SMART DRAWER", parked: "DRAWER",
};
const LAMP_TONE: Record<Tone, "ok" | "warn" | "fail"> = { ask: "warn", work: "ok", ok: "ok", held: "warn", due: "warn" };

const day = (offset: number) => { const d = new Date(Date.now() - offset * 86400000); return d.toLocaleString("en-US", { month: "short", day: "numeric" }).toUpperCase(); };
const TODAY = "TODAY";
const LEDGER = "Payments ledger cutover";

function sprite(o: { kind: Kind; id: string }, state: "rest" | "sel" | "stale" = "rest"): string {
  const base = (name: string) => `${SPRITE_BASE}${name}${state === "rest" ? "" : `_${state}`}.png`;
  switch (o.kind) {
    case "project": case "repository": case "conductor": case "smart": return base("drawer");
    case "parked": return `${SPRITE_BASE}drawer_stale.png`;
    case "action": return spriteUrl("story", o.id, state);
    case "pr": return spriteUrl("artifact", o.id, state);
    case "person": return spriteUrl("people", o.id, state);
    case "agent": return spriteUrl("coder", o.id, state);
    default: return spriteUrl(o.kind, o.id, state);
  }
}
const AGENT_BADGE = spriteUrl("coder", "conductor-badge");

const RUNBOOK: Obj = { id: "m-standup-a1", name: "Write the rollback runbook", kind: "action", when: TODAY, where: LEDGER, tone: "ask", word: "CLAUDE CODE ASKS" };
const RECON: Obj = { id: "m-standup-a2", name: "Shard the reconciliation job", kind: "action", when: TODAY, where: LEDGER, tone: "work", word: "CODEX WORKS" };
const FLAG: Obj = { id: "m-standup-a3", name: "Add the ledger freeze flag", kind: "action", when: TODAY, where: LEDGER, tone: "ok", word: "PR #412" };
const COMMS: Obj = { id: "act-cutover-comms", name: "Write the cutover comms", kind: "action", when: TODAY, where: LEDGER };
const AG_RUNBOOK: Obj = { id: "claude:c1a0de00-runbook", name: "Claude Code: rollback runbook", kind: "agent", when: "42 MIN", where: LEDGER, tone: "ask", word: "ASKS" };
const AG_RECON: Obj = { id: "codex:c0dex000-recon", name: "Codex: reconciliation", kind: "agent", when: "30 MIN", where: LEDGER, tone: "work", word: "WORKS" };
const AG_FLAG: Obj = { id: "claude:flag", name: "Claude Code: freeze flag", kind: "agent", when: "1 H", where: LEDGER, tone: "ok", word: "PR #412" };
const PR412: Obj = { id: "pr-412", name: "#412 Add the ledger freeze flag", kind: "pr", when: TODAY, where: LEDGER, tone: "ok", word: "CHECKS PASS" };

const DRAWER: Obj[] = [
  { id: "m-standup", name: "Ledger cutover sync", kind: "meeting", when: TODAY, where: LEDGER },
  { id: "d-freeze", name: "Freeze the old ledger on Nov 5", kind: "decision", when: TODAY, where: LEDGER },
  RUNBOOK, RECON, FLAG, COMMS,
  AG_RUNBOOK, AG_RECON, AG_FLAG, PR412,
  { id: "n-1", name: "Ledger cutover risks", kind: "note", when: day(1), where: LEDGER },
  { id: "art-cutover-reqs", name: "Cutover requirements", kind: "artifact", when: TODAY, where: LEDGER },
  { id: "m-standup-notes", name: "Ledger cutover sync: notes", kind: "artifact", when: TODAY, where: LEDGER },
  { id: "repo-payments-ledger", name: "payments-ledger", kind: "repository", when: day(2), where: LEDGER },
  { id: "p-jordan", name: "Jordan Patel", kind: "person", when: "WEEKLY", where: LEDGER },
  { id: "p-avery", name: "Avery Chen", kind: "person", when: "WEEKLY", where: LEDGER },
];
const DRAWER_GROUPS: [string, Kind[]][] = [
  ["Meetings", ["meeting"]], ["Decisions", ["decision"]], ["Action items", ["action"]], ["Agents", ["agent", "pr"]],
  ["Notes, files", ["note", "artifact"]], ["Repository, people", ["repository", "person"]],
];

const PROJECTS: Obj[] = [
  { id: "p-ledger", name: LEDGER, kind: "project", when: TODAY, where: "", tone: "ask", count: 3 },
  { id: "p-obs", name: "Platform observability", kind: "project", when: day(1), where: "", count: 1 },
  { id: "p-hiring", name: "Staff hiring loop", kind: "project", when: day(3), where: "", count: 1 },
];
const CONDUCTOR: Obj = { id: "conductor", name: "Conductor", kind: "conductor", when: "", where: "", tone: "ask", count: 3, badge: AGENT_BADGE };
const NEEDS: Obj = { id: "needs-you", name: "Needs you", kind: "smart", when: "", where: "", tone: "ask", count: 6 };
const PEOPLE: Obj = { id: "people", name: "People", kind: "person", when: "", where: "" };
const PARKED: Obj = { id: "parked", name: "Parked", kind: "parked", when: "", where: "" };
const LOOSE: Obj[] = [
  { id: "m-bare", name: "Vendor call", kind: "meeting", when: TODAY, where: "", tone: "due" },
  { id: "n-2", name: "Questions for Avery 1:1", kind: "note", when: day(1), where: "" },
  { id: "thought-shards", name: "Idea: shard the reconciliation", kind: "note", when: TODAY, where: "" },
  { id: "m-avery", name: "1:1 Avery", kind: "meeting", when: day(2), where: "" },
];

/* ── the species (proposed: README "New species") ─────────────────────── */

function Lamp({ tone }: { tone?: Tone }) {
  return tone ? <span className="p14-lamp" data-tone={tone} aria-hidden="true" /> : null;
}

/** DeskIcon: the object on the glass (a chrome Button: the sprite over its name). */
function Icon({ o, sel, drop, ghost, className, style, onClick, name }: {
  o: Obj; sel?: boolean; drop?: boolean; ghost?: boolean; className?: string; style?: React.CSSProperties; onClick?: () => void; name?: string;
}) {
  const label = [name ?? o.name, KIND_WORD[o.kind], o.word, o.count ? `${o.count} need you` : ""].filter(Boolean).join(", ");
  return (
    <Button variant="chrome" className={`p14-icon ${className ?? ""}`} data-sel={sel ? "true" : undefined}
      data-drop={drop ? "true" : undefined} data-ghost={ghost ? "true" : undefined} style={style} aria-label={label}
      data-testid={`p14-icon-${o.id}`} onClick={onClick}>
      <span className="p14-icon-art">
        <img src={sprite(o, sel || drop ? "sel" : "rest")} alt="" draggable={false} />
        {o.badge ? <img className="p14-icon-badge" src={o.badge} alt="" /> : null}
        <Lamp tone={o.tone} />
        {o.count ? <span className="p14-count" aria-hidden="true">{o.count}</span> : null}
      </span>
      <span className="p14-icon-name">{name ?? o.name}</span>
    </Button>
  );
}

/** The drag ghost: the dragged object's sprite only, under the pointer (S5). */
function Ghost({ o, x, y }: { o: Obj; x: number; y: number }) {
  return <img className="p14-ghost" src={sprite(o)} alt="" aria-hidden="true" style={{ left: x, top: y }} data-testid="p14-ghost" />;
}

/** DragPath: the pointer's way from the lifted object to the target (S5; drawn, aria-hidden). */
function DragPath({ d }: { d: string }) {
  return (
    <svg className="p14-ghost-path" aria-hidden="true" style={{ position: "fixed", inset: 0, width: "100vw", height: "100vh", pointerEvents: "none", zIndex: 2147482999 }}>
      <path d={d} fill="none" stroke="#eef0f3" strokeWidth={2} strokeDasharray="2 6" opacity={0.8} />
    </svg>
  );
}

function placeWindow(id: string, r: { x: number; y: number; w: number; h: number }) {
  const s = useDesk.getState();
  const cur = s.panelRects[id];
  if (!cur || cur.x !== r.x || cur.y !== r.y || cur.w !== r.w || cur.h !== r.h) s.setPanelRect(id, r, true);
}

function Win({ id, title, icon, rect, children, footer, actions, minW = 300 }: {
  id: string; title: string; icon: Obj; rect: { x: number; y: number; w: number; h: number }; children: ReactNode; footer?: ReactNode; actions?: ReactNode; minW?: number;
}) {
  useLayoutEffect(() => { placeWindow(id, rect); }, [id, rect.x, rect.y, rect.w, rect.h]);
  return (
    <DeskWindowFrame id={id} title={title} label={title} glyph="▢" className="desk-pullout p14-win" minW={minW} minH={200}
      defaultW={rect.w} defaultH={rect.h} entrance={false} open actions={actions}
      icon={<img className="p14-winicon" src={sprite(icon)} alt="" />} onClose={() => { P.moment = 1; bump(); }}>
      <div className="desk-pullout-body">
        <div className="p14-body">{children}</div>
      </div>
      {footer}
    </DeskWindowFrame>
  );
}

/* ── drawer bodies ───────────────────────────────────────────────────── */

function DrawerHead({ view, onView }: { view: "icons" | "list"; onView: (v: string) => void }) {
  return (
    <div className="p14-drawer-head">
      <div className="p14-facts" data-testid="p14-drawer-facts">
        <LampGadget label="3 NEED YOU" on tone="warn" />
        <span className="p14-fact">CUTOVER <b>NOV 5</b></span>
        <span className="p14-fact">STATUS <b>ON TRACK</b></span>
        <span className="p14-fact"><b>16</b> OBJECTS</span>
      </div>
      <FilterTokens label="Drawer view" value={view} onChange={onView}
        options={[{ value: "icons", label: "Icons" }, { value: "list", label: "List" }]} />
    </div>
  );
}

function IconGrid({ items, sel, drop, ghost, onSel }: { items: Obj[]; sel?: string | null; drop?: string; ghost?: string; onSel?: (id: string) => void }) {
  return (
    <div className="p14-grid" data-testid="p14-grid">
      {items.map((o) => <Icon key={o.id} o={o} sel={sel === o.id} drop={drop === o.id} ghost={ghost === o.id} onClick={() => onSel?.(o.id)} />)}
    </div>
  );
}

/** ObjectList: name, kind, when, where; one lamp; sort headers; selection by click. */
function ObjectList({ items, sel, onSel }: { items: Obj[]; sel?: string | null; onSel?: (id: string) => void }) {
  return (
    <div className="p14-list" role="table" aria-label="Drawer contents" data-testid="p14-list">
      <div className="p14-list-head" role="row">
        <span aria-hidden="true" />
        <Button variant="chrome" className="p14-sort" aria-pressed="true" data-col="name">Name ▲</Button>
        <Button variant="chrome" className="p14-sort" data-col="kind">Kind</Button>
        <Button variant="chrome" className="p14-sort" data-col="when">When</Button>
        <Button variant="chrome" className="p14-sort" data-col="state">State</Button>
      </div>
      <div className="p14-list-rows">
      {[...items].sort((a, b) => a.name.localeCompare(b.name)).map((o) => (
        <Button key={o.id} variant="chrome" className="p14-row" role="row" data-sel={sel === o.id ? "true" : undefined}
          aria-label={`${o.name}, ${KIND_WORD[o.kind]}`} onClick={() => onSel?.(o.id)} data-testid={`p14-row-${o.id}`}>
          <img src={sprite(o)} alt="" />
          <span style={{ minWidth: 0 }}>
            <span className="p14-row-name" style={{ display: "block" }}>{o.name}</span>
            <span className="p14-row-sub">{KIND_WORD[o.kind]} · {o.when}</span>
          </span>
          <span className="p14-cell" data-col="kind">{KIND_WORD[o.kind]}</span>
          <span className="p14-cell" data-col="when">{o.when}</span>
          <span data-col="state">{o.word ? <LampGadget label={o.word} on tone={LAMP_TONE[o.tone ?? "ok"]} /> : null}</span>
        </Button>
      ))}
      </div>
    </div>
  );
}

function InfoBody({ o }: { o: Obj }) {
  return (
    <>
      <div className="p14-info-head">
        <img src={sprite(o)} alt="" />
        <div>
          <div className="p14-primary">{o.name}</div>
          <p className="p14-caption">{KIND_WORD[o.kind]}</p>
        </div>
      </div>
      <dl className="p14-facts-table" data-testid="p14-info">
        <dt>Where</dt><dd>{LEDGER}</dd>
        <dt>From</dt><dd>Ledger cutover sync</dd>
        <dt>Made</dt><dd>{TODAY} 08:40</dd>
        <dt>Due</dt><dd>None</dd>
        <dt>Owner</dt><dd>Claude Code (agent)</dd>
        <dt>State</dt><dd><LampGadget label="CLAUDE CODE ASKS" on tone="warn" /></dd>
        <dt>Branch</dt><dd><code className="p14-mono">hs/write-the-rollback-runbook</code></dd>
      </dl>
    </>
  );
}
const infoVerbs = (
  <span className="p14-verbs">
    <Button dense variant="ghost">Rename</Button>
    <Button dense variant="ghost">Park</Button>
    <Button dense variant="primary">Open</Button>
  </span>
);

/* ── the hand (moment 3) ─────────────────────────────────────────────── */

const HANDEE = COMMS;
function ConfirmLine({ agent }: { agent: Obj }) {
  return (
    <div className="p14-confirm" data-testid="p14-confirm">
      <img src={sprite(HANDEE)} alt="" />
      <span className="p14-arrow" aria-hidden="true">→</span>
      <img src={sprite(agent)} alt="" />
      <span className="p14-what">
        <span className="p14-primary">{HANDEE.name}</span>
        <span className="p14-mono">CLAUDE CODE · YOLO · hs/write-the-cutover-comms</span>
      </span>
      <span className="p14-verbs">
        <Button dense variant="ghost" data-testid="p14-brief">Brief ▸</Button>
        <Button dense variant="ghost">Cancel</Button>
        <Button dense variant="primary" data-testid="p14-hand">Hand</Button>
      </span>
    </div>
  );
}
const HAND_AGENT: Obj = { id: "claude:launcher", name: "Claude Code", kind: "agent", when: "", where: "" };
const CODEX_AGENT: Obj = { id: "codex:launcher", name: "Codex", kind: "agent", when: "", where: "" };

/* ── the lane (moment 4; S3, S4) ─────────────────────────────────────── */

type Ev = { t: string; kind: string; tone?: Tone | "next"; text?: string; code?: string; words?: string; verbs?: ReactNode };
const EVENTS: Ev[] = [
  { t: "09:42", kind: "Brief", text: "6 sources · 4.2 KB · 3 checks", verbs: <Button dense variant="ghost">Brief</Button> },
  { t: "09:43", kind: "Read", code: "ledger/freeze.py · docs/runbooks/README.md · +2" },
  { t: "09:45", kind: "Says", words: "I will draft the runbook from the freeze decision and the Nov 12 rollback window." },
  { t: "09:47", kind: "Write", code: "docs/runbooks/ledger-rollback.md +84" },
  { t: "09:48", kind: "Run", tone: "ok", code: "pytest tests/runbooks -q · 6 passed" },
  { t: "09:51", kind: "Commit", code: "a1c9e02 Draft the ledger rollback runbook" },
  { t: "09:53", kind: "PR", tone: "work", text: "#413 opened · checks 6 of 7 · review none yet" },
  { t: "09:55", kind: "Held", tone: "held", code: "psql -h staging-ledger -c 'select count(*) from entries'",
    verbs: <><Button dense variant="ghost" data-testid="p14-deny">Deny</Button><Button dense variant="secondary" data-testid="p14-approve">Approve</Button></> },
  { t: "09:56", kind: "Asks", tone: "ask", text: "The runbook needs a rollback owner. Jordan or Avery?" },
  { t: "", kind: "Merge", tone: "next", text: "Your press in GitHub" },
];

function AskWell() {
  useP();
  return (
    <div className="p14-ask" data-testid="p14-ask">
      <p className="p14-caption">Claude Code asks · 6 min</p>
      <p className="p14-ask-q" data-testid="p14-question">The runbook needs a rollback owner. Jordan or Avery?</p>
      <div className="p14-ask-row">
        <StringGadget label="Answer" value={P.answer} onChange={(v) => { P.answer = v; bump(); }} placeholder="Say or type the answer"
          micLabel="Speak the answer" />
        <Button variant="primary" data-testid="p14-answer">Answer</Button>
      </div>
      <div className="p14-draft">
        <span className="p14-caption">Draft</span>
        <span className="p14-text">Jordan owns it. Avery reviews.</span>
        <Button dense variant="ghost">Use draft</Button>
        <EgressChip label="API.ANTHROPIC.COM" scope="cloud" />
      </div>
    </div>
  );
}

function Rail() {
  return (
    <ol className="p14-rail" aria-label="Lane" data-testid="p14-rail">
      {EVENTS.map((e, i) => (
        <li key={i} className="p14-ev" data-tone={e.tone}>
          <span className="p14-ev-time">{e.t}</span>
          <span className="p14-ev-node"><span className="p14-ev-dot" /></span>
          <span className="p14-ev-body">
            <span className="p14-ev-line">
              <span className="p14-ev-kind">{e.kind}</span>
              {e.text ? <span className="p14-ev-text">{e.text}</span> : null}
              {e.code ? <code className="p14-ev-code">{e.code}</code> : null}
            </span>
            {e.words ? <span className="p14-ev-words">{e.words}</span> : null}
            {e.verbs ? <span className="p14-verbs">{e.verbs}</span> : null}
          </span>
        </li>
      ))}
    </ol>
  );
}

const STATIONS: { kind: string; tone?: Tone | "next"; text: string }[] = [
  { kind: "Brief", tone: "ok", text: "09:42" }, { kind: "Work", tone: "ok", text: "14 calls" }, { kind: "Commit", tone: "ok", text: "1" },
  { kind: "PR", tone: "work", text: "#413" }, { kind: "Held", tone: "held", text: "1 call" }, { kind: "Asks", tone: "ask", text: "now" }, { kind: "Merge", tone: "next", text: "yours" },
];
function Track() {
  return (
    <ol className="p14-track p14-rail" aria-label="Lane stations" data-testid="p14-track">
      {STATIONS.map((s) => (
        <li key={s.kind} className="p14-station" data-tone={s.tone} data-on={s.tone !== "next" ? "true" : undefined}>
          <span className="p14-ev-dot" />
          <span className="p14-ev-kind">{s.kind}</span>
          <span className="p14-mono">{s.text}</span>
        </li>
      ))}
    </ol>
  );
}

function PRCard() {
  return (
    <div className="p14-pr" data-testid="p14-pr">
      <div className="p14-pr-line">
        <img className="p14-winicon" src={sprite({ kind: "pr", id: "pr-413" })} alt="" />
        <span className="p14-primary">#413 Draft the ledger rollback runbook</span>
      </div>
      <div className="p14-pr-line">
        <LampGadget label="CHECKS 6 OF 7" on tone="ok" />
        <LampGadget label="1 RUNNING" on={false} />
        <span className="p14-fact">REVIEW <b>NONE YET</b></span>
      </div>
      <div className="p14-pr-line">
        <code className="p14-mono">hs/write-the-rollback-runbook → main</code>
      </div>
    </div>
  );
}

function Files() {
  return (
    <SurfaceSection label="Files changed · 3">
      <div className="p14-files" data-testid="p14-files">
        <div className="p14-file"><code>docs/runbooks/ledger-rollback.md</code><span>+84</span></div>
        <div className="p14-file"><code>ledger/freeze.py</code><span>+3 −1</span></div>
        <div className="p14-file"><code>tests/runbooks/test_rollback.py</code><span>+22</span></div>
      </div>
    </SurfaceSection>
  );
}

function LaneFooter() {
  const compact = useCompactViewport();
  return (
  <SurfaceFooter
    egress={<EgressChip label="GITHUB.COM" scope="cloud" />}
    receipt={compact ? undefined : <span className="p14-mono">hs/write-the-rollback-runbook</span>}
    verbs={<>
      <Button dense variant="ghost">Re-brief</Button>
      <Button dense variant="danger">Stop</Button>
      <Button dense variant="secondary" data-testid="p14-open-pr">Open PR</Button>
    </>}
  />
  );
}
const rawVerb = <Button dense variant="ghost" aria-label="Raw: the terminal pane">Raw</Button>;

function LaneBody({ shape }: { shape: "rail" | "cols" | "track" }) {
  const compact = useCompactViewport();
  if (shape === "track") {
    return (<>
      <Track />
      <AskWell />
      <div className="p14-lane-cols">
        <div className="p14-lane-col"><Rail /></div>
        <div className="p14-lane-col"><PRCard /><Files /></div>
      </div>
    </>);
  }
  if (shape === "cols" && !compact) {
    return (
      <div className="p14-lane-cols">
        <div className="p14-lane-col"><AskWell /><Rail /></div>
        <div className="p14-lane-col"><PRCard /><Files /></div>
      </div>
    );
  }
  return (<><AskWell /><PRCard /><Rail /><Files /></>);
}

/* ── Needs you (moment 5; S6) ────────────────────────────────────────── */

type Need = { o: Obj; fact: string; lamp: string; tone: Tone; verbs: ReactNode; group: string };
const NEED_ROWS: Need[] = [
  { o: AG_RUNBOOK, fact: "The runbook needs a rollback owner. Jordan or Avery?", lamp: "ASKS · 6 MIN", tone: "ask", group: "Agents",
    verbs: <><Button dense variant="ghost">Open</Button><Button dense variant="primary" data-testid="p14-need-answer">Answer</Button></> },
  { o: AG_RECON, fact: "psql -h staging-ledger -c 'select count(*) from entries'", lamp: "HELD CALL", tone: "held", group: "Agents",
    verbs: <><Button dense variant="ghost">Deny</Button><Button dense variant="secondary">Approve</Button></> },
  { o: PR412, fact: "Approved · 7 of 7 checks · your merge", lamp: "CHECKS PASS", tone: "ok", group: "Agents",
    verbs: <><EgressChip label="GITHUB.COM" scope="cloud" /><Button dense variant="secondary">Open PR</Button></> },
  { o: { id: "d-ops", name: "Run a second ops interview", kind: "decision", when: TODAY, where: "Staff hiring loop" }, fact: "Staff hiring loop · from Hiring debrief", lamp: "TO REVIEW", tone: "due", group: "To review",
    verbs: <Button dense variant="secondary">Review</Button> },
  { o: { id: "req-sam", name: "Sam: send the status by Thursday", kind: "action", when: TODAY, where: "" }, fact: "Sam Rivera · 1:1", lamp: "DUE TODAY", tone: "due", group: "Due",
    verbs: <Button dense variant="secondary">Done</Button> },
  { o: { id: "m-bare", name: "Vendor call", kind: "meeting", when: TODAY, where: "" }, fact: "20 min · no summary", lamp: "NO SUMMARY", tone: "due", group: "Due",
    verbs: <Button dense variant="secondary">Summarize</Button> },
];

function NeedsBody({ grouped }: { grouped?: boolean }) {
  const rows = (list: Need[]) => list.map((n) => (
    <div key={n.o.id} className="p14-nrow" data-testid="p14-need-row">
      <img src={sprite(n.o)} alt="" />
      <span className="p14-nrow-what">
        <span className="p14-nrow-name">{n.o.name}</span>
        <span className="p14-nrow-fact">{n.fact}</span>
      </span>
      <LampGadget label={n.lamp} on tone={LAMP_TONE[n.tone]} />
      <span className="p14-verbs">{n.verbs}</span>
    </div>
  ));
  return (<>
    <h2 className="p14-display" data-testid="p14-needs-head">6 need you</h2>
    {grouped
      ? ["Agents", "Due", "To review"].map((g) => (
        <SurfaceSection key={g} label={g}><div className="p14-needs">{rows(NEED_ROWS.filter((n) => n.group === g))}</div></SurfaceSection>))
      : <div className="p14-needs">{rows(NEED_ROWS)}</div>}
  </>);
}

/* ── geometry: 1440 rects per alternative (393: every window fills the work area) ── */

const R = {
  A: { drawer: { x: 150, y: 44, w: 930, h: 560 }, info: { x: 1000, y: 120, w: 400, h: 470 }, list: { x: 150, y: 44, w: 980, h: 700 },
       hand: { x: 150, y: 44, w: 930, h: 600 }, conductor: { x: 150, y: 60, w: 640, h: 330 }, lane: { x: 520, y: 40, w: 900, h: 740 }, needs: { x: 300, y: 50, w: 860, h: 520 } },
  B: { back: { x: 250, y: 44, w: 760, h: 520 }, front: { x: 560, y: 100, w: 820, h: 560 }, tray: { x: 244, y: 40, w: 1180, h: 610 },
       lane: { x: 244, y: 40, w: 1184, h: 610 } },
  C: { info: { x: 960, y: 130, w: 420, h: 470 }, lane: { x: 430, y: 40, w: 990, h: 740 }, needs: { x: 520, y: 44, w: 880, h: 620 } },
};

/* ── A "Workbench" ───────────────────────────────────────────────────── */

const A_FREE: [Obj, number, number][] = [
  [PROJECTS[0], 20, 12], [PROJECTS[1], 20, 124], [PROJECTS[2], 20, 236], [PEOPLE, 20, 348], [CONDUCTOR, 20, 460],
  [NEEDS, 1300, 12], [PARKED, 1300, 660],
  [DRAWER[0], 210, 24], [LOOSE[0], 330, 24], [LOOSE[1], 450, 24], [LOOSE[2], 570, 24], [DRAWER[11], 690, 24],
  [{ id: "d-otel", name: "Adopt OpenTelemetry", kind: "decision", when: TODAY, where: "", tone: "due" }, 810, 24],
  [DRAWER[13], 210, 140], [DRAWER[15], 330, 140], [AG_RUNBOOK, 1170, 12],
];

function ScreenA() {
  useP();
  const compact = useCompactViewport();
  const m = P.moment;
  const selFree = m === 1 ? "p-ledger" : null;
  const drop = m === 3 ? "conductor" : undefined;
  const all = A_FREE.map(([o]) => o);
  return (<>
    <div className="p14-screen" data-testid="p14-screen" data-alt="A" aria-label="Workbench screen" data-covered={m > 1 ? "true" : undefined}>
      <div className="p14-a-free">
        {A_FREE.map(([o, x, y]) => (
          <Icon key={o.id} o={o} className="p14-a-icon" style={{ left: x, top: y }} sel={selFree === o.id || (m === 2 && o.id === "p-ledger") || (m === 4 && o.id === "conductor") || (m === 5 && o.id === "needs-you")}
            drop={drop === o.id} />
        ))}
      </div>
      <div className="p14-a-grid">{all.map((o) => <Icon key={o.id} o={o} sel={selFree === o.id} />)}</div>
    </div>
    {m === 3 && !compact ? <><DragPath d="M 840 250 C 660 360, 320 500, 112 512" /><Ghost o={HANDEE} x={62} y={486} /></> : null}
    {m === 2 ? <DrawerA /> : null}
    {m === 2 && P.view === "icons" && !compact ? <InfoA /> : null}
    {m === 3 ? <HandA /> : null}
    {m === 4 ? <><ConductorA /><LaneWin rect={R.A.lane} shape="rail" /></> : null}
    {m === 5 ? <NeedsWin rect={R.A.needs} /> : null}
  </>);
}

function DrawerA() {
  useP();
  const compact = useCompactViewport();
  const list = P.view === "list" || compact;
  return (
    <Win id="p14:drawer" title={LEDGER} icon={PROJECTS[0]} rect={list ? R.A.list : R.A.drawer}
      footer={<SurfaceFooter receipt={<span className="p14-mono">16 OBJECTS · 1 SELECTED</span>} verbs={<>
        <Button dense variant="ghost">Get Info</Button><Button dense variant="secondary">Open</Button></>} />}>
      <DrawerHead view={list ? "list" : "icons"} onView={(v) => { P.view = v as "icons" | "list"; bump(); }} />
      {list ? <ObjectList items={DRAWER} sel={RUNBOOK.id} /> : <IconGrid items={DRAWER} sel={RUNBOOK.id} />}
    </Win>
  );
}
function InfoA() {
  return (
    <Win id="p14:info" title={`Info: ${RUNBOOK.name}`} icon={RUNBOOK} rect={R.A.info}
      footer={<SurfaceFooter verbs={infoVerbs} />}>
      <InfoBody o={RUNBOOK} />
    </Win>
  );
}
function HandA() {
  const compact = useCompactViewport();
  return (
    <Win id="p14:drawer" title={LEDGER} icon={PROJECTS[0]} rect={R.A.hand}
      footer={<SurfaceFooter egress={<EgressChip label="API.ANTHROPIC.COM" scope="cloud" />} />}>
      <DrawerHead view={compact ? "list" : "icons"} onView={() => undefined} />
      <ConfirmLine agent={HAND_AGENT} />
      {compact ? <ObjectList items={DRAWER} sel={HANDEE.id} /> : <IconGrid items={DRAWER} ghost={HANDEE.id} />}
    </Win>
  );
}
function ConductorA() {
  const items = [HAND_AGENT, CODEX_AGENT, AG_RUNBOOK, AG_RECON, AG_FLAG];
  return (
    <Win id="p14:conductor" title="Conductor" icon={CONDUCTOR} rect={R.A.conductor}>
      <IconGrid items={items} sel={AG_RUNBOOK.id} />
    </Win>
  );
}

function LaneWin({ rect, shape }: { rect: { x: number; y: number; w: number; h: number }; shape: "rail" | "cols" | "track" }) {
  return (
    <Win id="p14:lane" title="Claude Code: rollback runbook" icon={AG_RUNBOOK} rect={rect} footer={<LaneFooter />} actions={rawVerb} minW={340}>
      <LaneBody shape={shape} />
    </Win>
  );
}
function NeedsWin({ rect, grouped }: { rect: { x: number; y: number; w: number; h: number }; grouped?: boolean }) {
  return (
    <Win id="p14:needs" title="Needs you" icon={NEEDS} rect={rect}>
      <NeedsBody grouped={grouped} />
    </Win>
  );
}

/* ── B "Bench" ───────────────────────────────────────────────────────── */

function ShelfItem({ o, pressed }: { o: Obj; pressed?: boolean }) {
  return (
    <Button variant="chrome" className="p14-shelf-item" aria-pressed={pressed ? "true" : "false"} aria-label={`${o.name}${o.count ? `, ${o.count} need you` : ""}`}>
      <span className="p14-icon-art" style={{ width: 36, height: 36 }}>
        <img src={sprite(o, pressed ? "sel" : "rest")} alt="" />
        {o.badge ? <img className="p14-icon-badge" style={{ width: 20, height: 20, right: -6 }} src={o.badge} alt="" /> : null}
        <Lamp tone={o.tone} />
      </span>
      <span className="p14-shelf-name">{o.name}</span>
      {o.count ? <span className="p14-shelf-n" aria-hidden="true">{o.count}</span> : <span />}
    </Button>
  );
}

function Shelf({ open }: { open?: string }) {
  return (
    <nav className="p14-shelf" aria-label="Shelf" data-testid="p14-shelf">
      <span className="p14-shelf-cap">Drawers</span>
      {PROJECTS.map((o) => <ShelfItem key={o.id} o={o} pressed={open === o.id} />)}
      <span className="p14-shelf-cap">Smart</span>
      <ShelfItem o={NEEDS} pressed={open === "needs-you"} />
      <ShelfItem o={{ id: "today", name: "Today", kind: "smart", when: "", where: "", count: 0 }} />
      <span className="p14-shelf-cap">Desk</span>
      <ShelfItem o={PEOPLE} />
      <ShelfItem o={{ id: "loose", name: "Loose objects", kind: "smart", when: "", where: "" }} />
      <ShelfItem o={PARKED} />
    </nav>
  );
}

function Bay({ o, item, lamp, tone, pressed, drop, free }: { o: Obj; item: string; lamp?: string; tone?: Tone; pressed?: boolean; drop?: boolean; free?: boolean }) {
  return (
    <Button variant="chrome" className="p14-bay" aria-pressed={pressed ? "true" : "false"} data-drop={drop ? "true" : undefined} data-free={free ? "true" : undefined}
      aria-label={`${o.name}: ${item}${lamp ? `, ${lamp}` : ""}`} data-testid={`p14-bay-${o.id}`}>
      <span className="p14-icon-art"><img src={sprite(o, pressed || drop ? "sel" : "rest")} alt="" /><Lamp tone={tone} /></span>
      <span className="p14-bay-agent">{o.name.split(":")[0]}</span>
      <span className="p14-bay-item">{item}</span>
      {lamp ? <LampGadget label={lamp} on tone={LAMP_TONE[tone ?? "ok"]} /> : <span />}
    </Button>
  );
}

function Pit({ pressed, drop, confirm }: { pressed?: string; drop?: boolean; confirm?: boolean }) {
  return (
    <section className="p14-pit" aria-label="Conductor" data-testid="p14-pit">
      <div className="p14-pit-name"><strong>Conductor</strong><span className="p14-mono" style={{ color: "var(--wb-ink)" }}>3 AT WORK</span></div>
      {confirm ? <div className="p14-pit-confirm"><ConfirmLine agent={HAND_AGENT} /></div> : (<>
        <Bay o={AG_RUNBOOK} item={RUNBOOK.name} lamp="ASKS" tone="ask" pressed={pressed === AG_RUNBOOK.id} />
        <Bay o={AG_RECON} item={RECON.name} lamp="WORKS" tone="work" />
        <Bay o={AG_FLAG} item={FLAG.name} lamp="PR #412" tone="ok" />
        <Bay o={HAND_AGENT} item={drop ? "Drop to hand" : "Hand"} free drop={drop} />
      </>)}
    </section>
  );
}

function TrayBody({ sel, ghost }: { sel?: string; ghost?: string }) {
  return (<>
    <DrawerHead view="icons" onView={() => undefined} />
    <div>
      {DRAWER_GROUPS.map(([label, kinds]) => (
        <div key={label} className="p14-shelfrow">
          <span className="p14-caption">{label}</span>
          <IconGrid items={DRAWER.filter((o) => kinds.includes(o.kind))} sel={sel} ghost={ghost} />
        </div>
      ))}
    </div>
  </>);
}

function ScreenB() {
  useP();
  const m = P.moment;
  const compact = useCompactViewport();
  return (<>
    <div className="p14-screen" data-testid="p14-screen" data-alt="B" aria-label="Bench" data-covered={m > 1 ? "true" : undefined}>
      <Shelf open={m === 2 || m === 3 ? "p-ledger" : m === 5 ? "needs-you" : undefined} />
      <div className="p14-bench" aria-hidden={compact ? undefined : "true"}>
        {compact ? <div className="p14-a-grid" style={{ display: "grid" }}>{LOOSE.map((o) => <Icon key={o.id} o={o} />)}</div> : null}
      </div>
      <Pit pressed={m === 4 ? AG_RUNBOOK.id : undefined} drop={m === 3 && !compact} />
      {m === 3 && !compact ? <div className="p14-pit-above" data-testid="p14-pit-confirm"><ConfirmLine agent={HAND_AGENT} /></div> : null}
    </div>
    {m === 3 && !compact ? <><DragPath d="M 806 450 C 900 620, 1150 660, 1292 770" /><Ghost o={HANDEE} x={1262} y={742} /></> : null}
    {m === 1 && !compact ? <>
      <Win id="p14:drawer" title={LEDGER} icon={PROJECTS[0]} rect={R.B.back}><TrayBody /></Win>
      <NeedsWin rect={R.B.front} grouped />
    </> : null}
    {m === 2 ? <TrayB /> : null}
    {m === 3 ? (
      <Win id="p14:drawer" title={LEDGER} icon={PROJECTS[0]} rect={{ ...R.B.tray, h: 570 }}
        footer={compact ? undefined : <SurfaceFooter egress={<EgressChip label="API.ANTHROPIC.COM" scope="cloud" />} />}>
        {compact ? <><ConfirmLine agent={HAND_AGENT} /><ObjectList items={DRAWER} sel={HANDEE.id} /></> : <TrayBody ghost={HANDEE.id} />}
      </Win>
    ) : null}
    {m === 4 ? <LaneWin rect={R.B.lane} shape="cols" /> : null}
    {m === 5 ? <NeedsWin rect={R.B.tray} grouped /> : null}
  </>);
}

function TrayB() {
  const compact = useCompactViewport();
  return (
    <Win id="p14:drawer" title={LEDGER} icon={PROJECTS[0]} rect={R.B.tray}
      footer={<SurfaceFooter receipt={<span className="p14-mono">16 OBJECTS · 1 SELECTED</span>} verbs={<>
        <Button dense variant="ghost">Rename</Button><Button dense variant="ghost">Park</Button><Button dense variant="secondary">Open</Button></>} />}>
      {compact ? <><DrawerHead view="list" onView={() => undefined} /><ObjectList items={DRAWER} sel={RUNBOOK.id} /></> : (
        <div className="p14-tray">
          <div className="p14-tray-main"><TrayBody sel={RUNBOOK.id} /></div>
          <aside className="p14-tray-info" aria-label="Info" data-testid="p14-tray-info"><p className="p14-caption">Info</p><InfoBody o={RUNBOOK} /></aside>
        </div>
      )}
    </Win>
  );
}

/* ── C "Stage" ───────────────────────────────────────────────────────── */

type Placed = [Obj, number, number];
const ZONES: { id: string; name: string; o: Obj; rect: [number, number, number, number]; facts?: string; items: Placed[]; garage?: boolean }[] = [
  { id: "p-ledger", name: LEDGER, o: PROJECTS[0], rect: [16, 12, 820, 500], facts: "3 NEED YOU · NOV 5",
    items: [[DRAWER[0], 10, 4], [DRAWER[1], 130, 4], [RUNBOOK, 250, 4], [RECON, 250, 130], [FLAG, 250, 256], [COMMS, 10, 256],
      [AG_RUNBOOK, 370, 4], [AG_RECON, 370, 130], [AG_FLAG, 370, 256], [PR412, 490, 256], [DRAWER[10], 10, 130], [DRAWER[11], 130, 130],
      [DRAWER[13], 640, 4], [DRAWER[14], 640, 130], [DRAWER[15], 640, 256], [DRAWER[12], 130, 256]] },
  { id: "p-obs", name: "Platform observability", o: PROJECTS[1], rect: [852, 12, 572, 240], facts: "1 NEEDS YOU",
    items: [[{ id: "m-arch", name: "Architecture review: tracing", kind: "meeting", when: day(1), where: "" }, 10, 4],
      [{ id: "d-otel", name: "Adopt OpenTelemetry", kind: "decision", when: day(1), where: "", tone: "due" }, 130, 4],
      [{ id: "m-arch-a1", name: "Pilot OTel in billing", kind: "action", when: day(1), where: "" }, 250, 4]] },
  { id: "p-hiring", name: "Staff hiring loop", o: PROJECTS[2], rect: [852, 268, 572, 244], facts: "1 NEEDS YOU",
    items: [[{ id: "m-hiring", name: "Hiring debrief", kind: "meeting", when: day(3), where: "" }, 10, 4],
      [{ id: "d-ops", name: "Run a second ops interview", kind: "decision", when: day(3), where: "", tone: "due" }, 130, 4]] },
  { id: "desk", name: "Desk", o: { id: "desk", name: "Desk", kind: "smart", when: "", where: "" }, rect: [16, 528, 690, 252],
    items: [[NEEDS, 10, 4], [PEOPLE, 130, 4], [LOOSE[0], 250, 4], [LOOSE[1], 370, 4], [LOOSE[2], 490, 4], [PARKED, 10, 120]] },
  { id: "garage", name: "Conductor", o: CONDUCTOR, rect: [722, 528, 702, 252], facts: "2 READY · 3 OUT", garage: true,
    items: [[HAND_AGENT, 10, 4], [CODEX_AGENT, 130, 4]] },
];

function Zone({ z, sel, drop, children, captions }: { z: typeof ZONES[number]; sel?: string | null; drop?: string; children?: ReactNode; captions?: [string, number, number][] }) {
  const [x, y, w, h] = z.rect;
  return (
    <section className="p14-zone" data-garage={z.garage ? "true" : undefined} aria-label={z.name} style={{ left: x, top: y, width: w, height: h }} data-testid={`p14-zone-${z.id}`}>
      <span className="p14-zone-sign"><img src={sprite(z.o)} alt="" /><span>{z.name}</span>{z.facts ? <span className="p14-fact">· {z.facts}</span> : null}</span>
      {captions?.map(([t, cx, cy]) => <span key={t} className="p14-caption p14-zone-cap" style={{ left: cx, top: cy }}>{t}</span>)}
      <div className="p14-zone-grid">
        {z.items.map(([o, ix, iy]) => <Icon key={o.id} o={o} sel={sel === o.id} drop={drop === o.id} style={{ left: ix + 10, top: iy + 40 }} />)}
      </div>
      {children}
    </section>
  );
}

/** Trails: where each agent walked from the garage (screen coordinates, 1440 only). */
function Trails({ extra }: { extra?: boolean }) {
  return (
    <svg className="p14-trail" aria-hidden="true" data-testid="p14-trails">
      {extra ? <path d="M 120 420 C 260 470, 640 470, 776 586" style={{ strokeDasharray: "6 4", opacity: 0.9 }} /> : (<>
        <path d="M 790 600 C 700 520, 520 420, 452 96" />
        <path d="M 800 610 C 720 540, 540 470, 452 222" />
        <path d="M 810 620 C 740 560, 560 520, 452 348" />
      </>)}
    </svg>
  );
}

function ScreenC() {
  useP();
  const m = P.moment;
  const compact = useCompactViewport();
  if (m === 2) return <StageZoom />;
  return (<>
    <div className="p14-screen" data-testid="p14-screen" data-alt="C" aria-label="Stage" data-covered={m > 3 ? "true" : undefined}>
      <div className="p14-stage">
        {ZONES.map((z) => (
          <Zone key={z.id} z={z} sel={m === 4 ? AG_RUNBOOK.id : m === 5 ? "needs-you" : null} drop={m === 3 ? HAND_AGENT.id : undefined}>
            {m === 3 && z.id === "garage" ? (
              <div className="p14-zone-inline" style={{ left: 10, right: 10, bottom: 10 }}><ConfirmLine agent={HAND_AGENT} /></div>
            ) : null}
          </Zone>
        ))}
        {!compact ? <Trails extra={m === 3} /> : null}
      </div>
    </div>
    {m === 3 && !compact ? <Ghost o={HANDEE} x={764} y={570} /> : null}
    {m === 4 ? <LaneWin rect={R.C.lane} shape="track" /> : null}
    {m === 5 ? <NeedsWin rect={R.C.needs} /> : null}
  </>);
}

/** C moment 2: the drawer opens by entering its place: the zone fills the stage. */
function StageZoom() {
  useP();
  const compact = useCompactViewport();
  const z = ZONES[0];
  const big: typeof z = { ...z, rect: [16, 12, 1408, 768], facts: "3 NEED YOU · CUTOVER NOV 5 · ON TRACK · 16 OBJECTS",
    items: [
      [DRAWER[0], 20, 30], [DRAWER[1], 160, 30], [DRAWER[10], 20, 170], [DRAWER[11], 160, 170], [DRAWER[12], 300, 170],
      [RUNBOOK, 460, 30], [RECON, 460, 170], [FLAG, 460, 310], [COMMS, 460, 450],
      [AG_RUNBOOK, 600, 30], [AG_RECON, 600, 170], [AG_FLAG, 600, 310], [PR412, 740, 310],
      [DRAWER[13], 20, 450], [DRAWER[14], 160, 450], [DRAWER[15], 300, 450]] };
  return (<>
    <div className="p14-screen" data-testid="p14-screen" data-alt="C" aria-label="Stage" data-covered="true">
      <div className="p14-stage">
        {compact ? null : <Zone z={big} sel={RUNBOOK.id} captions={[["Meetings, decisions", 30, 50], ["Notes, files", 30, 190], ["Action items", 470, 50], ["Agents at work", 610, 50], ["Repository, people", 30, 470]]} />}
      </div>
    </div>
    {compact ? (
      <Win id="p14:drawer" title={LEDGER} icon={PROJECTS[0]} rect={R.A.list}
        footer={<SurfaceFooter verbs={<><Button dense variant="ghost">Get Info</Button><Button dense variant="secondary">Open</Button></>} />}>
        <DrawerHead view="list" onView={() => undefined} />
        <ObjectList items={DRAWER} sel={RUNBOOK.id} />
      </Win>
    ) : (
      <Win id="p14:info" title={`Info: ${RUNBOOK.name}`} icon={RUNBOOK} rect={R.C.info} footer={<SurfaceFooter verbs={infoVerbs} />}>
        <InfoBody o={RUNBOOK} />
      </Win>
    )}
  </>);
}

/* ── the gate (the one seat) ─────────────────────────────────────────── */

function Gate({ chair }: { chair: ReactNode }) {
  useP();
  if (!P.alt) return <>{chair}</>;
  return P.alt === "A" ? <ScreenA /> : P.alt === "B" ? <ScreenB /> : <ScreenC />;
}
G.__pScreen = (chair: ReactNode) => <Gate chair={chair} />;

G.__p = {
  set: (next: Partial<typeof P>) => { Object.assign(P, next); bump(); },
  state: () => ({ alt: P.alt, moment: P.moment, view: P.view }),
  reset: () => { P.alt = null; P.moment = 1; P.view = "icons"; P.sel = null; P.answer = ""; bump(); },
};
