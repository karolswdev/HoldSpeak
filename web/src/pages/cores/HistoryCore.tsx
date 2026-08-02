// HS-95-06 — the meeting memory core: archive, facets, import, detail,
// intelligence, aftercare — hosted anywhere (see ActivityCore's rules).
// HS-98-03 — re-crafted native: the detail leaves its modal and lives
// as the split's second pane; import is an in-surface section; rows
// are honest; confirms are inline two-steps. Wire calls unchanged.
// HS-111-03 — the archive browser (audit §3): the list is a
// SurfaceLedger catalog (reverse-chron, state tokens naming their
// axis), the record's spine is the always-visible transcript well
// (SurfaceWell), artifacts are etched receipts, exports and DELETE
// live on the ONE footer receipt bar, and the recovery cards became
// gadget-grammar attention slabs. Wire calls unchanged.
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { openPrimitive, openSurfaceOr } from "../../desk/shell";
import type { CoreProps } from "./ActivityCore";
import {
  Button,
  Disclosure,
  InlineMessage,
  StatusPill,
} from "../../components/signal/Signal";
import {
  apiBlob,
  apiFetch,
  readableError,
  type JsonRecord,
} from "../../lib/api";
import {
  authorityBasisLabel,
  controlModeLabel,
  effectClassLabel,
  humanizeWireValue,
  proposalStatusLabel,
} from "../../lib/productLanguage";
import { MeetingConflictRecovery } from "../../meetings/MeetingConflictRecovery";
import { MeetingIntelRecovery } from "../../meetings/MeetingIntelRecovery";
import { asRows, rowId, useResource } from "../pageSupport";
import {
  ConfirmVerb,
  SurfaceCode,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceLibrary,
  SurfaceLibraryTile,
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceSplit,
  SurfaceState,
  SurfaceVerbs,
  SurfaceWell,
} from "../../desk/surface/Surface";
import {
  CheckGadget,
  CycleGadget,
  EgressChip,
  GadgetGroup,
  GadgetRow,
  GadgetTable,
  StringGadget,
} from "../../desk/surface/gadgets";
import { Material } from "../../desk/surface/Material";
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

/* HS-111-03 — the catalog's state token: axis-named, tone as color on
   the words (never a shuffle, never a pill). "Intelligence", never
   the banned abbreviation (HS-100-05 vocabulary guard). The axis word
   rides its own span so the narrow rail can fold it away without
   losing the state. */
type StateToken = { axis?: string; label: string; tone?: "warn" | "danger" };

function stateToken(row: JsonRecord): StateToken {
  const capture = String(row.capture_status ?? "");
  if (capture === "recording") return { label: "REC", tone: "danger" };
  if (capture === "capture_failed")
    return { label: "CAPTURE FAILED", tone: "danger" };
  if (capture === "recoverable") return { label: "RECOVERABLE", tone: "warn" };
  const intelValue = row.intel_status;
  const state =
    typeof intelValue === "object" && intelValue !== null
      ? String((intelValue as JsonRecord).state ?? "")
      : String(intelValue ?? "");
  const axis = "INTELLIGENCE";
  const known: Record<string, StateToken> = {
    disabled: { axis, label: "OFF" },
    skipped: { axis, label: "SKIPPED", tone: "warn" },
    queued: { axis, label: "QUEUED", tone: "warn" },
    pending: { axis, label: "QUEUED", tone: "warn" },
    running: { axis, label: "RUNNING", tone: "warn" },
    partial: { axis, label: "PARTIAL", tone: "warn" },
    error: { axis, label: "FAILED", tone: "danger" },
    failed: { axis, label: "FAILED", tone: "danger" },
    import_failed: { label: "IMPORT FAILED", tone: "danger" },
  };
  if (row.status === "failed") return { label: "FAILED", tone: "danger" };
  return known[state] ?? { label: "SAVED" };
}

function StateTokenSpan({ token }: { token: StateToken }) {
  return (
    <span className="surface-token" data-tone={token.tone}>
      {token.axis ? (
        <span className="surface-token-axis">{`${token.axis} `}</span>
      ) : null}
      {token.label}
    </span>
  );
}

const MONTHS = [
  "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
  "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
];

