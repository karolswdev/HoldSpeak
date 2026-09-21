import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
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
import { renderHeroSlot } from "./core-layout";
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
import { intelEgressBadge } from "./liveEgress";
import { onReturnToTask } from "../../desk/returnToTask";

type Segment = Record<string, unknown>;

export function LiveCore({ hero }: CoreProps) {
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
    let timer = 0;
    const bump = () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(() => void reloadRuntimeStatus(), 300);
    };
    const offDeskChanged = subscribe("desk_changed", bump);
    const offReturn = onReturnToTask(() => void reloadRuntimeStatus());
    const onFocus = () => void reloadRuntimeStatus();
    window.addEventListener("focus", onFocus);
    return () => {
      window.clearTimeout(timer);
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

  const active = Boolean(
    state.active ?? state.meeting_active ?? state.status === "recording",
  );
  const duration = String(
    state.formatted_duration ??
      (state.duration as Record<string, unknown> | undefined)?.formatted ??
      state.duration ??
      "00:00",
  );
  const perform = async (path: string, json: unknown = {}) => {
    await action.run(async () => {
      const value = await apiFetch<Record<string, unknown>>(path, { method: "POST", json });
      if (path.endsWith("start")) {
        setRetainedMeetingId("");
        setCaptureAlert("");
        setIntelResult(null);
        setState((current) => ({
          ...current,
          ...((value.meeting as Record<string, unknown>) ?? {}),
          active: true,
        }));
      }
      if (path.endsWith("stop")) {
        const meetingId = String(state.id ?? state.meeting_id ?? "");
        if (meetingId) setRetainedMeetingId(meetingId);
        setState((current) => ({ ...current, active: false }));
      }
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

  const verbs = (
    <Button
      variant={active ? "danger" : "primary"}
      dense
      loading={action.busy}
      onClick={() =>
        void perform(active ? "/api/meeting/stop" : "/api/meeting/start")
      }
    >
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
     facts stood three times on one screen. The row keeps the fact nothing
     else on this face states: WHERE the meeting is being heard. */
  const factsLine = `${connection || "This device"} · ${
    active ? "recording" : "ready"
  }`;

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
            <SurfaceFacts
              value={`${intelActionCount} action item${intelActionCount === 1 ? "" : "s"}${
                intelResult.final ? " · final" : ""
              }`}
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
  const configureFace = (
    <>
      <SurfaceSection label="Intent routing">
        <GadgetGroup>
          <GadgetRow label="ROUTING">
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
          <GadgetRow
            label="PREVIEW"
            fact="TESTS ROUTING · NEVER TOUCHES THE LIVE MEETING"
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
                  <GadgetRow key={key} label={key.toUpperCase()}>
                    <span className="gadget-fact">{value.toUpperCase()}</span>
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
          <span
            className="surface-token"
            data-tone={intelState === "error" ? "danger" : undefined}
          >
            {intelState}
          </span>
          {intelEgressChip}
        </div>
      </SurfaceSection>
      <SurfaceSection label="Deferred plugin jobs">
        <SurfaceState
          loading={pluginJobs.loading}
          error={pluginJobs.error}
          onRetry={() => void pluginJobs.reload()}
        >
          <SurfaceFacts value={pluginJobs.data} />
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
          loading={devices.loading}
          error={devices.error}
          empty={!asRows(devices.data, ["devices", "items"]).length}
          emptyLabel="No attached audio devices"
          emptyGlyph="◌"
          onRetry={() => void devices.reload()}
        >
          <SurfaceRows>
            {asRows(devices.data, ["devices", "items"]).map(
              (device, index) => {
                const battery = presentValue(device.battery_pct);
                const rssi = presentValue(device.rssi_dbm);
                const facts = [
                  battery ? `Battery ${battery}%` : "",
                  rssi ? `RSSI ${rssi} dBm` : "",
                ]
                  .filter(Boolean)
                  .join(" · ");
                return (
                  <SurfaceRow
                    key={rowId(device, index)}
                    title={String(device.name ?? device.id ?? "Device")}
                    detail={facts || undefined}
                    meta={
                      <LampGadget
                        label={device.stale ? "STALE" : "LIVE"}
                        on
                        tone={device.stale ? "warn" : "ok"}
                      />
                    }
                  />
                );
              },
            )}
          </SurfaceRows>
        </SurfaceState>
      </SurfaceSection>
    </>
  );

  return (
    <>
      {renderHeroSlot(hero, verbs, presentValue(state.title) || (active ? "Recording" : "Ready to record"))}
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
      {retainedMeetingId ? (
        <p className="surface-receipt-line" data-tone="ok" role="status">
          <svg width="12" height="12" viewBox="0 0 16 16" aria-hidden="true" style={{ flexShrink: 0 }}><path d="M3.5 8.5 6.5 11.5 12.5 4.5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg>{" "}
          Meeting saved{" "}
          <button
            type="button"
            className="btn-link"
            onClick={() => openPrimitive(`meeting:${retainedMeetingId}`)}
          >
            Return to saved Meeting
          </button>
        </p>
      ) : null}
      {doorOpen ? (
        configureFace
      ) : (
        <>
          <SurfaceFacts value={factsLine} />
          {intelFace}
          <SurfaceSection
            label="Transcript"
            actions={
              active ? (
                <Button dense onClick={() => setMetaOpen((open) => !open)}>
                  Edit details
                </Button>
              ) : undefined
            }
          >
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
              <SurfaceState
                empty
                emptyLabel={
                  active ? "Listening for speech" : "Start a meeting to begin"
                }
                emptyGlyph="●"
              />
            )}
          </SurfaceSection>
        </>
      )}
      {/* HS-129-05 — the readiness fact rides the shared receipt slot.
          HS-202-04 (F21, M6) — the receipt carries the clock and nothing
          else: the segment count belongs to the stream head that counts
          them, and `SEG` was an abbreviation no face ever defined (the
          recovery slab spelled it out in HS-201-06). */}
      <SurfaceFooter
        egress={intelEgressChip}
        receipt={
          <span className="surface-footer-receipt-line" role="status">
            {active ? `REC ${duration}` : "READY"}
          </span>
        }
      />
    </>
  );
}
