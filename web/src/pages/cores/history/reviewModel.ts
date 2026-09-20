// HS-200-12 — the meeting review face's model: the projection
// `GET /api/meetings/{id}/outcome-review` returns, decoded, and the tokens
// the face draws from it.  Board: P4Review / P4ReviewPhone / P4Processing.
//
// The three C2 axes on a proposal are INDEPENDENT (settled design D1):
// kind is always PROPOSAL (extraction produces a proposal); support is what
// the transcript establishes (a deterministic mapping, never a model score);
// acceptance is his Confirm alone.  The token vocabulary is the one
// `features/project-room/update/model.ts` already speaks — SUPPORTED /
// LINKED / LINKED · EDITED / UNSUPPORTED and UNREVIEWED / ACCEPTED /
// REJECTED — so a claim reads the same on the brief and on the meeting.
import type { ChipState } from "../../../desk/surface/patterns/StateChip";

export type ProposalSupport = "unknown" | "source_linked" | "supported" | "disputed";
export type ProposalAcceptance = "unreviewed" | "accepted" | "rejected" | "superseded";
export type ProposalState = "proposed" | "confirmed" | "dismissed";

export interface ReviewUnknown {
  type: string;
  value: string;
}

export interface ReviewProposal {
  id: string;
  kind: "decision" | "action";
  text: string;
  originalText: string | null;
  owner: string | null;
  due: string | null;
  /** HS-200-12 (counsel P1-3): the value HE supplied, when he did. */
  ownerSupplied: string | null;
  dueSupplied: string | null;
  extractionRevision: string | null;
  state: ProposalState;
  support: ProposalSupport;
  acceptance: ProposalAcceptance;
  supportInvalidated: boolean;
  unknowns: ReviewUnknown[];
  spanStart: number | null;
  spanEnd: number | null;
  segmentIndex: number | null;
  jobAttempt: number | null;
  modelHost: string | null;
  extractionModel: string | null;
  decisionRecordId: string | null;
  commitmentId: string | null;
  decidedAt: string | null;
  textEdited: boolean;
}

export interface ReviewJob {
  jobId: string;
  status: string;
  attempt: number;
  sameJob: boolean;
  lastError: string | null;
  modelHost: string | null;
  extractionModel: string | null;
  updatedAt: string | null;
}

export type CoverageState = "available" | "reading" | "queued" | "failed" | "unread";

export interface ReviewCoverage {
  turns: number;
  read: number | null;
  state: CoverageState;
  observedAt: string | null;
}

export interface MeetingReviewModel {
  meetingId: string;
  title: string;
  startedAt: string | null;
  /** The transcript revision the current read is keyed under. */
  revision: string | null;
  priorRevision: { decided: number; open: number };
  project: { id: string; name: string } | null;
  job: ReviewJob | null;
  coverage: ReviewCoverage;
  extractedAt: string | null;
  proposals: ReviewProposal[];
}

const str = (v: unknown): string | null => (v == null || v === "" ? null : String(v));
const num = (v: unknown): number | null =>
  typeof v === "number" && Number.isFinite(v) ? v : null;

export function decodeReviewProposal(raw: Record<string, unknown>): ReviewProposal {
  const record = (raw.support_record ?? null) as Record<string, unknown> | null;
  const state = (["proposed", "confirmed", "dismissed"].includes(String(raw.state ?? ""))
    ? String(raw.state)
    : "proposed") as ProposalState;
  const support = (["unknown", "source_linked", "supported", "disputed"].includes(
    String(raw.support ?? ""),
  )
    ? String(raw.support)
    : "unknown") as ProposalSupport;
  const acceptance = (["unreviewed", "accepted", "rejected", "superseded"].includes(
    String(raw.acceptance ?? ""),
  )
    ? String(raw.acceptance)
    : "unreviewed") as ProposalAcceptance;
  return {
    id: String(raw.id ?? ""),
    kind: raw.kind === "decision" ? "decision" : "action",
    text: String(raw.text ?? ""),
    originalText: str(raw.original_text),
    owner: str(raw.owner),
    due: str(raw.due),
    ownerSupplied: str(raw.owner_supplied),
    dueSupplied: str(raw.due_supplied),
    extractionRevision: str(raw.extraction_revision),
    state,
    support,
    acceptance,
    supportInvalidated: Boolean(record?.invalidated_at),
    unknowns: Array.isArray(raw.unknowns)
      ? (raw.unknowns as Record<string, unknown>[]).map((u) => ({
          type: String(u.type ?? ""),
          value: String(u.value ?? "unknown"),
        }))
      : [],
    spanStart: num(raw.span_start),
    spanEnd: num(raw.span_end),
    segmentIndex: num(raw.segment_index),
    jobAttempt: num(raw.job_attempt),
    modelHost: str(raw.model_host),
    extractionModel: str(raw.extraction_model),
    decisionRecordId: str(raw.decision_record_id),
    commitmentId: str(raw.commitment_id),
    decidedAt: str(raw.decided_at),
    textEdited: Boolean(raw.text_edited),
  };
}

