// HS-200-11 — the preparation brief's wire shapes, decoded ONCE.
// The manifest's coverage vocabulary is the one `desk/coverage.ts` reads
// (C4); the claims are the update posture's `UpdateClaim` unchanged, because
// only the binding is new (design D3, "the claim seam").

import { decodeClaim, type UpdateClaim } from "../update/model";

export type ManifestSourceState = "available" | "stale" | "failed" | "unavailable";

export type ManifestRepair = { token: string; verb: string; href: string };

export type ManifestSource = {
  sourceId: string;
  kind: string;
  label: string;
  state: ManifestSourceState;
  observedAt: string | null;
  revision: string;
  reason: string | null;
  repair: ManifestRepair | null;
  tokens: string[];
  host: string;
  watchIds: string[];
};

export type ManifestDecision = {
  ref: string;
  text: string;
  lifecycle: "current" | "superseded";
  at: string | null;
  meetingTitle: string;
  /** The record that replaced a superseded one (P1-2). */
  successorRef: string | null;
  /** HS-200-16: the RECORD's own kind. Confirming an action-kind proposal
   *  also writes a decision record, so this list holds commitments too; the
   *  face draws each row as what it IS, never as the list it arrived in. */
  kind: "decision" | "action";
};

/** An item the bound left out, named (P1-3). */
export type NotIncluded = { title: string; ref: string; section: string; why: string };

export type ManifestCommitment = {
  ref: string;
  text: string;
  owner: string | null;
  dueAt: string | null;
  /** HS-200-16: the mirror -- this list holds decision-kind rows too. */
  kind: "decision" | "action";
};

export type BriefManifest = {
  projectId: string;
  projectRevision: number;
  purpose: string;
  preparedAt: string;
  calendar: { present: boolean };
  coverage: { expected: number; available: number; complete: boolean };
  sources: ManifestSource[];
  omitted: ManifestSource[];
  decisions: ManifestDecision[];
  commitments: ManifestCommitment[];
  notIncluded: NotIncluded[];
};

export type OutlineEntry = { text: string; spanId: string };

export type BriefOutline = {
  priorities: OutlineEntry[];
  questions: OutlineEntry[];
  obligations: OutlineEntry[];
};

export type BriefLifecycle = "draft" | "kept" | "discarded";

export type Brief = {
  id: string;
  projectId: string;
  projectRevision: number;
  purpose: string;
  lifecycle: BriefLifecycle;
  manifestRevision: number;
  manifest: BriefManifest;
  manifestSha256: string;
  integrity: "verified" | "mismatch";
  outline: BriefOutline;
  bodyMd: string;
  claims: UpdateClaim[];
  generator: string;
  generatorHost: string | null;
  generatorModel: string | null;
  elapsedMs: number;
  createdAt: string;
  keptAt: string | null;
};

/** The bounded route state the hub names BEFORE anything is sent (AC5). */
export type BriefRouteState =
  | "ready"
  | "not_set"
  | "key_missing"
  | "unavailable"
  | "unreachable"
  | "no_output"
  | "unusable_output"
  | "stopped";

/** The invoke receipt (P0): did a request LEAVE, to which host, under which
 *  kernel operation, with what outcome.  `NOTHING SENT` only when `sent` is
 *  false -- never inferred from the absence of an answer. */
export type InvokeReceipt = {
  sent: boolean;
  operationId: string;
  outcome: string;
  sendPhase: string;
  host: string;
};

export type BriefRoute = {
  state: BriefRouteState;
  token: string;
  host: string;
  model: string;
  boundary: string;
  reason: string;
  repair: string;
  invoke: InvokeReceipt;
};

/** A refused preparation: the hub's route state and the purpose, verbatim. */
export type PrepareRefusal = {
  route: BriefRoute;
  purpose: string;
  error: string;
};

const str = (v: unknown, fallback = ""): string => (v == null ? fallback : String(v));
const strOrNull = (v: unknown): string | null => (v == null || v === "" ? null : String(v));

function decodeSource(raw: Record<string, unknown>): ManifestSource {
  const repair = raw.repair && typeof raw.repair === "object" ? (raw.repair as Record<string, unknown>) : null;
  return {
    sourceId: str(raw.source_id),
    kind: str(raw.kind),
    label: str(raw.label),
    state: (str(raw.state, "unavailable") as ManifestSourceState),
    observedAt: strOrNull(raw.observed_at),
    revision: str(raw.revision),
    reason: strOrNull(raw.reason),
    repair: repair ? { token: str(repair.token), verb: str(repair.verb), href: str(repair.href, "/") } : null,
    tokens: Array.isArray(raw.tokens) ? (raw.tokens as unknown[]).map(String) : [],
    host: str(raw.host),
    watchIds: Array.isArray(raw.watch_ids) ? (raw.watch_ids as unknown[]).map(String) : [],
  };
}

