import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { openPrimitive } from "../../desk/shell";
import { useDesk } from "../../desk/store";
import { openSurfaceOr } from "../../desk/shell";
import type {
  CoreProps,
  MeetingStateResponse,
  RuntimeStatusResponse,
} from "./core-types";
import { apiFetch } from "../../lib/api";
import { useRuntimeBus } from "../../runtime/RuntimeBus";
import { asRows, useResource } from "../pageSupport";
import { useAction } from "./core-hooks";
import { frameNames } from "../../desk/components/window/dockState";
import { StringGadget } from "../../desk/surface/gadgets";
import { presentValue } from "../../desk/surface/format";
import { StatusBar, type StatusBarItem } from "../../desk/surface/kit";
import { useWindowInterior } from "../../desk/surface/interior";

import { LiveProject } from "./LiveProject";
import { LiveReady } from "./LiveReady";
import { liveListeningParts, useMeetingLevel, type MicCheck, type TranscriptPass } from "./LiveLevel";

import { burstTimer } from "../../desk/burstTimer";
import { onReturnToTask } from "../../desk/returnToTask";
import { useSpeechSetup } from "../../desk/firstrun/SpeechSetup";
import { NO_TRANSCRIPT_SPEECH, speechWasMissing } from "../../desk/firstrun/speechTruth";
import {
  meetingStopReceiptLabel,
  parseMeetingStopOutcome,
  type MeetingStopOutcome,
} from "../../meetings/meetingStopOutcome";
import { clearWriteFailure, currentWriteFailure, reportWriteFailure } from "../../desk/hooks/useWriteReceipt";
import {
  useWindowMast,
  useWindowTitle,
  PreferencePane,
  PreferenceWell,
  PaneNotice,
  TranscriptWell,
  ListPane,
  ListView,
  ReadingDocument,
  PaneInspector,
  InspectorBody,
  InspectorFacts,
  InspectorForm,
  InspectorFigures,
  useWindowBack,
  useHasWindowBack,
  ActionNotice,
  CycleGadget,
  StepTrack,
  LiveLevel, Meter, Elapsed, PaneActions, PaneViews, VerbToolbar, type ListVerb,
} from "../../desk/surface";
import { plainFailure } from "../../desk/surface/plainFailure";
import { useOnDeskChanged } from "../../desk/useDeskChangedRefresh";
import { spriteUrl } from "../../desk/sprites";
import { readPlannedRoute } from "../../meetings/summaryRoute";
import { useSummaryRun } from "./history/useSummaryRun";
import { summaryFailureReason } from "./history/SummaryState";
import { ShowMe } from "../../desk/walk/ShowMe";

type Segment = Record<string, unknown>;

/** PHILO-17 (owner 2026-10-10, "A meeting opens in one window"): the live
 *  room is the body of the meeting's own window while it records
 *  (`meetingId`); Stop keeps its transcript and work track. Open meeting
 *  hands the same window to its saved record (`onStopped`). Without `meetingId` it is the Live meeting window, the
 *  place a meeting starts; the started meeting then opens in its own window. */
export type LiveCoreProps = CoreProps & {
  meetingId?: string;
  captureStopped?: boolean;
  onStopped?: () => void;
};

