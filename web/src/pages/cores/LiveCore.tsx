// HS-95-06 — the live meeting's core: record, watch the transcript
// arrive, keep the result — hosted anywhere (see ActivityCore's rules).
// HS-98-04 — re-crafted native: the transcript is the primary pane, the
// rail collapses with the window, the meeting-details modal became an
// inline block, and device facts are honest. Wire calls unchanged.
// HS-102-02 — the refit: the working posture (AGENT_BRIEF §3). The
// face leads with the ONE verb; duration/segments fold into a single
// quiet facts line; the transcript rides SurfaceStream (the same
// dated-stream shape the Journal wears); Bookmark is a verb ON the
// stream, not a form section; intent routing, the preview textarea,
// deferred plugin jobs, and device diagnostics fold behind the gear
// (a configuring posture is exactly where canon rule 1 allows a
// label+input stack). Wire calls unchanged.
// HS-111-03 — the refinement pass (audit §3.6, scope-limited): the
// stream, the one-verb posture, and the bookmark-in-controls pattern
// stay UNTOUCHED. The details form and the configure door move to the
// gadget grammar, every text input gains its mic, the loose egress
// prose becomes the ONE EgressChip, and the readiness foot is the
// footer receipt bar. Wire calls unchanged.
// HS-132-03 — the desk hears elected intelligence live: `intel_complete`,
// the `bookmark` confirmation, `capture_recovery`, `intent_controls_updated`,
// `device_health`, and `plugin_jobs_processed`. C1 publishes complete semantic
// results, not provider token streams.
// W2-LIVE (2026-10-27, canvas betterment/canvases/live-direction-2026-10-27.html,
// direction A "the transcript is the page"): while it records, the body is the
// transcript as a document (a time mark from the wire's `start_time`, the
// speaker's name when the speaker changes, a bookmark as an ember mark); the
// status bar carries the live state once (Recording · 12:04 · Summaries on
// <engine>); Bookmark is a toolbar verb. The gear wing moved to Settings ▸
// Meetings (LiveMeetingTools); the toolbar verb Settings opens it.
import { useEffect, useRef, useState } from "react";
import { openPrimitive } from "../../desk/shell";
import { useDesk } from "../../desk/store";
import { openSurfaceOr } from "../../desk/shell";
import type {
  CoreProps,
  MeetingStateResponse,
  RuntimeStatusResponse,
} from "./core-types";
import { Button } from "../../components/signal/Signal";
import { apiFetch } from "../../lib/api";
import { useRuntimeBus } from "../../runtime/RuntimeBus";
import { asRows, useResource } from "../pageSupport";
import {
  SurfaceFacts,
  SurfaceSection,
  SurfaceState,
} from "../../desk/surface/Surface";
import { useAction } from "./core-hooks";
import {
  GadgetGroup,
  GadgetRow,
  StringGadget,
} from "../../desk/surface/gadgets";
import { presentValue } from "../../desk/surface/format";
import { DotWord, StatusBar, Steps, ToolGlyph, Toolbar, meetingSteps, type StatusBarItem } from "../../desk/surface/kit";
import { useWindowInterior } from "../../desk/surface/interior";
import { countToken } from "../../desk/surface/count";
import { LiveTranscript } from "./LiveTranscript";
import { LiveReady } from "./LiveReady";
import { LiveListening, type MicCheck, type TranscriptPass } from "./LiveLevel";
import { useCompactViewport } from "../../desk/useCompactViewport";
import "./liveTranscript.css";
import { burstTimer } from "../../desk/burstTimer";
import { onReturnToTask } from "../../desk/returnToTask";
import { useSpeechSetup } from "../../desk/firstrun/SpeechSetup";
import { NO_TRANSCRIPT_SPEECH, speechWasMissing } from "../../desk/firstrun/speechTruth";
import {
  meetingStopReceiptLabel,
  parseMeetingStopOutcome,
  type MeetingStopOutcome,
} from "../../meetings/meetingStopOutcome";
import {
  clearWriteFailure,
  currentWriteFailure,
  reportWriteFailure,
} from "../../desk/hooks/useWriteReceipt";

type Segment = Record<string, unknown>;

