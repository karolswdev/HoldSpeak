/** PHILO-14 C2 — the agent's window: a launched agent's lane (ratified board
 * A-4 with C-4's station track; docs/internal/philo/phase-14/canvas).
 *
 * Title `<Agent>: <item>`; the title bar's Raw gadget puts the terminal pane
 * (the session window's PaneWell, its arm strip and keys) in the body in
 * place of the lane: the tmux pane is debug, behind Raw, never the face.
 * Body: the station track (BRIEF · WORK · COMMIT · PR · HELD · ASKS ·
 * MERGE); the wait (TO ANSWER: the ask well; TO APPROVE: the held call with
 * Deny / Approve; DECIDING: one line); the timeline rail; the PR card and
 * the files changed (a column at 1440, under the PR at 393). Footer:
 * GITHUB.COM where the PR is, the branch, Re-brief, Stop, Open PR.
 *
 * Reads `GET /api/agent/launches/{id}/lane` (laneStore). Writes go through
 * the routes that exist: Answer and Re-brief are steers (the steer route of
 * the launch's session), Deny / Approve decide the gate proposal, Stop is the
 * kill route (two presses), Open PR opens the PR on GitHub. */
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { ApiError, apiFetch, readableError } from "../../lib/api";
import { useDurableDraft } from "../../lib/durableDraft";
import { GONE, markLaunchSeen, reviewResult, useAgentFlights, type AgentFlight, type CoderSessionRow } from "../agentFlights";
import { handRefOf, openHand } from "../agentHand";
import type { AgentId } from "../firstrun/agentsStep";
import { useConductor } from "../conductor/store";
import { launchLive, liveWord, type LiveState } from "../conductor/members";
import { checkLaunchDone } from "../conductor/open";
import { WhyThisState } from "../agents/WhyThisState";
import { ResultBlock, filesWords } from "./ResultBlock";
import { AgentWords, cutAtWord } from "../components/AgentWords";
import { DeskWindowFrame } from "../components/DeskWindow";
import { ArmStrip, KeyPalette, PANE_STATE_LABEL } from "../components/SessionPullout";
import { useFrontWindowId } from "../components/window/windowRegistry";
import { useGate } from "../gate";
import { spriteUrl } from "../sprites";
import { useSteering } from "../steering";
import { useDesk } from "../store";
import {
  AskWell,
  ActionNotice,
  FoldGadget,
  PaneWell,
  StringGadget,
  TransportKey,
} from "../surface";
import { SurfaceWings } from "../surface/wings";
import { stateWords } from "../surface/words";
import { StepList, type StepEntry } from "./StepList";
import { wireClock, wireDate } from "../surface/format";
import { DotWord, StatusBar, ToolGlyph, Toolbar } from "../surface/kit";
import { controlModeLabel } from "../../lib/productLanguage";
import { useCompactViewport } from "../useCompactViewport";
import { useOnCoderFrame } from "../useDeskChangedRefresh";
import { answerCoderOpenFirst } from "./coderOpen";
import {
  agentName,
  baseWord,
  checksSummary,
  gatedHead,
  isNotRead,
  isToolCall,
  laneEntries,
  laneStations,
  laneTitle,
  reviewWord,
  turnEndWord,
  turnWord,
  unreadParts,
  waitAge,
  type LaneEntry,
  type LaneEvent,
  type LaneGated,
  type LaneWait,
  type LaneWire,
  branchFace,
} from "./laneWire";
import { TERMINAL_GONE_WORDS, laneSessionKey, launchForSession, useLane, useLaneLaunchId } from "./laneStore";
import "./lane.css";


/** The lane title icon: the launch's OWN agent sprite at 32 (Codex keeps
 * its face; PHILO-14 A0c r2). */
export function laneTitleSprite(agent: string | null | undefined, key: string): string {
  return spriteUrl("agent", key, "rest", agent, 32);
}

/** The lane refreshes this often while its window is in front. */
export const LANE_FRONT_POLL_MS = 5_000;
export const LANE_WINDOW_ID = "lane";
/** The done face shows this many of the newest steps (one press shows all). */
export const STEPS_SHOWN_DONE = 3;
/** The window's two faces: its steps, its terminal. */
export const LANE_WINGS = [
  { id: "steps", label: "Steps" },
  { id: "terminal", label: "Terminal" },
];

/** The lane window host: mounted once on the Desk. It opens on a launch by
 * id, or on the launch of the open coder session; a coder object of a launch
 * opens here (not its card). */
export function LaneWindow() {
  const launchId = useLaneLaunchId();
  const explicit = useLane((s) => s.launchId);
  const openKey = useSteering((s) => s.openKey);

  useEffect(
    () =>
      answerCoderOpenFirst((coder) => {
        const key = `${coder.agent || "claude"}:${coder.sessionId || coder.id}`;
        const launch = launchForSession(key);
        if (!launch) return false;
        useLane.getState().open(launch, { sessionKey: key });
        return true;
      }),
    [],
  );

  // A session window opened on a launch's session (Watch live, a restored
  // window): that launch's lane takes it over by id.
  const fromKey = useAgentFlights((s) => s.flights.find((f) => openKey && f.sessionKey === openKey && f.launchId)?.launchId ?? null);
  useEffect(() => {
    if (fromKey && fromKey !== explicit) useLane.getState().open(fromKey, { sessionKey: openKey });
  }, [fromKey, explicit, openKey]);

  // The flights tell which session is a launch's: read once if no face has.
  useEffect(() => {
    if (!useAgentFlights.getState().loaded) void useAgentFlights.getState().load();
  }, []);

  if (!launchId) return null;
  return <LaneFrame launchId={launchId} />;
}

