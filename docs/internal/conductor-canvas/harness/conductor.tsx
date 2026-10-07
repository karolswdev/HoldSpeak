/* The Conductor canvas: the faces of docs/internal/CONDUCTOR.md ("F faces"), drawn on the
 * REAL product as it is on main.
 *
 * Loaded only in CANVAS_MODE=proposal. Every seat (seats.mjs) calls one `globalThis.__k*`
 * function defined here. The build moves each piece into the named product file.
 *
 * WHAT IS REAL: the hub (an isolated HOME), the Chair, Needs you, the Room, the Floor list,
 * the menus, the ⌘K deck, the session window and its steer composer, the first-run face;
 * the two agent sessions (the product's own hook ingest wrote them: Claude Code waiting with
 * a question, Codex working); the Project, the action item, the decision, the people.
 *
 * THE PROPOSAL (Q-numbered as in ../README.md):
 *   Q1 First run: an Agents card after Connections. One row per agent (Claude Code, Codex)
 *      with the lamps INSTALLED / SIGNED IN / HOOKS and the verb `Install hooks`; a tmux row;
 *      done folds the card to its receipt. Not installed: tokens + `Copy install` + `Check again`.
 *   Q2 `Hand to agent`: one registry verb (verbRegistry.ts VERBS, scope object) -> the Object
 *      menu, the object context menu and the ⌘K deck at once; and a row verb on Door rows
 *      (action item, decision) and Room rows (action item, issue).
 *   Q3 The launch sheet: a docked desk window (the Ask AI posture, never a modal): agent
 *      picker, the brief's sources + bytes, PEOPLE CUT, the worktree and branch, the Control
 *      mode chip (it unfolds the mapping well, QC), egress chip naming the cloud agent's host
 *      on the Launch footer, verbs Cancel / Launch.
 *   Q4 In flight: the item wears `<AGENT> · WORKING | WAITING | PR OPEN | MERGED` where it
 *      lives (the Door row, the Room's OPEN HERE row); the session row in AGENTS names its item.
 *   Q5 Needs you coder row (R5): the waiting agent's question, agent, project, age;
 *      `Speak answer` opens the session window with the steer composer already recording;
 *      `Open`. Enter sends in the steer composer.
 *   Q6 Follow-through: on merge the commitment closes with the PR as evidence: it leaves
 *      OPEN HERE and the Room's receipt line names it.
 *   QC The Control-mode mapping (CONDUCTOR.md), as tokens, for the owner's ruling.
 *   Q7 (R7, DRAFT) Settings > People: People MCP access as one FilterTokens strip OFF / READ /
 *      WRITE, the tokens AGENTS · READ (or AGENTS · NONE) and the source (DEFAULT / SETTING /
 *      ENV); a People row on the Settings hub (MCP · WRITE, AGENTS · READ). The read and the
 *      press are the REAL routes (GET / PUT /api/settings/people-access on this branch).
 *
 * STAND-INS (named, so no board claims more than it shows):
 *   S1 agent detection (claude / codex / tmux, versions, sign-in, hooks) is answered here;
 *      the route is K1's (`agents_detect`). `Install hooks` writes nothing.
 *   S2 `Launch` spawns nothing: the launch record lives in this shim; nothing leaves the machine.
 *   S3 the brief's sources, bytes and the PEOPLE CUT count are composed here from the seeded
 *      records (K2 builds `compose_agent_brief`).
 *   S4 two GitHub issues (#418, #421) are added to the Room's OPEN HERE read; PR #412 and
 *      #413 are canvas numbers. The rig sets every agent state (__k.set).
 *   S5 the steer POST is answered `delivered` here: no text reaches an agent.
 *   S6 the steer mic draws its listening state; no audio is captured.
 *   S7 the session -> item link (origin_ref, K2) is held here by title.
 *   S8 (Q7) Settings has no People module on main: this shim adds the module and its hub row
 *      (PREF_MODULES and the hub ledger, seats.mjs). The control itself calls the real route.
 */
import { useEffect, useState, useSyncExternalStore, type ReactNode } from "react";
import { Button } from "@w/components/signal/Signal";
import {
  ChoiceCard,
  ChoiceCardGroup,
  Disclosure,
  EgressChip,
  ProjectButton,
  StateChip,
  SurfaceFooter,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceSection,
} from "@w/desk/surface";
import { Card } from "@w/desk/firstrun/Card";
import { DeskWindowFrame } from "@w/desk/components/DeskWindow";
import { VERBS, type VerbContext } from "@w/desk/verbRegistry";
import { useDesk } from "@w/desk/store";
import { objectByRef } from "@w/desk/world";
import { openCoderSession, openProjectRoom } from "@w/desk/shell";
import { authenticatedHeaders } from "@w/lib/auth";
import { refreshNeedsYou } from "@w/desk/needsYou";
import { useSteering } from "@w/desk/steering";
import { FilterTokens, GadgetGroup, GadgetRow } from "@w/desk/surface";

