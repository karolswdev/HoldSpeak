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
import { useEffect, useMemo, useRef, useState } from "react";
import { openPrimitive } from "../../desk/shell";
import { useDesk } from "../../desk/store";
import type {
  CoreProps,
  MeetingStateResponse,
  RuntimeStatusResponse,
  IntentControlResponse,
  PluginJobsSummaryResponse,
  DevicesHealthResponse,
} from "./core-types";
import { Button } from "../../components/signal/Signal";
import { apiFetch } from "../../lib/api";
import { useRuntimeBus } from "../../runtime/RuntimeBus";
import { asRows, rowId, useResource } from "../pageSupport";
import {
  SurfaceCode,
  SurfaceFacts,
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceState,
  SurfaceStream,
  SurfaceStreamEntry,
  SurfaceWell,
} from "../../desk/surface/Surface";
import { useAction } from "./core-hooks";
import {
  CycleGadget,
  EgressChip,
  FoldGadget,
  GadgetGroup,
  GadgetRow,
  LampGadget,
  PadGadget,
  StringGadget,
} from "../../desk/surface/gadgets";
import { SurfaceWings, useWindowWings } from "../../desk/surface/wings";
import { presentValue } from "../../desk/surface/format";
import { useWaitWord } from "../../desk/surface/objects/ListView";
import { DotWord, StatusBar, Steps, ToolGlyph, Toolbar, meetingSteps, type StatusBarItem } from "../../desk/surface/kit";
import { useWindowInterior } from "../../desk/surface/interior";
import { countToken } from "../../desk/surface/count";
import { intelEgressBadge } from "./liveEgress";
import { burstTimer } from "../../desk/burstTimer";
import { onReturnToTask } from "../../desk/returnToTask";
import { SpeechSetup, useSpeechSetup } from "../../desk/firstrun/SpeechSetup";
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
  const intentControl = useResource<IntentControlResponse>("/api/intents/control", {});
  const pluginJobs = useResource<PluginJobsSummaryResponse>("/api/plugin-jobs/summary", {});
  const devices = useResource<DevicesHealthResponse>("/api/devices/health", {});
  const { state: connection, subscribe } = useRuntimeBus();
  /* HS-202-02 (Astra's counsel finding 3) — the Intelligence badge maps
     the hub's real posture, but only what it read ONCE on mount. Set an
     engine in the Concierge and this face kept the old placement until it
     remounted. It rides the same signals the Meetings face does. */
  const reloadRuntimeStatus = runtimeStatus.reload;
  useEffect(() => {
    const burst = burstTimer(() => void reloadRuntimeStatus(), 300);
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
  }, [subscribe, reloadRuntimeStatus]);
  const [state, setState] = useState<Record<string, unknown>>({});
  const [segments, setSegments] = useState<Segment[]>([]);
  const action = useAction();
  const [bookmark, setBookmark] = useState("");
  const [bookmarking, setBookmarking] = useState(false);
  const [metaOpen, setMetaOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [tags, setTags] = useState("");
  const [previewText, setPreviewText] = useState("");
  const [previewResult, setPreviewResult] = useState<Record<string, unknown> | null>(null);
  const [retainedMeetingId, setRetainedMeetingId] = useState("");
  const [stopOutcome, setStopOutcome] = useState<MeetingStopOutcome | null>(null);
  const [doorOpen, setDoorOpen] = useState(false);
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
  const deviceReloadAt = useRef(0);
  useWindowWings(
    <SurfaceWings
      wings={[]}
      active="live"
      onChange={() => {}}
      name="Live meeting"
      door="Configure meeting"
      doorOpen={doorOpen}
      onDoor={() => setDoorOpen((v) => !v)}
    />,
    [doorOpen],
  );

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

  // ── the dials other surfaces moved ─────────────────────────────────
  const setIntentControls = intentControl.setData;
  useEffect(
    () =>
      subscribe("intent_controls_updated", (frame) => {
        if (frame.data && typeof frame.data === "object")
          setIntentControls(frame.data as IntentControlResponse);
      }),
    [subscribe, setIntentControls],
  );
  const reloadPluginJobs = pluginJobs.reload;
  useEffect(
    () => subscribe("plugin_jobs_processed", () => void reloadPluginJobs()),
    [subscribe, reloadPluginJobs],
  );
  // Battery/RSSI frames are chatty; one refetch per 5s is enough to keep
  // the device list honest without hammering the hub.
  const reloadDevices = devices.reload;
  useEffect(
    () =>
      subscribe("device_health", () => {
        const now = Date.now();
        if (now - deviceReloadAt.current < 5000) return;
        deviceReloadAt.current = now;
        void reloadDevices();
      }),
    [subscribe, reloadDevices],
  );

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
  const perform = async (path: string, json: unknown = {}) => {
    await action.run(async () => {
      const value = await apiFetch<Record<string, unknown>>(path, { method: "POST", json });
      if (path.endsWith("start")) {
        setStopOutcome(null);
        const startedId = String((value.meeting as Record<string, unknown> | undefined)?.id ?? "");
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
  const previewRoute = async () => {
    await action.run(async () => {
      setPreviewResult(
        await apiFetch<Record<string, unknown>>("/api/intents/preview", {
          method: "POST",
          json: { text: previewText },
        }),
      );
    });
  };
  const commitBookmark = async () => {
    if (!bookmarking) return;
    setBookmarking(false);
    const label = bookmark;
    setBookmark("");
    await perform("/api/bookmark", { label });
  };
  const transcript = useMemo<Array<Segment & { key: string }>>(
    () =>
      segments.map((segment, index) => ({
        ...segment,
        key: String(segment.id ?? segment.segment_id ?? index),
      })),
    [segments],
  );

  /* Window grammar (2026-10-24): title bar → toolbar → the four steps and
     the transcript → status bar. "editor": edge to edge, the body scrolls. */
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
      {active ? null : <ToolGlyph kind="record" />}
      {active ? "Stop meeting" : "Start meeting"}
    </Button>
  );
  const intelState = String(
    (state.intel_status as Record<string, unknown> | undefined)?.state ??
      state.intel_status ??
      "idle",
  );
  /* HS-202-04 (M6, UX-CANON A.7) — one fact, one place. This row printed
     the running clock that the footer receipt already carries, and the
     segment count that the stream head already counts, so the same two
     facts stood three times on one screen.
     Astra's counsel on #599, finding 2: the row's remaining state word
     still repeated the footer receipt (`ready` beside `READY`). The two
     slots hold DIFFERENT facts and now say so: this row is the LINK to
     the hub (`runtime/RuntimeBus.tsx:14` — connecting/connected/
     reconnecting/offline), the footer receipt is the CAPTURE. The axis is
     named, per the copy contract's `unqualified-state` rule. */
  const link: string = connection || "unknown";
  const linkTone =
    link === "connected" ? ("ok" as const) : link === "offline" ? ("fail" as const) : link === "unknown" ? undefined : ("warn" as const);

  /** HS-202-04 — the queue summary with its zero counts dropped. A
   *  non-count value (a timestamp, a state word) is kept as it is; only a
   *  number that counts nothing is withheld (UX-CANON A.8). */
  const jobFacts = useMemo(() => {
    const wire = (pluginJobs.data ?? {}) as Record<string, unknown>;
    const kept: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(wire)) {
      /* Keep only what `SurfaceFacts` would actually DRAW
         (`desk/surface/Surface.tsx:381-393`: string | number | boolean,
         minus anything that presents as nothing). The idle wire carries
         `next_retry_at: null` (`holdspeak/services/plugin_job_service.py:29`),
         which draws nothing — counted as a fact it left the section
         looking non-empty and the shot showed a header with a lone verb
         under it (M5). */
      if (!["string", "number", "boolean"].includes(typeof value)) continue;
      if (typeof value === "number" && value <= 0) continue;
      if (typeof value === "string" && !value.trim()) continue;
      kept[key] = value;
    }
    return kept;
  }, [pluginJobs.data]);

  const intelSummary = String(intelResult?.summary ?? "");
  const intelTopics = Array.isArray(intelResult?.topics)
    ? (intelResult.topics as unknown[]).map(String).filter(Boolean)
    : [];
  const intelActionCount = Array.isArray(intelResult?.action_items)
    ? (intelResult.action_items as unknown[]).length
    : Number(intelResult?.action_item_count ?? 0);
  const intelFace =
    intelResult ? (
      /* HS-202-04 (F06) — a meeting result is a SUMMARY on every face.
         The registry ruled it already (`docs/product-language.json:23`:
         "The wire calls it meeting intelligence… Every face says
         Summary") and Live was the one face that disobeyed its own
         registry. `Intelligence` stays the name of the durable ledger
         application, never of a meeting's result. */
      <SurfaceSection
        label="Summary"
        actions={<LampGadget on tone="ok" label="READY" />}
      >
        {intelResult ? (
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
            {/* HS-202-04 (UX-CANON A.8; Astra's counsel on #599, finding
                2) — a Summary with nothing to do printed `0 action
                items`. `countToken` withholds the zero, and the line is
                omitted entirely when it would carry no fact. */}
            <SurfaceFacts
              value={[
                countToken(intelActionCount, "action item", "action items"),
                intelResult.final ? "final" : "",
              ]
                .filter(Boolean)
                .join(" · ")}
            />
          </div>
        ) : null}
      </SurfaceSection>
    ) : null;

  const routeFacts = previewResult
    ? (["route", "intent", "confidence"] as const)
        .map((key) => [key, presentValue(previewResult[key])] as const)
        .filter(([, value]) => value !== "")
    : [];
  /* HS-202-02 — the badge states what the hub said. `intel_egress.label`
     was never a key the hub publishes, so this chip printed the species
     default ("⌂ This device") on every desk, under a hardcoded home glyph
     and with no scope (03-interaction-walk.md Appendix B.2). */
  const intelBadge = intelEgressBadge(runtimeStatus.data.intel_egress);
  const intelEgressChip = intelBadge ? (
    <EgressChip
      label={intelBadge.label}
      scope={intelBadge.scope}
      title={
        intelBadge.scope === "local"
          ? "Transcript processing stays on this device."
          : "Transcript text can leave this device."
      }
    />
  ) : null;
  const devicesWait = useWaitWord(devices.loading);
  const configureFace = (
    <div className="live-configure">
      <SurfaceSection label="Intent routing">
        <GadgetGroup>
          <GadgetRow label="Routing">
            <CycleGadget
              label="Intent routing preset"
              value={String(intentControl.data.profile ?? "auto")}
              onChange={(next) =>
                void apiFetch("/api/intents/profile", {
                  method: "PUT",
                  json: { profile: next },
                }).then(() => intentControl.reload())
              }
              options={[
                { value: "auto", label: "Auto" },
                { value: "off", label: "Off" },
                { value: "balanced", label: "Balanced" },
                { value: "aggressive", label: "Aggressive" },
              ]}
            />
          </GadgetRow>
          {/* W1 (2026-10-27): the caption is one quiet sentence, not a
              mono caps token line. */}
          <GadgetRow
            label="Try a phrase"
            fact="Tests the route only, the live meeting does not change"
            wide
          >
            <PadGadget
              label="Preview route"
              value={previewText}
              rows={2}
              onChange={setPreviewText}
            />
          </GadgetRow>
        </GadgetGroup>
        <div className="surface-actions">
          <Button
            dense
            loading={action.busy}
            disabled={!previewText.trim()}
            onClick={previewRoute}
          >
            Preview route
          </Button>
        </div>
        {previewResult ? (
          <>
            {routeFacts.length ? (
              <GadgetGroup>
                {routeFacts.map(([key, value]) => (
                  <GadgetRow key={key} label={key[0].toUpperCase() + key.slice(1)}>
                    <span className="prefs-value">{value}</span>
                  </GadgetRow>
                ))}
              </GadgetGroup>
            ) : null}
            <FoldGadget title="RAW · ROUTE">
              <SurfaceWell head="RAW · ROUTE">
                <SurfaceCode>
                  {JSON.stringify(previewResult, null, 2)}
                </SurfaceCode>
              </SurfaceWell>
            </FoldGadget>
          </>
        ) : null}
      </SurfaceSection>
      {/* HS-202-04 (F06) — the gear door's run-state section names the
          same thing the result section does: the Summary. */}
      <SurfaceSection label="Summary">
        <div className="surface-actions">
          <DotWord tone={intelState === "error" ? "fail" : intelState === "running" ? "info" : "idle"}>
            {intelState === "error" ? "Failed" : intelState === "idle" ? "Nothing running" : intelState[0].toUpperCase() + intelState.slice(1).replace(/_/g, " ")}
          </DotWord>
          {intelEgressChip}
        </div>
      </SurfaceSection>
      <SurfaceSection label="Background work">
        <SurfaceState
          loading={pluginJobs.loading}
          error={pluginJobs.error}
          empty={!Object.keys(jobFacts).length}
          emptyLabel="No jobs waiting"
          emptyGlyph="○"
          onRetry={() => void pluginJobs.reload()}
        >
          {/* HS-202-04 (UX-CANON A.8; Astra's counsel on #599, finding 2)
              — the hub's queue summary is all counts, so an idle desk drew
              SIX counters of zero in this one section
              (`assets/story-04-shots/live-door-summary-393.png`). A count
              of zero says nothing; the section says the true thing. */}
          <SurfaceFacts value={jobFacts} />
          <div className="surface-actions">
            <Button
              dense
              onClick={() =>
                void apiFetch("/api/plugin-jobs/process", {
                  method: "POST",
                  json: {},
                }).then(() => pluginJobs.reload())
              }
            >
              Process pending
            </Button>
          </div>
        </SurfaceState>
      </SurfaceSection>
      <SurfaceSection label="Devices">
        <SurfaceState
          error={devices.error}
          empty={!devices.loading && !asRows(devices.data, ["devices", "items"]).length}
          emptyLabel="No attached audio devices"
          emptyGlyph="◌"
          onRetry={() => void devices.reload()}
        >
          {/* W1: a read that may never answer says how long it has waited,
              then No answer; never a ring that turns forever. */}
          {devicesWait ? (
            <DotWord tone={devicesWait.tone} data-testid="live-devices-wait">{devicesWait.word}</DotWord>
          ) : null}
          <SurfaceRows>
            {asRows(devices.data, ["devices", "items"]).map(
              (device, index) => {
                const battery = presentValue(device.battery_pct);
                const rssi = presentValue(device.rssi_dbm);
                const facts = [
                  battery ? `Battery ${battery}%` : "",
                  rssi ? `Signal ${rssi} dBm` : "",
                ]
                  .filter(Boolean)
                  .join(" · ");
                return (
                  <SurfaceRow
                    key={rowId(device, index)}
                    title={String(device.name ?? device.id ?? "Device")}
                    detail={facts || undefined}
                    meta={
                      <DotWord tone={device.stale ? "warn" : "ok"}>
                        {device.stale ? "Stale" : "Live"}
                      </DotWord>
                    }
                  />
                );
              },
            )}
          </SurfaceRows>
        </SurfaceState>
      </SurfaceSection>
    </div>
  );

  /* The status bar: the capture state, audio only, speech, and the link to
     the hub, each a dot and a word (UX-CANON A.9 as amended 2026-10-25: no
     egress chip here; the configure face keeps it, where the choice is made).
     HS-202-04 (F21, M6): the clock stands once, here; the stream head owns
     the segment count. The link and the capture are different facts. */
  const meetingTitle = presentValue(state.title);
  const statusItems: StatusBarItem[] = [
    active && meetingTitle ? { key: "title", text: meetingTitle } : null,
    // W1-TRUTH (atlas 2026-10-27): never "Ready" next to "Speech not set
    // up". Before a meeting with no speech model the one state is the
    // warning (its one verb, Set up speech, is in the toolbar).
    active
      ? { key: "capture", lamp: "fail" as const, text: "Recording", value: duration, testId: "live-capture-state" }
      : speech.notSetUp
        ? { key: "capture", lamp: "warn" as const, text: "Speech not set up", testId: "live-capture-state" }
        : { key: "capture", lamp: "ok" as const, text: "Ready", testId: "live-capture-state" },
    active && audioOnly ? { key: "audio", text: "Audio only" } : null,
    { key: "link", lamp: linkTone, text: `Link ${link}`, testId: "live-link-state" },
  ].filter(Boolean) as StatusBarItem[];

  return (
    <>
      {hero ? (
        hero(verbs)
      ) : (
        <Toolbar label="Live meeting" data-testid="live-toolbar">
          {verbs}
          {active ? (
            <Button dense variant="secondary" onClick={() => setMetaOpen((open) => !open)}>
              <ToolGlyph kind="edit" />
              Edit details
            </Button>
          ) : null}
          <SpeechSetup setup={speech} primary={false} toolbar testId="live-speech-setup" />
        </Toolbar>
      )}
      <div className="live-room" data-testid="live-room">
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
      {doorOpen ? (
        configureFace
      ) : (
        <>
          {/* PHILO-17 (the Today language): the meeting's place in its four
              steps, and a REC lamp that is dark at rest and breathes red
              while it records (colour only; nothing moves). */}
          <div className="live-deck" data-active={active || undefined} data-testid="live-deck">
            {active ? <DotWord tone="fail" className="live-rec-word" data-testid="live-rec">Rec</DotWord> : null}
            {/* W1-TRUTH: Today's stepper, the same four steps (Prep,
                Record, Summary, Send follow-up); Live is at Record. */}
            <Steps label="Meeting steps" data-testid="live-steps" steps={meetingSteps(1)} />
          </div>
          {intelFace}
          <SurfaceSection label="Transcript" className="live-transcript">
            {metaOpen ? (
              <GadgetGroup label="Meeting details">
                <GadgetRow label="TITLE">
                  <StringGadget
                    label="Title"
                    value={title}
                    onChange={setTitle}
                  />
                </GadgetRow>
                <GadgetRow label="TAGS" fact="COMMA SEPARATED">
                  <StringGadget label="Tags" value={tags} onChange={setTags} />
                </GadgetRow>
                <div className="surface-actions">
                  <Button
                    variant="primary"
                    dense
                    loading={action.busy}
                    onClick={saveMetadata}
                  >
                    Save
                  </Button>
                  <Button
                    dense
                    variant="ghost"
                    onClick={() => setMetaOpen(false)}
                  >
                    Close
                  </Button>
                </div>
              </GadgetGroup>
            ) : null}
            {transcript.length ? (
              <SurfaceStream
                count={segments.length}
                countLabel={segments.length === 1 ? "segment" : "segments"}
                controls={
                  active ? (
                    bookmarking ? (
                      <span
                        className="live-bookmark-composer"
                        onBlur={(event) => {
                          if (
                            !event.currentTarget.contains(
                              event.relatedTarget as Node | null,
                            )
                          )
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
                      <Button dense onClick={() => setBookmarking(true)}>
                        + Bookmark
                      </Button>
                    )
                  ) : undefined
                }
              >
                <ul className="surface-stream-entries">
                  {transcript.map((segment) => (
                    <SurfaceStreamEntry
                      key={String(segment.key)}
                      when={String(segment.timestamp ?? segment.start ?? "")}
                    >
                      {String(segment.text ?? segment.transcript ?? "")}
                    </SurfaceStreamEntry>
                  ))}
                </ul>
              </SurfaceStream>
            ) : (
              <p className="live-empty" role="status" data-testid="live-transcript-empty">
                {active
                  ? audioOnly ? NO_TRANSCRIPT_SPEECH : "Listening for speech"
                  : "Start a meeting to begin"}
              </p>
            )}
          </SurfaceSection>
        </>
      )}
      </div>
      <StatusBar items={statusItems} data-testid="live-statusbar" />
    </>
  );
}
