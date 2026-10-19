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
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import {
  AppHead,
  EgressChip,
  StatusStrip,
  SurfaceFooter,
  SurfaceState,
  objectSprite,
} from "../surface";
import { FoldGadget } from "../surface/gadgets";
import { DeskWindowFrame } from "../components/DeskWindow";
import { useAgentFlights } from "../agentFlights";
import { AGENT_HOST, AGENT_INSTALL, AGENT_NAME, needsHooks, type AgentId, type AgentRow } from "../firstrun/agentsStep";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import { useDesk } from "../store";
import { useOnCoderFrame, useOnDeskChanged } from "../useDeskChangedRefresh";
import { canRun, conductorHead, conductorMembers, headWords, type ConductorMember } from "./members";
import { answerMember, answers, openMember, resumeAll, stopMember, stops } from "./open";
import { AgentRow as AgentRowFace } from "../agents/AgentRow";
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
  }, []);
  const reread = () => void useConductor.getState().readFlights();
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
    case "idle":
      return { word: "Idle", tone: "idle" };
    case "pr":
      return { word: member.lamp?.label.startsWith("PR #") ? `${member.lamp.label} open` : "PR open", tone: "ok" };
    case "queued":
      // Betterment AG5: at the working-at-once limit the hand waits.
      return { word: "Waits for a free agent", tone: "idle" };
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
}: {
  member: ConductorMember;
  selected: boolean;
  onSelect(): void;
  verb?: ReactNode;
  meta?: ReactNode;
}) {
  return (
    <li className="cw-row" data-object-id={member.id} data-selected={selected ? "" : undefined} data-testid="conductor-row">
      <Sprite member={member} />
      <div className="cw-row-text">
        <Button variant="chrome" className="cw-row-title" aria-pressed={selected} onClick={onSelect}>
          {rowTitle(member)}
        </Button>
        <span className="cw-row-meta">
          <Pill member={member} />
          {meta}
        </span>
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

export function ConductorWindow() {
  const reads = useConductorReads();
  const sessions = useAgentFlights((s) => s.sessions);
  const flights = useAgentFlights((s) => s.flights);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [coldOpen, setColdOpen] = useState<boolean | null>(null);

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
  const head = conductorHead(members, flightsKnown ? reads.launches : null);
  const selected = useMemo(() => members.find((m) => m.id === selectedId) ?? null, [members, selectedId]);
  // Betterment AG4: a hand opens Agents on its new agent: that row is
  // selected and in view once the read draws it.
  const focus = useConductor((s) => s.focus);
  useEffect(() => {
    if (!focus || !members.some((m) => m.id === focus)) return;
    setSelectedId(focus);
    useConductor.getState().clearFocus();
    window.requestAnimationFrame(() => {
      document.querySelector(`.conductor-window [data-object-id="${CSS.escape(focus)}"]`)?.scrollIntoView?.({ block: "nearest" });
    });
  }, [focus, members]);
  useEffect(() => {
    if (selectedId && !selected) setSelectedId(null);
  }, [selectedId, selected]);

  const loading = (reads.flightsState === "idle" || reads.flightsState === "loading") && !members.length;
  const failed = [
    reads.detectState === "failed" ? { part: "AGENTS", token: reads.detectFailure } : null,
    reads.flightsState === "failed" ? { part: "SESSIONS", token: "" } : null,
  ].filter((f): f is { part: string; token: string } => f !== null);
  const retry = () => {
    if (reads.detectState === "failed") void useConductor.getState().readDetect();
    if (reads.flightsState === "failed") void useConductor.getState().readFlights();
  };
  const info = (member: ConductorMember | null) => {
    if (member) useConductor.getState().openInfo(member);
  };
  const words = headWords(head);
  const installed = (reads.detect?.agents ?? []).filter((a) => a.installed).length;

  const asks = members.filter((m) => m.role === "live" && (m.live === "ask" || m.live === "held"));
  const atWork = members.filter((m) => m.role === "live" && !(m.live === "ask" || m.live === "held"));
  const ready = members.filter((m) => m.role === "ready");
  // Betterment AG6: an agent a restart stopped stands in its own section
  // with Resume (one press); the rest of today's ended agents fold.
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
  const question = (m: ConductorMember) => sessions.find((row) => row.key === m.sessionKey)?.question ?? "";
  const waitIdOf = (m: ConductorMember) => {
    const raw = sessions.find((row) => row.key === m.sessionKey)?.raw ?? {};
    const session = ((raw as Record<string, unknown>).session ?? raw) as Record<string, unknown>;
    return session.wait_id ? String(session.wait_id) : null;
  };
  // ONE filled primary per window: the first ask's Answer, else the first
  // agent that lacks hooks.
  const leadAsk = asks[0]?.id ?? null;
  const leadFix = leadAsk ? null : fixable[0]?.id ?? null;
  // The agents on this Mac fold away while agents work and none needs a fix.
  const coldFolded = coldOpen === null ? !(fixable.length > 0 || (!asks.length && !atWork.length)) : !coldOpen;
  const select = (id: string) => setSelectedId((now) => (now === id ? null : id));

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
      <div className="desk-pullout-body drawer-body" data-testid="conductor-window">
        <div className="drawer-scroll cw">
          <div className="cw-head">
            <AppHead fact={headFact(head, members)} className="cw-apphead" data-testid="conductor-head">
              <StatusStrip
                items={[
                  ...failed.map((f) => ({
                    key: `fail-${f.part}`,
                    lamp: "fail" as const,
                    text: `${f.part} ·`,
                    value: `NOT READ${f.token ? ` · ${f.token}` : ""}`,
                    testId: "conductor-not-read",
                  })),
                  // `2 AT WORK` is the fact; the ask is a lamp (it needs him).
                  ...words.filter((w) => !w.endsWith(" AT WORK")).map((w) => ({
                    key: w,
                    lamp: w.endsWith(" ASK") ? ("ask" as const) : undefined,
                    text: w,
                  })),
                  installed > 0 ? { key: "agents", text: `${installed} ON THIS MAC` } : null,
                ]}
              />
            </AppHead>
            {failed.length ? (
              <Button dense variant="ghost" onClick={retry}>
                Retry
              </Button>
            ) : null}
            {stopped.length >= 2 ? (
              <Button
                dense
                variant={leadAsk || leadFix ? "secondary" : "primary"}
                loading={resuming === "all"}
                disabled={resuming !== null}
                onClick={() => resume(stopped, "all")}
                data-testid="conductor-resume-all"
              >
                Resume all
              </Button>
            ) : null}
          </div>

          {loading ? <SurfaceState loading /> : null}
          {!loading && !members.length && !failed.length ? <SurfaceState empty emptyLabel="No agent found" /> : null}

          {asks.length ? (
            <section className="cw-section" data-testid="conductor-asks" aria-label="Needs you">
              <h3 className="cw-cap">NEEDS YOU</h3>
              {asks.map((m) => (
                <AgentRowFace
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
                />
              ))}
            </section>
          ) : null}

          {atWork.length ? (
            <section className="cw-section" data-testid="conductor-work" aria-label="At work">
              <h3 className="cw-cap">AT WORK</h3>
              <ul className="cw-well">
                {atWork.map((m) => (
                  <CoderRow
                    key={m.id}
                    member={m}
                    selected={m.id === selectedId}
                    onSelect={() => select(m.id)}
                    meta={
                      <>
                        <span>{titleOfAgent(m)}</span>
                        {m.facts.where ? <span>{String(m.facts.where)}</span> : null}
                        {m.when ? <span className="cw-mono">{agoWord(m.when)}</span> : null}
                      </>
                    }
                    verb={
                      m.live === "queued" ? undefined : (
                        <Button dense variant="ghost" onClick={() => openMember(m)} data-testid="conductor-open">
                          Open
                        </Button>
                      )
                    }
                  />
                ))}
              </ul>
            </section>
          ) : null}

          {ready.length ? (
            coldFolded ? (
              <div className="cw-fold">
                <Button dense variant="ghost" aria-expanded={false} onClick={() => setColdOpen(true)} data-testid="conductor-coders-fold">
                  Agents on this Mac
                </Button>
              </div>
            ) : (
              <section className="cw-section" data-testid="conductor-coders" aria-label="Agents on this Mac">
                <h3 className="cw-cap">
                  ON THIS MAC
                  {asks.length || atWork.length ? (
                    <Button dense variant="ghost" aria-expanded onClick={() => setColdOpen(false)} className="cw-cap-verb">
                      Hide
                    </Button>
                  ) : null}
                </h3>
                <ul className="cw-well">
                  {ready.map((m) => (
                    <CoderRow
                      key={m.id}
                      member={m}
                      selected={m.id === selectedId}
                      onSelect={() => select(m.id)}
                      meta={m.detect?.version ? <span className="cw-mono">{m.detect.version}</span> : null}
                      verb={<ReadyVerb member={m} lead={m.id === leadFix} />}
                    />
                  ))}
                </ul>
                <HooksLine member={selected?.role === "ready" ? selected : null} />
              </section>
            )
          ) : null}

          {stopped.length ? (
            <section className="cw-section" data-testid="conductor-stopped" aria-label="Stopped by restart">
              <h3 className="cw-cap">STOPPED BY RESTART</h3>
              <ul className="cw-well">
                {stopped.map((m) => (
                  <CoderRow
                    key={m.id}
                    member={m}
                    selected={m.id === selectedId}
                    onSelect={() => select(m.id)}
                    meta={
                      <>
                        <span>{titleOfAgent(m)}</span>
                        {m.when ? <span className="cw-mono">{agoWord(m.when)}</span> : null}
                      </>
                    }
                    verb={
                      <Button
                        dense
                        variant={stopped.length === 1 && !leadAsk && !leadFix ? "primary" : "secondary"}
                        loading={resuming === m.id}
                        disabled={resuming !== null}
                        onClick={() => resume([m], m.id)}
                        data-testid="conductor-resume"
                      >
                        Resume
                      </Button>
                    }
                  />
                ))}
              </ul>
            </section>
          ) : null}

          {ended.length ? (
            <FoldGadget title="Ended today" token={String(ended.length)} className="cw-ended">
              <ul className="cw-well" data-testid="conductor-ended">
                {ended.map((m) => (
                  <CoderRow
                    key={m.id}
                    member={m}
                    selected={m.id === selectedId}
                    onSelect={() => select(m.id)}
                    meta={m.when ? <span className="cw-mono">{agoWord(m.when)}</span> : null}
                    verb={
                      <Button dense variant="ghost" onClick={() => openMember(m)}>
                        Open
                      </Button>
                    }
                  />
                ))}
              </ul>
            </FoldGadget>
          ) : null}
        </div>
      </div>
      <SurfaceFooter
        egress={selected?.role === "live" ? <EgressChip label={AGENT_HOST[selected.agent as AgentId] ?? AGENT_HOST.claude} scope="cloud" /> : null}
        className="cw-footer"
        receipt={<MemberReceipt member={selected} />}
        verbs={selected ? <MemberVerbs member={selected} onInfo={() => info(selected)} trim /> : null}
      />
    </DeskWindowFrame>
  );
}
