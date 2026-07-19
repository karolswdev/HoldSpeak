// HS-95-06 — the meeting memory core: archive, facets, import, detail,
// intelligence, aftercare — hosted anywhere (see ActivityCore's rules).
// HS-98-03 — re-crafted native: the detail leaves its modal and lives
// as the split's second pane; import is an in-surface section; rows
// are honest; confirms are inline two-steps. Wire calls unchanged.
import { useEffect, useMemo, useState } from "react";
import { openSurfaceOr } from "../../desk/shell";
import type { CoreProps } from "./ActivityCore";
import {
  Button,
  Disclosure,
  Field,
  InlineMessage,
  Select,
  StatusPill,
  Tabs,
  TextInput,
} from "../../components/signal/Signal";
import {
  apiBlob,
  apiFetch,
  readableError,
  type JsonRecord,
} from "../../lib/api";
import {
  authorityBasisLabel,
  effectClassLabel,
  humanizeWireValue,
  proposalStatusLabel,
} from "../../lib/productLanguage";
import { MeetingConflictRecovery } from "../../meetings/MeetingConflictRecovery";
import { MeetingIntelRecovery } from "../../meetings/MeetingIntelRecovery";
import { PostureNote, asRows, rowId, useResource } from "../pageSupport";
import {
  ConfirmVerb,
  SurfaceCode,
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceSplit,
  SurfaceState,
  SurfaceVerbs,
} from "../../desk/surface/Surface";
import { humanTime, presentValue } from "../../desk/surface/format";

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

