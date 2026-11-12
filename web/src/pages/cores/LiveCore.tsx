import { useCallback, useEffect, useRef, useState } from "react";
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
import { useAction } from "./core-hooks";
import { frameNames } from "../../desk/components/window/dockState";
import { StringGadget } from "../../desk/surface/gadgets";
import { presentValue } from "../../desk/surface/format";
import { StatusBar, ToolGlyph, Toolbar, ToolbarFold, type StatusBarItem } from "../../desk/surface/kit";
import { useWindowInterior } from "../../desk/surface/interior";

import { LiveReady } from "./LiveReady";
import { LiveListening, type MicCheck, type TranscriptPass } from "./LiveLevel";

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
  TranscriptWell,
  ListPane,
  ListView,
  ReadingDocument,
  PaneInspector,
  InspectorBody,
  InspectorFacts,
  InspectorForm,
  InspectorFigures,
  ActionNotice,
  CycleGadget,
  PaneActions,
  StepTrack,
} from "../../desk/surface";
import { plainFailure } from "../../desk/surface/plainFailure";
import { useOnDeskChanged } from "../../desk/useDeskChangedRefresh";
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
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [caughtId, setCaughtId] = useState<string | null>(null);
  const [stage, setStage] = useState("transcript");
  const [title, setTitle] = useState("");
  const [tags, setTags] = useState("");
  const drafts = useRef({ title, tags, bookmark });
  drafts.current = { title, tags, bookmark };
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
    [subscribe],
  );

  useEffect(
    () =>
      subscribe("intel_complete", (frame) => {
        intelArrived.current = true;
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
        if (raw !== "" && Number.isFinite(secs))
          setSegments((current) => {
            const index = current.reduce((found, row, at) => (Number(row.start_time) <= secs ? at : found), -1);
            return index < 0
              ? current
              : current.map((row, at) => (at === index ? { ...row, is_bookmarked: true } : row));
          });
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
  const active = !captureStopped && Boolean(
    (meetingId && state.active !== false && state.meeting_active !== false) ||
      (state.active ?? state.meeting_active ?? state.status === "recording"),
  );
  // PHILO-17 speech: the live `duration` frame (a "MM:SS" string, one a
  // second) leads. `formatted_duration` arrives once with meeting_started /
  // meeting_updated and stood in front of the live frame, so REC froze at
  // 00:01 while the dock counter ran.
  const meetingKey = String(meetingId || state.id || state.meeting_id || "");
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
        setState((current) => ({ ...current, active: false }));
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
      if (drafts.current.title === title && drafts.current.tags === tags) setMetaOpen(false);
    });
  };
  const commitBookmark = async () => {
    if (!bookmarking) return;
    const label = bookmark;
    await action.run(async () => {
      await apiFetch("/api/bookmark", { method: "POST", json: { label } });
      if (drafts.current.bookmark === label) { setBookmark(""); setBookmarking(false); }
    });
  };

  // The frame, fitted verb row and bounded transcript/inspector own their seats.
  useWindowInterior("list");
  const verbs = (
    <Button
      variant={active ? "danger" : "primary"}
      dense
      loading={action.busy}
      data-testid="live-toggle"
      onClick={() =>
        void perform(active ? "/api/meeting/stop" : "/api/meeting/start")
      }
    >
      {!active ? <ToolGlyph kind="record" /> : null}
      {active ? "Stop meeting" : "Start meeting"}
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
  const statusItems: StatusBarItem[] = [
    action.message ? { key: "write", lamp: "fail" as const, text: "Failed", priority: 100 } : null,
    // W1-TRUTH (atlas 2026-10-27): never "Ready" next to "Speech not set
    // up". Before a meeting with no speech model the one state is the
    // warning (its one verb, Set up speech, is in the toolbar).
    active
      ? { key: "capture", lamp: "fail" as const, text: "Recording", testId: "live-capture-state" }
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
    summaryItem,
    /* W6-A (atlas pass 3, defect 17): this is the page's own link to the
       hub, not a device of his. Connected is the normal case and says
       nothing; a lost link names what is lost, at both widths. */
    link === "connected" || link === "unknown"
      ? null
      : { key: "link", lamp: linkTone, text: link === "offline" ? "Hub not reached" : "Connecting to the hub", testId: "live-link-state" },
  ].filter(Boolean) as StatusBarItem[];

  /* Live slice 3: the transcript's foot. The saved reach is the newest
     pass of THIS meeting, else the checkpoint /api/state carries. */
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
  useWindowTitle(active || stopped ? name : null, [active, stopped, name]);
  useWindowMast({
    line:
      action.message ||
      captureAlert ||
      (!active && !stopped && (mic?.state === "failed" || mic?.state === "not_allowed"))
        ? "Failed"
        : active
          ? "Recording"
          : stopped
            ? intelState === "running"
              ? "Stopped · summary running"
              : "Stopped"
            : speech.notSetUp
              ? "Speech not set up"
              : "Ready",
    figures: active || stopped ? [{ value: duration, label: active ? "recording" : "length" }] : [],
  });
  const tasks = caught.filter((row) => row.kind === "Owed").length;
  const microphone = (
    <CycleGadget
      roster
      label="Microphone"
      value={micDevice}
      options={[{ value: micDevice }, { value: "settings", label: "Change in Settings…" }]}
      onChange={(value) => {
        if (value === "settings") openSurfaceOr("configure-settings", "/settings", "meetings");
      }}
    />
  );
  const facts = (
    <InspectorFacts
      header={false}
      name="Meeting facts"
      data-feedback-redact="true"
      rows={[
        { label: "Microphone", value: micDevice },
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
  const inspector = metaOpen ? (
    <PaneInspector label="Meeting details" testId="live-details">
      <InspectorForm
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
        notice={action.message ? <ActionNotice tone="danger">{action.message}</ActionNotice> : undefined}
        completion={{
          cancel: () => {
            setMetaOpen(false);
            action.setMessage("");
          },
          primary: {
            label: "Save",
            busy: action.busy,
            run: () => void saveMetadata(),
          },
        }}
      />
    </PaneInspector>
  ) : bookmarking ? (
    <PaneInspector label="Name this moment">
      <InspectorForm
        rows={[
          {
            label: "Name this moment",
            control: (
              <StringGadget
                autoFocus
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
        notice={action.message ? <ActionNotice tone="danger">{action.message}</ActionNotice> : undefined}
        completion={{
          cancel: () => {
            setBookmark("");
            setBookmarking(false);
            action.setMessage("");
          },
          primary: {
            label: "Bookmark",
            busy: action.busy,
            run: () => void commitBookmark(),
          },
        }}
      />
    </PaneInspector>
  ) : (
    <PaneInspector label={name} testId="live-caught">
      <InspectorBody>
        {caught.length ? <InspectorFigures label="Caught so far" figures={[
          { value: decisions.length || "—", label: decisions.length === 1 ? "decision" : "decisions", tone: "ask" },
          { value: tasks || "—", label: tasks === 1 ? "task" : "tasks" },
        ]} /> : null}
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
            { key: "name", word: "Caught so far" },
            { key: "at", word: "At", track: "52px", priority: 0 },
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
  return (
    <>
      <ListPane
        deck={active || stopped || inspectorOpen || caught.length > 0}
        open={inspectorOpen}
        onBack={() => setInspectorOpen(false)}
        label="Meeting inspector"
        list={
          <>
            <Toolbar label="Live meeting" data-testid="live-toolbar">
              {stopped && savedMeetingId && (!stopOutcome || stopOutcome.databaseSaved === true || stopOutcome.saveStatus === "saved") ? (
                <Button dense variant="primary" onClick={openSaved}>
                  Open meeting
                </Button>
              ) : null}
              {verbs}
              <ToolbarFold
                label="Actions"
                data-testid="live-actions"
                verbs={[
                  ...(active
                    ? [
                        {
                          key: "moment",
                          label: "Name this moment",
                          testId: "live-bookmark",
                          onSelect: () => {
                            action.setMessage("");
                            setBookmarking(true);
                            setMetaOpen(false);
                            setInspectorOpen(true);
                          },
                        },
                        {
                          key: "details",
                          label: "Edit details",
                          onSelect: () => {
                            action.setMessage("");
                            setMetaOpen(true);
                            setBookmarking(false);
                            setInspectorOpen(true);
                          },
                        },
                      ]
                    : []),
                  {
                    key: "caught",
                    label: "Caught so far",
                    onSelect: () => {
                      setMetaOpen(false);
                      setBookmarking(false);
                      setInspectorOpen(true);
                    },
                  },
                  {
                    key: "settings",
                    label: "Settings",
                    testId: "live-settings",
                    onSelect: () => openSurfaceOr("configure-settings", "/settings", "meetings"),
                  },
                ]}
              />
              <ShowMe app="surface-live" />
            </Toolbar>
            <PreferencePane label="Meeting transcript" testId="live-room">
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
              {bookmarkReceipt ? <ActionNotice tone="info">{bookmarkReceipt.text}</ActionNotice> : null}
              {stopOutcome && stopOutcome.captureStopped !== false ? (
                <ActionNotice
                  tone={stopOutcome.saveStatus === "saved" ? "info" : "warn"}
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
              {stopped ? (
                <StepTrack
                  label="Meeting work"
                  selected={stage}
                  onSelect={(id) => {
                    setStage(id);
                    if (id === "proposals") setInspectorOpen(true);
                  }}
                  current={intelState === "running" || intelState === "queued" ? "summary" : null}
                  steps={[
                    {
                      id: "recorded",
                      name: "Recorded",
                      state: stopOutcome?.saveStatus === "saved" ? "done" : "waiting",
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
              {stopped && stage === "summary" ? (
                <PreferenceWell><ReadingDocument data-testid="live-summary">
                  {String(intelResult?.summary || (intelState === "running" ? "Summary running" : "No summary"))}
                </ReadingDocument></PreferenceWell>
              ) : active || stopped || segments.length ? (
                <TranscriptWell
                  id={meetingKey || "live"}
                  segments={segments}
                  live={active}
                  mark={(row) =>
                    row.is_bookmarked === true ||
                    decisions.some(
                      (decision) =>
                        typeof decision.source_timestamp === "number" &&
                        Number(row.start_time) <= decision.source_timestamp &&
                        Number(row.end_time) >= decision.source_timestamp,
                    )
                  }
                  emptyLabel={audioOnly ? NO_TRANSCRIPT_SPEECH : active ? "Listening for speech" : "No transcript"}
                  footer={active ? <PaneActions>{listening}{microphone}</PaneActions> : undefined}
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
        {active || stopped || inspectorOpen || caught.length ? inspector : null}
      </ListPane>
      <StatusBar items={statusItems} data-testid="live-statusbar" />
    </>
  );
}