function LaneFrame({ launchId }: { launchId: string }) {
  const lane = useLane((s) => s.lane);
  const raw = useLane((s) => s.raw);
  const error = useLane((s) => s.error);
  // Atlas pass 2: the window's state is the Agents list's truth: the live
  // flight, else the launch's entry in the hub's history (an ended launch,
  // a session gone), never a "working" guessed from no flight at all.
  const live = useAgentFlights((s) => s.flights.find((f) => f.launchId === launchId) ?? null);
  const past = useConductor((s) => s.history.find((f) => f.launchId === launchId) ?? null);
  const flight = live ?? past;
  useEffect(() => {
    if (!live && useConductor.getState().flightsState !== "ok") void useConductor.getState().readFlights();
  }, [live, launchId]);
  const gone = flight && GONE.has(flight.state) ? flight : null;
  // W4 AGENT 2: the window's state word is the Agents row's word, from the
  // same source (the hub's flight with its session row: members.launchLive).
  const sessionRow = useAgentFlights((s) => (live?.sessionKey ? s.sessions.find((row) => row.key === live.sessionKey) ?? null : null));
  const shared = gone ? null : sharedState(flight, sessionRow);
  const front = useFrontWindowId() === LANE_WINDOW_ID;
  const compact = useCompactViewport();
  const reload = useCallback(() => {
    void useLane.getState().load();
  }, []);

  useOnCoderFrame(reload);
  useEffect(() => {
    if (!front) return;
    const tick = setInterval(reload, LANE_FRONT_POLL_MS);
    return () => clearInterval(tick);
  }, [front, reload]);
  // Betterment AG0: an open agent window has seen its done turn (Done · New
  // becomes Quiet): on open (the hub's current done turn), and when the
  // shared read shows a new done turn while the window is open.
  useEffect(() => {
    void markLaunchSeen(launchId, null);
  }, [launchId]);
  const unseenTurn = flight?.state === "done" && flight.isNew ? flight.turnId ?? null : null;
  useEffect(() => {
    if (unseenTurn) void markLaunchSeen(launchId, unseenTurn);
  }, [launchId, unseenTurn]);

  const agent = agentName(lane?.launch.agent ?? flight?.agent);
  const title = laneTitle(lane?.launch.agent ?? flight?.agent, flight?.title);
  const sessionKey = lane?.launch.session_key ?? flight?.sessionKey ?? null;

  return (
    <DeskWindowFrame
      id={LANE_WINDOW_ID}
      title={title}
      label={title}
      kindWord="Agent"
      glyph="▮"
      className="desk-pullout is-lane"
      minW={360}
      minH={320}
      defaultW={940}
      defaultH={560}
      icon={
        <img
          src={laneTitleSprite(lane?.launch.agent ?? flight?.agent, sessionKey ?? launchId)}
          alt=""
          width={16}
          height={16}
          className="desk-session-glyph desk-chrome-sprite"
          draggable={false}
        />
      }
      wings={
        // W3 AGENT WINDOW: the terminal is the window's second face, a wing
        // (the strip Speak and the Room wear), not a title-bar tab.
        sessionKey || flight?.stateSource === "screen" ? (
          <SurfaceWings
            wings={LANE_WINGS}
            active={raw ? "terminal" : "steps"}
            onChange={(id) => useLane.getState().setRaw(id === "terminal")}
            name={title}
          />
        ) : undefined
      }
      open
      onClose={() => useLane.getState().close()}
    >
      {lane ? <LaneToolbar lane={lane} agent={agent} gone={gone} shared={shared} /> : null}
      <LaneBody lane={lane} error={error} raw={raw} agent={agent} compact={compact} itemTitle={flight?.title ?? ""}
        gone={Boolean(gone)} shared={shared} screenSaid={flight?.screen?.said ?? null}
        checkedAt={gone?.state === "checked" ? gone.endedAt ?? null : undefined} />
      {lane ? <LaneFooter lane={lane} agent={agent} gone={gone} shared={shared} /> : null}
    </DeskWindowFrame>
  );
}

function LaneBody({
  lane, error, raw, agent, compact, itemTitle, screenSaid = null, gone = false, shared = null, checkedAt,
}: {
  /** W4 AGENT 3: he pressed Done (when; `null` with no time): the result stays. */
  checkedAt?: string | null;
  /** The launch's one state (the Agents row's word); null before a read. */
  shared?: LaneShared | null;
  /** The session is gone (the Agents list's truth): nothing is lit. */
  gone?: boolean;
  screenSaid?: string | null;
  lane: LaneWire | null;
  error: string | null;
  raw: boolean;
  agent: string;
  compact: boolean;
  itemTitle: string;
}) {
  const events = useLane((s) => s.events);
  const more = useLane((s) => s.more);
  const eventsNotRead = useLane((s) => s.eventsNotRead);
  const rebrief = useLane((s) => s.rebrief);
  const [briefOpen, setBriefOpen] = useState(false);
  const [allSteps, setAllSteps] = useState(false);
  const bodyRef = useRef<HTMLDivElement>(null);

  const onScroll = () => {
    const el = bodyRef.current;
    if (!el || !more || raw) return;
    if (el.scrollTop + el.clientHeight >= el.scrollHeight - 120) void useLane.getState().load();
  };

  if (!lane) {
    return (
      <div className="desk-pullout-body lw-body" data-testid="lane-body">
        {error ? <NotReadLine part="LANE" reason={error} /> : <p className="lw-notread">Reading the agent</p>}
      </div>
    );
  }

  const stations = laneStations(lane, events);
  const pr = lane.follow_through?.pr;
  const worktree = lane.worktree;
  const branch = branchFace(lane.launch.branch ?? (isNotRead(worktree) ? null : worktree.branch)) || undefined;
  const base = isNotRead(worktree) ? "" : baseWord(worktree.base);
  const doing = gone ? { word: "", tone: "idle" as const, key: "gone" as const } : laneDoing(lane, agent, shared);
  // Betterment AG10: the turn is done; its Result leads the Story. W4 AGENT
  // 3: a launch he checked (Done) keeps its result.
  const checked = checkedAt !== undefined;
  const done = doing.key === "done" || checked;
  const doneAt = wireDate(checked ? checkedAt ?? null : shared?.doneAt ?? null);
  const doneHead = done
    ? { word: checked ? "Done · checked by you" : "Done", age: doneAt ? spokeWord(doneAt) : null }
    : null;
  // W3 AGENT WINDOW (canvas direction A): the objects the agent made, as
  // object rows: the PR, its branch, the files it changed.
  const objects = (
    <LaneObjects lane={lane} itemTitle={itemTitle} branch={branch} base={base} />
  );
  const entries = laneEntries(lane, events);
  // AG10 face: a lane whose only entry is the brief (an agent with no hook
  // reports no events) shows the brief as a plain fold, not a one-row list.
  const onlyBrief = entries.every((entry) => entry.kind === "brief") && !eventsNotRead && !more;
  const steps = stepEntries(lane, entries, briefOpen, () => setBriefOpen((v) => !v));
  // The newest reported step is lit while the agent works; the wait is lit
  // while it asks; nothing is lit when it is done, idle or stopped.
  const lit = doing.key === "work"
    ? [...steps].reverse().find((s) => s.at != null && s.kind !== "brief")?.id ?? null
    : steps.find((s) => s.kind === "asks")?.id ?? null;
  // W4 AGENT 3 (canvas direction A, "It is done"): the result leads; the
  // steps fold to the last three, one press shows them all.
  const folds = done && !allSteps && steps.length > STEPS_SHOWN_DONE + 1;
  const shownSteps = folds ? steps.slice(-STEPS_SHOWN_DONE) : steps;
  const rail = onlyBrief ? (
    <div className="lw-col">
      {isNotRead(lane.gated) ? <NotReadLine part="HELD" reason={lane.gated.not_read} /> : null}
      {lane.launch.brief_text ? (
        <FoldGadget title="Brief" className="lw-brief-fold">
          <pre className="lw-brief" data-testid="lane-brief-text">{lane.launch.brief_text}</pre>
        </FoldGadget>
      ) : null}
    </div>
  ) : (
    <div className="lw-col lw-steps-col">
      {eventsNotRead ? <NotReadLine part="TIMELINE" reason={eventsNotRead} testId="lane-events-not-read" /> : null}
      {isNotRead(lane.gated) ? <NotReadLine part="HELD" reason={lane.gated.not_read} /> : null}
      {done && steps.length > STEPS_SHOWN_DONE + 1 ? (
        <div className="lw-steps-fold">
          <span className="lw-steps-fold-cap">{folds ? `The last ${STEPS_SHOWN_DONE} steps` : "All steps"}</span>
          <Button dense variant="ghost" aria-pressed={allSteps} data-testid="lane-all-steps" onClick={() => setAllSteps((v) => !v)}>
            {allSteps ? "Show the last 3" : "Show all"}
          </Button>
        </div>
      ) : null}
      <StepList data-testid="lane-rail" entries={shownSteps} lit={lit} />
      {briefOpen && lane.launch.brief_text ? (
        <pre className="lw-brief" data-testid="lane-brief-text">{lane.launch.brief_text}</pre>
      ) : null}
      {more ? (
        <Button dense variant="ghost" className="lw-more" onClick={() => void useLane.getState().load()}>
          Load more
        </Button>
      ) : null}
    </div>
  );

  return (
    <div className="desk-pullout-body lw-body" data-testid="lane-body" ref={bodyRef} onScroll={onScroll}>
      {/* W2-BUILDER (atlas 2026-10-27): the wait (the ask he must answer)
          comes first, then the result, then the work; Details last. */}
      {lane.launch.stopped ? null : rebrief ? <RebriefWell /> : (
        <>
          {!raw ? <HeldPlate lane={lane} agent={agent} /> : null}
          <WaitWell lane={lane} agent={agent} shared={checked ? "done" : shared?.key ?? null} />
        </>
      )}
      {!raw && (done || Boolean(reviewResult(lane.launch.review))) ? <ResultBlock lane={lane} screenSaid={screenSaid} done={doneHead} /> : null}
      {unreadParts(lane).map(([part, reason]) => (
        <NotReadLine key={part} part={part} reason={reason} testId={`lane-not-read-${part.toLowerCase()}`} />
      ))}
      {raw ? <RawPane /> : null}
      {!raw && onlyBrief && !done && !reviewResult(lane.launch.review) ? (
        <section className="lw-work-empty" data-testid="lane-work-empty" aria-label="Its work">
          {screenSaid ? (
            <>
              <span className="lw-work-caption">Its last words</span>
              <AgentWords className="lw-ev-text" text={screenSaid} />
            </>
          ) : (
            <>
              <span className="lw-work-caption">No steps reported yet</span>
              <span className="lw-work-line">{agent || "The agent"} reports each step here when it uses a tool. Terminal shows its screen now.</span>
            </>
          )}
        </section>
      ) : null}
      {compact ? (
        <div className="lw-col">
          {objects}
          {rail}
        </div>
      ) : (
        <div className="lw-cols">
          {rail}
          <div className="lw-col lw-objects-col">
            {objects}
          </div>
        </div>
      )}
      <FoldGadget title="Details" className="lw-details">
        {/* W4 AGENT 2 (slice 2): the recorded stages as dots and words. */}
        <ol className="lw-track" data-testid="lane-track" aria-label="Recorded stages">
          {stations.filter((s) => s.state !== "ahead").map((station) => (
            <li key={station.word} className="lw-track-step" data-state={station.state} aria-current={station.state === "current" ? "step" : undefined}>
              <DotWord tone={station.state === "current" || station.tone !== "ok" ? station.tone ?? "idle" : "ok"}>
                {sentenceCaps(station.word)}
              </DotWord>
              {station.sub && station.sub !== "—" ? <span className="lw-track-sub">{` · ${sentenceCaps(String(station.sub))}`}</span> : null}
            </li>
          ))}
        </ol>
      </FoldGadget>
    </div>
  );
}

