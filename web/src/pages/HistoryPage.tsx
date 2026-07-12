import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Button,
  Dialog,
  Disclosure,
  EmptyState,
  Field,
  InlineMessage,
  Panel,
  Select,
  StatusPill,
  Tabs,
  TextInput,
  Toolbar,
} from "../components/signal/Signal";
import { apiBlob, apiFetch, readableError, type JsonRecord } from "../lib/api";
import { MeetingConflictRecovery } from "../meetings/MeetingConflictRecovery";
import { MeetingIntelRecovery } from "../meetings/MeetingIntelRecovery";
import {
  ConfirmAction,
  PageHero,
  ResourceState,
  asRows,
  rowId,
  useResource,
} from "./pageSupport";
import {
  decodeWorkroomContext,
  workroomHref,
  workroomSubjectId,
} from "../workrooms/context";

const ARCHIVE_TABS = [
  "meetings",
  "actions",
  "speakers",
  "projects",
  "queues",
].map((id) => ({ id, label: id[0].toUpperCase() + id.slice(1) }));
const DETAIL_TABS = [
  "transcript",
  "artifacts",
  "aftercare",
  "routing",
  "proposals",
].map((id) => ({ id, label: id[0].toUpperCase() + id.slice(1) }));

function displayState(value: unknown): string {
  const state = String(value ?? "").trim();
  const known: Record<string, string> = {
    pending: "Queued",
    complete: "Succeeded",
    capture_failed: "Capture failed",
    import_failed: "Import failed",
    recoverable: "Recovery available",
    recording: "Recording",
    finalized: "Saved",
    error: "Intelligence failed",
    partial: "Intelligence incomplete",
    skipped: "Intelligence skipped",
    queued: "Intelligence queued",
    running: "Intelligence running",
    ready: "Intelligence ready",
  };
  return (
    known[state] ||
    state
      .replace(/_/g, " ")
      .replace(/^./, (character) => character.toUpperCase())
  );
}

