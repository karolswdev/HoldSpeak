// Parked: wave 13 replaces the agent rail and cards with selection and inspection.
import { useGuideView } from "../walk/viewState";
/** Agents (the language, 2026-11-08; owner: "the agent window is too
 *  somber, basic and weak … a product differentiator"; "every single app
 *  needs to be native"). The Agents window is one object window in the
 *  grammar the Programs window ratified: the RAIL of agents at the left
 *  (AgentRail.tsx: Start an agent, then Needs you, Running, Ended today,
 *  On this Mac; each tile the provider sprite, what it works on, its state
 *  word and a spine), the picked agent at the right (AgentPane.tsx: the
 *  mast, the spine, the plate with its one verb, the activity ledger,
 *  Details), the StatusBar (`1 needs you · 2 working · 3 of 3`, never a
 *  zero). An agent that needs him is picked first.
 *
 *  The members (`members.ts`) are the agents: ready, live, stale. Every
 *  read and verb is one the hub already answers (`store.ts`, `open.ts`,
 *  `agents/AgentRow.tsx`).
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { StatusBar, SurfaceState, ToolGlyph, countWords, objectSprite, type StatusBarItem } from "../surface";
import { DeskWindowFrame } from "../components/DeskWindow";
import { BackSlotContext, type WindowBack } from "../surface/back";
import { useAgentFlights } from "../agentFlights";
import { needsHooks } from "../firstrun/agentsStep";
import { AGENT_CHANGE_KINDS, useOnCoderFrame, useOnDeskChanged } from "../useDeskChangedRefresh";
import {
  canRun,
  conductorHead,
  conductorMembers,
  fleetCounts,
  fleetOrder,
  fleetRank,
  fleetWords,
  headWords,
  liveWord,
  ownAgentMember,
  type ConductorMember,
} from "./members";
import { resumeAll } from "./open";
import { StartAgent } from "./StartAgent";
import { AgentPane, memberTitle, plainReceipt } from "./AgentPane";
import { AgentRail, type RailSection } from "./AgentRail";
import { openSurfaceWhenReady } from "../shell";
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
  useOnDeskChanged(reread, AGENT_CHANGE_KINDS);
  return state;
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
  // W4 AGENT 2: the same word the agent's window says (members.liveWord).
  const label = member.lamp?.label ?? "";
  const pr = /^PR #(\d+)/.exec(label);
  return liveWord(member.live ?? "work", {
    isNew: member.isNew,
    pr: pr ? Number(pr[1]) : null,
    phase: label === "RESUMES" ? "resuming" : label === "STARTS" ? "starting" : null,
  });
}


/** The agent picked when he has picked none (or his pick left): what needs
 *  him first, then what runs, what ended, the agents on this Mac. */
export function defaultAgent(sections: readonly RailSection[], picked: string | null): string | null {
  const all = sections.flatMap((section) => section.rows.map((row) => row.member.id));
  if (picked && all.includes(picked)) return picked;
  return all[0] ?? null;
}