/** W3 AGENT WINDOW: what the agent made, as object rows: the PR (its checks
 *  and review as dots and words), the branch, the files changed. */
function LaneObjects({ lane, itemTitle, branch, base }: { lane: LaneWire; itemTitle: string; branch?: string; base: string }) {
  const pr = lane.follow_through?.pr;
  const worktree = lane.worktree;
  const checks = checksSummary(pr?.checks);
  const review = prReviewWords(pr?.review_decision);
  const files = isNotRead(worktree) ? null : worktree.files;
  if (!(pr && pr.number != null) && !branch && !files?.length && !isNotRead(worktree)) return null;
  return (
    <section className="lw-objects" aria-label="It made">
      <span className="lw-objects-cap">It made</span>
      {pr && pr.number != null ? (
        <div className="lw-obj" data-testid="lane-pr" title={pr.url ?? undefined}>
          <img className="lw-obj-sprite" src={spriteUrl("pr", `pr-${pr.number}`, "rest", null, 20)} alt="" width={20} height={20} draggable={false} />
          <span className="lw-obj-text">
            <span className="lw-obj-title">{`#${pr.number} ${pr.title || itemTitle}`}</span>
            {pr.title && itemTitle ? <span className="lw-obj-sub" data-testid="lane-pr-item">{itemTitle}</span> : null}
          </span>
          <span className="lw-obj-facts">
            {checks ? (
              <DotWord tone={checks.failed ? "fail" : checks.running ? "warn" : "ok"} data-testid="lane-pr-checks">
                {`Checks ${checks.passed} of ${checks.total}`}
              </DotWord>
            ) : null}
            <DotWord tone={review.tone} data-testid="lane-pr-review">{review.word}</DotWord>
          </span>
        </div>
      ) : null}
      {branch ? (
        <div className="lw-obj">
          <img className="lw-obj-sprite" src={spriteUrl("repository", `branch-${branch}`, "rest", null, 20)} alt="" width={20} height={20} draggable={false} />
          <span className="lw-obj-text">
            <code className="lw-obj-code" data-testid="lane-branch">{branch}</code>
            {base ? <span className="lw-obj-sub">{`into ${base}`}</span> : null}
          </span>
        </div>
      ) : null}
      {isNotRead(worktree) ? (
        <div className="lw-files-notread"><NotReadLine part="FILES" reason={worktree.not_read} testId="lane-files-not-read" /></div>
      ) : files && files.length ? (
        <div className="lw-files" data-testid="lane-files">
          <span className="lw-files-cap">{filesWords(files.length)}</span>
          {files.map((f) => (
            <code key={f.path} className="lw-file">{f.path}</code>
          ))}
        </div>
      ) : null}
    </section>
  );
}

/** The PR's review in sentence case, as a dot and a word. */
function prReviewWords(decision: string | null | undefined): { word: string; tone: "ok" | "warn" | "fail" | "idle" } {
  const d = String(decision ?? "").toUpperCase();
  if (d === "APPROVED") return { word: "Approved", tone: "ok" };
  if (d === "CHANGES_REQUESTED") return { word: "Changes asked", tone: "fail" };
  if (d === "REVIEW_REQUIRED") return { word: "Review asked", tone: "warn" };
  return { word: "No review yet", tone: "idle" };
}

/** The step entries with their verbs (Brief on the brief) and, while the
 *  agent asks, the wait as the last step. */
function stepEntries(lane: LaneWire, entries: readonly LaneEntry[], briefOpen: boolean, toggleBrief: () => void): StepEntry[] {
  const out: StepEntry[] = entries.map((entry: LaneEntry) => {
    const { gated: _gated, ...rest } = entry;
    if (entry.kind === "brief" && lane.launch.brief_text) {
      return {
        ...rest,
        verbs: (
          <Button dense variant="ghost" aria-pressed={briefOpen} onClick={toggleBrief} data-testid="lane-brief">
            Brief
          </Button>
        ),
      };
    }
    // PHILO-17 THE REFIT: a held call's Deny / Approve live on the held
    // plate at the top of the lane (heldNow), not on the list.
    return rest;
  });
  const wait = isNotRead(lane.wait) ? null : lane.wait;
  if (wait?.question && (wait.kind === "TO ANSWER" || wait.kind === "TO APPROVE") && !turnEndWord(wait) && turnWord(wait).word === "ASKS") {
    out.push({ id: "asks", at: wireDate(wait.started)?.getTime() ?? null, time: wireClock(wait.started), kind: "asks", word: "ASKS",
      text: wait.kind === "TO APPROVE" ? "to run a call · above" : "above" });
  }
  return out;
}