type AnyRec = Record<string, any>;
const G = globalThis as any;

/* ── the shim's store ─────────────────────────────────────────────────── */

type Agent = "claude" | "codex";
type Flight = "working" | "waiting" | "pr_open" | "merged";
type Launch = { agent: Agent; state: Flight; pr?: number; session?: string; at: string };
type Origin = { title: string; kind: "action item" | "decision" | "issue" | "note"; project: string; projectId: string };
type AgentsMode = "found" | "installing" | "done" | "missing";

const AGENT_NAME: Record<Agent, string> = { claude: "Claude Code", codex: "Codex" };
const AGENT_HOST: Record<Agent, string> = { claude: "API.ANTHROPIC.COM", codex: "API.OPENAI.COM" };
const FLIGHT_WORD: Record<Flight, string> = { working: "WORKING", waiting: "WAITING", pr_open: "PR OPEN", merged: "MERGED" };
const FLIGHT_CHIP: Record<Flight, "working" | "warning" | "active" | "success"> = { working: "working", waiting: "warning", pr_open: "active", merged: "success" };

const S = {
  tick: 0,
  subs: new Set<() => void>(),
  agents: "found" as AgentsMode,
  launches: new Map<string, Launch>(),
  sheet: null as null | { origin: Origin; agent: Agent; control: boolean; brief: boolean },
  coderRow: false,
  steerOpen: false,
  micListen: false,
  coders: [] as AnyRec[],
  closed: null as null | { title: string; pr: number; at: string },
};
const bump = () => { S.tick++; S.subs.forEach((f) => f()); };
const useK = () => useSyncExternalStore((f) => { S.subs.add(f); return () => S.subs.delete(f); }, () => S.tick);
const clock = () => { const d = new Date(); return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`; };

/* ── fetch shim (S4, S5) ──────────────────────────────────────────────── */

const realFetch = window.fetch.bind(window);
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
const ISSUES = [
  { source: "github", kind: "issue", title: "#418 Reconciliation job slow on month-end data", why: "ISSUE · OPEN 2 D", severity: "info", url: "https://github.com/acme/payments-ledger/issues/418", since: "" },
  { source: "github", kind: "issue", title: "#421 Add the ledger freeze flag", why: "ISSUE · OPEN 1 D", severity: "info", url: "https://github.com/acme/payments-ledger/issues/421", since: "" },
];
async function shimFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const url = new URL(typeof input === "string" ? input : input instanceof URL ? input.href : input.url, location.origin);
  const method = (init?.method || (input instanceof Request ? input.method : "GET")).toUpperCase();
  if (method === "GET" && url.pathname === "/api/projects/p-ledger/room") {
    const res = await realFetch(input as RequestInfo, init);
    if (!res.ok) return res;
    const body = await res.json();
    const ny = body?.needsYou;
    if (ny && Array.isArray(ny.items)) {
      const closed = [...S.launches.entries()].filter(([, l]) => l.state === "merged").map(([t]) => t);
      ny.items = [...ny.items.filter((it: AnyRec) => !closed.includes(String(it.title))), ...ISSUES];
      ny.count = ny.items.length;
    }
    return json(body);
  }
  const steer = /^\/api\/coders\/([^/]+)\/steer$/.exec(url.pathname);
  if (method === "POST" && steer) {
    G.__kSteered = JSON.parse(String(init?.body || "{}"));
    return json({ status: "delivered", detail: "delivered", pane_id: "%7" });
  }
  return realFetch(input as RequestInfo, init);
}
window.fetch = shimFetch as typeof window.fetch;

async function readCoders(): Promise<void> {
  try {
    const res = await realFetch("/api/coders/sessions", { headers: Object.fromEntries(new Headers(authenticatedHeaders() as HeadersInit).entries()) });
    if (res.ok) { S.coders = ((await res.json()).sessions ?? []) as AnyRec[]; bump(); void refreshNeedsYou(true); }
  } catch { /* the rig reads again */ }
}

/* ── S7: the session -> item link ─────────────────────────────────────── */
const SESSION_OF: Record<string, string> = {
  "claude:c1a0de00-runbook": "Write the rollback runbook",
  "codex:c0dex000-recon": "#418 Reconciliation job slow on month-end data",
};
const ORIGINS: Record<string, Origin> = {
  "Write the rollback runbook": { title: "Write the rollback runbook", kind: "action item", project: "Payments ledger cutover", projectId: "p-ledger" },
  "Freeze the old ledger on Nov 5": { title: "Freeze the old ledger on Nov 5", kind: "decision", project: "Payments ledger cutover", projectId: "p-ledger" },
  "#418 Reconciliation job slow on month-end data": { title: "#418 Reconciliation job slow on month-end data", kind: "issue", project: "Payments ledger cutover", projectId: "p-ledger" },
  "#421 Add the ledger freeze flag": { title: "#421 Add the ledger freeze flag", kind: "issue", project: "Payments ledger cutover", projectId: "p-ledger" },
};
const originOf = (title: string, kind: Origin["kind"] = "action item"): Origin =>
  ORIGINS[title] ?? { title, kind, project: "Payments ledger cutover", projectId: "p-ledger" };

function handToAgent(origin: Origin) {
  S.sheet = { origin, agent: "claude", control: false, brief: false };
  bump();
  window.setTimeout(() => useDesk.getState().focusPanel("agent-hand"), 50);
}

/* ── Q2: the registry verb (Object menu, object context menu, ⌘K) ─────── */

const HANDABLE = new Set(["decision", "note"]);
function selectedObj(ctx: VerbContext) {
  return ctx.selectedRef ? objectByRef(useDesk.getState().items, ctx.selectedRef) : null;
}
const at = VERBS.findIndex((v) => v.id === "object.ask");
VERBS.splice(at + 1, 0, {
  id: "object.hand-to-agent",
  label: "Hand to agent",
  menu: "object",
  scope: "object",
  glyph: "⇥",
  keywords: ["agent", "claude", "codex", "coder", "launch", "delegate"],
  ghost: (ctx) => {
    const o = selectedObj(ctx);
    if (!o) return "Select an object";
    return HANDABLE.has(o.kind) ? null : "Not a work item";
  },
  run: (ctx) => {
    const o = selectedObj(ctx);
    if (!o || !HANDABLE.has(o.kind)) return;
    handToAgent(originOf(String(o.title), o.kind === "decision" ? "decision" : "note"));
  },
});

/* ── Q1: the first-run Agents card ────────────────────────────────────── */

const DETECT = {
  claude: { tool: "claude", version: "2.1.4", glyph: "CC", install: "npm i -g @anthropic-ai/claude-code" },
  codex: { tool: "codex", version: "0.46.0", glyph: "CX", install: "npm i -g @openai/codex" },
};
function Lamp({ on, label }: { on: boolean; label: string }) {
  return <StateChip state={on ? "success" : "idle"} label={label} icon={on ? "●" : "○"} />;
}
function AgentsCard() {
  useK();
  const mode = S.agents;
  const hooked = mode === "done";
  if (mode === "done") {
    return (
      <Card title="Agents" testId="firstrun-agents" selected
        state={<StateChip state="success" label="2 AGENTS READY" icon="●" />}>
        <span className="k-tokens" data-testid="k-agents-receipt">
          <span className="surface-token" data-chip>CLAUDE CODE · HOOKS IN</span>
          <span className="surface-token" data-chip>CODEX · HOOKS IN</span>
          <span className="surface-token" data-chip>TMUX 3.5A</span>
        </span>
      </Card>
    );
  }
  const missing = mode === "missing";
  return (
    <Card title="Agents" testId="firstrun-agents"
      state={missing ? <StateChip state="idle" label="NO AGENT FOUND" /> : <StateChip state="success" label="2 FOUND" icon="●" />}>
      <ul className="concierge-found-list firstrun-ledger" aria-label="Found agents">
        {(["claude", "codex"] as Agent[]).map((a) => (
          <SurfaceLedgerRow
            key={a}
            lead={<span className="concierge-group-glyph">{DETECT[a].glyph}</span>}
            primary={<span className="concierge-group-name">{AGENT_NAME[a]}</span>}
            cells={
              <span className="k-tokens k-agent-cells" data-testid="k-agent-row" data-agent={a}>
                {missing ? (
                  <>
                    <span className="surface-token" data-chip>{DETECT[a].tool.toUpperCase()} NOT INSTALLED</span>
                    <Button dense variant="secondary" aria-label={`Copy install: ${AGENT_NAME[a]}`}
                      onClick={() => void navigator.clipboard?.writeText(DETECT[a].install).catch(() => {})}>Copy install</Button>
                  </>
                ) : (
                  <>
                    <span className="surface-token k-literal" data-chip>{DETECT[a].tool} {DETECT[a].version}</span>
                    <Lamp on label="INSTALLED" />
                    <Lamp on label="SIGNED IN" />
                    <Lamp on={hooked} label="HOOKS" />
                  </>
                )}
              </span>
            }
            expands={false}
            wrap
          />
        ))}
        <SurfaceLedgerRow
          lead={<span className="concierge-group-glyph">TM</span>}
          primary={<span className="concierge-group-name">tmux</span>}
          cells={
            <span className="k-tokens k-agent-cells" data-testid="k-agent-row" data-agent="tmux">
              {missing ? <span className="surface-token" data-chip>TMUX NOT INSTALLED</span> : (
                <>
                  <span className="surface-token k-literal" data-chip>tmux 3.5a</span>
                  <Lamp on label="INSTALLED" />
                </>
              )}
            </span>
          }
          expands={false}
          wrap
        />
      </ul>
      <span className="k-agents-foot">
        {missing ? (
          <Button dense variant="secondary" data-testid="k-check-again" onClick={() => { bump(); }}>Check again</Button>
        ) : (
          <>
            <EgressChip label="THIS DEVICE" scope="local" />
            <Button dense variant="secondary" loading={mode === "installing"} disabled={mode === "installing"}
              aria-label="Install hooks: Claude Code and Codex"
              onClick={() => { S.agents = "installing"; bump(); window.setTimeout(() => { S.agents = "done"; bump(); }, 900); }}>
              Install hooks
            </Button>
          </>
        )}
      </span>
    </Card>
  );
}
G.__kFirstRun = () => (
  <div className="firstrun-cards k-agents-cards" data-testid="k-agents-slot"><AgentsCard /></div>
);

/* ── Q3 + QC: the launch sheet ────────────────────────────────────────── */

const MODES: { mode: string; launch: string; bash: string; question: string; real?: string }[] = [
  { mode: "SECURE", launch: "YOU PRESS LAUNCH", bash: "EVERY CALL WAITS", question: "TO NEEDS YOU" },
  { mode: "NORMAL", launch: "ON THE VERB", bash: "READ · TEST · GIT READ PASS", question: "DRAFT · YOU SEND" },
  { mode: "YOLO", launch: "ON THE VERB", bash: "PASS IN ITS WORKTREE", question: "ROUTINE ANSWERED", real: "TO NEEDS YOU" },
];
const CURRENT_MODE = "YOLO";

function briefSources(o: Origin): { lead: string; name: string; fact: string }[] {
  return [
    { lead: o.kind === "decision" ? "DEC" : o.kind === "issue" ? "GH" : "ACT", name: o.title, fact: o.kind.toUpperCase() },
    { lead: "MTG", name: "Ledger cutover sync", fact: "1 QUOTE" },
    { lead: "DEC", name: "Freeze the old ledger on Nov 5", fact: "ACCEPTED" },
    { lead: "RM", name: o.project, fact: "3 OPEN" },
    { lead: "MEM", name: "Memory pages", fact: "2 PAGES" },
    { lead: ".HS", name: "payments-ledger", fact: "4 FACTS" },
  ];
}
const slug = (t: string) => t.toLowerCase().replace(/^#\d+\s*/, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 32);

function LaunchSheet() {
  useK();
  const sh = S.sheet;
  if (!sh) return null;
  const o = sh.origin;
  const src = briefSources(o);
  const close = () => { S.sheet = null; bump(); };
  const launch = () => {
    S.launches.set(o.title, { agent: sh.agent, state: "working", at: clock() });
    S.sheet = null;
    bump();
  };
  return (
    <DeskWindowFrame
      id="agent-hand"
      glyph="⇥"
      label="Hand to agent"
      kindWord="Agent launch"
      className="desk-pullout k-hand"
      defaultW={560}
      defaultH={660}
      icon={<span className="desk-ask-glyph" aria-hidden="true">⇥</span>}
      title={o.title}
      open
      onClose={close}
    >
      <div className="desk-pullout-body k-hand-body" data-testid="k-launch-sheet">
        <SurfaceSection label="AGENT">
          <ChoiceCardGroup name="k-agent" value={sh.agent} layout="row" ariaLabel="Agent"
            onChange={(v) => { sh.agent = v as Agent; bump(); }}>
            <ChoiceCard name="k-agent" selectedValue={sh.agent} onChange={(v) => { sh.agent = v as Agent; bump(); }} value="claude" label="Claude Code" summary={<span className="surface-token" data-chip>HOOKS IN · 2.1.4</span>} />
            <ChoiceCard name="k-agent" selectedValue={sh.agent} onChange={(v) => { sh.agent = v as Agent; bump(); }} value="codex" label="Codex" summary={<span className="surface-token" data-chip>HOOKS IN · 0.46.0</span>} />
          </ChoiceCardGroup>
        </SurfaceSection>
        <SurfaceSection label={`BRIEF · ${src.length} SOURCES · 4.2 KB`}>
          <SurfaceLedger count={null} cols="room">
            {src.map((s) => (
              <SurfaceLedgerRow key={s.lead + s.name} lead={<span className="k-lead">{s.lead}</span>}
                primary={s.name} cells={<span className="surface-token" data-chip>{s.fact}</span>} expands={false} wrap />
            ))}
          </SurfaceLedger>
          <span className="k-tokens" data-testid="k-brief-tokens">
            <span className="surface-token" data-chip>PEOPLE CUT · 3 NAMES</span>
            <span className="surface-token" data-chip>ACCEPTANCE · 3 CHECKS</span>
          </span>
          <Disclosure label="BRIEF TEXT" open={sh.brief} onOpenChange={(v) => { sh.brief = v; bump(); }}>
            <pre className="desk-pullout-md k-brief-text">{`# ${o.title}\n\nProject: ${o.project}\nFrom: Ledger cutover sync\n> The team agreed to freeze the old ledger on Nov 5.\n> [owner] owns the rollback plan.\n\nDecision: Freeze the old ledger on Nov 5 (accepted)\nControl: ${CURRENT_MODE}\nDone when: the runbook names the rollback steps,\nthe owner and the Nov 12 window; a PR is open.`}</pre>
          </Disclosure>
        </SurfaceSection>
        <SurfaceSection label="WHERE">
          <span className="k-tokens" data-testid="k-where">
            <span className="surface-token k-literal" data-chip>~/dev/payments-ledger</span>
            <span className="surface-token" data-chip>NEW WORKTREE</span>
            <span className="surface-token k-literal" data-chip>hs/{slug(o.title)}</span>
            <Button dense variant="ghost" aria-expanded={sh.control} data-testid="k-control"
              onClick={() => { sh.control = !sh.control; bump(); }}>
              {`CONTROL · ${CURRENT_MODE}`}
            </Button>
          </span>
        </SurfaceSection>
        {sh.control ? (
          <SurfaceSection label="CONTROL MODE · PROPOSED · OWNER RULES" className="k-control-well">
            <div role="region" aria-label="Control mode mapping" data-testid="k-control-board">
              <SurfaceLedger count={null} cols="room">
                {MODES.map((m) => (
                  <SurfaceLedgerRow key={m.mode} lead={<span className="k-lead">{m.mode === CURRENT_MODE ? "✓" : ""}</span>}
                    primary={m.mode} expands={false} wrap
                    cells={
                      <span className="k-tokens">
                        <span className="surface-token" data-chip>LAUNCH · {m.launch}</span>
                        <span className="surface-token" data-chip>BASH · {m.bash}</span>
                        <span className="surface-token" data-chip>QUESTION · {m.question}</span>
                        {m.real ? <span className="surface-token" data-chip>REAL · {m.real}</span> : null}
                      </span>
                    } />
                ))}
              </SurfaceLedger>
            </div>
          </SurfaceSection>
        ) : null}
      </div>
      <SurfaceFooter
        className="k-hand-footer"
        egress={<EgressChip label={AGENT_HOST[sh.agent]} scope="cloud" />}
        receipt={<span className="surface-footer-receipt-line">{AGENT_NAME[sh.agent].toUpperCase()} · {CURRENT_MODE}</span>}
        verbs={<>
          <Button dense variant="ghost" onClick={close}>Cancel</Button>
          <Button dense variant="primary" onClick={launch} data-testid="k-launch">Launch</Button>
        </>}
      />
    </DeskWindowFrame>
  );
}
G.__kDesk = () => <LaunchSheet />;