export function decodeManifest(raw: Record<string, unknown> | null | undefined): BriefManifest {
  const r = raw ?? {};
  const coverage = (r.coverage as Record<string, unknown> | undefined) ?? {};
  const calendar = (r.calendar as Record<string, unknown> | undefined) ?? {};
  const rows = (key: string): ManifestSource[] =>
    Array.isArray(r[key])
      ? (r[key] as unknown[])
          .filter((s): s is Record<string, unknown> => !!s && typeof s === "object")
          .map(decodeSource)
      : [];
  return {
    projectId: str(r.project_id),
    projectRevision: Number(r.project_revision ?? 0),
    purpose: str(r.purpose),
    preparedAt: str(r.prepared_at),
    calendar: { present: Boolean(calendar.present) },
    coverage: {
      expected: Number(coverage.expected ?? 0),
      available: Number(coverage.available ?? 0),
      complete: Boolean(coverage.complete ?? true),
    },
    sources: rows("sources"),
    omitted: rows("omitted"),
    decisions: Array.isArray(r.decisions)
      ? (r.decisions as Record<string, unknown>[]).map((d) => ({
          ref: str(d.ref),
          text: str(d.text),
          lifecycle: str(d.lifecycle) === "superseded" ? "superseded" : "current",
          at: strOrNull(d.at),
          meetingTitle: str(d.meeting_title),
          successorRef: strOrNull(d.successor_ref),
          kind: str(d.kind) === "action" ? ("action" as const) : ("decision" as const),
        }))
      : [],
    commitments: Array.isArray(r.commitments)
      ? (r.commitments as Record<string, unknown>[]).map((c) => ({
          ref: str(c.ref),
          text: str(c.text),
          owner: strOrNull(c.owner),
          dueAt: strOrNull(c.due_at),
          kind: str(c.kind) === "decision" ? ("decision" as const) : ("action" as const),
        }))
      : [],
    notIncluded: Array.isArray(r.not_included)
      ? (r.not_included as Record<string, unknown>[]).map((n) => ({
          title: str(n.title),
          ref: str(n.ref),
          section: str(n.section),
          why: str(n.why),
        }))
      : [],
  };
}

function decodeOutline(raw: unknown): BriefOutline {
  const r = (raw && typeof raw === "object" ? raw : {}) as Record<string, unknown>;
  const entries = (key: string): OutlineEntry[] =>
    Array.isArray(r[key])
      ? (r[key] as Record<string, unknown>[]).map((e) => ({ text: str(e.text), spanId: str(e.span_id) }))
      : [];
  return { priorities: entries("priorities"), questions: entries("questions"), obligations: entries("obligations") };
}

export function decodeBrief(raw: Record<string, unknown>): Brief {
  let claims: UpdateClaim[] = [];
  try {
    const parsed = typeof raw.claims_json === "string" ? JSON.parse(raw.claims_json) : raw.claims_json;
    if (Array.isArray(parsed)) claims = (parsed as Record<string, unknown>[]).map(decodeClaim);
  } catch {
    claims = [];
  }
  return {
    id: str(raw.id),
    projectId: str(raw.project_id),
    projectRevision: Number(raw.project_revision ?? 0),
    purpose: str(raw.purpose),
    lifecycle: (str(raw.lifecycle, "draft") as BriefLifecycle),
    manifestRevision: Number(raw.manifest_revision ?? 1),
    manifest: decodeManifest(raw.manifest as Record<string, unknown>),
    manifestSha256: str(raw.manifest_sha256),
    integrity: str(raw.integrity) === "mismatch" ? "mismatch" : "verified",
    outline: decodeOutline(raw.outline),
    bodyMd: str(raw.body_md),
    claims,
    generator: str(raw.generator, "deterministic"),
    generatorHost: strOrNull(raw.generator_host),
    generatorModel: strOrNull(raw.generator_model),
    elapsedMs: Number(raw.elapsed_ms ?? 0),
    createdAt: str(raw.created_at),
    keptAt: strOrNull(raw.kept_at),
  };
}

export function decodeInvoke(raw: unknown): InvokeReceipt {
  const r = (raw && typeof raw === "object" ? raw : {}) as Record<string, unknown>;
  return {
    sent: Boolean(r.sent),
    operationId: str(r.operation_id),
    outcome: str(r.outcome),
    sendPhase: str(r.send_phase),
    host: str(r.host),
  };
}

export function decodeRoute(raw: Record<string, unknown> | null | undefined): BriefRoute {
  const r = raw ?? {};
  return {
    state: (str(r.state, "not_set") as BriefRouteState),
    token: str(r.token, "MODEL NOT SET"),
    host: str(r.host),
    model: str(r.model),
    boundary: str(r.boundary),
    reason: str(r.reason),
    repair: str(r.repair, "Set up model"),
    invoke: decodeInvoke(r.invoke),
  };
}

