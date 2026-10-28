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
import { GONE, markLaunchSeen, reviewResult, useAgentFlights, type AgentFlight } from "../agentFlights";
import { handRefOf, openHand } from "../agentHand";
import type { AgentId } from "../firstrun/agentsStep";
import { useConductor } from "../conductor/store";
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
  StationTrack,
  StringGadget,
  TransportKey,
} from "../surface";
import { SurfaceWings } from "../surface/wings";
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
  const flightTurn = live?.state === "waiting" && (live.turnEnd === "idle" || live.turnEnd === "done") ? live.turnEnd : null;
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
      {lane ? <LaneToolbar lane={lane} done={flight?.state === "done"} agent={agent} gone={gone} flightTurn={flightTurn} /> : null}
      <LaneBody lane={lane} error={error} raw={raw} agent={agent} compact={compact} itemTitle={flight?.title ?? ""}
        done={flight?.state === "done"} gone={Boolean(gone)} flightTurn={flightTurn} screenSaid={flight?.screen?.said ?? null} />
      {lane ? <LaneFooter lane={lane} agent={agent} done={flight?.state === "done"} gone={gone} flightTurn={flightTurn} /> : null}
    </DeskWindowFrame>
  );
}

function LaneBody({
  lane, error, raw, agent, compact, itemTitle, done = false, screenSaid = null, gone = false, flightTurn = null,
}: {
  flightTurn?: "done" | "idle" | null;
  /** The session is gone (the Agents list's truth): nothing is lit. */
  gone?: boolean;
  screenSaid?: string | null;
  /** Betterment AG10: the turn is done; its Result leads the Story. */
  done?: boolean;
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
  const bodyRef = useRef<HTMLDivElement>(null);

  const onScroll = () => {
    const el = bodyRef.current;
    if (!el || !more || raw) return;
    if (el.scrollTop + el.clientHeight >= el.scrollHeight - 120) void useLane.getState().load();
  };

  if (!lane) {
    return (
      <div className="desk-pullout-body lw-body" data-testid="lane-body">
        {error ? <NotReadLine part="LANE" reason={error} /> : <p className="lw-notread">LANE · READING</p>}
      </div>
    );
  }

  const stations = laneStations(lane, events);
  const pr = lane.follow_through?.pr;
  const worktree = lane.worktree;
  const branch = branchFace(lane.launch.branch ?? (isNotRead(worktree) ? null : worktree.branch)) || undefined;
  const base = isNotRead(worktree) ? "" : baseWord(worktree.base);
  const doing = gone ? { word: "", tone: "idle" as const } : laneDoing(lane, agent, done, flightTurn);
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
  const lit = doing.tone === "info" && doing.word.endsWith("is working")
    ? [...steps].reverse().find((s) => s.at != null && s.kind !== "brief")?.id ?? null
    : steps.find((s) => s.kind === "asks")?.id ?? null;
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
      <StepList data-testid="lane-rail" entries={steps} lit={lit} />
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
          <WaitWell lane={lane} agent={agent} flightTurn={flightTurn} />
        </>
      )}
      {!raw && (done || Boolean(reviewResult(lane.launch.review))) ? <ResultBlock lane={lane} screenSaid={screenSaid} /> : null}
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
        <StationTrack data-testid="lane-track" label="Recorded stages" stations={stations.filter((s) => s.state !== "ahead")} />
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
        <NotReadLine part="FILES" reason={worktree.not_read} testId="lane-files-not-read" />
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

/** A part of the lane that could not be read: `PART · NOT READ · <reason>`
 * (UX-CANON A.10), never an empty list. */
function NotReadLine({ part, reason, testId }: { part: string; reason: string; testId?: string }) {
  return (
    <p className="lw-notread" role="status" data-testid={testId}>
      {part} · NOT READ · {reason}
    </p>
  );
}

/* ── the wait ─────────────────────────────────────────────────────── */

