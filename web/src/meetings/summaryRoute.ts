/** HS-201-04 — the ONE place the face reads the disclosed summary route
 *  and starts a summary run.
 *
 *  The settled contract (story 03): every read model that can start a run
 *  carries `planned_route = {status, reason_code, selection_hash, legs}`
 *  and `run_receipt = {..., attempts}`. A run gesture MUST send the
 *  disclosed `selection_hash` as `expected_selection_hash`; the hub binds
 *  that exact selection and refuses drift with 409 BEFORE any provider is
 *  contacted (holdspeak/services/meeting_route_projection.py:147).
 *
 *  Article III (the point of decision): the host beside the verb comes
 *  from `legs[0].host`, and the hosts after the run come from
 *  `run_receipt.attempts`. Neither is ever composed from configuration.
 */
import { ApiError, apiFetch } from "../lib/api";

export interface RouteLeg {
  ordinal: number;
  host: string;
  boundary?: string | null;
  profile_id?: string | null;
  profile_revision?: number | null;
  deployment_revision_id?: string | null;
}

export interface PlannedRoute {
  status: string;
  reason_code: string | null;
  selection_hash: string | null;
  legs: RouteLeg[];
}

export interface RunAttempt {
  leg_ordinal: number;
  host: string;
  outcome: string;
  operation_id?: string | null;
}

export interface RunReceipt {
  receipt_id?: string;
  job_id?: string;
  meeting_id?: string;
  selection_hash?: string | null;
  outcome: string;
  attempts: RunAttempt[];
}

