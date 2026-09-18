// HS-200-13 — the recall face's model (posture 5, boards P5Recall /
// P5RecallPhone / P5RecallQuiet).  Pure: the wire shape
// `GET /api/memory/recall` returns (holdspeak/services/recall_service.py),
// the five filters, and the token helpers the face draws with.

export type RecallFilter = "all" | "decisions" | "commitments" | "briefs" | "meetings";

/** The same five at both widths (design D2(e), `FilterTokens`). */
export const RECALL_FILTERS: { value: RecallFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "decisions", label: "Decisions" },
  { value: "commitments", label: "Commitments" },
  { value: "briefs", label: "Briefs" },
  { value: "meetings", label: "Meetings" },
];

export type DecisionState = "current" | "superseded" | "disputed";

export interface RecallSource {
  kind: "meeting";
  meeting_id: string;
  title: string;
  started_at: string | null;
  offset_seconds: number | null;
  segment_index: number | null;
  /** `MTG 09-07 · 11:31` */
  token: string;
  /** The review-meetings surface scope: `meeting:<id>?segment=<n>`. */
  scope: string;
}

export interface RecallProject {
  id: string;
  name: string;
}

export interface DecisionCard {
  id: string;
  ref: string;
  text: string;
  rationale: string;
  lifecycle: string;
  state: DecisionState;
  /** `DEC 09-07` */
  dec_token: string;
  decided_at: string | null;
  /** `["DECISION", "SUPPORTED", "ACCEPTED"]` — the three C2 axes. */
  axes: string[];
  support: string;
  acceptance: string;
  successor: { id: string; dec_token: string; text: string } | null;
  predecessor_id: string | null;
  supersession_reason: string | null;
  dispute_reason: string | null;
  project: RecallProject | null;
  source: RecallSource | null;
  carried: boolean;
  commitment_ids: string[];
}

export type NextAction = "name_owner" | "set_date" | "mark_done";

export interface OwedRow {
  id: string;
  ref: string;
  action_item_id: string;
  text: string;
  owner: string | null;
  /** `OWNER · PRIYA` / `OWNER · UNKNOWN` */
  owner_token: string;
  due_at: string | null;
  /** `DUE TODAY` / `OVERDUE · 2 D` / `DUE 09-12` / `DUE · UNKNOWN` */
  due_token: string;
  due_tone: "danger" | "warn" | "idle";
  status: string;
  unknowns: ("owner" | "due")[];
  next_action: NextAction;
  project: RecallProject | null;
  decision_record_id: string | null;
  decision_state: DecisionState | null;
}

export interface MemoryHitRow {
  kind: string;
  source_ref: string;
  title: string;
  snippet: string;
  occurred_at?: string;
  project_id?: string | null;
  retrieval_origin?: string;
  related_to?: string | null;
  relationship?: string | null;
  /** Brief rows only. */
  section?: string;
  brief_id?: string;
}

export interface RecallResult {
  query: string;
  filter: RecallFilter;
  searched_at: string;
  projects_searched: number;
  current: DecisionCard[];
  superseded: DecisionCard[];
  disputed: DecisionCard[];
  owed: OwedRow[];
  meetings: MemoryHitRow[];
  briefs: MemoryHitRow[];
  also: MemoryHitRow[];
  remembered: number;
}

/** The verb each next action reads as (story 13 AC3: one verb per row). */
export const NEXT_ACTION_VERB: Record<NextAction, string> = {
  name_owner: "Name an owner",
  set_date: "Set a date",
  mark_done: "Mark done",
};

/** The tone an axis chip wears. */
export function axisTone(axis: string): "ok" | "warn" | "danger" | undefined {
  switch (axis) {
    case "SUPPORTED":
    case "ACCEPTED":
      return "ok";
    case "SUPERSEDED":
    case "NO SOURCE":
      return "warn";
    case "DISPUTED":
      return "danger";
    default:
      return undefined;
  }
}

/** `SEARCHED 09:20` — the search's own clock, local. */
export function searchedToken(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return `SEARCHED ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

const WORDS = ["No", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten"];

/** The miss's one true line: `Four projects searched, none holds this`. */
export function missLine(projectsSearched: number): string {
  const n = Math.max(0, Math.trunc(projectsSearched));
  if (n === 0) return "Nothing on the desk holds this";
  const word = n <= 10 ? WORDS[n] : String(n);
  return n === 1 ? `${word} project searched, it does not hold this` : `${word} projects searched, none holds this`;
}

/** The display line for a searched state. */
export function displayLine(remembered: number): string {
  return remembered > 0 ? `${remembered} remembered` : "Nothing matches";
}

export const EMPTY_RESULT: RecallResult = {
  query: "",
  filter: "all",
  searched_at: "",
  projects_searched: 0,
  current: [],
  superseded: [],
  disputed: [],
  owed: [],
  meetings: [],
  briefs: [],
  also: [],
  remembered: 0,
};

/** The wire's shape, defensively decoded (a missing section is empty). */
export function decodeRecall(raw: unknown): RecallResult {
  const r = (raw && typeof raw === "object" ? raw : {}) as Record<string, unknown>;
  const list = <T,>(key: string): T[] => (Array.isArray(r[key]) ? (r[key] as T[]) : []);
  const filter = String(r.filter || "all") as RecallFilter;
  return {
    query: String(r.query || ""),
    filter: RECALL_FILTERS.some((f) => f.value === filter) ? filter : "all",
    searched_at: String(r.searched_at || ""),
    projects_searched: Number(r.projects_searched || 0),
    current: list<DecisionCard>("current"),
    superseded: list<DecisionCard>("superseded"),
    disputed: list<DecisionCard>("disputed"),
    owed: list<OwedRow>("owed"),
    meetings: list<MemoryHitRow>("meetings"),
    briefs: list<MemoryHitRow>("briefs"),
    also: list<MemoryHitRow>("also"),
    remembered: Number(r.remembered || 0),
  };
}