export function ConductorWindow() {
  const reads = useConductorReads();
  const sessions = useAgentFlights((s) => s.sessions);
  const flights = useAgentFlights((s) => s.flights);
  const [pickedId, setPickedId] = useState<string | null>(null);
  // Start an agent unfolds in the pane (Betterment AG8).
  const [starting, setStarting] = useState(false);
  const [paneOpen, setPaneOpen] = useState(false);
  useGuideView(() => ({pickedId,paneOpen}), saved => {setPickedId(saved.pickedId);setPaneOpen(saved.paneOpen);}, undefined, 1, CONDUCTOR_WINDOW_ID);
  const [windowBack, setWindowBack] = useState<WindowBack | null>(null);

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

  // The flights read decides what stands above the agents on this Mac.
  // Until it answers (ok or failed), the window says it is reading and
  // draws no tiles (#1352: the late sessions pushed the ready rows down).
  const loading = reads.flightsState === "idle" || reads.flightsState === "loading";
  const failed = [
    reads.detectState === "failed" ? { part: "Agents", token: reads.detectFailure } : null,
    reads.flightsState === "failed" ? { part: "Sessions", token: "" } : null,
  ].filter((f): f is { part: string; token: string } => f !== null);
  const retry = () => {
    if (reads.detectState === "failed") void useConductor.getState().readDetect();
    if (reads.flightsState === "failed") void useConductor.getState().readFlights();
  };

  // The fleet's order (Betterment AG8): Needs you (the oldest ask first),
  // New, Working, Quiet. A helper stands right after its parent (AG11).
  const parentIds = new Set(members.map((m) => m.launchId).filter(Boolean) as string[]);
  const nested = (m: ConductorMember) => Boolean(m.helperOf && parentIds.has(m.helperOf));
  const helpersOf = (m: ConductorMember) => (m.launchId ? members.filter((h) => h.helperOf === m.launchId && nested(h)) : []);
  const ordered = fleetOrder(members).filter((m) => !nested(m));
  const counts = fleetCounts(members);
  const ready = loading ? [] : members.filter((m) => m.role === "ready");
  // Betterment AG6: an agent a restart stopped has Resume (one press).
  const stopped = members.filter((m) => m.role === "stale" && m.flightState === "stopped_by_restart" && m.launchId);
  const ended = members.filter((m) => m.role === "stale" && !stopped.includes(m));
  const fixable = ready.filter((m) => m.detect && m.detect.installed && needsHooks(m.detect));

  const sections: RailSection[] = useMemo(() => {
    const asks: RailSection["rows"] = [];
    const running: RailSection["rows"] = [];
    const add = (m: ConductorMember, parent?: ConductorMember) => {
      const row = { member: m, group: fleetRank(m) === 0 ? "ask" : "work", helperOf: parent ? memberTitle(parent) : undefined };
      (fleetRank(m) === 0 ? asks : running).push(row);
    };
    for (const m of ordered) {
      add(m);
      for (const h of helpersOf(m)) add(h, m);
    }
    for (const m of ownMembers) (fleetRank(m) === 0 ? asks : running).push({ member: m, group: fleetRank(m) === 0 ? "ask" : "own" });
    const out: RailSection[] = [
      { id: "asks", word: "Needs you", rows: asks },
      { id: "running", word: "Running", rows: running },
      { id: "ended", word: "Ended today", rows: [...stopped.map((m) => ({ member: m, group: "restart" })), ...ended.map((m) => ({ member: m, group: "ended" }))] },
      { id: "installed", word: "On this Mac", rows: ready.map((m) => ({ member: m, group: "mac" })) },
    ];
    return out.filter((section) => section.rows.length);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [members, ownMembers, loading]);

  const everyone = useMemo(() => sections.flatMap((section) => section.rows.map((row) => row.member)), [sections]);
  // Betterment AG4: a hand opens Agents on its new agent: that tile is picked.
  const focus = useConductor((s) => s.focus);
  const railRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!focus || !everyone.some((m) => m.id === focus)) return;
    setPaneOpen(true);
    setPickedId(focus);
    setStarting(false);
    useConductor.getState().clearFocus();
    window.requestAnimationFrame(() => {
      railRef.current?.querySelector(`[data-object-id="${CSS.escape(focus)}"]`)?.scrollIntoView?.({ block: "nearest" });
    });
  }, [focus, everyone]);
  const picked = defaultAgent(sections, pickedId);
  const member = everyone.find((m) => m.id === picked) ?? null;
  const pick = (id: string) => {
    setPaneOpen(true);
    setPickedId(id);
    setStarting(false);
  };

  const runs = everyone.some((m) => m.role !== "ready");
  const nothing = !loading && !runs && !failed.length && !starting;
  const [resuming, setResuming] = useState(false);

  // The status bar: what is there, in warm words; never a zero.
  const queued = members.filter((m) => m.role === "live" && m.live === "queued").length;
  const fleet = fleetWords(counts);
  const workingRows = sections.find((s) => s.id === "running")?.rows
    .filter(({ member: m, group }) => group === "work" && memberPill(m).word === "Working").length ?? 0;
  const words = headWords(head);
  const items: Array<StatusBarItem | null> = [
    ...failed.map((f) => ({
      key: `fail-${f.part}`,
      lamp: "fail" as const,
      text: `${f.part} not read${f.token ? ` · ${f.token}` : ""}`,
      testId: "conductor-not-read",
    })),
    counts.needYou ? { key: "ask", lamp: "ask" as const, text: `${counts.needYou} ${counts.needYou === 1 ? "needs" : "need"} you` } : null,
    { key: "new", lamp: "ok" as const, text: countWords(counts.fresh, "new", "new") },
    // W4 AGENT 2: "N working" counts the tiles that say Working, no other.
    { key: "working", lamp: "info" as const, text: countWords(workingRows, "working", "working") },
    { key: "queued", text: countWords(queued, "waiting", "waiting") },
    { key: "mac", lamp: "warn" as const, text: fixable.length ? `${fixable.length} not connected` : null },
    { key: "restart", lamp: "warn" as const, text: countWords(stopped.length, "stopped by restart", "stopped by restart") },
    // W4 AGENT 3: a launch he checked (Done) is done, not stopped.
    { key: "checked", lamp: "ok" as const, text: countWords(ended.filter((m) => m.flightState === "checked").length, "done today", "done today") },
    { key: "ended", text: countWords(ended.filter((m) => m.flightState !== "checked").length, "stopped today", "stopped today") },
    { key: "own", text: ownMembers.length ? `${ownMembers.length} started by you` : null },
    !fleet && !loading && !failed.length ? { key: "fact", text: headFact(head, members) } : null,
    ...words.filter((w) => / OF /.test(w)).map((w) => ({ key: w, text: w.toLowerCase() })),
  ];

  const row = member?.sessionKey ? sessions.find((r) => r.key === member.sessionKey) : undefined;
  let pane;
  if (starting) {
    pane = (
      <div className="aw-start">
        <StartAgent
          onCancel={() => setStarting(false)}
          onStarted={(launched) => {
            setStarting(false);
            if (launched) useConductor.getState().openWindow(null, launched);
            void useConductor.getState().readFlights();
          }}
        />
      </div>
    );
  } else if (loading) {
    pane = <SurfaceState loading />;
  } else if (nothing && !member) {
    pane = (
      <div className="cw-empty" data-testid="conductor-empty">
        <SurfaceState empty emptyImage={objectSprite("conductor", "conductor")} emptyKind="agent"
          emptyLabel="An agent works on one item for you, in its own branch."
          onAction={() => setStarting(true)} actionLabel="Start an agent" />
      </div>
    );
  } else if (member) {
    pane = <AgentPane key={member.id} member={member} pill={memberPill(member)} row={row} onStart={() => setStarting(true)}
      opened={pickedId === member.id} />;
  } else {
    pane = null;
  }

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
      defaultW={860}
      defaultH={580}
      origin={reads.origin}
      open
      unmountOnMinimize
      // PHILO-16 (A1) §4.3: an agent that asks (or holds a call) lights the bar.
      lamp={head.ask > 0 ? "ask" : undefined}
      footClassName="cw-footer"
      onBack={windowBack?.onBack}
      backTestId={windowBack?.testId}
      backLabel={windowBack?.label}
      onClose={() => useConductor.getState().closeWindow()}
    >
      <BackSlotContext.Provider value={setWindowBack}>
        <div ref={railRef} className="desk-pullout-body surface-host-body aw" data-surface-host="conductor"
          data-testid="conductor-window" data-interior="list">
          <div className="aw-frame surface-rail-layout">
            <AgentRail sections={sections} picked={starting ? null : picked} starting={starting} paneOpen={paneOpen} pillOf={memberPill}
              onBack={() => { setPaneOpen(false); setStarting(false); }}
              onPick={pick} onStart={() => { setPaneOpen(true); setStarting((open) => !open); }} />
            <div className="aw-pane" data-testid="agents-pane" data-member={member?.id}>{pane}</div>
          </div>
        </div>
        <StatusBar
          data-testid="conductor-head"
          items={items}
          verbs={<>
            {stopped.length >= 2 ? (
              <Button dense variant="secondary" loading={resuming} disabled={resuming}
                onClick={() => {
                  setResuming(true);
                  void resumeAll(stopped).finally(() => setResuming(false));
                }}
                data-testid="conductor-resume-all">
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
            <Button dense variant="ghost" onClick={() => openSurfaceWhenReady("open-terminals")} data-testid="conductor-terminals">
              Terminals
            </Button>
          </>}
        />
      </BackSlotContext.Provider>
    </DeskWindowFrame>
  );
}
