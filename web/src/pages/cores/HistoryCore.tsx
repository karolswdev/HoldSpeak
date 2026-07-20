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
import { SurfaceWings, useWindowWings } from "../../desk/surface/wings";
import { spriteUrl } from "../../desk/sprites";

// HS-100-08 — Meetings opens on OUTCOMES (thesis §1.2): what needs
// you, what settled, the transcript as a receipt. Record/import and
// the typed artifacts are wings; speakers/projects/queues plumbing
// stacks behind the one gear door.
const WINGS = [
  { id: "outcomes", label: "Outcomes" },
  { id: "record", label: "Record" },
  { id: "artifacts", label: "Artifacts" },
];
// Door sections (ids are part of the phase-91 archive lock).
const DOOR_SECTIONS = ["actions", "speakers", "projects", "queues"] as const;
// Receipt sections inside a meeting ("transcript", "aftercare",
// "routing", "proposals" remain the wire vocabulary).

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
  view,
  onClose,
  onDeleted,
}: {
  meeting: JsonRecord | null;
  /** "outcomes" (the face) or "artifacts" (the wing). */
  view: "outcomes" | "artifacts";
  onClose(): void;
  onDeleted(): void;
}) {
  const id = String(meeting?.id ?? "");
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
  const openActions = actionRows.filter((row) => row.status !== "done");
  const settledActions = actionRows.filter((row) => row.status === "done");
  if (!meeting) return null;

  const proposalsBlock = proposalRows.length ? (
    <SurfaceRows>
      {proposalRows.map((row, index) => {
        const policy = (row.policy_snapshot ?? {}) as JsonRecord;
        const operation = (row.operation ?? {}) as JsonRecord;
        const refused = policy.outcome === "refused";
        const effect = String(operation.effect_class ?? row.action ?? "");
        const destination = String(operation.destination ?? row.target ?? "");
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
                      (row.commitment as JsonRecord | undefined)?.approve ??
                        `Approve for ${String(row.target ?? "executor")}`,
                    )}
                  </Button>
                  <Button
                    dense
                    variant="ghost"
                    onClick={() => void decide(row, "rejected")}
                  >
                    {String(
                      (row.commitment as JsonRecord | undefined)?.reject ??
                        "Reject proposed action",
                    )}
                  </Button>
                </>
              ) : undefined
            }
          />
        );
      })}
    </SurfaceRows>
  ) : null;

  const actionRow = (row: JsonRecord, index: number) => (
    <SurfaceRow
      key={rowId(row, index)}
      title={String(row.text ?? row.title ?? "Action item")}
      detail={presentValue(row.owner ?? row.status) || undefined}
      meta={
        <StatusPill tone={row.status === "done" ? "success" : "warning"}>
          {row.status === "done" ? "Action item complete" : "Open action item"}
        </StatusPill>
      }
    />
  );

  const startedAt = detail?.started_at ?? meeting.started_at;
  const durationS = Number(detail?.duration_seconds ?? meeting.duration_seconds ?? 0);
  const intelStatus = detail?.intel_status;
  const intelOff =
    (typeof intelStatus === "object" && intelStatus !== null
      ? String((intelStatus as JsonRecord).state ?? "")
      : String(intelStatus ?? "")) === "disabled";
  const hasOutcomes =
    proposalRows.length > 0 || openActions.length > 0 || settledActions.length > 0;
  return (
    <SurfaceSection>
      <div className="surface-detail-head">
        <div className="surface-detail-title">
          <strong className="surface-primary">
            {String(detail?.title ?? meeting.title ?? "Meeting")}
          </strong>
          <small>
            {[
              humanTime(startedAt),
              durationS > 0
                ? `${Math.max(1, Math.round(durationS / 60))} min`
                : "",
              segments.length
                ? `${segments.length} segment${segments.length === 1 ? "" : "s"}`
                : "",
            ]
              .filter(Boolean)
              .join(" · ")}
          </small>
        </div>
        <Button dense variant="ghost" onClick={onClose}>
          Close
        </Button>
      </div>
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
      {view === "artifacts" ? (
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
      ) : (
        <>
          {/* 1 — what needs you: undecided proposals, then open actions.
              Intelligence OFF says so honestly instead of celebrating
              an empty queue it never filled. */}
          <div className="surface-outcome-sec">
            {intelOff && !hasOutcomes ? (
              <p className="surface-boundary-note">
                Intelligence is off — no outcomes were made for this
                meeting.
              </p>
            ) : (
              <span className="surface-eyebrow">
                {`Needs you — ${proposalRows.filter((row) => row.status === "proposed").length + openActions.length}`}
              </span>
            )}
            {proposalsBlock}
            {openActions.length ? (
              <SurfaceRows>{openActions.map(actionRow)}</SurfaceRows>
            ) : null}
            {!intelOff && !proposalRows.length && !openActions.length ? (
              <p className="surface-boundary-note">✓ Nothing waiting on you</p>
            ) : null}
            {aftercare.slack_configured ? (
              <div className="surface-actions">
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
                  <PostureNote
                    mode={String(authority.control_mode ?? "neutral")}
                    describe
                  />
                </small>
              </div>
            ) : null}
          </div>
          {/* 2 — settled. */}
          {settledActions.length ? (
            <div className="surface-outcome-sec">
              <span className="surface-eyebrow">
                {`Settled — ${settledActions.length}`}
              </span>
              <SurfaceRows>{settledActions.map(actionRow)}</SurfaceRows>
            </div>
          ) : null}
          {/* 3 — the receipts ("transcript" and "routing" stay quoted
              vocabulary): behind disclosures, never a wall. */}
          <Disclosure
            title={`Transcript — the receipt (${segments.length} segments)`}
            open={!hasOutcomes && segments.length > 0}
          >
            {segments.length ? (
              <ol className="transcript-list">
                {segments.map((row, index) => (
                  <li key={rowId(row, index)}>
                    <time>
                      {(() => {
                        const s = Number(row.start_time ?? row.start ?? NaN);
                        if (!Number.isFinite(s)) {
                          return String(row.timestamp ?? "");
                        }
                        const m = Math.floor(s / 60);
                        const sec = Math.floor(s % 60);
                        return `${m}:${String(sec).padStart(2, "0")}`;
                      })()}
                    </time>
                    <p>{String(row.text ?? row.transcript ?? "")}</p>
                  </li>
                ))}
              </ol>
            ) : (
              <SurfaceState empty emptyLabel="No transcript" emptyGlyph="¶" />
            )}
          </Disclosure>
          {timelineRows.length ? (
            <Disclosure title="Routing receipt">
              <SurfaceCode>{JSON.stringify(timelineRows, null, 2)}</SurfaceCode>
            </Disclosure>
          ) : null}
          <div className="surface-actions surface-detail-foot">
            <span className="surface-eyebrow">Export</span>
            <Button dense variant="ghost" onClick={() => void exportMeeting("markdown")}>
              Markdown
            </Button>
            <Button dense variant="ghost" onClick={() => void exportMeeting("txt")}>
              Text
            </Button>
            <Button dense variant="ghost" onClick={() => void exportMeeting("json")}>
              JSON
            </Button>
            <Button dense variant="ghost" onClick={() => void exportMeeting("srt")}>
              SRT
            </Button>
            <span className="surface-detail-foot-gap" />
            <ConfirmVerb
              label="Delete meeting"
              confirmLabel="Delete meeting?"
              busy={busy}
              onConfirm={() => void remove()}
            />
          </div>
        </>
      )}
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
  const [view, setView] = useState("outcomes");
  const [doorOpen, setDoorOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [speaker, setSpeaker] = useState("");
  const [tag, setTag] = useState("");
  const [openActions, setOpenActions] = useState(false);
  const [selected, setSelected] = useState<JsonRecord | null>(null);
  const [openedRequestedMeetingId, setOpenedRequestedMeetingId] = useState<
    string | null
  >(null);
  const [requestedMeetingError, setRequestedMeetingError] = useState("");
  const [queueStatus, setQueueStatus] = useState("pending");
  useWindowWings(
    <SurfaceWings
      wings={WINGS}
      active={doorOpen ? "" : view}
      onChange={(id) => {
        setDoorOpen(false);
        setView(id);
      }}
      door="Meeting plumbing"
      doorOpen={doorOpen}
      onDoor={() => setDoorOpen((v) => !v)}
    />,
    [view, doorOpen],
  );
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
  const meetingRows = useMemo(
    () => asRows(meetings.data, ["meetings"]),
    [meetings.data],
  );
  const requestedMeeting = useMemo(
    () =>
      requestedMeetingId
        ? (meetingRows.find(
            (row) => String(row.id) === requestedMeetingId,
          ) ?? null)
        : null,
    [meetingRows, requestedMeetingId],
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
    setView("outcomes");
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
      <Button
        variant="primary"
        dense
        onClick={() => {
          setDoorOpen(false);
          setView("record");
        }}
      >
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
          "meeting",
      )}
    </StatusPill>
  );

  /* The rail: this week's meetings, search-first; the filter wall
     stays folded. */
  const rail = (
    <SurfaceSection
      label="Meetings"
      actions={
        <TextInput
          type="search"
          aria-label="Search meetings"
          placeholder="Search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      }
    >
      <Disclosure title="Filters">
        <div className="surface-actions">
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
      <SurfaceState
        loading={meetings.loading}
        error={meetings.error}
        empty={!meetingRows.length}
        emptyLabel="Nothing here yet"
        emptyImage={spriteUrl("meeting", "archive-empty")}
        onRetry={() => void meetings.reload()}
      >
        <SurfaceRows>
          {meetingRows.map((row, index) => (
            <SurfaceRow
              key={rowId(row, index)}
              title={String(row.title ?? "Meeting")}
              detail={humanTime(row.started_at ?? row.created_at) || undefined}
              meta={rowState(row)}
              selected={Boolean(
                selected && String(selected.id) === String(row.id),
              )}
              onOpen={() => setSelected(row)}
              verbs={
                <>
                  {["capture_failed", "recoverable", "recording"].includes(
                    String(row.capture_status ?? ""),
                  ) ? (
                    <Button
                      dense
                      onClick={() =>
                        void apiFetch(
                          `/api/meetings/${encodeURIComponent(String(row.id))}/capture/recover`,
                          { method: "POST" },
                        ).then(() => meetings.reload())
                      }
                    >
                      Recover saved work
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

  /* The door: cross-meeting plumbing ("actions", "speakers",
     "projects", "queues" — DOOR_SECTIONS). */
  const doorRows = (section: (typeof DOOR_SECTIONS)[number]) =>
    section === "actions"
      ? asRows(actions.data, ["items", "action_items"])
      : section === "speakers"
        ? asRows(speakers.data, ["speakers"])
        : section === "projects"
          ? asRows(projects.data, ["projects"])
          : [...asRows(intel.data, ["jobs"]), ...asRows(plugin.data, ["jobs"])];
  const door = (
    <div className="surface-door">
      {DOOR_SECTIONS.map((section) => (
        <SurfaceSection
          key={section}
          label={section[0].toUpperCase() + section.slice(1)}
        >
          {section === "queues" ? (
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
          {doorRows(section).length ? (
            <SurfaceRows>
              {doorRows(section).map((row, index) => (
                <SurfaceRow
                  key={rowId(row, index)}
                  title={String(
                    row.title ?? row.name ?? row.text ?? row.kind ?? section,
                  )}
                  detail={
                    humanTime(row.started_at ?? row.created_at) ||
                    presentValue(row.owner ?? row.status ?? row.summary) ||
                    undefined
                  }
                  meta={rowState(row)}
                  verbs={
                    section === "queues" && row.status === "failed" ? (
                      <Button
                        dense
                        onClick={() =>
                          void apiFetch(
                            `/api/${row.meeting_id ? "intel/retry" : "plugin-jobs"}/${encodeURIComponent(String(row.meeting_id ?? row.id))}${row.meeting_id ? "" : "/retry-now"}`,
                            { method: "POST" },
                          ).then(() => {
                            void intel.reload();
                            void plugin.reload();
                          })
                        }
                      >
                        {row.meeting_id
                          ? "Retry intelligence"
                          : "Retry background work"}
                      </Button>
                    ) : undefined
                  }
                />
              ))}
            </SurfaceRows>
          ) : (
            <SurfaceState empty emptyLabel="Nothing here" emptyGlyph="·" />
          )}
        </SurfaceSection>
      ))}
    </div>
  );

  const face = doorOpen ? (
    door
  ) : view === "record" ? (
    <ImportSection
      onDone={() => setView("outcomes")}
      onImported={() => void meetings.reload()}
    />
  ) : view === "artifacts" ? (
    selected ? (
      <MeetingDetail
        meeting={selected}
        view="artifacts"
        onClose={() => setSelected(null)}
        onDeleted={() => void meetings.reload()}
      />
    ) : (
      <SurfaceState
        empty
        emptyLabel="Open a meeting to read its artifacts"
        emptyGlyph="◇"
      />
    )
  ) : (
    <div className="surface-split-railed">
      <SurfaceSplit
        main={rail}
        detailOpen={Boolean(selected)}
        detail={
          <MeetingDetail
            meeting={selected}
            view="outcomes"
            onClose={() => setSelected(null)}
            onDeleted={() => void meetings.reload()}
          />
        }
      />
    </div>
  );

  return (
    <>
      {hero ? (
        hero(verbs)
      ) : (
        <SurfaceVerbs status={`${meetingRows.length} visible`}>
          {verbs}
        </SurfaceVerbs>
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
      {face}
      <div className="surface-status">
        <span>{`${meetingRows.length} ${meetingRows.length === 1 ? "meeting" : "meetings"}`}</span>
        {query || speaker || tag || dateFrom || dateTo || openActions ? (
          <span>filtered</span>
        ) : null}
        {selected ? <span>1 open</span> : null}
      </div>
    </>
  );
}
