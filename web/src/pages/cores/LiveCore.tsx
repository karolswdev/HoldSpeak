// HS-95-06 — the live meeting's core: record, watch the transcript
// arrive, keep the result — hosted anywhere (see ActivityCore's rules).
// HS-98-04 — re-crafted native: the transcript is the primary pane, the
// rail collapses with the window, the meeting-details modal became an
// inline block, and device facts are honest. Wire calls unchanged.
import { useEffect, useMemo, useState } from "react";
import { openPrimitive } from "../../desk/shell";
import type { CoreProps } from "./ActivityCore";
import {
  Button,
  Field,
  InlineMessage,
  Select,
  StatusPill,
  TextArea,
  TextInput,
} from "../../components/signal/Signal";
import { apiFetch, readableError, type JsonRecord } from "../../lib/api";
import { useRuntimeBus } from "../../runtime/RuntimeBus";
import { asRows, rowId, useResource } from "../pageSupport";
import {
  MetricStrip,
  SurfaceCode,
  SurfaceColumns,
  SurfaceFacts,
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceState,
  SurfaceVerbs,
} from "../../desk/surface/Surface";
import { presentValue } from "../../desk/surface/format";

type Segment = Record<string, unknown>;

export function LiveCore({ hero }: CoreProps) {
  const initial = useResource<JsonRecord>("/api/state", {});
  const runtimeStatus = useResource<JsonRecord>("/api/runtime/status", {});
  const intentControl = useResource<JsonRecord>("/api/intents/control", {});
  const pluginJobs = useResource<JsonRecord>("/api/plugin-jobs/summary", {});
  const devices = useResource<JsonRecord>("/api/devices/health", {});
  const { state: connection, subscribe } = useRuntimeBus();
  const [state, setState] = useState<JsonRecord>({});
  const [segments, setSegments] = useState<Segment[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [bookmark, setBookmark] = useState("");
  const [metaOpen, setMetaOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [tags, setTags] = useState("");
  const [previewText, setPreviewText] = useState("");
  const [previewResult, setPreviewResult] = useState<JsonRecord | null>(null);
  const [retainedMeetingId, setRetainedMeetingId] = useState("");

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
              ? (frame.data as JsonRecord)
              : {}),
          }));
      }),
    [subscribe],
  );

  const active = Boolean(
    state.active ?? state.meeting_active ?? state.status === "recording",
  );
  const duration = String(
    state.formatted_duration ??
      (state.duration as JsonRecord | undefined)?.formatted ??
      state.duration ??
      "00:00",
  );
  const action = async (path: string, json: unknown = {}) => {
    setBusy(true);
    setMessage("");
    try {
      const value = await apiFetch<JsonRecord>(path, { method: "POST", json });
      if (path.endsWith("start")) {
        setRetainedMeetingId("");
        setState((current) => ({
          ...current,
          ...((value.meeting as JsonRecord) ?? {}),
          active: true,
        }));
      }
      if (path.endsWith("stop")) {
        const meetingId = String(state.id ?? state.meeting_id ?? "");
        if (meetingId) setRetainedMeetingId(meetingId);
        setState((current) => ({ ...current, active: false }));
      }
      return value;
    } catch (error) {
      setMessage(readableError(error));
      return null;
    } finally {
      setBusy(false);
    }
  };
  const saveMetadata = async () => {
    setBusy(true);
    try {
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
    } catch (error) {
      setMessage(readableError(error));
    } finally {
      setBusy(false);
    }
  };
  const previewRoute = async () => {
    setBusy(true);
    try {
      setPreviewResult(
        await apiFetch<JsonRecord>("/api/intents/preview", {
          method: "POST",
          json: { text: previewText },
        }),
      );
    } catch (error) {
      setMessage(readableError(error));
    } finally {
      setBusy(false);
    }
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
      loading={busy}
      onClick={() =>
        void action(active ? "/api/meeting/stop" : "/api/meeting/start")
      }
    >
      {active ? "Stop meeting" : "Start meeting"}
    </Button>
  );
  const intelState = String(
    (state.intel_status as JsonRecord | undefined)?.state ??
      state.intel_status ??
      "idle",
  );
  return (
    <>
      {hero ? (
        hero(verbs)
      ) : (
        <SurfaceVerbs
          status={
            presentValue(state.title) ||
            (active ? "Recording" : "Ready to record")
          }
        >
          {verbs}
        </SurfaceVerbs>
      )}
      {message ? <InlineMessage tone="error">{message}</InlineMessage> : null}
      {retainedMeetingId ? (
        <InlineMessage tone="success">
          Meeting saved.{" "}
          <button
            type="button"
            className="btn-link"
            onClick={() => openPrimitive(`meeting:${retainedMeetingId}`)}
          >
            Return to saved Meeting
          </button>
        </InlineMessage>
      ) : null}
      <MetricStrip
        items={[
          { label: "Connection", value: connection },
          { label: "Duration", value: duration },
          { label: "Segments", value: segments.length },
          { label: "Room", value: active ? "recording" : "idle" },
        ]}
      />
      <SurfaceColumns
        main={
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
              <div className="surface-preview">
                <span className="surface-preview-label">Meeting details</span>
                <Field label="Title">
                  {({ id }) => (
                    <TextInput
                      id={id}
                      value={title}
                      onChange={(event) => setTitle(event.target.value)}
                    />
                  )}
                </Field>
                <Field label="Tags" description="Comma-separated.">
                  {({ id, describedBy }) => (
                    <TextInput
                      id={id}
                      aria-describedby={describedBy}
                      value={tags}
                      onChange={(event) => setTags(event.target.value)}
                    />
                  )}
                </Field>
                <div className="surface-actions">
                  <Button
                    variant="primary"
                    dense
                    loading={busy}
                    onClick={saveMetadata}
                  >
                    Save details
                  </Button>
                  <Button
                    dense
                    variant="ghost"
                    onClick={() => setMetaOpen(false)}
                  >
                    Close
                  </Button>
                </div>
              </div>
            ) : null}
            {transcript.length ? (
              <ol className="transcript-list">
                {transcript.map((segment) => (
                  <li key={String(segment.key)}>
                    <time>
                      {String(segment.timestamp ?? segment.start ?? "")}
                    </time>
                    <p>{String(segment.text ?? segment.transcript ?? "")}</p>
                  </li>
                ))}
              </ol>
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
        }
        side={
          <>
            <SurfaceSection label="Bookmark">
              <Field label="Optional label">
                {({ id }) => (
                  <TextInput
                    id={id}
                    value={bookmark}
                    onChange={(event) => setBookmark(event.target.value)}
                    placeholder="Decision, follow-up…"
                  />
                )}
              </Field>
              <div className="surface-actions">
                <Button
                  dense
                  disabled={!active}
                  onClick={async () => {
                    if (await action("/api/bookmark", { label: bookmark }))
                      setBookmark("");
                  }}
                >
                  Add bookmark
                </Button>
              </div>
            </SurfaceSection>
            <SurfaceSection label="Intelligence">
              <div className="surface-actions">
                <StatusPill tone={intelState === "error" ? "error" : "neutral"}>
                  {intelState}
                </StatusPill>
                <small>
                  {presentValue(
                    (runtimeStatus.data.intel_egress as JsonRecord | undefined)
                      ?.label ??
                      (typeof runtimeStatus.data.intel_egress === "string"
                        ? runtimeStatus.data.intel_egress
                        : ""),
                  ) || "This device"}
                </small>
              </div>
            </SurfaceSection>
          </>
        }
      />
      <SurfaceColumns
        main={
          <SurfaceSection label="Intent routing">
            <Field label="Intent routing preset">
              {({ id }) => (
                <Select
                  id={id}
                  value={String(intentControl.data.profile ?? "auto")}
                  onChange={(event) =>
                    void apiFetch("/api/intents/profile", {
                      method: "PUT",
                      json: { profile: event.target.value },
                    }).then(() => intentControl.reload())
                  }
                >
                  <option value="auto">Automatic</option>
                  <option value="off">Off</option>
                  <option value="balanced">Balanced</option>
                  <option value="aggressive">Aggressive</option>
                </Select>
              )}
            </Field>
            <Field
              label="Preview route"
              description="Tests routing without changing the live meeting."
            >
              {({ id, describedBy }) => (
                <TextArea
                  id={id}
                  aria-describedby={describedBy}
                  value={previewText}
                  onChange={(event) => setPreviewText(event.target.value)}
                />
              )}
            </Field>
            <div className="surface-actions">
              <Button
                dense
                loading={busy}
                disabled={!previewText.trim()}
                onClick={previewRoute}
              >
                Preview route
              </Button>
            </div>
            {previewResult ? (
              <SurfaceCode>
                {JSON.stringify(previewResult, null, 2)}
              </SurfaceCode>
            ) : null}
          </SurfaceSection>
        }
        side={
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
        }
      />
      <SurfaceSection label="Devices">
        <SurfaceState
          loading={devices.loading}
          error={devices.error}
          empty={!asRows(devices.data, ["devices", "items"]).length}
          emptyLabel="No attached audio devices"
          emptyGlyph="🎙"
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
                      <StatusPill tone={device.stale ? "warning" : "success"}>
                        {device.stale ? "stale" : "live"}
                      </StatusPill>
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
}