/* ── Q4: the flight chip; Q2: the row verb ────────────────────────────── */

function FlightChip({ title }: { title: string }) {
  useK();
  const l = S.launches.get(title);
  if (!l) return null;
  // In flight the agent is the fact; once a PR exists, the PR is.
  const label = l.pr && (l.state === "pr_open" || l.state === "merged")
    ? `PR #${l.pr} · ${FLIGHT_WORD[l.state] === "PR OPEN" ? "OPEN" : FLIGHT_WORD[l.state]}`
    : `${AGENT_NAME[l.agent].toUpperCase()} · ${FLIGHT_WORD[l.state]}`;
  return <StateChip state={FLIGHT_CHIP[l.state]} label={label} data-testid="k-flight" />;
}
const PR_URL = (n?: number) => `https://github.com/acme/payments-ledger/pull/${n ?? ""}`;
function RowVerb({ title, kind }: { title: string; kind: Origin["kind"]; url?: string | null }) {
  useK();
  const l = S.launches.get(title);
  if (!l) {
    return (
      <Button dense variant="ghost" aria-label={`Hand to agent: ${title}`} data-testid="k-hand-verb"
        onClick={() => handToAgent(originOf(title, kind))}>Hand to agent</Button>
    );
  }
  if (l.state === "pr_open" || l.state === "merged") {
    return (
      <span className="k-tokens">
        <EgressChip label="GITHUB.COM" scope="cloud" />
        <Button dense variant="ghost" aria-label={`Open PR #${l.pr}: ${title}`} onClick={() => window.open(PR_URL(l.pr), "_blank", "noopener")}>Open PR</Button>
      </span>
    );
  }
  const key = Object.entries(SESSION_OF).find(([, t]) => t === title)?.[0];
  return key ? (
    <Button dense variant="ghost" aria-label={`Open session: ${title}`} onClick={() => openCoderSession(key)}>Session</Button>
  ) : null;
}
const titleOf = (item: AnyRec) => String(item?.title ?? "");
const kindOf = (item: AnyRec): Origin["kind"] | null =>
  ORIGINS[titleOf(item)]?.kind ?? (item?.kind === "issue" ? "issue" : item?.actionItemId ? "action item" : /^(decision|decisions)$/.test(String(item?.source)) ? "decision" : null);