function WaitWell({ lane, agent, flightTurn = null }: { lane: LaneWire; agent: string; flightTurn?: "done" | "idle" | null }) {
  const wait = lane.wait;
  if (isNotRead(wait)) return <NotReadLine part="ASKS" reason={wait.not_read} />;
  if (!wait || !wait.question) return null;
  if (wait.kind === "TO ANSWER") return <AnswerWell lane={lane} wait={wait} agent={agent} />;
  // TO APPROVE: the held plate above says it (HeldPlate).
  if (wait.kind === "TO APPROVE") return null;
  const turn = turnEndWord(wait) ? (flightTurn ? (flightTurn === "done" ? "DONE" : "IDLE") : turnEndWord(wait)) : null;
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
    return (
      <div className="lw-deciding" data-testid="lane-deciding">
        <span className="lw-word">HoldSpeak decides</span>
        <AgentWords className="lw-ev-text" text={wait.question} />
      </div>
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
      <span className="lw-fact">{`${controlModeLabel(control.mode).toUpperCase()} · ARM FIRST`}</span>
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
  const word = last?.outcome === "auto_answered" ? "THE DESK ANSWERED" : "SENT";
  const shown = receipt ?? (last ? { word, at: lastAt, text: String(last.text_head), tone: "ok" as const } : null);
  const queuedList = Array.isArray(lane.launch.queued_rebriefs)
    ? lane.launch.queued_rebriefs.filter((q) => q?.text)
    : lane.launch.queued_rebrief?.text ? [lane.launch.queued_rebrief] : [];
  const queued = !stopped && queuedList.length ? queuedList : null;
  // Phase 16: what was typed into the agent (the brief, an answer) is drawn
  // by AgentWords, cut at a whole word; the other receipts are tokens.
  const sentWords = Boolean(shown && (shown.word === "SENT" || shown.word === "THE DESK ANSWERED") && shown.text);
  return (
    <>
      {stopped ? <ReceiptTokens testId="lane-stopped" tokens={["STOPPED", wireClock(stopped.at), "BY YOU"]} /> : null}
      {queued
        ? queued.map((q, i) => (
            <div className="lw-queued" key={String(q.id ?? i)}>
              <ReceiptTokens
                testId="lane-queued"
                tone="warn"
                tokens={["QUEUED", i === 0 ? "AFTER THIS TURN" : `AFTER ${i + 1} TURNS`, String(q.text)]}
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
          tokens={[shown.word, shown.at ? wireClock(shown.at) : "", sentWords ? "" : shown.text]}
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

/** One receipt: tokens joined by ` · ` (the word, the time), then what was
 *  sent: one or two lines by AgentWords (compact). */
function ReceiptTokens({ tokens, tone, testId, words }: { tokens: string[]; tone?: string; testId: string; words?: string }) {
  const shown = tokens.filter(Boolean);
  if (!words?.trim()) {
    return (
      <p className="lw-receipt" data-tone={tone} data-testid={testId}>
        {shown.join(" · ")}
      </p>
    );
  }
  return (
    <div className="lw-receipt lw-receipt-words" data-tone={tone} data-testid={testId}>
      <span className="lw-receipt-head">{`${shown.join(" · ")} · `}</span>
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

/** PHILO-17 THE REFIT: what the coder does now, as the lane's one headline. */
export function laneDoing(
  lane: LaneWire, agent: string, done = false,
  /** The flight's own turn end (the Agents list reads it): it leads the
   *  lane's wait when the two differ, so both faces say the same word. */
  flightTurn: "done" | "idle" | null = null,
): { word: string; tone: "ok" | "warn" | "info" | "idle" } {
  const name = agent || "The agent";
  if (lane.launch.stopped) return { word: "Stopped by you", tone: "idle" };
  // AG12: a durable pair finding is the lane's owner-facing state. Keep the
  // lane headline aligned with the ordinary row while the builder waits for
  // the owner's correction; the persisted pair Result remains below it.
  if (lane.launch.review?.status === "needs_you") return { word: `${name} needs you`, tone: "warn" };
  // Betterment AG10: the flight knows the turn is done (also from a screen,
  // with no hook to say it); the head never says "working" then.
  if (done) return { word: `${name} is done`, tone: "ok" };
  const wait = isNotRead(lane.wait) ? null : lane.wait;
  if (heldNow(lane) || wait?.kind === "TO APPROVE") return { word: `${name} wants to run`, tone: "warn" };
  if (wait?.question && wait.kind === "TO ANSWER") return { word: `${name} asks you`, tone: "warn" };
  if (wait?.question && wait.kind === "DECIDING") return { word: "HoldSpeak drafts the answer", tone: "info" };
  const turn = flightTurn ? (flightTurn === "done" ? "DONE" : "IDLE") : wait ? turnEndWord(wait) : null;
  if (turn === "DONE") return { word: `${name} is done`, tone: "ok" };
  if (turn === "IDLE") return { word: `${name} is idle`, tone: "idle" };
  const pr = lane.follow_through?.pr;
  if (pr?.number != null && pr.state === "merged") return { word: `PR #${pr.number} merged`, tone: "ok" };
  return { word: `${name} is working`, tone: "info" };
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
  const age = waitAge(asks?.started ?? held?.created_at).toUpperCase();
  return (
    <section className="lw-plate" aria-label={`${agent} wants to run`} data-testid="lane-approve-well">
      <header className="lw-plate-bar">
        <span className="lw-plate-label">Wants to run</span>
        {age ? <span className="lw-plate-age">{age}</span> : null}
      </header>
      <div className="lw-plate-body">
        {asks ? <AgentWords className="lw-ask-q" text={String(asks.question)} /> : null}
        {held ? (
          <code className="lw-plate-call" data-testid="lane-held-call">
            {held.hold_reason ? <span className="lw-plate-why">{held.hold_reason}</span> : null}
            {gatedHead(held)}
          </code>
        ) : null}
      </div>
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
        word: "NOT DECIDED", at: Date.now(), text: standing ? `ALREADY ${standing.toUpperCase()}` : "HUB UNREACHABLE", tone: "fail",
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
  const caption = ["HELD", reason, part].filter(Boolean).join(" · ");
  return (
    <section className="lw-ask lw-raw-held" aria-label="Held call" data-testid="lane-raw-held">
      <p className="lw-caption">{caption}</p>
      {notRead ? (
        <p className="lw-notread" role="status">{`CALL · NOT READ · ${notRead}`}</p>
      ) : full ? (
        <pre className="lw-raw-command" data-testid="lane-raw-command">{full.command}</pre>
      ) : (
        <p className="lw-notread">CALL · READING</p>
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
function LaneToolbar({ lane, done = false, agent, gone = null, flightTurn = null }: { lane: LaneWire; done?: boolean; agent: string; gone?: AgentFlight | null; flightTurn?: "done" | "idle" | null }) {
  const pr = lane.follow_through?.pr;
  const prUrl = pr?.number != null && pr.url ? pr.url : null;
  const sessionKey = lane.launch.stopped || (lane.control && !isNotRead(lane.control) && lane.control.pane === false) ? null : lane.launch.session_key;
  const rebrief = useLane((s) => s.rebrief);
  const canStop = Boolean(lane.launch.session_key && !lane.launch.stopped && (!lane.control || isNotRead(lane.control) || lane.control.pane !== false));
  const armHere = rebrief || !lane.wait || isNotRead(lane.wait) || lane.wait.kind !== "TO ANSWER" || !lane.wait.question;
  const finished = laneDoing(lane, agent, done, flightTurn).tone === "ok";
  // The one filled primary: Open PR when the work is done and nothing else
  // asks for a press (a held call's Approve, an answer).
  const prPrimary = finished && !approveShowing(lane);
  if (gone) {
    // The session is gone: the one verb that fits is Start again (a new
    // agent on the same item); its PR stays one press away.
    const again = Boolean(againRef(gone));
    if (!again && !prUrl) return null;
    return (
      <Toolbar label="Agent" className="lw-toolbar" data-testid="lane-toolbar">
        {again ? (
          <Button dense variant="primary" data-testid="lane-start-again" onClick={() => startAgain(gone)}>
            <ToolGlyph kind="run" />Start again
          </Button>
        ) : null}
        {prUrl ? (
          <Button dense variant="secondary" data-testid="lane-open-pr" title={prUrl}
            onClick={() => window.open(prUrl, "_blank", "noopener,noreferrer")}>
            <ToolGlyph kind="open" />Open PR
          </Button>
        ) : null}
      </Toolbar>
    );
  }
  if (!sessionKey && !prUrl && !canStop) return null;
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
      {prPrimary ? <>{openPr}{tellIt}</> : <>{tellIt}{openPr}</>}
    </Toolbar>
  );
}

/** The status bar: the agent's state as a dot and a word, when it last
 *  reported a step, how many it reported, and the lane's receipts (the stop,
 *  the last send or refusal). */
function LaneFooter({ lane, agent, done = false, gone = null, flightTurn = null }: { lane: LaneWire; agent: string; done?: boolean; gone?: AgentFlight | null; flightTurn?: "done" | "idle" | null }) {
  const events = useLane((s) => s.events);
  const spoke = lastStep(events);
  const doing = gone ? { word: goneWord(gone), tone: "idle" as const } : laneDoing(lane, agent, done, flightTurn);
  const steps = events.filter(isToolCall).length;
  return (
    <StatusBar
      className="lw-footer"
      data-testid="lane-status"
      items={[
        { key: "state", text: doing.word, lamp: doing.tone === "idle" ? undefined : doing.tone, testId: "lane-head" },
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