function DecideVerbs({ call }: { call: LaneGated }) {
  // The held plate's verbs: Approve is the lane's one first move.
  const [busy, setBusy] = useState(false);
  const pending = useRef(false);
  const [decidedId, setDecidedId] = useState<string | null>(null);
  const [failure, setFailure] = useState<{ label: string; retry(): void } | null>(null);
  const recoverRead = async () => {
    if (pending.current) return;
    pending.current = true;
    setBusy(true);
    try {
      await useGate.getState().refresh();
      await useLane.getState().load();
      const error = useGate.getState().error ?? useLane.getState().error;
      setFailure(error ? { label: `Decision read failed · Decisions unchanged · Retry · ${error}`, retry: () => void recoverRead() } : null);
    } finally {
      pending.current = false;
      setBusy(false);
    }
  };
  const decide = async (decision: "approved" | "denied") => {
    if (pending.current || decidedId === call.id) return;
    pending.current = true;
    setBusy(true);
    setFailure(null);
    try {
      await useGate.getState().decide(call.id, decision);
      setDecidedId(call.id);
      await useLane.getState().load();
      const error = useGate.getState().error ?? useLane.getState().error;
      if (error) setFailure({ label: `Decision saved · Decision read failed · Retry · ${error}`, retry: () => void recoverRead() });
    } catch (error) {
      setFailure({
        label: `${decision === "approved" ? "Approve" : "Deny"} failed · ${readableError(error)}`,
        retry: () => void decide(decision),
      });
      await useLane.getState().load();
    } finally {
      pending.current = false;
      setBusy(false);
    }
  };
  return (
    <>
      {failure ? <ActionNotice tone="danger" role="alert" action={busy ? undefined : { label: "Retry", onClick: failure.retry }}>{failure.label}</ActionNotice> : null}
      {decidedId === call.id ? null : <>
      <Button dense variant="ghost" disabled={busy} onClick={() => void decide("denied")} data-testid="lane-deny">
        Deny
      </Button>
      {/* PHILO-14 A5: a call the hub cannot show whole is never approved
          here; Terminal shows the live pane with the whole command. */}
      {call.args_cut ? (
        <Button dense variant="secondary" onClick={() => useLane.getState().setRaw(true)} data-testid="lane-raw-cut">
          Terminal
        </Button>
      ) : (
        <Button dense variant="primary" disabled={busy} onClick={() => void decide("approved")} data-testid="lane-approve">
          Approve
        </Button>
      )}
      </>}
    </>
  );
}

/** A part of the lane that could not be read: `Files not read · <reason>`
 * (UX-CANON A.10), never an empty list; quiet sans in sentence case (W5-WORDS). */
function NotReadLine({ part, reason, testId }: { part: string; reason: string; testId?: string }) {
  const word = part.charAt(0).toUpperCase() + part.slice(1).toLowerCase();
  return (
    <p className="lw-notread" role="status" data-testid={testId}>
      {`${word} not read · ${reason}`}
    </p>
  );
}

/* ── the wait ─────────────────────────────────────────────────────── */

function WaitWell({ lane, agent, shared = null }: { lane: LaneWire; agent: string; shared?: LaneShared["key"] | null }) {
  const wait = lane.wait;
  if (isNotRead(wait)) return <NotReadLine part="ASKS" reason={wait.not_read} />;
  if (!wait || !wait.question) return null;
  // W4 AGENT 2: a done turn is not a wait: its Result (below) says it.
  if (shared === "done" && turnWord(wait).word !== "ASKS") return null;
  if (wait.kind === "TO ANSWER") return <AnswerWell lane={lane} wait={wait} agent={agent} />;
  // TO APPROVE: the held plate above says it (HeldPlate).
  if (wait.kind === "TO APPROVE") return null;
  const turn = turnEndWord(wait) ? (shared === "idle" ? "IDLE" : turnEndWord(wait)) : null;
  if (turn) {
    // PHILO-15 15: the agent's last words, as a fact; not a wait for you.
    return (
      <div className="lw-deciding" data-testid="lane-turn-end" data-turn={turn.toLowerCase()}>
        <DotWord tone={turn === "DONE" ? "ok" : "info"} className="lw-turn-word">{turn === "DONE" ? "Done" : "Idle"}</DotWord>
        <AgentWords className="lw-ev-text" text={wait.question} />
      </div>
    );
  }
  if (wait.kind === "DECIDING") {
    // W4 AGENT 2 (slice 2): the same soft plate as the waiting card.
    const age = waitAge(wait.started);
    return (
      <section className="lw-soft-plate" data-tone="info" data-testid="lane-deciding" aria-label="HoldSpeak decides">
        <header className="ask-well-head">
          <span className="ask-well-state" data-tone="info"><span className="ask-well-dot" aria-hidden="true" />HoldSpeak decides</span>
          {age ? <span className="ask-well-age">{`Asked ${age} ago`}</span> : null}
        </header>
        <AgentWords className="lw-ask-q" text={wait.question} />
      </section>
    );
  }
  return null;
}

/** TO ANSWER: the ask well. The answer goes to the lane's own session (its
 * launch's registered key) and names the wait it answers; the field is that
 * session's steer draft. */
function AnswerWell({ lane, wait, agent }: { lane: LaneWire; wait: LaneWait; agent: string }) {
  const key = laneSessionKey(lane);
  const sending = useLane((s) => s.sending);
  const answerSeq = useLane((s) => s.answerSeq);
  const scope = `steer:${key || "unattached"}`;
  const { value, setDraft } = useDurableDraft(scope);
  const draft = wait.draft?.text?.trim() || undefined;
  const inputRef = useRef<HTMLInputElement | null>(null);
  const answer = async (text: string) => {
    if (await useLane.getState().send(text, { waitId: wait.wait_id ?? null })) setDraft("");
  };
  return (
    <AskWell
      data-testid="lane-ask"
      plate
      // PHILO-17: one filled primary. When the held plate's Approve shows,
      // it is the lane's first move and Answer is quieter.
      primary={!approveShowing(lane)}
      agent={agent}
      word={turnWord(wait).word}
      age={waitAge(wait.started)}
      question={String(wait.question)}
      value={value}
      onChange={setDraft}
      onAnswer={(text) => void answer(text)}
      draft={draft}
      onUseDraft={(text) => {
        setDraft(text);
        inputRef.current?.focus();
      }}
      busy={sending}
      disabled={!key || Boolean(lane.control && !isNotRead(lane.control) && lane.control.pane === false)}
      listenSignal={answerSeq}
      draftScope={scope}
      inputRef={inputRef}
      // Betterment AG2: Answer needs no ARM (the press is the authority for
      // this wait); the ARM stays behind Terminal with the keys.
      arm={lane.control && !isNotRead(lane.control) && lane.control.pane === false ? <span className="lw-quiet" data-testid="lane-terminal-unavailable">Terminal unavailable</span> : <TerminalGone />}
    />
  );
}

