/* Programs (PROGRAMS-DESIGN-2026-10-28 §4, §9, §9b, §11): the hub's shapes,
 * as the faces read them. `GET /api/programs`, `GET /api/programs/{id}`,
 * the `program_changed` frame. The words a state reads (`state_word`) come
 * from the hub (`program_service.STEP_WORDS` / `PROGRAM_WORDS`); the faces
 * draw them through `stateWords`. */

export type ProgramState = "drafting" | "running" | "waiting" | "done" | "parked" | "failed";

export type StepState =
  | "planned" | "ready" | "briefed" | "working" | "waiting" | "checking" | "check_failed"
  | "review" | "findings" | "pr_open" | "merge_ask" | "merged" | "done" | "parked" | "failed";

export type StationKey = "brief" | "work" | "check" | "review" | "pr" | "merge";

/** The desk's Control mode ladder (design §6, owner 2026-10-28): Secure ·
 *  Normal · YOLO. The desk's own policy wire says `safe` / `neutral`. */
export type Control = "secure" | "normal" | "yolo";

/** One engine decision, "Decided for you" (§6, §8, §9 item 3). */
export interface DecidedRow {
  id: number | string;
  at: string;
  step_id: string | null;
  /** The decision's kind and choice (`add_step` / `add`, `merge` / `merge`). */
  kind?: string | null;
  choice?: string | null;
  /** What was decided (`Merged PR #101 of step 1 (check green)`). */
  line: string;
  /** The rule, in muted words (`YOLO: the engine adds a missing step and says so`). */
  rule: string | null;
  /** It can still be undone (a merge cannot). */
  overturnable: boolean;
  /** When he overturned it; null while it stands. */
  overturned_at?: string | null;
  operation_id?: string | null;
}

export interface ProgramCheckpoint {
  id: number | string;
  step_id: string;
  at: string;
  by: "agent" | "engine" | "owner";
  line: string;
  operation_id?: string | null;
  /** An engine decision's own fields (null on a plain checkpoint). */
  kind?: string | null;
  choice?: string | null;
  rule?: string | null;
  overturnable?: boolean;
  overturned_at?: string | null;
}

/** The program's Runs on engine (pi only): `null` for Claude Code / Codex. */
export interface ProgramEngine {
  id: string | null;
  /** `qwen3.8-27b on karol`. */
  label: string;
  /** `qwen` (the held word: `Ready · waiting for qwen`). */
  short: string;
  model?: string | null;
  /** No engine named: the desk's assignment for coding. */
  assignment?: boolean;
  /** The named engine is not in the library any more. */
  missing?: boolean;
}

export interface ProgramSummary {
  id: string;
  title: string;
  state: ProgramState;
  state_word: string;
  done: number;
  total: number;
  /** Items only he can press (merge, findings, parked, ask review). */
  your_turn: number;
  /** Questions of a step's agent (answered in its lane). */
  asks: number;
  project_id: string | null;
  control: Control;
  /** `Secure`, `Normal`, `YOLO` (the Program wire only). */
  control_word?: string;
  updated_at: string;
  created_at: string;
  last_checkpoint: ProgramCheckpoint | null;
  in_state_seconds: number | null;
  /** Done only: `1 h 12`. */
  done_in?: string;
}

export interface ProgramList {
  programs: ProgramSummary[];
  counts: Partial<Record<ProgramState, number>>;
  worst: ProgramState | null;
  worst_word: string;
}

export interface ProgramFinding {
  id: string;
  level?: "required" | "should" | "note" | string;
  text: string;
  decision?: "fix_now" | "later" | "skip" | null;
}

export interface CheckSection {
  name: string;
  /** `green`, `red`, `no result`, `not run`. */
  state: string;
  detail?: string;
}