export function decodeMeetingReview(raw: Record<string, unknown>): MeetingReviewModel {
  const job = (raw.job ?? null) as Record<string, unknown> | null;
  const coverage = (raw.coverage ?? {}) as Record<string, unknown>;
  const project = (raw.project ?? null) as Record<string, unknown> | null;
  const state = String(coverage.state ?? "unread");
  return {
    meetingId: String(raw.meeting_id ?? ""),
    title: String(raw.title ?? ""),
    startedAt: str(raw.started_at),
    revision: str(raw.revision),
    priorRevision: {
      decided: num((raw.prior_revision as Record<string, unknown> | undefined)?.decided) ?? 0,
      open: num((raw.prior_revision as Record<string, unknown> | undefined)?.open) ?? 0,
    },
    project: project && project.id ? { id: String(project.id), name: String(project.name ?? "") } : null,
    job: job
      ? {
          jobId: String(job.job_id ?? ""),
          status: String(job.status ?? ""),
          attempt: num(job.attempt) ?? 1,
          sameJob: Boolean(job.same_job),
          lastError: str(job.last_error),
          modelHost: str(job.model_host),
          extractionModel: str(job.extraction_model),
          updatedAt: str(job.updated_at),
        }
      : null,
    coverage: {
      turns: num(coverage.turns) ?? 0,
      read: num(coverage.read),
      state: (["available", "reading", "queued", "failed", "unread"].includes(state)
        ? state
        : "unread") as CoverageState,
      observedAt: str(coverage.observed_at),
    },
    extractedAt: str(raw.extracted_at),
    proposals: Array.isArray(raw.proposals)
      ? (raw.proposals as Record<string, unknown>[]).map(decodeReviewProposal)
      : [],
  };
}

/* ── tokens ── */

export type ReviewToken = { label: string; state: ChipState };

/** What the transcript establishes, with the honest EDITED suffix. */
export function supportToken(p: Pick<ReviewProposal, "support" | "supportInvalidated">): ReviewToken {
  if (p.support === "supported") return { label: "SUPPORTED", state: "success" };
  if (p.support === "disputed") return { label: "DISPUTED", state: "failure" };
  if (p.support === "source_linked") {
    return p.supportInvalidated
      ? { label: "LINKED · EDITED", state: "warning" }
      : { label: "LINKED", state: "idle" };
  }
  return { label: "UNSUPPORTED", state: "warning" };
}

/** His judgment, never inferred from a score. */
export function acceptanceToken(p: Pick<ReviewProposal, "acceptance">): ReviewToken {
  if (p.acceptance === "accepted") return { label: "ACCEPTED", state: "success" };
  if (p.acceptance === "rejected") return { label: "REJECTED", state: "failure" };
  if (p.acceptance === "superseded") return { label: "SUPERSEDED", state: "warning" };
  return { label: "UNREVIEWED", state: "idle" };
}

/** `OWNER · UNKNOWN` — a typed unknown, never a hedged guess. */
export function unknownToken(u: ReviewUnknown): string {
  return `${u.type.toUpperCase()} · ${u.value.toUpperCase()}`;
}

const pad = (n: number) => String(n).padStart(2, "0");

