/* The Decisions app's hub calls (the native face, 2026-11-08): every read
 * and write the face makes, one typed function each. The ledger and Commit
 * are declared operations (holdspeak/decision_operations.py); the state,
 * the words, Supersede and Delete are the `decision.*` rows of
 * holdspeak/operations.py; a record read is the decision-records route.
 * The PR that made this file lists each one. */
import { apiFetch } from "../../lib/api";

export type LedgerRow = {
  source: "meeting" | "desk";
  id: string;
  text: string;
  rationale?: string | null;
  decided_at?: string | null;
  /** The record's lifecycle when it has one (active, superseded, disputed),
   *  else the decision's own. */
  lifecycle?: string | null;
  /** The decision's own state: a Desk decision's status (proposed,
   *  accepted, deprecated), a meeting decision's lifecycle. */
  status?: string | null;
  meeting_id?: string | null;
  meeting_title?: string | null;
  record_id?: string | null;
  committed_to?: string | null;
  committed?: number | boolean | null;
};
export type Ledger = { decisions?: LedgerRow[]; page?: { total?: number } };

export type RecordSource = { source_type: string; source_ref: string; text?: string; speaker?: string; meeting_id?: string };
export type RecordWork = { id: string; work_type: string; work_ref: string };
export type RecordRevision = { id: string; field_name: string; old_value: string | null; new_value: string | null; created_at: string };
export type DecisionRecord = {
  id: string;
  title?: string | null;
  decision_text: string;
  rationale: string | null;
  alternatives: string | null;
  owner: string | null;
  review_date: string | null;
  lifecycle: string;
  status?: string | null;
  sources?: RecordSource[];
  work?: RecordWork[];
  revisions?: RecordRevision[];
  predecessor_id?: string | null;
  successor_id?: string | null;
  source_type?: string;
  source_id?: string;
  created_at?: string | null;
  committed_to?: string | null;
  dispute_reason?: string | null;
  project_id?: string | null;
};

const enc = encodeURIComponent;

/** `decision.ledger` (declared): one page of the desk's decisions and the total. */
export function readLedger(query: { q?: string; current?: boolean; decisionId?: string; limit?: number; offset?: number }): Promise<Ledger> {
  const params = new URLSearchParams();
  if (query.decisionId) params.set("decision_id", query.decisionId);
  if (query.q?.trim()) params.set("q", query.q.trim());
  if (query.current) params.set("current", "true");
  params.set("limit", String(query.limit ?? 100));
  if (!query.decisionId) params.set("offset", String(query.offset ?? 0));
  return apiFetch<Ledger>(`/api/decisions/ledger?${params}`);
}

/** The record with its sources, work, revisions and lineage (hand-written route). */
export const readRecord = (id: string) => apiFetch<DecisionRecord>(`/api/decision-records/${enc(id)}`);

/** `follow_through.commit_decision` (declared): a decided record becomes one
 *  action item and one commitment; a second press answers the first. */
export const commitDecision = (recordId: string, who?: string | null) =>
  apiFetch<{ id: string; owner?: string | null; replayed?: boolean }>(`/api/decision-records/${enc(recordId)}/commit`, {
    method: "POST", json: who ? { who } : {},
  });

/** `decision.supersede` (declared): a Desk decision's successor, proposed. */
export const supersedeDecision = (deskId: string) =>
  apiFetch<{ decision?: { id?: string } }>(`/api/decisions/${enc(deskId)}/supersede`, { method: "POST", json: {} });

export { writeDecisionStatus } from "../decide";