/** MMM DD — the catalog's date column. */
function ledgerDate(value: unknown): string {
  const date = new Date(String(value ?? ""));
  if (Number.isNaN(date.getTime())) return "";
  return `${MONTHS[date.getMonth()]} ${String(date.getDate()).padStart(2, "0")}`;
}

/** n MIN, folding to n HR past ten hours — a catalog cell, not a
 * six-digit minute wall. Empty when the wire has no duration. */
function durationToken(seconds: unknown): string {
  const minutes = Math.round(Number(seconds ?? 0) / 60);
  if (!Number.isFinite(minutes) || minutes <= 0) return "";
  if (minutes >= 600) return `${Math.round(minutes / 60)} HR`;
  return `${minutes} MIN`;
}

/** hh:mm — the receipt stamp's clock. */
function clockTime(value: unknown): string {
  const date = new Date(String(value ?? ""));
  if (Number.isNaN(date.getTime())) return "";
  return `${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function download(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** The one receipt channel: what the machine just did, on the footer. */
type Receipt = { text: string; tone?: "danger" };

function ImportSection({
  onDone,
  onImported,
  scope,
}: {
  onDone(): void;
  onImported(): void;
  scope?: string;
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
      actions={
        <Button dense variant="ghost" onClick={onDone}>
          Close
        </Button>
      }
    >
      <div className="surface-record-lead">
        <Button
          variant="primary"
          onClick={() => openSurfaceOr("record-live", "/live", scope)}
        >
          Record meeting
        </Button>
        <span className="quiet">or drop a recording below</span>
      </div>
      <label
        className={"surface-dropwell" + (file ? " has-file" : "")}
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          event.stopPropagation();
          const dropped = event.dataTransfer?.files?.[0];
          if (dropped) setFile(dropped);
        }}
      >
        <input
          type="file"
          accept="audio/*,.wav,.mp3,.m4a,.ogg,.flac,.vtt,.srt,.txt"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
        {file ? (
          <>
            <span className="surface-dropwell-name surface-primary">
              {file.name}
            </span>
            <small>drop another file to replace it</small>
          </>
        ) : (
          <>
            <span className="surface-dropwell-glyph" aria-hidden="true">
              ⇣
            </span>
            <span className="surface-primary">Drop it here, or browse</span>
            {/* Rendered as mono tokens (CSS uppercases); the literal
                lowercase suffixes and ffmpeg stay in source — they are
                the wire truth. */}
            <small>.wav direct · .mp3 .m4a .ogg .flac via ffmpeg · .vtt .srt .txt</small>
          </>
        )}
      </label>
      {file ? (
        <GadgetGroup>
          <GadgetRow label="TITLE">
            <StringGadget label="Title" value={title} onChange={setTitle} />
          </GadgetRow>
          <GadgetRow label="SPEAKER">
            <StringGadget
              label="Speaker"
              value={speaker}
              onChange={setSpeaker}
            />
          </GadgetRow>
          <GadgetRow label="TAGS" fact="COMMA SEPARATED">
            <StringGadget label="Tags" value={tags} onChange={setTags} />
          </GadgetRow>
        </GadgetGroup>
      ) : null}
      {error ? <InlineMessage tone="error">{error}</InlineMessage> : null}
      <div className="surface-actions">
        <Button
          variant="primary"
          loading={busy}
          disabled={!file}
          onClick={submit}
        >
          Import
        </Button>
      </div>
    </SurfaceSection>
  );
}

function MeetingDetail({
  meeting,
  view,
  momentSegmentIndex,
  onClose,
  onDeleted,
  onReceipt,
}: {
  meeting: JsonRecord | null;
  /** "outcomes" (the face) or "artifacts" (the wing). */
  view: "outcomes" | "artifacts";
  /** HS-109-02/05: a resolved decision moment seeks this transcript row. */
  momentSegmentIndex?: number | null;
  onClose(): void;
  onDeleted(): void;
  /** HS-111-03 — outcomes land on the footer receipt bar. */
  onReceipt(receipt: Receipt): void;
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
      onReceipt({
        text: decision === "approved" ? "APPROVED" : "REJECTED",
      });
    } catch (reason) {
      onReceipt({ text: `⚠ REFUSED · ${readableError(reason)}`, tone: "danger" });
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
      onReceipt({
        text: what === "digest" ? "PROPOSED DIGEST" : "PROPOSED FOLLOW-UP",
      });
    } catch (reason) {
      onReceipt({ text: `⚠ REFUSED · ${readableError(reason)}`, tone: "danger" });
    } finally {
      setBusy(false);
    }
  };
  const segments = asRows(detail, ["segments", "transcript"]);
  useEffect(() => {
    if (momentSegmentIndex == null || !segments.length) return;
    const frame = window.requestAnimationFrame(() => {
      document
        .getElementById(`transcript-${id}-${momentSegmentIndex}`)
        ?.scrollIntoView({ block: "center", behavior: "smooth" });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [id, momentSegmentIndex, segments.length]);
  const artifactRows = asRows(artifacts, ["artifacts", "items"]);
  const actionRows = asRows(aftercare, ["action_items", "actions", "items"]);
  const timelineRows = asRows(timeline, ["timeline", "items"]);
  const proposalRows = asRows(proposals, ["proposals"]);
  const openActions = actionRows.filter((row) => row.status !== "done");
  const settledActions = actionRows.filter((row) => row.status === "done");
  if (!meeting) return null;

  const startedAt = detail?.started_at ?? meeting.started_at;
  const durationS = Number(detail?.duration_seconds ?? meeting.duration_seconds ?? 0);
  const intelStatus = detail?.intel_status;
  const intelOff =
    (typeof intelStatus === "object" && intelStatus !== null
      ? String((intelStatus as JsonRecord).state ?? "")
      : String(intelStatus ?? "")) === "disabled";
  const hasOutcomes =
    proposalRows.length > 0 || openActions.length > 0 || settledActions.length > 0;
  const captureBad =
    Boolean(detail?.capture_status) && detail?.capture_status !== "finalized";

  /* The needs-you table: undecided proposals lead, open action items
     follow — pending receipts, one dense table (audit §3.2.3). */
  const undecided = proposalRows.filter(
    (row) =>
      row.status === "proposed" &&
      (row.policy_snapshot as JsonRecord | undefined)?.outcome !== "refused",
  ).length;
  const needsCount = undecided + openActions.length;
  const needsRows: Array<{ cells: ReactNode[]; verbs: ReactNode }> =
    [
      ...proposalRows.map((row) => {
        const policy = (row.policy_snapshot ?? {}) as JsonRecord;
        const operation = (row.operation ?? {}) as JsonRecord;
        const refused = policy.outcome === "refused";
        const effect = String(operation.effect_class ?? row.action ?? "");
        const destination = String(operation.destination ?? row.target ?? "");
        const facts = [
          effect ? `EFFECT: ${effectClassLabel(effect)}` : null,
          destination ? `DEST: ${humanizeWireValue(destination)}` : null,
          `BASIS: ${authorityBasisLabel(
            String(policy.authority_basis ?? "per_action_required"),
          )}`,
        ]
          .filter((fact): fact is string => Boolean(fact))
          .join(" · ")
          .toUpperCase();
        const commitment = row.commitment as JsonRecord | undefined;
        return {
          cells: [
            <span key="what" title={presentValue(row.preview ?? row.body ?? "")}>
              {String(row.title ?? row.kind ?? "Proposed action")}
            </span>,
            <span key="facts" title={facts}>
              {facts}
            </span>,
          ],
          verbs:
            row.status === "proposed" && !refused ? (
              <>
                <Button
                  dense
                  loading={busy}
                  title={String(commitment?.approve ?? "")}
                  onClick={() => void decide(row, "approved")}
                >
                  Approve
                </Button>
                <Button
                  dense
                  variant="ghost"
                  title={String(commitment?.reject ?? "")}
                  onClick={() => void decide(row, "rejected")}
                >
                  Reject
                </Button>
              </>
            ) : (
              <span
                className="surface-token"
                data-tone={refused ? "danger" : undefined}
              >
                {refused
                  ? "REFUSED"
                  : proposalStatusLabel(String(row.status ?? "")).toUpperCase()}
              </span>
            ),
        };
      }),
      ...openActions.map((row) => ({
        cells: [
          <span key="what">{String(row.text ?? row.title ?? "Action item")}</span>,
          <span key="facts">
            {presentValue(row.owner) ? `OWNER: ${presentValue(row.owner)}`.toUpperCase() : ""}
          </span>,
        ],
        verbs: <span className="surface-token" data-tone="warn">OPEN</span>,
      })),
    ];

  return (
    <SurfaceSection>
      {/* 0 — the record index line: title over ONE mono facts line. */}
      <div className="surface-detail-head">
        <div className="surface-detail-title">
          <strong className="surface-primary">
            {String(detail?.title ?? meeting.title ?? "Meeting")}
          </strong>
          <span className="surface-detail-facts">
            {[
              ledgerDate(startedAt),
              durationS > 0
                ? durationToken(durationS) || "1 MIN"
                : "",
              segments.length ? `${segments.length} SEG` : "",
              artifactRows.length ? `${artifactRows.length} ART` : "",
            ]
              .filter(Boolean)
              .join(" · ")}
            {captureBad || intelOff ? " · " : ""}
            {captureBad || intelOff ? (
              <StateTokenSpan token={stateToken(detail ?? meeting)} />
            ) : null}
          </span>
        </div>
        <Button dense variant="ghost" onClick={onClose}>
          Close
        </Button>
      </div>
      {error ? <InlineMessage tone="error">{error}</InlineMessage> : null}
      {/* 1 — attention slabs, only when real. */}
      {captureBad ? (
        <GadgetGroup label="Capture">
          <GadgetRow
            label={
              <span
                className="surface-token"
                data-tone={stateToken(detail ?? meeting).tone ?? "warn"}
              >
                {String(detail?.capture_status ?? "").replace(/_/g, " ").toUpperCase()}
              </span>
            }
            fact={
              detail?.capture_failure
                ? String(detail.capture_failure)
                : undefined
            }
          >
            <span className="gadget-fact">
              TRANSCRIPT RETAINED · LAST DURABLE CHECKPOINT
            </span>
          </GadgetRow>
        </GadgetGroup>
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
          <SurfaceLibrary
            count={artifactRows.length}
            token={`${artifactRows.length} ${artifactRows.length === 1 ? "ARTIFACT" : "ARTIFACTS"}`}
          >
            {artifactRows.map((row, index) => {
              const title = String(row.title ?? row.artifact_type ?? "Artifact");
              let body = String(row.body_markdown ?? row.content ?? "").trim();
              // Plugin-authored bodies often self-title with a leading
              // markdown heading matching `title` — the tile's spine
              // already carries the name, so drop the redundant echo.
              const headingEcho = new RegExp(
                `^#{1,3}\\s+${title.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\s*\\n+`,
                "i",
              );
              body = body.replace(headingEcho, "");
              const kind = String(row.artifact_type ?? "")
                .replace(/[_-]+/g, " ")
                .toUpperCase();
              const stamped = clockTime(row.created_at);
              return (
                <SurfaceLibraryTile
                  key={rowId(row, index)}
                  variant="receipt"
                  stamp={[
                    `ART ${String(index + 1).padStart(2, "0")}`,
                    kind,
                    stamped,
                  ]
                    .filter(Boolean)
                    .join(" · ")}
                  face={
                    body ? (
                      <Material>{body}</Material>
                    ) : (
                      // HS-111-07 — a body-less artifact face folds its
                      // wire behind the RAW pattern, never bare JSON.
                      <Disclosure title="RAW · ARTIFACT">
                        <SurfaceWell head={`RAW · ${kind || "ARTIFACT"}`}>
                          <SurfaceCode>
                            {JSON.stringify(row, null, 2)}
                          </SurfaceCode>
                        </SurfaceWell>
                      </Disclosure>
                    )
                  }
                  name={title}
                  says={
                    <span>
                      {String(detail?.title ?? meeting.title ?? "Meeting")}
                      {" · "}
                      {humanTime(row.created_at) || "just now"}
                    </span>
                  }
                  verbs={
                    <Button
                      dense
                      onClick={() =>
                        openPrimitive(`artifact:${String(row.id)}`)
                      }
                    >
                      Open
                    </Button>
                  }
                />
              );
            })}
          </SurfaceLibrary>
        ) : (
          <SurfaceState empty emptyLabel="No artifacts yet" emptyGlyph="◇" />
        )
      ) : (
        <>
          {/* 2 — what needs you: pending receipts in ONE dense table.
              Intelligence OFF says so as a token, never a sentence. */}
          <div className="surface-outcome-sec">
            {intelOff && !hasOutcomes ? (
              <span className="surface-token">
                INTELLIGENCE OFF · NO OUTCOMES
              </span>
            ) : needsRows.length ? (
              <>
                <span className="surface-eyebrow">
                  {`Needs you: ${needsCount}`}
                </span>
                <GadgetTable
                  head={["ITEM", "FACTS"]}
                  rows={needsRows.map((row) => row.cells)}
                  verbs={(index) => needsRows[index].verbs}
                />
              </>
            ) : (
              <span className="surface-token">QUEUE 0</span>
            )}
          </div>
          {/* 3 — THE TRANSCRIPT WELL: always visible, never folded. */}
          <SurfaceWell head={`TRANSCRIPT · ${segments.length} SEG`}>
            {segments.length ? (
              <ol className="transcript-list">
                {segments.map((row, index) => (
                  <li
                    key={rowId(row, index)}
                    id={`transcript-${id}-${index}`}
                    data-moment={index === momentSegmentIndex || undefined}
                  >
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
          </SurfaceWell>
          {/* 4 — settled: quiet ledger lines. */}
          {settledActions.length ? (
            <div className="surface-outcome-sec">
              <span className="surface-eyebrow">
                {`Settled: ${settledActions.length}`}
              </span>
              <ul className="surface-settled">
                {settledActions.map((row, index) => (
                  <li key={rowId(row, index)}>
                    <span aria-hidden="true">✓</span>
                    <span>
                      {String(row.text ?? row.title ?? "Action item")}
                      {presentValue(row.owner)
                        ? ` · ${presentValue(row.owner)}`
                        : ""}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          {/* 5 — the routing receipt stays folded, in its own well. */}
          {timelineRows.length ? (
            <Disclosure title="Routing receipt">
              <SurfaceWell head={`ROUTING · ${timelineRows.length}`}>
                <SurfaceCode>
                  {JSON.stringify(timelineRows, null, 2)}
                </SurfaceCode>
              </SurfaceWell>
            </Disclosure>
          ) : null}
          {/* 6 — aftercare rides the gadget grammar, only when wired. */}
          {aftercare.slack_configured ? (
            <GadgetGroup label="Aftercare">
              <GadgetRow label="DIGEST → SLACK">
                <Button
                  dense
                  loading={busy}
                  onClick={() => void proposeSlack("digest")}
                >
                  Send
                </Button>
              </GadgetRow>
              <GadgetRow label="FOLLOW-UP → SLACK">
                <Button
                  dense
                  loading={busy}
                  onClick={() => void proposeSlack("followup")}
                >
                  Send
                </Button>
              </GadgetRow>
              <GadgetRow label="BASIS">
                <span className="surface-token">
                  {controlModeLabel(String(authority.control_mode ?? "neutral"))}
                </span>
              </GadgetRow>
            </GadgetGroup>
          ) : null}
        </>
      )}
    </SurfaceSection>
  );
}

export function HistoryCore({ hero, scope }: CoreProps) {
  // Scope arrives as a prop (a qualified ref, e.g. "meeting:<id>") — the
  // flat wrapper decodes the URL; the desk passes it straight.
  const requestedMeetingScope =
    scope && scope.startsWith("meeting:")
      ? scope.slice("meeting:".length)
      : null;
  const [requestedMeetingId, requestedMeetingQuery = ""] =
    requestedMeetingScope?.split("?", 2) ?? [null, ""];
  const requestedMomentSegment = requestedMeetingQuery
    ? Number(new URLSearchParams(requestedMeetingQuery).get("segment"))
    : null;
  const [view, setView] = useState("outcomes");
  const [doorOpen, setDoorOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [speaker, setSpeaker] = useState("");
  const [tag, setTag] = useState("");
  const [openActions, setOpenActions] = useState(false);
  const [selected, setSelected] = useState<JsonRecord | null>(null);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [removing, setRemoving] = useState(false);
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
  if (query) meetingParams.set("search", query);
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
  const filtered = Boolean(
    query || speaker || tag || dateFrom || dateTo || openActions,
  );
  /* HS-111-03 — the footer's export/delete verbs act on the OPEN
     record; receipts land in the same bar's center channel. */
  const exportMeeting = async (format: string) => {
    if (!selected) return;
    const id = String(selected.id);
    try {
      download(
        await apiBlob(
          `/api/meetings/${encodeURIComponent(id)}/export?format=${format}`,
        ),
        `holdspeak-meeting-${id}.${format === "markdown" ? "md" : format}`,
      );
      setReceipt({
        text: `EXPORTED ${format === "markdown" ? "MD" : format.toUpperCase()} ${clockTime(new Date().toISOString())}`,
      });
    } catch (reason) {
      setReceipt({
        text: `⚠ REFUSED · ${readableError(reason)}`,
        tone: "danger",
      });
    }
  };
  const removeSelected = async () => {
    if (!selected) return;
    setRemoving(true);
    try {
      await apiFetch(`/api/meetings/${encodeURIComponent(String(selected.id))}`, {
        method: "DELETE",
      });
      setSelected(null);
      setReceipt({ text: `DELETED ${clockTime(new Date().toISOString())}` });
      void meetings.reload();
    } catch (reason) {
      setReceipt({
        text: `⚠ REFUSED · ${readableError(reason)}`,
        tone: "danger",
      });
    } finally {
      setRemoving(false);
    }
  };
  const needing = meetingRows.filter((row) => stateToken(row).tone).length;

  /* The rail: the catalog ledger — reverse-chron, never re-sorted;
     attention is the state token's tone, not a shuffle. */
  const rail = (
    <SurfaceSection label="Meetings">
      <SurfaceLedger
        cols="meetings"
        count={`${meetingRows.length} RECORDS${needing ? ` · ${needing} NEEDS YOU` : ""}`}
        controls={
          <>
            <StringGadget
              label="Search meetings"
              value={query}
              onChange={setQuery}
            />
            <Button
              dense
              variant="ghost"
              aria-expanded={filtersOpen}
              onClick={() => setFiltersOpen((open) => !open)}
            >
              Filters
            </Button>
          </>
        }
      >
        {filtersOpen ? (
          /* Filters apply on change (the resource re-fetches on param
             change); one RESET verb, no submit wall. */
          <GadgetGroup label="Filters">
            <GadgetRow label="SPEAKER">
              <CycleGadget
                label="Speaker"
                value={speaker}
                onChange={setSpeaker}
                options={[
                  { value: "", label: "ANY" },
                  ...asRows(facets.data, ["speakers"]).map((row) => ({
                    value: String(row.id ?? row.name ?? row.value),
                    label: String(row.name ?? row.label ?? row.value),
                  })),
                ]}
              />
            </GadgetRow>
            <GadgetRow label="TAG">
              <CycleGadget
                label="Tag"
                value={tag}
                onChange={setTag}
                options={[
                  { value: "", label: "ANY" },
                  ...(Array.isArray(facets.data.tags)
                    ? facets.data.tags
                    : []
                  ).map((value) => ({ value: String(value) })),
                ]}
              />
            </GadgetRow>
            <GadgetRow label="FROM">
              <StringGadget
                label="From date"
                type="date"
                mic={false}
                value={dateFrom}
                onChange={setDateFrom}
              />
            </GadgetRow>
            <GadgetRow label="TO">
              <StringGadget
                label="To date"
                type="date"
                mic={false}
                value={dateTo}
                onChange={setDateTo}
              />
            </GadgetRow>
            <GadgetRow label="OPEN ACTIONS">
              <CheckGadget
                label="Only meetings with open actions"
                checked={openActions}
                onChange={setOpenActions}
              />
            </GadgetRow>
            <div className="surface-actions">
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
                Reset
              </Button>
            </div>
          </GadgetGroup>
        ) : null}
        <SurfaceState
          loading={meetings.loading}
          error={meetings.error}
          empty={!meetingRows.length}
          emptyLabel="Nothing here yet"
          emptyImage={spriteUrl("meeting", "archive-empty")}
          onRetry={() => void meetings.reload()}
        >
          <ul className="surface-ledger-rows">
            {meetingRows.map((row, index) => {
              const token = stateToken(row);
              const isOpen = Boolean(
                selected && String(selected.id) === String(row.id),
              );
              const recoverable = [
                "capture_failed",
                "recoverable",
                "recording",
              ].includes(String(row.capture_status ?? ""));
              return (
                <SurfaceLedgerRow
                  key={rowId(row, index)}
                  time={ledgerDate(row.started_at ?? row.created_at)}
                  primary={String(row.title ?? "Meeting")}
                  open={isOpen}
                  onToggle={() => setSelected(isOpen ? null : row)}
                  cells={
                    <>
                      <span className="surface-ledger-cell">
                        {`${Number(row.segment_count ?? 0)} SEG`}
                      </span>
                      <span className="surface-ledger-cell">
                        {durationToken(row.duration_seconds)}
                      </span>
                      <span className="surface-ledger-cell">
                        <StateTokenSpan token={token} />
                      </span>
                    </>
                  }
                >
                  {recoverable ? (
                    <div className="surface-row-verbs">
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
                    </div>
                  ) : null}
                </SurfaceLedgerRow>
              );
            })}
          </ul>
        </SurfaceState>
      </SurfaceLedger>
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
            <GadgetGroup>
              <GadgetRow label="STATUS">
                <CycleGadget
                  label="Queue status"
                  value={queueStatus}
                  onChange={(next) => {
                    setQueueStatus(next);
                    window.setTimeout(() => {
                      void intel.reload();
                      void plugin.reload();
                    });
                  }}
                  options={[
                    { value: "pending", label: "Queued" },
                    { value: "running", label: "Running" },
                    { value: "failed", label: "Failed" },
                    { value: "complete", label: "Succeeded" },
                  ]}
                />
              </GadgetRow>
            </GadgetGroup>
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
                  meta={
                    <StatusPill tone={row.status === "failed" ? "error" : "neutral"}>
                      {displayState(row.status ?? row.kind ?? section)}
                    </StatusPill>
                  }
                  onOpen={
                    section === "projects"
                      ? () =>
                          openSurfaceOr(
                            "open-project-memory",
                            "/history",
                            `project:${String(row.id)}`,
                          )
                      : undefined
                  }
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

  const detailPane = (paneView: "outcomes" | "artifacts") => (
    <MeetingDetail
      meeting={selected}
      view={paneView}
      momentSegmentIndex={requestedMomentSegment}
      onClose={() => setSelected(null)}
      onDeleted={() => void meetings.reload()}
      onReceipt={setReceipt}
    />
  );

  const face = doorOpen ? (
    door
  ) : view === "record" ? (
    <ImportSection
      onDone={() => setView("outcomes")}
      onImported={() => void meetings.reload()}
      scope={scope}
    />
  ) : view === "artifacts" ? (
    selected ? (
      detailPane("artifacts")
    ) : (
      /* The wing works from cold: no record open → the catalog, so
         the hand can pick one. Never a dead-end empty state. */
      rail
    )
  ) : (
    <div className="surface-split-railed">
      <SurfaceSplit
        main={rail}
        detailOpen={Boolean(selected)}
        detail={detailPane("outcomes")}
      />
    </div>
  );

  return (
    <>
      {hero ? hero(verbs) : <SurfaceVerbs>{verbs}</SurfaceVerbs>}
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
      {/* HS-111-03 — the ONE footer receipt bar: residency chip, the
          receipt center channel, the open record's export + delete. */}
      <div className="surface-status surface-receiptbar">
        <EgressChip />
        <span
          className="surface-receiptbar-receipt"
          data-tone={receipt?.tone}
          role="status"
        >
          {receipt
            ? receipt.text
            : `${meetingRows.length} RECORDS${filtered ? " · FILTERED" : ""}`}
        </span>
        {selected && !doorOpen && view !== "record" ? (
          <span className="surface-receiptbar-verbs">
            <Button
              dense
              variant="ghost"
              onClick={() => void exportMeeting("markdown")}
            >
              MD
            </Button>
            <Button
              dense
              variant="ghost"
              onClick={() => void exportMeeting("txt")}
            >
              TXT
            </Button>
            <Button
              dense
              variant="ghost"
              onClick={() => void exportMeeting("json")}
            >
              JSON
            </Button>
            <Button
              dense
              variant="ghost"
              onClick={() => void exportMeeting("srt")}
            >
              SRT
            </Button>
            <ConfirmVerb
              label="Delete"
              confirmLabel="Delete?"
              busy={removing}
              onConfirm={() => void removeSelected()}
            />
          </span>
        ) : null}
      </div>
    </>
  );
}
