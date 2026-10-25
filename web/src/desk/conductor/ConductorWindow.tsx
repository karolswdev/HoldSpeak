/** PHILO-14 C4 — the Conductor drawer (ratified board A-4: the Conductor
 *  window, a drawer of agent icons; A-1: the drawer with its count and the
 *  automaton badge on the screen).
 *
 *  The drawer's frame and species (lane A2): the head (`2 AT WORK · 1 ASK`,
 *  `3 OF 3` at the launch cap, never a zero), Icons | List, the body as an
 *  IconGrid of DeskIcons or an ObjectList, the footer with the selection's
 *  verbs. The members are the agents (`members.ts`): ready, live, stale.
 *
 *  This window is where agents live: the Agents application and the
 *  Arrival's AGENTS section fold into it (PROPOSAL §3, Movement C).
 */
import { Fragment, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import {
  EgressChip,
  StatusBar,
  SurfaceState,
  ToolGlyph,
  Toolbar,
  countWords,
  objectSprite,
  type ObjectListRow,
  type ObjectListSort,
  type ObjectListTone,
  type StatusBarItem,
} from "../surface";
import { FootSlotContext } from "../surface/foot";
import { ObjectList } from "../surface/objects/ObjectList";
import { DeskWindowFrame } from "../components/DeskWindow";
import { reviewResult, useAgentFlights } from "../agentFlights";
import { AGENT_HOST, AGENT_INSTALL, AGENT_NAME, needsHooks, type AgentId, type AgentRow } from "../firstrun/agentsStep";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import { useDesk } from "../store";
import { useOnCoderFrame, useOnDeskChanged } from "../useDeskChangedRefresh";
import {
  canRun,
  conductorHead,
  conductorMembers,
  fleetCounts,
  fleetGroups,
  fleetOrder,
  fleetRank,
  fleetWords,
  headWords,
  ownAgentMember,
  reviewWords,
  type ConductorMember,
} from "./members";
import { allowHelper, answerMember, answers, cancelQueuedHand, openMember, resumeAll, stopMember, stops } from "./open";
import { StartAgent } from "./StartAgent";
import { handRefOf, openHand } from "../agentHand";
import { AgentRow as AgentRowFace, DeskAnswerLine } from "../agents/AgentRow";
import { ReviewResult } from "./ReviewResult";
import { openAgentLane } from "../shell";
import { CONDUCTOR_WINDOW_ID, useConductor } from "./store";
import "../drawer/drawer.css";
import "./conductor.css";


/** The reads, live while the window is open. */
function useConductorReads() {
  const state = useConductor();
  useEffect(() => {
    void useConductor.getState().readDetect();
    void useConductor.getState().readFlights();
    void useConductor.getState().readOwnAgents();
  }, []);
  const reread = () => {
    void useConductor.getState().readFlights();
    void useConductor.getState().readOwnAgents();
  };
  useOnCoderFrame(reread);
  useOnDeskChanged(reread);
  return state;
}

/** The receipt of a selected member: its Stop, its hooks install that the
 *  hub refused (with Retry), or a stale launch's close. */
export function MemberReceipt({ member }: { member: ConductorMember | null }) {
  const stop = useConductor((s) => (member ? s.stops[member.ref] : undefined));
  const failure = useConductor((s) => s.installFailure);
  const failedFor = useConductor((s) => s.installFailedAgent);
  const installing = useConductor((s) => s.installing);
  const done = useConductor((s) => s.installDone);
  if (failure && failedFor && (member?.detect ? failedFor === member.detect.id : !member)) {
    const agent = failedFor;
    return (
      <span className="drawer-receipt cw-receipt" data-tone="fail" role="status" data-testid="conductor-install-failed">
        NOT CONNECTED · {failure}
        <Button dense variant="ghost" loading={installing === agent} onClick={() => void useConductor.getState().installHooks(agent)}>
          Retry
        </Button>
      </span>
    );
  }
  if (stop) {
    return (
      <span className="drawer-receipt cw-receipt" data-tone={stop.tone === "ok" ? undefined : "fail"} role="status" data-testid="conductor-stop-receipt">
        {stop.word} · {stop.text}
      </span>
    );
  }
  if (member?.receipt) {
    return <span className="drawer-receipt cw-receipt" data-testid="conductor-receipt">{member.receipt}</span>;
  }
  // PHILO-15 B35: the install's receipt, beside the agent it installed (or
  // with nothing selected, where the row verb was pressed).
  if (done && (!member || member.detect?.id === done.agent)) {
    return (
      <span className="drawer-receipt cw-receipt" role="status" data-testid="conductor-install-done">
        CONNECTED · {AGENT_NAME[done.agent].toUpperCase()} · {done.at}
      </span>
    );
  }
  return null;
}

/** PHILO-17 U32: where Connect is offered (the selected agent, or with
 *  nothing selected any agent), one plain line in the body says why. */
export function HooksLine({ member }: { member: ConductorMember | null }) {
  const agents = useConductor((s) => s.detect?.agents);
  const offered = member ? Boolean(member.detect && needsHooks(member.detect)) : (agents ?? []).some(needsHooks);
  if (!offered) return null;
  return (
    <span className="kit-pill cw-hooks-line" data-tone="info" data-dot="" data-testid="conductor-hooks-line">
      {HOOKS_LINE}
    </span>
  );
}

/* Betterment AG1: InstallHooksVerbs (unused) is parked in
 * desk/_parked/agents/InstallHooksVerbs.tsx. */

/** The verbs of one selected member (every verb names what it does). The
 *  Stop confirmation REPLACES the verb row (it is the only question then),
 *  and it is bound to the member pressed, whatever is selected after. */
export function MemberVerbs({ member, onInfo, trim = false }: {
  member: ConductorMember | null;
  onInfo?: () => void;
  /** PHILO-17: in the Conductor's foot, the row verbs (Answer, Open,
   *  Install hooks, Copy install) stay on their rows; the foot keeps the
   *  quiet ones (Get Info, Stop). The Get Info window passes nothing. */
  trim?: boolean;
}) {
  const installing = useConductor((s) => s.installing);
  const { copy, receipt } = useCopyReceipt();
  const [confirmFor, setConfirmFor] = useState<ConductorMember | null>(null);
  const [stopping, setStopping] = useState(false);
  useEffect(() => {
    if (!stopping) setConfirmFor((now) => (now && now.id !== member?.id ? null : now));
  }, [member?.id, stopping]);
  if (confirmFor) {
    const pressed = confirmFor;
    return (
      <>
        <Button dense variant="ghost" disabled={stopping} onClick={() => setConfirmFor(null)}>
          Back
        </Button>
        <Button
          dense
          variant="danger"
          loading={stopping}
          data-testid="conductor-stop-confirm"
          onClick={() => {
            setStopping(true);
            void stopMember(pressed).finally(() => {
              setStopping(false);
              setConfirmFor(null);
            });
          }}
        >
          Stop · sure? (ends the agent's session)
        </Button>
      </>
    );
  }
  const detect = member?.detect;
  return (
    <>
      {receipt}
      {onInfo ? (
        <Button dense variant="ghost" disabled={!member} onClick={onInfo}>
          Get Info
        </Button>
      ) : null}
      {!trim && detect && !detect.installed ? (
        <Button dense variant="secondary" aria-label={`Copy install: ${member!.name}`} onClick={() => void copy(AGENT_INSTALL[detect.id])}>
          Copy install
        </Button>
      ) : null}
      {!trim && detect && needsHooks(detect) ? (
        <Button
          dense
          variant="primary"
          loading={installing === detect.id}
          onClick={() => void useConductor.getState().installHooks(detect.id)}
        >
          {`Connect ${AGENT_NAME[detect.id]}`}
        </Button>
      ) : null}
      {member && stops(member) ? (
        <Button dense variant="danger" data-testid="conductor-stop" onClick={() => setConfirmFor(member)}>
          Stop
        </Button>
      ) : null}
      {!trim && member && answers(member) ? (
        <Button dense variant="primary" onClick={() => answerMember(member)}>
          Answer
        </Button>
      ) : null}
      {!trim && member && member.role !== "ready" && member.live !== "queued" ? (
        <Button dense variant="secondary" onClick={() => openMember(member)}>
          Open
        </Button>
      ) : null}
    </>
  );
}

/** Phase 16: the Conductor's one big fact: `2 at work`; with none at work,
 *  the asks; with neither, the agents ready. Never a zero. PHILO-17 U32:
 *  ready means the agent can run (`canRun`), not only that it is on this Mac. */
export function headFact(head: { atWork: number; ask: number }, members: readonly ConductorMember[]): string {
  if (head.atWork > 0) return `${head.atWork} at work`;
  if (head.ask > 0) return `${head.ask} ${head.ask === 1 ? "asks" : "ask"}`;
  const found = members.filter((m) => m.role === "ready" && m.detect?.installed);
  const ready = found.filter((m) => canRun(m.detect!)).length;
  if (ready > 0) return `${ready} ready`;
  return found.length ? "No agent ready" : "No agent";
}

/** Gaps: the stopped agents whose item takes Hand again (a new agent in
 *  the same worktree; the hub checks it). */
const HAND_AGAIN = new Set(["resume_failed", "stopped_by_restart", "ended", "expired"]);

function handAgain(member: ConductorMember): void {
  const o = member.origin;
  const kind = handRefOf(`${o?.kind}:${o?.id}`)?.kind;
  if (!o || !kind) return;
  openHand({ kind, id: o.id, title: o.title, projectId: o.projectId, agent: o.agent as AgentId });
}

/** PHILO-17 U32: what Connect does, in one line, where it is offered. */
export const HOOKS_LINE = "Connect: see the agent's work, hand it work";

/** `Asked 6 min ago`, `Asked 3 h ago`, `Asked Oct 5`; `Asks` with no age. */
export function askedWord(when: string | undefined): string {
  if (!when) return "Asks";
  return `Asked ${agoWord(when)}`;
}

/** The kind plate of an agent: `CC` Claude Code, `CX` Codex, `PI` pi. */
export function agentPlate(agent: string): string {
  if (agent === "claude") return "CC";
  if (agent === "codex") return "CX";
  if (agent === "pi") return "PI";
  return agent.slice(0, 3).toUpperCase() || "AGT";
}


/* ── PHILO-17 THE REFIT: the Conductor reads like Today ─────────────────
 * One question leads: which coder needs you. The asks are raised plates
 * with a Workbench title bar (the focus object), the question in full and
 * ONE verb (Answer). Then the coders at work as quiet rows (one verb:
 * Open), the coders on this Mac (a row that lacks hooks carries the verb
 * that fixes it), and the launches that ended today, folded. A press on a
 * row's name selects it; the foot keeps the quiet verbs (Get Info, Stop). */

/** The plain word of a member's state (never a wire code) and its tone. */
export function memberPill(member: ConductorMember): { word: string; tone: "ok" | "warn" | "danger" | "info" | "idle"; live?: boolean } {
  if (member.role === "ready") {
    const row = member.detect;
    if (!row?.installed) return { word: "Not installed", tone: "idle" };
    // `not_read`: the hub could not read the hooks; a fact, not a fault.
    if (row.hooks === "not_read") return { word: "Hooks not checked", tone: "idle" };
    if (row.hooks !== "installed") {
      const word = { missing: "Not connected", partial: "Some hooks missing", unreadable: "Hooks unreadable", broken: "Hooks broken" }[row.hooks] ?? "No hooks";
      return { word, tone: "warn" };
    }
    if ((row.signed_in as string) === "no") return { word: "Signed out", tone: "warn" };
    return { word: "Ready", tone: "ok" };
  }
  if (member.role === "stale") return { word: plainReceipt(member.receipt ?? "Ended"), tone: member.state?.tone === "ok" ? "ok" : "idle" };
  switch (member.live) {
    case "ask":
      return { word: "Asks you", tone: "warn", live: true };
    case "held":
      return { word: "Wants to run", tone: "warn", live: true };
    case "needs_you":
      return { word: "Needs you", tone: "warn", live: true };
    case "idle":
      return { word: "Idle", tone: "idle" };
    case "pr":
      return { word: member.lamp?.label.startsWith("PR #") ? `${member.lamp.label} open` : "PR open", tone: "ok" };
    case "queued":
      // Betterment AG5: at the working-at-once limit the hand waits.
      return { word: "Waits for a free agent", tone: "idle" };
    case "no_signal":
      // Betterment AG7: no hook and no screen rule for ten minutes.
      return { word: "No signal", tone: "idle" };
    case "done":
      // Betterment AG0: Done · New until he opens it, then Quiet.
      return member.isNew ? { word: "Done · New", tone: "ok" } : { word: "Quiet", tone: "idle" };
    default:
      if (member.lamp?.label === "RESUMES") return { word: "Resuming", tone: "info", live: true };
      return { word: member.lamp?.label === "STARTS" ? "Starting" : "Working", tone: "info", live: true };
  }
}

/** `PR #413 MERGED · ITEM CLOSED` → `PR #413 merged · item closed`. */
export function plainReceipt(receipt: string): string {
  const lower = receipt.toLowerCase().replace(/\bpr #/g, "PR #");
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}

/** `6 MIN` → `6 min ago`; `OCT 5` → `Oct 5`. */
export function agoWord(when: string | undefined): string {
  if (!when) return "";
  if (/^\d+ (MIN|H)$/.test(when)) return `${when.toLowerCase()} ago`;
  return when.charAt(0) + when.slice(1).toLowerCase();
}

/** The row's title: the item the agent works on, else its name. */
function rowTitle(member: ConductorMember): string {
  return member.role === "ready" ? member.name : String(member.facts.from || member.name);
}

function Pill({ member }: { member: ConductorMember }) {
  const pill = memberPill(member);
  return (
    <span className="kit-pill" data-tone={pill.tone === "idle" ? undefined : pill.tone} data-dot="" data-live={pill.live ? "" : undefined} data-testid="conductor-pill">
      {pill.word}
    </span>
  );
}

function Sprite({ member, size = "row" }: { member: ConductorMember; size?: "row" | "plate" }) {
  return (
    <span className={size === "plate" ? "cw-plate-sprite" : "cw-row-sprite"} aria-hidden="true">
      <img src={member.sprite} alt="" draggable={false} />
    </span>
  );
}

/** One quiet row: sprite, the name (a press selects), meta, at most one verb. */
function CoderRow({
  member,
  selected,
  onSelect,
  verb,
  meta,
  helper,
}: {
  /** Betterment AG11: "Helper of …": the row is indented under its parent. */
  helper?: string;
  member: ConductorMember;
  selected: boolean;
  onSelect(): void;
  verb?: ReactNode;
  meta?: ReactNode;
}) {
  return (
    <li className="cw-row" data-object-id={member.id} data-selected={selected ? "" : undefined} data-testid="conductor-row"
      data-helper={helper ? "" : undefined}>
      <Sprite member={member} />
      <div className="cw-row-text">
        <Button variant="chrome" className="cw-row-title" aria-pressed={selected} onClick={onSelect}>
          {rowTitle(member)}
        </Button>
        <span className="cw-row-meta">
          <Pill member={member} />
          {helper ? <span data-testid="conductor-helper-of">{helper}</span> : null}
          {reviewWords(member.review) ? <span data-testid="conductor-review">{reviewWords(member.review)}</span> : null}
          {meta}
        </span>
        <ReviewResult review={member.review} />
        {/* Betterment AG3: what the desk answered for him, New until opened. */}
        <DeskAnswerLine answer={member.deskAnswer} />
      </div>
      {verb}
    </li>
  );
}

/* Betterment AG2: the asking plate (AskPlate) became AgentRow
 * (desk/agents/AgentRow.tsx): answer and allow in one press, the command
 * shown first. `useHeldCall` moved with it. */
export { useHeldCall } from "../agents/AgentRow";

function titleOfAgent(member: ConductorMember): string {
  return AGENT_NAME[member.agent as AgentId] ?? member.agent;
}

/** The verb of an agent on this Mac: the one that fixes it, or none. */
function ReadyVerb({ member, lead }: { member: ConductorMember; lead: boolean }) {
  const installing = useConductor((s) => s.installing);
  const { copy, receipt } = useCopyReceipt();
  const row = member.detect;
  if (!row) return null;
  if (!row.installed) {
    return (
      <>
        {receipt}
        <Button dense variant="ghost" aria-label={`Copy install: ${member.name}`} onClick={() => void copy(AGENT_INSTALL[row.id])}>
          Copy install
        </Button>
      </>
    );
  }
  if (!needsHooks(row)) return null;
  return (
    <Button
      dense
      variant={lead ? "primary" : "secondary"}
      aria-label={`Connect ${member.name}`}
      data-testid="conductor-install-hooks"
      loading={installing === row.id}
      disabled={Boolean(installing) && installing !== row.id}
      onClick={() => void useConductor.getState().installHooks(row.id)}
    >
      {`Connect ${AGENT_NAME[row.id]}`}
    </Button>
  );
}

/* Window grammar (2026-10-24): the Agents window reads title bar → Toolbar
 * [Start an agent] → the asks (each a plate: the question and its answer
 * in one row, which a list row cannot hold) → the dense list view of every
 * other agent, grouped Working · On this Mac · Stopped by restart · Stopped
 * today · Started by you (Name with the agent's portrait, What, State as a
 * dot and a word, When) → StatusBar (`1 working · 2 on this Mac · 2 stopped
 * today`, never a zero) with the selected row's verbs at its right. A press
 * selects a row; Enter or a double press opens it. */
const ROW_GROUP = { work: 0, mac: 1, restart: 2, ended: 3, own: 4 } as const;
type RowGroup = keyof typeof ROW_GROUP;

const LIST_COLUMNS = [
  { key: "name", word: "Name", track: "minmax(132px, 0.7fr)" },
  { key: "what", word: "What", track: "minmax(0, 1.2fr)" },
  { key: "project", word: "Project", track: "minmax(0, 0.6fr)" },
  { key: "state", word: "State", track: "minmax(128px, 0.8fr)" },
  { key: "when", word: "When", track: "96px" },
] as const;

const PILL_TONE: Record<string, ObjectListTone> = { ok: "ok", warn: "warn", danger: "fail", info: "info", idle: "idle" };

/** A row's state for the dense list's own state cell: a dot and a word
 *  (`idle` is the plain grey dot). */
function rowState(member: ConductorMember): NonNullable<ObjectListRow["state"]> {
  const pill = memberPill(member);
  return { label: pill.word, tone: PILL_TONE[pill.tone], live: pill.live, testId: "conductor-pill" };
}

/** The selected row's own verb: the one that fixes it, opens it, resumes
 *  it, or cancels its wait. Get Info and Stop follow (MemberVerbs). */
function RowVerb({
  member,
  group,
  resuming,
  onResume,
  cancelling,
  onCancel,
}: {
  member: ConductorMember;
  group: RowGroup;
  resuming: string | null;
  onResume: () => void;
  cancelling: string | null;
  onCancel: () => void;
}) {
  if (group === "mac") return <ReadyVerb member={member} lead={false} />;
  if (group === "restart") {
    return (
      <Button dense variant="secondary" loading={resuming === member.id} disabled={resuming !== null}
        onClick={onResume} data-testid="conductor-resume">
        <ToolGlyph kind="retry" />
        Resume
      </Button>
    );
  }
  if (group === "own") return null;
  if (member.live === "queued") {
    return (
      <Button dense variant="secondary" loading={cancelling === member.id} disabled={cancelling !== null}
        onClick={onCancel} data-testid="conductor-cancel-queued">
        Cancel
      </Button>
    );
  }
  return (
    <>
      {group === "ended" && HAND_AGAIN.has(String(member.flightState)) && member.origin ? (
        // Gaps: a new agent continues in the same worktree.
        <Button dense variant="secondary" onClick={() => handAgain(member)} data-testid="conductor-hand-again">
          Hand again
        </Button>
      ) : null}
      <Button dense variant="secondary" onClick={() => openMember(member)} data-testid="conductor-open">
        <ToolGlyph kind="open" />
        Open
      </Button>
    </>
  );
}

export function ConductorWindow() {
  const reads = useConductorReads();
  const sessions = useAgentFlights((s) => s.sessions);
  const flights = useAgentFlights((s) => s.flights);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  // Betterment AG8: Start an agent unfolds in place.
  const [starting, setStarting] = useState(false);
  const [foot, setFoot] = useState<HTMLElement | null>(null);
  const [sort, setSort] = useState<ObjectListSort>({ key: "order", dir: "asc" });

  const flightsKnown = reads.flightsState === "ok";
  const members = useMemo(
    () =>
      conductorMembers({
        detect: reads.detect?.agents ?? null,
        // Unknown stays unknown: a failed read lists no agent as gone.
        sessions: flightsKnown ? sessions : [],
        flights: flightsKnown ? flights : [],
        launchedAt: reads.launchedAt,
        history: flightsKnown ? reads.history : [],
        endedAt: reads.endedAt,
      }),
    [reads.detect, reads.launchedAt, reads.history, reads.endedAt, sessions, flights, flightsKnown],
  );
  const ownMembers = useMemo(() => reads.ownAgents.map(ownAgentMember), [reads.ownAgents]);
  const head = conductorHead(members, flightsKnown ? reads.launches : null);
  const everyone = useMemo(() => [...members, ...ownMembers], [members, ownMembers]);
  const selected = useMemo(() => everyone.find((m) => m.id === selectedId) ?? null, [everyone, selectedId]);
  // Betterment AG4: a hand opens Agents on its new agent: that row is
  // selected and in view once the read draws it.
  const focus = useConductor((s) => s.focus);
  const bodyRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!focus || !members.some((m) => m.id === focus)) return;
    setSelectedId(focus);
    useConductor.getState().clearFocus();
    window.requestAnimationFrame(() => {
      bodyRef.current?.querySelector(`[data-object-id="${CSS.escape(focus)}"]`)?.scrollIntoView?.({ block: "nearest" });
    });
  }, [focus, members]);
  useEffect(() => {
    if (selectedId && !selected) setSelectedId(null);
  }, [selectedId, selected]);

  // The flights read decides what stands ABOVE the agents on this Mac
  // (Needs you, At work). Until it answers (ok or failed), the window says
  // it is reading and draws no rows: the detect read alone used to draw the
  // ready rows first, and the late sessions pushed them 220 px down at 393
  // (the desk sweep's still fence, under load).
  const loading = reads.flightsState === "idle" || reads.flightsState === "loading";
  const failed = [
    reads.detectState === "failed" ? { part: "Agents", token: reads.detectFailure } : null,
    reads.flightsState === "failed" ? { part: "Sessions", token: "" } : null,
  ].filter((f): f is { part: string; token: string } => f !== null);
  const retry = () => {
    if (reads.detectState === "failed") void useConductor.getState().readDetect();
    if (reads.flightsState === "failed") void useConductor.getState().readFlights();
  };
  const info = (member: ConductorMember | null) => {
    if (member) useConductor.getState().openInfo(member);
  };
  const words = headWords(head);

  // Betterment AG8: the fleet's order: Needs you (the oldest ask first),
  // New (the newest first), Working, Quiet. Betterment AG11: a helper
  // stands right after its parent.
  const parentIds = new Set(members.map((m) => m.launchId).filter(Boolean) as string[]);
  const nested = (m: ConductorMember) => Boolean(m.helperOf && parentIds.has(m.helperOf));
  const helpersOf = (m: ConductorMember) => (m.launchId ? members.filter((h) => h.helperOf === m.launchId && nested(h)) : []);
  const ordered = fleetOrder(members).filter((m) => !nested(m));
  const projects = fleetGroups(members.filter((m) => !nested(m)));
  const counts = fleetCounts(members);
  const asks = ordered.filter((m) => fleetRank(m) === 0);
  // #1352: no rows until the sessions read answers.
  const ready = loading ? [] : members.filter((m) => m.role === "ready");
  // Betterment AG6: an agent a restart stopped has Resume (one press).
  const stopped = members.filter((m) => m.role === "stale" && m.flightState === "stopped_by_restart" && m.launchId);
  const ended = members.filter((m) => m.role === "stale" && !stopped.includes(m));
  const [resuming, setResuming] = useState<string | null>(null);
  const resume = (targets: ConductorMember[], key: string) => {
    // The receipt shows in the foot of the selected agent: one Resume selects it.
    if (targets.length === 1) setSelectedId(targets[0].id);
    setResuming(key);
    void resumeAll(targets).finally(() => setResuming(null));
  };
  const fixable = ready.filter((m) => m.detect && m.detect.installed && needsHooks(m.detect));
  // Betterment AG8: "On this Mac" shows only when something is missing: an
  // agent whose hooks are not in, or no agent installed at all.
  const missing = fixable.length ? fixable : ready.some((m) => m.detect?.installed) ? [] : ready;
  const question = (m: ConductorMember) => sessions.find((row) => row.key === m.sessionKey)?.question ?? "";
  const waitIdOf = (m: ConductorMember) => {
    const raw = sessions.find((row) => row.key === m.sessionKey)?.raw ?? {};
    const session = ((raw as Record<string, unknown>).session ?? raw) as Record<string, unknown>;
    return session.wait_id ? String(session.wait_id) : null;
  };
  // ONE filled primary per window: the first ask's Answer, else Start an
  // agent. While Start an agent is open, its Start is the one primary.
  const leadAsk = starting ? null : asks[0]?.id ?? null;
  const [cancelling, setCancelling] = useState<string | null>(null);
  const cancelQueued = (m: ConductorMember) => {
    setCancelling(m.id);
    void cancelQueuedHand(m).finally(() => setCancelling(null));
  };
  const select = (id: string) => setSelectedId((now) => (now === id ? null : id));
  const [allowingHelper, setAllowingHelper] = useState<string | null>(null);

  /** One agent that needs him: the whole job in its plate. */
  const askRow = (m: ConductorMember): ReactNode => (
    <Fragment key={m.id}>
    {m.helperRequest ? (
      <CoderRow
        member={m}
        selected={m.id === selectedId}
        onSelect={() => select(m.id)}
        meta={<span data-testid="conductor-helper-request">Secure asks: {m.helperRequest.instruction}</span>}
        verb={
          <Button
            dense
            variant="primary"
            loading={allowingHelper === m.id}
            disabled={allowingHelper !== null}
            data-testid="conductor-allow-helper"
            onClick={() => {
              setAllowingHelper(m.id);
              void allowHelper(m).finally(() => setAllowingHelper(null));
            }}
          >
            Allow helper
          </Button>
        }
      />
    ) : <AgentRowFace
      key={m.id}
      member={m}
      question={question(m)}
      waitId={waitIdOf(m)}
      lead={m.id === leadAsk}
      selected={m.id === selectedId}
      onSelect={() => select(m.id)}
      onTerminal={() => {
        if (m.launchId) openAgentLane(m.launchId, { sessionKey: m.sessionKey, raw: true });
        else openMember(m);
      }}
      onOpenAnswer={() => answerMember(m)}
      onOpen={() => openMember(m)}
    />}
    {helperAsks(m)}
    </Fragment>
  );
  /** A parent's asking helpers, as plates under its name (AG11). */
  const helperAsks = (m: ConductorMember): ReactNode => {
    const rows = helpersOf(m).filter((h) => fleetRank(h) === 0);
    return rows.length ? (
      <ul className="cw-well surface-group-well cw-helpers" data-testid="conductor-helpers" aria-label={`Helpers of ${rowTitle(m)}`}>
        {rows.map(askRow)}
      </ul>
    ) : null;
  };
  /** AG15: an owner-started pane that asks has the same answer surface,
   *  with no launch verbs. */
  const ownAsk = (m: ConductorMember): ReactNode => (
    <AgentRowFace
      key={m.id}
      member={m}
      question=""
      waitId={null}
      lead={false}
      selected={m.id === selectedId}
      onSelect={() => select(m.id)}
      onTerminal={() => undefined}
      onOpenAnswer={() => undefined}
      onOpen={() => undefined}
    />
  );
  const workingParents = ordered.filter((m) => fleetRank(m) > 0 && helpersOf(m).some((h) => fleetRank(h) === 0));
  const ownAsks = ownMembers.filter((m) => fleetRank(m) === 0);

  // The list view: every agent that does not ask, in its group.
  const groupOf = new Map<string, RowGroup>();
  const listed: Array<{ m: ConductorMember; group: RowGroup; parent?: ConductorMember }> = [];
  const add = (m: ConductorMember, group: RowGroup, parent?: ConductorMember) => {
    groupOf.set(m.id, group);
    listed.push({ m, group, parent });
  };
  for (const m of ordered) {
    if (fleetRank(m) > 0) add(m, "work");
    for (const h of helpersOf(m)) if (fleetRank(h) > 0) add(h, "work", m);
  }
  for (const m of missing) add(m, "mac");
  for (const m of stopped) add(m, "restart");
  for (const m of ended) add(m, "ended");
  for (const m of ownMembers) if (fleetRank(m) > 0) add(m, "own");
  const rows: ObjectListRow[] = listed.map(({ m, group, parent }, index) => {
    const what = m.role === "ready"
      ? (m.detect?.version ? String(m.detect.version) : "")
      : group === "own"
        ? String(m.ownAgent?.title || m.ownAgent?.project || "On this Mac")
        : rowTitle(m);
    const extra = [parent ? `Helper of ${rowTitle(parent)}` : null, reviewWords(m.review)].filter(Boolean).join(" · ");
    return {
      id: m.id,
      kind: "agent",
      name: m.role === "ready" ? m.name : titleOfAgent(m),
      sprite: m.sprite,
      when: m.when ? agoWord(m.when) : undefined,
      whenSort: m.whenSort,
      group: ROW_GROUP[group],
      cells: {
        // Betterment AG3: what the desk answered for him stays in view on
        // the row (New until he opens the agent).
        what: m.deskAnswer?.state === "answered" ? (
          <span className="cw-what">
            <span className="cw-what-text">{extra ? `${what} · ${extra}` : what}</span>
            <DeskAnswerLine answer={m.deskAnswer} />
          </span>
        ) : extra ? `${what} · ${extra}` : what,
        project: projects && m.role === "live" ? String(m.facts.where || "") : "",
      },
      state: rowState(m),
      sortValues: { order: index, state: memberPill(m).word },
    };
  });
  const hasRows = rows.length > 0;
  const nothing = !loading && !asks.length && !hasRows && !ownAsks.length && !failed.length && !starting;
  const selectedGroup = selected ? groupOf.get(selected.id) ?? null : null;

  // The status bar: what is there, in warm words; never a zero.
  const queued = members.filter((m) => m.role === "live" && m.live === "queued").length;
  const fleet = fleetWords(counts);
  const items: Array<StatusBarItem | null> = [
    ...failed.map((f) => ({
      key: `fail-${f.part}`,
      lamp: "fail" as const,
      text: `${f.part} not read${f.token ? ` · ${f.token}` : ""}`,
      testId: "conductor-not-read",
    })),
    counts.needYou ? { key: "ask", lamp: "ask" as const, text: `${counts.needYou} ${counts.needYou === 1 ? "needs" : "need"} you` } : null,
    { key: "new", lamp: "ok" as const, text: countWords(counts.fresh, "new", "new") },
    { key: "working", lamp: "info" as const, text: countWords(counts.working, "working", "working") },
    { key: "queued", text: countWords(queued, "waiting", "waiting") },
    { key: "mac", lamp: fixable.length ? "warn" as const : undefined, text: missing.length ? `${missing.length} on this Mac` : null },
    { key: "restart", lamp: "warn" as const, text: countWords(stopped.length, "stopped by restart", "stopped by restart") },
    { key: "ended", text: ended.length ? `${ended.length} stopped today` : null },
    { key: "own", text: ownMembers.length ? `${ownMembers.length} started by you` : null },
    !fleet && !loading && !failed.length ? { key: "fact", text: headFact(head, members) } : null,
    ...words.filter((w) => / OF /.test(w)).map((w) => ({ key: w, text: w.toLowerCase() })),
  ];

  return (
    <DeskWindowFrame
      id={CONDUCTOR_WINDOW_ID}
      title="Agents"
      label="Agents"
      kindWord="Drawer"
      glyph="◉"
      icon={<img className="drawer-winicon" src={objectSprite("conductor", "conductor")} alt="" />}
      className="desk-pullout drawer-window conductor-window"
      minW={340}
      minH={280}
      defaultW={760}
      defaultH={520}
      origin={reads.origin}
      open
      unmountOnMinimize
      // PHILO-16 (A1) §4.3: an agent that asks (or holds a call) lights the bar.
      lamp={head.ask > 0 ? "ask" : undefined}
      onClose={() => useConductor.getState().closeWindow()}
    >
      <FootSlotContext.Provider value={foot}>
      <div ref={bodyRef} className="desk-pullout-body drawer-body surface-host-body" data-surface-host="conductor"
        data-testid="conductor-window" data-interior="list">
        <Toolbar label="Agents" data-testid="conductor-toolbar">
          <Button
            dense
            variant={starting || leadAsk ? "secondary" : "primary"}
            aria-expanded={starting}
            onClick={() => setStarting((open) => !open)}
            data-testid="conductor-start"
          >
            <ToolGlyph kind="new" />
            Start an agent
          </Button>
          {stopped.length >= 2 ? (
            <Button
              dense
              variant="secondary"
              loading={resuming === "all"}
              disabled={resuming !== null}
              onClick={() => resume(stopped, "all")}
              data-testid="conductor-resume-all"
            >
              <ToolGlyph kind="retry" />
              Resume all
            </Button>
          ) : null}
          {failed.length ? (
            <Button dense variant="secondary" onClick={retry}>
              <ToolGlyph kind="retry" />
              Retry
            </Button>
          ) : null}
        </Toolbar>
        <div className="drawer-scroll cw cw-scroll">
          {starting ? (
            <div className="cw-pane">
              <StartAgent
                onCancel={() => setStarting(false)}
                onStarted={(row) => {
                  setStarting(false);
                  if (row) useConductor.getState().openWindow(null, row);
                  void useConductor.getState().readFlights();
                }}
              />
            </div>
          ) : null}

          {loading ? <SurfaceState loading /> : null}
          {nothing ? (
            <div className="cw-empty" data-testid="conductor-empty">
              <SurfaceState empty emptyImage={objectSprite("conductor", "conductor")} emptyLabel="An agent works on one item for you, in its own branch." />
            </div>
          ) : null}

          {asks.length || workingParents.length || ownAsks.length ? (
            <section className="cw-section cw-pane cw-asks" data-testid="conductor-asks" aria-label="Needs you">
              {asks.map(askRow)}
              {workingParents.map((m) => <Fragment key={`helpers-${m.id}`}>{helperAsks(m)}</Fragment>)}
              {ownAsks.map(ownAsk)}
            </section>
          ) : null}

          {hasRows ? (
            <div className="cw-list" data-testid="conductor-list">
              <ObjectList
                label="Agents"
                density="dense"
                rows={rows}
                columns={LIST_COLUMNS.filter((column) => !["project", "when", "what"].includes(column.key)
                  || rows.some((row) => column.key === "when" ? row.when : row.cells?.[column.key]))}
                sort={sort}
                onSort={(key: string) => setSort((current) => ({ key, dir: current.key === key && current.dir === "asc" ? "desc" : "asc" }))}
                selectedId={selectedId}
                onSelect={setSelectedId}
                onOpen={(id) => {
                  const m = everyone.find((row) => row.id === id);
                  const group = groupOf.get(id);
                  if (!m) return;
                  if (group === "mac") info(m);
                  else if (group !== "own" && m.live !== "queued") openMember(m);
                }}
                rowProps={(row) => ({ "data-testid": "conductor-row", "data-group": groupOf.get(row.id) })}
              />
            </div>
          ) : null}
          {/* AG12: a selected agent's pair result reads under the list. */}
          {selected && selectedGroup && reviewResult(selected.review) ? (
            <div className="cw-pane cw-selection" data-testid="conductor-selection">
              <ReviewResult review={selected.review} />
            </div>
          ) : null}
        </div>
      </div>
      <footer ref={setFoot} className="desk-surface-foot surface-footer cw-footer" />
      <StatusBar
        data-testid="conductor-head"
        egress={selected?.role === "live" ? <EgressChip label={AGENT_HOST[selected.agent as AgentId] ?? AGENT_HOST.claude} scope="cloud" /> : null}
        items={items}
        // The receipt (Stop, a hooks install, a stale launch's close) leads
        // the verbs: an empty receipt leaves no separator behind.
        verbs={<>
          <MemberReceipt member={selected} />
          {selected ? (
          <>
            {selectedGroup ? (
              <RowVerb
                member={selected}
                group={selectedGroup}
                resuming={resuming}
                onResume={() => resume([selected], selected.id)}
                cancelling={cancelling}
                onCancel={() => cancelQueued(selected)}
              />
            ) : null}
            <MemberVerbs member={selected} onInfo={() => info(selected)} trim />
          </>
          ) : null}
        </>}
      />
      </FootSlotContext.Provider>
    </DeskWindowFrame>
  );
}
