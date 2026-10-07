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
import { MicButton } from "../components/MicButton";
import { useFrontWindowId } from "../components/window/windowRegistry";
import { useGate } from "../gate";
import { spriteUrl } from "../sprites";
import { useSteering } from "../steering";
import { useDesk } from "../store";
import { EgressChip, PaneWell, StringGadget, SurfaceFooter } from "../surface";
import { egressFor } from "../surface/egress";
import { useCompactViewport } from "../useCompactViewport";
import { useOnCoderFrame } from "../useDeskChangedRefresh";
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
  waitAge,
  type LaneEntry,
  type LaneEvent,
  type LaneGated,
  type LaneWait,
  type LaneWire,
} from "./laneWire";
import { launchForSession, useLane, useLaneLaunchId } from "./laneStore";
import { AskWell, FilesChanged, PRCard, StationTrack, TimelineRail, type TimelineEntry } from "./species";
import "./lane.css";

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
  // window): the lane takes it over by id, so Stop does not close the lane.
  useEffect(() => {
    if (launchId && !explicit) useLane.getState().open(launchId, { sessionKey: openKey });
  }, [launchId, explicit, openKey]);

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
          src={spriteUrl("agent", sessionKey ?? launchId)}
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
        <p className="lw-notread">{error ? `LANE · NOT READ · ${error}` : "LANE · READING"}</p>
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
      number={pr.number}
      title={itemTitle}
      checks={checks}
      review={reviewWord(pr.review_decision)}
      branch={branch}
      base={isNotRead(worktree) ? undefined : baseWord(worktree.base) || undefined}
    />
  ) : null;
  const files = isNotRead(worktree) ? (
    <p className="lw-notread" data-testid="lane-files-not-read">{`FILES · NOT READ · ${worktree.not_read}`}</p>
  ) : (
    <FilesChanged files={worktree.files.map((f) => ({ path: f.path }))} />
  );
  const rail = (
    <div className="lw-col">
      {eventsNotRead ? <p className="lw-notread" data-testid="lane-events-not-read">{`TIMELINE · NOT READ · ${eventsNotRead}`}</p> : null}
      {isNotRead(lane.gated) ? <p className="lw-notread">{`HELD · NOT READ · ${lane.gated.not_read}`}</p> : null}
      <TimelineRail label="Lane" entries={railEntries(lane, events, briefOpen, () => setBriefOpen((v) => !v))} />
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
      <StationTrack label="Lane stations" stations={stations} />
      {rebrief ? <RebriefWell /> : <WaitWell lane={lane} agent={agent} />}
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
      <Button dense variant="secondary" disabled={busy} onClick={() => void decide("approved")} data-testid="lane-approve">
        Approve
      </Button>
    </>
  );
}

/* ── the wait ─────────────────────────────────────────────────────── */

