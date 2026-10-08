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
import { apiFetch } from "../../lib/api";
import { useDurableDraft } from "../../lib/durableDraft";
import { useAgentFlights } from "../agentFlights";
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
const GLYPH_CLOSE = String.fromCodePoint(0x2715);

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
      kindWord="Agent lane"
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
          aria-label="Raw: the terminal pane"
          data-testid="lane-raw"
          disabled={!sessionKey}
          onClick={() => useLane.getState().setRaw(!raw)}
        >
          Raw
        </Button>
      }
      open
      onClose={() => useLane.getState().close()}
    >
      <LaneBody lane={lane} error={error} raw={raw} agent={agent} compact={compact} itemTitle={flight?.title ?? ""} />
      {lane ? <LaneFooter lane={lane} compact={compact} /> : null}
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

  if (raw) {
    return (
      <div className="desk-pullout-body lw-body" data-testid="lane-body">
        <RawPane />
      </div>
    );
  }
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
      <TimelineRail data-testid="lane-rail" label="Lane" entries={railEntries(lane, events, briefOpen, () => setBriefOpen((v) => !v))} />
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
      <StationTrack data-testid="lane-track" label="Lane stations" stations={stations} />
      <LaneReceipts lane={lane} />
      {unreadParts(lane).map(([part, reason]) => (
        <NotReadLine key={part} part={part} reason={reason} testId={`lane-not-read-${part.toLowerCase()}`} />
      ))}
      {lane.launch.stopped ? null : rebrief ? <RebriefWell /> : <WaitWell lane={lane} agent={agent} />}
      {compact ? (
        <div className="lw-col">
          {prCard}
          {rail}
          {files}
        </div>
      ) : (
        <div className="lw-cols">
          {rail}
          <div className="lw-col">
            {prCard}
            {files}
          </div>
        </div>
      )}
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
    if (kind === "held" && gated && (gated.state === "held" || gated.state === "pending")) {
      return { ...rest, verbs: <DecideVerbs call={gated} /> };
    }
    return rest;
  });
}