export interface ProgramStep {
  id: string;
  ordinal: number;
  title: string;
  state: StepState;
  state_word: string;
  /** Index into `stations` of the lit station; -1 = none yet. */
  station: number;
  stations: StationKey[];
  brief: string;
  owns: string[];
  after: number[];
  effort: "low" | "medium" | "high" | null;
  profile: string | null;
  /** `Claude Code`, `Codex`, `pi`. */
  agent: string;
  engine: ProgramEngine | null;
  prefer_idle: boolean;
  held_reason: string | null;
  race: number;
  race_of: string | null;
  /** `merge`: `level` (the Control level decides), `owner`, `auto`, `none`. */
  gate: { check: boolean; review: "none" | "agent" | "person"; review_depth: string | null; merge: string | null };
  launch_id: string | null;
  branch: string | null;
  worktree: string | null;
  pr: { number: number | null; url: string | null } | null;
  check: {
    verdict: string | null;
    log: string | null;
    sections: CheckSection[];
    reasons: string[];
    command: string | null;
    minutes: number | null;
    commit: string | null;
    running: boolean;
  };
  review: { verdict: string | null; round: number | null; reviewer: string | null };
  findings: ProgramFinding[];
  rounds: number;
  parked_reason: string | null;
  parked_by: string | null;
  origin_ref: string | null;
  for_person_id: string | null;
  for_person: string | null;
  report: string | null;
  last_checkpoint: ProgramCheckpoint | null;
  started_at: string | null;
  ended_at: string | null;
  updated_at: string | null;
  elapsed_seconds: number | null;
  elapsed: string;
  /** A race's contenders (top-level steps only). */
  contenders?: ProgramStep[];
}

export type YourTurnKind = "answer" | "merge" | "finding" | "parked" | "ask_review" | "core" | "race" | "add_step" | "close";

export interface YourTurnItem {
  id: string;
  kind: YourTurnKind;
  title: string;
  choices: string[];
  program_id: string;
  program_title: string;
  step_id: string;
  ordinal: number;
  step_title: string;
  launch_id: string | null;
  since: string | null;
  project_id: string | null;
  for_person_id: string | null;
  pr: { number: number | null; url: string | null } | null;
  finding_id?: string;
  level?: string;
  /** A core question (the goal, the shape of the work, egress, money,
   *  authority, safety, no rule): its reason. */
  core?: boolean;
  reason?: string | null;
  /** add_step: the proposal's index (sent as `finding_id`). */
  proposal?: number;
}

export interface ProgramPlace {
  project: { id: string; name: string } | null;
  origin: { ref: string; kind: string; id: string; title: string } | null;
  person: { id: string; name: string } | null;
}

export interface Program extends ProgramSummary {
  goal: string;
  repository: { root: string | null; label: string; base_branch: string | null };
  check_command: string | null;
  default: { profile: string | null; agent: string; engine: ProgramEngine | null };
  reviewer: { profile: string | null; agent: string | null; engine: ProgramEngine | null };
  prefer_idle: boolean;
  template: string | null;
  origin_ref: string | null;
  for_person_id: string | null;
  note_id: string | null;
  note_window: string | null;
  place: ProgramPlace;
  steps: ProgramStep[];
  checkpoints: ProgramCheckpoint[];
  your_turn_items: YourTurnItem[];
  decided_for_you?: DecidedRow[];
  spend_limit_usd?: number | null;
  /** He closed it (Secure). */
  closed_at?: string | null;
  revision: number;
  status_line: string;
}

/** `program_changed`: one per change; the faces re-read what it names. */
export interface ProgramChangedFrame {
  program_id: string;
  step_id?: string | null;
  state: ProgramState;
  your_turn: number;
}

/** A decide press (`POST …/steps/{sid}/decide`). */
export interface DecideBody {
  kind: Exclude<YourTurnKind, "answer">;
  choice: string;
  finding_id?: string;
  reason?: string;
}

/** The step a Drafting row writes (`POST …/plan`). */
export interface PlanStep {
  id?: string;
  title: string;
  brief?: string;
  owns?: string[];
  after?: number[];
  profile?: string | null;
  engine?: string | null;
  prefer_idle?: boolean;
  effort?: "low" | "medium" | "high";
  race?: number;
}

/** The Programs room line of a person or a project (§9b). */
export interface ProgramRoomRow {
  id: string;
  title: string;
  state: ProgramState;
  state_word: string;
  done: number;
  total: number;
  your_turn: number;
  updated_at?: string;
}

export interface PersonProgramRow extends ProgramRoomRow {
  line: string;
  to_show: { step_id: string; title: string; pr_number: number | null; pr_url: string | null; merged_at: string | null }[];
  to_ask: { step_id: string; title: string; kind: string }[];
}