function record(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

/** Read `planned_route` off any meeting read model (detail, ledger row,
 *  recovery, run response, 409 body). Null when the wire carries none. */
export function readPlannedRoute(source: unknown): PlannedRoute | null {
  const row = record(source);
  if (!row) return null;
  const raw = record(row.planned_route ?? row.current_planned_route);
  if (!raw) return null;
  const legs = Array.isArray(raw.legs) ? raw.legs : [];
  return {
    status: String(raw.status ?? "unavailable"),
    reason_code:
      raw.reason_code == null ? null : String(raw.reason_code),
    selection_hash:
      raw.selection_hash == null ? null : String(raw.selection_hash),
    legs: legs
      .map((leg) => record(leg))
      .filter((leg): leg is Record<string, unknown> => leg !== null)
      .map((leg, index) => ({
        ordinal: Number(leg.ordinal ?? index + 1),
        host: String(leg.host ?? ""),
        boundary: leg.boundary == null ? null : String(leg.boundary),
        profile_id: leg.profile_id == null ? null : String(leg.profile_id),
        profile_revision:
          leg.profile_revision == null ? null : Number(leg.profile_revision),
        deployment_revision_id:
          leg.deployment_revision_id == null
            ? null
            : String(leg.deployment_revision_id),
      }))
      .filter((leg) => leg.host !== ""),
  };
}

/** Read `run_receipt` off any read model. Null when no run happened.
 *  Since lane A's `a07d4bb5` this field is the last EXECUTED receipt: a
 *  refusal no longer replaces it, and the refusal is served separately as
 *  `last_refusal` (`holdspeak/db/intel.py:2352`, `:2363`). */
export function readRunReceipt(source: unknown): RunReceipt | null {
  return readReceiptField(source, "run_receipt");
}

/** Read `last_refusal`: the newest durable no-call refusal (`outcome:
 *  "refused"`, no attempts). It survives a reload and a restart, so the
 *  face can say a run was refused without holding the 409 in memory. */
export function readLastRefusal(source: unknown): RunReceipt | null {
  return readReceiptField(source, "last_refusal");
}

function readReceiptField(source: unknown, field: string): RunReceipt | null {
  const row = record(source);
  if (!row) return null;
  const raw = record(row[field]);
  if (!raw) return null;
  const attempts = Array.isArray(raw.attempts) ? raw.attempts : [];
  return {
    receipt_id: raw.receipt_id == null ? undefined : String(raw.receipt_id),
    job_id: raw.job_id == null ? undefined : String(raw.job_id),
    meeting_id: raw.meeting_id == null ? undefined : String(raw.meeting_id),
    selection_hash:
      raw.selection_hash == null ? null : String(raw.selection_hash),
    outcome: String(raw.outcome ?? ""),
    attempts: attempts
      .map((attempt) => record(attempt))
      .filter((a): a is Record<string, unknown> => a !== null)
      .map((attempt, index) => ({
        leg_ordinal: Number(attempt.leg_ordinal ?? index + 1),
        host: String(attempt.host ?? ""),
        outcome: String(attempt.outcome ?? ""),
        operation_id:
          attempt.operation_id == null ? null : String(attempt.operation_id),
      }))
      .filter((attempt) => attempt.host !== ""),
  };
}

/**
 * The receipt to show, out of every receipt the face holds.
 *
 * A refusal writes its own receipt, and that receipt has no attempts —
 * nothing was contacted. Showing it in place of the last real run would
 * erase the destinations the user is owed (the lane A interlock: "the
 * response does not turn an old successful receipt into a new refusal").
 * So: the first candidate that actually contacted something wins, and a
 * bare refusal receipt is kept only when there is nothing else.
 */
export function pickRunReceipt(
  ...candidates: (RunReceipt | null | undefined)[]
): RunReceipt | null {
  const present = candidates.filter((value): value is RunReceipt => Boolean(value));
  return present.find((value) => value.attempts.length > 0) ?? present[0] ?? null;
}

/**
 * The last receipt per meeting that ACTUALLY contacted something.
 *
 * Durable retention is the hub's job and lane A now does it (`a07d4bb5`:
 * `run_receipt` is the last EXECUTED receipt, `last_refusal` is separate).
 * This map is only the gap between a 409 RESPONSE — whose body still
 * carries the bare refusal receipt — and the next read that answers with
 * the executed one. It gives up its value to any newer executed receipt.
 */
const EXECUTED_RECEIPTS = new Map<string, RunReceipt>();

/** Remember the executed receipt among these candidates, then return the
 *  best one to show: the freshest executed receipt if any candidate has
 *  attempts, else the one remembered for this meeting, else the bare one. */
export function executedReceipt(
  meetingId: string,
  ...candidates: (RunReceipt | null | undefined)[]
): RunReceipt | null {
  const picked = pickRunReceipt(...candidates);
  if (picked && picked.attempts.length > 0) {
    if (meetingId) EXECUTED_RECEIPTS.set(meetingId, picked);
    return picked;
  }
  return (meetingId ? EXECUTED_RECEIPTS.get(meetingId) : null) ?? picked ?? null;
}

/** Test seam: the map outlives a component, so a fence that reuses a
 *  meeting id must be able to start from nothing. */
export function forgetExecutedReceipts(): void {
  EXECUTED_RECEIPTS.clear();
}

/** A route that can start a run: resolved, hashed, with at least one leg. */
export function routeReady(route: PlannedRoute | null | undefined): boolean {
  return Boolean(
    route &&
      route.status === "ready" &&
      route.selection_hash &&
      route.legs.length > 0,
  );
}

/** The refusal reason as a token, in the hub's own plain words
 *  (`meeting_route_projection.unavailable` already de-underscores them).
 *  UX-CANON A.10: an honest state with a plain reason, never a stack. */
export function routeReasonToken(route: PlannedRoute | null | undefined): string {
  const reason = String(route?.reason_code ?? "").trim();
  return (reason || "route unavailable").toUpperCase();
}

/** The refusal as ONE short fact line, in the product's own words.
 *
 *  The hub's `plainReason` is a two-sentence instruction; a face says a
 *  fact, not a paragraph (UX-CANON A.3). The full sentence stays on the
 *  token's title for anyone who hovers, and the repair is the face's own
 *  next move: the fresh route is drawn beside the verb. */
export function refusalFact(refusal: {
  code?: string;
  plainReason?: string;
}): string {
  const words: Record<string, string> = {
    selection_drift: "ROUTE CHANGED",
    selection_hash_required: "ROUTE NOT READ",
    route_unavailable: "NO SUMMARY ROUTE",
    running: "SUMMARY IS RUNNING",
    queued: "SUMMARY IS QUEUED",
    ready: "SUMMARY IS READY",
    reserved: "MEETING IS NOT SETTLED",
    empty: "NO TRANSCRIPT",
    no_assignment: "NO ENGINE FOR SUMMARIES",
  };
  const known = words[String(refusal.code ?? "")];
  if (known) return known;
  const first = String(refusal.plainReason ?? "").split(/(?<=[.!?])\s/)[0] ?? "";
  return (first.replace(/[.!?]+$/, "").trim() || "REFUSED").toUpperCase();
}

export interface SummaryRefusal {
  code: string;
  plainReason: string;
  /** The FRESH route the hub disclosed with its refusal. */
  route: PlannedRoute | null;
  /** The receipt of the refusal (or the last real run) — never dropped. */
  receipt: RunReceipt | null;
}

export type SummaryRunOutcome<T> =
  | { ok: true; result: T; receipt: RunReceipt | null; route: PlannedRoute | null }
  | { ok: false; refusal: SummaryRefusal };

/**
 * POST a summary run with the disclosed selection hash.
 *
 * A 409 comes back as a refusal (code, plain reason, the fresh route and
 * the receipt) instead of an exception, so the face can show it as a
 * refusal and KEEP an earlier successful receipt on screen. Every other
 * failure keeps its exception for the caller's existing error path.
 */
export async function postSummaryRun<T = Record<string, unknown>>(
  path: string,
  route: PlannedRoute | null | undefined,
): Promise<SummaryRunOutcome<T>> {
  try {
    const result = await apiFetch<T>(path, {
      method: "POST",
      json: { expected_selection_hash: route?.selection_hash ?? "" },
    });
    return {
      ok: true,
      result,
      receipt: readRunReceipt(result),
      route: readPlannedRoute(result) ?? route ?? null,
    };
  } catch (reason) {
    if (reason instanceof ApiError && reason.status === 409) {
      const payload = record(reason.payload) ?? {};
      return {
        ok: false,
        refusal: {
          code: String(payload.code ?? "conflict"),
          plainReason: String(
            payload.plainReason ?? payload.error ?? reason.message,
          ),
          route: readPlannedRoute(payload),
          receipt: readRunReceipt(payload),
        },
      };
    }
    throw reason;
  }
}