/** Secure and Normal: the lane's ARM, where the action is, with the mode.
 * Absent when the session is armed or the policy lets the owner type (YOLO). */
/** Betterment AG0/AG2: an answer or ARM the hub refused because the pane is
 * gone says so where the ARM was. */
function TerminalGone() {
  const terminalGone = useLane((s) => s.terminalGone);
  return terminalGone ? <span className="lw-fact" data-testid="lane-terminal-gone">{TERMINAL_GONE_WORDS}</span> : null;
}

function ArmLine({ lane, compact = false }: { lane: LaneWire; compact?: boolean }) {
  const control = lane.control;
  const terminalGone = useLane((s) => s.terminalGone);
  if (terminalGone) {
    return <span className="lw-fact" data-testid={compact ? "lane-terminal-gone-footer" : "lane-terminal-gone"}>{TERMINAL_GONE_WORDS}</span>;
  }
  if (!control || isNotRead(control) || control.pane === false || control.direct || control.armed || !laneSessionKey(lane)) return null;
  return (
    <span className="lw-arm" data-testid={compact ? "lane-arm-footer" : "lane-arm"}>
      <span className="lw-fact">{`${controlModeLabel(control.mode)} · arm first`}</span>
      <TransportKey compact label="ARM" glyph="⏻" title="Arm this pane" onClick={() => void useLane.getState().arm()} />
    </span>
  );
}

/** The lane's receipts, kept when the well that made them closes or the
 * wait clears: the stop (from the launch), the last send or refusal. */
function LaneReceipts({ lane }: { lane: LaneWire }) {
  const receipt = useLane((s) => s.receipt);
  const stopped = lane.launch.stopped;
  const answers = Array.isArray(lane.answers) ? lane.answers : [];
  // PHILO-15 15 (B47): an answer the desk typed is its own receipt, named
  // as the desk's (never the owner's SENT).
  const last = [...answers].reverse().find((a) => (a.outcome === "delivered" || a.outcome === "auto_answered") && a.text_head);
  const lastAt = last ? wireDate(last.ts)?.getTime() : undefined;
  // PHILO-15 15 (B47): an answer the desk typed is its own receipt.
  const word = last?.outcome === "auto_answered" ? "The desk answered" : "Sent";
  const shown = receipt ?? (last ? { word, at: lastAt, text: String(last.text_head), tone: "ok" as const } : null);
  const queuedList = Array.isArray(lane.launch.queued_rebriefs)
    ? lane.launch.queued_rebriefs.filter((q) => q?.text)
    : lane.launch.queued_rebrief?.text ? [lane.launch.queued_rebrief] : [];
  const queued = !stopped && queuedList.length ? queuedList : null;
  // Phase 16: what was typed into the agent (the brief, an answer) is drawn
  // by AgentWords, cut at a whole word; the other receipts are tokens.
  const sentWords = Boolean(shown && /^(SENT|Sent|The desk answered)$/.test(shown.word) && shown.text);
  return (
    <>
      {stopped ? <ReceiptTokens testId="lane-stopped" word="Stopped by you" at={wireDate(stopped.at)?.getTime()} /> : null}
      {queued
        ? queued.map((q, i) => (
            <div className="lw-queued" key={String(q.id ?? i)}>
              <ReceiptTokens
                testId="lane-queued"
                tone="warn"
                word={i === 0 ? "Queued after this turn" : `Queued after ${i + 1} turns`}
                text={String(q.text)}
              />
              {q.id ? (
                <Button
                  dense
                  variant="ghost"
                  data-testid="lane-take-back"
                  aria-label={`Take back: ${String(q.text)}`}
                  onClick={() => void useLane.getState().takeBack(String(q.id), String(q.text ?? ""))}
                >
                  Take back
                </Button>
              ) : null}
            </div>
          ))
        : null}
      {shown && !(stopped && shown.word === "STOPPED") && !(queued && shown.word === "QUEUED") ? (
        <ReceiptTokens
          testId="lane-receipt"
          tone={shown.tone}
          word={shown.word}
          at={shown.at}
          text={sentWords ? "" : shown.text}
          words={sentWords ? (receipt ? shown.text : sentHead(shown.text)) : undefined}
        />
      ) : null}
    </>
  );
}

/** The hub keeps the first 120 characters of what was typed
 *  (`TEXT_HEAD_CHARS`, holdspeak/db/steering.py): a head that long was cut,
 *  maybe inside a word, so its last word goes and `…` says so (Phase 16:
 *  the owner saw `…line". P`). */
export const SENT_HEAD_CHARS = 120;
export function sentHead(text: string): string {
  const raw = String(text ?? "");
  if (raw.length < SENT_HEAD_CHARS) return raw;
  const flat = raw.replace(/\s+/g, " ").trim();
  const space = flat.lastIndexOf(" ");
  return space > 0 ? `${flat.slice(0, space).replace(/[\s·]+$/, "")} …` : cutAtWord(flat, flat.length);
}

/** One receipt (W4 AGENT 2, slice 2): a dot and a sentence-case word, the
 *  age quiet (`6 min ago`), then what was sent: one or two lines by
 *  AgentWords (compact), or the receipt's own fact. */
function ReceiptTokens({ word, at, text, tone, testId, words }: {
  word: string; at?: number; text?: string; tone?: string; testId: string; words?: string;
}) {
  const dot = tone === "ok" || tone === "warn" || tone === "fail" ? tone : "idle";
  const when = at ? spokeWord(new Date(at)) : "";
  const head = (
    <>
      <DotWord tone={dot} className="lw-receipt-word">{sentenceCaps(word)}</DotWord>
      {when ? <span className="lw-receipt-age">{` · ${when}`}</span> : null}
      {text ? <span className="lw-receipt-fact">{` · ${sentenceCaps(text)}`}</span> : null}
    </>
  );
  if (!words?.trim()) {
    return (
      <p className="lw-receipt" data-tone={tone} data-testid={testId}>
        {head}
      </p>
    );
  }
  return (
    <div className="lw-receipt lw-receipt-words" data-tone={tone} data-testid={testId}>
      <span className="lw-receipt-head">{head}{" · "}</span>
      <AgentWords compact lines={2} ask={false} className="lw-receipt-text" text={words} />
    </div>
  );
}

/** The call the gate holds now (the newest held one the Control mode held). */
export function heldNow(lane: LaneWire): LaneGated | undefined {
  const gated = Array.isArray(lane.gated) ? lane.gated : [];
  return [...gated].reverse().find((g) => (g.state === "held" || g.state === "pending") && g.was_held !== false);
}

/** The held plate shows a filled Approve (a held call the hub shows whole). */
export function approveShowing(lane: LaneWire): boolean {
  const held = heldNow(lane);
  return Boolean(held && !held.args_cut);
}

/** Atlas pass 2: a launch whose session left, in the Agents list's words. */
export function goneWord(flight: Pick<AgentFlight, "state">): string {
  if (flight.state === "expired") return "Session gone";
  if (flight.state === "stopped_by_restart") return "Stopped by restart";
  if (flight.state === "resume_failed") return "Could not resume";
  if (flight.state === "checked") return "Done · checked by you";
  return "Ended";
}

/** Start again: a new agent on the same item (Hand again, as Agents does). */
function againRef(flight: AgentFlight): ReturnType<typeof handRefOf> {
  return handRefOf(`${flight.kind}:${flight.id}`) ?? handRefOf(flight.originRef);
}