function WaitWell({ lane, agent }: { lane: LaneWire; agent: string }) {
  const wait = lane.wait;
  if (isNotRead(wait)) return <p className="lw-notread">{`ASKS · NOT READ · ${wait.not_read}`}</p>;
  if (!wait || !wait.question) return null;
  if (wait.kind === "TO ANSWER") return <AnswerWell wait={wait} agent={agent} />;
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

/** TO ANSWER: the ask well. The answer is a steer to the launch's session;
 * the field is the steer composer's draft (one draft per session). */
function AnswerWell({ wait, agent }: { wait: LaneWait; agent: string }) {
  const openKey = useSteering((s) => s.openKey);
  const steerState = useSteering((s) => s.steerState);
  const steerDetail = useSteering((s) => s.steerDetail);
  const answerSeq = useSteering((s) => s.answerSeq);
  const scope = `steer:${openKey || "unattached"}`;
  const { value, setDraft } = useDurableDraft(scope);
  const draft = wait.draft?.text?.trim() || undefined;
  const draftEgress = useDraftEgress(Boolean(draft));
  const inputRef = useRef<HTMLInputElement | null>(null);
  const answer = async (text: string) => {
    const sent = await useSteering.getState().steer(text, true);
    if (sent) {
      setDraft("");
      void useLane.getState().load();
    }
  };
  return (
    <>
      <AskWell
        agent={agent}
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
        busy={steerState === "sending" || !openKey}
        listenSignal={answerSeq}
        draftScope={scope}
        inputRef={inputRef}
      />
      <SteerFate state={steerState} detail={steerDetail} />
    </>
  );
}

function SteerFate({ state, detail }: { state: string; detail: string }) {
  if (state === "refused") {
    return (
      <span className="lw-fate" data-tone="fail" data-testid="lane-steer-fate">
        <span aria-hidden="true">{GLYPH_CLOSE}</span> {`NOT SENT · ${detail}`}
      </span>
    );
  }
  if (state === "sent") return <span className="lw-fate" data-testid="lane-steer-fate">SENT</span>;
  return null;
}

/** TO APPROVE: the held call with Deny / Approve (the gate proposal). A
 * permission prompt the gate does not hold is answered in the pane: Raw. */
function ApproveWell({ wait, agent, gated }: { wait: LaneWait; agent: string; gated: LaneWire["gated"] }) {
  const held = Array.isArray(gated) ? [...gated].reverse().find((g) => g.state === "held" || g.state === "pending") : undefined;
  const age = waitAge(wait.started);
  return (
    <section className="lw-ask" aria-label={`${agent} asks`} data-testid="lane-approve-well">
      <p className="lw-caption">{[`${agent.toUpperCase()} ASKS`, age.toUpperCase()].filter(Boolean).join(" · ")}</p>
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

/** Re-brief: a steer, prefilled `Re-brief: `. */
function RebriefWell() {
  const steerState = useSteering((s) => s.steerState);
  const steerDetail = useSteering((s) => s.steerDetail);
  const [text, setText] = useState(REBRIEF_PREFIX);
  const ready = text.trim().length > REBRIEF_PREFIX.trim().length;
  const send = async () => {
    if (!ready) return;
    if (await useSteering.getState().steer(text.trim(), true)) {
      useLane.getState().setRebrief(false);
      void useLane.getState().load();
    }
  };
  return (
    <section className="lw-ask" aria-label="Re-brief" data-testid="lane-rebrief-well">
      <p className="lw-caption">Re-brief</p>
      <div className="lw-ask-row">
        <StringGadget
          label="Re-brief"
          value={text}
          onChange={setText}
          mic={false}
          autoFocus
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.nativeEvent.isComposing) {
              event.preventDefault();
              void send();
            }
          }}
        />
        <MicButton label="Speak the re-brief" onText={(t) => setText((prev) => (prev.trim() ? `${prev.trimEnd()} ${t}` : t))} />
        <Button variant="primary" disabled={!ready || steerState === "sending"} onClick={() => void send()}>
          Send
        </Button>
        <Button variant="ghost" onClick={() => useLane.getState().setRebrief(false)}>
          Back
        </Button>
      </div>
      <SteerFate state={steerState} detail={steerDetail} />
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
  const sessionKey = lane.launch.session_key;
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

/** Stop: the kill route, two presses (as the session window's KILL). The
 * kill needs the session-control grant: the confirming press arms it first. */
function StopVerb() {
  const [confirm, setConfirm] = useState(false);
  const factoryState = useSteering((s) => s.factoryState);
  const factoryDetail = useSteering((s) => s.factoryDetail);
  const armError = useSteering((s) => s.armError);
  const stop = async () => {
    const steering = useSteering.getState();
    if (!steering.armed) await steering.arm();
    if (!useSteering.getState().armed) return;
    if (await useSteering.getState().killOpen("session")) setConfirm(false);
    void useLane.getState().load();
  };
  const refusal = armError || (factoryState === "failed" ? factoryDetail : "");
  if (!confirm) {
    return (
      <Button dense variant="danger" data-testid="lane-stop" onClick={() => setConfirm(true)}>
        Stop
      </Button>
    );
  }
  return (
    <>
      {refusal ? <span className="lw-fate" data-tone="fail">{refusal}</span> : null}
      <Button dense variant="ghost" onClick={() => setConfirm(false)}>
        Back
      </Button>
      <Button
        dense
        variant="danger"
        data-testid="lane-stop-confirm"
        disabled={factoryState === "working"}
        onClick={() => void stop()}
      >
        Stop · sure?
      </Button>
    </>
  );
}

/* ── the drafting model's host ────────────────────────────────────── */

type AssignmentEntry = { profile_id?: string; label?: string; boundary?: string };
let draftEntry: Promise<AssignmentEntry | null> | null = null;

function readDraftEntry(): Promise<AssignmentEntry | null> {
  if (!draftEntry) {
    draftEntry = apiFetch<{ task_overrides?: Array<{ id?: string; effective?: { assignment?: { entries?: AssignmentEntry[] } | null } }> }>(
      "/api/inference/assignments",
    )
      .then((body) => {
        const row = (body?.task_overrides ?? []).find((r) => r?.id === DRAFT_CAPABILITY);
        return row?.effective?.assignment?.entries?.[0] ?? null;
      })
      .catch(() => {
        draftEntry = null;
        return null;
      });
  }
  return draftEntry;
}

/** The EgressChip of the model that drafts answers: its endpoint's host
 * (`API.ANTHROPIC.COM`, `192.168.1.43 · LAN`, `THIS DEVICE`); `NOT SET`
 * when no model is assigned to drafts. */
export function useDraftEgress(enabled: boolean): { label: string; scope?: "local" | "mixed" | "cloud" | "remote" } {
  const targets = useDesk((s) => s.inferenceTargets);
  const [entry, setEntry] = useState<AssignmentEntry | null | undefined>(undefined);
  useEffect(() => {
    if (!enabled) return;
    let live = true;
    void readDraftEntry().then((e) => {
      if (live) setEntry(e);
    });
    return () => {
      live = false;
    };
  }, [enabled]);
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
    if (!host && (entry.boundary === "same_device" || target?.boundary === "same_device")) host = "same_device";
    const egress = egressFor(host || entry.label || "");
    return { label: (egress.label || "NOT SET").toUpperCase(), scope: egress.scope };
  }, [entry, targets]);
}

/** Test seam. */
export function __resetDraftEgress(): void {
  draftEntry = null;
}