/** The refusal's receipt line: what happened to the request, honestly.
 *  `NOTHING SENT` only when no kernel operation exists (P0). */
export function refusalReceipt(route: BriefRoute): { sent: boolean; host: string; line: string } {
  if (!route.invoke.sent) return { sent: false, host: "", line: "NOTHING SENT" };
  const host = route.invoke.host || route.host;
  const answered = route.invoke.outcome === "succeeded";
  const what =
    route.state === "stopped" ? "REQUEST HAD LEFT"
    : answered ? "NOTHING USABLE RECEIVED"
    : "NOT ANSWERED";
  return { sent: true, host, line: `SENT · ${host} · ${what}` };
}

/* ── tokens the face draws, from stored facts only ── */

/** `COVERAGE · 3 OF 4` — the head token where a sources ledger exists
 *  (verdict Q2).  Null when there is nothing to count (A.8). */
export function coverageToken(coverage: BriefManifest["coverage"]): string | null {
  if (coverage.expected === 0) return null;
  return `COVERAGE · ${coverage.available} OF ${coverage.expected}`;
}

/** The state chip on one source row: the C4 word for the C4 state. */
export function sourceStateToken(source: ManifestSource): { label: string; state: "success" | "warning" | "failure" | "idle" } {
  if (source.state === "available") return { label: "AVAILABLE", state: "success" };
  if (source.state === "stale") return { label: "STALE", state: "warning" };
  if (source.state === "failed") return { label: source.repair?.token ?? "CANT CHECK", state: "failure" };
  return { label: source.repair?.token ?? "UNAVAILABLE", state: "idle" };
}

/** `OBSERVED 09:10` or nothing at all — never `OBSERVED —`. */
export function observedToken(observedAt: string | null): string | null {
  if (!observedAt) return null;
  const d = new Date(observedAt);
  if (Number.isNaN(d.getTime())) return null;
  const pad = (n: number) => String(n).padStart(2, "0");
  return `OBSERVED ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function clockToken(prefix: string, iso: string | null): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${prefix} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** `DUE 09-20` -- a commitment's due DAY.
 *
 *  HS-200-16: this row used `clockToken`, which draws a wall clock.  A
 *  due value is a DATE (`2026-09-20`); `new Date("2026-09-20")` is UTC
 *  midnight, so the face read `DUE 18:00` -- a date shown as a time, and
 *  in a negative-offset zone the wrong day.  Recall already says
 *  `DUE 09-20` for the same commitment
 *  (`holdspeak/services/recall_service.py:93-105`).
 */
export function dueDayToken(prefix: string, iso: string | null): string | null {
  if (!iso) return null;
  const dateOnly = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso.trim());
  if (dateOnly) return `${prefix} ${dateOnly[2]}-${dateOnly[3]}`;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${prefix} ${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

/** `11.4 S` from milliseconds; nothing under a tenth of a second (A.8). */
export function elapsedToken(ms: number): string | null {
  if (!ms || ms < 100) return null;
  return `${(ms / 1000).toFixed(1)} S`;
}

/** The short emblem the source ledger leads with. */
export function sourceEmblem(kind: string): string {
  const key = kind.toLowerCase();
  if (key === "github") return "GH";
  if (key === "jira") return "J";
  if (key === "meeting") return "MTG";
  if (key === "confluence") return "CNF";
  return key.slice(0, 2).toUpperCase() || "SRC";
}

/** The claim's source, named without a raw id (162's law): a decision by
 *  its date (`DEC 09-05`), a commitment by its date (`CMT 09-12`), a Room
 *  source by its own label (`karolswdev/HoldSpeak`, `KAN`). */
export function refLabel(ref: string, manifest: BriefManifest): string {
  const short = (iso: string | null | undefined): string => {
    if (!iso) return "";
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return "";
    const pad = (n: number) => String(n).padStart(2, "0");
    return `${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  };
  if (ref.startsWith("decision_record:")) {
    const decision = manifest.decisions.find((d) => d.ref === ref);
    const date = short(decision?.at);
    return date ? `DEC ${date}` : "DEC";
  }
  if (ref.startsWith("commitment:")) {
    const commitment = manifest.commitments.find((c) => c.ref === ref);
    const date = short(commitment?.dueAt);
    return date ? `CMT ${date}` : "CMT";
  }
  if (ref.startsWith("source:")) {
    const id = ref.slice("source:".length);
    const source = manifest.sources.find((s) => s.sourceId === id);
    return source ? source.label || sourceEmblem(source.kind) : "SOURCE";
  }
  const kind = ref.split(":", 1)[0] || "REF";
  return kind.replace(/_/g, " ").toUpperCase();
}