function startAgain(flight: AgentFlight): void {
  const ref = againRef(flight);
  if (!ref) return;
  openHand({ kind: ref.kind, id: ref.id, title: flight.title, projectId: flight.projectId || null, agent: flight.agent as AgentId });
}

/** W4 AGENT 2: the launch's one state, as the Agents row says it. */
export interface LaneShared {
  key: LiveState | "merged";
  word: string;
  tone: "ok" | "warn" | "info" | "idle";
  /** A done turn's end (the hub's `done_at`). */
  doneAt?: string | null;
}

/** The launch's state from the hub's flight and its session row (the
 *  Agents row's own derivation, `members.launchLive`); null with no flight
 *  read yet. The open window has seen a done turn: it says Done. */
export function sharedState(flight: AgentFlight | null | undefined, row: CoderSessionRow | null = null): LaneShared | null {
  if (!flight) return null;
  if (flight.state === "merged") {
    return { key: "merged", word: flight.pr?.number != null ? `PR #${flight.pr.number} merged` : "Merged", tone: "ok" };
  }
  const key = launchLive(flight, row);
  const said = liveWord(key, {
    pr: flight.pr?.number ?? null,
    phase: flight.state === "starting" ? "starting" : flight.state === "resuming" ? "resuming" : null,
  });
  return { key, word: said.word, tone: said.tone === "danger" ? "warn" : said.tone, doneAt: key === "done" ? flight.doneAt ?? null : null };
}

/** PHILO-17 THE REFIT: what the coder does now, as the lane's one headline:
 *  the Agents row's word (W4 AGENT 2). A call the gate holds now is the
 *  lane's own fact (the plate above): it says so first. */
export function laneDoing(
  lane: LaneWire, agent: string,
  shared: LaneShared | null = null,
): { word: string; tone: "ok" | "warn" | "info" | "idle"; key: LaneShared["key"] | "stopped" | "gone" } {
  void agent;
  if (lane.launch.stopped) return { word: "Stopped by you", tone: "idle", key: "stopped" };
  // AG12: a durable pair finding is the owner-facing state on every face.
  if (lane.launch.review?.status === "needs_you" || shared?.key === "needs_you") return { word: "Needs you", tone: "warn", key: "needs_you" };
  if (heldNow(lane)) return { word: "Wants to run", tone: "warn", key: "held" };
  if (shared) return shared;
  // No flight read yet: the lane's own read, in the same words.
  const wait = isNotRead(lane.wait) ? null : lane.wait;
  if (wait?.kind === "TO APPROVE") return { word: "Wants to run", tone: "warn", key: "held" };
  const turn = wait ? (turnEndWord(wait) ?? (wait.question && wait.kind === "TO ANSWER" && turnWord(wait).word !== "ASKS" ? turnWord(wait).word : null)) : null;
  if (turn === "DONE") return { word: "Done", tone: "ok", key: "done" };
  if (turn === "IDLE") return { word: "Idle", tone: "idle", key: "idle" };
  if (wait?.question && (wait.kind === "TO ANSWER" || wait.kind === "DECIDING")) return { word: "Asks you", tone: "warn", key: "ask" };
  const pr = lane.follow_through?.pr;
  if (pr?.number != null && pr.state === "merged") return { word: `PR #${pr.number} merged`, tone: "ok", key: "merged" };
  return { word: "Working", tone: "info", key: "work" };
}

/** When the agent last reported a step: its newest event. (The hub's
 *  screen read time is when the desk looked, not when the agent spoke, so
 *  it is not used.) */
function lastStep(events: readonly LaneEvent[]): Date | null {
  const times = events.map((event) => wireDate(event.ts)).filter((date): date is Date => Boolean(date));
  if (!times.length) return null;
  return new Date(Math.max(...times.map((date) => date.getTime())));
}

function spokeWord(at: Date, now: number = Date.now()): string {
  const minutes = Math.floor((now - at.getTime()) / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  if (minutes < 24 * 60) return `${Math.floor(minutes / 60)} h ago`;
  return `on ${at.toLocaleDateString([], { month: "short", day: "numeric" })}`;
}

/** The held call on a focus plate: the Workbench title bar, the call (its
 * reason and command), Deny and Approve. A call the hub cannot show whole is
 * never approved here: Raw shows it whole (PHILO-14 A5). A permission prompt
 * the gate does not hold is answered in the pane: Raw. */
function HeldPlate({ lane, agent }: { lane: LaneWire; agent: string }) {
  const held = heldNow(lane);
  const wait = isNotRead(lane.wait) ? null : lane.wait;
  const asks = wait?.kind === "TO APPROVE" && wait.question ? wait : null;
  if (!held && !asks) return null;
  const age = waitAge(asks?.started ?? held?.created_at);
  const reason = held?.hold_reason ? reasonWords(held.hold_reason) : null;
  // W4 AGENT 2 (slice 2): the soft plate of the waiting card: the head a dot
  // and a word with the age quiet, the reason in sentence case, the call as
  // code (the one mono part), Deny / Approve.
  return (
    <section className="lw-plate lw-soft-plate" data-tone="warn" aria-label={`${agent} wants to run`} data-testid="lane-approve-well">
      <header className="ask-well-head">
        <span className="ask-well-state" data-tone="warn"><span className="ask-well-dot" aria-hidden="true" />Wants to run</span>
        {age ? <span className="ask-well-age">{`${age} ago`}</span> : null}
      </header>
      {asks ? <AgentWords className="lw-ask-q" text={String(asks.question)} /> : null}
      {held ? (
        <div className="lw-plate-callbox" data-testid="lane-held-call">
          {reason ? (
            <span className="lw-plate-why">
              {reason.word}
              {reason.target ? <code className="lw-plate-target">{reason.target}</code> : null}
            </span>
          ) : null}
          <code className="lw-plate-call">{gatedHead(held)}</code>
        </div>
      ) : null}
      <div className="lw-plate-verbs">
        {held ? (
          <DecideVerbs call={held} />
        ) : (
          <Button dense variant="primary" onClick={() => useLane.getState().setRaw(true)}>
            Terminal
          </Button>
        )}
      </div>
    </section>
  );
}

/** The gate's hold reason (`OUTSIDE THE WORKTREE · /tmp/x`) in his words:
 *  the reason in sentence case, the path or command word as code. */
export function reasonWords(reason: string): { word: string; target: string } {
  const [head, ...rest] = String(reason).split(" · ");
  return { word: sentenceCaps(head), target: rest.join(" · ") };
}

/** `HUB UNREACHABLE` → `Hub unreachable`; a token with any lower case letter
 *  (an agent's words, a path) stays as it is; `PR` keeps its caps. */
export function sentenceCaps(token: string): string {
  const text = String(token ?? "");
  if (!/[A-Z]/.test(text) || /[a-z]/.test(text)) return text;
  const lower = text.toLowerCase().replace(/\bpr\b/g, "PR");
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}

/** Tell it (was Re-brief; Betterment AG1): the owner's new instruction to
 * the lane's own agent, in his own words. The hub types it now when the
 * agent is idle or asks; mid-turn it is QUEUED · AFTER THIS TURN
 * (PHILO-15 B46). */
function RebriefWell() {
  const sending = useLane((s) => s.sending);
  const [text, setText] = useState("");
  const ready = text.trim().length > 0;
  const send = async () => {
    if (!ready) return;
    if (await useLane.getState().sendRebrief(text.trim())) useLane.getState().setRebrief(false);
  };
  return (
    <section className="lw-ask" aria-label="Tell it" data-testid="lane-rebrief-well">
      <p className="lw-caption">Tell it</p>
      <div className="lw-ask-row">
        <StringGadget
          label="Tell it"
          value={text}
          onChange={setText}
          micLabel="Speak what to tell it"
          autoFocus
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.nativeEvent.isComposing) {
              event.preventDefault();
              void send();
            }
          }}
        />
        <Button variant="primary" disabled={!ready || sending} onClick={() => void send()}>
          Send
        </Button>
        <Button variant="ghost" onClick={() => useLane.getState().setRebrief(false)}>
          Back
        </Button>
      </div>
    </section>
  );
}