// The Door (ChairHome NeedsYouRow): the chip in the meta line, the verb after the row's own verb.
G.__kRowChip = (item: AnyRec) => <FlightChip title={titleOf(item)} />;
G.__kRowVerb = (item: AnyRec) => {
  const k = kindOf(item);
  return k ? <RowVerb title={titleOf(item)} kind={k} /> : null;
};
// The Room (OPEN HERE): the same chip and verb.
G.__kRoomChip = (item: AnyRec) => <FlightChip title={titleOf(item)} />;
G.__kRoomVerb = (item: AnyRec) => {
  const k = item?.kind === "issue" ? "issue" : item?.actionItemId ? "action item" : null;
  return k ? <RowVerb title={titleOf(item)} kind={k} url={item.url} /> : null;
};
// Q6: the Room's receipt line names the closed commitment and its PR.
function ClosedReceipt() {
  useK();
  if (!S.closed) return null;
  return (
    <span className="surface-footer-receipt-line" data-tone="ok" role="status" data-testid="k-closed-receipt">
      DONE · {S.closed.title} · PR #{S.closed.pr} MERGED · {S.closed.at}
    </span>
  );
}
G.__kRoomReceipt = () => (S.closed ? <ClosedReceipt /> : null);

/* ── Q4: the AGENTS row names its item ────────────────────────────────── */
G.__kAgentCells = (key: string, blocked: boolean) => {
  const title = SESSION_OF[key];
  const l = title ? S.launches.get(title) : null;
  if (!title) return null;
  return (
    <span className="k-agent-cells-pin" style={{ display: "flex", flexWrap: "wrap", justifyContent: "flex-end", gap: 6, width: "100%", minWidth: 0 }}>
      <StateChip state={FLIGHT_CHIP[l?.state ?? (blocked ? "waiting" : "working")]}
        label={`${AGENT_NAME[key.startsWith("codex") ? "codex" : "claude"].toUpperCase()} · ${FLIGHT_WORD[l?.state ?? (blocked ? "waiting" : "working")]}`} />
      <span className="surface-token" data-testid="k-agent-origin" title={title}>↳ {/^#\d+/.test(title) ? `ISSUE ${title.split(" ")[0]}` : title}</span>
    </span>
  );
};

/* ── Q5: the Needs you coder row ──────────────────────────────────────── */

const ageWord = (s: number) => (s < 60 ? "JUST NOW" : s < 3600 ? `${Math.floor(s / 60)} MIN` : `${Math.floor(s / 3600)} H`);
function waiting(): AnyRec[] {
  return S.coders.filter((r) => (r.session?.state ?? r.state) === "waiting" && r.session?.question);
}
function CoderRows({ primary }: { primary: boolean }) {
  useK();
  useEffect(() => { if (S.coderRow && !S.coders.length) void readCoders(); }, []);
  if (!S.coderRow) return null;
  return (
    <>
      {waiting().map((r, i) => {
        const s = r.session;
        const key = `${s.agent}:${s.session_id}`;
        const title = SESSION_OF[key];
        const o = title ? originOf(title) : null;
        const speak = () => { S.steerOpen = true; S.micListen = true; bump(); openCoderSession(key); };
        return (
          <SurfaceLedgerRow
            key={key}
            onToggle={() => openCoderSession(key)}
            lead={<span className="arrival-source-emblem" data-testid="k-coder-emblem">{s.agent === "codex" ? "CX" : "CC"}</span>}
            primary={<span data-testid="k-coder-question">{String(s.question)}</span>}
            cells={
              <span className="arrival-needs-you-meta">
                <span className="arrival-why-token" data-tone="warning">{AGENT_NAME[s.agent as Agent].toUpperCase()} · WAITING · {ageWord(Number(r.age_seconds ?? 0))}</span>
                {o ? <ProjectButton name={o.project} onOpen={() => openProjectRoom(o.projectId)} data-testid="k-coder-project" /> : null}
              </span>
            }
            trailing={
              <>
                <Button dense variant={primary && i === 0 ? "primary" : "ghost"} aria-label={`Speak answer: ${AGENT_NAME[s.agent as Agent]}`}
                  data-testid="k-speak-answer" onClick={speak}>Speak answer</Button>
                <Button dense variant="ghost" aria-label={`Open: ${AGENT_NAME[s.agent as Agent]} session`} onClick={() => openCoderSession(key)}>Open</Button>
              </>
            }
            wrap
            expands={false}
            data-testid="k-coder-row"
          />
        );
      })}
    </>
  );
}
// K3's refetch: every live session, named by its repo (never its folder path).
G.__kAgentSessions = () => (S.coders.length
  ? S.coders.filter((r) => S.launches.get(SESSION_OF[`${r.session?.agent}:${r.session?.session_id}`])?.state !== "merged")   // step 6: a merged launch's session is cleaned up
    .map((r) => ({ ...r, session: { ...r.session, project: r.session?.project_name, awaiting_response: r.session?.state === "waiting" } }))
  : null);
G.__kCoderRows = (muted: boolean) => (muted ? null : <CoderRows primary />);
G.__kCoderFirst = () => S.coderRow && waiting().length > 0;
G.__kCoderCount = () => (S.coderRow ? waiting().length : 0);
G.__kSteerOpen = () => S.steerOpen;
G.__kMicStart = (scope?: string) => S.micListen && String(scope ?? "").startsWith("steer:");

/* The proposal's styles (layout only; every color is a product token). */
const css = document.createElement("style");
css.id = "k-proposal";
css.textContent = `
.k-agents-cards { grid-template-columns: minmax(0, 1fr) !important; }
.k-lamps { display: inline-flex; flex-wrap: wrap; gap: 6px; }
.k-agents-foot { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: flex-end; margin-top: 8px; }
.k-agent-cells { justify-content: flex-end; min-width: 0; }
.k-tokens { display: inline-flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.k-lead { font-family: var(--font-mono); font-size: 12px; letter-spacing: 0.06em; color: var(--text-muted, #9ba2b0); }
.k-answer-well { margin: 8px 0 12px; }
.surface-ledger-row .k-tokens { flex-wrap: wrap; justify-content: flex-end; min-width: 0; max-width: 100%; }
.k-hand-body { padding: 12px 16px; box-sizing: border-box; display: flex; flex-direction: column; gap: 4px; overflow: auto; }
.surface-token.k-ellipsis[data-chip] { display: block; white-space: normal; max-width: 100%; min-width: 0; line-height: 18px; padding-block: 2px; overflow-wrap: anywhere; }
.k-room-cells { justify-content: flex-start !important; }
.k-literal { text-transform: none; letter-spacing: 0; }
.k-brief-text { white-space: pre-wrap; font-size: 12px; }
`;
document.head.appendChild(css);

/* ── Q7 (R7, DRAFT): Settings > People, the People MCP access ──────────── */

type PeopleAccess = { mode: string; effective: string; source: string; agents: string };
const ACCESS: { value: PeopleAccess | null } = { value: null };

async function readAccess(): Promise<void> {
  try {
    const res = await realFetch("/api/settings/people-access", { headers: Object.fromEntries(new Headers(authenticatedHeaders() as HeadersInit).entries()) });
    if (res.ok) { ACCESS.value = (await res.json()) as PeopleAccess; bump(); }
  } catch { /* the rig reads again */ }
}

async function setAccess(mode: string): Promise<void> {
  const headers = { ...Object.fromEntries(new Headers(authenticatedHeaders() as HeadersInit).entries()), "Content-Type": "application/json" };
  const res = await realFetch("/api/settings/people-access", { method: "PUT", headers, body: JSON.stringify({ mode }) });
  if (res.ok) { ACCESS.value = (await res.json()) as PeopleAccess; bump(); }
}

const SOURCE_TOKEN: Record<string, string> = { default: "DEFAULT", config: "SETTING", env: "ENV" };

function PeopleAccessModule() {
  useK();
  useEffect(() => { void readAccess(); }, []);
  const a = ACCESS.value;
  return (
    <GadgetGroup label="MCP access">
      <GadgetRow label="Access">
        <span data-testid="k-people-access">
          <FilterTokens
            label="People MCP access"
            value={a?.mode ?? "write"}
            options={[{ value: "off", label: "OFF" }, { value: "read", label: "READ" }, { value: "write", label: "WRITE" }]}
            onChange={(mode) => void setAccess(mode)}
          />
        </span>
      </GadgetRow>
      <GadgetRow label="Agents">
        <span className="surface-token" data-chip data-testid="k-people-agents">
          {`AGENTS · ${(a?.agents ?? "read").toUpperCase()}`}
        </span>
        <span className="surface-token" data-chip data-muted data-testid="k-people-source">
          {SOURCE_TOKEN[a?.source ?? "default"] ?? "DEFAULT"}
        </span>
      </GadgetRow>
    </GadgetGroup>
  );
}

function PeopleHubRow({ onOpen }: { onOpen(id: string): void }) {
  useK();
  useEffect(() => { if (!ACCESS.value) void readAccess(); }, []);
  const a = ACCESS.value;
  return (
    <SurfaceLedgerRow
      primary="People"
      expands={false}
      onToggle={() => onOpen("people")}
      trailing={<Button variant="ghost" dense onClick={() => onOpen("people")}>Open</Button>}
      cells={<>
        <span className="surface-token" data-chip>{`MCP · ${(a?.effective ?? "write").toUpperCase()}`}</span>
        <span className="surface-token" data-chip>{`AGENTS · ${(a?.agents ?? "read").toUpperCase()}`}</span>
      </>}
    />
  );
}

G.__kPrefModules = () => [{ id: "people", label: "People", glyph: "people", sprite: "system", keys: [] }];
G.__kHubRow = (onOpen: (id: string) => void) => <PeopleHubRow onOpen={onOpen} />;
G.__kSettingsModule = (id: string) => (id === "people" ? <PeopleAccessModule /> : null);

/* ── the rig's hands (the canvas's own state; never a product write) ── */
G.__k = {
  agents: (m: AgentsMode) => { S.agents = m; bump(); },
  set: (title: string, l: Partial<Launch> | null) => {
    if (!l) S.launches.delete(title);
    else S.launches.set(title, { agent: "claude", state: "working", at: clock(), ...(S.launches.get(title) ?? {}), ...l } as Launch);
    bump();
  },
  close: (title: string, pr: number) => { S.closed = { title, pr, at: clock() }; bump(); },
  hand: (title: string, kind: Origin["kind"]) => handToAgent(originOf(title, kind)),
  sheet: (patch: Partial<NonNullable<typeof S.sheet>>) => { if (S.sheet) Object.assign(S.sheet, patch); bump(); },
  coderRow: (on: boolean) => { S.coderRow = on; void readCoders(); bump(); },
  readCoders,
  reset: () => { S.sheet = null; S.steerOpen = false; S.micListen = false; useSteering.getState().closeSession(); bump(); },
  state: () => ({ sheet: S.sheet, launches: Object.fromEntries(S.launches), coders: S.coders.length, steered: G.__kSteered ?? null }),
};
export {};
void (null as unknown as ReactNode);
void useState;