function ImportSection({
  onDone,
  onImported,
}: {
  onDone(): void;
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
      onDone();
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setBusy(false);
    }
  };
  return (
    <SurfaceSection
      label="Import a recording or transcript"
      actions={
        <Button dense variant="ghost" onClick={onDone}>
          Close
        </Button>
      }
    >
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
      <div className="surface-actions">
        <Button
          variant="primary"
          loading={busy}
          disabled={!file}
          onClick={submit}
        >
          Import to this device
        </Button>
      </div>
    </SurfaceSection>
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
  const [authority, setAuthority] = useState<JsonRecord>({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
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
      apiFetch<JsonRecord>("/api/authority/policy")
        .then(setAuthority)
        .catch(() => setAuthority({})),
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
  if (!meeting) return null;
  return (
    <SurfaceSection
      label={String(detail?.title ?? meeting.title ?? "Meeting detail")}
      actions={
        <Button dense variant="ghost" onClick={onClose}>
          Close
        </Button>
      }
    >
      <Tabs
        label="Meeting detail sections"
        tabs={DETAIL_TABS}
        active={active}
        onChange={setActive}
      />
      {error ? <InlineMessage tone="error">{error}</InlineMessage> : null}
      {detail?.capture_status && detail.capture_status !== "finalized" ? (
        <InlineMessage tone="warning">
          {`Meeting saved · ${displayState(detail.capture_status)}${detail.capture_failure ? ` · ${String(detail.capture_failure)}` : ""}. The transcript below is the last durable checkpoint.`}
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
          setDetail(await apiFetch(`/api/meetings/${encodeURIComponent(id)}`));
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
          <SurfaceState empty emptyLabel="No transcript" emptyGlyph="¶" />
        )
      ) : null}
      {active === "artifacts" ? (
        artifactRows.length ? (
          <>
            {artifactRows.map((row, index) => (
              <Disclosure
                key={rowId(row, index)}
                title={String(row.title ?? row.artifact_type ?? "Artifact")}
              >
                <SurfaceCode>
                  {String(
                    row.body_markdown ??
                      row.content ??
                      JSON.stringify(row, null, 2),
                  )}
                </SurfaceCode>
              </Disclosure>
            ))}
          </>
        ) : (
          <SurfaceState empty emptyLabel="No artifacts yet" emptyGlyph="◇" />
        )
      ) : null}
      {active === "aftercare" ? (
        <>
          {actionRows.length ? (
            <SurfaceRows>
              {actionRows.map((row, index) => (
                <SurfaceRow
                  key={rowId(row, index)}
                  title={String(row.text ?? row.title ?? "Action item")}
                  detail={presentValue(row.owner ?? row.status) || undefined}
                  meta={
                    <StatusPill
                      tone={row.status === "done" ? "success" : "warning"}
                    >
                      {row.status === "done"
                        ? "Action item complete"
                        : "Open action item"}
                    </StatusPill>
                  }
                />
              ))}
            </SurfaceRows>
          ) : (
            <SurfaceState empty emptyLabel="No aftercare yet" emptyGlyph="☑" />
          )}
          {aftercare.slack_configured ? (
            <div className="surface-actions">
              <Button loading={busy} onClick={() => void proposeSlack("digest")}>
                Send digest to Slack
              </Button>
              <Button
                loading={busy}
                onClick={() => void proposeSlack("followup")}
              >
                Send follow-up to Slack
              </Button>
              <small>
                <PostureNote
                  mode={String(authority.control_mode ?? "neutral")}
                  describe
                />
              </small>
            </div>
          ) : null}
        </>
      ) : null}
      {active === "routing" ? (
        <SurfaceCode>{JSON.stringify(timelineRows, null, 2)}</SurfaceCode>
      ) : null}
      {active === "proposals" ? (
        proposalRows.length ? (
          <SurfaceRows>
            {proposalRows.map((row, index) => {
              const policy = (row.policy_snapshot ?? {}) as JsonRecord;
              const operation = (row.operation ?? {}) as JsonRecord;
              const refused = policy.outcome === "refused";
              const effect = String(operation.effect_class ?? row.action ?? "");
              const destination = String(
                operation.destination ?? row.target ?? "",
              );
              const facts = [
                effect ? effectClassLabel(effect) : null,
                destination ? humanizeWireValue(destination) : null,
                authorityBasisLabel(
                  String(policy.authority_basis ?? "per_action_required"),
                ),
              ].filter((fact): fact is string => Boolean(fact));
              return (
                <SurfaceRow
                  key={rowId(row, index)}
                  title={
                    refused
                      ? "Operation refused"
                      : String(row.title ?? row.kind ?? "Proposed action")
                  }
                  detail={
                    <>
                      {presentValue(row.preview ?? row.body ?? row.status)}
                      {" · "}
                      <PostureNote mode={String(policy.mode ?? "neutral")} />
                      {facts.length ? ` · ${facts.join(" · ")}` : ""}
                    </>
                  }
                  meta={
                    row.status === "proposed" && !refused ? undefined : (
                      <StatusPill tone={refused ? "error" : "neutral"}>
                        {refused
                          ? "Refused"
                          : proposalStatusLabel(String(row.status ?? ""))}
                      </StatusPill>
                    )
                  }
                  verbs={
                    row.status === "proposed" && !refused ? (
                      <>
                        <Button
                          dense
                          loading={busy}
                          onClick={() => void decide(row, "approved")}
                        >
                          {String(
                            (row.commitment as JsonRecord | undefined)
                              ?.approve ??
                              `Approve for ${String(row.target ?? "executor")}`,
                          )}
                        </Button>
                        <Button
                          dense
                          variant="ghost"
                          onClick={() => void decide(row, "rejected")}
                        >
                          {String(
                            (row.commitment as JsonRecord | undefined)
                              ?.reject ?? "Reject proposed action",
                          )}
                        </Button>
                      </>
                    ) : undefined
                  }
                />
              );
            })}
          </SurfaceRows>
        ) : (
          <SurfaceState empty emptyLabel="No proposals" emptyGlyph="✋" />
        )
      ) : null}
      <div className="surface-actions">
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
        <ConfirmVerb
          label="Delete meeting"
          confirmLabel="Delete meeting?"
          busy={busy}
          onConfirm={() => void remove()}
        />
      </div>
    </SurfaceSection>
  );
}

export function HistoryCore({ hero, scope }: CoreProps) {
  // Scope arrives as a prop (a qualified ref, e.g. "meeting:<id>") — the
  // flat wrapper decodes the URL; the desk passes it straight.
  const requestedMeetingId =
    scope && scope.startsWith("meeting:")
      ? scope.slice("meeting:".length)
      : null;
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
  const meetings = useResource<JsonRecord>(`/api/meetings?${meetingParams}`, {});
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
  const verbs = (
    <>
      <Button variant="primary" dense onClick={() => setImportOpen(true)}>
        Import
      </Button>
      <Button
        dense
        variant="secondary"
        onClick={() => openSurfaceOr("record-live", "/live", scope)}
      >
        Record meeting
      </Button>
    </>
  );
  const rowState = (row: JsonRecord) => (
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
  );
  const archive = (
    <SurfaceSection label="Archive">
      <Tabs
        label="Archive sections"
        tabs={ARCHIVE_TABS}
        active={active}
        onChange={setActive}
      />
      {active === "meetings" ? (
        <Disclosure title="Filters">
          <div className="surface-actions">
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
            <Button dense onClick={() => void meetings.reload()}>
              Apply filters
            </Button>
            <Button
              dense
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
          </div>
        </Disclosure>
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
      <SurfaceState
        loading={source.loading}
        error={source.error}
        empty={!rows.length}
        emptyLabel="Nothing here yet"
        emptyGlyph="◫"
        onRetry={() => void source.reload()}
      >
        <SurfaceRows>
          {rows.map((row, index) => (
            <SurfaceRow
              key={rowId(row, index)}
              title={String(
                row.title ?? row.name ?? row.text ?? row.kind ?? "Archive item",
              )}
              detail={
                humanTime(row.started_at ?? row.created_at) ||
                presentValue(row.owner ?? row.status ?? row.summary) ||
                undefined
              }
              meta={rowState(row)}
              selected={Boolean(
                selected && String(selected.id) === String(row.id),
              )}
              onOpen={
                active === "meetings" ? () => setSelected(row) : undefined
              }
              verbs={
                <>
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
                  {active === "meetings" ? (
                    <Button dense onClick={() => setSelected(row)}>
                      Review meeting
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
                </>
              }
            />
          ))}
        </SurfaceRows>
      </SurfaceState>
    </SurfaceSection>
  );
  return (
    <>
      {hero ? (
        hero(verbs)
      ) : (
        <SurfaceVerbs status={`${rows.length} visible`}>{verbs}</SurfaceVerbs>
      )}
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
      {importOpen ? (
        <ImportSection
          onDone={() => setImportOpen(false)}
          onImported={() => void meetings.reload()}
        />
      ) : null}
      <SurfaceSplit
        main={archive}
        detailOpen={Boolean(selected)}
        detail={
          <MeetingDetail
            meeting={selected}
            onClose={() => setSelected(null)}
            onDeleted={() => void meetings.reload()}
          />
        }
      />
    </>
  );
}
