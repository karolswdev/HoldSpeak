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
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { ApiError, apiFetch } from "../../lib/api";
import { useDurableDraft } from "../../lib/durableDraft";
import { useAgentFlights } from "../agentFlights";
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
  EgressChip,
  FilesChanged,
  FoldGadget,
  PaneWell,
  PRCard,
  StationTrack,
  StringGadget,
  SurfaceFooter,
  TimelineRail,
  TransportKey,
  type TimelineEntry,
} from "../surface";
import { wireClock, wireDate } from "../surface/format";
import { controlModeLabel } from "../../lib/productLanguage";
import { egressFor } from "../surface/egress";
import { useCompactViewport } from "../useCompactViewport";
import { useOnCoderFrame, useOnDeskChanged } from "../useDeskChangedRefresh";
import { answerCoderOpenFirst } from "./coderOpen";
import {
  agentName,
  baseWord,
  checksSummary,
  gatedHead,
  isNotRead,
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
} from "./laneWire";
import { laneSessionKey, launchForSession, useLane, useLaneLaunchId } from "./laneStore";
import "./lane.css";


/** The lane title icon: the launch's OWN agent sprite at 32 (Codex keeps
 * its face; PHILO-14 A0c r2). */
export function laneTitleSprite(agent: string | null | undefined, key: string): string {
  return spriteUrl("agent", key, "rest", agent, 32);
}

/** The lane refreshes this often while its window is in front. */
export const LANE_FRONT_POLL_MS = 5_000;
export const LANE_WINDOW_ID = "lane";
/** The capability whose model drafts an answer (`agent_responder.CAPABILITY`). */
const DRAFT_CAPABILITY = "background.cadence_draft";
const REBRIEF_PREFIX = "Re-brief: ";

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
  const flight = useAgentFlights((s) => s.flights.find((f) => f.launchId === launchId) ?? null);
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

  const agent = agentName(lane?.launch.agent ?? flight?.agent);
  const title = laneTitle(lane?.launch.agent ?? flight?.agent, flight?.title);
  const sessionKey = lane?.launch.session_key ?? flight?.sessionKey ?? null;

  return (
    <DeskWindowFrame
      id={LANE_WINDOW_ID}
      title={title}
      label={title}
      kindWord="Coder lane"
      glyph="▮"
      className="desk-pullout is-lane"
      minW={360}
      minH={320}
      defaultW={940}
      defaultH={720}
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
      actions={
        <Button
          dense
          variant="ghost"
          aria-pressed={raw}
          aria-label={raw ? "Back to session" : "Open terminal"}
          data-testid="lane-raw"
          disabled={!sessionKey}
          onClick={() => useLane.getState().setRaw(!raw)}
        >
          {raw ? "Back to session" : "Open terminal"}
        </Button>
      }
      open
      onClose={() => useLane.getState().close()}
    >
      <LaneBody lane={lane} error={error} raw={raw} agent={agent} compact={compact} itemTitle={flight?.title ?? ""} />
      {lane ? <LaneFooter lane={lane} /> : null}
    </DeskWindowFrame>
  );
}