/* ── Raw ──────────────────────────────────────────────────────────── */

/** PHILO-15 20 (B63): the whole command of a held CUT call, read from the
 * hub (it keeps it for this read only, never for the agent), with Deny and
 * Approve. The Needs row and the lane rail say `CUT · APPROVE IN RAW`. */
interface FullCall {
  id: string;
  state: string;
  command: string;
  /** The text kept has the length the hook declared (Astra r1 on #1011). */
  whole: boolean;
  shown_chars?: number;
  declared_chars?: number;
  hold_reason?: string;
}

function RawHeldCall({ call }: { call: LaneGated }) {
  const [full, setFull] = useState<FullCall | null>(null);
  const [notRead, setNotRead] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let live = true;
    apiFetch<FullCall>(`/api/gate/proposals/${encodeURIComponent(call.id)}/command`)
      .then((data) => {
        if (!live) return;
        // A read with no command text is said, never drawn as a call.
        if (data && typeof data.command === "string") setFull(data);
        else setNotRead("NO COMMAND");
      })
      .catch((err: unknown) => {
        if (live) setNotRead(err instanceof Error ? err.message : String(err));
      });
    return () => {
      live = false;
    };
  }, [call.id]);
  const decide = async (decision: "approved" | "denied") => {
    setBusy(true);
    try {
      // The hub's answer is the receipt: what it decided, and when (a call
      // decided elsewhere first answers 409 with its standing state).
      const done = await apiFetch<{ state?: string; decided_at?: number | null }>(
        `/api/gate/proposals/${encodeURIComponent(call.id)}/decide`,
        { method: "POST", json: { decision, actor: "owner" } },
      );
      const state = String(done?.state ?? decision);
      const at = done?.decided_at ? done.decided_at * 1000 : Date.now();
      useLane.getState().setReceipt({
        word: state === "approved" ? "APPROVED" : "DENIED", at, text: "", tone: state === "approved" ? "ok" : "warn",
      });
    } catch (err: unknown) {
      const standing = err instanceof ApiError ? String((err.payload as { state?: string } | undefined)?.state ?? "") : "";
      useLane.getState().setReceipt({
        word: "NOT DECIDED", at: Date.now(), text: standing ? `Already ${standing.replace(/_/g, " ")}` : "Hub unreachable", tone: "fail",
      });
    } finally {
      setBusy(false);
      void useGate.getState().refresh();
      void useLane.getState().load();
    }
  };
  const reason = full?.hold_reason || call.hold_reason || "";
  // A part of the call is never approved: it says how much is there.
  const part = full && !full.whole
    ? `CUT · ${full.shown_chars ?? full.command.length} OF ${full.declared_chars ?? "?"} CHARS`
    : "";
  const caption = stateWords(["HELD", reason, part].filter(Boolean).join(" · "));
  return (
    <section className="lw-ask lw-raw-held" aria-label="Held call" data-testid="lane-raw-held">
      <p className="lw-caption">{caption}</p>
      {notRead ? (
        <p className="lw-notread" role="status">{`Call not read · ${notRead}`}</p>
      ) : full ? (
        <pre className="lw-raw-command" data-testid="lane-raw-command">{full.command}</pre>
      ) : (
        <p className="lw-notread">Reading the call</p>
      )}
      <div className="lw-verbs">
        <Button dense variant="ghost" disabled={busy} onClick={() => void decide("denied")} data-testid="lane-raw-deny">
          Deny
        </Button>
        {full?.whole ? (
          <Button dense variant="primary" disabled={busy} onClick={() => void decide("approved")} data-testid="lane-raw-approve">
            Approve
          </Button>
        ) : null}
      </div>
    </section>
  );
}

function RawPane() {
  const lane = useLane((s) => s.lane);
  const launchId = useLane((s) => s.launchId);
  const gated = lane && Array.isArray(lane.gated) ? lane.gated : [];
  const cut = gated.filter((g) => g.args_cut && (g.state === "held" || g.state === "pending"));
  const paneStatus = useSteering((s) => s.paneStatus);
  const paneDetail = useSteering((s) => s.paneDetail);
  const paneId = useSteering((s) => s.paneId);
  const paneLines = useSteering((s) => s.paneLines);
  const paneRaw = useSteering((s) => s.paneRaw);
  const paneGeom = useSteering((s) => s.paneGeom);
  const paneChangedAt = useSteering((s) => s.paneChangedAt);
  const armed = useSteering((s) => s.armed);
  const postureAuthorized = useSteering((s) => s.postureAuthorized);
  // Betterment AG10: Terminal opens at the bottom: the prompt line, the
  // newest output (the well itself follows the tail).
  const rawRef = useRef<HTMLDivElement>(null);
  const live = paneStatus === "live";
  useEffect(() => {
    if (live) rawRef.current?.querySelector(".terminal-well")?.scrollIntoView?.({ block: "end" });
  }, [live]);
  return (
    <div className="lw-raw" data-testid="lane-raw-pane" ref={rawRef}>
      {/* Betterment AG7: the hook or the screen rule behind the state. */}
      {launchId ? <WhyThisState launchId={launchId} /> : null}
      {cut.map((call) => (
        <RawHeldCall key={call.id} call={call} />
      ))}
      <PaneWell
        live={paneStatus === "live"}
        lines={paneLines}
        raw={paneRaw}
        pane={paneGeom}
        changedAt={paneChangedAt}
        absence={
          <>
            <span>Terminal unavailable · {PANE_STATE_LABEL[paneStatus] || paneStatus}</span>
            {paneDetail ? <span className="lw-pane-detail">{paneDetail}</span> : null}
          </>
        }
      />
      {/* PHILO-17 THE REFIT: the pane's controls fold until asked for. */}
      {paneStatus !== "live" ? <div className="lw-verbs">
        <Button dense variant="ghost" onClick={() => void useSteering.getState().poll()}>Retry</Button>
        <Button dense variant="ghost" onClick={() => useLane.getState().setRaw(false)}>Story</Button>
      </div> : null}
      {paneStatus === "live" && paneId ? <FoldGadget title="Keys" className="lw-keys">
        <ArmStrip />
        {armed || postureAuthorized ? <KeyPalette /> : null}
      </FoldGadget> : null}
    </div>
  );
}

/* ── the toolbar and the status bar ─────────────────────────────── */