function download(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function ImportDialog({
  open,
  onClose,
  onImported,
}: {
  open: boolean;
  onClose(): void;
  onImported(): void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [speaker, setSpeaker] = useState("");
  const [tags, setTags] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const submit = async () => {
    if (!file) return;
    setBusy(true);
    setError("");
    const body = new FormData();
    body.append("file", file);
    if (title.trim()) body.append("title", title.trim());
    if (speaker.trim()) body.append("speaker", speaker.trim());
    if (tags.trim()) body.append("tags", tags.trim());
    body.append("started_at_ms", String(file.lastModified));
    try {
      await apiFetch("/api/meetings/import", { method: "POST", body });
      setFile(null);
      setTitle("");
      setSpeaker("");
      setTags("");
      onImported();
      onClose();
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setBusy(false);
    }
  };
  return (
    <Dialog
      open={open}
      title="Import a recording or transcript"
      onClose={onClose}
    >
      <div className="dialog-form">
        <Field
          label="File"
          description="WAV works directly. Compressed audio needs ffmpeg. VTT, SRT and TXT keep transcript structure."
        >
          {({ id, describedBy }) => (
            <input
              className="hs-control"
              id={id}
              aria-describedby={describedBy}
              type="file"
              accept="audio/*,.wav,.mp3,.m4a,.ogg,.flac,.vtt,.srt,.txt"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
          )}
        </Field>
        <Field label="Title">
          {({ id }) => (
            <TextInput
              id={id}
              value={title}
              onChange={(event) => setTitle(event.target.value)}
            />
          )}
        </Field>
        <Field label="Speaker">
          {({ id }) => (
            <TextInput
              id={id}
              value={speaker}
              onChange={(event) => setSpeaker(event.target.value)}
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
        {error ? <InlineMessage tone="error">{error}</InlineMessage> : null}
        <Button
          variant="primary"
          loading={busy}
          disabled={!file}
          onClick={submit}
        >
          Import to this device
        </Button>
      </div>
    </Dialog>
  );
}

function MeetingDetail({
  meeting,
  onClose,
  onDeleted,
}: {
  meeting: JsonRecord | null;
  onClose(): void;
  onDeleted(): void;
}) {
  const id = String(meeting?.id ?? "");
  const [active, setActive] = useState("transcript");
  const [detail, setDetail] = useState<JsonRecord | null>(meeting);
  const [artifacts, setArtifacts] = useState<JsonRecord>({});
  const [aftercare, setAftercare] = useState<JsonRecord>({});
  const [timeline, setTimeline] = useState<JsonRecord>({});
  const [proposals, setProposals] = useState<JsonRecord>({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  useEffect(() => {
    if (!id) return;
    setDetail(meeting);
    setError("");
    void Promise.all([
      apiFetch<JsonRecord>(`/api/meetings/${encodeURIComponent(id)}`).then(
        setDetail,
      ),
      apiFetch<JsonRecord>(`/api/meetings/${encodeURIComponent(id)}/artifacts`)
        .then(setArtifacts)
        .catch(() => setArtifacts({})),
      apiFetch<JsonRecord>(`/api/meetings/${encodeURIComponent(id)}/aftercare`)
        .then(setAftercare)
        .catch(() => setAftercare({})),
      apiFetch<JsonRecord>(
        `/api/meetings/${encodeURIComponent(id)}/intent-timeline`,
      )
        .then(setTimeline)
        .catch(() => setTimeline({})),
      apiFetch<JsonRecord>(`/api/meetings/${encodeURIComponent(id)}/proposals`)
        .then(setProposals)
        .catch(() => setProposals({})),
    ]).catch((reason) => setError(readableError(reason)));
  }, [id, meeting]);
  const decide = async (
    proposal: JsonRecord,
    decision: "approved" | "rejected",
  ) => {
    setBusy(true);
    try {
      await apiFetch(
        `/api/meetings/${encodeURIComponent(id)}/proposals/${encodeURIComponent(String(proposal.id))}/decision`,
        { method: "POST", json: { decision } },
      );
      setProposals(
        await apiFetch(`/api/meetings/${encodeURIComponent(id)}/proposals`),
      );
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setBusy(false);
    }
  };
  const proposeSlack = async (what: "digest" | "followup") => {
    setBusy(true);
    try {
      await apiFetch(`/api/meetings/${encodeURIComponent(id)}/export/slack`, {
        method: "POST",
        json: { what },
      });
      setProposals(
        await apiFetch(`/api/meetings/${encodeURIComponent(id)}/proposals`),
      );
      setActive("proposals");
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setBusy(false);
    }
  };
  const exportMeeting = async (format: string) => {
    try {
      download(
        await apiBlob(
          `/api/meetings/${encodeURIComponent(id)}/export?format=${format}`,
        ),
        `holdspeak-meeting-${id}.${format === "markdown" ? "md" : format}`,
      );
    } catch (reason) {
      setError(readableError(reason));
    }
  };
  const remove = async () => {
    setBusy(true);
    try {
      await apiFetch(`/api/meetings/${encodeURIComponent(id)}`, {
        method: "DELETE",
      });
      setConfirmDelete(false);
      onDeleted();
      onClose();
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setBusy(false);
    }
  };
  const segments = asRows(detail, ["segments", "transcript"]);
  const artifactRows = asRows(artifacts, ["artifacts", "items"]);
  const actionRows = asRows(aftercare, ["action_items", "actions", "items"]);
  const timelineRows = asRows(timeline, ["timeline", "items"]);
  const proposalRows = asRows(proposals, ["proposals"]);
  return (
    <Dialog
      open={Boolean(meeting)}
      title={String(detail?.title ?? meeting?.title ?? "Meeting detail")}
      onClose={onClose}
    >
      <div className="meeting-detail">
        <Tabs
          label="Meeting detail sections"
          tabs={DETAIL_TABS}
          active={active}
          onChange={setActive}
        />
        {error ? <InlineMessage tone="error">{error}</InlineMessage> : null}
        {detail?.capture_status && detail.capture_status !== "finalized" ? (
          <InlineMessage tone="warning">
            {`Meeting saved · ${String(detail.capture_status)}${detail.capture_failure ? ` · ${String(detail.capture_failure)}` : ""}. The transcript below is the last durable checkpoint, not false completion.`}
          </InlineMessage>
        ) : null}
        <MeetingConflictRecovery
          meetingId={id}
          onResolved={(result) => {
            onDeleted();
            if (result.deleted) {
              onClose();
            } else if (result.meeting) {
              setDetail(result.meeting);
            }
          }}
        />
        <MeetingIntelRecovery
          meetingId={id}
          onChanged={async () => {
            setDetail(
              await apiFetch(`/api/meetings/${encodeURIComponent(id)}`),
            );
            onDeleted();
          }}
        />
        {active === "transcript" ? (
          segments.length ? (
            <ol className="transcript-list">
              {segments.map((row, index) => (
                <li key={rowId(row, index)}>
                  <time>{String(row.timestamp ?? row.start ?? "")}</time>
                  <p>{String(row.text ?? row.transcript ?? "")}</p>
                </li>
              ))}
            </ol>
          ) : (
            <EmptyState title="No transcript">
              This meeting has no persisted transcript segments.
            </EmptyState>
          )
        ) : null}
        {active === "artifacts" ? (
          artifactRows.length ? (
            <div className="data-list">
              {artifactRows.map((row, index) => (
                <Disclosure
                  key={rowId(row, index)}
                  title={String(row.title ?? row.artifact_type ?? "Artifact")}
                >
                  <pre className="code-block">
                    {String(
                      row.body_markdown ??
                        row.content ??
                        JSON.stringify(row, null, 2),
                    )}
                  </pre>
                </Disclosure>
              ))}
            </div>
          ) : (
            <EmptyState title="No artifacts">
              Run meeting intelligence to create routed artifacts.
            </EmptyState>
          )
        ) : null}
        {active === "aftercare" ? (
          <>
            {actionRows.length ? (
              <ul className="data-list">
                {actionRows.map((row, index) => (
                  <li className="data-row" key={rowId(row, index)}>
                    <div>
                      <strong>
                        {String(row.text ?? row.title ?? "Action item")}
                      </strong>
                      <small>{String(row.owner ?? row.status ?? "")}</small>
                    </div>
                    <StatusPill
                      tone={row.status === "done" ? "success" : "warning"}
                    >
                      {row.status === "done"
                        ? "Action item complete"
                        : "Open action item"}
                    </StatusPill>
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState title="No aftercare yet">
                Action items and follow-up material appear after intelligence
                completes.
              </EmptyState>
            )}
            {aftercare.slack_configured ? (
              <div className="button-row">
                <Button
                  loading={busy}
                  onClick={() => void proposeSlack("digest")}
                >
                  Send digest to Slack
                </Button>
                <Button
                  loading={busy}
                  onClick={() => void proposeSlack("followup")}
                >
                  Send follow-up to Slack
                </Button>
                <small>
                  Each creates an exact-message proposed action. Approval sends
                  it to the configured Slack destination.
                </small>
              </div>
            ) : null}
          </>
        ) : null}
        {active === "routing" ? (
          <pre className="code-block">
            {JSON.stringify(timelineRows, null, 2)}
          </pre>
        ) : null}
        {active === "proposals" ? (
          proposalRows.length ? (
            <ul className="data-list">
              {proposalRows.map((row, index) => (
                <li className="data-row" key={rowId(row, index)}>
                  <div>
                    <strong>
                      {String(row.title ?? row.kind ?? "Proposed action")}
                    </strong>
                    <small>
                      {String(row.preview ?? row.body ?? row.status ?? "")}
                    </small>
                  </div>
                  <div className="button-row">
                    <Button
                      dense
                      loading={busy}
                      disabled={row.status !== "proposed"}
                      onClick={() => void decide(row, "approved")}
                    >
                      {String(
                        (row.commitment as JsonRecord | undefined)?.approve ??
                          `Approve for ${String(row.target ?? "executor")}`,
                      )}
                    </Button>
                    <Button
                      dense
                      variant="ghost"
                      disabled={row.status !== "proposed"}
                      onClick={() => void decide(row, "rejected")}
                    >
                      {String(
                        (row.commitment as JsonRecord | undefined)?.reject ??
                          "Reject proposed action",
                      )}
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState title="No proposals">
              Proposed external actions appear here before execution.
            </EmptyState>
          )
        ) : null}
        <div className="button-row">
          <Select
            aria-label="Export format"
            defaultValue="markdown"
            onChange={(event) => void exportMeeting(event.target.value)}
          >
            <option value="markdown">Export…</option>
            <option value="txt">Plain text</option>
            <option value="json">JSON</option>
            <option value="srt">SRT</option>
          </Select>
          <Button variant="ghost" onClick={() => setConfirmDelete(true)}>
            Delete meeting
          </Button>
        </div>
      </div>
      <ConfirmAction
        open={confirmDelete}
        title="Delete this meeting?"
        detail="Transcript, artifacts and aftercare for this meeting will be removed."
        busy={busy}
        onConfirm={remove}
        onClose={() => setConfirmDelete(false)}
      />
    </Dialog>
  );
}

export default function HistoryPage() {
  const workroom = decodeWorkroomContext(window.location.search);
  const requestedMeetingId =
    workroomSubjectId(workroom, "meeting") ??
    new URLSearchParams(window.location.search).get("meeting");
  const [active, setActive] = useState("meetings");
  const [query, setQuery] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [speaker, setSpeaker] = useState("");
  const [tag, setTag] = useState("");
  const [openActions, setOpenActions] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [selected, setSelected] = useState<JsonRecord | null>(null);
  const [openedRequestedMeetingId, setOpenedRequestedMeetingId] = useState<
    string | null
  >(null);
  const [requestedMeetingError, setRequestedMeetingError] = useState("");
  const [queueStatus, setQueueStatus] = useState("pending");
  const meetingParams = new URLSearchParams({ limit: "100" });
  if (query) meetingParams.set("q", query);
  if (dateFrom) meetingParams.set("date_from", dateFrom);
  if (dateTo) meetingParams.set("date_to", dateTo);
  if (speaker) meetingParams.set("speaker", speaker);
  if (tag) meetingParams.set("tag", tag);
  if (openActions) meetingParams.set("has_open_actions", "true");
  const meetings = useResource<JsonRecord>(
    `/api/meetings?${meetingParams}`,
    {},
  );
  const facets = useResource<JsonRecord>("/api/meetings/facets", {});
  const actions = useResource<JsonRecord>("/api/all-action-items", {});
  const speakers = useResource<JsonRecord>("/api/speakers", {});
  const projects = useResource<JsonRecord>("/api/projects", {});
  const intel = useResource<JsonRecord>(
    `/api/intel/jobs?status=${queueStatus}&limit=50&history_limit=5`,
    {},
  );
  const plugin = useResource<JsonRecord>(
    `/api/plugin-jobs?status=${queueStatus}&limit=50`,
    {},
  );
  const source =
    active === "meetings"
      ? meetings
      : active === "actions"
        ? actions
        : active === "speakers"
          ? speakers
          : active === "projects"
            ? projects
            : intel;
  const rows = useMemo(
    () =>
      active === "meetings"
        ? asRows(meetings.data, ["meetings"])
        : active === "actions"
          ? asRows(actions.data, ["items", "action_items"])
          : active === "speakers"
            ? asRows(speakers.data, ["speakers"])
            : active === "projects"
              ? asRows(projects.data, ["projects"])
              : [
                  ...asRows(intel.data, ["jobs"]),
                  ...asRows(plugin.data, ["jobs"]),
                ],
    [
      active,
      meetings.data,
      actions.data,
      speakers.data,
      projects.data,
      intel.data,
      plugin.data,
    ],
  );
  const requestedMeeting = useMemo(
    () =>
      requestedMeetingId
        ? (asRows(meetings.data, ["meetings"]).find(
            (row) => String(row.id) === requestedMeetingId,
          ) ?? null)
        : null,
    [meetings.data, requestedMeetingId],
  );
  useEffect(() => {
    if (
      !requestedMeetingId ||
      openedRequestedMeetingId === requestedMeetingId ||
      meetings.loading
    )
      return;
    setOpenedRequestedMeetingId(requestedMeetingId);
    setRequestedMeetingError("");
    setActive("meetings");
    if (requestedMeeting) {
      setSelected(requestedMeeting);
      return;
    }
    void apiFetch<JsonRecord>(
      `/api/meetings/${encodeURIComponent(requestedMeetingId)}`,
    )
      .then(setSelected)
      .catch((reason) => setRequestedMeetingError(readableError(reason)));
  }, [
    meetings.loading,
    openedRequestedMeetingId,
    requestedMeeting,
    requestedMeetingId,
  ]);
  const orientedMeeting =
    requestedMeeting ??
    (requestedMeetingId && String(selected?.id ?? "") === requestedMeetingId
      ? selected
      : null);
  return (
    <div className="page-wrap">
      <PageHero
        eyebrow="Meeting memory"
        title="Meetings"
        workroomSubject={
          orientedMeeting
            ? String(orientedMeeting.title ?? "Meeting")
            : undefined
        }
        actions={
          <div className="button-row">
            <Button variant="primary" onClick={() => setImportOpen(true)}>
              Import
            </Button>
            <Link
              className="btn btn--secondary"
              to={workroomHref("/live", {
                action: workroom?.subject_ref
                  ? "record-follow-up"
                  : "record-meeting",
                subjectRef: workroom?.subject_ref,
                returnRef: workroom?.return_ref,
              })}
            >
              Record meeting
            </Link>
          </div>
        }
      >
        Review meetings, import recordings, and export retained work.
      </PageHero>
      {requestedMeetingError ? (
        <InlineMessage tone="error">
          {requestedMeetingError}{" "}
          <Button
            dense
            variant="ghost"
            onClick={() => {
              setRequestedMeetingError("");
              setOpenedRequestedMeetingId(null);
            }}
          >
            Try again
          </Button>
        </InlineMessage>
      ) : null}
      <Panel title="Archive" eyebrow={`${rows.length} visible`}>
        <Tabs
          label="Archive sections"
          tabs={ARCHIVE_TABS}
          active={active}
          onChange={setActive}
        />
        {active === "meetings" ? (
          <>
            <Toolbar label="Archive filters">
              <Field label="Search meetings">
                {({ id }) => (
                  <TextInput
                    id={id}
                    type="search"
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                  />
                )}
              </Field>
              <Field label="From">
                {({ id }) => (
                  <TextInput
                    id={id}
                    type="date"
                    value={dateFrom}
                    onChange={(event) => setDateFrom(event.target.value)}
                  />
                )}
              </Field>
              <Field label="To">
                {({ id }) => (
                  <TextInput
                    id={id}
                    type="date"
                    value={dateTo}
                    onChange={(event) => setDateTo(event.target.value)}
                  />
                )}
              </Field>
              <Field label="Speaker">
                {({ id }) => (
                  <Select
                    id={id}
                    value={speaker}
                    onChange={(event) => setSpeaker(event.target.value)}
                  >
                    <option value="">Any speaker</option>
                    {asRows(facets.data, ["speakers"]).map((row, index) => (
                      <option
                        key={rowId(row, index)}
                        value={String(row.id ?? row.name ?? row.value)}
                      >
                        {String(row.name ?? row.label ?? row.value)}
                      </option>
                    ))}
                  </Select>
                )}
              </Field>
              <Field label="Tag">
                {({ id }) => (
                  <Select
                    id={id}
                    value={tag}
                    onChange={(event) => setTag(event.target.value)}
                  >
                    <option value="">Any tag</option>
                    {(Array.isArray(facets.data.tags)
                      ? facets.data.tags
                      : []
                    ).map((value) => (
                      <option key={String(value)}>{String(value)}</option>
                    ))}
                  </Select>
                )}
              </Field>
              <label className="hs-check">
                <input
                  type="checkbox"
                  checked={openActions}
                  onChange={(event) => setOpenActions(event.target.checked)}
                />
                <span>
                  <strong>Open actions</strong>
                </span>
              </label>
              <Button onClick={() => void meetings.reload()}>
                Apply filters
              </Button>
              <Button
                variant="ghost"
                onClick={() => {
                  setQuery("");
                  setDateFrom("");
                  setDateTo("");
                  setSpeaker("");
                  setTag("");
                  setOpenActions(false);
                }}
              >
                Clear
              </Button>
            </Toolbar>
          </>
        ) : null}
        {active === "queues" ? (
          <Field label="Queue status">
            {({ id }) => (
              <Select
                id={id}
                value={queueStatus}
                onChange={(event) => {
                  setQueueStatus(event.target.value);
                  window.setTimeout(() => {
                    void intel.reload();
                    void plugin.reload();
                  });
                }}
              >
                <option value="pending">Queued</option>
                <option value="running">Running</option>
                <option value="failed">Failed</option>
                <option value="complete">Succeeded</option>
              </Select>
            )}
          </Field>
        ) : null}
        <ResourceState
          loading={source.loading}
          error={source.error}
          empty={!rows.length}
          onRetry={() => void source.reload()}
        >
          <ul className="data-list">
            {rows.map((row, index) => (
              <li className="data-row" key={rowId(row, index)}>
                <div>
                  <strong>
                    {String(
                      row.title ??
                        row.name ??
                        row.text ??
                        row.kind ??
                        "Archive item",
                    )}
                  </strong>
                  <small>
                    {String(
                      row.started_at ??
                        row.created_at ??
                        row.owner ??
                        row.status ??
                        row.summary ??
                        "",
                    )}
                  </small>
                </div>
                <div className="button-row">
                  <StatusPill
                    tone={
                      row.status === "failed" ||
                      ["error", "failed", "import_failed"].includes(
                        String(row.intel_status ?? ""),
                      ) ||
                      ["capture_failed", "recoverable", "recording"].includes(
                        String(row.capture_status ?? ""),
                      )
                        ? "error"
                        : ["partial", "skipped", "queued"].includes(
                              String(row.intel_status ?? ""),
                            )
                          ? "warning"
                          : row.status === "complete"
                            ? "success"
                            : "neutral"
                    }
                  >
                    {displayState(
                      (row.capture_status !== "finalized"
                        ? row.capture_status
                        : row.intel_status) ??
                        row.status ??
                        row.kind ??
                        active.slice(0, -1),
                    )}
                  </StatusPill>
                  {active === "meetings" ? (
                    <Button dense onClick={() => setSelected(row)}>
                      Review meeting
                    </Button>
                  ) : null}
                  {active === "meetings" &&
                  ["capture_failed", "recoverable", "recording"].includes(
                    String(row.capture_status ?? ""),
                  ) ? (
                    <Button
                      dense
                      onClick={() =>
                        void apiFetch(
                          `/api/meetings/${encodeURIComponent(String(row.id))}/capture/recover`,
                          { method: "POST" },
                        ).then(() => source.reload())
                      }
                    >
                      Recover saved work
                    </Button>
                  ) : null}
                  {active === "queues" && row.status === "failed" ? (
                    <Button
                      dense
                      onClick={() =>
                        void apiFetch(
                          `/api/${row.meeting_id ? "intel/retry" : "plugin-jobs"}/${encodeURIComponent(String(row.meeting_id ?? row.id))}${row.meeting_id ? "" : "/retry-now"}`,
                          { method: "POST" },
                        ).then(() => source.reload())
                      }
                    >
                      {row.meeting_id
                        ? "Retry intelligence"
                        : "Retry background work"}
                    </Button>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        </ResourceState>
      </Panel>
      <ImportDialog
        open={importOpen}
        onClose={() => setImportOpen(false)}
        onImported={() => void meetings.reload()}
      />
      <MeetingDetail
        meeting={selected}
        onClose={() => setSelected(null)}
        onDeleted={() => void meetings.reload()}
      />
    </div>
  );
}