function LaneBody({
  lane, error, raw, agent, compact, itemTitle,
}: {
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
  const checks = checksSummary(pr?.checks);
  const branch = lane.launch.branch ?? (isNotRead(worktree) ? null : worktree.branch) ?? undefined;
  const prCard = pr && pr.number != null ? (
    <PRCard
      data-testid="lane-pr"
      number={pr.number}
      title={pr.title || itemTitle}
      item={pr.title ? itemTitle : undefined}
      checks={checks}
      review={reviewWord(pr.review_decision)}
      branch={branch}
      base={isNotRead(worktree) ? undefined : baseWord(worktree.base) || undefined}
    />
  ) : null;
  const files = isNotRead(worktree) ? (
    <NotReadLine part="FILES" reason={worktree.not_read} testId="lane-files-not-read" />
  ) : (
    <FilesChanged data-testid="lane-files" files={worktree.files.map((f) => ({ path: f.path }))} />
  );
  const rail = (
    <div className="lw-col">
      {eventsNotRead ? <NotReadLine part="TIMELINE" reason={eventsNotRead} testId="lane-events-not-read" /> : null}
      {isNotRead(lane.gated) ? <NotReadLine part="HELD" reason={lane.gated.not_read} /> : null}
      <TimelineRail data-testid="lane-rail" label="Activity" entries={railEntries(lane, events, briefOpen, () => setBriefOpen((v) => !v))} />
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
      <LaneHead lane={lane} agent={agent} itemTitle={itemTitle} />
      {unreadParts(lane).map(([part, reason]) => (
        <NotReadLine key={part} part={part} reason={reason} testId={`lane-not-read-${part.toLowerCase()}`} />
      ))}
      {lane.launch.stopped ? null : rebrief ? <RebriefWell /> : (
        <>
          {!raw ? <HeldPlate lane={lane} agent={agent} /> : null}
          <WaitWell lane={lane} agent={agent} />
        </>
      )}
      {raw ? <RawPane /> : null}
      {compact ? (
        <div className="lw-col">
          {prCard}
          {rail}
        </div>
      ) : (
        <div className="lw-cols">
          {rail}
          <div className="lw-col">
            {prCard}
          </div>
        </div>
      )}
      <FoldGadget title="Details" className="lw-details">
        <StationTrack data-testid="lane-track" label="Recorded stages" stations={stations.filter((s) => s.state !== "ahead")} />
        {branch ? <span className="lw-footer-branch" data-testid="lane-branch">{branch}</span> : null}
        {files}
        {lane.launch.session_key && !lane.launch.stopped && (!lane.control || isNotRead(lane.control) || lane.control.pane !== false) ? <div className="lw-verbs">
          {/* Stop retains its own session-control grant and confirmation. */}
          {rebrief || !lane.wait || isNotRead(lane.wait) || lane.wait.kind !== "TO ANSWER" || !lane.wait.question ? <ArmLine lane={lane} compact /> : null}
          <StopVerb />
        </div> : null}
      </FoldGadget>
    </div>
  );
}

/** The rail entries with their verbs: Brief on BRIEF, Deny / Approve on a
 * held call. */
function railEntries(lane: LaneWire, events: readonly LaneEvent[], briefOpen: boolean, toggleBrief: () => void): TimelineEntry[] {
  return laneEntries(lane, events).map((entry: LaneEntry) => {
    const { at: _at, kind, gated, heads: _heads, ...rest } = entry;
    if (kind === "brief" && lane.launch.brief_text) {
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
    // plate at the top of the lane (heldNow), not on the rail.
    return rest;
  });
}

function DecideVerbs({ call }: { call: LaneGated }) {
  // The held plate's verbs: Approve is the lane's one first move.
  const [busy, setBusy] = useState(false);
  const decide = async (decision: "approved" | "denied") => {
    setBusy(true);
    try {
      await useGate.getState().decide(call.id, decision);
    } finally {
      setBusy(false);
      void useLane.getState().load();
    }
  };
  return (
    <>
      <Button dense variant="ghost" disabled={busy} onClick={() => void decide("denied")} data-testid="lane-deny">
        Deny
      </Button>
      {/* PHILO-14 A5: a call the hub cannot show whole is never approved
          here; Raw shows the live pane with the whole command. */}
      {call.args_cut ? (
        <Button dense variant="secondary" onClick={() => useLane.getState().setRaw(true)} data-testid="lane-raw-cut">
          Raw
        </Button>
      ) : (
        <Button dense variant="primary" disabled={busy} onClick={() => void decide("approved")} data-testid="lane-approve">
          Approve
        </Button>
      )}
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

function WaitWell({ lane, agent }: { lane: LaneWire; agent: string }) {
  const wait = lane.wait;
  if (isNotRead(wait)) return <NotReadLine part="ASKS" reason={wait.not_read} />;
  if (!wait || !wait.question) return null;
  if (wait.kind === "TO ANSWER") return <AnswerWell lane={lane} wait={wait} agent={agent} />;
  // TO APPROVE: the held plate above says it (HeldPlate).
  if (wait.kind === "TO APPROVE") return null;
  const turn = turnEndWord(wait);
  if (turn) {
    // PHILO-15 15: the agent's last words, as a fact; not a wait for you.
    return (
      <div className="lw-deciding" data-testid="lane-turn-end" data-turn={turn.toLowerCase()}>
        <span className="lw-word">{turn}</span>
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
  const draftEgress = useDraftEgress(Boolean(draft));
  const inputRef = useRef<HTMLInputElement | null>(null);
  const answer = async (text: string) => {
    if (await useLane.getState().send(text, { waitId: wait.wait_id ?? null })) setDraft("");
  };
  return (
    <AskWell
      data-testid="lane-ask"
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
      draftEgress={draft ? draftEgress : undefined}
      busy={sending}
      disabled={!key || Boolean(lane.control && !isNotRead(lane.control) && lane.control.pane === false)}
      listenSignal={answerSeq}
      draftScope={scope}
      inputRef={inputRef}
      arm={lane.control && !isNotRead(lane.control) && lane.control.pane === false ? <span className="surface-token">Terminal unavailable</span> : <ArmLine lane={lane} />}
    />
  );
}

/** Secure and Normal: the lane's ARM, where the action is, with the mode.
 * Absent when the session is armed or the policy lets the owner type (YOLO). */
function ArmLine({ lane, compact = false }: { lane: LaneWire; compact?: boolean }) {
  const control = lane.control;
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

/** PHILO-17 THE REFIT: what the coder does now, as the lane's one headline. */
export function laneDoing(lane: LaneWire, agent: string): { word: string; tone: "ok" | "warn" | "info" | "idle" } {
  const name = agent || "The coder";
  if (lane.launch.stopped) return { word: `${name} stopped`, tone: "idle" };
  const wait = isNotRead(lane.wait) ? null : lane.wait;
  if (heldNow(lane) || wait?.kind === "TO APPROVE") return { word: `${name} wants approval`, tone: "warn" };
  if (wait?.question && wait.kind === "TO ANSWER") return { word: `${name} asks you`, tone: "warn" };
  if (wait?.question && wait.kind === "DECIDING") return { word: "HoldSpeak drafts the answer", tone: "info" };
  const turn = wait ? turnEndWord(wait) : null;
  if (turn === "DONE") return { word: `${name} is done`, tone: "ok" };
  if (turn === "IDLE") return { word: `${name} is idle`, tone: "idle" };
  const pr = lane.follow_through?.pr;
  if (pr?.number != null && pr.state === "merged") return { word: `PR #${pr.number} merged`, tone: "ok" };
  return { word: `${name} is working`, tone: "info" };
}

function LaneHead({ lane, agent, itemTitle }: { lane: LaneWire; agent: string; itemTitle: string }) {
  const doing = laneDoing(lane, agent);
  return (
    <div className="lw-head" data-testid="lane-head">
      <span className="lw-head-sprite" aria-hidden="true">
        <img src={laneTitleSprite(lane.launch.agent, lane.launch.session_key ?? lane.launch.launch_id ?? "lane")} alt="" draggable={false} />
      </span>
      <div className="lw-head-text">
        <h2 className="lw-head-title" data-tone={doing.tone}>{doing.word}</h2>
        <span className="lw-head-meta">
          {itemTitle ? <span>{itemTitle}</span> : null}
        </span>
      </div>
    </div>
  );
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
    <section className="lw-plate" aria-label={`${agent} wants approval`} data-testid="lane-approve-well">
      <header className="lw-plate-bar">
        <span className="lw-plate-label">WANTS APPROVAL</span>
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
            Raw
          </Button>
        )}
      </div>
    </section>
  );
}

/** Re-brief: the owner's new instruction to the lane's own agent,
 * prefilled `Re-brief: `. The hub types it now when the agent is idle or
 * asks; mid-turn it is QUEUED · AFTER THIS TURN (PHILO-15 B46). */
function RebriefWell() {
  const sending = useLane((s) => s.sending);
  const [text, setText] = useState(REBRIEF_PREFIX);
  const ready = text.trim().length > REBRIEF_PREFIX.trim().length;
  const send = async () => {
    if (!ready) return;
    if (await useLane.getState().sendRebrief(text.trim())) useLane.getState().setRebrief(false);
  };
  return (
    <section className="lw-ask" aria-label="Re-brief" data-testid="lane-rebrief-well">
      <p className="lw-caption">Re-brief</p>
      <div className="lw-ask-row">
        <StringGadget
          label="Re-brief"
          value={text}
          onChange={(next) => setText(next.startsWith(REBRIEF_PREFIX.trim()) ? next : `${REBRIEF_PREFIX}${next}`)}
          micLabel="Speak the re-brief"
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
  return (
    <div className="lw-raw" data-testid="lane-raw-pane">
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
        <Button dense variant="ghost" onClick={() => useLane.getState().setRaw(false)}>Back to session</Button>
      </div> : null}
      {paneStatus === "live" && paneId ? <FoldGadget title="Keys" className="lw-keys">
        <ArmStrip />
        {armed || postureAuthorized ? <KeyPalette /> : null}
      </FoldGadget> : null}
    </div>
  );
}

/* ── the footer ───────────────────────────────────────────────────── */

function LaneFooter({ lane }: { lane: LaneWire }) {
  const pr = lane.follow_through?.pr;
  const prUrl = pr?.number != null && pr.url ? pr.url : null;
  const sessionKey = lane.launch.stopped || (lane.control && !isNotRead(lane.control) && lane.control.pane === false) ? null : lane.launch.session_key;
  const rebrief = useLane((s) => s.rebrief);
  return (
    <SurfaceFooter
      className="lw-footer"
      egress={prUrl ? <EgressChip label="GITHUB.COM" scope="cloud" /> : undefined}
      receipt={<LaneReceipts lane={lane} />}
      verbs={
        <>
          {sessionKey ? (
            <Button
              dense
              variant="ghost"
              aria-pressed={rebrief}
              data-testid="lane-rebrief"
              onClick={() => useLane.getState().setRebrief(!rebrief)}
            >
              Re-brief
            </Button>
          ) : null}
          {prUrl ? (
            <Button
              dense
              variant="secondary"
              data-testid="lane-open-pr"
              onClick={() => window.open(prUrl, "_blank", "noopener,noreferrer")}
            >
              Open PR
            </Button>
          ) : null}
        </>
      }
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
        Stop · sure? (ends the coder's session)
      </Button>
    </>
  );
}

/* ── the drafting model's host ────────────────────────────────────── */

type AssignmentEntry = { profile_id?: string; label?: string; boundary?: string };
type AssignmentRoster = { task_overrides?: Array<{ id?: string; effective?: { assignment?: { entries?: AssignmentEntry[] } | null } }> };

/** The drafting model's entry, read now. `effective` is the whole chain
 * (exact, group, global): with only the Default for AI work, drafts inherit
 * it (PHILO-15 05). No cache: a changed default shows at once (Astra r1). */
function readDraftEntry(capability: string): Promise<AssignmentEntry | null> {
  return apiFetch<AssignmentRoster>("/api/inference/assignments").then((body) => {
    const row = (body?.task_overrides ?? []).find((r) => r?.id === capability);
    return row?.effective?.assignment?.entries?.[0] ?? null;
  });
}

/** The EgressChip of the model that drafts answers: its endpoint's host
 * (`API.ANTHROPIC.COM`, `192.168.1.43 · LAN`, `THIS DEVICE`), else the
 * model's name; `NOT SET` when no model is assigned to drafts and no Default
 * for AI work exists (drafts inherit the default, PHILO-15 05). Read on every
 * open and again after any desk write (`desk_changed`: the Settings and the
 * Concierge assign through mutating `/api` requests, which announce it). */
export function useDraftEgress(
  enabled: boolean,
  /** PHILO-15 B53: the Room's Draft update names its own model's host. */
  capability: string = DRAFT_CAPABILITY,
): {
  label: string;
  scope?: "local" | "mixed" | "cloud" | "remote";
  /** PHILO-17 U31: true an engine is set, false none is, undefined not read yet. */
  assigned?: boolean;
  /** The first read failed: nothing is known (Try again with `retry`). */
  failed?: boolean;
  retry?: () => void;
} {
  const targets = useDesk((s) => s.inferenceTargets);
  const [entry, setEntry] = useState<AssignmentEntry | null | undefined>(undefined);
  const [readFailed, setReadFailed] = useState(false);
  const seq = useRef(0);
  const read = useCallback(() => {
    const mine = ++seq.current;
    setReadFailed(false);
    void readDraftEntry(capability)
      .then((e) => {
        if (seq.current === mine) setEntry(e);
      })
      .catch(() => {
        // The last read stays on the glass when a re-read fails; with no
        // read yet, the failure is said (never taken as "no engine").
        if (seq.current === mine) setReadFailed(true);
      });
  }, [capability]);
  useEffect(() => {
    if (!enabled) return;
    read();
    return () => {
      seq.current += 1; // an answer after close is dropped
    };
  }, [enabled, read]);
  useOnDeskChanged(() => {
    if (enabled) read();
  });
  return useMemo(() => {
    // PHILO-17 U31: `assigned` says if an engine is set (undefined: not read yet).
    if (entry === undefined) return { label: "NOT SET", assigned: undefined, failed: readFailed, retry: read };
    if (!entry) return { label: "NOT SET", assigned: false, retry: read };
    const target = targets.find((t) => t.profile_id === entry.profile_id || t.id === entry.profile_id);
    let host = "";
    if (target?.endpoint) {
      try {
        host = new URL(target.endpoint).hostname;
      } catch {
        host = "";
      }
    }
    // The assignment projection names a this-device entry `local`; the
    // deployment revision names it `same_device` (PHILO-15 05: a local
    // default read its model label as a cloud host).
    if (!host && [entry.boundary, target?.boundary].some((b) => b === "same_device" || b === "local")) host = "same_device";
    const egress = egressFor(host || entry.label || "");
    // No host to read: the chip names the model (its label), and its scope is
    // the entry's own boundary, so a LAN default never reads as cloud.
    const lan = !host && ["private_network", "mesh"].includes(String(entry.boundary ?? target?.boundary ?? ""));
    return { label: (egress.label || "NOT SET").toUpperCase(), scope: lan ? "local" : egress.scope, assigned: true, retry: read };
  }, [entry, targets, readFailed, read]);
}

/** Test seam (the chip keeps no cache since PHILO-15 05 r1). */
export function __resetDraftEgress(): void {}