/** W3 AGENT WINDOW (canvas direction A): the toolbar by state. Working and
 *  asking: Tell it, Open PR; the answer to a waiting ask is its card's
 *  primary. Done: Open PR is the primary, Tell it continues the work. Stop
 *  (two presses) and the mode's ARM stay at the right end. */
function LaneToolbar({ lane, agent, gone = null, shared = null }: { lane: LaneWire; agent: string; gone?: AgentFlight | null; shared?: LaneShared | null }) {
  const pr = lane.follow_through?.pr;
  const prUrl = pr?.number != null && pr.url ? pr.url : null;
  const sessionKey = lane.launch.stopped || (lane.control && !isNotRead(lane.control) && lane.control.pane === false) ? null : lane.launch.session_key;
  const rebrief = useLane((s) => s.rebrief);
  const canStop = Boolean(lane.launch.session_key && !lane.launch.stopped && (!lane.control || isNotRead(lane.control) || lane.control.pane !== false));
  const armHere = rebrief || !lane.wait || isNotRead(lane.wait) || lane.wait.kind !== "TO ANSWER" || !lane.wait.question;
  const state = laneDoing(lane, agent, shared).key;
  const finished = state === "done" || state === "merged";
  // The one filled primary: Open PR when the work is done and nothing else
  // asks for a press (a held call's Approve, an answer).
  const prPrimary = finished && !approveShowing(lane);
  if (gone) {
    // The session is gone: the one verb that fits is Start again (a new
    // agent on the same item); its PR stays one press away. W4 AGENT 3: a
    // launch he checked (Done) is finished work: Open PR only.
    const again = gone.state !== "checked" && Boolean(againRef(gone));
    if (!again && !prUrl) return null;
    return (
      <Toolbar label="Agent" className="lw-toolbar" data-testid="lane-toolbar">
        {again ? (
          <Button dense variant="primary" data-testid="lane-start-again" onClick={() => startAgain(gone)}>
            <ToolGlyph kind="run" />Start again
          </Button>
        ) : null}
        {prUrl ? (
          <Button dense variant={again ? "secondary" : "primary"} data-testid="lane-open-pr" title={prUrl}
            onClick={() => window.open(prUrl, "_blank", "noopener,noreferrer")}>
            <ToolGlyph kind="open" />Open PR
          </Button>
        ) : null}
      </Toolbar>
    );
  }
  // W4 AGENT 3 (slice 3, canvas direction A): Done: he checked the work of
  // a done turn; the launch closes and leaves Running (the hub's
  // `POST /api/agent/launches/{id}/done`). The primary when no PR leads.
  const doneVerb = state === "done" ? <DoneVerb launchId={lane.launch.launch_id} primary={!prUrl && !approveShowing(lane)} /> : null;
  if (!sessionKey && !prUrl && !canStop && !doneVerb) return null;
  const openPr = prUrl ? (
    <Button
      dense
      variant={prPrimary ? "primary" : "secondary"}
      data-testid="lane-open-pr"
      title={prUrl}
      onClick={() => window.open(prUrl, "_blank", "noopener,noreferrer")}
    >
      <ToolGlyph kind="open" />Open PR
    </Button>
  ) : null;
  const tellIt = sessionKey ? (
    <Button
      dense
      variant="secondary"
      aria-pressed={rebrief}
      data-testid="lane-rebrief"
      onClick={() => useLane.getState().setRebrief(!rebrief)}
    >
      <ToolGlyph kind="ask" />Tell it
    </Button>
  ) : null;
  return (
    <Toolbar
      label="Agent"
      className="lw-toolbar"
      data-testid="lane-toolbar"
      trailingStays
      trailing={canStop ? (
        <span className="lw-toolbar-end">
          {armHere ? <ArmLine lane={lane} compact /> : null}
          {/* Stop retains its own session-control grant and confirmation. */}
          <StopVerb />
        </span>
      ) : undefined}
    >
      {prPrimary || doneVerb ? <>{doneVerb && !prUrl ? doneVerb : null}{openPr}{tellIt}{doneVerb && prUrl ? doneVerb : null}</> : <>{tellIt}{openPr}</>}
    </Toolbar>
  );
}

/** Done (W4 AGENT 3): one press; a refusal is said by the verb (the work
 *  started again, the hub cannot be reached), with Retry. */
function DoneVerb({ launchId, primary }: { launchId: string; primary: boolean }) {
  const [busy, setBusy] = useState(false);
  const [refused, setRefused] = useState<string | null>(null);
  const press = async () => {
    setBusy(true);
    setRefused(null);
    try {
      setRefused(await checkLaunchDone(launchId));
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <Button dense variant={primary ? "primary" : "secondary"} loading={busy} disabled={busy}
        onClick={() => void press()} data-testid="lane-done" title="The work is checked: the agent moves to Ended today">
        <ToolGlyph kind="done" />{refused ? "Try Done again" : "Done"}
      </Button>
      {refused ? <span className="lw-quiet" role="status" data-testid="lane-done-refused">{`Not done · ${refused}`}</span> : null}
    </>
  );
}

/** The status bar: the agent's state as a dot and a word, when it last
 *  reported a step, how many it reported, and the lane's receipts (the stop,
 *  the last send or refusal). */
function LaneFooter({ lane, agent, gone = null, shared = null }: { lane: LaneWire; agent: string; gone?: AgentFlight | null; shared?: LaneShared | null }) {
  const events = useLane((s) => s.events);
  const spoke = lastStep(events);
  const doing = gone
    ? { word: goneWord(gone), tone: gone.state === "checked" ? ("ok" as const) : ("idle" as const) }
    : laneDoing(lane, agent, shared);
  const steps = events.filter(isToolCall).length;
  const finished = !gone && shared?.key === "done" ? wireDate(shared.doneAt ?? null) : null;
  return (
    <StatusBar
      className="lw-footer"
      data-testid="lane-status"
      items={[
        { key: "state", text: doing.word, lamp: doing.tone === "idle" ? undefined : doing.tone, testId: "lane-head" },
        // W4 AGENT 2 (slice 3): the done fact: when the turn ended.
        finished ? { key: "finished", text: `Finished ${spokeWord(finished)}`, testId: "lane-finished" } : null,
        spoke ? { key: "spoke", text: `Last step ${spokeWord(spoke)}`, testId: "lane-last-step" } : null,
        steps ? { key: "steps", text: `${steps} ${steps === 1 ? "step" : "steps"}`, testId: "lane-step-count" } : null,
      ]}
      trailing={<LaneReceipts lane={lane} />}
    />
  );
}

/** Stop: the kill route on the lane's own session, two presses. Secure and
 * Normal need the owner's ARM first (the ARM by it); YOLO arms per press
 * (R6). The second press says what it does. */
function StopVerb() {
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const stop = async () => {
    setBusy(true);
    try {
      if (await useLane.getState().stop()) setConfirm(false);
    } finally {
      setBusy(false);
    }
  };
  if (!confirm) {
    return (
      <Button dense variant="danger" data-testid="lane-stop" onClick={() => setConfirm(true)}>
        Stop
      </Button>
    );
  }
  return (
    <>
      <Button dense variant="ghost" onClick={() => setConfirm(false)}>
        Back
      </Button>
      <Button dense variant="danger" data-testid="lane-stop-confirm" disabled={busy} onClick={() => void stop()}>
        Stop · sure? (ends the agent's session)
      </Button>
    </>
  );
}