export function LiveCore({ meetingId, captureStopped = false, onStopped }: LiveCoreProps) {
  const initial = useResource<MeetingStateResponse>("/api/state", {});
  const runtimeStatus = useResource<RuntimeStatusResponse>("/api/runtime/status", {});
  /* W2-LIVE: the summary engine by its name, the fact Settings ▸ Meetings
     shows on its "Summaries run on" row (`meetings.engine`, `engineSet`,
     `summariesOff` from /api/settings/hub). */
  const settingsHub = useResource<Record<string, unknown>>("/api/settings/hub", {});
  /* W2-LIVE-2: the ready sheet's devices (`meeting.mic_device`,
     `meeting.system_audio_device`), the facts Settings ▸ Meetings shows. */
  const settings = useResource<Record<string, unknown>>("/api/settings", {});
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
    const offDeskChanged = subscribe("desk_changed", (frame) => {
      if (frameNames(frame?.data, [
        "assignment", "engine", "inference", "inference_assignment", "meeting", "meeting_summary",
        "model", "model_profile", "setting", "settings",
      ])) bump();
    });
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
  const [decisions, setDecisions] = useState<Segment[]>([]);
  const [caughtError, setCaughtError] = useState("");
  const caughtSequence = useRef(0);
  const intelArrived = useRef(false);
  const action = useAction();
  const [bookmark, setBookmark] = useState("");
  const [bookmarking, setBookmarking] = useState(false);
  const [metaOpen, setMetaOpen] = useState(false);
  const [projectOpen, setProjectOpen] = useState(false);
  const [projectTicket, setProjectTicket] = useState(0);
  const projectTicketNow = useRef(projectTicket);
  projectTicketNow.current = projectTicket;
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [showCaught, setShowCaught] = useState(true);
  const [caughtId, setCaughtId] = useState<string | null>(null);
  const [stage, setStage] = useState("transcript");
  const [title, setTitle] = useState("");
  const [tags, setTags] = useState("");
  const drafts = useRef({ title, tags, bookmark });
  drafts.current = { title, tags, bookmark };
  const [retainedMeetingId, setRetainedMeetingId] = useState("");
  const [stopOutcome, setStopOutcome] = useState<MeetingStopOutcome | null>(null);
  const retained = useRef(false);
  retained.current = Boolean(captureStopped || state.stopped || (stopOutcome && stopOutcome.captureStopped !== false));
  const meetingKey = String(meetingId || state.id || state.meeting_id || "");
  const [savedReadError, setSavedReadError] = useState("");
  const savedReadSequence = useRef(0);
  const retainStopped = (outcome: MeetingStopOutcome, value: unknown) => {
    retained.current = true;
    setStopOutcome(outcome);
    if (outcome.saveStatus === "saved" && !outcome.deviceCleanupError) setBookmarkReceipt({ seq: ++bookmarkSeq.current, text: meetingStopReceiptLabel(outcome) });
    if (outcome.meetingId) setRetainedMeetingId(outcome.meetingId);
    const snapshot = value && typeof value === "object" ? value as Record<string, unknown> : {};
    setState(current => ({ ...current, ...snapshot, duration: snapshot.formatted_duration ?? current.duration, active: false, meeting_active: false, stopped: true }));
    if (Array.isArray(snapshot.segments)) setSegments(asRows(snapshot, ["segments"]));
  };
  // Routed analysis publishes one elected semantic result. The provider token
  // stream retired with the C1 controller boundary; no private partial output
  // reaches this surface or a journal.
  const [intelResult, setIntelResult] = useState<Record<string, unknown> | null>(
    null,
  );
  const [bookmarkReceipt, setBookmarkReceipt] = useState<{
    text: string;
    project?: string;
    seq: number;
  } | null>(null);
  const [paneLayout,setPaneLayout] = useState<"split"|"compact">("compact");
  const [view, setView] = useState("transcript");
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
    if (initial.loading) return;
    setState((current) => ({ ...initial.data, ...current }));
    setSegments((current) => {
      const snapshot = asRows(initial.data, ["segments"]);
      const key = (row: Segment) => String(row.id ?? row.segment_id ?? `${row.start_time ?? row.timestamp}-${row.end_time}-${row.text ?? row.transcript}`);
      const seen = new Set(snapshot.map(key));
      return [...snapshot, ...current.filter((row) => !seen.has(key(row)))];
    });
    if (!intelArrived.current)
      setIntelResult(
        initial.data.intel && typeof initial.data.intel === "object"
          ? (initial.data.intel as Record<string, unknown>)
          : null,
      );
    setTitle(String(initial.data.title ?? ""));
    setTags(
      Array.isArray(initial.data.tags) ? initial.data.tags.join(", ") : "",
    );
  }, [initial.data, initial.loading]);
  useEffect(
    () =>
      subscribe("*", (frame) => {
        if (retained.current) return;
        if (frame.type === "stopped") {
          const payload = frame.data && typeof frame.data === "object" ? frame.data as Record<string, unknown> : {};
          const outcome = parseMeetingStopOutcome(payload, meetingKey);
          if (outcome.captureStopped !== false) retainStopped(outcome, payload.meeting);
          return;
        }
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
            ...(frame.type === "stopped" ? { active: false, meeting_active: false } : {}),
            ...(frame.type === "meeting_started" || frame.type === "meeting_updated"
              ? (frame.data as Record<string, unknown>)
              : {}),
          }));
      }),
    [subscribe, meetingKey],
  );

  useEffect(
    () =>
      subscribe("intel_complete", (frame) => {
        const payload = frame.data as Record<string, unknown> | null;
        if (retained.current || (payload?.meeting_id && meetingKey && payload.meeting_id !== meetingKey)) return;
        intelArrived.current = true;
        setIntelResult(
          frame.data && typeof frame.data === "object"
            ? (frame.data as Record<string, unknown>)
            : null,
        );
      }),
    [subscribe, meetingKey],
  );

  useEffect(
    () =>
      subscribe("transcript_pass", (frame) => {
        if (retained.current) return;
        if (frame.data && typeof frame.data === "object") setPass(frame.data as TranscriptPass);
      }),
    [subscribe],
  );

  // ── the bookmark's confirmation ────────────────────────────────────
  useEffect(
    () =>
      subscribe("bookmark", (frame) => {
        if (retained.current) return;
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
        if (data) setState(current => ({ ...current, bookmarks: [...asRows(current, ["bookmarks"]), data] }));
        bookmarkSeq.current += 1;
        setBookmarkReceipt({
          seq: bookmarkSeq.current,
          text: [label || "Bookmark dropped", at].filter(Boolean).join(" · "),
        });
      }),
    [subscribe],
  );


  // ── capture told the truth about itself ────────────────────────────
  useEffect(
    () =>
      subscribe("capture_recovery", (frame) => {
        if (retained.current) return;
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
  const active = !captureStopped && Boolean(
    (meetingId && state.active !== false && state.meeting_active !== false) ||
      (state.active ?? state.meeting_active ?? state.status === "recording"),
  );
  const level = useMeetingLevel(active);
  // PHILO-17 speech: the live `duration` frame (a "MM:SS" string, one a
  // second) leads. `formatted_duration` arrives once with meeting_started /
  // meeting_updated and stood in front of the live frame, so REC froze at
  // 00:01 while the dock counter ran.
  const readCaught = useCallback(async () => {
    const mine = ++caughtSequence.current;
    if (!meetingKey) { setDecisions([]); return; }
    try {
      const answer = await apiFetch<{ decisions?: Segment[] }>(`/api/decisions?scope=all&limit=500&meeting_id=${encodeURIComponent(meetingKey)}`);
      if (mine === caughtSequence.current) { setDecisions(answer.decisions ?? []); setCaughtError(""); }
    } catch (cause) { if (mine === caughtSequence.current) setCaughtError(plainFailure("Caught decisions not read", cause)); }
  }, [meetingKey]);
  useEffect(() => { void readCaught(); return () => { caughtSequence.current += 1; }; }, [readCaught, intelResult]);
  useOnDeskChanged(() => { void readCaught(); }, ["decision"]);
  const readSaved = useCallback(async () => {
    if (!retained.current || !meetingKey || stopOutcome?.databaseSaved === false) return;
    const mine = ++savedReadSequence.current;
    try {
      const saved = await apiFetch<Record<string, unknown>>(`/api/meetings/${encodeURIComponent(meetingKey)}?include_parked=true`);
      if (mine !== savedReadSequence.current) return;
      if (saved.id !== meetingKey) return;
      setState(current => ({ ...current, ...saved, duration: saved.formatted_duration ?? current.duration, active: false, meeting_active: false, stopped: true }));
      if (Array.isArray(saved.segments)) setSegments(asRows(saved, ["segments"]));
      if (saved.intel && typeof saved.intel === "object") setIntelResult(saved.intel as Record<string, unknown>);
      setSavedReadError("");
    } catch (cause) { if (mine === savedReadSequence.current) setSavedReadError(plainFailure("Meeting not read", cause)); }
  }, [meetingKey, stopOutcome?.databaseSaved]);
  useEffect(() => {
    const burst = burstTimer(() => void readSaved(), 300);
    const off = subscribe("desk_changed", frame => {
      if (!retained.current || !frame.data || typeof frame.data !== "object") return;
      const data = frame.data as Record<string, unknown>;
      const changed = Array.isArray(data.changes) ? data.changes : [data];
      if (changed.some(row => row && typeof row === "object" && String(row.id) === meetingKey && ["meeting", "meeting_summary"].includes(String(row.kind)))) burst.bump();
    });
    const returned = () => { if (retained.current) void readSaved(); };
    const offReturn = onReturnToTask(returned);
    window.addEventListener("focus", returned);
    return () => { burst.cancel(); off(); offReturn(); window.removeEventListener("focus", returned); savedReadSequence.current++; };
  }, [subscribe, meetingKey, readSaved]);
  const summary = useSummaryRun(() => readPlannedRoute(state), readSaved);
  const retrySummary = () => summary.run(meetingKey, readPlannedRoute(state));
  const markedMoments = useMemo(() => new Set(asRows(state, ["bookmarks"]).map(moment => {
    const at = Number(moment.timestamp ?? moment.time);
    return Number.isFinite(at) ? segments.reduce((picked, row, index) => Number(row.start_time) <= at ? index : picked, -1) : -1;
  }).filter(index => index >= 0)), [segments, state.bookmarks]);
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
  const readySheet = !initial.loading && !active && !meetingId && !initial.data.meeting_active && !initial.data.active;
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
        if (startedId && startedId !== meetingId) {
          useDesk.setState((st) => ({
            recording: "recording",
            recordingExternal: false,
            recordingStartedAt: Date.now(),
            liveMeetingId: startedId,
            recordingEpoch: st.recordingEpoch + 1,
          }));
          useDesk.getState().openPullout(`meeting:${startedId}`);
          if (!meetingId) useDesk.getState().closeSurfaceWindow("record-live");
          else onStopped?.();
          return;
        }
        setRetainedMeetingId("");
        setCaptureAlert("");
        setIntelResult(null);
        intelArrived.current = false;
        setSegments([]);
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
            "Still recording · The hub did not stop it",
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
        retainStopped(outcome, value.meeting);
        if (meetingId) {
          useDesk.setState((st) => ({
            recording: "idle", recordingExternal: false, recordingStartedAt: null, liveMeetingId: null,
            recordingEpoch: st.recordingEpoch + 1,
          }));
          // Keep the stopped transcript in this window until Open meeting.
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
      setBookmarkReceipt({ seq: ++bookmarkSeq.current, text: "Meeting saved" });
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
    if (!active) return;
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
      if (drafts.current.title === title && drafts.current.tags === tags) { setMetaOpen(false); setInspectorOpen(false); }
    });
  };
  const commitBookmark = async () => {
    if (!bookmarking || !active) return;
    const label = bookmark;
    await action.run(async () => {
      await apiFetch("/api/bookmark", { method: "POST", json: { label } });
      if (drafts.current.bookmark === label) { setBookmark(""); setBookmarking(false); setInspectorOpen(false); }
    });
  };

  // The frame, fitted verb row and bounded transcript/inspector own their seats.
  useWindowInterior("list");
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

  const caught: Array<Record<string, unknown>> = [
    ...decisions.map((row) => ({ ...row, kind: "Decision" })),
    ...asRows(intelResult ?? {}, ["action_items"]).map((row) => ({ ...row, kind: "Owed" })),
  ];
  /* W2-LIVE: the summary engine by its name (the hub's own fact), or the
     honest word when there is none. Egress is not drawn here (A.9 as
     amended 2026-10-25); Settings ▸ Meetings and Engines disclose it. */
  const meetingsHub = (settingsHub.data?.meetings ?? null) as Record<string, unknown> | null;
  const intelPosture = runtimeStatus.data?.intel_egress as Record<string, unknown> | undefined;
  const engineName = presentValue(meetingsHub?.engine);
  let summaryItem: StatusBarItem | null = null;
  if (intelState === "running" || intelState === "queued") summaryItem = {
    key: "summary", lamp: "info", priority: 80,
    text: intelState === "running" ? "Summary running" : "Summary queued", testId: "live-summary-engine",
    meter: { total: 1, current: 0, state: "working", label: intelState === "running" ? "Summary running" : "Summary queued" },
  };
  else if (intelState === "error") summaryItem = { key: "summary", lamp: "fail", priority: 100, text: "Summary failed", testId: "live-summary-engine" };
  else if (meetingsHub?.summariesOff === true || intelPosture?.enabled === false) summaryItem = { key: "summary", text: "Summaries off", testId: "live-summary-engine" };
  else if (meetingsHub?.engineSet === false) summaryItem = { key: "summary", lamp: "warn", priority: 100, text: "No engine for summaries", testId: "live-summary-engine" };
  else if (engineName) summaryItem = { key: "summary", text: `Summaries on ${engineName}`, testId: "live-summary-engine" };

  /* The status bar: the capture state with its clock, audio only, the
     summary engine, and the link to the hub, each said once. */
  const ownPass = pass && (!pass.meeting_id || !meetingKey || pass.meeting_id === meetingKey) ? pass : null;
  const statusItems: StatusBarItem[] = [
    action.message ? { key: "write", lamp: "fail" as const, text: "Failed", priority: 100 } : null,
    // W1-TRUTH (atlas 2026-10-27): never "Ready" next to "Speech not set
    // up". Before a meeting with no speech model the one state is the
    // warning (its one verb, Set up speech, is in the toolbar).
    active
      ? { key: "capture", lamp: "fail" as const, live: true, text: "Recording", value: duration, testId: "live-capture-state" }
      : (captureStopped || stopOutcome || state.stopped)
        ? { key: "capture", lamp: "idle" as const, text: "Stopped", value: duration, testId: "live-capture-state" }
        : speech.notSetUp
        ? {
            key: "capture",
            lamp: "warn" as const,
            text: "Speech not set up",
            testId: "live-capture-state",
          }
        : {
            key: "capture",
            lamp: action.message ? ("fail" as const) : ("idle" as const),
            text: action.message ? "Failed" : stopOutcome ? "Stopped" : "Ready",
            testId: "live-capture-state",
          },
    active && audioOnly ? { key: "audio", text: "Audio only" } : null,
    ...(active && segments.length ? liveListeningParts({level,pass:ownPass,savedThrough:Number(ownPass?.saved_through ?? state.capture_checkpoint_seconds ?? 0),micLabel:String(state.mic_label || "Me"),remoteLabel:String(state.remote_label || "Remote"),quiet:audioOnly}) : []),
    summaryItem,
    /* W6-A (atlas pass 3, defect 17): this is the page's own link to the
       hub, not a device of his. Connected is the normal case and says
       nothing; a lost link names what is lost, at both widths. */
    link === "connected" || link === "unknown"
      ? null
      : { key: "link", lamp: linkTone, text: link === "offline" ? "Hub not reached" : "Connecting to the hub", testId: "live-link-state" },
  ].filter(Boolean) as StatusBarItem[];

  const retryCapture = async () => {
    if (!meetingKey) { void initial.reload(); return; }
    try {
      const answer = await apiFetch<{ recovered?: boolean }>(`/api/meetings/${encodeURIComponent(meetingKey)}/capture/recover`, { method: "POST" });
      if (answer.recovered) setCaptureAlert("");
    } catch (cause) { setCaptureAlert(plainFailure("Capture not recovered", cause)); }
  };

  const name = String(state.title || title || "Live meeting");
  const stopped = !active && Boolean(captureStopped || stopOutcome || state.stopped);
  const savedMeetingId = retainedMeetingId || (stopped ? meetingKey : "");
  const micDevice = String(
    (settings.data.meeting as Record<string, unknown> | undefined)?.mic_device || "System default",
  );
  const people = Number(state.people_count ?? state.participant_count) || 0;
  useWindowTitle(active || stopped ? name : null, [active, stopped, name]);
  useWindowMast({
    line:
      active
          ? ["Recording", people > 0 ? `${people} ${people === 1 ? "person" : "people"}` : ""].filter(Boolean).join(" · ")
          : stopped
            ? intelState === "running"
              ? "Stopped · summary running"
              : "Stopped"
            : mic?.state === "not_allowed" ? "Microphone not allowed" : speech.notSetUp
              ? "Speech not set up"
              : "Ready",
    figures: active || stopped ? [{ value: duration, label: active ? "recording" : "length", tone: active ? "stop" : undefined }] : [],
  });
  const tasks = caught.filter((row) => row.kind === "Owed").length;
  const microphone = (
    <CycleGadget
      roster
      label="Microphone"
      value={micDevice}
      options={[{ value: micDevice }, { value: "settings", label: "Settings…" }]}
      onChange={(value) => {
        if (value === "settings") openSurfaceOr("configure-settings", "/settings", "meetings");
      }}
    />
  );
  const transcriptEnd = Math.max(0, ...segments.map(row => Number(row.end_time ?? row.start_time) || 0));
  const transcriptTo = `${Math.floor(transcriptEnd / 60)}:${String(Math.floor(transcriptEnd % 60)).padStart(2, "0")}`;
  const savedFact = stopOutcome ? stopOutcome.databaseSaved === true ? "Meeting and transcript" : stopOutcome.jsonSaved === true ? "Transcript file only" : "Not confirmed" : state.capture_status === "finalized" ? "Meeting and transcript" : "Not confirmed";
  const facts = (
    <InspectorFacts
      header={false}
      name="Meeting facts"
      data-feedback-redact="true"
      rows={[
        ...(bookmarkReceipt ? [{label:"Last result",value:bookmarkReceipt.text}] : []),
        ...(bookmarkReceipt?.project ? [{ label: "Project", value: bookmarkReceipt.project }] : []),
        ...(stopped ? [{ label: "Length", value: duration }, { label: "Saved", value: savedFact }] : [{ label: "Microphone", value: micDevice }]),
        {
          label: "Devices",
          value:
            Array.isArray(state.devices) && state.devices.length
              ? state.devices
                  .map((device) =>
                    typeof device === "object" && device
                      ? String(
                          (device as Record<string, unknown>).name ||
                            (device as Record<string, unknown>).id ||
                            "Device",
                        )
                      : String(device),
                  )
                  .join(", ")
              : "None attached",
        },
      ]}
    />
  );
  const inspector = projectOpen ? <LiveProject key={projectTicket} meetingId={meetingKey} onCancel={() => { setProjectOpen(false); setInspectorOpen(false); }} onAdded={name => { if (projectTicketNow.current === projectTicket) { setProjectOpen(false); setInspectorOpen(false); } bookmarkSeq.current += 1; setBookmarkReceipt({ seq: bookmarkSeq.current, text: `Added to ${name}`, project: name }); }} /> : metaOpen ? (
    <PaneInspector label="Meeting details" testId="live-details">
      <InspectorForm
        fit="rows"
        rows={[
          {
            label: "Title",
            control: <StringGadget label="Title" value={title} onChange={setTitle} />,
          },
          {
            label: "Tags",
            control: <StringGadget label="Tags" value={tags} onChange={setTags} />,
          },
        ]}
        notice={action.message ? <ActionNotice tone="danger"><span data-feedback-redact="true">Details not saved · {action.message} · Review the details. Your edits are kept.</span></ActionNotice> : undefined}
        completion={{
          cancel: () => {
            setMetaOpen(false);
            setInspectorOpen(false);
            action.setMessage("");
          },
          primary: {
            label: "Save",
            disabled: !active,
            busy: action.busy,
            run: () => void saveMetadata(),
          },
        }}
      />
    </PaneInspector>
  ) : bookmarking ? (
    <PaneInspector label="Name this moment">
      <InspectorForm
        fit="rows"
        rows={[
          {
            label: "Moment",
            control: (
              <StringGadget
                label="Name this moment"
                value={bookmark}
                onChange={setBookmark}
                onKeyDown={(event) => {
                  if (event.key === "Enter") void commitBookmark();
                }}
              />
            ),
          },
        ]}
        notice={action.message ? <ActionNotice tone="danger"><span data-feedback-redact="true">Moment not saved · {action.message} · The name is kept.</span></ActionNotice> : undefined}
        completion={{
          cancel: () => {
            setBookmark("");
            setBookmarking(false);
            setInspectorOpen(false);
            action.setMessage("");
          },
          primary: {
            label: "Bookmark",
            disabled: !active,
            busy: action.busy,
            run: () => void commitBookmark(),
          },
        }}
      />
    </PaneInspector>
  ) : (
    <PaneInspector label={name} object={<img src={spriteUrl("meeting", meetingKey, "rest", null, 32)} alt="" width={32} height={32} />} testId="live-caught">
      <InspectorBody fit="rows">
        {decisions.length || tasks ? <InspectorFigures label="Caught so far" figures={tasks && decisions.length ? [{ value: decisions.length, label: decisions.length === 1 ? "decision" : "decisions", tone: "ask" }, { value: tasks, label: tasks === 1 ? "task" : "tasks" }] : [{ value: tasks || decisions.length, label: tasks ? tasks === 1 ? "task" : "tasks" : decisions.length === 1 ? "decision" : "decisions", tone: tasks ? "info" : "ask" }]} /> : null}
        {caughtError ? (
          <ActionNotice tone="danger" action={{ label: "Retry", onClick: () => void readCaught() }}>
            {caughtError}
          </ActionNotice>
        ) : null}
        <ListView
          label="Caught so far"
          rows={caught.map((row, index) => ({
            id: String(row.id ?? index),
            kind: row.kind === "Decision" ? "decision" : "action",
            name: String(row.text ?? row.task ?? row.description ?? row.title ?? row.decision ?? ""),
            detail: [row.kind === "Owed" ? "Task" : row.kind, row.owner].filter(Boolean).join(" · "),
            leadingLamp: {
              label: String(row.kind),
              state: row.kind === "Decision" ? ("waiting" as const) : ("working" as const),
            },
            cells: {
              at:
                typeof row.source_timestamp === "number"
                  ? `${Math.floor(row.source_timestamp / 60)}:${String(Math.floor(row.source_timestamp % 60)).padStart(2, "0")}`
                  : "",
            },
          }))}
          columns={[
            { key: "name", word: "Caught so far", track: "minmax(0, 3fr)" },
            { key: "at", word: "At", track: "minmax(52px, 0fr)", minWidth: 52, priority: 0 },
          ]}
          selectedId={caughtId}
          onSelect={setCaughtId}
          empty="Nothing caught yet"
          rowProps={() => ({ "data-feedback-redact": "true" })}
        />
        {facts}
      </InspectorBody>
    </PaneInspector>
  );
  const openSaved = () => {
    if (onStopped) onStopped();
    else if (savedMeetingId) openPrimitive(`meeting:${savedMeetingId}`);
  };
  const hasInspector = projectOpen || metaOpen || bookmarking || ((paneLayout === "split" || view !== "caught") && (inspectorOpen || (showCaught && (active || stopped || caught.length > 0))));
  const hostBack = useHasWindowBack();
  const closeInspector = () => { setInspectorOpen(false); setMetaOpen(false); setBookmarking(false); setProjectOpen(false); };
  useWindowBack(inspectorOpen ? { onBack: closeInspector, label: "Back", testId: "live-inspector-back" } : null, [inspectorOpen]);
  const changeView = (value: string) => { closeInspector(); setView(value); if (value === "caught") setShowCaught(true); else if (paneLayout === "compact" && value !== "summary") setShowCaught(false); };
  const paneVerbs: ListVerb[] = [
    ...(stopped && savedMeetingId && (!stopOutcome || stopOutcome.databaseSaved === true || stopOutcome.saveStatus === "saved") ? [{ id: "open", label: "Open meeting", variant: "primary" as const, enabled: () => true, run: openSaved }] : []),
    { id: "capture", label: active ? "Stop meeting" : "Start meeting", variant: active ? "stop" : "primary", testId: "live-toggle", dispatching: action.busy, enabled: () => !action.busy, run: () => void perform(active ? "/api/meeting/stop" : "/api/meeting/start") },
    ...(active ? [
      { id: "moment", label: "Name this moment", testId: "live-bookmark", enabled: () => true, run: () => { action.setMessage(""); setView("transcript"); setBookmarking(true); setMetaOpen(false); setProjectOpen(false); setInspectorOpen(true); } },
      { id: "details", label: "Edit details", enabled: () => true, run: () => { action.setMessage(""); setView("transcript"); setMetaOpen(true); setBookmarking(false); setProjectOpen(false); setInspectorOpen(true); } },
    ] : []),
    ...(meetingKey && (active || stopped) ? [{ id: "project", label: "Add to project", enabled: () => true, run: () => { setView("transcript"); setProjectTicket(ticket => ticket + 1); setProjectOpen(true); setMetaOpen(false); setBookmarking(false); setInspectorOpen(true); } }] : []),
    { id: "settings", label: "Settings", toolbar: false, testId: "live-settings", enabled: () => true, run: () => openSurfaceOr("configure-settings", "/settings", "meetings") },
  ];
  const summaryStatus = state.intel_status && typeof state.intel_status === "object" ? state.intel_status as Record<string, unknown> : {};
  const summaryJob = state.intel_job && typeof state.intel_job === "object" ? state.intel_job as Record<string, unknown> : {};
  const summaryStart = summaryStatus.requested_at || summaryJob.started_at || summaryJob.requested_at;
  const summaryEnd = summaryStatus.completed_at || summaryJob.completed_at;
  const summaryWorking = intelState === "running" || intelState === "queued";
  return (
    <>
      <PaneViews onLayoutChange={setPaneLayout} inspectorShown={hasInspector} label="Meeting view" value={view} onChange={changeView} tabs={[{ id: "transcript", label: "Transcript" }, { id: "caught", label: "Caught so far", inspector: true }, ...(stopped ? [{ id: "summary", label: "Summary" }] : [])]}>
      <ListPane
        deck={hasInspector}
        open={inspectorOpen}
        hostBack={hostBack}
        listShare={.65}
        onBack={closeInspector}
        label="Meeting inspector"
        list={
          <>
            <VerbToolbar label="Live meeting" testId="live-toolbar" verbs={paneVerbs} trailing={active ? microphone : undefined} trailingVerbs={active ? [{id:"microphone",label:"Microphone",enabled:()=>true,run:()=>{},items:[{id:"current",label:micDevice,enabled:()=>false,run:()=>{}},{id:"settings",label:"Settings…",enabled:()=>true,run:()=>openSurfaceOr("configure-settings", "/settings", "meetings")}]}] : []} />
            <ShowMe app="surface-live" />
            <PreferencePane label="Meeting transcript" testId="live-room">
              {stopped ? (
                <StepTrack
                  label="Meeting work"
                  selected={stage}
                  onSelect={(id) => {
                    setStage(id);
                    changeView(id === "proposals" ? "caught" : id === "summary" ? "summary" : "transcript");
                  }}
                  current={intelState === "running" || intelState === "queued" || intelState === "error" ? "summary" : stage}
                  steps={[
                    {
                      id: "recorded",
                      name: "Recorded",
                      state: "done",
                    },
                    {
                      id: "transcript",
                      name: "Transcript",
                      state: segments.length ? "done" : audioOnly ? "parked" : "planned",
                    },
                    {
                      id: "summary",
                      name: "Summary",
                      state:
                        intelState === "error"
                          ? "failed"
                          : intelState === "running" || intelState === "queued"
                            ? "working"
                            : intelResult?.summary
                              ? "done"
                              : "planned",
                    },
                    {
                      id: "proposals",
                      name: "Proposals",
                      state: caught.length ? "waiting" : "planned",
                    },
                  ]}
                />
              ) : null}
              {view === "caught" ? inspector : stopped && view === "summary" ? (
                <InspectorBody fit="rows">
                  <PaneNotice><PaneActions data-testid="live-summary-progress">
                    <Meter total={1} current={summaryWorking ? 0 : intelResult?.summary ? 1 : 0} state={summaryWorking ? "working" : intelState === "error" ? "failed" : intelResult?.summary ? "done" : "planned"} label={summaryWorking ? "Summary running" : intelState === "error" ? "Summary failed" : intelResult?.summary ? "Summary done" : "No summary"} />
                    {summaryStart ? <><span>Elapsed</span><Elapsed start={String(summaryStart)} end={summaryEnd ? String(summaryEnd) : undefined} running={summaryWorking} /></> : state.ended_at ? <><span>Since Stop</span><Elapsed start={String(state.ended_at)} end={!summaryWorking && summaryEnd ? String(summaryEnd) : undefined} running={summaryWorking} /></> : null}
                  </PaneActions></PaneNotice>
                  <InspectorFacts header={false} name="Summary facts" rows={[{ label: "Engine", value: engineName || "Not set" }]} />
                  <PreferenceWell><PaneNotice><div data-feedback-redact="true"><ReadingDocument data-testid="live-summary">{String(intelResult?.summary || (summaryWorking ? "Summary running" : intelState === "error" ? summaryFailureReason(state) : "No summary"))}</ReadingDocument></div></PaneNotice></PreferenceWell>
                </InspectorBody>
              ) : active || stopped || segments.length ? (
                <TranscriptWell
                  id={meetingKey || "live"}
                  segments={segments}
                  live={active}
                  mark={(row, index) =>
                    row.is_bookmarked === true || markedMoments.has(index) ||
                    decisions.some(
                      (decision) =>
                        typeof decision.source_timestamp === "number" &&
                        Number(row.start_time) <= decision.source_timestamp &&
                        Number(row.end_time) >= decision.source_timestamp,
                    )
                  }
                  emptyLabel={audioOnly ? NO_TRANSCRIPT_SPEECH : active ? "Listening for speech" : "No transcript"}
                />
              ) : (
                <LiveReady
                  microphone={microphone}
                  settings={settings.data}
                  hub={settingsHub.data}
                  speech={speech}
                  name={readyName}
                  onName={setReadyName}
                  mic={mic}
                  checkingMic={checkingMic}
                  onCheckMic={() => void checkMic()}
                />
              )}
            </PreferencePane>
          </>
        }
      >
        {hasInspector ? inspector : null}
      </ListPane>
      </PaneViews>
      {stopped && intelState === "error" ? <ActionNotice tone="danger" action={{ label: "Try again", onClick: () => void retrySummary(), busy: summary.runningId === meetingKey }}><span data-feedback-redact="true">{summary.receipt?.tone === "danger" ? summary.receipt.title || summary.receipt.text : summaryFailureReason(state)}</span></ActionNotice> : null}
      {savedReadError ? <ActionNotice tone="danger" action={{ label: "Retry", onClick: () => void readSaved() }}>{savedReadError}</ActionNotice> : null}
      {action.message && !metaOpen && !bookmarking ? (
        <ActionNotice
          tone="danger"
          action={{
            label: "Retry",
            onClick: () => void perform(active ? "/api/meeting/stop" : "/api/meeting/start"),
          }}
        >
          {active ? "Meeting did not stop" : "Meeting did not start"}
        </ActionNotice>
      ) : null}
      {captureAlert ? (
        <ActionNotice
          tone="danger"
          action={{
            label: "Retry",
            onClick: () => void retryCapture(),
          }}
        >
          Capture needs attention
        </ActionNotice>
      ) : null}
      {stopOutcome && stopOutcome.captureStopped !== false && (stopOutcome.saveStatus !== "saved" || stopOutcome.deviceCleanupError) ? (
        <ActionNotice
          tone={stopOutcome.saveStatus === "saved" ? "info" : "warn"}
          keeps={stopOutcome.saveStatus !== "saved" ? <InspectorFacts header={false} name="Kept after Stop" rows={[{ label: "Transcript", value: stopOutcome.jsonSaved ? `File kept to ${transcriptTo}` : `Saved to ${Math.floor(Number(state.capture_checkpoint_seconds || 0) / 60)}:${String(Math.floor(Number(state.capture_checkpoint_seconds || 0) % 60)).padStart(2, "0")}` }, { label: "Meeting record", value: stopOutcome.databaseSaved ? "Saved" : "Not saved" }, { label: "Audio", value: "Not reported" }]} /> : undefined}
          action={
            stopOutcome.recoveryAvailable
              ? {
                  label: "Retry recovery",
                  onClick: () => void recoverCapture(),
                }
              : undefined
          }
        >
          <span
            title={
              [stopOutcome.saveError, stopOutcome.deviceCleanupError].filter(Boolean).join(" · ") || undefined
            }
          >
            {meetingStopReceiptLabel(stopOutcome)}
          </span>
        </ActionNotice>
      ) : null}
      <StatusBar transient={bookmarkReceipt ? {id:bookmarkReceipt.seq,item:{text:<span title={bookmarkReceipt.text} data-feedback-redact="true">{bookmarkReceipt.project ? "Added to project" : bookmarkReceipt.text}</span>,priority:90}} : undefined} parts={statusItems} trailing={active ? <LiveLevel level={level.level} label="Meeting level" /> : undefined} data-testid="live-statusbar" />
    </>
  );
}
