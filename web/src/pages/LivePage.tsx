import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Button,
  Dialog,
  EmptyState,
  Field,
  InlineMessage,
  Panel,
  Select,
  StatusPill,
  TextArea,
  TextInput,
} from "../components/signal/Signal";
import { apiFetch, readableError, type JsonRecord } from "../lib/api";
import { useRuntimeBus } from "../runtime/RuntimeBus";
import {
  PageHero,
  ResourceState,
  asRows,
  rowId,
  useResource,
} from "./pageSupport";

type Segment = Record<string, unknown>;

export default function LivePage() {
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

  return (
    <div className="page-wrap">
      <PageHero
        eyebrow="Meeting room"
        title={String(state.title ?? "Ready to record")}
        actions={
          <Button
            variant={active ? "danger" : "primary"}
            loading={busy}
            onClick={() =>
              void action(active ? "/api/meeting/stop" : "/api/meeting/start")
            }
          >
            {active ? "Stop meeting" : "Start meeting"}
          </Button>
        }
      >
        Record a meeting, review its transcript, and keep the result.
      </PageHero>
      {message ? <InlineMessage tone="error">{message}</InlineMessage> : null}
      {retainedMeetingId ? (
        <InlineMessage tone="success">
          Meeting saved.{" "}
          <Link
            to={`/?open=${encodeURIComponent(`meeting:${retainedMeetingId}`)}`}
          >
            Return to saved Meeting
          </Link>
        </InlineMessage>
      ) : null}
      <div className="metric-grid">
        <div className="metric">
          <strong>
            <StatusPill
              tone={connection === "connected" ? "success" : "warning"}
            >
              {connection}
            </StatusPill>
          </strong>
          <span>Connection</span>
        </div>
        <div className="metric">
          <strong>{duration}</strong>
          <span>Duration</span>
        </div>
        <div className="metric">
          <strong>{segments.length}</strong>
          <span>Segments</span>
        </div>
        <div className="metric">
          <strong>
            <StatusPill tone={active ? "live" : "neutral"}>
              {active ? "recording" : "idle"}
            </StatusPill>
          </strong>
          <span>Room</span>
        </div>
      </div>
      <div className="page-grid">
        <Panel
          className="span-8 live-transcript"
          title="Transcript"
          eyebrow="Live transcript"
          actions={
            active ? (
              <Button dense onClick={() => setMetaOpen(true)}>
                Edit details
              </Button>
            ) : null
          }
        >
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
            <EmptyState
              title={
                active ? "Listening for speech" : "Start a meeting to begin"
              }
            >
              Transcript segments appear here without moving your reading
              position.
            </EmptyState>
          )}
        </Panel>
        <div className="span-4 live-rail">
          <Panel title="Bookmark" eyebrow="Mark the moment">
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
            <Button
              disabled={!active}
              onClick={async () => {
                if (await action("/api/bookmark", { label: bookmark }))
                  setBookmark("");
              }}
            >
              Add bookmark
            </Button>
          </Panel>
          <Panel title="Intelligence" eyebrow="Hub-reported">
            <StatusPill
              tone={
                String(
                  (state.intel_status as JsonRecord | undefined)?.state ??
                    state.intel_status ??
                    "idle",
                ) === "error"
                  ? "error"
                  : "neutral"
              }
            >
              {String(
                (state.intel_status as JsonRecord | undefined)?.state ??
                  state.intel_status ??
                  "idle",
              )}
            </StatusPill>
            <p>
              Processing and egress posture come from the hub; the browser never
              infers them.
            </p>
            <small>
              {String(
                (runtimeStatus.data.intel_egress as JsonRecord | undefined)
                  ?.label ??
                  runtimeStatus.data.intel_egress ??
                  "This device",
              )}
            </small>
          </Panel>
        </div>
        <Panel className="span-8" title="Intent routing" eyebrow="Live control">
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
          <Button
            loading={busy}
            disabled={!previewText.trim()}
            onClick={previewRoute}
          >
            Preview route
          </Button>
          {previewResult ? (
            <pre className="code-block">
              {JSON.stringify(previewResult, null, 2)}
            </pre>
          ) : null}
        </Panel>
        <Panel className="span-4" title="Deferred plugin jobs" eyebrow="Queue">
          <ResourceState
            loading={pluginJobs.loading}
            error={pluginJobs.error}
            onRetry={() => void pluginJobs.reload()}
          >
            <pre className="code-block">
              {JSON.stringify(pluginJobs.data, null, 2)}
            </pre>
            <Button
              onClick={() =>
                void apiFetch("/api/plugin-jobs/process", {
                  method: "POST",
                  json: {},
                }).then(() => pluginJobs.reload())
              }
            >
              Process pending
            </Button>
          </ResourceState>
        </Panel>
        <Panel
          className="span-12"
          title="Devices"
          eyebrow="Attached audio health"
        >
          <ResourceState
            loading={devices.loading}
            error={devices.error}
            empty={!asRows(devices.data, ["devices", "items"]).length}
            onRetry={() => void devices.reload()}
          >
            <ul className="data-list">
              {asRows(devices.data, ["devices", "items"]).map(
                (device, index) => (
                  <li className="data-row" key={rowId(device, index)}>
                    <div>
                      <strong>
                        {String(device.name ?? device.id ?? "Device")}
                      </strong>
                      <small>
                        Battery {String(device.battery_pct ?? "—")}% · RSSI{" "}
                        {String(device.rssi_dbm ?? "—")} dBm
                      </small>
                    </div>
                    <StatusPill tone={device.stale ? "warning" : "success"}>
                      {device.stale ? "stale" : "live"}
                    </StatusPill>
                  </li>
                ),
              )}
            </ul>
          </ResourceState>
        </Panel>
      </div>
      <Dialog
        open={metaOpen}
        title="Meeting details"
        onClose={() => setMetaOpen(false)}
      >
        <div className="dialog-form">
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
          <Button variant="primary" loading={busy} onClick={saveMetadata}>
            Save details
          </Button>
        </div>
      </Dialog>
    </div>
  );
}