function DecideVerbs({ call }: { call: LaneGated }) {
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
        <Button dense variant="secondary" disabled={busy} onClick={() => void decide("approved")} data-testid="lane-approve">
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
  if (wait.kind === "TO APPROVE") return <ApproveWell wait={wait} agent={agent} gated={lane.gated} />;
  if (wait.kind === "DECIDING") {
    return (
      <p className="lw-deciding" data-testid="lane-deciding">
        <span className="lw-word">HoldSpeak decides</span>
        <span className="lw-ev-text">{wait.question}</span>
      </p>
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
      disabled={!key}
      listenSignal={answerSeq}
      draftScope={scope}
      inputRef={inputRef}
      arm={<ArmLine lane={lane} />}
    />
  );
}

/** Secure and Normal: the lane's ARM, where the action is, with the mode.
 * Absent when the session is armed or the policy lets the owner type (YOLO). */
function ArmLine({ lane, compact = false }: { lane: LaneWire; compact?: boolean }) {
  const control = lane.control;
  if (!control || isNotRead(control) || control.direct || control.armed || !laneSessionKey(lane)) return null;
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
  const last = [...answers].reverse().find((a) => a.outcome === "delivered" && a.text_head);
  const lastAt = last ? wireDate(last.ts)?.getTime() : undefined;
  const shown = receipt ?? (last ? { word: "SENT", at: lastAt, text: String(last.text_head), tone: "ok" as const } : null);
  const queued = !stopped && lane.launch.queued_rebrief?.text ? lane.launch.queued_rebrief : null;
  return (
    <>
      {stopped ? <ReceiptTokens testId="lane-stopped" tokens={["STOPPED", wireClock(stopped.at), "BY YOU"]} /> : null}
      {queued ? (
        <ReceiptTokens testId="lane-queued" tone="warn" tokens={["QUEUED", "AFTER THIS TURN", String(queued.text)]} />
      ) : null}
      {shown && !(stopped && shown.word === "STOPPED") && !(queued && shown.word === "QUEUED") ? (
        <ReceiptTokens testId="lane-receipt" tone={shown.tone} tokens={[shown.word, shown.at ? wireClock(shown.at) : "", shown.text]} />
      ) : null}
    </>
  );
}

/** One receipt: tokens joined by ` · ` (the word, the time, what was sent). */
function ReceiptTokens({ tokens, tone, testId }: { tokens: string[]; tone?: string; testId: string }) {
  const shown = tokens.filter(Boolean);
  return (
    <p className="lw-receipt" data-tone={tone} data-testid={testId}>
      {shown.join(" · ")}
    </p>
  );
}

/** TO APPROVE: the held call with Deny / Approve (the gate proposal). A
 * permission prompt the gate does not hold is answered in the pane: Raw. */
function ApproveWell({ wait, agent, gated }: { wait: LaneWait; agent: string; gated: LaneWire["gated"] }) {
  const held = Array.isArray(gated) ? [...gated].reverse().find((g) => g.state === "held" || g.state === "pending") : undefined;
  const caption = [`${agent.toUpperCase()} ASKS`, waitAge(wait.started).toUpperCase()].filter(Boolean).join(" · ");
  return (
    <section className="lw-ask" aria-label={`${agent} asks`} data-testid="lane-approve-well">
      <p className="lw-caption">{caption}</p>
      <p className="lw-ask-q">{String(wait.question)}</p>
      {held ? (
        <div className="lw-ask-row">
          <code className="lw-ev-code">{gatedHead(held)}</code>
          <span className="lw-verbs">
            <DecideVerbs call={held} />
          </span>
        </div>
      ) : (
        <div className="lw-verbs">
          <Button dense variant="secondary" onClick={() => useLane.getState().setRaw(true)}>
            Raw
          </Button>
        </div>
      )}
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

function RawPane() {
  const paneStatus = useSteering((s) => s.paneStatus);
  const paneLines = useSteering((s) => s.paneLines);
  const paneRaw = useSteering((s) => s.paneRaw);
  const paneGeom = useSteering((s) => s.paneGeom);
  const paneChangedAt = useSteering((s) => s.paneChangedAt);
  const armed = useSteering((s) => s.armed);
  const postureAuthorized = useSteering((s) => s.postureAuthorized);
  return (
    <div className="lw-raw" data-testid="lane-raw-pane">
      <PaneWell
        live={paneStatus === "live"}
        lines={paneLines}
        raw={paneRaw}
        pane={paneGeom}
        changedAt={paneChangedAt}
        absence={
          <>
            <span aria-hidden="true">{GLYPH_CLOSE}</span> {PANE_STATE_LABEL[paneStatus] || paneStatus}
          </>
        }
      />
      <ArmStrip />
      {armed || postureAuthorized ? <KeyPalette /> : null}
    </div>
  );
}

/* ── the footer ───────────────────────────────────────────────────── */

function LaneFooter({ lane, compact }: { lane: LaneWire; compact: boolean }) {
  const pr = lane.follow_through?.pr;
  const prUrl = pr?.number != null && pr.url ? pr.url : null;
  const sessionKey = lane.launch.stopped ? null : lane.launch.session_key;
  const branch = lane.launch.branch ?? (isNotRead(lane.worktree) ? null : lane.worktree.branch);
  const rebrief = useLane((s) => s.rebrief);
  return (
    <SurfaceFooter
      className="lw-footer"
      egress={prUrl ? <EgressChip label="GITHUB.COM" scope="cloud" /> : undefined}
      receipt={!compact && branch ? <span className="lw-footer-branch" data-testid="lane-branch">{branch}</span> : undefined}
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
          {sessionKey ? <ArmLine lane={lane} compact /> : null}
          {sessionKey ? <StopVerb /> : null}
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
        Stop · sure? (ends the agent's session)
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
function readDraftEntry(): Promise<AssignmentEntry | null> {
  return apiFetch<AssignmentRoster>("/api/inference/assignments").then((body) => {
    const row = (body?.task_overrides ?? []).find((r) => r?.id === DRAFT_CAPABILITY);
    return row?.effective?.assignment?.entries?.[0] ?? null;
  });
}

/** The EgressChip of the model that drafts answers: its endpoint's host
 * (`API.ANTHROPIC.COM`, `192.168.1.43 · LAN`, `THIS DEVICE`), else the
 * model's name; `NOT SET` when no model is assigned to drafts and no Default
 * for AI work exists (drafts inherit the default, PHILO-15 05). Read on every
 * open and again after any desk write (`desk_changed`: the Settings and the
 * Concierge assign through mutating `/api` requests, which announce it). */
export function useDraftEgress(enabled: boolean): { label: string; scope?: "local" | "mixed" | "cloud" | "remote" } {
  const targets = useDesk((s) => s.inferenceTargets);
  const [entry, setEntry] = useState<AssignmentEntry | null | undefined>(undefined);
  const seq = useRef(0);
  const read = useCallback(() => {
    const mine = ++seq.current;
    void readDraftEntry()
      .then((e) => {
        if (seq.current === mine) setEntry(e);
      })
      .catch(() => {
        // The last read stays on the glass when a re-read fails.
      });
  }, []);
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
    if (!entry) return { label: "NOT SET" };
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
    return { label: (egress.label || "NOT SET").toUpperCase(), scope: lan ? "local" : egress.scope };
  }, [entry, targets]);
}

/** Test seam (the chip keeps no cache since PHILO-15 05 r1). */
export function __resetDraftEgress(): void {}