/** Wall-clock hh:mm of a meeting offset, from the meeting's start. */
function clockAt(startedAt: string | null, offsetSeconds: number): string {
  if (!startedAt) {
    const m = Math.floor(offsetSeconds / 60);
    return `${pad(Math.floor(m / 60))}:${pad(m % 60)}`;
  }
  const at = new Date(new Date(startedAt).getTime() + offsetSeconds * 1000);
  if (Number.isNaN(at.getTime())) return "";
  return `${pad(at.getHours())}:${pad(at.getMinutes())}`;
}

/** `MTG 09-07 · 11:31–11:33` — the transcript span as a provenance label. */
export function spanLabel(
  p: Pick<ReviewProposal, "spanStart" | "spanEnd">,
  startedAt: string | null,
): string | null {
  if (p.spanStart == null) return null;
  const start = startedAt ? new Date(startedAt) : null;
  const date =
    start && !Number.isNaN(start.getTime())
      ? `${pad(start.getMonth() + 1)}-${pad(start.getDate())}`
      : "";
  const from = clockAt(startedAt, p.spanStart);
  const to = p.spanEnd != null && p.spanEnd !== p.spanStart ? clockAt(startedAt, p.spanEnd) : "";
  const clock = to && to !== from ? `${from}–${to}` : from;
  return date ? `MTG ${date} · ${clock}` : `MTG · ${clock}`;
}

/** Rows keyed under an EARLIER transcript revision than the current read. */
export function isPriorRevision(p: Pick<ReviewProposal, "extractionRevision">, model: Pick<MeetingReviewModel, "revision">): boolean {
  return Boolean(model.revision && p.extractionRevision && p.extractionRevision !== model.revision);
}

/** Why `Accept reviewed` leaves a row alone (mirrors the service's rule). */
export function heldReason(p: ReviewProposal, model: Pick<MeetingReviewModel, "revision">): "unsupported" | "unknown" | "prior" | null {
  if (p.support !== "supported" && p.support !== "source_linked") return "unsupported";
  if (p.kind === "action" && (!p.owner || !p.due)) return "unknown";
  if (isPriorRevision(p, model)) return "prior";
  return null;
}

/** hh:mm of an ISO stamp, for `EXTRACTED 12:04` / `OBSERVED 12:04`. */
export function stamp(value: string | null): string {
  if (!value) return "";
  const at = new Date(value);
  if (Number.isNaN(at.getTime())) return "";
  return `${pad(at.getHours())}:${pad(at.getMinutes())}`;
}

/** `JOB K-8C21` — the job's short handle, never its raw id. */
export function jobHandle(jobId: string): string {
  const tail = jobId.replace(/[^a-z0-9]/gi, "").slice(-5).toUpperCase();
  return tail.length > 1 ? `${tail.slice(0, 1)}-${tail.slice(1)}` : tail;
}

/** The display line: the one big honest fact of the face. */
export function reviewHeadline(model: MeetingReviewModel): { text: string; accent: boolean } {
  const processing = model.job && ["queued", "reserved", "claimed", "running"].includes(model.job.status);
  if (processing) return { text: "Reading the meeting", accent: true };
  const open = model.proposals.filter((p) => p.state === "proposed" && !isPriorRevision(p, model)).length;
  if (open > 0) return { text: `${open} to review`, accent: true };
  const decided = model.proposals.length - open;
  if (decided > 0) return { text: "Reviewed", accent: false };
  // HS-201-04 (Astra's counsel finding 3): a disclosed summary request runs
  // ANALYSIS only — it does not run the plugin proposal chain (the lane A
  // handoff, "summary-only scope"). With no proposal at all, nothing looked,
  // so the face must not say it looked and found nothing.
  if (!extractionRan(model)) return { text: "Not run", accent: false };
  return { text: "Nothing to review", accent: false };
}

/** True only when the proposal chain left something of its own behind.
 *  The review read model's `job` is the SUMMARY job and `extracted_at` is
 *  the SUMMARY's completion stamp (`proposal_bridge_service.py:1046`,
 *  `:1048`) — neither says extraction ran. A proposal does. */
export function extractionRan(model: MeetingReviewModel): boolean {
  return model.proposals.length > 0;
}