/** PHILO-17 (owner 2026-10-10, "A meeting opens in one window"): the live
 *  room is the body of the meeting's own window while it records
 *  (`meetingId`); on Stop that window shows the saved meeting
 *  (`onStopped`). Without `meetingId` it is the Live meeting window, the
 *  place a meeting starts; the started meeting then opens in its own window. */
export type LiveCoreProps = CoreProps & { meetingId?: string; onStopped?: () => void };

export function LiveCore({ hero, meetingId, onStopped }: LiveCoreProps) {
  const initial = useResource<MeetingStateResponse>("/api/state", {});
  const runtimeStatus = useResource<RuntimeStatusResponse>("/api/runtime/status", {});
  /* W2-LIVE: the summary engine by its name, the fact Settings ▸ Meetings
     shows on its "Summaries run on" row (`meetings.engine`, `engineSet`,
     `summariesOff` from /api/settings/hub). */
  const settingsHub = useResource<Record<string, unknown>>("/api/settings/hub", {});
  /* W2-LIVE-2: the ready sheet's devices (`meeting.mic_device`,
     `meeting.system_audio_device`), the facts Settings ▸ Meetings shows. */
  const settings = useResource<Record<string, unknown>>("/api/settings", {});
  const compact = useCompactViewport();
  /* The name he gives before Start; the hub's start takes no title, so it
     is sent with PATCH /api/meeting once the meeting is live. */
  const [readyName, setReadyName] = useState("");
  const { state: connection, subscribe } = useRuntimeBus();
  /* HS-202-02 (Astra's counsel finding 3) — the Intelligence badge maps
     the hub's real posture, but only what it read ONCE on mount. Set an
     engine in the Concierge and this face kept the old placement until it
     remounted. It rides the same signals the Meetings face does. */
  const reloadRuntimeStatus = runtimeStatus.reload;
  const reloadSettingsHub = settingsHub.reload;
  useEffect(() => {
    const burst = burstTimer(() => {
      void reloadRuntimeStatus();
      void reloadSettingsHub();
    }, 300);
    const bump = burst.bump;
    const offDeskChanged = subscribe("desk_changed", bump);
    const offReturn = onReturnToTask(() => void reloadRuntimeStatus());
    const onFocus = () => void reloadRuntimeStatus();
    window.addEventListener("focus", onFocus);
    return () => {
      burst.cancel();
      offDeskChanged();
      offReturn();
      window.removeEventListener("focus", onFocus);
    };
  }, [subscribe, reloadRuntimeStatus, reloadSettingsHub]);
  const [state, setState] = useState<Record<string, unknown>>({});
  const [segments, setSegments] = useState<Segment[]>([]);
  const action = useAction();
  const [bookmark, setBookmark] = useState("");
  const [bookmarking, setBookmarking] = useState(false);
  const [metaOpen, setMetaOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [tags, setTags] = useState("");
  const [retainedMeetingId, setRetainedMeetingId] = useState("");
  const [stopOutcome, setStopOutcome] = useState<MeetingStopOutcome | null>(null);
  // Routed analysis publishes one elected semantic result. The provider token
  // stream retired with the C1 controller boundary; no private partial output
  // reaches this surface or a journal.
  const [intelResult, setIntelResult] = useState<Record<string, unknown> | null>(
    null,
  );
  const [bookmarkReceipt, setBookmarkReceipt] = useState<{
    text: string;
    seq: number;
  } | null>(null);
  const [captureAlert, setCaptureAlert] = useState("");
  const bookmarkSeq = useRef(0);
  /* Live slice 3: the engine's pass (`transcript_pass`: writing / listening,
     how far the saved transcript reaches) and, before Start, the hub's
     microphone check. */
  const [pass, setPass] = useState<TranscriptPass | null>(null);
  const [mic, setMic] = useState<MicCheck | null>(null);
  const [checkingMic, setCheckingMic] = useState(false);
  /* W2-LIVE: no gear wing. Its parts (routing, try a phrase, background
     work, attached devices) are in Settings ▸ Meetings ▸ Live meeting; the
     toolbar verb Settings opens them. With no wing the head shows the
     window's own name, on the phone too. */

  useEffect(() => {
    setState(initial.data);
    setSegments(asRows(initial.data, ["segments"]));
    setTitle(String(initial.data.title ?? ""));
    setTags(
      Array.isArray(initial.data.tags) ? initial.data.tags.join(", ") : "",
    );
  }, [initial.data]);
  useEffect(
    () =>
      subscribe("*", (frame) => {
        if (
          frame.type === "segment" &&
          frame.data &&
          typeof frame.data === "object"
        )
          setSegments((current) => [...current, frame.data as Segment]);
        else if (
          [
            "meeting_started",
            "meeting_updated",
            "duration",
            "stopped",
            "runtime_activity",
            "intel_status",
          ].includes(frame.type)
        )
          setState((current) => ({
            ...current,
            [frame.type]: frame.data,
            ...(frame.type === "meeting_started" ||
            frame.type === "meeting_updated"
              ? (frame.data as Record<string, unknown>)
              : {}),
          }));
      }),
    [subscribe],
  );

  useEffect(
    () =>
      subscribe("intel_complete", (frame) => {
        setIntelResult(
          frame.data && typeof frame.data === "object"
            ? (frame.data as Record<string, unknown>)
            : null,
        );
      }),
    [subscribe],
  );

  useEffect(
    () =>
      subscribe("transcript_pass", (frame) => {
        if (frame.data && typeof frame.data === "object") setPass(frame.data as TranscriptPass);
      }),
    [subscribe],
  );

  // ── the bookmark's confirmation ────────────────────────────────────
  useEffect(
    () =>
      subscribe("bookmark", (frame) => {
        const data = frame.data as Record<string, unknown> | undefined;
        const label = String(data?.label ?? data?.name ?? "").trim();
        // HS-132-14 walk finding: nothing server-side emits formatted_time,
        // so a raw float ("6.22566…") reached the receipt. Seconds render
        // as m:ss; a preformatted string passes through untouched.
        const raw = data?.formatted_time ?? data?.timestamp ?? data?.time ?? "";
        const secs = typeof raw === "number" ? raw : Number(raw);
        const at = Number.isFinite(secs)
          ? `${Math.floor(secs / 60)}:${String(Math.floor(secs % 60)).padStart(2, "0")}`
          : String(raw).trim();
        bookmarkSeq.current += 1;
        setBookmarkReceipt({
          seq: bookmarkSeq.current,
          text: [label || "Bookmark dropped", at].filter(Boolean).join(" · "),
        });
      }),
    [subscribe],
  );
  useEffect(() => {
    if (!bookmarkReceipt) return;
    const timer = window.setTimeout(() => setBookmarkReceipt(null), 6000);
    return () => window.clearTimeout(timer);
  }, [bookmarkReceipt]);

  // ── capture told the truth about itself ────────────────────────────
  useEffect(
    () =>
      subscribe("capture_recovery", (frame) => {
        const data = frame.data as Record<string, unknown> | undefined;
        setCaptureAlert(
          String(data?.error ?? "Capture is degraded and may lose audio."),
        );
      }),
    [subscribe],
  );

  // (W2-LIVE: the intent, queue and device frames moved with the gear wing
  // to LiveMeetingTools in Settings ▸ Meetings.)

  // The meeting's own window shows this room only while it records.
  // PHILO-17 (Astra r1): the hub's idle state says `meeting_active: false`
  // (runtime/activity.py); either word ends the room.
  const active = Boolean(
    (meetingId && state.active !== false && state.meeting_active !== false) ||
      (state.active ?? state.meeting_active ?? state.status === "recording"),
  );
  // PHILO-17 speech: the live `duration` frame (a "MM:SS" string, one a
  // second) leads. `formatted_duration` arrives once with meeting_started /
  // meeting_updated and stood in front of the live frame, so REC froze at
  // 00:01 while the dock counter ran.
  const duration = String(
    (typeof state.duration === "string" && state.duration) ||
      (state.duration as Record<string, unknown> | undefined)?.formatted ||
      state.formatted_duration ||
      "00:00",
  );
  // PHILO-17 speech: no speech model means a meeting with audio only. The
  // face says so before he records, and while he records.
  const speech = useSpeechSetup();
  const audioOnly = active ? speechWasMissing(state) : speech.notSetUp;
  const checkMic = async () => {
    setCheckingMic(true);
    try {
      setMic(await apiFetch<MicCheck>("/api/meeting/mic-check", { method: "POST" }));
    } catch (error) {
      setMic({ state: "failed", level: null, error: error instanceof Error ? error.message : String(error) });
    } finally {
      setCheckingMic(false);
    }
  };
  // Before a meeting: listen once when the ready sheet opens (one short
  // sample on the hub; the grant is read first and never asked for).
  const readySheet = !active && !meetingId;
  useEffect(() => {
    if (readySheet) void checkMic();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [readySheet]);
  const perform = async (path: string, json: unknown = {}) => {
    await action.run(async () => {
      const value = await apiFetch<Record<string, unknown>>(path, { method: "POST", json });
      if (path.endsWith("start")) {
        setStopOutcome(null);
        const startedId = String((value.meeting as Record<string, unknown> | undefined)?.id ?? "");
        const named = readyName.trim();
        if (named) {
          // The name never blocks the recording: a refused name stays the
          // hub's default title, and Edit details can set it again.
          await apiFetch("/api/meeting", { method: "PATCH", json: { title: named } }).catch(() => undefined);
          setTitle(named);
          setReadyName("");
        }
        if (!meetingId && startedId) {
          useDesk.setState((st) => ({
            recording: "recording",
            recordingExternal: false,
            recordingStartedAt: Date.now(),
            liveMeetingId: startedId,
            recordingEpoch: st.recordingEpoch + 1,
          }));
          useDesk.getState().openPullout(`meeting:${startedId}`);
          useDesk.getState().closeSurfaceWindow("record-live");
          return;
        }
        setRetainedMeetingId("");
        setCaptureAlert("");
        setIntelResult(null);
        setState((current) => ({
          ...current,
          ...((value.meeting as Record<string, unknown>) ?? {}),
          // The last meeting's clock is not this one's.
          duration: undefined,
          active: true,
        }));
      }
      if (path.endsWith("stop")) {
        const stoppedId = meetingId || String(state.id ?? state.meeting_id ?? "");
        const outcome = parseMeetingStopOutcome(value, stoppedId);
        if (outcome.meetingId) setRetainedMeetingId(outcome.meetingId);
        setStopOutcome(outcome);
        if (outcome.captureStopped === false) {
          reportWriteFailure(
            "STOP RECORDING",
            new Error("capture remains active"),
            () => void perform(path, json),
            outcome.meetingId || undefined,
            "STILL RECORDING · THE HUB DID NOT STOP IT",
          );
          return;
        }
        if (meetingId) {
          const stopSubject = outcome.meetingId || stoppedId;
          if (outcome.saveStatus !== "saved" || outcome.deviceCleanupError) {
            const detail = [outcome.saveError, outcome.deviceCleanupError]
              .filter(Boolean)
              .join(" · ") || meetingStopReceiptLabel(outcome);
            const refusal = Object.assign(new Error(detail), { name: "ApiError" });
            reportWriteFailure(
              "STOP RECORDING",
              refusal,
              undefined,
              stopSubject || undefined,
              meetingStopReceiptLabel(outcome),
            );
          } else if (
            stopSubject &&
            currentWriteFailure()?.verb === "STOP RECORDING" &&
            currentWriteFailure()?.subject === stopSubject
          ) {
            clearWriteFailure(stopSubject);
          }
        }
        setState((current) => ({ ...current, active: false }));
        if (meetingId) {
          useDesk.setState((st) => ({
            recording: "idle", recordingExternal: false, recordingStartedAt: null, liveMeetingId: null,
            recordingEpoch: st.recordingEpoch + 1,
          }));
          onStopped?.();
        }
      }
    });
  };
  const recoverCapture = async () => {
    const current = stopOutcome;
    if (!current?.recoveryAvailable || !retainedMeetingId) return;
    await action.run(async () => {
      await apiFetch(`/api/meetings/${encodeURIComponent(retainedMeetingId)}/capture/recover`, {
        method: "POST",
      });
      // The original Stop facts prove JSON was retained; a successful
      // recovery response proves the durable Meeting row now exists.
      setStopOutcome({
        ...current,
        databaseSaved: true,
        saveStatus: "saved",
        saveError: "",
        recoveryAvailable: false,
      });
    });
  };
  const saveMetadata = async () => {
    await action.run(async () => {
      await apiFetch("/api/meeting", {
        method: "PATCH",
        json: {
          title,
          tags: tags
            .split(",")
            .map((value) => value.trim())
            .filter(Boolean),
        },
      });
      setState((current) => ({
        ...current,
        title,
        tags: tags
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean),
      }));
      setMetaOpen(false);
    });
  };
  const commitBookmark = async () => {
    if (!bookmarking) return;
    setBookmarking(false);
    const label = bookmark;
    setBookmark("");
    await perform("/api/bookmark", { label });
  };

  /* Window grammar (2026-10-24): title bar → toolbar → the body → status
     bar. "editor": edge to edge, the body scrolls. W2-LIVE: before a meeting
     the body holds the four steps; while it records, the transcript is the
     page. */
  useWindowInterior("editor");
  const verbs = (
    <Button
      variant={active ? "danger" : "primary"}
      dense
      loading={action.busy}
      onClick={() =>
        void perform(active ? "/api/meeting/stop" : "/api/meeting/start")
      }
    >
      {active ? <span className="live-stop-glyph" aria-hidden="true" /> : <ToolGlyph kind="record" />}
      {active ? "Stop meeting" : "Start meeting"}
    </Button>
  );
  const bookmarkVerb = active ? (
    bookmarking ? (
      <span
        className="live-bookmark-composer"
        onBlur={(event) => {
          if (!event.currentTarget.contains(event.relatedTarget as Node | null))
            void commitBookmark();
        }}
      >
        <StringGadget
          autoFocus
          label="Name this moment"
          value={bookmark}
          onChange={setBookmark}
          onKeyDown={(event) => {
            if (event.key === "Enter") void commitBookmark();
            if (event.key === "Escape") {
              setBookmark("");
              setBookmarking(false);
            }
          }}
        />
      </span>
    ) : (
      <Button dense variant="secondary" onClick={() => setBookmarking(true)} data-testid="live-bookmark">
        <svg className="kit-toolglyph" width={16} height={16} viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <path d="M3.75 14V2.5M3.75 3h8.25l-2 3 2 3H3.75" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        Bookmark
      </Button>
    )
  ) : null;
  const settingsVerb = (
    <Button
      dense
      variant="secondary"
      data-testid="live-settings"
      aria-label="Settings"
      title="Settings ▸ Meetings"
      onClick={() => openSurfaceOr("configure-settings", "/settings", "meetings")}
    >
      <svg className="kit-toolglyph" width={16} height={16} viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <circle cx="8" cy="8" r="2.25" stroke="currentColor" strokeWidth={1.5} />
        <path d="M8 1.75v1.75M8 12.5v1.75M1.75 8h1.75M12.5 8h1.75M3.6 3.6l1.25 1.25M11.15 11.15l1.25 1.25M3.6 12.4l1.25-1.25M11.15 4.85l1.25-1.25" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" />
      </svg>
      <span className="live-verb-label">Settings</span>
    </Button>
  );
  const intelState = String(
    (state.intel_status as Record<string, unknown> | undefined)?.state ??
      state.intel_status ??
      "idle",
  );
  /* HS-202-04 (M6, UX-CANON A.7) — one fact, one place. The link to the
     hub (`runtime/RuntimeBus.tsx` connecting/connected/reconnecting/
     offline) and the capture are different facts, each named. */
  const link: string = connection || "unknown";
  const linkTone =
    link === "connected" ? ("ok" as const) : link === "offline" ? ("fail" as const) : link === "unknown" ? undefined : ("warn" as const);

  const intelSummary = String(intelResult?.summary ?? "");
  const intelTopics = Array.isArray(intelResult?.topics)
    ? (intelResult.topics as unknown[]).map(String).filter(Boolean)
    : [];
  const intelActionCount = Array.isArray(intelResult?.action_items)
    ? (intelResult.action_items as unknown[]).length
    : Number(intelResult?.action_item_count ?? 0);
  const intelFace =
    intelResult ? (
      /* HS-202-04 (F06) — a meeting result is a SUMMARY on every face
         (`docs/product-language.json:23`). */
      <SurfaceSection
        label="Summary"
        actions={<DotWord tone="ok">Ready</DotWord>}
      >
        <div className="live-intel-result">
          {intelSummary ? <p>{intelSummary}</p> : null}
          {intelTopics.length ? (
            <div className="surface-actions">
              {intelTopics.slice(0, 8).map((topic) => (
                <span className="surface-token" key={topic}>
                  {topic}
                </span>
              ))}
            </div>
          ) : null}
          {/* HS-202-04 (UX-CANON A.8) — `countToken` withholds the zero,
              and the line is omitted when it would carry no fact. */}
          <SurfaceFacts
            value={[
              countToken(intelActionCount, "action item", "action items"),
              intelResult.final ? "final" : "",
            ]
              .filter(Boolean)
              .join(" · ")}
          />
        </div>
      </SurfaceSection>
    ) : null;

  /* W2-LIVE: the summary engine by its name (the hub's own fact), or the
     honest word when there is none. Egress is not drawn here (A.9 as
     amended 2026-10-25); Settings ▸ Meetings and Engines disclose it. */
  const meetingsHub = (settingsHub.data?.meetings ?? null) as Record<string, unknown> | null;
  const intelPosture = runtimeStatus.data?.intel_egress as Record<string, unknown> | undefined;
  const engineName = presentValue(meetingsHub?.engine);
  const summaryItem: StatusBarItem | null =
    meetingsHub?.summariesOff === true || intelPosture?.enabled === false
      ? { key: "summary", text: "Summaries off", testId: "live-summary-engine" }
      : intelState === "running" || intelState === "queued"
        ? { key: "summary", lamp: "info" as const, text: intelState === "running" ? "Summary running" : "Summary queued", testId: "live-summary-engine" }
        : intelState === "error"
          ? { key: "summary", lamp: "fail" as const, text: "Summary failed", testId: "live-summary-engine" }
          : meetingsHub?.engineSet === false
            ? { key: "summary", lamp: "warn" as const, text: "No engine for summaries", testId: "live-summary-engine" }
            : engineName
              ? { key: "summary", text: `Summaries on ${engineName}`, testId: "live-summary-engine" }
              : null;

  /* The status bar: the capture state with its clock, audio only, the
     summary engine, and the link to the hub, each said once. */
  const statusItems: StatusBarItem[] = [
    // W1-TRUTH (atlas 2026-10-27): never "Ready" next to "Speech not set
    // up". Before a meeting with no speech model the one state is the
    // warning (its one verb, Set up speech, is in the toolbar).
    active
      ? { key: "capture", lamp: "fail" as const, text: "Recording", value: duration, testId: "live-capture-state" }
      : speech.notSetUp
        ? { key: "capture", lamp: "warn" as const, text: "Speech not set up", testId: "live-capture-state" }
        : { key: "capture", lamp: "ok" as const, text: "Ready", testId: "live-capture-state" },
    active && audioOnly ? { key: "audio", text: "Audio only" } : null,
    summaryItem,
    /* W2-LIVE-2: no title here (the title bar names the meeting), so the
       phone keeps one line; on the phone the link is said only when it is
       not connected. */
    compact && link === "connected"
      ? null
      : { key: "link", lamp: linkTone, text: `Link ${link}`, testId: "live-link-state" },
  ].filter(Boolean) as StatusBarItem[];

  /* Live slice 3: the transcript's foot. The saved reach is the newest
     pass of THIS meeting, else the checkpoint /api/state carries. */
  const meetingKey = String(meetingId || state.id || state.meeting_id || "");
  const ownPass = pass && (!pass.meeting_id || !meetingKey || pass.meeting_id === meetingKey) ? pass : null;
  const savedThrough = Number(ownPass?.saved_through ?? state.capture_checkpoint_seconds ?? 0) || 0;
  const listening = (
    <LiveListening
      pass={ownPass}
      savedThrough={savedThrough}
      micLabel={String(state.mic_label || "Me")}
      remoteLabel={String(state.remote_label || "Remote")}
      quiet={audioOnly}
      idleWord={segments.length ? "Listening" : "Listening for speech"}
    />
  );

  return (
    <>
      {hero ? (
        hero(verbs)
      ) : (
        <Toolbar label="Live meeting" data-testid="live-toolbar" trailing={settingsVerb} trailingStays>
          {verbs}
          {bookmarkVerb}
          {active ? (
            <Button dense variant="secondary" aria-label="Edit details" onClick={() => setMetaOpen((open) => !open)}>
              <ToolGlyph kind="edit" />
              <span className="live-verb-label">Edit details</span>
            </Button>
          ) : null}
          {/* W2-LIVE-2: Set up speech is the Transcript row's verb on the
              ready sheet; while it records the status bar says Audio only. */}
        </Toolbar>
      )}
      <div className="live-room" data-testid="live-room" data-active={active || undefined}>
      {action.message ? <SurfaceState error={action.message} /> : null}
      {captureAlert ? (
        <SurfaceState
          error={`Capture recovery · ${captureAlert}`}
          onRetry={() => setCaptureAlert("")}
        />
      ) : null}
      {bookmarkReceipt ? (
        <p className="surface-receipt-line" data-tone="ok" role="status">
          <svg width="12" height="12" viewBox="0 0 16 16" aria-hidden="true" style={{ flexShrink: 0 }}><path d="M3.5 8.5 6.5 11.5 12.5 4.5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
          {bookmarkReceipt.text}
        </p>
      ) : null}
      {retainedMeetingId && stopOutcome?.saveStatus === "saved" ? (
        <p
          className="surface-receipt-line"
          data-tone={stopOutcome.deviceCleanupError ? "warn" : "ok"}
          role="status"
          title={stopOutcome.deviceCleanupError || undefined}
        >
          <svg width="12" height="12" viewBox="0 0 16 16" aria-hidden="true" style={{ flexShrink: 0 }}><path d="M3.5 8.5 6.5 11.5 12.5 4.5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg>{" "}
          {meetingStopReceiptLabel(stopOutcome)}{" "}
          <Button
            variant="chrome"
            className="btn-link"
            onClick={() => openPrimitive(`meeting:${retainedMeetingId}`)}
          >
            Return to saved Meeting
          </Button>
        </p>
      ) : null}
      {stopOutcome && stopOutcome.captureStopped !== false && stopOutcome.saveStatus !== "saved" ? (
        <p
          className="surface-receipt-line"
          data-tone="warn"
          role="status"
          title={[stopOutcome.saveError, stopOutcome.deviceCleanupError]
            .filter(Boolean)
            .join(" · ") || undefined}
        >
          <svg width="12" height="12" viewBox="0 0 16 16" aria-hidden="true" style={{ flexShrink: 0 }}><path d="M8 2.5v6M8 11.5v1" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg>{" "}
          {meetingStopReceiptLabel(stopOutcome)}
          {stopOutcome.databaseSaved === true && retainedMeetingId ? (
            <Button
              variant="chrome"
              className="btn-link"
              onClick={() => openPrimitive(`meeting:${retainedMeetingId}`)}
            >
              Open Meeting
            </Button>
          ) : null}
          {stopOutcome.recoveryAvailable && retainedMeetingId ? (
            <Button variant="ghost" dense onClick={() => void recoverCapture()}>
              Retry recovery
            </Button>
          ) : null}
        </p>
      ) : null}
      {metaOpen ? (
        <GadgetGroup label="Meeting details">
          <GadgetRow label="Title">
            <StringGadget label="Title" value={title} onChange={setTitle} />
          </GadgetRow>
          <GadgetRow label="Tags" fact="Comma separated">
            <StringGadget label="Tags" value={tags} onChange={setTags} />
          </GadgetRow>
          <div className="surface-actions">
            <Button variant="primary" dense loading={action.busy} onClick={saveMetadata}>
              Save
            </Button>
            <Button dense variant="ghost" onClick={() => setMetaOpen(false)}>
              Close
            </Button>
          </div>
        </GadgetGroup>
      ) : null}
      {active ? null : (
        /* PHILO-17 (the Today language), W1-TRUTH: Today's four steps
           (Prep, Record, Summary, Send follow-up); Live is at Record. */
        <div className="live-deck" data-testid="live-deck">
          <Steps label="Meeting steps" data-testid="live-steps" steps={meetingSteps(1)} />
        </div>
      )}
      {intelFace}
      {segments.length ? (
        <LiveTranscript segments={segments} listening={active} listen={listening} />
      ) : active ? (
        <div className="live-empty" role="status" data-testid="live-transcript-empty">
          {audioOnly ? NO_TRANSCRIPT_SPEECH : listening}
        </div>
      ) : (
        /* W2-LIVE-2 (canvas A, Before): the ready sheet, not an empty
           Transcript head. */
        <LiveReady settings={settings.data} hub={settingsHub.data} speech={speech}
          name={readyName} onName={setReadyName}
          mic={mic} checkingMic={checkingMic} onCheckMic={() => void checkMic()} />
      )}
      </div>
      <StatusBar items={statusItems} data-testid="live-statusbar" />
    </>
  );
}
